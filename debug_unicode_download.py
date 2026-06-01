import os
from downloader import Downloader
import logging
import sys

# Setup logging
logging.basicConfig(level=logging.INFO, stream=sys.stdout)

def main():
    # Folder with difficult characters
    folder_name = "Kênh TikTok"
    # Video TikTok mẫu
    video_url = "https://www.tiktok.com/@kenh14official/video/7317204481358990610" 

    print(f"Testing download into: {folder_name}")
    
    downloader = Downloader()
    try:
        success = downloader.download_video(video_url, subfolder=folder_name)
        if success:
            print("Download SUCCESS")
        else:
            print("Download FAILED (indicated by return value)")
    except Exception as e:
        print(f"Download CRASHED: {e}")

if __name__ == "__main__":
    main()
