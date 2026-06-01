from selenium import webdriver
from selenium.webdriver.common.by import By
import time

def check_type():
    # List of URLs (Mix of potentially working and failing)
    urls = [
        "https://www.tiktok.com/@suckhoevn.247/video/7589603341613780232", # Fail candidate 1
        "https://www.tiktok.com/@suckhoevn.247/video/7586896734144498951", # Fail candidate 2
        "https://www.tiktok.com/@suckhoevn.247/video/7592939411017305351"  # Previously fixed
    ]
    
    options = webdriver.ChromeOptions()
    options.add_argument("--mute-audio")
    
    driver = webdriver.Chrome(options=options)
    
    for url in urls:
        print(f"\nChecking {url}...")
        try:
            driver.get(url)
            time.sleep(8)
            
            # Check for Video Tag
            videos = driver.find_elements(By.TAG_NAME, "video")
            print(f"Video Tags Found: {len(videos)}")
            for v in videos:
                print(f"- Src: {v.get_attribute('src')}")
                
            # Check for Image Slider/Swiper
            images = driver.find_elements(By.CSS_SELECTOR, "div[data-e2e='swiper-slide']")
            if not images:
                 # Try another selector common for slideshows
                 images = driver.find_elements(By.CSS_SELECTOR, ".swiper-slide")
            
            print(f"Swiper/Slideshow Images Found: {len(images)}")
            
            if len(images) > 0:
                print(">>> TYPE: SLIDESHOW DETECTED")
            elif len(videos) > 0:
                print(">>> TYPE: VIDEO DETECTED")
            else:
                print(">>> TYPE: UNKNOWN")
                
        except Exception as e:
            print(f"Error: {e}")
            
    driver.quit()

if __name__ == "__main__":
    check_type()
