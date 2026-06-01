import json
import logging
import sys
import os

# Sửa lỗi hiển thị tiếng Việt trên console Windows
try:
    sys.stdout.reconfigure(encoding='utf-8')
except:
    pass

def simulate_js_execution(script, mock_html_content):
    """
    Giả lập driver.execute_script bằng cách chạy script JS đơn giản trong Python
    (Ở đây ta dùng logic tương đương của JS nhưng viết bằng Python để verify dữ liệu)
    """
    try:
        data = json.loads(mock_html_content)
    except:
        return "Invalid JSON"

    # Logic của findVideoDesc trong main.py
    def findVideoDesc(obj):
        if not obj or not isinstance(obj, dict): return None
        if 'desc' in obj and ('playAddr' in obj or 'id' in obj or 'author' in obj):
            return obj['desc']
        for key, value in obj.items():
            if key in ['webapp.user-detail', 'userInfo', 'user']: continue
            res = findVideoDesc(value)
            if res: return res
        return None

    # Logic của findStats trong main.py
    def findStats(obj):
        if not obj or not isinstance(obj, dict): return None
        if 'stats' in obj and 'diggCount' in obj['stats']: return obj['stats']
        if 'statistics' in obj and 'diggCount' in obj['statistics']: return obj['statistics']
        for key, value in obj.items():
            res = findStats(value)
            if res: return res
        return None

    # Logic của findMedia trong main.py
    def findMedia(obj):
        if not obj or not isinstance(obj, dict): return None
        if 'imagePost' in obj and 'images' in obj['imagePost']:
            return {'type': 'slideshow', 'images': [img['imageURL']['urlList'][0] for img in obj['imagePost']['images']]}
        if 'playAddr' in obj and 'urlList' in obj['playAddr']:
            return {'type': 'video', 'url': obj['playAddr']['urlList'][0]}
        for key, value in obj.items():
            res = findMedia(value)
            if res: return res
        return None

    if "findVideoDesc" in script:
        return findVideoDesc(data)
    elif "findStats" in script:
        return findStats(data)
    elif "findMedia" in script:
        return findMedia(data)
    return None

# --- MOCK DATA ---
MOCK_SHOP_VIDEO = {
    "__DEFAULT_SCOPE__": {
        "webapp.video-detail": {
            "itemInfo": {
                "itemStruct": {
                    "id": "123456",
                    "desc": "Day la Caption Video That",
                    "playAddr": {"urlList": ["https://video-link.com/v.mp4"]},
                    "stats": {"diggCount": 100, "commentCount": 50}
                }
            }
        },
        "webapp.user-detail": {
            "userInfo": {
                "user": {"desc": "Bio cua Profile (391.5K Likes...)", "id": "user123"}
            }
        }
    }
}

def run_diagnostic():
    print("=== START EXTRACTION LOGIC DIAGNOSTIC ===")
    
    mock_json = json.dumps(MOCK_SHOP_VIDEO)
    
    # Test 1: Caption extraction
    print("\nTest 1: Caption Extraction (Must avoid Bio stats)")
    res_caption = simulate_js_execution("findVideoDesc", mock_json)
    if res_caption == "Day la Caption Video That":
        print("[OK] Success: Correct video caption captured.")
    else:
        print(f"[FAIL] Error: Captured '{res_caption}' instead.")

    # Test 2: Stats extraction
    print("\nTest 2: Statistics Extraction")
    res_stats = simulate_js_execution("findStats", mock_json)
    if res_stats and res_stats.get('diggCount') == 100:
        print(f"[OK] Success: Likes = {res_stats['diggCount']}")
    else:
        print(f"[FAIL] Error: {res_stats}")

    # Test 3: Media extraction
    print("\nTest 3: Media Extraction (Video Link)")
    res_media = simulate_js_execution("findMedia", mock_json)
    if res_media and res_media['type'] == 'video':
        print(f"[OK] Success: Link = {res_media['url']}")
    else:
        print(f"[FAIL] Error: {res_media}")

    print("\n=== DIAGNOSTIC COMPLETE ===")

if __name__ == "__main__":
    run_diagnostic()
