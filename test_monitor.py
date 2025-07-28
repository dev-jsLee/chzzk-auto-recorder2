"""
치지직 방송 모니터링 테스트 스크립트
"""

import asyncio
import logging
import os
from datetime import datetime
from dotenv import load_dotenv

from src.chzzk_recorder.monitor import LiveMonitor, LiveStatus, StreamInfo
from src.config import config


# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('test_monitor.log', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)


async def on_live_start(stream_info: StreamInfo):
    """방송 시작 시 호출되는 콜백"""
    logger.info("🔴 방송 시작!")
    logger.info(f"📺 제목: {stream_info.title}")
    logger.info(f"🏷️  카테고리: {stream_info.category}")
    logger.info(f"👤 스트리머: {stream_info.streamer_name}")
    logger.info(f"👀 시청자 수: {stream_info.viewer_count}명")
    logger.info(f"⏰ 시작 시간: {stream_info.started_at}")
    
    # 파일명 생성 테스트
    filename = config.recording.generate_filename(stream_info)
    logger.info(f"📁 생성될 파일명: {filename}")


async def on_live_end(stream_info: StreamInfo):
    """방송 종료 시 호출되는 콜백"""
    logger.info("⏹️  방송 종료!")
    logger.info(f"📺 제목: {stream_info.title}")


async def on_status_change(old_status: LiveStatus, new_status: LiveStatus, stream_info: StreamInfo):
    """상태 변경 시 호출되는 콜백"""
    logger.info(f"🔄 상태 변경: {old_status.value} → {new_status.value}")


async def test_single_check():
    """단일 상태 확인 테스트"""
    logger.info("=== 단일 상태 확인 테스트 ===")
    
    # 환경변수 로드
    load_dotenv()
    
    channel_id = os.getenv("CHZZK_CHANNEL_ID")
    nid_aut = os.getenv("NID_AUT")
    nid_ses = os.getenv("NID_SES")
    
    if not all([channel_id, nid_aut, nid_ses]):
        logger.error("환경변수가 설정되지 않았습니다. .env 파일을 확인하세요.")
        return
    
    monitor = LiveMonitor(channel_id, nid_aut, nid_ses)
    
    try:
        stream_info = await monitor.check_live_status()
        
        logger.info("=== 방송 상태 확인 결과 ===")
        logger.info(f"방송 상태: {stream_info.status.value}")
        
        if stream_info.is_live:
            logger.info(f"📺 제목: {stream_info.title}")
            logger.info(f"🏷️  카테고리: {stream_info.category or '카테고리 정보 없음'}")
            logger.info(f"👤 스트리머: {stream_info.streamer_name}")
            logger.info(f"👀 시청자 수: {stream_info.viewer_count}명")
            logger.info(f"⏰ 시작 시간: {stream_info.started_at}")
            
            # 파일명 생성 테스트
            filename = config.recording.generate_filename(stream_info)
            logger.info(f"📁 생성될 파일명: {filename}")
        else:
            logger.info("현재 방송하지 않음")
            
            # 테스트용 파일명 생성 (오프라인 상태에서도 확인)
            test_stream_info = StreamInfo(
                channel_id=channel_id,
                status=LiveStatus.ONLINE,
                title="테스트 방송 제목",
                category=None,  # 카테고리 없음 테스트
                streamer_name="테스트스트리머"
            )
            test_filename = config.recording.generate_filename(test_stream_info)
            logger.info(f"📁 테스트 파일명 (카테고리 없음): {test_filename}")
            
            # 카테고리 있는 경우 테스트
            test_stream_info.category = "테스트 카테고리"
            test_filename_with_cat = config.recording.generate_filename(test_stream_info)
            logger.info(f"📁 테스트 파일명 (카테고리 있음): {test_filename_with_cat}")
    
    except Exception as e:
        logger.error(f"오류 발생: {e}")


async def test_continuous_monitoring():
    """연속 모니터링 테스트"""
    logger.info("=== 연속 모니터링 테스트 ===")
    logger.info("Ctrl+C로 중지할 수 있습니다.")
    
    # 환경변수 로드
    load_dotenv()
    
    channel_id = os.getenv("CHZZK_CHANNEL_ID")
    nid_aut = os.getenv("NID_AUT")
    nid_ses = os.getenv("NID_SES")
    
    if not all([channel_id, nid_aut, nid_ses]):
        logger.error("환경변수가 설정되지 않았습니다. .env 파일을 확인하세요.")
        return
    
    monitor = LiveMonitor(channel_id, nid_aut, nid_ses)
    last_status = LiveStatus.UNKNOWN
    
    try:
        while True:
            try:
                stream_info = await monitor.check_live_status()
                
                # 상태 변경 시에만 로그 출력
                if stream_info.status != last_status:
                    await on_status_change(last_status, stream_info.status, stream_info)
                    
                    if stream_info.status == LiveStatus.ONLINE and last_status != LiveStatus.ONLINE:
                        await on_live_start(stream_info)
                    elif stream_info.status == LiveStatus.OFFLINE and last_status == LiveStatus.ONLINE:
                        await on_live_end(stream_info)
                    
                    last_status = stream_info.status
                
                # 지정된 간격으로 대기
                await asyncio.sleep(config.recording.polling_interval)
                
            except Exception as e:
                logger.error(f"모니터링 오류: {e}")
                await asyncio.sleep(30)  # 오류 시 30초 대기
                
    except KeyboardInterrupt:
        logger.info("사용자에 의해 중지됨")
    finally:
        await monitor.close()


async def main():
    """메인 함수"""
    logger.info("치지직 방송 모니터링 테스트 시작")
    
    while True:
        print("\n=== 치지직 방송 모니터링 테스트 ===")
        print("1. 단일 상태 확인")
        print("2. 연속 모니터링 (Ctrl+C로 중지)")
        print("3. 종료")
        
        choice = input("선택하세요 (1-3): ").strip()
        
        if choice == "1":
            await test_single_check()
        elif choice == "2":
            await test_continuous_monitoring()
        elif choice == "3":
            logger.info("테스트 종료")
            break
        else:
            print("잘못된 선택입니다.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("프로그램 종료")
    except Exception as e:
        logger.error(f"예상치 못한 오류: {e}")
        raise 