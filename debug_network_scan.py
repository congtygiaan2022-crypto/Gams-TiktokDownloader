from selenium import webdriver
import time
import requests

def scan_network():
    url = "https://www.tiktok.com/@suckhoevn.247/video/7592939411017305351"
    options = webdriver.ChromeOptions()
    # options.add_argument("--headless")
    options.add_argument("--mute-audio")
    
    print(f"Opening {url}...")
    try:
        driver = webdriver.Chrome(options=options)
        driver.get(url)
        time.sleep(15) # Wait for buffer
        
        # Scan Performance Entries
        entries = driver.execute_script("""
            return performance.getEntriesByType("resource")
                .map(e => e.name)
                .filter(name => name.includes(".mp4") || name.includes("video") || name.includes("blob:"))
        """)
        
        print(f"Found {len(entries)} candidate resources.")
        video_url = None
        
        for e in entries:
            print(f"- {e[:100]}")
            if "blob:" not in e and ".mp4" in e:
                video_url = e
                break
        
        if video_url:
            print(f"FOUND VIDEO URL IN NETWORK: {video_url}")
            # Try download
            headers = {"User-Agent": driver.execute_script("return navigator.userAgent;"), "Referer": url}
            cookies = {c['name']: c['value'] for c in driver.get_cookies()}
            print("Downloading...")
            r = requests.get(video_url, headers=headers, cookies=cookies, stream=True)
            if r.status_code == 200:
                print("Download SUCCESS (200 OK)")
            else:
                print(f"Download FAIL ({r.status_code})")
        else:
            print("No direct .mp4 link found in network resources.")
            
        driver.quit()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    scan_network()
