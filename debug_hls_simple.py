"""
간단한 HLS URL 디버깅 스크립트
"""

import asyncio
import json
import os
from dotenv import load_dotenv
import httpx

async def debug_chzzk_api():
    """치지직 API 직접 호출해서 HLS URL 확인"""
    print("=== 치지직 HLS URL 디버깅 시작 ===")
    
    # 환경변수 로드  
    load_dotenv()
    
    channel_id = os.getenv("CHZZK_CHANNEL_ID")
    nid_aut = os.getenv("NID_AUT")
    nid_ses = os.getenv("NID_SES")
    
    if not all([channel_id, nid_aut, nid_ses]):
        print("❌ 환경변수가 설정되지 않았습니다.")
        return
    
    print(f"📺 채널 ID: {channel_id}")
    
    # HTTP 클라이언트 설정
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://chzzk.naver.com/",
    }
    
    cookies = {
        "NID_AUT": nid_aut,
        "NID_SES": nid_ses
    }
    
    async with httpx.AsyncClient(headers=headers, cookies=cookies, timeout=10) as client:
        try:
            # 1. 방송 상태 확인
            status_url = f"https://api.chzzk.naver.com/polling/v2/channels/{channel_id}/live-status"
            print(f"\n🔍 방송 상태 확인: {status_url}")
            
            status_response = await client.get(status_url)
            status_data = status_response.json()
            
            print("📊 방송 상태 응답:")
            print(json.dumps(status_data, indent=2, ensure_ascii=False))
            
            if not status_data.get("content"):
                print("❌ 방송 정보가 없습니다")
                return
                
            live_status = status_data["content"].get("status")
            print(f"📡 방송 상태: {live_status}")
            
            if live_status != "OPEN":
                print("📴 방송 중이 아닙니다")
                return
            
            # 2. 방송 상세 정보 확인
            detail_url = f"https://api.chzzk.naver.com/service/v2/channels/{channel_id}/live-detail"
            print(f"\n🔍 상세 정보 확인: {detail_url}")
            
            detail_response = await client.get(detail_url)
            detail_data = detail_response.json()
            
            print("📊 상세 정보 응답:")
            print(json.dumps(detail_data, indent=2, ensure_ascii=False))
            
            content = detail_data.get("content", {})
            if not content:
                print("❌ 상세 정보가 없습니다")
                return
            
            # 3. HLS URL 찾기
            print("\n🔍 HLS URL 찾기:")
            
            live_playback = content.get("livePlayback", {})
            print(f"📁 livePlayback 키들: {list(live_playback.keys())}")
            
            if "media" in live_playback:
                media_list = live_playback["media"]
                print(f"📺 미디어 개수: {len(media_list)}")
                
                for i, media in enumerate(media_list):
                    print(f"미디어 {i}: {media}")
                    
                    if media.get("mediaId") == "HLS":
                        hls_url = media.get("path")
                        print(f"✅ HLS URL 발견: {hls_url}")
                        return
            
            # 다른 방법으로 HLS URL 찾기
            def find_hls_recursively(obj, path=""):
                if isinstance(obj, dict):
                    for key, value in obj.items():
                        current_path = f"{path}.{key}" if path else key
                        if isinstance(value, str) and ".m3u8" in value:
                            print(f"🎯 M3U8 URL 발견 at {current_path}: {value}")
                        elif "hls" in key.lower():
                            print(f"🔍 HLS 관련 키 at {current_path}: {value}")
                        find_hls_recursively(value, current_path)
                elif isinstance(obj, list):
                    for i, item in enumerate(obj):
                        find_hls_recursively(item, f"{path}[{i}]")
            
            print("\n🔍 재귀적 HLS URL 검색:")
            find_hls_recursively(live_playback)
            
            print("\n❌ HLS URL을 찾을 수 없습니다")
            print("📋 전체 livePlayback 내용을 확인하세요")
            
        except Exception as e:
            print(f"❌ 오류 발생: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_chzzk_api()) 