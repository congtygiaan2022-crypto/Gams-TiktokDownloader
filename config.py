import os

# Cấu hình GemLogin API
GEMLOGIN_API_URL = "http://localhost:1010"
API_VERSION = "v1"

# Đường dẫn
LOG_FILE = "automation.log"
DOWNLOAD_REPORT_FILE = "tải video tiktok.txt"

# Thời gian chờ
REQUEST_TIMEOUT = 120  # Tăng lên 120s để tránh lỗi Read timeout khi khởi động profile chậm

# Hiệu năng
DOWNLOAD_THREADS = 3 # Số luồng tải video
CHECK_THREADS = 1    # Số luồng check (Hiện tại chưa dùng hết nếu chỉ có 1 profile)
MAX_VIDEOS_PER_CHANNEL = 10 # Số video tối đa lấy mỗi kênh

# Tính năng mới
DOWNLOAD_SLIDESHOW = True  # Tải slideshow/ảnh
EXTRACT_STATS = True       # Lấy thống kê (Like, Comment, Share)

# Đường dẫn lưu video
DOWNLOAD_PATH = "downloads"

# Cấu hình vòng lặp (Dashboard)
RUN_ONCE = False
LOOP_COUNT = 5000
LOOP_DELAY = 600

IS_DARK = True