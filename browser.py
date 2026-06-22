import logging
import socket
import time
import subprocess
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

class Browser:
    def __init__(self):
        self.driver = None
        self.logger = logging.getLogger(__name__)
        self._native_process = None  # Track subprocess cho Chrome/CốcCốc native

    def _wait_for_port(self, address, timeout=10):
        """Chờ port mở trước khi kết nối."""
        host, port = address.split(':')
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                with socket.create_connection((host, int(port)), timeout=1):
                    return True
            except:
                time.sleep(0.5)
        return False

    def _kill_browser_processes(self, process_name):
        """Tắt tất cả tiến trình browser đang chạy để tránh khóa profile."""
        try:
            self.logger.info(f"Đang đóng các tiến trình {process_name} để tránh khóa profile...")
            subprocess.run(f'taskkill /F /IM {process_name}', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(1)
        except Exception as e:
            self.logger.warning(f"Lỗi khi tắt tiến trình {process_name}: {e}")

    def attach(self, debugger_address, driver_path=None):
        """
        Kết nối với instance Chrome/CốcCốc hiện có qua debuggerAddress.
        debugger_address: '127.0.0.1:xxxxx'
        """
        try:
            print(f"DEBUG: Connecting to {debugger_address}...", flush=True)
            self.logger.info(f"Đang kiểm tra kết nối tới {debugger_address}...")
            if not self._wait_for_port(debugger_address):
                self.logger.error(f"Port {debugger_address} không phản hồi sau 10 giây.")
                return None

            chrome_options = Options()
            chrome_options.add_experimental_option("debuggerAddress", debugger_address)
            
            self.logger.info("Đang khởi tạo WebDriver...")
            if driver_path:
                service = Service(executable_path=driver_path)
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
            else:
                self.driver = webdriver.Chrome(options=chrome_options)
            
            # Đảm bảo có cửa sổ hoạt động
            try:
                time.sleep(2)
                handles = self.driver.window_handles
                if handles:
                    self.driver.switch_to.window(handles[0])
                    self.logger.info(f"Đã chuyển hướng tới window handle: {handles[0]}")
                else:
                    self.logger.warning("Không tìm thấy window handle nào sau khi kết nối.")
            except Exception as hw_err:
                self.logger.warning(f"Lỗi khi kiểm tra window handles: {hw_err}")

            self.driver.set_page_load_timeout(45)
            self.logger.info(f"Đã kết nối Chrome tại {debugger_address}")
            return self.driver
        except Exception as e:
            self.logger.error(f"Lỗi kết nối automation: {e}")
            return None

    def launch_chrome(self, user_data_dir, profile_name="Default", debug_port=9222, chrome_exe=None, driver_path=None):
        """
        Tự khởi động Chrome với remote debugging port.
        
        Args:
            user_data_dir: Đường dẫn thư mục User Data của Chrome
            profile_name: Tên thư mục profile (Default, Profile 1, ...)
            debug_port: Port debug (mặc định 9222)
            chrome_exe: Đường dẫn tới chrome.exe (None = tự tìm)
            driver_path: Đường dẫn chromedriver.exe
        """
        try:
            # Tắt Chrome đang chạy để tránh khóa profile
            self._kill_browser_processes("chrome.exe")

            # Tìm Chrome exe nếu không chỉ định
            if not chrome_exe or not os.path.exists(chrome_exe):
                chrome_exe = self._find_chrome_exe()
            if not chrome_exe:
                self.logger.error("Không tìm thấy Chrome. Vui lòng chỉ định đường dẫn chrome.exe.")
                return None

            # Check for Chrome 136+ restriction on default User Data Dir
            default_chrome_dir = os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data").lower()
            default_chrome_dir_alt = os.path.expandvars(r"%USERPROFILE%\AppData\Local\Google\Chrome\User Data").lower()
            
            if user_data_dir.lower() in (default_chrome_dir, default_chrome_dir_alt):
                project_dir = os.path.dirname(os.path.abspath(__file__))
                new_dir = os.path.join(project_dir, "downloads", "chrome_automation_profile")
                self.logger.warning(
                    f"CẢNH BÁO CHROME 136+: Không thể mở debug port trên thư mục User Data mặc định của Chrome. "
                    f"Tự động chuyển sang thư mục chuyên dụng: {new_dir}"
                )
                user_data_dir = new_dir
            
            os.makedirs(user_data_dir, exist_ok=True)

            import re
            m = re.search(r'\(([^)]+)\)$', profile_name)
            profile_dir = m.group(1) if m else profile_name

            self.logger.info(f"Đang khởi động Chrome: {chrome_exe}")
            self.logger.info(f"  User Data: {user_data_dir}")
            self.logger.info(f"  Profile Dir: {profile_dir} (từ '{profile_name}')")
            self.logger.info(f"  Debug port: {debug_port}")

            cmd = [
                chrome_exe,
                f"--remote-debugging-port={debug_port}",
                f"--user-data-dir={user_data_dir}",
                f"--profile-directory={profile_dir}",
                "--no-first-run",
                "--no-default-browser-check",
                "--disable-gpu",
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ]

            self._native_process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            self.logger.info(f"Đã khởi động Chrome (PID: {self._native_process.pid}), đang chờ port...")
            time.sleep(3)

            debugger_address = f"127.0.0.1:{debug_port}"
            return self.attach(debugger_address, driver_path=driver_path)

        except Exception as e:
            self.logger.error(f"Lỗi khởi động Chrome: {e}")
            return None

    def launch_cococ(self, user_data_dir, profile_name="Default", debug_port=9223, cococ_exe=None, driver_path=None):
        """
        Tự khởi động Cốc Cốc với remote debugging port.
        Cốc Cốc dựa trên Chromium nên dùng cùng cơ chế với Chrome.
        
        Args:
            user_data_dir: Đường dẫn thư mục User Data của Cốc Cốc
            profile_name: Tên thư mục profile
            debug_port: Port debug (mặc định 9223, khác Chrome để tránh xung đột)
            cococ_exe: Đường dẫn tới browser.exe của Cốc Cốc
            driver_path: Đường dẫn chromedriver tương thích với Cốc Cốc
        """
        try:
            # Tắt Cốc Cốc đang chạy để tránh khóa profile
            self._kill_browser_processes("browser.exe")

            if not cococ_exe or not os.path.exists(cococ_exe):
                cococ_exe = self._find_cococ_exe()
            if not cococ_exe:
                self.logger.error("Không tìm thấy Cốc Cốc. Vui lòng chỉ định đường dẫn browser.exe.")
                return None

            # Check for Chromium 136+ restriction on default User Data Dir
            default_cococ_dir = os.path.expandvars(r"%LOCALAPPDATA%\CocCoc\Browser\User Data").lower()
            default_cococ_dir_alt = os.path.expandvars(r"%USERPROFILE%\AppData\Local\CocCoc\Browser\User Data").lower()
            
            if user_data_dir.lower() in (default_cococ_dir, default_cococ_dir_alt):
                project_dir = os.path.dirname(os.path.abspath(__file__))
                new_dir = os.path.join(project_dir, "downloads", "cococ_automation_profile")
                self.logger.warning(
                    f"CẢNH BÁO CỐC CỐC: Không thể mở debug port trên thư mục User Data mặc định của Cốc Cốc. "
                    f"Tự động chuyển sang thư mục chuyên dụng: {new_dir}"
                )
                user_data_dir = new_dir
            
            os.makedirs(user_data_dir, exist_ok=True)

            import re
            m = re.search(r'\(([^)]+)\)$', profile_name)
            profile_dir = m.group(1) if m else profile_name

            self.logger.info(f"Đang khởi động Cốc Cốc: {cococ_exe}")
            self.logger.info(f"  User Data: {user_data_dir}")
            self.logger.info(f"  Profile Dir: {profile_dir} (từ '{profile_name}')")
            self.logger.info(f"  Debug port: {debug_port}")

            cmd = [
                cococ_exe,
                f"--remote-debugging-port={debug_port}",
                f"--user-data-dir={user_data_dir}",
                f"--profile-directory={profile_dir}",
                "--no-first-run",
                "--no-default-browser-check",
                "--disable-gpu",
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ]

            self._native_process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            self.logger.info(f"Đã khởi động Cốc Cốc (PID: {self._native_process.pid}), đang chờ port...")
            time.sleep(3)

            debugger_address = f"127.0.0.1:{debug_port}"
            return self.attach(debugger_address, driver_path=driver_path)

        except Exception as e:
            self.logger.error(f"Lỗi khởi động Cốc Cốc: {e}")
            return None

    def _find_chrome_exe(self):
        """Tự tìm đường dẫn chrome.exe trên Windows."""
        candidates = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
            os.path.expandvars(r"%PROGRAMFILES%\Google\Chrome\Application\chrome.exe"),
        ]
        for path in candidates:
            if os.path.exists(path):
                self.logger.info(f"Tìm thấy Chrome tại: {path}")
                return path
        return None

    def _find_cococ_exe(self):
        """Tự tìm đường dẫn browser.exe của Cốc Cốc trên Windows."""
        candidates = [
            r"C:\Program Files\CocCoc\Browser\Application\browser.exe",
            r"C:\Program Files (x86)\CocCoc\Browser\Application\browser.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\CocCoc\Browser\Application\browser.exe"),
        ]
        for path in candidates:
            if os.path.exists(path):
                self.logger.info(f"Tìm thấy Cốc Cốc tại: {path}")
                return path
        return None

    def _find_chrome_user_data(self):
        """Tự tìm thư mục User Data của Chrome trên Windows."""
        candidates = [
            os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data"),
            os.path.expandvars(r"%USERPROFILE%\AppData\Local\Google\Chrome\User Data"),
        ]
        for path in candidates:
            if os.path.isdir(path):
                self.logger.info(f"Tìm thấy Chrome User Data tại: {path}")
                return path
        return None

    def _find_cococ_user_data(self):
        """Tự tìm thư mục User Data của Cốc Cốc trên Windows."""
        candidates = [
            os.path.expandvars(r"%LOCALAPPDATA%\CocCoc\Browser\User Data"),
            os.path.expandvars(r"%USERPROFILE%\AppData\Local\CocCoc\Browser\User Data"),
        ]
        for path in candidates:
            if os.path.isdir(path):
                self.logger.info(f"Tìm thấy Cốc Cốc User Data tại: {path}")
                return path
        return None

    def get_chrome_profiles(self, user_data_dir):
        """Lấy danh sách profile trong thư mục User Data của Chrome/CốcCốc."""
        profiles = []
        if not user_data_dir or not os.path.isdir(user_data_dir):
            return profiles
        try:
            for item in os.listdir(user_data_dir):
                item_path = os.path.join(user_data_dir, item)
                # Profile dirs: Default, Profile 1, Profile 2, ...
                if os.path.isdir(item_path) and (item == "Default" or item.startswith("Profile ")):
                    # Thử đọc tên display từ Preferences
                    pref_file = os.path.join(item_path, "Preferences")
                    display_name = item
                    if os.path.exists(pref_file):
                        try:
                            import json
                            with open(pref_file, 'r', encoding='utf-8', errors='ignore') as f:
                                prefs = json.load(f)
                            name = prefs.get('profile', {}).get('name', '')
                            if name:
                                display_name = f"{name} ({item})"
                        except:
                            pass
                    profiles.append({'id': item, 'name': display_name})
        except Exception as e:
            self.logger.error(f"Lỗi đọc danh sách profile Chrome: {e}")
        return profiles

    def maximize_window(self):
        """Phóng to cửa sổ trình duyệt để thấy rõ nội dung."""
        if self.driver:
            try:
                self.driver.maximize_window()
                self.logger.info("Đã phóng to cửa sổ trình duyệt.")
            except Exception as e:
                self.logger.warning(f"Không thể phóng to cửa sổ: {e}")

    def close(self):
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            self.driver = None

        # Đóng process Chrome/CốcCốc native nếu tool đã tự khởi động
        if self._native_process:
            try:
                self._native_process.terminate()
                self._native_process.wait(timeout=5)
            except:
                try:
                    self._native_process.kill()
                except:
                    pass
            self._native_process = None
