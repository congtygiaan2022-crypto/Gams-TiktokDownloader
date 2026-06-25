import os
import logging
import threading
import config

class TikTokManager:
    def __init__(self, channels_file='danhsachtiktok.txt', history_file='lichsutaitiktok.txt', queue_file='hangdoitiktok.txt', error_file='kenhloi.txt'):
        self.channels_file = channels_file
        self.history_file = history_file
        self.queue_file = queue_file
        self.error_file = error_file
        self.report_file = getattr(config, 'DOWNLOAD_REPORT_FILE', 'tải video tiktok.txt')
        self.logger = logging.getLogger(__name__)
        self.lock = threading.Lock() # Lock cho safe-thread

        # Đảm bảo các file tồn tại
        # (Dùng lock ở đây không quá cần thiết vì init chạy 1 lần, nhưng an toàn hơn)
        with self.lock:
            for f in [self.channels_file, self.history_file, self.queue_file, self.report_file, self.error_file]:
                if not os.path.exists(f):
                    with open(f, 'w', encoding='utf-8') as file:
                        pass

    def _write_file_atomically(self, filepath, lines):
        """Ghi dữ liệu xuống file một cách an toàn (atomic write) để tránh lỗi corrupt file khi bị kill process."""
        temp_filepath = filepath + ".tmp"
        try:
            with open(temp_filepath, 'w', encoding='utf-8') as f:
                for line in lines:
                    f.write(line + '\n')
                f.flush()
                try:
                    os.fsync(f.fileno())
                except:
                    pass
            # os.replace thay thế file đích một cách an toàn và ghi đè trực tiếp trên cả Windows/Linux
            os.replace(temp_filepath, filepath)
        except Exception as e:
            self.logger.error(f"Lỗi ghi file an toàn {filepath}: {e}")
            if os.path.exists(temp_filepath):
                try:
                    os.remove(temp_filepath)
                except:
                    pass

    def get_channels(self):
        """Đọc danh sách kênh từ file. Trả về list {'url': url, 'name': name}."""
        channels = []
        with self.lock:
            if os.path.exists(self.channels_file):
                with open(self.channels_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.replace('\x00', '').strip()
                        if not line:
                            continue
                        
                        parts = line.split('|')
                        url = parts[0].strip()
                        if not url:
                            continue
                        name = parts[1].strip() if len(parts) > 1 else None
                        status = parts[2].strip() if len(parts) > 2 else ""
                        channels.append({'url': url, 'name': name, 'status': status})
        return channels

    def update_group_names(self, target_url, new_names):
        """Cập nhật tên cho một nhóm kênh trùng URL theo danh sách tên."""
        target_url = target_url.replace('\x00', '').strip()
        if not target_url:
            return
            
        with self.lock:
            channels_lines = []
            if os.path.exists(self.channels_file):
                with open(self.channels_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    
                name_idx = 0
                for line in lines:
                    line = line.replace('\x00', '').strip()
                    if not line: continue
                    parts = line.split('|')
                    url = parts[0].strip()
                    if not url: continue
                    
                    if url == target_url and name_idx < len(new_names):
                        name = new_names[name_idx]
                        status = parts[2].strip() if len(parts) > 2 else ""
                        new_line = f"{url}|{name}"
                        if status:
                            new_line += f"|{status}"
                        channels_lines.append(new_line)
                        name_idx += 1
                    else:
                        channels_lines.append(line)
                        
                self._write_file_atomically(self.channels_file, channels_lines)
            self.logger.info(f"Đã cập nhật tên nhóm kênh cho {target_url}")

    def update_channel_status(self, target_url, status):
        """Cập nhật trạng thái cho kênh (kênh live/kênh die) trong file."""
        target_url = target_url.replace('\x00', '').strip()
        if not target_url:
            return
            
        with self.lock:
            channels_lines = []
            if os.path.exists(self.channels_file):
                with open(self.channels_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.replace('\x00', '').strip()
                        if not line: continue
                        
                        parts = line.split('|')
                        url = parts[0].strip()
                        if not url: continue
                        
                        if url == target_url:
                            # Giữ lại name nếu có, cập nhật hoặc thêm status ở cuối
                            name = parts[1].strip() if len(parts) > 1 else ""
                            # Cấu trúc: URL|Tên|Trạng thái
                            channels_lines.append(f"{url}|{name}|{status}")
                        else:
                            channels_lines.append(line)
            
            self._write_file_atomically(self.channels_file, channels_lines)
            
            # Ngoài file chính, nếu kênh die hoặc lỗi thì ghi vào kenhloi.txt
            if "die" in status.lower() or "something went wrong" in status.lower() or "lỗi" in status.lower():
                try:
                    with open(self.error_file, 'a', encoding='utf-8') as f:
                        import datetime
                        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        f.write(f"[{now}] {target_url}|{status}\n")
                except: pass

            self.logger.info(f"✓ Đã cập nhật trạng thái kênh {target_url} -> {status}")

    def update_channel_name(self, target_url, new_name):
        """Cập nhật tên cho kênh cụ thể trong file, bảo lưu trạng thái nếu có."""
        target_url = target_url.replace('\x00', '').strip()
        if not target_url:
            return
            
        with self.lock:
            # Đọc toàn bộ danh sách hiện tại
            channels = []
            if os.path.exists(self.channels_file):
                 with open(self.channels_file, 'r', encoding='utf-8') as f:
                    for line in f:
                         line = line.replace('\x00', '').strip()
                         if not line: continue
                         parts = line.split('|')
                         url = parts[0].strip()
                         if not url: continue
                         channels.append({
                             'url': url, 
                             'name': parts[1].strip() if len(parts) > 1 else None,
                             'status': parts[2].strip() if len(parts) > 2 else ""
                         })
            
            updated = False
            for ch in channels:
                if ch['url'] == target_url:
                    ch['name'] = new_name
                    updated = True
            
            if updated:
                channels_lines = []
                for ch in channels:
                    line = f"{ch['url']}"
                    if ch['name']:
                        line += f"|{ch['name']}"
                    if ch['status']:
                        # Đảm bảo nếu có status thì phải có dấu gạch cho name
                        if not ch['name']: line += "|"
                        line += f"|{ch['status']}"
                    channels_lines.append(line)
                self._write_file_atomically(self.channels_file, channels_lines)
                self.logger.info(f"Đã cập nhật tên kênh cho {target_url} thành {new_name}")

    def get_downloaded_history(self):
        """Đọc danh sách video đã tải."""
        with self.lock:
            with open(self.history_file, 'r', encoding='utf-8') as f:
                return set(line.strip() for line in f if line.strip())

    def update_history(self, video_url):
        """Thêm video vào lịch sử tải và force flush xuống disk."""
        with self.lock:
            with open(self.history_file, 'a', encoding='utf-8') as f:
                f.write(video_url + '\n')
                f.flush()
                try:
                    os.fsync(f.fileno())
                except: pass

    def add_to_download_report(self, channel_name, video_url, filename):
        """Lưu lại log tải video chi tiết kèm tên file để user dễ theo dõi và sync xuống disk."""
        import datetime
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self.lock:
            with open(self.report_file, 'a', encoding='utf-8') as f:
                f.write(f"[{now}] Kênh: {channel_name} | Video: {video_url} | File: {filename}\n")
                f.flush()
                try:
                    os.fsync(f.fileno())
                except:
                    pass
            self.logger.info(f"✓ Đã lưu log tải vào {self.report_file}")

    def add_to_queue(self, video_urls, channel_name):
        """Thêm video mới vào hàng đợi kèm thông tin kênh."""
        # Cần lock toàn bộ quá trình check + write để tránh race condition
        with self.lock:
            # Đọc history (tự đọc để tránh deadlock nếu gọi method có lock)
            history = set()
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    history = set(line.strip() for line in f if line.strip())
            
            # Đọc queue
            existing_queue = set()
            if os.path.exists(self.queue_file):
                with open(self.queue_file, 'r', encoding='utf-8') as f:
                     for line in f:
                        if '|' in line:
                            _, url = line.strip().split('|', 1)
                            existing_queue.add(url)

            new_items = []
            for url in video_urls:
                if url not in history and url not in existing_queue:
                    new_items.append(f"{channel_name}|{url}")
            
            if new_items:
                with open(self.queue_file, 'a', encoding='utf-8') as f:
                    for item in new_items:
                        f.write(item + '\n')
                self.logger.info(f"Đã thêm {len(new_items)} video mới vào hàng đợi cho {channel_name}.")

    def _get_queue_urls(self):
        """Helper nội bộ, không dùng lock vì được gọi bởi function đã có lock hoặc cẩn thận."""
        # Hàm này cũ, giờ logic đã gộp vào add_to_queue để an toàn.
        # Giữ lại nếu cần nhưng cẩn thận deadlock.
        urls = set()
        if os.path.exists(self.queue_file):
            with open(self.queue_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if '|' in line:
                         _, url = line.strip().split('|', 1)
                         urls.add(url)
        return urls

    def pop_from_queue(self):
        """Lấy và xóa item đầu tiên khỏi hàng đợi. Trả về (channel_name, url)."""
        with self.lock:
            if not os.path.exists(self.queue_file):
                return None, None
                
            with open(self.queue_file, 'r', encoding='utf-8') as f:
                lines = [line.strip() for line in f if line.strip()]
                
            if not lines:
                return None, None
            
            item_line = lines[0]
            remaining = lines[1:]
            
            with open(self.queue_file, 'w', encoding='utf-8') as f:
                for line in remaining:
                    f.write(line + '\n')
            
            if '|' in item_line:
                return item_line.split('|', 1)
            return None, None
