from selenium import webdriver
from selenium.webdriver.common.by import By
import time

def inspect_specific():
    urls = [
        "https://www.tiktok.com/@suckhoevn.247/video/7589603341613780232",
        "https://www.tiktok.com/@suckhoevn.247/video/7586896734144498951"
    ]
    
    options = webdriver.ChromeOptions()
    options.add_argument("--mute-audio")
    
    driver = webdriver.Chrome(options=options)
    
    for url in urls:
        print(f"\n--- INSPECTING: {url} ---")
        try:
            driver.get(url)
            time.sleep(15)
            
            # Dump all resources larger than typical images/scripts via name filtering
            print("Scanning ALL resources...")
            resources = driver.execute_script("""
                return performance.getEntriesByType("resource")
                    .map(e => e.name)
            """)
            
            video_candidates = []
            audio_candidates = []
            
            for r in resources:
                if ".mp4" in r: video_candidates.append(r)
                if ".mp3" in r or ".m4a" in r: audio_candidates.append(r)
                if "blob:" in r: print(f"BLOB FOUND: {r}")
                
            print(f"MP4 Candidates ({len(video_candidates)}):")
            for v in video_candidates: print(f"- {v[:100]}...")
            
            print(f"Audio Candidates ({len(audio_candidates)}):")
            for a in audio_candidates: print(f"- {a[:100]}...")
            
            # Check for Images if no video
            if not video_candidates:
                images = driver.execute_script("""
                    return Array.from(document.querySelectorAll('img')).map(i => i.src)
                """)
                print(f"Images Found on page: {len(images)}")
                
        except Exception as e:
            print(f"Error: {e}")
            
    driver.quit()

if __name__ == "__main__":
    inspect_specific()
