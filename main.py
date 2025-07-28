#!/usr/bin/env python3
"""
치지직 자동 녹화 시스템 메인 실행 파일
"""

import asyncio
import logging
import logging.handlers
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

from src.chzzk_recorder.auto_recorder import ChzzkAutoRecorder, AutoRecorderError
from src.chzzk_recorder import RecordingInfo, LiveStatus, StreamInfo
from src.config import config


def setup_logging():
    """로깅 설정"""
    # 로그 디렉터리 생성
    log_dir = config.logging.file_path.parent
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # 로깅 설정
    handlers = []
    
    # 콘솔 핸들러
    if config.logging.console_output:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(config.logging.level)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        handlers.append(console_handler)
    
    # 파일 핸들러
    file_handler = logging.handlers.RotatingFileHandler(
        config.logging.file_path,
        maxBytes=config.logging.max_file_size_mb * 1024 * 1024,
        backupCount=config.logging.backup_count,
        encoding='utf-8'
    )
    file_handler.setLevel(config.logging.level)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(file_formatter)
    handlers.append(file_handler)
    
    # 루트 로거 설정
    logging.basicConfig(
        level=config.logging.level,
        handlers=handlers,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


async def on_recording_start(recording_info: RecordingInfo):
    """녹화 시작 콜백"""
    logger = logging.getLogger(__name__)
    logger.info("🎬 자동 녹화 시작!")
    logger.info(f"📁 파일: {recording_info.file_path.name}")
    logger.info(f"📺 제목: {recording_info.stream_info.title}")
    logger.info(f"🏷️  카테고리: {recording_info.stream_info.category or '없음'}")
    logger.info(f"👤 스트리머: {recording_info.stream_info.streamer_name}")


async def on_recording_stop(recording_info: RecordingInfo):
    """녹화 종료 콜백"""
    logger = logging.getLogger(__name__)
    duration_str = str(recording_info.duration) if recording_info.duration else "알 수 없음"
    size_mb = recording_info.file_size / 1024 / 1024 if recording_info.file_size > 0 else 0
    
    logger.info("🛑 자동 녹화 완료!")
    logger.info(f"📁 파일: {recording_info.file_path.name}")
    logger.info(f"📊 크기: {size_mb:.1f}MB")
    logger.info(f"⏱️  시간: {duration_str}")


async def on_status_change(old_status: LiveStatus, new_status: LiveStatus, stream_info: StreamInfo):
    """방송 상태 변경 콜백"""
    logger = logging.getLogger(__name__)
    logger.info(f"🔄 방송 상태 변경: {old_status.value} → {new_status.value}")
    
    if new_status == LiveStatus.ONLINE:
        logger.info(f"📺 {stream_info.title}")
        logger.info(f"👀 시청자: {stream_info.viewer_count}명")


async def on_error(error: Exception):
    """오류 발생 콜백"""
    logger = logging.getLogger(__name__)
    logger.error(f"❌ 시스템 오류: {error}")


def load_environment():
    """환경변수 로드 및 검증"""
    logger = logging.getLogger(__name__)
    
    # .env 파일 로드
    load_dotenv()
    
    # 필수 환경변수 확인
    required_vars = ['CHZZK_CHANNEL_ID', 'NID_AUT', 'NID_SES']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error("❌ 필수 환경변수가 설정되지 않았습니다:")
        for var in missing_vars:
            logger.error(f"  - {var}")
        logger.error("\n.env 파일을 확인하고 다음을 설정하세요:")
        logger.error("1. 치지직에 로그인")
        logger.error("2. F12 > Application > Cookies > chzzk.naver.com")
        logger.error("3. NID_AUT, NID_SES 값을 .env에 복사")
        logger.error("4. 모니터링할 채널 ID를 CHZZK_CHANNEL_ID에 설정")
        sys.exit(1)
    
    return {
        'channel_id': os.getenv('CHZZK_CHANNEL_ID'),
        'nid_aut': os.getenv('NID_AUT'),
        'nid_ses': os.getenv('NID_SES')
    }


def print_startup_info(env_vars: dict):
    """시작 정보 출력"""
    logger = logging.getLogger(__name__)
    
    logger.info("=" * 60)
    logger.info("🚀 치지직 자동 녹화 시스템 시작")
    logger.info("=" * 60)
    logger.info(f"📺 모니터링 채널: {env_vars['channel_id']}")
    logger.info(f"📁 녹화 저장 경로: {config.recording.recording_path}")
    logger.info(f"🎬 녹화 품질: {config.recording.quality}")
    logger.info(f"⏰ 폴링 간격: {config.recording.polling_interval}초")
    logger.info(f"🔧 FFmpeg 경로: {config.system.ffmpeg_path}")
    
    # 설정 검증
    errors = config.validate()
    if errors:
        logger.error("❌ 설정 오류:")
        for error in errors:
            logger.error(f"  - {error}")
        sys.exit(1)
    
    logger.info("✅ 설정 검증 완료")
    logger.info("=" * 60)


async def main():
    """메인 함수"""
    # 로깅 설정
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # 환경변수 로드
        env_vars = load_environment()
        
        # 시작 정보 출력
        print_startup_info(env_vars)
        
        # 자동 녹화 시스템 초기화
        auto_recorder = ChzzkAutoRecorder(
            channel_id=env_vars['channel_id'],
            nid_aut=env_vars['nid_aut'],
            nid_ses=env_vars['nid_ses'],
            config=config
        )
        
        # 콜백 설정
        auto_recorder.set_callbacks(
            on_recording_start=on_recording_start,
            on_recording_stop=on_recording_stop,
            on_status_change=on_status_change,
            on_error=on_error
        )
        
        # 시스템 시작
        logger.info("🔄 시스템 시작 중...")
        await auto_recorder.start()
        
    except KeyboardInterrupt:
        logger.info("🛑 사용자에 의해 중단됨")
    except AutoRecorderError as e:
        logger.error(f"❌ 자동 녹화 시스템 오류: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ 예상치 못한 오류: {e}")
        logger.exception("상세한 오류 정보:")
        sys.exit(1)
    finally:
        logger.info("🏁 시스템 종료")


if __name__ == "__main__":
    # Python 3.11+ 버전 확인
    if sys.version_info < (3, 11):
        print("❌ Python 3.11 이상이 필요합니다")
        sys.exit(1)
    
    try:
        # asyncio 이벤트 루프 실행
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 프로그램 중단됨")
    except Exception as e:
        print(f"❌ 실행 오류: {e}")
        sys.exit(1)
