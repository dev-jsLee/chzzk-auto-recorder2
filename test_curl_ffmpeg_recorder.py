"""
curl + FFmpeg 파이프라인을 사용한 치지직 HLS 스트림 녹화 테스트
"""

import asyncio
import os
import sys
import signal
import subprocess
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# 프로젝트 루트를 sys.path에 추가
sys.path.insert(0, str(Path(__file__).parent))

from src.chzzk_recorder.monitor.live_monitor import LiveMonitor, LiveStatus
from src.config import config

# 전역 프로세스 변수
curl_process = None
ffmpeg_process = None
recording_active = False

def signal_handler(sig, frame):
    """시그널 핸들러"""
    global curl_process, ffmpeg_process, recording_active
    print(f"\n⚠️ 시그널 받음: {sig}")
    recording_active = False
    
    if curl_process:
        print("🛑 curl 프로세스 종료 중...")
        curl_process.terminate()
    
    if ffmpeg_process:
        print("🛑 FFmpeg 프로세스 종료 중...")
        ffmpeg_process.terminate()
    
    print("👋 테스트 종료")
    sys.exit(0)

async def test_curl_ffmpeg_recording():
    """curl + FFmpeg로 치지직 스트림 녹화 테스트"""
    global curl_process, ffmpeg_process, recording_active
    
    print("🧪 curl + FFmpeg 치지직 녹화 테스트")
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
        filename = f"{timestamp}_curl_ffmpeg_{stream_info.title.replace(' ', '_')}.mp4"
        safe_filename = "".join(c for c in filename if c.isalnum() or c in "._-")
        
        # 출력 디렉터리 생성
        output_dir = Path("test_recordings")
        output_dir.mkdir(exist_ok=True)
        output_path = output_dir / safe_filename
        
        print(f"💾 저장 경로: {output_path}")
        
        # curl 명령어 구성 (HTTPS 스트림 다운로드)
        curl_cmd = [
            "curl",
            "-s",  # silent
            "-L",  # follow redirects
            "-H", f"Cookie: NID_AUT={nid_aut}; NID_SES={nid_ses}",
            "-H", "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "-H", "Referer: https://chzzk.naver.com/",
            stream_info.hls_url
        ]
        
        # FFmpeg 명령어 구성 (stdin에서 HLS 데이터 읽기)
        ffmpeg_cmd = [
            "ffmpeg",
            "-i", "pipe:0",  # stdin에서 입력
            "-c", "copy",    # 스트림 복사 (재인코딩 없음)
            "-f", "mp4",
            "-movflags", "+faststart",  # 스트리밍 최적화
            "-y",  # 파일 덮어쓰기
            str(output_path)
        ]
        
        print(f"🎬 명령어: curl [options] [URL] | ffmpeg -i pipe:0 [options] output.mp4")
        print("⏱️ 10초간 녹화 테스트 시작...")
        
        # curl 프로세스 시작
        recording_active = True
        curl_process = subprocess.Popen(
            curl_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=0  # unbuffered
        )
        
        # FFmpeg 프로세스 시작 (curl의 stdout을 stdin으로)
        ffmpeg_process = subprocess.Popen(
            ffmpeg_cmd,
            stdin=curl_process.stdout,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=0
        )
        
        # curl의 stdout을 닫기 (FFmpeg이 제어)
        curl_process.stdout.close()
        
        # 10초 대기
        start_time = asyncio.get_event_loop().time()
        while recording_active and (asyncio.get_event_loop().time() - start_time) < 10:
            # 프로세스 상태 확인
            if curl_process.poll() is not None and ffmpeg_process.poll() is not None:
                break
            await asyncio.sleep(0.5)
        
        # 프로세스 정리
        if curl_process and curl_process.poll() is None:
            print("🛑 curl 프로세스 종료 중...")
            curl_process.terminate()
            try:
                curl_process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                curl_process.kill()
        
        if ffmpeg_process and ffmpeg_process.poll() is None:
            print("🛑 FFmpeg 프로세스 종료 중...")
            ffmpeg_process.terminate()
            try:
                ffmpeg_process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                ffmpeg_process.kill()
        
        # 결과 확인
        if curl_process and ffmpeg_process:
            curl_stdout, curl_stderr = curl_process.communicate()
            ffmpeg_stdout, ffmpeg_stderr = ffmpeg_process.communicate()
            
            print(f"\n📊 curl 종료 코드: {curl_process.returncode}")
            print(f"📊 FFmpeg 종료 코드: {ffmpeg_process.returncode}")
            
            if curl_process.returncode == 0 and ffmpeg_process.returncode == 0:
                print("✅ curl + FFmpeg 실행 성공!")
            else:
                print("❌ 실행 실패")
                if curl_process.returncode != 0:
                    print(f"curl 오류: {curl_stderr.decode()[:300]}...")
                if ffmpeg_process.returncode != 0:
                    print(f"FFmpeg 오류: {ffmpeg_stderr.decode()[:300]}...")
        
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
        if curl_process and curl_process.poll() is None:
            curl_process.terminate()
        if ffmpeg_process and ffmpeg_process.poll() is None:
            ffmpeg_process.terminate()

if __name__ == "__main__":
    asyncio.run(test_curl_ffmpeg_recording()) 