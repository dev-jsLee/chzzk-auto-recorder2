#!/bin/bash
# 치지직 자동 녹화 컨테이너 상태 확인 스크립트

echo "===========================================" 
echo "    치지직 자동 녹화 시스템 상태 확인"
echo "==========================================="
echo "현재 시간: $(date)"
echo

# 1. Supervisor 상태 확인
echo "📊 프로세스 상태 (Supervisor):"
echo "-------------------------------------------"
supervisorctl status 2>/dev/null || echo "❌ Supervisor가 실행되지 않음"
echo

# 2. 메인 프로세스 확인
echo "🔍 메인 프로세스 확인:"
echo "-------------------------------------------"
if pgrep -f "main.py" > /dev/null; then
    echo "✅ 메인 녹화 프로세스 실행 중"
    ps aux | grep "main.py" | grep -v grep
else
    echo "❌ 메인 녹화 프로세스가 실행되지 않음"
fi
echo

# 3. 로그 파일 상태
echo "📝 로그 파일 상태:"
echo "-------------------------------------------"
LOG_DIR="/app/logs"
if [ -d "$LOG_DIR" ]; then
    echo "로그 디렉터리: $LOG_DIR"
    ls -la "$LOG_DIR"/*.log 2>/dev/null | tail -5
    echo
    
    # 최신 로그 몇 줄 표시
    MAIN_LOG="$LOG_DIR/chzzk-recorder.log"
    if [ -f "$MAIN_LOG" ]; then
        echo "📋 최신 로그 (마지막 10줄):"
        echo "-------------------------------------------"
        tail -10 "$MAIN_LOG"
        echo
    fi
else
    echo "❌ 로그 디렉터리를 찾을 수 없음"
fi

# 4. 녹화 디렉터리 상태
echo "💾 녹화 파일 상태:"
echo "-------------------------------------------"
RECORDING_DIR="/app/recordings"
if [ -d "$RECORDING_DIR" ]; then
    echo "녹화 디렉터리: $RECORDING_DIR"
    echo "총 파일 수: $(find "$RECORDING_DIR" -name "*.mp4" | wc -l)"
    echo "총 용량: $(du -sh "$RECORDING_DIR" 2>/dev/null | cut -f1)"
    echo
    echo "최신 녹화 파일 (최대 5개):"
    find "$RECORDING_DIR" -name "*.mp4" -type f -exec ls -lah {} \; 2>/dev/null | sort -k6,7 | tail -5
else
    echo "❌ 녹화 디렉터리를 찾을 수 없음"
fi
echo

# 5. 시스템 리소스 사용량
echo "💻 시스템 리소스:"
echo "-------------------------------------------"
echo "메모리 사용량:"
free -h
echo
echo "디스크 사용량:"
df -h /app/recordings 2>/dev/null || df -h /
echo
echo "CPU 사용량 (Top 5 프로세스):"
ps aux --sort=-%cpu | head -6
echo

# 6. 네트워크 연결 상태
echo "🌐 네트워크 연결:"
echo "-------------------------------------------"
echo "치지직 API 연결 테스트:"
if curl -s --max-time 5 "https://api.chzzk.naver.com" > /dev/null; then
    echo "✅ 치지직 API 접근 가능"
else
    echo "❌ 치지직 API 접근 불가"
fi
echo

# 7. 컨테이너 환경변수 (민감한 정보 제외)
echo "⚙️ 환경 설정:"  
echo "-------------------------------------------"
echo "시간대: ${TZ:-Not Set}"
echo "Python 경로: $(which python)"
echo "uv 경로: $(which uv)"
echo "FFmpeg 버전: $(ffmpeg -version 2>/dev/null | head -1 | cut -d' ' -f3 || echo "설치되지 않음")"
echo "Streamlink 버전: $(streamlink --version 2>/dev/null || echo "설치되지 않음")"
echo

# 8. 헬스체크 결과 (있는 경우)
echo "🏥 헬스체크 결과:"
echo "-------------------------------------------"
HEALTH_FILE="/app/logs/health_status.json"
if [ -f "$HEALTH_FILE" ]; then
    echo "헬스체크 파일 업데이트 시간: $(stat -c %y "$HEALTH_FILE" 2>/dev/null)"
    echo "상태 요약:"
    python3 -c "
import json
try:
    with open('$HEALTH_FILE', 'r') as f:
        data = json.load(f)
    print(f'전체 상태: {\"✅ 정상\" if data.get(\"healthy\") else \"❌ 문제 있음\"}')
    for name, check in data.get('checks', {}).items():
        status_icon = '✅' if check['status'] == 'pass' else '⚠️' if check['status'] == 'warn' else '❌'
        print(f'{status_icon} {name}: {check.get(\"description\", \"\")}')
except Exception as e:
    print(f'헬스체크 파일 읽기 실패: {e}')
    "
else
    echo "헬스체크 파일이 없습니다."
    # 직접 헬스체크 실행
    python3 /app/healthcheck.py 2>/dev/null || echo "헬스체크 실행 실패"
fi

echo
echo "==========================================="
echo "    상태 확인 완료"
echo "===========================================" 