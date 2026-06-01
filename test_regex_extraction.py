from selenium import webdriver
import time

def test_regex_extraction():
    url = "https://www.tiktok.com/@suckhoevn.247/video/7586896734144498951"  # Slideshow
    
    options = webdriver.ChromeOptions()
    options.add_argument("--mute-audio")
    
    driver = webdriver.Chrome(options=options)
    
    try:
        print(f"Loading {url}...")
        driver.get(url)
        time.sleep(5)
        
        script = """
            try {
                let el = document.getElementById("__UNIVERSAL_DATA_FOR_REHYDRATION__");
                if (!el) return "NO_ELEMENT";
                
                let jsonText = el.textContent || el.innerHTML;
                if (!jsonText) return "EMPTY_TEXT";
                
                // Try regex patterns
                let patterns = [
                    /"playAddr":"(https:\/\/[^"]+\.mp4[^"]*)"/,
                    /"downloadAddr":"(https:\/\/[^"]+\.mp4[^"]*)"/,
                    /"playAddr":\{"uri":"[^"]*","urlList":\["([^"]+)"/,
                    /"downloadAddr":\{"uri":"[^"]*","urlList":\["([^"]+)"/
                ];
                
                for (let i = 0; i < patterns.length; i++) {
                    let match = jsonText.match(patterns[i]);
                    if (match && match[1]) {
                        let url = match[1].replace(/\\\\u002F/g, '/').replace(/\\\\/g, '');
                        if (url.includes('tiktok') && url.includes('.mp4')) {
                            return "PATTERN_" + i + ": " + url;
                        }
                    }
                }
                
                return "NO_MATCH";
            } catch(e) { return "ERROR: " + e.message; }
        """
        
        result = driver.execute_script(script)
        print(f"\nResult: {result}")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    test_regex_extraction()
