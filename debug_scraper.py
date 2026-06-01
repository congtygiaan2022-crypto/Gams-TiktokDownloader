from gemlogin_api import GemLoginAPI
from browser import Browser
from selenium.webdriver.common.by import By
import time
import logging
import sys

# Setup logging
logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger(__name__)

def start_browser_session(api, browser_handler, profile_id):
    """Start profile and attach selenium, returning driver."""
    logger.info(f"Starting profile {profile_id}...")
    try:
        result = api.start_profile(profile_id)
        
        debugger_address = result.get('http') or result.get('selenium_remote_debug_address') or result.get('remote_debugging_address')
        driver_path = result.get('driver_path')
        
        if not debugger_address:
            # Fallback for port
            port = result.get('port')
            if port:
                debugger_address = f"127.0.0.1:{port}"
        
        return browser_handler.attach(debugger_address, driver_path=driver_path)
    except Exception as e:
        logger.error(f"Failed to start/attach session: {e}")
        return None

def main():
    api = GemLoginAPI()
    browser_handler = Browser()
    
    profiles = api.get_profiles()
    if not profiles:
        print("No profiles")
        return
        
    profile_id = profiles[0].get('id')
    driver = start_browser_session(api, browser_handler, profile_id)
    
    url = "https://www.tiktok.com/@kenh14official"
    print(f"Scraping TikTok: {url}")
    driver.get(url)
    time.sleep(5)
    
    video_links = []
    max_videos = 15 # Try to get MORE
    scroll_attempts = 0
    
    while len(video_links) < max_videos and scroll_attempts < 5:
        driver.execute_script("window.scrollBy(0, 1000);")
        time.sleep(2)
        elements = driver.find_elements(By.XPATH, "//a[contains(@href, '/video/')]")
        
        current_found = []
        for el in elements:
            href = el.get_attribute('href')
            if href and '/video/' in href:
                 clean_href = href.split('?')[0]
                 current_found.append(clean_href)
                 if clean_href not in video_links:
                     video_links.append(clean_href)
        
        print(f"Scroll {scroll_attempts}: Found {len(current_found)} links on page. Total unique: {len(video_links)}")
        for i, l in enumerate(video_links):
            print(f"  {i+1}: {l}")
            
        scroll_attempts += 1
        
    print("Done.")
    browser_handler.close()
    api.stop_profile(profile_id)

if __name__ == "__main__":
    main()
