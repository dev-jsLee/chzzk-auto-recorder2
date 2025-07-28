"""
치지직 자동 녹화 시스템
"""

from .monitor import LiveMonitor, LiveStatus, StreamInfo
from .recorder import StreamRecorder, RecordingStatus, RecordingInfo
from .auto_recorder import ChzzkAutoRecorder, AutoRecorderError

__version__ = "0.1.0"
__all__ = [
    "LiveMonitor", "LiveStatus", "StreamInfo",
    "StreamRecorder", "RecordingStatus", "RecordingInfo",
    "ChzzkAutoRecorder", "AutoRecorderError"
] 