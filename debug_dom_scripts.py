from selenium import webdriver
from selenium.webdriver.common.by import By
import json
import time

def check_scripts():
    url = "https://www.tiktok.com/@suckhoevn.247/video/7592939411017305351"
    options = webdriver.ChromeOptions()
    # options.add_argument("--headless")
    options.add_argument("--mute-audio")
    
    print(f"Opening {url}...")
    try:
        driver = webdriver.Chrome(options=options)
        driver.get(url)
        time.sleep(10)
        
        # Check specific IDs often used by TikTok/Next.js/React apps
        ids = ["__UNIVERSAL_DATA_FOR_REHYDRATION__", "SIGI_STATE", "__NEXT_DATA__", "sigi-persisted-data"]
        
        found_data = {}
        
        for i in ids:
            try:
                el = driver.find_element(By.ID, i)
                content = el.get_attribute("innerHTML") or el.get_attribute("textContent")
                print(f"FOUND script with ID: {i} (Length: {len(content)})")
                found_data[i] = content
            except:
                print(f"Not found: {i}")

        # Dump found scripts to file for analysis
        if found_data:
            with open("tiktok_scripts_dump.txt", "w", encoding="utf-8") as f:
                for k, v in found_data.items():
                    f.write(f"--- ID: {k} ---\n{v}\n\n")
            print("Dumped scripts to tiktok_scripts_dump.txt")
            
            # Quick check for playAddr
            for k, v in found_data.items():
                if "playAddr" in v:
                    print(f"SUCCESS: 'playAddr' found in {k}")
                elif "video" in v and "http" in v:
                    print(f"Potential video URL found in {k}")

        driver.quit()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_scripts()
