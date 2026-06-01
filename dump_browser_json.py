from selenium import webdriver
import time

def dump_browser_json():
    url = "https://www.tiktok.com/@suckhoevn.247/video/7586896734144498951"
    
    options = webdriver.ChromeOptions()
    options.add_argument("--mute-audio")
    
    driver = webdriver.Chrome(options=options)
    
    try:
        driver.get(url)
        time.sleep(5)
        
        script = """
            let el = document.getElementById("__UNIVERSAL_DATA_FOR_REHYDRATION__");
            return el ? el.textContent : null;
        """
        
        json_text = driver.execute_script(script)
        
        if json_text:
            with open("browser_json_dump.txt", "w", encoding="utf-8") as f:
                f.write(json_text)
            print(f"Dumped {len(json_text)} chars to browser_json_dump.txt")
            
            # Quick check
            if "playAddr" in json_text:
                print("✓ 'playAddr' found in text")
            else:
                print("✗ 'playAddr' NOT found in text")
                
            if '"video"' in json_text:
                print("✓ '\"video\"' found in text")
            else:
                print("✗ '\"video\"' NOT found in text")
        else:
            print("Could not get JSON text")
            
    finally:
        driver.quit()

if __name__ == "__main__":
    dump_browser_json()
