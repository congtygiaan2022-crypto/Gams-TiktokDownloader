import logging
import time
import sys
import os
import re
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_video_url_from_kituchat(driver, video_url):
    """Sử dụng kituchat.net để lấy link video không logo."""
    try:
        logger.info(f"Đang thử KituCHAT cho: {video_url}")
        driver.get("https://kituchat.net/tai-video-tiktok/")
        time.sleep(2)
        
        input_el = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "params")))
        input_el.clear()
        input_el.send_keys(video_url)
        
        btn_tai_ve = driver.find_element(By.CSS_SELECTOR, ".btn-submit")
        btn_tai_ve.click()
        
        logger.info("Đang chờ kết quả từ KituCHAT...")
        time.sleep(5)
        
        all_btns = driver.find_elements(By.CSS_SELECTOR, ".result button, .result a, .btn-first, button.btn")
        
        # Priority 1: NO WATERMARK(HD)
        for btn in all_btns:
            try:
                text = btn.text.strip().upper()
                if "NO WATERMARK(HD)" in text or "KHÔNG LOGO (HD)" in text:
                    href = btn.get_attribute("href")
                    if href and href.startswith("http") and not (href.startswith("https://www.tiktok.com/") or "/video/" in href):
                        logger.info(f"✓ THÀNH CÔNG (ƯU TIÊN 1): Tìm thấy {text} qua href")
                        return href
                    onclick = btn.get_attribute("onclick")
                    if onclick:
                        match = re.search(r"['\"](https?://[^'\"]+)['\"]", onclick)
                        if match:
                            link = match.group(1)
                            logger.info(f"✓ THÀNH CÔNG (ƯU TIÊN 1): Tìm thấy {text} qua onclick")
                            return link
            except: continue

        # Priority 2: NO WATERMARK
        for btn in all_btns:
            try:
                text = btn.text.strip().upper()
                if "NO WATERMARK" in text and "(HD)" not in text:
                    href = btn.get_attribute("href")
                    if href and href.startswith("http") and not (href.startswith("https://www.tiktok.com/") or "/video/" in href):
                        logger.info(f"✓ THÀNH CÔNG (ƯU TIÊN 2): Tìm thấy {text} qua href")
                        return href
                    onclick = btn.get_attribute("onclick")
                    if onclick:
                        match = re.search(r"['\"](https?://[^'\"]+)['\"]", onclick)
                        if match:
                            link = match.group(1)
                            logger.info(f"✓ THÀNH CÔNG (ƯU TIÊN 2): Tìm thấy {text} qua onclick")
                            return link
            except: continue
        return None
    except Exception as e:
        logger.error(f"Lỗi KituCHAT: {e}")
        return None

def get_video_url_from_lovetik(driver, video_url):
    """Sử dụng vi.lovetik.com để lấy link video không logo."""
    try:
        logger.info(f"Đang thử Lovetik cho: {video_url}")
        driver.get("https://vi.lovetik.com/")
        time.sleep(2)
        
        input_el = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "k__input")))
        input_el.clear()
        input_el.send_keys(video_url)
        
        btn_start = driver.find_element(By.ID, "btn-start")
        btn_start.click()
        
        logger.info("Đang chờ kết quả từ Lovetik...")
        time.sleep(5)
        
        # Priorities
        priorities = ["MP4 HD ORIGINAL", "MP4 HD 1080P", "MP4 720P", "NO WATERMARK", "HD"]
        
        rows = driver.find_elements(By.CSS_SELECTOR, ".result_list tr, .result_list li, tr, li")
        for priority in priorities:
            for row in rows:
                try:
                    row_text = " ".join(row.text.upper().split())
                    if "WATERMARK" in row_text and "NO" not in row_text: continue
                    if priority in row_text:
                        link_el = row.find_element(By.TAG_NAME, "a")
                        href = link_el.get_attribute("href")
                        if href and not (href.startswith("https://www.tiktok.com/") or "/video/" in href):
                            logger.info(f"✓ THÀNH CÔNG: Tìm thấy {priority} từ hàng: {row_text.replace('\n', ' ')}")
                            return href
                except: continue
        return None
    except Exception as e:
        logger.error(f"Lỗi Lovetik: {e}")
        return None

def main():
    test_url = input("Nhập URL TikTok để test (mặc định là video mẫu): ")
    if not test_url:
        test_url = "https://www.tiktok.com/@kenh14official/video/7639660001983761672"
    
    print("\n--- BẮT ĐẦU GIẢ LẬP TẢI VÀ KIỂM TRA ---")
    
    # Ở đây chúng tôi dùng Chrome driver mặc định, user cần có webdriver trong PATH
    # Nếu user dùng GemLogin/GPM thì code này sẽ cần chỉnh lại 1 chút, 
    # nhưng đây là bản test nhanh.
    try:
        options = webdriver.ChromeOptions()
        # options.add_argument("--headless") # Chạy ẩn nếu muốn
        driver = webdriver.Chrome(options=options)
        
        # Test KituCHAT
        link_k = get_video_url_from_kituchat(driver, test_url)
        if link_k:
            print(f"\n[KituCHAT] Link không logo: {link_k[:100]}...")
        else:
            print("\n[KituCHAT] KHÔNG tìm thấy link không logo.")
            
        # Test Lovetik
        link_l = get_video_url_from_lovetik(driver, test_url)
        if link_l:
            print(f"\n[Lovetik] Link không logo: {link_l[:100]}...")
        else:
            print("\n[Lovetik] KHÔNG tìm thấy link không logo.")
            
        driver.quit()
        print("\n--- HOÀN THÀNH KIỂM TRA ---")
        
    except Exception as e:
        print(f"Lỗi khi chạy trình duyệt: {e}")
        print("Vui lòng đảm bảo bạn đã cài đặt Chrome và chromedriver tương ứng.")

if __name__ == "__main__":
    main()
