import sys
import os

# Add parent directory to path so we can import config and main
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from main import copy_existing_download
from tiktok_manager import TikTokManager

def test():
    video_url = "https://www.tiktok.com/@kenh14official/video/7654525345504218375"
    origin_channel_name = "Kenh14.vn"
    copy_channels = [
        {"name": "Kenh14.vn"},
        {"name": "Kenh14.vn 2"},
        {"name": "Kenh14.vn 3"}
    ]
    
    # Ensure config points to correct directories relative to workspace
    # Since we are running in scratch, we want config paths relative to project root
    config.DOWNLOAD_PATH = "downloads"
    config.DOWNLOAD_REPORT_FILE = "tải video tiktok.txt"
    
    print("Initializing TikTokManager...")
    tk_manager = TikTokManager()
    
    print(f"Calling copy_existing_download for video {video_url}...")
    copy_existing_download(video_url, origin_channel_name, copy_channels, tk_manager)
    
    print("\nVerification:")
    for ch in copy_channels:
        dest_dir = os.path.join("downloads", ch["name"])
        print(f"Checking directory: {dest_dir}")
        if os.path.exists(dest_dir):
            files = os.listdir(dest_dir)
            print(f" > Files: {files}")
        else:
            print(" > Directory DOES NOT EXIST")

if __name__ == "__main__":
    test()
