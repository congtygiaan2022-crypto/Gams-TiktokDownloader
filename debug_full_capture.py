from selenium import webdriver
from selenium.webdriver.common.by import By
import time
import json
import base64

def full_debug():
    url = "https://www.tiktok.com/@suckhoevn.247/video/7592939411017305351"
    options = webdriver.ChromeOptions()
    # options.add_argument("--headless") # Commented out to see if it makes a difference, but run mostly headless if needed.
    # Note: Antigravity browser tool usually runs headless by default if not specified, 
    # but here we rely on the installed chrome.
    options.add_argument("--mute-audio")
    options.add_argument("--window-size=1280,720")
    
    print(f"Opening {url}...")
    try:
        driver = webdriver.Chrome(options=options)
        driver.get(url)
        time.sleep(15) # Wait for everything to load/popup
        
        # 1. Screenshot
        print("Taking screenshot...")
        driver.save_screenshot("debug_page_state.png")
        
        # 2. Check for Login Text
        page_source = driver.page_source.lower()
        if "log in" in page_source or "đăng nhập" in page_source:
             print("STATUS: Login text detected in page source.")
             
        # 3. Dump Network Resources
        print("Scanning resources...")
        resources = driver.execute_script("""
            return performance.getEntriesByType("resource")
                .map(e => e.name)
                .filter(n => n.includes(".mp4") || n.includes("blob:") || n.includes("googlevideo") || n.includes("tiktokcdn"));
        """)
        
        print("--- CONTENT CANDIDATES ---")
        for r in resources:
            print(r)
            
        driver.quit()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    full_debug()
