from selenium import webdriver
from selenium.webdriver.common.by import By
import json
import time
import requests
import os

def check_extraction_and_download():
    url = "https://www.tiktok.com/@suckhoevn.247/video/7592939411017305351"
    options = webdriver.ChromeOptions()
    # options.add_argument("--headless")
    options.add_argument("--mute-audio")
    
    print(f"Opening {url}...")
    try:
        driver = webdriver.Chrome(options=options)
        driver.get(url)
        time.sleep(10)
        
        # 1. Extract
        script = """
            try {
                let el = document.getElementById("__UNIVERSAL_DATA_FOR_REHYDRATION__");
                if (!el) return null;
                let data = JSON.parse(el.textContent);
                
                function findKey(obj, key) {
                    if (typeof obj !== 'object' || obj === null) return null;
                    if (obj.hasOwnProperty(key)) return obj[key];
                    for (let k in obj) {
                        let res = findKey(obj[k], key);
                        if (res) return res;
                    }
                    return null;
                }
                return findKey(data, "playAddr");
            } catch(e) { return null; }
        """
        extracted_url = driver.execute_script(script)
        
        if extracted_url:
            print(f"EXTRACTED URL: {extracted_url[:100]}...")
            
            # 2. Prepare Cookies/Headers for Requests
            cookies = {c['name']: c['value'] for c in driver.get_cookies()}
            headers = {
                "User-Agent": driver.execute_script("return navigator.userAgent;"),
                "Referer": url
            }
            
            # 3. Try Downloading with Requests
            print("Attempting download with requests...")
            r = requests.get(extracted_url, cookies=cookies, headers=headers, stream=True)
            print(f"Status Code: {r.status_code}")
            print(f"Content-Type: {r.headers.get('Content-Type')}")
            
            if r.status_code == 200:
                with open("test_download.mp4", "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
                size = os.path.getsize("test_download.mp4")
                print(f"Downloaded test_download.mp4 ({size} bytes)")
            else:
                print("Download failed.")
                
        else:
            print("FAILED TO EXTRACT URL using script.")
            
        driver.quit()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_extraction_and_download()
