from selenium import webdriver
import json
import time

def debug_extraction():
    url = "https://www.tiktok.com/@suckhoevn.247/video/7592939411017305351"
    options = webdriver.ChromeOptions()
    options.add_argument("--mute-audio")
    # Enable Logging
    options.set_capability('goog:loggingPrefs', {'browser': 'ALL'})
    
    print(f"Opening {url}...")
    driver = webdriver.Chrome(options=options)
    try:
        driver.get(url)
        time.sleep(15) 
        
        # 1. Debug JS Extraction
        print("--- JS EXTRACTION DEBUG ---")
        script = """
            try {
                let el = document.getElementById("__UNIVERSAL_DATA_FOR_REHYDRATION__");
                if (!el) { console.error("DEBUG: Element ID not found"); return "ID_NOT_FOUND"; }
                
                let jsonText = el.textContent || el.innerHTML;
                if (!jsonText) { console.error("DEBUG: Empty Content"); return "EMPTY_CONTENT"; }
                
                try {
                    var data = JSON.parse(jsonText);
                    console.log("DEBUG: JSON Parsed. Keys: " + Object.keys(data).join(','));
                } catch(e) { console.error("DEBUG: JSON Parse Error: " + e.message); return "JSON_PARSE_ERROR"; }
                
                try {
                    let vid = data["__DEFAULT_SCOPE__"]["webapp.video-detail"].itemInfo.itemStruct.video;
                    if (vid && vid.playAddr) {
                        console.log("DEBUG: Found playAddr directly");
                        return vid.playAddr;
                    }
                } catch(e) { console.log("DEBUG: Direct path failed: " + e.message); }
                
                // Fallback Search
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
                if (found) { console.log("DEBUG: Found playAddr via recursive search"); return found; }
                
                console.log("DEBUG: playAddr NOT FOUND in data");
                return "KEY_NOT_FOUND";
                
            } catch(e) { console.error("DEBUG: Script Error: " + e.message); return "SCRIPT_ERROR"; }
        """
        res = driver.execute_script(script)
        print(f"JS Result: {res}")
        
        # Print Browser Console Logs
        for entry in driver.get_log('browser'):
            if "DEBUG" in str(entry):
                print(f"CONSOLE: {entry['message']}")

        # 2. Debug Network Scan
        print("\n--- NETWORK SCAN DEBUG ---")
        net_script = """
            return performance.getEntriesByType("resource")
                .map(e => e.name)
                .filter(name => (name.includes(".mp4") || name.includes("video")) && !name.includes("blob:") && !name.includes("login") && !name.includes("playback1.mp4"))
        """
        net_res = driver.execute_script(net_script)
        print(f"Found {len(net_res)} Valid Network Candidates:")
        for u in net_res:
            print(f"- {u[:100]}...")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    debug_extraction()
