"""
치지직 스트림 녹화 엔진
"""

import asyncio
import logging
import subprocess
import signal
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional, Callable, Any
import time
import os
import shutil

from ..monitor import StreamInfo

logger = logging.getLogger(__name__)


class RecordingStatus(Enum):
    """녹화 상태"""
    IDLE = "idle"           # 대기 중
    STARTING = "starting"   # 시작 중
    RECORDING = "recording" # 녹화 중
    STOPPING = "stopping"  # 중지 중
    STOPPED = "stopped"     # 중지됨
    ERROR = "error"         # 오류 발생


@dataclass
class RecordingInfo:
    """녹화 정보"""
    stream_info: StreamInfo
    file_path: Path
    status: RecordingStatus
    started_at: Optional[datetime] = None
    stopped_at: Optional[datetime] = None
    file_size: int = 0
    duration: Optional[timedelta] = None
    error_message: Optional[str] = None
    
    @property
    def is_recording(self) -> bool:
        """녹화 중인지 확인"""
        return self.status == RecordingStatus.RECORDING
    
    @property
    def is_active(self) -> bool:
        """활성 상태인지 확인 (시작 중이거나 녹화 중)"""
        return self.status in [RecordingStatus.STARTING, RecordingStatus.RECORDING]


class StreamRecorderError(Exception):
    """스트림 녹화 오류"""
    pass


class StreamRecorder:
    """치지직 스트림 녹화기"""
    
    def __init__(self, 
                 output_directory: Path,
                 ffmpeg_path: str = "ffmpeg",
                 quality: str = "best",
                 timeout: int = 30):
        """
        초기화
        
        Args:
            output_directory: 녹화 파일 저장 디렉터리
            ffmpeg_path: FFmpeg 실행 파일 경로
            quality: 녹화 품질 (best, worst, 1080p, 720p 등)
            timeout: FFmpeg 명령 타임아웃 (초)
        """
        self.output_directory = Path(output_directory)
        self.ffmpeg_path = ffmpeg_path
        self.quality = quality
        self.timeout = timeout
        
        # 상태 관리
        self._current_recording: Optional[RecordingInfo] = None
        self._ffmpeg_process: Optional[subprocess.Popen] = None
        self._stop_event = asyncio.Event()
        
        # 콜백 함수들
        self._on_recording_start: Optional[Callable[[RecordingInfo], None]] = None
        self._on_recording_stop: Optional[Callable[[RecordingInfo], None]] = None
        self._on_recording_error: Optional[Callable[[RecordingInfo, Exception], None]] = None
        
        # 출력 디렉터리 생성
        self.output_directory.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"StreamRecorder 초기화: 저장 경로={self.output_directory}")
    
    def set_callbacks(self,
                     on_start: Optional[Callable[[RecordingInfo], None]] = None,
                     on_stop: Optional[Callable[[RecordingInfo], None]] = None,
                     on_error: Optional[Callable[[RecordingInfo, Exception], None]] = None):
        """콜백 함수 설정"""
        self._on_recording_start = on_start
        self._on_recording_stop = on_stop
        self._on_recording_error = on_error
    
    async def start_recording(self, stream_info: StreamInfo, filename: str) -> RecordingInfo:
        """
        녹화 시작
        
        Args:
            stream_info: 방송 정보
            filename: 저장할 파일명
            
        Returns:
            RecordingInfo: 녹화 정보
            
        Raises:
            StreamRecorderError: 녹화 시작 실패
        """
        if self._current_recording and self._current_recording.is_active:
            raise StreamRecorderError("이미 녹화가 진행 중입니다")
        
        if not stream_info.hls_url:
            raise StreamRecorderError("HLS URL이 없습니다")
        
        # 녹화 정보 생성
        file_path = self.output_directory / filename
        recording_info = RecordingInfo(
            stream_info=stream_info,
            file_path=file_path,
            status=RecordingStatus.STARTING,
            started_at=datetime.now()
        )
        
        self._current_recording = recording_info
        logger.info(f"녹화 시작: {filename}")
        
        try:
            # FFmpeg 명령 생성
            ffmpeg_cmd = self._build_ffmpeg_command(stream_info.hls_url, file_path)
            logger.debug(f"FFmpeg 명령: {' '.join(ffmpeg_cmd)}")
            
            # FFmpeg 프로세스 시작
            self._ffmpeg_process = subprocess.Popen(
                ffmpeg_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                bufsize=1
            )
            
            # 프로세스가 정상적으로 시작되었는지 확인
            await asyncio.sleep(2)  # 잠시 대기
            
            if self._ffmpeg_process.poll() is not None:
                # 프로세스가 이미 종료됨
                _, stderr = self._ffmpeg_process.communicate()
                raise StreamRecorderError(f"FFmpeg 시작 실패: {stderr}")
            
            # 상태 업데이트
            recording_info.status = RecordingStatus.RECORDING
            logger.info(f"녹화 시작됨: {filename}")
            
            # 콜백 호출
            if self._on_recording_start:
                self._on_recording_start(recording_info)
            
            # 백그라운드에서 모니터링 시작
            asyncio.create_task(self._monitor_recording(recording_info))
            
            return recording_info
            
        except Exception as e:
            recording_info.status = RecordingStatus.ERROR
            recording_info.error_message = str(e)
            self._current_recording = None
            
            # 녹화 시작 실패 시 콜백 호출
            if self._on_recording_error:
                try:
                    if asyncio.iscoroutinefunction(self._on_recording_error):
                        asyncio.create_task(self._on_recording_error(recording_info, e))
                    else:
                        self._on_recording_error(recording_info, e)
                except Exception as callback_error:
                    logger.error(f"Error callback 실행 중 오류: {callback_error}")
            
            raise StreamRecorderError(f"녹화 시작 실패: {e}")
    
    async def stop_recording(self) -> Optional[RecordingInfo]:
        """
        녹화 중지
        
        Returns:
            RecordingInfo: 녹화 정보 (녹화 중이 아니면 None)
        """
        if not self._current_recording or not self._current_recording.is_active:
            logger.warning("중지할 녹화가 없습니다")
            return None
        
        recording_info = self._current_recording
        recording_info.status = RecordingStatus.STOPPING
        
        logger.info(f"녹화 중지 중: {recording_info.file_path.name}")
        
        try:
            # FFmpeg 프로세스 종료
            if self._ffmpeg_process and self._ffmpeg_process.poll() is None:
                # SIGTERM 전송
                self._ffmpeg_process.terminate()
                
                # 정상 종료 대기 (최대 5초)
                try:
                    self._ffmpeg_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    # 강제 종료
                    logger.warning("FFmpeg 프로세스 강제 종료")
                    self._ffmpeg_process.kill()
                    self._ffmpeg_process.wait()
            
            # 녹화 완료 처리
            recording_info.stopped_at = datetime.now()
            recording_info.status = RecordingStatus.STOPPED
            
            if recording_info.started_at:
                recording_info.duration = recording_info.stopped_at - recording_info.started_at
            
            # 파일 크기 확인
            if recording_info.file_path.exists():
                recording_info.file_size = recording_info.file_path.stat().st_size
                logger.info(f"녹화 완료: {recording_info.file_path.name} "
                           f"({recording_info.file_size / 1024 / 1024:.1f}MB)")
            else:
                logger.warning(f"녹화 파일이 생성되지 않음: {recording_info.file_path}")
            
            # 콜백 호출
            if self._on_recording_stop:
                self._on_recording_stop(recording_info)
            
            return recording_info
            
        except Exception as e:
            recording_info.status = RecordingStatus.ERROR
            recording_info.error_message = str(e)
            
            if self._on_recording_error:
                self._on_recording_error(recording_info, e)
            
            logger.error(f"녹화 중지 중 오류: {e}")
            return recording_info
        
        finally:
            self._current_recording = None
            self._ffmpeg_process = None
    
    async def _monitor_recording(self, recording_info: RecordingInfo):
        """녹화 모니터링"""
        while recording_info.is_active and self._ffmpeg_process:
            await asyncio.sleep(5)  # 5초마다 확인
            
            # 프로세스 상태 확인
            if self._ffmpeg_process.poll() is not None:
                # 프로세스가 종료됨
                _, stderr = self._ffmpeg_process.communicate()
                
                if recording_info.status == RecordingStatus.STOPPING:
                    # 정상적인 중지
                    break
                else:
                    # 예상치 못한 종료
                    error_msg = f"FFmpeg 프로세스 예상치 못한 종료: {stderr}"
                    recording_info.status = RecordingStatus.ERROR
                    recording_info.error_message = error_msg
                    
                    logger.error(error_msg)
                    
                    if self._on_recording_error:
                        self._on_recording_error(recording_info, StreamRecorderError(error_msg))
                    
                    break
            
            # 파일 크기 업데이트
            if recording_info.file_path.exists():
                recording_info.file_size = recording_info.file_path.stat().st_size
    
    def _build_ffmpeg_command(self, hls_url: str, output_path: Path) -> list[str]:
        """FFmpeg 명령 생성"""
        cmd = [
            self.ffmpeg_path,
            "-y",  # 파일 덮어쓰기
            "-i", hls_url,
            "-c", "copy",  # 코덱 복사 (재인코딩 없음)
            "-bsf:a", "aac_adtstoasc",  # AAC 스트림 처리
            "-f", "mp4",
            str(output_path)
        ]
        
        return cmd
    
    def get_current_recording(self) -> Optional[RecordingInfo]:
        """현재 녹화 정보 반환"""
        return self._current_recording
    
    def is_recording(self) -> bool:
        """녹화 중인지 확인"""
        return self._current_recording is not None and self._current_recording.is_active
    
    async def cleanup(self):
        """정리 작업"""
        if self.is_recording():
            await self.stop_recording()
    
    @staticmethod
    def check_ffmpeg(ffmpeg_path: str = "ffmpeg") -> bool:
        """FFmpeg 설치 확인"""
        try:
            result = subprocess.run(
                [ffmpeg_path, "-version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
            return False 