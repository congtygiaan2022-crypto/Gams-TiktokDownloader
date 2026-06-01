import logging
import time
import sys
import os
import config
from gemlogin_api import GemLoginAPI
from browser import Browser
from tiktok_manager import TikTokManager
from downloader import Downloader
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json

# Sửa lỗi hiển thị tiếng Việt trên console Windows
try:
    sys.stdout.reconfigure(encoding='utf-8')
except:
    pass

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import functions from main.py
# (Since we are in the same directory, we can import or just redefine for safety in standalone)
from main import extract_video_title, extract_video_stats

def dry_run_test(video_url):
    print(f"\n--- [DRY RUN START] Target: {video_url} ---")
    
    # 1. Khởi tạo Browser
    api = GemLoginAPI()
    browser_handler = Browser(api)
    
    profile_id = config.GEMLOGIN_PROFILE_ID
    logger.info(f"Đang mở profile: {profile_id}...")
    
    driver = browser_handler.start_profile(profile_id)
    if not driver:
        logger.error("Không thể mở trình duyệt.")
        return

    try:
        # 2. Điều hướng tới Video
        logger.info(f"Đang điều hướng tới video...")
        driver.get(video_url)
        time.sleep(5) # Chờ load

        # 3. Trích xuất Caption
        print("\n[STEP 1] Trích xuất Caption:")
        caption = extract_video_title(driver, video_url)
        print(f" > Kết quả: {caption if caption else 'KHÔNG TÌM THẤY'}")

        # 4. Trích xuất Statistics
        print("\n[STEP 2] Trích xuất Thống kê:")
        stats = extract_video_stats(driver)
        if stats:
            print(f" > Likes: {stats['digg_count']}")
            print(f" > Comments: {stats['comment_count']}")
            print(f" > Shares: {stats['share_count']}")
        else:
            print(" > Kết quả: KHÔNG TÌM THẤY")

        # 5. Trích xuất Link Media (Video/Slideshow)
        print("\n[STEP 3] Trích xuất Link Media:")
        extract_data_script = """
            function findMedia(obj) {
                if (!obj || typeof obj !== 'object') return null;
                if (obj.imagePost && obj.imagePost.images) {
                    return { type: 'slideshow', count: obj.imagePost.images.length };
                }
                if (obj.playAddr && obj.playAddr.urlList) {
                    return { type: 'video', url: obj.playAddr.urlList[0] };
                }
                for (let key in obj) {
                    if (key === 'webapp.user-detail') continue;
                    let res = findMedia(obj[key]);
                    if (res) return res;
                }
                return null;
            }
            try {
                let el = document.getElementById("__UNIVERSAL_DATA_FOR_REHYDRATION__");
                let data = JSON.parse(el.textContent);
                return findMedia(data);
            } catch(e) { return null; }
        """
        media = driver.execute_script(extract_data_script)
        if media:
            if media['type'] == 'slideshow':
                print(f" > Loại: SLIDESHOW ({media['count']} ảnh)")
            else:
                print(f" > Loại: VIDEO")
                print(f" > Link: {media['url'][:100]}...")
        else:
            print(" > Kết quả: KHÔNG TRÍCH XUẤT ĐƯỢC LINK TRỰC TIẾP")

    finally:
        print("\n--- [DRY RUN FINISH] ---")
        logger.info("Đang đóng trình duyệt...")
        browser_handler.close()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        target = sys.argv[1]
    else:
        target = input("Nhập URL TikTok để TEST: ").strip()
    
    if target:
        dry_run_test(target)
    else:
        print("URL không hợp lệ.")
