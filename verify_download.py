from tiktok_manager import TikTokManager
from downloader import Downloader
import logging
import sys
import config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

def main():
    tk_manager = TikTokManager()
    downloader = Downloader()

    print("Queue size before:", len(tk_manager._get_queue_urls()))

    # Process just 2 videos for testing
    for _ in range(2):
        channel_name, video_url = tk_manager.pop_from_queue()
        if not video_url:
            break
        
        # Skip invalid generic link if present
        if "tiktok.com" not in video_url:
            print("Skipping invalid link")
            continue

        print(f"Downloading {video_url}...")
        success = downloader.download_video(video_url)
        if success:
            tk_manager.update_history(video_url)
            print("Download success")
        else:
            print("Download failed")

    print("Queue size after:", len(tk_manager._get_queue_urls()))

if __name__ == "__main__":
    main()
