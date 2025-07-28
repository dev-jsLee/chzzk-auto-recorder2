"""
치지직 방송 상태 모니터링
"""

import asyncio
import logging
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Callable, Any
import re

import httpx
from httpx import AsyncClient


logger = logging.getLogger(__name__)


class LiveStatus(Enum):
    """방송 상태"""
    OFFLINE = "offline"
    ONLINE = "online" 
    UNKNOWN = "unknown"


@dataclass
class StreamInfo:
    """방송 정보"""
    channel_id: str
    status: LiveStatus
    title: Optional[str] = None
    category: Optional[str] = None
    streamer_name: Optional[str] = None
    viewer_count: Optional[int] = None
    thumbnail_url: Optional[str] = None
    hls_url: Optional[str] = None
    started_at: Optional[datetime] = None
    
    @property
    def is_live(self) -> bool:
        """방송 중인지 확인"""
        return self.status == LiveStatus.ONLINE


class ChzzkApiError(Exception):
    """치지직 API 오류"""
    pass


class LiveMonitor:
    """치지직 방송 상태 모니터링"""
    
    # 치지직 API 엔드포인트
    BASE_URL = "https://api.chzzk.naver.com"
    LIVE_STATUS_URL = BASE_URL + "/polling/v2/channels/{channel_id}/live-status"
    LIVE_DETAIL_URL = BASE_URL + "/service/v2/channels/{channel_id}/live-detail"
    CHANNEL_INFO_URL = BASE_URL + "/service/v1/channels/{channel_id}"
    
    def __init__(self, channel_id: str, nid_aut: str, nid_ses: str, timeout: int = 10):
        """
        초기화
        
        Args:
            channel_id: 치지직 채널 ID
            nid_aut: 네이버 인증 쿠키
            nid_ses: 네이버 세션 쿠키  
            timeout: 요청 타임아웃 (초)
        """
        self.channel_id = channel_id
        self.timeout = timeout
        self._last_status = LiveStatus.UNKNOWN
        self._running = False
        
        # HTTP 클라이언트 설정
        self._client = AsyncClient(
            timeout=httpx.Timeout(timeout),
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Referer": "https://chzzk.naver.com/",
            },
            cookies={
                "NID_AUT": nid_aut,
                "NID_SES": nid_ses,
            }
        )
        
        logger.info(f"LiveMonitor 초기화 완료: {channel_id}")
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    async def close(self):
        """리소스 정리"""
        await self._client.aclose()
        logger.info("LiveMonitor 종료")
    
    def _sanitize_filename(self, text: str) -> str:
        """파일명에 사용 불가능한 문자 제거/치환"""
        if not text:
            return "Unknown"
        
        # 특수문자 제거 및 공백을 언더스코어로 치환
        text = re.sub(r'[<>:"/\\|?*]', '', text)
        text = re.sub(r'\s+', '_', text.strip())
        
        # 길이 제한 (Windows 파일명 길이 제한 고려)
        if len(text) > 100:
            text = text[:100]
            
        return text or "Unknown"
    
    async def check_live_status(self) -> StreamInfo:
        """
        현재 방송 상태 확인
        
        Returns:
            StreamInfo: 방송 정보
            
        Raises:
            ChzzkApiError: API 요청 실패
        """
        try:
            # 1. 방송 상태 확인
            status_url = self.LIVE_STATUS_URL.format(channel_id=self.channel_id)
            logger.debug(f"방송 상태 확인: {status_url}")
            
            response = await self._client.get(status_url)
            response.raise_for_status()
            
            status_data = response.json()
            logger.debug(f"상태 응답: {status_data}")
            
            # 방송 상태 판단
            if not status_data.get("content"):
                return StreamInfo(
                    channel_id=self.channel_id,
                    status=LiveStatus.OFFLINE
                )
            
            live_status = status_data["content"].get("status")
            if live_status != "OPEN":
                return StreamInfo(
                    channel_id=self.channel_id, 
                    status=LiveStatus.OFFLINE
                )
            
            # 2. 방송 중이면 상세 정보 가져오기
            return await self._get_live_details()
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP 오류: {e.response.status_code} - {e.response.text}")
            raise ChzzkApiError(f"API 요청 실패: {e.response.status_code}")
        except httpx.TimeoutException:
            logger.error("요청 타임아웃")
            raise ChzzkApiError("요청 타임아웃")
        except Exception as e:
            logger.error(f"예상치 못한 오류: {e}")
            raise ChzzkApiError(f"알 수 없는 오류: {e}")
    
    async def _get_live_details(self) -> StreamInfo:
        """방송 상세 정보 가져오기"""
        detail_url = self.LIVE_DETAIL_URL.format(channel_id=self.channel_id)
        logger.debug(f"방송 상세 정보 확인: {detail_url}")
        
        response = await self._client.get(detail_url)
        response.raise_for_status()
        
        detail_data = response.json()
        content = detail_data.get("content", {})
        
        # 디버그: API 응답 구조 로깅
        logger.debug(f"Live detail response keys: {list(content.keys())}")
        
        if not content:
            return StreamInfo(
                channel_id=self.channel_id,
                status=LiveStatus.OFFLINE
            )
        
        # 방송 정보 추출
        live_title = content.get("liveTitle", "")
        category_value = content.get("categoryValue", "")
        channel_name = content.get("channel", {}).get("channelName", "")
        concurrent_user_count = content.get("concurrentUserCount", 0)
        live_image_url = content.get("liveImageUrl", "")
        
        # HLS URL 추출 (여러 방법으로 시도)
        hls_url = None
        
        # livePlayback 또는 livePlaybackJson 확인
        live_playback = content.get("livePlayback", {})
        live_playback_json = content.get("livePlaybackJson")
        
        logger.debug(f"livePlayback keys: {list(live_playback.keys())}")
        logger.debug(f"livePlaybackJson type: {type(live_playback_json)}")
        
        # livePlaybackJson이 문자열이면 JSON 파싱
        if live_playback_json and isinstance(live_playback_json, str):
            try:
                import json
                live_playback_json_parsed = json.loads(live_playback_json)
                logger.debug(f"Parsed livePlaybackJson keys: {list(live_playback_json_parsed.keys())}")
                live_playback = live_playback_json_parsed
            except json.JSONDecodeError as e:
                logger.warning(f"livePlaybackJson 파싱 실패: {e}")
                logger.debug(f"Raw livePlaybackJson: {live_playback_json}")
        elif live_playback_json and isinstance(live_playback_json, dict):
            logger.debug(f"livePlaybackJson is dict: {list(live_playback_json.keys())}")
            live_playback = live_playback_json
        
        # Method 1: livePlayback.media
        if "media" in live_playback:
            media_list = live_playback["media"]
            logger.debug(f"Found media count: {len(media_list)}")
            
            for media in media_list:
                logger.debug(f"Media item: {media}")
                if media.get("mediaId") == "HLS":
                    hls_url = media.get("path")
                    logger.info(f"HLS URL 발견 (Method 1): {hls_url}")
                    break
        else:
            logger.debug("Found media count: 0")
        
        # Method 2: livePlayback.json.media (기존 방법)
        if not hls_url and "json" in live_playback:
            json_data = live_playback["json"]
            logger.debug(f"Method 2 - json keys: {list(json_data.keys()) if isinstance(json_data, dict) else 'not dict'}")
            
            if isinstance(json_data, dict) and "media" in json_data:
                media_list = json_data["media"]
                for media in media_list:
                    if media.get("mediaId") == "HLS":
                        hls_url = media.get("path")
                        logger.info(f"HLS URL 발견 (Method 2): {hls_url}")
                        break
        
        # Method 3: 재귀적으로 .m3u8 URL 찾기
        if not hls_url:
            logger.debug("Method 3 - 재귀적 HLS URL 검색 시작")
            
            def find_hls_url(obj, path=""):
                nonlocal hls_url
                if hls_url:  # 이미 찾았으면 중단
                    return
                    
                if isinstance(obj, dict):
                    for key, value in obj.items():
                        current_path = f"{path}.{key}" if path else key
                        if isinstance(value, str) and ".m3u8" in value:
                            logger.info(f"HLS URL 발견 (Method 3) at {current_path}: {value}")
                            hls_url = value
                            return
                        elif "hls" in key.lower():
                            logger.debug(f"HLS 관련 키 at {current_path}: {value}")
                        find_hls_url(value, current_path)
                elif isinstance(obj, list):
                    for i, item in enumerate(obj):
                        find_hls_url(item, f"{path}[{i}]")
            
            find_hls_url(live_playback)
        
        if not hls_url:
            logger.warning("HLS URL을 찾을 수 없습니다")
            logger.debug(f"Full livePlayback content: {live_playback}")
            logger.debug(f"Raw livePlaybackJson: {content.get('livePlaybackJson', 'Not found')}")
        else:
            logger.info(f"최종 HLS URL: {hls_url}")
        
        # 시작 시간 (ISO 형식)
        started_at = None
        open_date = content.get("openDate")
        if open_date:
            try:
                started_at = datetime.fromisoformat(open_date.replace('Z', '+00:00'))
            except ValueError:
                logger.warning(f"시작 시간 파싱 실패: {open_date}")
        
        return StreamInfo(
            channel_id=self.channel_id,
            status=LiveStatus.ONLINE,
            title=self._sanitize_filename(live_title),
            category=self._sanitize_filename(category_value),
            streamer_name=self._sanitize_filename(channel_name),
            viewer_count=concurrent_user_count,
            thumbnail_url=live_image_url,
            hls_url=hls_url,
            started_at=started_at
        )
    
    async def start_monitoring(
        self, 
        interval: int,
        on_live_start: Optional[Callable[[StreamInfo], Any]] = None,
        on_live_end: Optional[Callable[[StreamInfo], Any]] = None,
        on_error: Optional[Callable[[Exception], Any]] = None
    ):
        """
        방송 상태 모니터링 시작
        
        Args:
            interval: 확인 주기 (초)
            on_live_start: 방송 시작 시 콜백
            on_live_end: 방송 종료 시 콜백  
            on_error: 오류 발생 시 콜백
        """
        self._running = True
        logger.info(f"방송 모니터링 시작: {self.channel_id} (간격: {interval}초)")
        
        while self._running:
            try:
                stream_info = await self.get_live_status()
                current_status = stream_info.status
                
                # 상태 변화 감지
                if current_status != self._last_status:
                    logger.info(f"방송 상태 변화: {self._last_status.value} -> {current_status.value}")
                    
                    if current_status == LiveStatus.ONLINE and on_live_start:
                        logger.info(f"방송 시작 감지: {stream_info.title}")
                        try:
                            result = on_live_start(stream_info)
                            if asyncio.iscoroutine(result):
                                await result
                        except Exception as e:
                            logger.error(f"방송 시작 콜백 오류: {e}")
                    
                    elif current_status == LiveStatus.OFFLINE and self._last_status == LiveStatus.ONLINE and on_live_end:
                        logger.info("방송 종료 감지")
                        try:
                            result = on_live_end(stream_info)
                            if asyncio.iscoroutine(result):
                                await result
                        except Exception as e:
                            logger.error(f"방송 종료 콜백 오류: {e}")
                    
                    self._last_status = current_status
                
                else:
                    if current_status == LiveStatus.ONLINE:
                        logger.debug(f"방송 중: {stream_info.title} (시청자: {stream_info.viewer_count}명)")
                    else:
                        logger.debug("방송 오프라인")
                
            except Exception as e:
                logger.error(f"모니터링 오류: {e}")
                if on_error:
                    try:
                        result = on_error(e)
                        if asyncio.iscoroutine(result):
                            await result
                    except Exception as callback_error:
                        logger.error(f"오류 콜백 실행 중 오류: {callback_error}")
            
            # 다음 확인까지 대기
            await asyncio.sleep(interval)
        
        logger.info("방송 모니터링 중지")
    
    def stop_monitoring(self):
        """모니터링 중지"""
        self._running = False
        logger.info("모니터링 중지 요청") 