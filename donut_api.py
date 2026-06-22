import requests
import logging
import config

class DonutAPI:
    """
    Client cho Donut Browser Local API.
    Base URL : http://127.0.0.1:10108  (default)
    Auth     : Bearer token (lấy trong app → Settings → Local API)

    Endpoints:
      GET  /v1/profiles          → danh sách profile
      POST /v1/profiles/{id}/run → khởi động profile
      POST /v1/profiles/{id}/kill→ dừng profile (bản Free trả về 402)
    """

    def __init__(self):
        self.base_url = getattr(config, 'DONUT_API_URL', 'http://127.0.0.1:10108').rstrip('/')
        self.api_key  = getattr(config, 'DONUT_API_KEY', '')
        self.logger   = logging.getLogger(__name__)
        self.timeout  = getattr(config, 'REQUEST_TIMEOUT', 60)

    @property
    def _headers(self):
        h = {'Content-Type': 'application/json'}
        if self.api_key:
            h['Authorization'] = f'Bearer {self.api_key}'
        return h

    # ─── profiles ───────────────────────────────────────────
    def get_profiles(self):
        """
        Trả về list profile dạng:
        [{'id': '...', 'name': '...', ...}, ...]
        """
        url = f'{self.base_url}/v1/profiles'
        try:
            resp = requests.get(url, headers=self._headers, timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json()
            if isinstance(data, list):
                return data
            profiles = (data.get('profiles') or data.get('data') or data.get('list') or data.get('items') or [])
            return profiles
        except requests.RequestException as e:
            self.logger.error(f'[DonutAPI] Lỗi lấy danh sách profile: {e}')
            return []

    def get_running_profile_port(self, profile_id: str):
        """Quét tìm port gỡ lỗi của profile nếu đang chạy."""
        import subprocess
        import re
        try:
            cmd = 'wmic process where "name=\'chrome.exe\'" get commandline,processid'
            output = subprocess.check_output(cmd, shell=True).decode('utf-8', errors='ignore')
            for line in output.splitlines():
                line = line.strip()
                if not line:
                    continue
                if profile_id in line and 'wayfern' in line.lower():
                    match = re.search(r'--remote-debugging-port=(\d+)', line)
                    if match:
                        return f"127.0.0.1:{match.group(1)}"
        except Exception as e:
            self.logger.error(f'[DonutAPI] Lỗi quét tìm port gỡ lỗi: {e}')
        return None

    def start_profile(self, profile_id: str):
        """
        Khởi động profile và trả về debugger address dạng '127.0.0.1:PORT'.
        Nếu tài khoản free bị lỗi 402, yêu cầu người dùng mở thủ công và tự động connect.
        """
        # 1. Kiểm tra xem profile đã chạy sẵn chưa
        addr = self.get_running_profile_port(profile_id)
        if addr:
            self.logger.info(f'[DonutAPI] Phát hiện profile {profile_id} đang chạy sẵn tại {addr}')
            return addr

        # 2. Thử gọi API khởi động
        url = f'{self.base_url}/v1/profiles/{profile_id}/run'
        try:
            self.logger.info(f'[DonutAPI] Đang gọi API khởi động profile {profile_id}...')
            resp = requests.post(url, headers=self._headers, json={}, timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json()
            port = (data.get('remote_debugging_port')
                    or data.get('debuggingPort')
                    or data.get('port')
                    or (data.get('data') or {}).get('remote_debugging_port'))
            if port:
                addr = f'127.0.0.1:{port}'
                self.logger.info(f'[DonutAPI] Profile {profile_id} khởi động thành công tại {addr}')
                return addr
        except Exception as e:
            self.logger.warning(f'[DonutAPI] Không thể khởi động qua API ({e}).')

        # 3. Fallback: Hướng dẫn người dùng mở thủ công và quét tiến trình
        self.logger.info(f'[DonutAPI] Chuyển sang chế độ kết nối thủ công cho profile {profile_id}.')
        
        def _safe_print(text):
            try:
                print(text)
            except UnicodeEncodeError:
                try:
                    # Fallback to ascii representation for CP1252 consoles
                    print(text.encode('ascii', errors='replace').decode('ascii'))
                except:
                    pass

        _safe_print(f"\n[!] [Donut] Vui long mo thu cong profile ID {profile_id} trong ung dung Donut Browser de tool tu dong ket noi!")
        
        # Chờ tối đa 60 giây
        import time
        for idx in range(60):
            addr = self.get_running_profile_port(profile_id)
            if addr:
                self.logger.info(f'[DonutAPI] Đã phát hiện profile {profile_id} được mở thủ công tại {addr}!')
                return addr
            if idx % 10 == 0 and idx > 0:
                _safe_print(f"  - Van dang cho ban mo profile {profile_id} trong app Donut... ({60 - idx}s)")
            time.sleep(1)

        self.logger.error(f'[DonutAPI] Hết thời gian chờ (60s) mở profile {profile_id} thủ công.')
        return None

    def stop_profile_locally(self, profile_id: str):
        """Đóng profile bằng cách kill tiến trình cục bộ."""
        import subprocess
        try:
            cmd = 'wmic process where "name=\'chrome.exe\'" get commandline,processid'
            output = subprocess.check_output(cmd, shell=True).decode('utf-8', errors='ignore')
            killed = False
            for line in output.splitlines():
                line = line.strip()
                if not line:
                    continue
                if profile_id in line and 'wayfern' in line.lower():
                    parts = line.split()
                    pid = parts[-1]
                    if pid.isdigit():
                        subprocess.run(f'taskkill /F /PID {pid}', shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
                        self.logger.info(f'[DonutAPI] Đã dừng profile {profile_id} cục bộ (PID: {pid})')
                        killed = True
            return killed
        except Exception as e:
            self.logger.error(f'[DonutAPI] Lỗi đóng profile cục bộ: {e}')
            return False

    def stop_profile(self, profile_id: str):
        """Dừng profile đang chạy."""
        url = f'{self.base_url}/v1/profiles/{profile_id}/kill'
        try:
            resp = requests.post(url, headers=self._headers, json={}, timeout=self.timeout)
            resp.raise_for_status()
            self.logger.info(f'[DonutAPI] Đã gửi lệnh dừng profile {profile_id} qua API.')
            return True
        except Exception as e:
            self.logger.warning(f'[DonutAPI] Lỗi stop profile {profile_id} qua API: {e}. Thử dừng cục bộ.')
            return self.stop_profile_locally(profile_id)
