"""
치지직 자동 녹화 시스템 설정 관리
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import logging


@dataclass
class RecordingConfig:
    """녹화 관련 설정"""
    recording_path: Path
    quality: str
    polling_interval: int
    max_duration_hours: int
    
    def generate_filename(self, stream_info, extension: str = "mp4") -> str:
        """스트림 정보를 기반으로 안전한 파일명 생성"""
        from datetime import datetime
        
        # 기본 정보
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        streamer = self._sanitize_filename(stream_info.streamer_name or "Unknown")
        title = self._sanitize_filename(stream_info.title or "No_Title")
        
        # 카테고리가 있고 'Unknown'이 아닌 경우에만 포함
        category = stream_info.category
        if category and category.strip() != "Unknown" and category.strip() != "":
            category_safe = self._sanitize_filename(category)
            filename = f"{timestamp}_{streamer}_{category_safe}_{title}.{extension}"
        else:
            filename = f"{timestamp}_{streamer}_{title}.{extension}"
        
        # 파일명 길이 제한 (255자 - 여유 공간)
        if len(filename) > 200:
            # 제목 부분을 줄임
            max_title_length = 200 - len(f"{timestamp}_{streamer}_.{extension}")
            if category and category.strip() != "Unknown" and category.strip() != "":
                max_title_length -= len(f"_{category_safe}")
            
            title_truncated = title[:max_title_length] if len(title) > max_title_length else title
            
            if category and category.strip() != "Unknown" and category.strip() != "":
                filename = f"{timestamp}_{streamer}_{category_safe}_{title_truncated}.{extension}"
            else:
                filename = f"{timestamp}_{streamer}_{title_truncated}.{extension}"
        
        return filename
    
    def _sanitize_filename(self, filename: str) -> str:
        """파일명에 사용할 수 없는 문자 제거"""
        if not filename:
            return "Unknown"
        
        # Windows/Linux에서 사용할 수 없는 문자들 제거
        unsafe_chars = '<>:"/\\|?*'
        for char in unsafe_chars:
            filename = filename.replace(char, '_')
        
        # 연속된 언더스코어를 하나로 변경
        filename = '_'.join(filter(None, filename.split('_')))
        
        # 앞뒤 공백 및 점 제거
        filename = filename.strip(' .')
        
        return filename or "Unknown"


@dataclass  
class StorageConfig:
    """저장소 관련 설정"""
    recordings_path: Path
    logs_path: Path
    temp_path: Path
    auto_cleanup_days: int


@dataclass
class NotificationConfig:
    """알림 관련 설정"""
    discord_webhook_url: Optional[str]
    telegram_bot_token: Optional[str]
    telegram_chat_id: Optional[str]
    enable_start_notification: bool
    enable_stop_notification: bool
    enable_error_notification: bool


@dataclass
class LoggingConfig:
    """로깅 관련 설정"""
    level: str
    file_path: Path
    max_file_size_mb: int
    backup_count: int
    console_output: bool


@dataclass
class SystemConfig:
    """시스템 관련 설정"""
    ffmpeg_path: str
    max_retries: int
    retry_delay_seconds: int
    health_check_interval: int


@dataclass
class DockerConfig:
    """Docker 관련 설정"""
    container_name: str
    restart_policy: str
    network_mode: str
    log_driver: str


@dataclass
class Config:
    """전체 설정"""
    recording: RecordingConfig
    storage: StorageConfig  
    notification: NotificationConfig
    logging: LoggingConfig
    system: SystemConfig
    docker: DockerConfig
    
    def create_directories(self):
        """필요한 디렉터리 생성"""
        directories = [
            self.recording.recording_path,
            self.storage.recordings_path,
            self.storage.logs_path,
            self.storage.temp_path,
            self.logging.file_path.parent,
        ]
        
        for directory in directories:
            if directory:
                directory.mkdir(parents=True, exist_ok=True)
    
    def validate(self):
        """설정 검증"""
        # 필수 경로 확인
        if not self.recording.recording_path:
            raise ValueError("녹화 저장 경로가 설정되지 않았습니다")
        
        # FFmpeg 경로 확인은 StreamRecorder에서 처리
        
        # 폴링 간격 확인
        if self.recording.polling_interval < 30:
            raise ValueError("폴링 간격은 30초 이상이어야 합니다")


# 기본 설정 생성
config = Config(
    recording=RecordingConfig(
        recording_path=Path("recordings"),
        quality="1080p",
        polling_interval=180,  # 3분
        max_duration_hours=12,
    ),
    storage=StorageConfig(
        recordings_path=Path("recordings"),
        logs_path=Path("logs"),
        temp_path=Path("temp"),
        auto_cleanup_days=30,
    ),
    notification=NotificationConfig(
        discord_webhook_url=os.getenv("DISCORD_WEBHOOK_URL"),
        telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN"),
        telegram_chat_id=os.getenv("TELEGRAM_CHAT_ID"),
        enable_start_notification=True,
        enable_stop_notification=True,
        enable_error_notification=True,
    ),
    logging=LoggingConfig(
        level=logging.INFO,
        file_path=Path("logs/chzzk_recorder.log"),
        max_file_size_mb=50,
        backup_count=5,
        console_output=True,
    ),
    system=SystemConfig(
        ffmpeg_path="ffmpeg",
        max_retries=3,
        retry_delay_seconds=60,
        health_check_interval=300,  # 5분
    ),
    docker=DockerConfig(
        container_name="chzzk-auto-recorder",
        restart_policy="unless-stopped",
        network_mode="bridge",
        log_driver="json-file",
    ),
) 