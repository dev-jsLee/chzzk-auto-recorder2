"""
치지직 자동 녹화 시스템 설정
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import logging
import re
from datetime import datetime


@dataclass
class RecordingConfig:
    """녹화 관련 설정"""
    # 녹화 파일 저장 경로
    recording_path: Path = Path("./recordings")
    
    # 녹화 품질 (1080p, 720p, 480p, 360p, 144p, best, worst)
    quality: str = "1080p"
    
    # 방송 상태 확인 주기 (초)
    polling_interval: int = 180
    
    # 파일명 형식 (사용 가능한 변수: {date}, {time}, {category}, {title}, {streamer})
    # 카테고리가 없는 경우 자동으로 제외됨
    filename_format: str = "{date}_{category}_{title}"
    
    # 날짜 형식 (strftime 형식)
    date_format: str = "%Y%m%d_%H%M%S"

    def generate_filename(self, stream_info, extension: str = "mp4") -> str:
        """
        방송 정보를 바탕으로 파일명 생성
        
        Args:
            stream_info: 방송 정보
            extension: 파일 확장자
            
        Returns:
            생성된 파일명
        """
        # 기본 변수들
        now = datetime.now()
        variables = {
            "date": now.strftime(self.date_format),
            "time": now.strftime("%H%M%S"),
            "streamer": self._safe_filename(stream_info.streamer_name or "unknown"),
            "title": self._safe_filename(stream_info.title or "untitled"),
        }
        
        # 카테고리가 있는 경우에만 추가
        if stream_info.category and stream_info.category.strip():
            variables["category"] = self._safe_filename(stream_info.category)
            filename = self.filename_format
        else:
            # 카테고리가 없는 경우 제거
            filename = self.filename_format.replace("{category}_", "").replace("_{category}", "")
            filename = filename.replace("{category}", "")  # 혹시 앞뒤에 언더바가 없는 경우
        
        # 변수 치환
        filename = filename.format(**variables)
        
        # 연속된 언더바 정리
        filename = re.sub(r'_+', '_', filename)
        filename = filename.strip('_')
        
        return f"{filename}.{extension}"
    
    def _safe_filename(self, text: str) -> str:
        """파일명에 안전한 문자열로 변환"""
        if not text:
            return "unknown"
        
        # 특수문자 제거 및 공백을 언더바로 변경
        safe = re.sub(r'[<>:"/\\|?*]', '', text)
        safe = re.sub(r'\s+', '_', safe.strip())
        safe = re.sub(r'_+', '_', safe)
        
        # 너무 긴 경우 자르기
        if len(safe) > 50:
            safe = safe[:50]
            
        return safe or "unknown"


@dataclass
class StorageConfig:
    """저장공간 관리 설정"""
    # 최대 저장 용량 (GB, 0이면 무제한)
    max_storage_gb: int = 0
    
    # 오래된 파일 자동 삭제 (일 단위, 0이면 삭제하지 않음)
    auto_delete_days: int = 0
    
    # 임시 파일 정리 주기 (시간 단위)
    temp_cleanup_hours: int = 24


@dataclass
class NotificationConfig:
    """알림 관련 설정"""
    # 알림 활성화 여부
    enabled: bool = True
    
    # 녹화 시작 알림
    notify_start: bool = True
    
    # 녹화 종료 알림
    notify_end: bool = True
    
    # 에러 발생 알림
    notify_error: bool = True


@dataclass
class LoggingConfig:
    """로깅 설정"""
    # 로그 레벨
    level: int = logging.INFO
    
    # 로그 파일 경로
    file_path: Path = Path("./logs/chzzk_recorder.log")
    
    # 로그 파일 최대 크기 (MB)
    max_file_size_mb: int = 10
    
    # 로그 파일 백업 개수
    backup_count: int = 5
    
    # 콘솔 출력 여부
    console_output: bool = True


@dataclass
class SystemConfig:
    """시스템 관련 설정"""
    # ffmpeg 실행 파일 경로
    ffmpeg_path: str = "ffmpeg"
    
    # 녹화 재시도 횟수
    max_retry_count: int = 3
    
    # 네트워크 요청 타임아웃 (초)
    request_timeout: int = 10
    
    # 동시 녹화 가능 수 (향후 다중 채널 지원용)
    max_concurrent_recordings: int = 1


@dataclass
class DockerConfig:
    """Docker 환경 설정"""
    # 컨테이너 내부 녹화 파일 저장 경로
    container_recording_path: Path = Path("/app/recordings")
    
    # 호스트와 공유할 볼륨 경로
    host_volume_path: Path = Path("/data/recordings")
    
    # 컨테이너 내부 로그 경로
    container_log_path: Path = Path("/app/logs")


class Config:
    """통합 설정 클래스"""
    
    def __init__(self):
        self.recording = RecordingConfig()
        self.storage = StorageConfig()
        self.notification = NotificationConfig()
        self.logging = LoggingConfig()
        self.system = SystemConfig()
        self.docker = DockerConfig()
    
    def create_directories(self):
        """필요한 디렉터리 생성"""
        # 녹화 파일 저장 디렉터리
        self.recording.recording_path.mkdir(parents=True, exist_ok=True)
        
        # 로그 파일 디렉터리
        self.logging.file_path.parent.mkdir(parents=True, exist_ok=True)
    
    def validate(self) -> list[str]:
        """설정 유효성 검사"""
        errors = []
        
        # 품질 설정 검사
        valid_qualities = ["1080p", "720p", "480p", "360p", "144p", "best", "worst"]
        if self.recording.quality not in valid_qualities:
            errors.append(f"Invalid quality: {self.recording.quality}. Must be one of {valid_qualities}")
        
        # 폴링 간격 검사
        if self.recording.polling_interval < 5:
            errors.append("Polling interval must be at least 5 seconds")
        
        # 로그 레벨 검사
        valid_log_levels = [logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR]
        if self.logging.level not in valid_log_levels:
            errors.append(f"Invalid log level: {self.logging.level}")
        
        return errors
    
    def get_log_level_name(self) -> str:
        """로그 레벨 이름 반환"""
        levels = {
            logging.DEBUG: "DEBUG",
            logging.INFO: "INFO", 
            logging.WARNING: "WARNING",
            logging.ERROR: "ERROR"
        }
        return levels.get(self.logging.level, "INFO")


# 전역 설정 인스턴스
config = Config() 