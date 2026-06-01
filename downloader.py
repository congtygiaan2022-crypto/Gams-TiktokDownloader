import os
import logging
import yt_dlp
import config

class Downloader:
    def __init__(self, download_dir=None):
        # Ưu tiên tham số truyền vào > config > mặc định 'downloads'
        if download_dir:
            self.download_dir = download_dir
        elif hasattr(config, 'DOWNLOAD_PATH') and config.DOWNLOAD_PATH:
            self.download_dir = config.DOWNLOAD_PATH
        else:
            self.download_dir = 'downloads'

        self.logger = logging.getLogger(__name__)
        
        if not os.path.exists(self.download_dir):
            os.makedirs(self.download_dir)

    def download_video(self, video_url, subfolder=None):
        """Tải video đơn lẻ sử dụng yt-dlp. Tùy chọn tải vào thư mục con."""
        
        target_dir = self.download_dir
        if subfolder:
            target_dir = os.path.join(self.download_dir, subfolder)
            if not os.path.exists(target_dir):
                os.makedirs(target_dir)

        ydl_opts = {
            'outtmpl': os.path.join(target_dir, '%(title)s [%(id)s].%(ext)s'),
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'noplaylist': True,
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'merge_output_format': 'mp4',
            # Các tùy chọn bổ sung để tránh bị TikTok chặn hoặc lỗi trích xuất dữ liệu
            'nocheckcertificate': True,
            'ignoreerrors': False,
            'logtostderr': False,
            'no_color': True,
            'no_call_home': True,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'headers': {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'Accept-Language': 'en-US,en;q=0.9',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache',
                'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                'Sec-Ch-Ua-Mobile': '?0',
                'Sec-Ch-Ua-Platform': '"Windows"',
            }
        }
        
        # Sử dụng cookies nếu có
        cookies_path = os.path.join(os.getcwd(), 'cookies.txt')
        if os.path.exists(cookies_path):
            ydl_opts['cookiefile'] = cookies_path
            self.logger.info(f"Sử dụng cookies từ: {cookies_path}")
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                self.logger.info(f"Đang tải TikTok: {video_url} vào {target_dir}")
                ydl.download([video_url])
                return True
        except Exception as e:
            self.logger.error(f"Lỗi khi tải {video_url}: {e}")
            return False

    def download_direct_url(self, direct_url, save_path, cookies_dict=None, user_agent=None):
        """Tải video trực tiếp từ URL (dùng cho trường hợp yt-dlp gặp lỗi)"""
        import requests
        try:
            headers = {}
            if user_agent:
                headers['User-Agent'] = user_agent
            else:
                headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            
            headers['Referer'] = 'https://www.tiktok.com/'
            
            self.logger.info(f"Đang tải direct link: {direct_url[:50]}...")
            
            with requests.get(direct_url, headers=headers, cookies=cookies_dict, stream=True) as r:
                r.raise_for_status()
                with open(save_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=1024*1024): # 1MB chunks
                        f.write(chunk)
            
            self.logger.info(f"Đã tải xong: {save_path}")
            return True
        except Exception as e:
            self.logger.error(f"Lỗi tải direct link: {e}")
            return False
