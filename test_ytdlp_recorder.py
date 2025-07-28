"""
yt-dlp를 사용한 치지직 HLS 스트림 녹화 테스트
"""

import asyncio
import os
import sys
import signal
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# 프로젝트 루트를 sys.path에 추가
sys.path.insert(0, str(Path(__file__).parent))

from src.chzzk_recorder.monitor.live_monitor import LiveMonitor, LiveStatus
from src.config import config

# 전역 프로세스 변수
recording_process = None
recording_active = False

def signal_handler(sig, frame):
    """시그널 핸들러"""
    global recording_process, recording_active
    print(f"\n⚠️ 시그널 받음: {sig}")
    recording_active = False
    
    if recording_process:
        print("🛑 yt-dlp 프로세스 종료 중...")
        recording_process.terminate()
        try:
            recording_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            recording_process.kill()
    
    print("👋 테스트 종료")
    sys.exit(0)

async def test_ytdlp_recording():
    """yt-dlp로 치지직 스트림 녹화 테스트"""
    global recording_process, recording_active
    
    print("🧪 yt-dlp 치지직 녹화 테스트")
    print("=" * 50)
    
    # 환경변수 로드
    load_dotenv()
    
    # 시그널 핸들러 등록
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 모니터 초기화
    channel_id = os.getenv("CHZZK_CHANNEL_ID")
    nid_aut = os.getenv("NID_AUT")
    nid_ses = os.getenv("NID_SES")
    
    if not all([channel_id, nid_aut, nid_ses]):
        print("❌ 환경변수가 설정되지 않았습니다")
        print("필요한 환경변수: CHZZK_CHANNEL_ID, NID_AUT, NID_SES")
        return
    
    monitor = LiveMonitor(channel_id, nid_aut, nid_ses)
    
    try:
        print("🔍 방송 상태 확인 중...")
        stream_info = await monitor.check_live_status()
        
        if not stream_info.is_live:
            print(f"📴 방송이 진행 중이 아닙니다 (상태: {stream_info.status.value})")
            return
        
        if not stream_info.hls_url:
            print("❌ HLS URL을 찾을 수 없습니다")
            return
        
        print(f"✅ 방송 중: {stream_info.title}")
        print(f"📺 스트리머: {stream_info.streamer_name}")
        print(f"👥 시청자: {stream_info.viewer_count}")
        print(f"🔗 HLS URL: {stream_info.hls_url[:100]}...")
        
        # 녹화 파일명 생성
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_ytdlp_{stream_info.title.replace(' ', '_')}.mp4"
        safe_filename = "".join(c for c in filename if c.isalnum() or c in "._-")
        
        # 출력 디렉터리 생성
        output_dir = Path("test_recordings")
        output_dir.mkdir(exist_ok=True)
        output_path = output_dir / safe_filename
        
        print(f"💾 저장 경로: {output_path}")
        
        # yt-dlp 명령어 구성
        ytdlp_cmd = [
            "yt-dlp",
            "--no-playlist",
            "--live-from-start",
            "--format", "best[ext=mp4]",
            "--output", str(output_path),
            "--verbose",
            stream_info.hls_url
        ]
        
        print(f"🎬 yt-dlp 명령어: {' '.join(ytdlp_cmd[:6])} [URL]")
        print("⏱️ 10초간 녹화 테스트 시작...")
        
        # yt-dlp 프로세스 시작
        import subprocess
        recording_active = True
        recording_process = subprocess.Popen(
            ytdlp_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            bufsize=1
        )
        
        # 10초 대기 (실제로는 더 짧을 수 있음)
        start_time = asyncio.get_event_loop().time()
        while recording_active and (asyncio.get_event_loop().time() - start_time) < 10:
            if recording_process.poll() is not None:
                # 프로세스가 종료됨
                break
            await asyncio.sleep(0.5)
        
        # 프로세스 정리
        if recording_process and recording_process.poll() is None:
            print("🛑 녹화 중단 중...")
            recording_process.terminate()
            try:
                recording_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                recording_process.kill()
                recording_process.wait()
        
        # 결과 확인
        if recording_process:
            stdout, stderr = recording_process.communicate()
            print(f"\n📊 종료 코드: {recording_process.returncode}")
            
            if recording_process.returncode == 0:
                print("✅ yt-dlp 실행 성공!")
            else:
                print("❌ yt-dlp 실행 실패")
                print(f"stderr: {stderr[:500]}...")
        
        # 파일 확인
        if output_path.exists():
            file_size = output_path.stat().st_size
            print(f"📁 파일 생성됨: {output_path}")
            print(f"📏 파일 크기: {file_size:,} bytes ({file_size/1024/1024:.1f} MB)")
            
            if file_size > 1024:  # 1KB 이상이면 성공으로 간주
                print("🎉 녹화 테스트 성공!")
            else:
                print("⚠️ 파일이 너무 작습니다")
        else:
            print("❌ 파일이 생성되지 않았습니다")
    
    except Exception as e:
        print(f"❌ 테스트 중 오류: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await monitor.close()
        if recording_process and recording_process.poll() is None:
            recording_process.terminate()

if __name__ == "__main__":
    asyncio.run(test_ytdlp_recording()) 