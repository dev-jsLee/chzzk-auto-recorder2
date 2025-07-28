"""
치지직 자동 녹화 시스템
"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Callable
import signal
import sys

from .monitor import LiveMonitor, StreamInfo, LiveStatus
from .recorder import StreamRecorder, RecordingInfo, RecordingStatus
from ..config import Config

logger = logging.getLogger(__name__)


class AutoRecorderError(Exception):
    """자동 녹화 시스템 오류"""
    pass


class ChzzkAutoRecorder:
    """치지직 자동 녹화 시스템"""
    
    def __init__(self, 
                 channel_id: str,
                 nid_aut: str,
                 nid_ses: str,
                 config: Config):
        """
        초기화
        
        Args:
            channel_id: 치지직 채널 ID
            nid_aut: 네이버 인증 쿠키
            nid_ses: 네이버 세션 쿠키
            config: 설정 객체
        """
        self.channel_id = channel_id
        self.config = config
        
        # 모니터링 및 녹화 컴포넌트
        self.monitor = LiveMonitor(channel_id, nid_aut, nid_ses)
        self.recorder = StreamRecorder(
            output_directory=config.recording.recording_path,
            ffmpeg_path=config.system.ffmpeg_path,
            quality=config.recording.quality,
            timeout=config.system.request_timeout
        )
        
        # 상태 관리
        self._running = False
        self._last_status = LiveStatus.UNKNOWN
        self._current_recording: Optional[RecordingInfo] = None
        self._monitor_task: Optional[asyncio.Task] = None
        
        # 콜백 함수들
        self._on_recording_start: Optional[Callable[[RecordingInfo], None]] = None
        self._on_recording_stop: Optional[Callable[[RecordingInfo], None]] = None
        self._on_status_change: Optional[Callable[[LiveStatus, LiveStatus, StreamInfo], None]] = None
        self._on_error: Optional[Callable[[Exception], None]] = None
        
        # 녹화기 콜백 설정
        self.recorder.set_callbacks(
            on_start=self._on_recorder_start,
            on_stop=self._on_recorder_stop,
            on_error=self._on_recorder_error
        )
        
        logger.info(f"자동 녹화 시스템 초기화: 채널={channel_id}")
    
    def set_callbacks(self,
                     on_recording_start: Optional[Callable[[RecordingInfo], None]] = None,
                     on_recording_stop: Optional[Callable[[RecordingInfo], None]] = None,
                     on_status_change: Optional[Callable[[LiveStatus, LiveStatus, StreamInfo], None]] = None,
                     on_error: Optional[Callable[[Exception], None]] = None):
        """콜백 함수 설정"""
        self._on_recording_start = on_recording_start
        self._on_recording_stop = on_recording_stop
        self._on_status_change = on_status_change
        self._on_error = on_error
    
    async def start(self):
        """자동 녹화 시스템 시작"""
        if self._running:
            raise AutoRecorderError("이미 실행 중입니다")
        
        logger.info("🚀 자동 녹화 시스템 시작")
        
        # 필요한 디렉터리 생성
        self.config.create_directories()
        
        # FFmpeg 설치 확인
        if not StreamRecorder.check_ffmpeg(self.config.system.ffmpeg_path):
            raise AutoRecorderError(f"FFmpeg를 찾을 수 없습니다: {self.config.system.ffmpeg_path}")
        
        self._running = True
        
        # 시그널 핸들러 설정 (graceful shutdown)
        if sys.platform != "win32":
            signal.signal(signal.SIGTERM, self._signal_handler)
            signal.signal(signal.SIGINT, self._signal_handler)
        
        # 모니터링 태스크 시작
        self._monitor_task = asyncio.create_task(self._monitor_loop())
        
        try:
            await self._monitor_task
        except asyncio.CancelledError:
            logger.info("모니터링 태스크 취소됨")
        except Exception as e:
            logger.error(f"자동 녹화 중 오류 발생: {e}")
            if self._on_error:
                try:
                    if asyncio.iscoroutinefunction(self._on_error):
                        asyncio.create_task(self._on_error(e))
                    else:
                        self._on_error(e)
                except Exception as callback_error:
                    logger.error(f"Error callback 실행 중 오류: {callback_error}")
            
            # 잠시 대기 후 재시도
            await asyncio.sleep(30)
        finally:
            await self._cleanup()
    
    async def stop(self):
        """자동 녹화 시스템 중지"""
        if not self._running:
            logger.warning("이미 중지된 상태입니다")
            return
        
        logger.info("🛑 자동 녹화 시스템 중지 중...")
        
        self._running = False
        
        # 모니터링 태스크 취소
        if self._monitor_task and not self._monitor_task.done():
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        
        await self._cleanup()
        logger.info("✅ 자동 녹화 시스템 중지 완료")
    
    async def _monitor_loop(self):
        """방송 상태 모니터링 루프"""
        logger.info(f"📡 방송 모니터링 시작 (폴링 간격: {self.config.recording.polling_interval}초)")
        
        while self._running:
            try:
                # 방송 상태 확인
                stream_info = await self.monitor.check_live_status()
                
                # 상태 변경 감지
                if stream_info.status != self._last_status:
                    logger.info(f"🔄 상태 변경: {self._last_status.value} → {stream_info.status.value}")
                    
                    # 콜백 호출
                    if self._on_status_change:
                        self._on_status_change(self._last_status, stream_info.status, stream_info)
                    
                    # 방송 시작 처리
                    if stream_info.status == LiveStatus.ONLINE and self._last_status != LiveStatus.ONLINE:
                        await self._handle_stream_start(stream_info)
                    
                    # 방송 종료 처리
                    elif stream_info.status == LiveStatus.OFFLINE and self._last_status == LiveStatus.ONLINE:
                        await self._handle_stream_stop(stream_info)
                    
                    self._last_status = stream_info.status
                
                # 녹화 상태 로깅 (디버그용)
                if self._current_recording:
                    recording = self._current_recording
                    if recording.is_recording:
                        size_mb = recording.file_size / 1024 / 1024 if recording.file_size > 0 else 0
                        logger.debug(f"📹 녹화 중: {recording.file_path.name} ({size_mb:.1f}MB)")
                
                # 다음 확인까지 대기
                await asyncio.sleep(self.config.recording.polling_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"모니터링 루프 오류: {e}")
                
                if self._on_error:
                    self._on_error(e)
                
                # 오류 시 30초 대기 후 재시도
                await asyncio.sleep(30)
    
    async def _handle_stream_start(self, stream_info: StreamInfo):
        """방송 시작 처리"""
        logger.info("🔴 방송 시작 감지!")
        logger.info(f"📺 제목: {stream_info.title}")
        logger.info(f"🏷️  카테고리: {stream_info.category or '없음'}")
        logger.info(f"👤 스트리머: {stream_info.streamer_name}")
        logger.info(f"👀 시청자 수: {stream_info.viewer_count}명")
        
        # 이미 녹화 중인지 확인
        if self._current_recording and self._current_recording.is_active:
            logger.warning("이미 녹화가 진행 중입니다")
            return
        
        # HLS URL 확인
        if not stream_info.hls_url:
            logger.error("HLS URL을 찾을 수 없습니다")
            return
        
        try:
            # 파일명 생성
            filename = self.config.recording.generate_filename(stream_info)
            logger.info(f"📁 파일명: {filename}")
            
            # 녹화 시작
            self._current_recording = await self.recorder.start_recording(stream_info, filename)
            logger.info("🎬 녹화 시작됨")
            
        except Exception as e:
            logger.error(f"녹화 시작 실패: {e}")
            if self._on_error:
                self._on_error(e)
    
    async def _handle_stream_stop(self, stream_info: StreamInfo):
        """방송 종료 처리"""
        logger.info("⏹️  방송 종료 감지!")
        
        if not self._current_recording or not self._current_recording.is_active:
            logger.info("진행 중인 녹화가 없습니다")
            return
        
        try:
            # 녹화 중지
            final_recording = await self.recorder.stop_recording()
            
            if final_recording:
                logger.info("🛑 녹화 중지됨")
                self._current_recording = None
            
        except Exception as e:
            logger.error(f"녹화 중지 실패: {e}")
            if self._on_error:
                self._on_error(e)
    
    async def _on_recorder_start(self, recording_info: RecordingInfo):
        """녹화 시작 콜백"""
        logger.info(f"🎬 녹화 시작: {recording_info.file_path.name}")
        
        if self._on_recording_start:
            self._on_recording_start(recording_info)
    
    async def _on_recorder_stop(self, recording_info: RecordingInfo):
        """녹화 종료 콜백"""
        duration_str = str(recording_info.duration) if recording_info.duration else "알 수 없음"
        size_mb = recording_info.file_size / 1024 / 1024 if recording_info.file_size > 0 else 0
        
        logger.info(f"🛑 녹화 완료: {recording_info.file_path.name}")
        logger.info(f"📊 파일 크기: {size_mb:.1f}MB")
        logger.info(f"⏱️  녹화 시간: {duration_str}")
        
        if self._on_recording_stop:
            self._on_recording_stop(recording_info)
    
    async def _on_recorder_error(self, recording_info: RecordingInfo, error: Exception):
        """녹화 오류 콜백"""
        logger.error(f"❌ 녹화 오류: {error}")
        logger.error(f"📁 파일: {recording_info.file_path.name}")
        
        self._current_recording = None
        
        if self._on_error:
            self._on_error(error)
    
    def _signal_handler(self, signum, frame):
        """시그널 핸들러 (graceful shutdown)"""
        logger.info(f"시그널 수신: {signum}")
        
        # 비동기 컨텍스트에서 실행
        if self._running:
            asyncio.create_task(self.stop())
    
    async def _cleanup(self):
        """정리 작업"""
        try:
            # 진행 중인 녹화 중지
            if self._current_recording and self._current_recording.is_active:
                logger.info("진행 중인 녹화를 중지합니다...")
                await self.recorder.cleanup()
            
            # 모니터 정리
            await self.monitor.close()
            
        except Exception as e:
            logger.error(f"정리 작업 중 오류: {e}")
    
    @property
    def is_running(self) -> bool:
        """실행 중인지 확인"""
        return self._running
    
    @property
    def current_status(self) -> LiveStatus:
        """현재 방송 상태"""
        return self._last_status
    
    @property
    def current_recording(self) -> Optional[RecordingInfo]:
        """현재 녹화 정보"""
        return self._current_recording
    
    def get_status_summary(self) -> dict:
        """상태 요약 정보"""
        recording_info = None
        if self._current_recording:
            recording_info = {
                "file_name": self._current_recording.file_path.name,
                "status": self._current_recording.status.value,
                "file_size_mb": self._current_recording.file_size / 1024 / 1024,
                "started_at": self._current_recording.started_at.isoformat() if self._current_recording.started_at else None
            }
        
        return {
            "channel_id": self.channel_id,
            "is_running": self._running,
            "stream_status": self._last_status.value,
            "recording_info": recording_info,
            "config": {
                "polling_interval": self.config.recording.polling_interval,
                "recording_path": str(self.config.recording.recording_path),
                "quality": self.config.recording.quality
            }
        } 