from selenium import webdriver
import json
import time

def dump_slideshow_json():
    # URL of the suspected Slideshow
    url = "https://www.tiktok.com/@suckhoevn.247/video/7586896734144498951"
    
    options = webdriver.ChromeOptions()
    options.add_argument("--mute-audio")
    
    driver = webdriver.Chrome(options=options)
    print(f"Opening {url}...")
    try:
        driver.get(url)
        time.sleep(15)
        
        script = """
            let el = document.getElementById("__UNIVERSAL_DATA_FOR_REHYDRATION__");
            if (el) return el.textContent;
            return null;
        """
        json_text = driver.execute_script(script)
        
        if json_text:
            with open("slideshow_debug.json", "w", encoding="utf-8") as f:
                f.write(json_text)
            print("Dumped JSON to slideshow_debug.json")
        else:
            print("Could not find __UNIVERSAL_DATA_FOR_REHYDRATION__")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    dump_slideshow_json()
