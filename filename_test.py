"""
파일명 생성 테스트 스크립트
"""

from src.chzzk_recorder.monitor import StreamInfo, LiveStatus
from src.config import config


def test_filename_generation():
    """파일명 생성 테스트"""
    print("=== 파일명 생성 테스트 ===\n")
    
    # 테스트 케이스 1: 카테고리가 있는 경우
    stream_info_with_category = StreamInfo(
        channel_id="test_channel",
        status=LiveStatus.ONLINE,
        title="오늘도 솔랭 도전! 다이아 가자!",
        category="리그 오브 레전드",
        streamer_name="테스트스트리머"
    )
    
    filename1 = config.recording.generate_filename(stream_info_with_category)
    print("📁 카테고리가 있는 경우:")
    print(f"   제목: {stream_info_with_category.title}")
    print(f"   카테고리: {stream_info_with_category.category}")
    print(f"   스트리머: {stream_info_with_category.streamer_name}")
    print(f"   생성된 파일명: {filename1}")
    print()
    
    # 테스트 케이스 2: 카테고리가 없는 경우 (None)
    stream_info_no_category = StreamInfo(
        channel_id="test_channel",
        status=LiveStatus.ONLINE,
        title="시청자와 함께하는 잡담방송",
        category=None,
        streamer_name="테스트스트리머2"
    )
    
    filename2 = config.recording.generate_filename(stream_info_no_category)
    print("📁 카테고리가 없는 경우 (None):")
    print(f"   제목: {stream_info_no_category.title}")
    print(f"   카테고리: {stream_info_no_category.category}")
    print(f"   스트리머: {stream_info_no_category.streamer_name}")
    print(f"   생성된 파일명: {filename2}")
    print()
    
    # 테스트 케이스 3: 카테고리가 빈 문자열인 경우
    stream_info_empty_category = StreamInfo(
        channel_id="test_channel",
        status=LiveStatus.ONLINE,
        title="특별한 방송입니다",
        category="",  # 빈 문자열
        streamer_name="테스트스트리머3"
    )
    
    filename3 = config.recording.generate_filename(stream_info_empty_category)
    print("📁 카테고리가 빈 문자열인 경우:")
    print(f"   제목: {stream_info_empty_category.title}")
    print(f"   카테고리: '{stream_info_empty_category.category}'")
    print(f"   스트리머: {stream_info_empty_category.streamer_name}")
    print(f"   생성된 파일명: {filename3}")
    print()
    
    # 테스트 케이스 4: 특수문자가 포함된 경우
    stream_info_special_chars = StreamInfo(
        channel_id="test_channel",
        status=LiveStatus.ONLINE,
        title="<방송제목> \"특수/문자\\테스트\" [대괄호] {중괄호}",
        category="게임/액션",
        streamer_name="특수*문자?스트리머"
    )
    
    filename4 = config.recording.generate_filename(stream_info_special_chars)
    print("📁 특수문자가 포함된 경우:")
    print(f"   제목: {stream_info_special_chars.title}")
    print(f"   카테고리: {stream_info_special_chars.category}")
    print(f"   스트리머: {stream_info_special_chars.streamer_name}")
    print(f"   생성된 파일명: {filename4}")
    print()
    
    # 설정 정보 출력
    print("=== 현재 설정 ===")
    print(f"파일명 형식: {config.recording.filename_format}")
    print(f"날짜 형식: {config.recording.date_format}")


if __name__ == "__main__":
    test_filename_generation() 