#!/usr/bin/env python3
"""
Docker 컨테이너 헬스체크 스크립트
"""

import sys
import os
import subprocess
import json
from datetime import datetime, timedelta
from pathlib import Path

def check_process_running(process_name):
    """프로세스가 실행 중인지 확인"""
    try:
        result = subprocess.run(
            ["pgrep", "-f", process_name],
            capture_output=True,
            text=True
        )
        return result.returncode == 0
    except Exception:
        return False

def check_supervisor_status():
    """supervisor 상태 확인"""
    try:
        result = subprocess.run(
            ["supervisorctl", "status"],
            capture_output=True,
            text=True
        )
        return result.returncode == 0 and "chzzk-recorder" in result.stdout
    except Exception:
        return False

def check_log_files():
    """로그 파일이 정상적으로 생성되고 있는지 확인"""
    log_dir = Path("/app/logs")
    main_log = log_dir / "chzzk-recorder.log"
    
    # 로그 파일이 존재하는지 확인
    if not main_log.exists():
        return False, "Main log file not found"
    
    # 로그 파일이 최근에 업데이트되었는지 확인 (최대 5분)
    try:
        stat = main_log.stat()
        last_modified = datetime.fromtimestamp(stat.st_mtime)
        if datetime.now() - last_modified > timedelta(minutes=5):
            return False, f"Log file not updated since {last_modified}"
    except Exception as e:
        return False, f"Error checking log file: {e}"
    
    return True, "OK"

def check_disk_space():
    """디스크 공간 확인"""
    try:
        result = subprocess.run(
            ["df", "/app/recordings"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            if len(lines) >= 2:
                fields = lines[1].split()
                if len(fields) >= 5:
                    # 사용률이 90% 이상이면 경고
                    usage_percent = int(fields[4].rstrip('%'))
                    if usage_percent >= 90:
                        return False, f"Disk space almost full: {usage_percent}%"
        return True, "OK"
    except Exception as e:
        return False, f"Error checking disk space: {e}"

def check_config_files():
    """설정 파일 존재 확인"""
    config_files = [
        "/app/.env",
        "/app/src/config.py"
    ]
    
    for config_file in config_files:
        if not Path(config_file).exists():
            return False, f"Config file missing: {config_file}"
    
    return True, "OK"

def create_status_report():
    """상태 보고서 생성"""
    status = {
        "timestamp": datetime.now().isoformat(),
        "healthy": True,
        "checks": {}
    }
    
    # 프로세스 확인
    status["checks"]["main_process"] = {
        "status": "pass" if check_process_running("main.py") else "fail",
        "description": "Main recorder process"
    }
    
    # Supervisor 확인
    supervisor_ok = check_supervisor_status()
    status["checks"]["supervisor"] = {
        "status": "pass" if supervisor_ok else "fail",  
        "description": "Supervisor process manager"
    }
    
    # 로그 파일 확인
    log_ok, log_msg = check_log_files()
    status["checks"]["log_files"] = {
        "status": "pass" if log_ok else "fail",
        "description": f"Log files: {log_msg}"
    }
    
    # 디스크 공간 확인
    disk_ok, disk_msg = check_disk_space()
    status["checks"]["disk_space"] = {
        "status": "pass" if disk_ok else "warn",
        "description": f"Disk space: {disk_msg}"
    }
    
    # 설정 파일 확인
    config_ok, config_msg = check_config_files()
    status["checks"]["config_files"] = {
        "status": "pass" if config_ok else "fail",
        "description": f"Config files: {config_msg}"
    }
    
    # 전체 상태 결정
    failed_checks = [
        name for name, check in status["checks"].items() 
        if check["status"] == "fail"
    ]
    
    if failed_checks:
        status["healthy"] = False
        status["failed_checks"] = failed_checks
    
    return status

def main():
    """메인 헬스체크 실행"""
    try:
        status = create_status_report()
        
        # 상태 보고서를 JSON 파일로 저장 (웹 인터페이스용)
        status_file = Path("/app/logs/health_status.json")
        status_file.parent.mkdir(exist_ok=True)
        
        with open(status_file, 'w') as f:
            json.dump(status, f, indent=2)
        
        # Docker 헬스체크 결과 반환
        if status["healthy"]:
            print("✅ Container is healthy")
            print(f"Timestamp: {status['timestamp']}")
            
            # 간단한 상태 요약 출력
            for name, check in status["checks"].items():
                icon = "✅" if check["status"] == "pass" else "⚠️" if check["status"] == "warn" else "❌"
                print(f"{icon} {name}: {check['description']}")
            
            sys.exit(0)
        else:
            print("❌ Container is unhealthy")
            print(f"Failed checks: {', '.join(status.get('failed_checks', []))}")
            
            for name, check in status["checks"].items():
                if check["status"] == "fail":
                    print(f"❌ {name}: {check['description']}")
            
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Healthcheck error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 