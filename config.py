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