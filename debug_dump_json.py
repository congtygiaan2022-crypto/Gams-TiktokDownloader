from selenium import webdriver
import json
import time

def dump_data():
    url = "https://www.tiktok.com/@suckhoevn.247/video/7592939411017305351"
    options = webdriver.ChromeOptions()
    # options.add_argument("--headless") # Keep headful
    options.add_argument("--mute-audio")
    
    print(f"Opening {url}...")
    try:
        driver = webdriver.Chrome(options=options)
        driver.get(url)
        time.sleep(10)
        
        # Safe extraction: serialize in JS first
        json_str = driver.execute_script("""
            let result = {};
            if (window.__UNIVERSAL_DATA_FOR_REHYDRATION__) {
                try {
                    result.universal = window.__UNIVERSAL_DATA_FOR_REHYDRATION__;
                } catch(e) { result.universal_error = e.toString(); }
            }
            if (window.SIGI_STATE) {
                try {
                    result.sigi = window.SIGI_STATE;
                } catch(e) { result.sigi_error = e.toString(); }
            }
            return JSON.stringify(result);
        """)
        
        data = json.loads(json_str)
        
        with open("tiktok_debug_data.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            
        print("Data dumped to tiktok_debug_data.json")
        driver.quit()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    dump_data()
