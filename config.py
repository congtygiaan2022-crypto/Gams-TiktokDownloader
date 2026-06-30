import os

# ============================================================
# CẤU HÌNH TRÌNH DUYỆT (Browser Settings)
# ============================================================
# Loại trình duyệt: gemlogin | gpmlogin | donut | chrome | cococ
BROWSER_TYPE = 'chrome'

# --- GemLogin ---
GEMLOGIN_API_URL = 'http://localhost:1010'

# --- GPM Login ---
GPM_LOGIN_API_URL = 'http://localhost:60064'

# --- Donut Browser ---
DONUT_API_URL = 'http://127.0.0.1:10108'
DONUT_API_KEY = 'vCizvRR9hHiMq3IQPxB1O1yNkYHTTh-otDNkvKcvwkk'

# --- Profile được chọn (GemLogin / GPM Login) ---
SELECTED_PROFILE_ID = '0ad52d04-01b2-488b-8628-f067a4940f17'
SELECTED_PROFILE_NAME = 'Tiktok Download 1'

# --- Chrome / Cốc Cốc Native (không qua API) ---
CHROME_EXE_PATH = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe'
CHROME_USER_DATA_DIR = 'C:\\Users\\admin\\AppData\\Local\\Google\\Chrome\\User Data'
CHROME_PROFILE_NAME = 'Chrome của bạn (Default)'
CHROME_DEBUG_PORT = 9222

COCOC_EXE_PATH = ''
COCOC_USER_DATA_DIR = ''
COCOC_PROFILE_NAME = 'Default'
COCOC_DEBUG_PORT = 9223

# --- Xoay Profile (Rotate) ---
ROTATE_PROFILES = False
PROFILE_ROTATE_INTERVAL = 5
PROFILE_ROTATE_ORDER = 'sequential'

# API_VERSION
API_VERSION = "v1"

# ============================================================
# ĐƯỜNG DẪN
# ============================================================
LOG_FILE = "automation.log"
DOWNLOAD_REPORT_FILE = "tải video tiktok.txt"

# ============================================================
# THỜI GIAN CHỜ
# ============================================================
REQUEST_TIMEOUT = 120  # Tăng lên 120s để tránh lỗi Read timeout khi khởi động profile chậm

# ============================================================
# HIỆU NĂNG
# ============================================================
DOWNLOAD_THREADS = 3
CHECK_THREADS = 1     # Số luồng check
MAX_VIDEOS_PER_CHANNEL = 10

# ============================================================
# TÍNH NĂNG
# ============================================================
DOWNLOAD_SLIDESHOW = True
EXTRACT_STATS = True

# ============================================================
# LƯU TRỮ
# ============================================================
DOWNLOAD_PATH = 'downloads'

# ============================================================
# CẤU HÌNH VÒNG LẶP (Dashboard)
# ============================================================
RUN_ONCE = False
LOOP_COUNT = 5000
LOOP_DELAY = 600

IS_DARK = True

# ============================================================
# DYNAMIC PROFILE LOADING (Quản lý Profile tách biệt)
# ============================================================
def load_profile(profile_id):
    global LOG_FILE, DOWNLOAD_REPORT_FILE, DOWNLOAD_PATH
    global BROWSER_TYPE, GEMLOGIN_API_URL, GPM_LOGIN_API_URL, DONUT_API_URL, DONUT_API_KEY
    global SELECTED_PROFILE_ID, SELECTED_PROFILE_NAME
    global CHROME_EXE_PATH, CHROME_USER_DATA_DIR, CHROME_PROFILE_NAME, CHROME_DEBUG_PORT
    global COCOC_EXE_PATH, COCOC_USER_DATA_DIR, COCOC_PROFILE_NAME, COCOC_DEBUG_PORT
    global ROTATE_PROFILES, PROFILE_ROTATE_INTERVAL, PROFILE_ROTATE_ORDER
    global DOWNLOAD_THREADS, MAX_VIDEOS_PER_CHANNEL, DOWNLOAD_SLIDESHOW, EXTRACT_STATS
    global RUN_ONCE, LOOP_COUNT, LOOP_DELAY, IS_DARK

    if not profile_id:
        return

    # Tách biệt các file log, báo cáo và thư mục tải xuống theo profile
    LOG_FILE = f"automation_{profile_id}.log"
    DOWNLOAD_REPORT_FILE = f"tải video tiktok_{profile_id}.txt"
    DOWNLOAD_PATH = f"downloads_{profile_id}"

    # Đọc cấu hình riêng biệt từ file JSON của profile nếu tồn tại
    cfg_filename = f"config_profile_{profile_id}.json"
    if os.path.exists(cfg_filename) and os.path.getsize(cfg_filename) > 0:
        try:
            import json
            with open(cfg_filename, "r", encoding="utf-8") as f:
                saved = json.load(f)
            
            # Cập nhật các biến cấu hình toàn cục
            for k, v in saved.items():
                globals()[k] = v
        except Exception as e:
            print(f"Error loading profile config: {e}")

# Tự động nạp profile nếu tiến trình được chạy với biến môi trường ACTIVE_PROFILE_ID
ACTIVE_PROFILE_ID = os.environ.get("ACTIVE_PROFILE_ID")
if ACTIVE_PROFILE_ID:
    load_profile(ACTIVE_PROFILE_ID)