"""
HLS URL 추출 디버깅 스크립트
"""

import asyncio
import logging
import os
from dotenv import load_dotenv

from src.chzzk_recorder.monitor import LiveMonitor, StreamInfo, LiveStatus
from src.config import config


# 디버그 로깅 설정
logging.basicConfig(
    level=logging.DEBUG,  # DEBUG 레벨로 설정
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('debug_hls.log', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)


async def debug_hls_extraction():
    """HLS URL 추출 디버깅"""
    logger.info("=== HLS URL 추출 디버깅 시작 ===")
    
    # 환경변수 로드
    load_dotenv()
    
    channel_id = os.getenv("CHZZK_CHANNEL_ID")
    nid_aut = os.getenv("NID_AUT")
    nid_ses = os.getenv("NID_SES")
    
    if not all([channel_id, nid_aut, nid_ses]):
        logger.error("환경변수가 설정되지 않았습니다. .env 파일을 확인하세요.")
        return False
    
    try:
        # 모니터 생성
        monitor = LiveMonitor(channel_id, nid_aut, nid_ses)
        
        logger.info(f"📺 채널 ID: {channel_id}")
        logger.info("🔍 방송 상태 확인 중...")
        
        # 방송 상태 확인
        stream_info = await monitor.check_live_status()
        
        logger.info("=== 방송 정보 ===")
        logger.info(f"상태: {stream_info.status.value}")
        logger.info(f"제목: {stream_info.title}")
        logger.info(f"카테고리: {stream_info.category}")
        logger.info(f"스트리머: {stream_info.streamer_name}")
        logger.info(f"시청자 수: {stream_info.viewer_count}")
        logger.info(f"썸네일 URL: {stream_info.thumbnail_url}")
        logger.info(f"시작 시간: {stream_info.started_at}")
        
        logger.info("=== HLS URL 정보 ===")
        if stream_info.hls_url:
            logger.info(f"✅ HLS URL 찾음: {stream_info.hls_url}")
            
            # HLS URL 유효성 간단 체크
            if ".m3u8" in stream_info.hls_url:
                logger.info("✅ HLS URL 형식이 올바른 것 같습니다 (.m3u8 포함)")
            else:
                logger.warning("⚠️  HLS URL 형식이 이상합니다 (.m3u8 없음)")
                
        else:
            logger.error("❌ HLS URL을 찾을 수 없습니다")
            
            if stream_info.status == LiveStatus.ONLINE:
                logger.error("방송 중인데 HLS URL이 없습니다. API 응답 구조가 변경되었을 수 있습니다.")
            else:
                logger.info("방송 중이 아니므로 HLS URL이 없는 것이 정상입니다.")
        
        # 정리
        await monitor.close()
        return True
        
    except Exception as e:
        logger.error(f"디버깅 중 오류 발생: {e}")
        logger.exception("상세한 오류 정보:")
        return False


async def main():
    """메인 함수"""
    logger.info("치지직 HLS URL 추출 디버깅 도구")
    
    success = await debug_hls_extraction()
    
    if success:
        logger.info("🎉 디버깅 완료!")
        print("\n" + "="*60)
        print("📋 디버깅 결과를 확인하세요:")
        print("- 콘솔 출력에서 실시간 로그 확인")
        print("- debug_hls.log 파일에서 상세 로그 확인")
        print("="*60)
    else:
        logger.error("❌ 디버깅 실패")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("디버깅 중단됨")
    except Exception as e:
        logger.error(f"예상치 못한 오류: {e}")
        raise 