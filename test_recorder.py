"""
치지직 녹화 엔진 테스트 스크립트
"""

import asyncio
import logging
import os
import time
from pathlib import Path
from dotenv import load_dotenv

from src.chzzk_recorder import (
    LiveMonitor, StreamInfo, LiveStatus,
    StreamRecorder, RecordingInfo, RecordingStatus
)
from src.config import config


# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('test_recorder.log', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)


async def on_recording_start(recording_info: RecordingInfo):
    """녹화 시작 콜백"""
    logger.info("🎬 녹화 시작!")
    logger.info(f"📁 파일: {recording_info.file_path.name}")
    logger.info(f"📺 제목: {recording_info.stream_info.title}")
    logger.info(f"⏰ 시작 시간: {recording_info.started_at}")


async def on_recording_stop(recording_info: RecordingInfo):
    """녹화 종료 콜백"""
    logger.info("🛑 녹화 종료!")
    logger.info(f"📁 파일: {recording_info.file_path.name}")
    logger.info(f"📊 파일 크기: {recording_info.file_size / 1024 / 1024:.1f}MB")
    if recording_info.duration:
        logger.info(f"⏱️  녹화 시간: {recording_info.duration}")


async def on_recording_error(recording_info: RecordingInfo, error: Exception):
    """녹화 오류 콜백"""
    logger.error("❌ 녹화 오류!")
    logger.error(f"📁 파일: {recording_info.file_path.name}")
    logger.error(f"🚨 오류: {error}")


def test_ffmpeg_installation():
    """FFmpeg 설치 확인"""
    logger.info("=== FFmpeg 설치 확인 ===")
    
    ffmpeg_path = config.system.ffmpeg_path
    is_installed = StreamRecorder.check_ffmpeg(ffmpeg_path)
    
    if is_installed:
        logger.info(f"✅ FFmpeg 설치됨: {ffmpeg_path}")
        return True
    else:
        logger.error(f"❌ FFmpeg 설치되지 않음: {ffmpeg_path}")
        logger.error("FFmpeg를 설치해주세요:")
        logger.error("  Windows: https://ffmpeg.org/download.html")
        logger.error("  macOS: brew install ffmpeg")
        logger.error("  Linux: sudo apt install ffmpeg")
        return False


async def test_live_stream_recording():
    """실제 방송 스트림 녹화 테스트"""
    logger.info("=== 실제 방송 스트림 녹화 테스트 ===")
    
    # 환경변수 로드
    load_dotenv()
    
    channel_id = os.getenv("CHZZK_CHANNEL_ID")
    nid_aut = os.getenv("NID_AUT")
    nid_ses = os.getenv("NID_SES")
    
    if not all([channel_id, nid_aut, nid_ses]):
        logger.error("환경변수가 설정되지 않았습니다. .env 파일을 확인하세요.")
        return False
    
    try:
        # 방송 상태 확인
        monitor = LiveMonitor(channel_id, nid_aut, nid_ses)
        stream_info = await monitor.check_live_status()
        
        if not stream_info.is_live:
            logger.warning("현재 방송하지 않습니다. 테스트용 스트림 정보를 생성합니다.")
            # 테스트용 가짜 스트림 정보 (실제로는 녹화되지 않음)
            stream_info = StreamInfo(
                channel_id=channel_id,
                status=LiveStatus.ONLINE,
                title="테스트 녹화",
                streamer_name="테스트스트리머",
                hls_url="https://example.com/test.m3u8"  # 테스트용 가짜 URL
            )
            logger.info("⚠️  테스트용 스트림 정보로 진행합니다 (실제 녹화되지 않음)")
        else:
            logger.info("✅ 방송 중인 스트림을 발견했습니다!")
            logger.info(f"📺 제목: {stream_info.title}")
            logger.info(f"🔗 HLS URL: {stream_info.hls_url}")
        
        # 녹화기 초기화
        recorder = StreamRecorder(
            output_directory=config.recording.recording_path,
            ffmpeg_path=config.system.ffmpeg_path,
            quality=config.recording.quality
        )
        
        # 콜백 설정
        recorder.set_callbacks(
            on_start=on_recording_start,
            on_stop=on_recording_stop,
            on_error=on_recording_error
        )
        
        # 파일명 생성
        filename = config.recording.generate_filename(stream_info)
        logger.info(f"📁 생성될 파일명: {filename}")
        
        if stream_info.is_live and stream_info.hls_url:
            # 실제 녹화 테스트
            print("\n실제 녹화를 진행하시겠습니까? (y/N): ", end="")
            user_input = input().strip().lower()
            
            if user_input == 'y':
                logger.info("🎬 녹화를 시작합니다...")
                
                try:
                    # 녹화 시작
                    recording_info = await recorder.start_recording(stream_info, filename)
                    
                    # 10초간 녹화
                    logger.info("⏰ 10초간 녹화합니다...")
                    await asyncio.sleep(10)
                    
                    # 녹화 중지
                    final_info = await recorder.stop_recording()
                    
                    if final_info and final_info.file_path.exists():
                        logger.info("✅ 녹화 테스트 성공!")
                        return True
                    else:
                        logger.error("❌ 녹화 파일이 생성되지 않았습니다.")
                        return False
                        
                except Exception as e:
                    logger.error(f"❌ 녹화 테스트 실패: {e}")
                    return False
                finally:
                    await recorder.cleanup()
            else:
                logger.info("녹화 테스트를 건너뜁니다.")
                return True
        else:
            logger.info("방송 중이 아니므로 실제 녹화 테스트를 건너뜁니다.")
            return True
            
    except Exception as e:
        logger.error(f"테스트 중 오류 발생: {e}")
        return False


async def test_recorder_basic_functions():
    """녹화기 기본 기능 테스트"""
    logger.info("=== 녹화기 기본 기능 테스트 ===")
    
    try:
        # 녹화기 초기화
        test_output_dir = Path("./test_recordings")
        recorder = StreamRecorder(
            output_directory=test_output_dir,
            ffmpeg_path=config.system.ffmpeg_path
        )
        
        logger.info(f"✅ 녹화기 초기화 성공: {test_output_dir}")
        
        # 출력 디렉터리 확인
        if test_output_dir.exists():
            logger.info("✅ 출력 디렉터리 생성됨")
        else:
            logger.error("❌ 출력 디렉터리 생성 실패")
            return False
        
        # 현재 녹화 상태 확인
        current = recorder.get_current_recording()
        is_recording = recorder.is_recording()
        
        logger.info(f"✅ 현재 녹화 정보: {current}")
        logger.info(f"✅ 녹화 중 여부: {is_recording}")
        
        # 정리
        await recorder.cleanup()
        
        # 테스트 디렉터리 정리
        if test_output_dir.exists() and not any(test_output_dir.iterdir()):
            test_output_dir.rmdir()
            logger.info("🧹 테스트 디렉터리 정리 완료")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 기본 기능 테스트 실패: {e}")
        return False


async def main():
    """메인 함수"""
    logger.info("치지직 녹화 엔진 테스트 시작")
    
    # 필요한 디렉터리 생성
    config.create_directories()
    
    tests = [
        ("FFmpeg 설치 확인", test_ffmpeg_installation),
        ("녹화기 기본 기능", test_recorder_basic_functions),
        ("실제 방송 녹화", test_live_stream_recording),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"테스트: {test_name}")
        logger.info('='*50)
        
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
                
            results.append((test_name, result))
            
            if result:
                logger.info(f"✅ {test_name} 성공")
            else:
                logger.error(f"❌ {test_name} 실패")
                
        except Exception as e:
            logger.error(f"❌ {test_name} 오류: {e}")
            results.append((test_name, False))
    
    # 결과 요약
    logger.info(f"\n{'='*50}")
    logger.info("테스트 결과 요약")
    logger.info('='*50)
    
    success_count = 0
    for test_name, result in results:
        status = "✅ 성공" if result else "❌ 실패"
        logger.info(f"{test_name}: {status}")
        if result:
            success_count += 1
    
    logger.info(f"\n전체: {len(results)}개 중 {success_count}개 성공")
    
    if success_count == len(results):
        logger.info("🎉 모든 테스트 통과!")
    else:
        logger.warning("⚠️ 일부 테스트 실패")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("테스트 중단됨")
    except Exception as e:
        logger.error(f"예상치 못한 오류: {e}")
        raise 