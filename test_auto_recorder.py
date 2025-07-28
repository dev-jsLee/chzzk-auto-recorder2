"""
치지직 자동 녹화 시스템 통합 테스트 스크립트
"""

import asyncio
import logging  
import os
import time
from pathlib import Path
from dotenv import load_dotenv

from src.chzzk_recorder.auto_recorder import ChzzkAutoRecorder, AutoRecorderError
from src.chzzk_recorder import RecordingInfo, LiveStatus, StreamInfo
from src.config import config


# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('test_auto_recorder.log', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)


# 테스트 상태 추적
test_stats = {
    "status_changes": 0,
    "recording_starts": 0,
    "recording_stops": 0,
    "errors": 0,
    "last_recording_info": None
}


async def on_recording_start(recording_info: RecordingInfo):
    """녹화 시작 콜백"""
    test_stats["recording_starts"] += 1
    test_stats["last_recording_info"] = recording_info
    
    logger.info("🎬 자동 녹화 시작!")
    logger.info(f"📁 파일: {recording_info.file_path.name}")
    logger.info(f"📺 제목: {recording_info.stream_info.title}")
    logger.info(f"🏷️  카테고리: {recording_info.stream_info.category or '없음'}")
    logger.info(f"👤 스트리머: {recording_info.stream_info.streamer_name}")
    logger.info(f"🔗 HLS URL: {recording_info.stream_info.hls_url}")


async def on_recording_stop(recording_info: RecordingInfo):
    """녹화 종료 콜백"""
    test_stats["recording_stops"] += 1
    test_stats["last_recording_info"] = recording_info
    
    duration_str = str(recording_info.duration) if recording_info.duration else "알 수 없음"
    size_mb = recording_info.file_size / 1024 / 1024 if recording_info.file_size > 0 else 0
    
    logger.info("🛑 자동 녹화 완료!")
    logger.info(f"📁 파일: {recording_info.file_path.name}")
    logger.info(f"📊 크기: {size_mb:.1f}MB")
    logger.info(f"⏱️  시간: {duration_str}")
    
    # 파일 존재 확인
    if recording_info.file_path.exists():
        logger.info("✅ 녹화 파일 생성 확인됨")
    else:
        logger.warning("⚠️  녹화 파일이 없습니다")


async def on_status_change(old_status: LiveStatus, new_status: LiveStatus, stream_info: StreamInfo):
    """방송 상태 변경 콜백"""
    test_stats["status_changes"] += 1
    
    logger.info(f"🔄 방송 상태 변경: {old_status.value} → {new_status.value}")
    
    if new_status == LiveStatus.ONLINE:
        logger.info(f"📺 제목: {stream_info.title}")
        logger.info(f"👀 시청자: {stream_info.viewer_count}명")
        if stream_info.hls_url:
            logger.info(f"🔗 HLS URL 확인됨")
        else:
            logger.warning("⚠️  HLS URL이 없습니다")


async def on_error(error: Exception):
    """오류 발생 콜백"""
    test_stats["errors"] += 1
    logger.error(f"❌ 시스템 오류: {error}")


def print_test_stats():
    """테스트 통계 출력"""
    logger.info("=" * 50)
    logger.info("🧪 테스트 통계")
    logger.info("=" * 50)
    logger.info(f"상태 변경 횟수: {test_stats['status_changes']}")
    logger.info(f"녹화 시작 횟수: {test_stats['recording_starts']}")
    logger.info(f"녹화 완료 횟수: {test_stats['recording_stops']}")
    logger.info(f"오류 발생 횟수: {test_stats['errors']}")
    
    if test_stats["last_recording_info"]:
        info = test_stats["last_recording_info"]
        size_mb = info.file_size / 1024 / 1024 if info.file_size > 0 else 0
        logger.info(f"마지막 녹화: {info.file_path.name} ({size_mb:.1f}MB)")


async def test_basic_functionality():
    """기본 기능 테스트"""
    logger.info("=== 자동 녹화 시스템 기본 기능 테스트 ===")
    
    # 환경변수 로드
    load_dotenv()
    
    channel_id = os.getenv("CHZZK_CHANNEL_ID")
    nid_aut = os.getenv("NID_AUT")
    nid_ses = os.getenv("NID_SES")
    
    if not all([channel_id, nid_aut, nid_ses]):
        logger.error("환경변수가 설정되지 않았습니다. .env 파일을 확인하세요.")
        return False
    
    try:
        # 자동 녹화 시스템 초기화
        auto_recorder = ChzzkAutoRecorder(
            channel_id=channel_id,
            nid_aut=nid_aut,
            nid_ses=nid_ses,
            config=config
        )
        
        # 초기화 확인
        logger.info("✅ 자동 녹화 시스템 초기화 성공")
        logger.info(f"📺 채널 ID: {auto_recorder.channel_id}")
        logger.info(f"🔄 실행 중: {auto_recorder.is_running}")
        logger.info(f"📡 현재 상태: {auto_recorder.current_status.value}")
        
        # 콜백 설정
        auto_recorder.set_callbacks(
            on_recording_start=on_recording_start,
            on_recording_stop=on_recording_stop,
            on_status_change=on_status_change,
            on_error=on_error
        )
        
        logger.info("✅ 콜백 설정 완료")
        
        # 상태 요약 정보 확인
        status_summary = auto_recorder.get_status_summary()
        logger.info(f"📊 상태 요약: {status_summary}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 기본 기능 테스트 실패: {e}")
        return False


async def test_short_run():
    """짧은 실행 테스트 (5분)"""
    logger.info("=== 자동 녹화 시스템 짧은 실행 테스트 ===")
    logger.info("⏰ 5분간 실행하여 방송 감지 및 녹화 테스트")
    
    # 환경변수 로드
    load_dotenv()
    
    channel_id = os.getenv("CHZZK_CHANNEL_ID")
    nid_aut = os.getenv("NID_AUT")
    nid_ses = os.getenv("NID_SES")
    
    if not all([channel_id, nid_aut, nid_ses]):
        logger.error("환경변수가 설정되지 않았습니다.")
        return False
    
    try:
        # 자동 녹화 시스템 초기화
        auto_recorder = ChzzkAutoRecorder(
            channel_id=channel_id,
            nid_aut=nid_aut,
            nid_ses=nid_ses,
            config=config
        )
        
        # 콜백 설정
        auto_recorder.set_callbacks(
            on_recording_start=on_recording_start,
            on_recording_stop=on_recording_stop,
            on_status_change=on_status_change,
            on_error=on_error
        )
        
        logger.info("🚀 자동 녹화 시스템 시작...")
        
        # 5분간 실행
        start_task = asyncio.create_task(auto_recorder.start())
        
        # 5분 대기
        await asyncio.sleep(300)  # 5분
        
        logger.info("⏰ 5분 경과, 시스템 중지...")
        await auto_recorder.stop()
        
        # 태스크 정리
        if not start_task.done():
            start_task.cancel()
            try:
                await start_task
            except asyncio.CancelledError:
                pass
        
        # 결과 출력
        print_test_stats()
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 짧은 실행 테스트 실패: {e}")
        return False


async def test_continuous_monitoring():
    """연속 모니터링 테스트 (무한 실행)"""
    logger.info("=== 자동 녹화 시스템 연속 모니터링 테스트 ===")
    logger.info("🔄 Ctrl+C로 중지할 수 있습니다")
    
    # 환경변수 로드
    load_dotenv()
    
    channel_id = os.getenv("CHZZK_CHANNEL_ID")
    nid_aut = os.getenv("NID_AUT")
    nid_ses = os.getenv("NID_SES")
    
    if not all([channel_id, nid_aut, nid_ses]):
        logger.error("환경변수가 설정되지 않았습니다.")
        return False
    
    try:
        # 자동 녹화 시스템 초기화
        auto_recorder = ChzzkAutoRecorder(
            channel_id=channel_id,
            nid_aut=nid_aut,
            nid_ses=nid_ses,
            config=config
        )
        
        # 콜백 설정
        auto_recorder.set_callbacks(
            on_recording_start=on_recording_start,
            on_recording_stop=on_recording_stop,
            on_status_change=on_status_change,
            on_error=on_error
        )
        
        logger.info("🚀 자동 녹화 시스템 시작...")
        logger.info("📡 방송 모니터링 중... (Ctrl+C로 중지)")
        
        # 시스템 시작 (무한 실행)
        await auto_recorder.start()
        
    except KeyboardInterrupt:
        logger.info("🛑 사용자에 의해 중지됨")
        await auto_recorder.stop()
        print_test_stats()
        return True
    except Exception as e:
        logger.error(f"❌ 연속 모니터링 테스트 실패: {e}")
        return False


async def test_config_validation():
    """설정 검증 테스트"""
    logger.info("=== 설정 검증 테스트 ===")
    
    try:
        # 설정 검증
        errors = config.validate()
        
        if errors:
            logger.error("❌ 설정 오류:")
            for error in errors:
                logger.error(f"  - {error}")
            return False
        else:
            logger.info("✅ 설정 검증 통과")
            
        # 디렉터리 생성 테스트
        config.create_directories()
        
        if config.recording.recording_path.exists():
            logger.info(f"✅ 녹화 디렉터리 생성됨: {config.recording.recording_path}")
        else:
            logger.error("❌ 녹화 디렉터리 생성 실패")
            return False
            
        if config.logging.file_path.parent.exists():
            logger.info(f"✅ 로그 디렉터리 생성됨: {config.logging.file_path.parent}")
        else:
            logger.error("❌ 로그 디렉터리 생성 실패")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 설정 검증 테스트 실패: {e}")
        return False


async def main():
    """메인 함수"""
    logger.info("치지직 자동 녹화 시스템 통합 테스트 시작")
    
    while True:
        print("\n" + "="*60)
        print("🧪 치지직 자동 녹화 시스템 통합 테스트")
        print("="*60)
        print("1. 설정 검증 테스트")
        print("2. 기본 기능 테스트")
        print("3. 짧은 실행 테스트 (5분)")
        print("4. 연속 모니터링 테스트 (무한 실행)")
        print("5. 종료")
        
        choice = input("\n선택하세요 (1-5): ").strip()
        
        if choice == "1":
            await test_config_validation()
        elif choice == "2":
            await test_basic_functionality()
        elif choice == "3":
            await test_short_run()
        elif choice == "4":
            await test_continuous_monitoring()
        elif choice == "5":
            logger.info("테스트 종료")
            break
        else:
            print("잘못된 선택입니다.")
        
        input("\n아무 키나 눌러서 계속...")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("테스트 중단됨")
    except Exception as e:
        logger.error(f"예상치 못한 오류: {e}")
        raise 