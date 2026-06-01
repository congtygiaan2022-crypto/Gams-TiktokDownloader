from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

def test_extraction():
    url = "https://www.tiktok.com/@suckhoevn.247/video/7586896734144498951"  # Slideshow
    
    options = webdriver.ChromeOptions()
    options.add_argument("--mute-audio")
    options.set_capability('goog:loggingPrefs', {'browser': 'ALL'})
    
    driver = webdriver.Chrome(options=options)
    
    try:
        print(f"Loading {url}...")
        driver.get(url)
        
        # Mimic main.py timing
        time.sleep(5)
        
        # Try to find video tag
        try:
            wait = WebDriverWait(driver, 10)
            video_el = wait.until(EC.presence_of_element_located((By.TAG_NAME, "video")))
            print(f"Video tag found, src: {video_el.get_attribute('src')}")
        except:
            print("No video tag found")
        
        # Now try JSON extraction with detailed logging
        script = """
            try {
                console.log("DEBUG: Starting extraction...");
                let el = document.getElementById("__UNIVERSAL_DATA_FOR_REHYDRATION__");
                if (!el) {
                    console.error("DEBUG: Element not found");
                    return "ELEMENT_NOT_FOUND";
                }
                
                let jsonText = el.textContent || el.innerHTML;
                if (!jsonText) {
                    console.error("DEBUG: Empty content");
                    return "EMPTY_CONTENT";
                }
                
                console.log("DEBUG: Parsing JSON...");
                let data = JSON.parse(jsonText);
                console.log("DEBUG: JSON parsed, keys: " + Object.keys(data).join(','));
                
                // Try direct path
                try {
                    let videoData = data["__DEFAULT_SCOPE__"]["webapp.video-detail"].itemInfo.itemStruct.video;
                    if (videoData && videoData.playAddr) {
                        console.log("DEBUG: Found playAddr via direct path");
                        return videoData.playAddr;
                    }
                } catch(e) {
                    console.log("DEBUG: Direct path failed: " + e.message);
                }
                
                // Try recursive search
                console.log("DEBUG: Trying recursive search...");
                function findKey(obj, key) {
                    if (typeof obj !== 'object' || obj === null) return null;
                    if (obj.hasOwnProperty(key)) return obj[key];
                    for (let k in obj) {
                        let res = findKey(obj[k], key);
                        if (res) return res;
                    }
                    return null;
                }
                
                let found = findKey(data, "playAddr");
                if (found) {
                    console.log("DEBUG: Found via recursive search");
                    return found;
                }
                
                console.log("DEBUG: playAddr not found anywhere");
                return "NOT_FOUND";
                
            } catch(e) {
                console.error("DEBUG: Exception: " + e.message);
                return "EXCEPTION: " + e.message;
            }
        """
        
        result = driver.execute_script(script)
        print(f"\nExtraction result: {result}")
        
        # Print console logs
        print("\n--- Browser Console Logs ---")
        for entry in driver.get_log('browser'):
            if "DEBUG" in str(entry['message']):
                print(entry['message'])
        
    finally:
        driver.quit()

if __name__ == "__main__":
    test_extraction()
