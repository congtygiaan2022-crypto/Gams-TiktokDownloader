# -*- coding: utf-8 -*-
"""
Upload_Git.py - Công cụ tự động cấu hình Git và upload source code lên GitHub
=============================================================================
Dành cho Nhà phát triển (Developer) chạy tại thư mục gốc của phần mềm.
"""

import os
import sys
import subprocess
import shutil

# Đảm bảo in tiếng Việt có dấu ra Console Windows không bị lỗi
try:
    sys.stdout.reconfigure(encoding='utf-8')
except AttributeError:
    pass

def get_current_git_remote():
    """Lấy URL remote origin hiện tại nếu có"""
    if os.path.exists(".git"):
        try:
            result = subprocess.run(
                ["git", "remote", "get-url", "origin"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8"
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
    return None

def write_gitignore():
    """Tự động ghi đè hoặc tạo file .gitignore chuẩn để tránh upload rác"""
    gitignore_content = """# Temp / OS files
Thumbs.db
ehthumbs.db
Desktop.ini
.DS_Store

# PyInstaller and Python build / cache files
__pycache__/
*.py[cod]
*$py.class
build/
dist/
*.spec

# Logs and download history files (from Antigravity_taivideotiktok)
automation.log
cookies.txt
danhsachtiktok.txt
hangdoitiktok.txt
kenhloi.txt
lichsutaitiktok.txt
tải video tiktok.txt
downloads/
*.log
browser_json_dump.txt
slideshow_debug.json
tiktok_scripts_dump.txt
tiktok_debug_data.json
debug_page_state.png

# AutoUpdate folder generated locally (important: keep it from git)
AutoUpdate - */

# Local config files (optional/local to dev)
repo_url.txt
.git_repo_url
"""
    with open(".gitignore", "w", encoding="utf-8") as f:
        f.write(gitignore_content)
    print("✓ Đã tự động tạo/cập nhật file .gitignore để lọc bỏ file rác.")

def create_auto_update_folder(git_repo_url):
    """Tạo thư mục AutoUpdate trong thư mục hiện tại và ghi các file cài đặt vào đó"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    folder_name = os.path.basename(current_dir)
    
    # Đặt tên folder: AutoUpdate - tên_folder_gốc
    update_folder_name = f"AutoUpdate - {folder_name}"
    update_folder_path = os.path.join(current_dir, update_folder_name)
    
    if not os.path.exists(update_folder_path):
        os.makedirs(update_folder_path)
        print(f"📁 Đã tạo thư mục cài đặt: {update_folder_name}")
    else:
        print(f"📁 Thư mục cài đặt đã tồn tại: {update_folder_name}")
        
    # 1. Viết file launcher_git.py cho thư mục AutoUpdate
    launcher_content = f"""# -*- coding: utf-8 -*-
\"\"\"
launcher_git.py - Trình khởi chạy tự động cập nhật qua Git
==========================================================
Chạy file này trên các máy con để tự động đồng bộ code từ kho lưu trữ Git.
\"\"\"

import sys
import os
import subprocess

# Đảm bảo in tiếng Việt và unicode ra Console Windows không bị lỗi
try:
    sys.stdout.reconfigure(encoding='utf-8')
except AttributeError:
    pass

# CẤU HÌNH ĐƯỜNG DẪN GIT CẬP NHẬT
GIT_REPO_URL = "{git_repo_url}"

def get_requirements_content():
    if os.path.exists("requirements.txt"):
        try:
            with open("requirements.txt", "r", encoding="utf-8") as f:
                return f.read().strip()
        except:
            pass
    return ""

def run_git_pull():
    print("=========================================")
    print(" DANG TU DONG KIEM TRA VA CAP NHAT...")
    print("=========================================")
    
    # 1. Đọc requirements trước khi pull
    req_before = get_requirements_content()
    
    # Tự động khởi tạo Git và liên kết Repo nếu chạy lần đầu trên máy mới tinh
    if not os.path.exists(".git"):
        print("[FOLDER] Phat hien cai dat moi tinh. Dang tu dong ket noi den kho Git...")
        try:
            subprocess.run(["git", "init"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(["git", "remote", "add", "origin", GIT_REPO_URL], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print("[OK] Khoi tao Git va lien ket Repository thanh cong.")
        except FileNotFoundError:
            print("[ERROR] Loi: May tinh nay chua duoc cai dat phan mem Git.")
            print("-> Vui long tai va cai dat Git tai: https://git-scm.com/")
            print("=========================================\\n")
            return
        except Exception as e:
            print(f"[!] Loi khoi tao Git: {{e}}")
            print("=========================================\\n")
            return
        
    try:
        # Luôn đảm bảo remote origin trỏ đúng URL cấu hình
        subprocess.run(["git", "remote", "set-url", "origin", GIT_REPO_URL], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
        # Chạy lệnh git pull để đồng bộ code mới nhất
        result = subprocess.run(
            ["git", "pull", "origin", "main"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=30
        )
        
        pulled_successfully = False
        if result.returncode == 0:
            pulled_successfully = True
            output = result.stdout.strip()
            if "Already up to date" in output:
                print("[OK] Ban dang chay phien ban moi nhat tu Git.")
            else:
                print("[CAP NHAT] DA CAP NHAT PHIEN BAN MOI THANH CONG!")
                print(output)
        else:
            # Nếu có lỗi khi pull (ví dụ conflict do sửa code cục bộ), thử reset remote để đè code sạch về
            print("[!] Phat hien xung dot hoac loi dong bo. Dang tu dong lam sach va tai lai...")
            subprocess.run(["git", "fetch", "--all"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            reset_result = subprocess.run(["git", "reset", "--hard", "origin/main"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if reset_result.returncode == 0:
                pulled_successfully = True
                print("[OK] Da dong bo thanh cong phien ban sach tu Git (De cac thay doi cuc bo).")
            else:
                print("[ERROR] Khong the dong bo ma nguon sach tu Git.")
                
        # 2. Đọc lại requirements.txt sau khi pull
        if pulled_successfully:
            req_after = get_requirements_content()
            if req_before != req_after and req_after != "":
                print("\\n[!] Phat hien thay doi ve thu vien can thiet.")
                print("Dang tu dong cai dat/cap nhat cac thu vien Python...")
                try:
                    subprocess.run(
                        [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
                        check=True
                    )
                    print("[OK] Thu vien da duoc cap nhat dong bo thanh cong.")
                except Exception as e:
                    print(f"[!] Loi cap nhat thu vien tu dong: {{e}}")
                    print("-> Ban co the chay thu cong file Cai_Dat_Thu_Vien.bat")
            
    except subprocess.TimeoutExpired:
        print("[!] Het thoi gian cho ket noi (Timeout). Bo qua cap nhat.")
    except FileNotFoundError:
        print("[ERROR] Loi: May tinh nay chua duoc cai dat phan mem Git.")
        print("-> Vui long tai va cai dat Git tai: https://git-scm.com/")
    except Exception as e:
        print(f"[!] Khong the cap nhat: {{e}}")
        
    print("=========================================\\n")

if __name__ == "__main__":
    # 1. Chạy cập nhật qua Git và tự động đồng bộ thư viện
    run_git_pull()
    
    # 2. Khởi chạy giao diện chính của Tool
    print("Dang khoi chay ung dung...")
    try:
        if os.path.exists("GiaanTesttool.py"):
            subprocess.Popen([sys.executable, "GiaanTesttool.py"])
        elif os.path.exists("main.py"):
            subprocess.Popen([sys.executable, "main.py"])
        else:
            print("[ERROR] Khong tim thay file chay ung dung (GiaanTesttool.py hoac main.py).")
            input("Nhan Enter de thoat.")
    except Exception as e:
        print(f"Loi khoi chay: {{e}}")
        input("Nhan Enter de thoat.")
"""
    with open(os.path.join(update_folder_path, "launcher_git.py"), "w", encoding="utf-8") as f:
        f.write(launcher_content)
    print("✓ Đã tạo file 'launcher_git.py' cập nhật tự động.")
    
    # Đồng thời lưu đè launcher_git.py trong folder dev để upload lên Git đồng bộ
    with open(os.path.join(current_dir, "launcher_git.py"), "w", encoding="utf-8") as f:
        f.write(launcher_content)

    # 2. Viết file Chay_Tool.bat cho thư mục AutoUpdate
    # CHÚ Ý: Viết 100% ASCII để tránh lỗi cmd.exe encoding lệch dòng
    chay_tool_bat_content = """@echo off
cd /d "%~dp0"
echo ====================================================
echo   DANG TU DONG DONG BO VA TAI PHAN MEM MOI TINH...
echo ====================================================
echo.
python launcher_git.py
if %errorlevel% neq 0 (
    echo.
    echo ====================================================
    echo   [LOI] Khong the khoi chay Tool.
    echo   Vui long kiem tra:
    echo   1. May tinh da cai dat Python - tich chon Add to PATH chua.
    echo   2. May tinh da cai dat phan mem Git chua.
    echo   3. Da chay file 'Cai_Dat_Thu_Vien.bat' truoc do chua.
    echo ====================================================
    echo.
    pause
)
"""
    with open(os.path.join(update_folder_path, "Chay_Tool.bat"), "w", encoding="ascii") as f:
        f.write(chay_tool_bat_content)
    print("✓ Đã tạo file 'Chay_Tool.bat' (định dạng ASCII an toàn).")

    # 3. Viết file Cai_Dat_Thu_Vien.bat cho thư mục AutoUpdate
    # CHÚ Ý: Viết 100% ASCII để tránh lỗi cmd.exe
    cai_dat_thu_vien_bat_content = """@echo off
cd /d "%~dp0"
echo ====================================================
echo   DANG TU DONG CAI DAT CAC THU VIEN BAT BUOC...
echo ====================================================
echo.
pip install -r requirements.txt
echo.
if %errorlevel% equ 0 (
    echo ====================================================
    echo   CAI DAT THU VIEN THANH CONG!
    echo   Bay gio ban co the mo file 'Chay_Tool.bat' de chay ung dung.
    echo ====================================================
) else (
    echo ====================================================
    echo   [LOI] Cai dat thu vien that bai.
    echo   Vui long kiem tra xem ban da cai dat Python - tich chon Add to PATH chua.
    echo ====================================================
)
echo.
pause
"""
    with open(os.path.join(update_folder_path, "Cai_Dat_Thu_Vien.bat"), "w", encoding="ascii") as f:
        f.write(cai_dat_thu_vien_bat_content)
    print("✓ Đã tạo file 'Cai_Dat_Thu_Vien.bat' (định dạng ASCII an toàn).")

    # 4. Sao chép requirements.txt sang thư mục AutoUpdate
    req_src = os.path.join(current_dir, "requirements.txt")
    req_dst = os.path.join(update_folder_path, "requirements.txt")
    if os.path.exists(req_src):
        shutil.copy2(req_src, req_dst)
        print("✓ Đã sao chép requirements.txt.")
    else:
        # Nếu chưa có requirements.txt, tạo mặc định cho Antigravity_taivideotiktok
        with open(req_dst, "w", encoding="utf-8") as f:
            f.write("requests\nselenium\nyt-dlp\n")
        # Đồng thời tạo cho thư mục dev luôn
        with open(req_src, "w", encoding="utf-8") as f:
            f.write("requests\nselenium\nyt-dlp\n")
        print("✓ Đã khởi tạo requirements.txt mặc định.")

    # 5. Tạo file HUONG_DAN_CAI_DAT.txt
    huong_dan_content = """====================================================
  HƯỚNG DẪN CÀI ĐẶT & CHẠY TOOL TỰ ĐỘNG CẬP NHẬT
====================================================

Để khởi chạy phần mềm lần đầu tiên trên máy tính của bạn, vui lòng làm theo 3 bước đơn giản dưới đây:

BƯỚC 1: CÀI ĐẶT PHẦN MỀM HỆ THỐNG (BẮT BUỘC)
Nếu máy bạn chưa có Python và Git, hãy tải và cài đặt chúng:
1. Python (từ phiên bản 3.10 trở lên):
   - Tải về tại: https://www.python.org/downloads/
   - Cài đặt bình thường. LƯU Ý CỰC KỲ QUAN TRỌNG: Khi vừa mở file cài đặt lên, hãy tích chọn vào ô "[x] Add Python to PATH" ở góc dưới cùng trước khi bấm "Install Now".
2. Phần mềm Git:
   - Tải về tại: https://git-scm.com/downloads
   - Cài đặt bình thường với các tùy chọn mặc định.

BƯỚC 2: CÀI ĐẶT THƯ VIỆN BỔ TRỢ
1. Nhấp đúp chuột chạy tệp tin "Cai_Dat_Thu_Vien.bat".
2. Chờ màn hình chạy xong và thông báo "CÀI ĐẶT THƯ VIỆN THÀNH CÔNG!" thì nhấn phím bất kỳ để đóng lại.

BƯỚC 3: KHỞI CHẠY PHẦN MỀM
1. Nhấp đúp chuột chạy tệp tin "Chay_Tool.bat".
2. Hệ thống sẽ tự động kết nối đến GitHub để tải toàn bộ code sạch mới nhất về máy của bạn, tự động tạo các file dữ liệu cấu hình trống và mở giao diện ứng dụng lên.
3. Từ lần chạy sau, mỗi khi bạn mở "Chay_Tool.bat", tool sẽ tự động kiểm tra và cập nhật code mới nhất.
"""
    with open(os.path.join(update_folder_path, "HUONG_DAN_CAI_DAT.txt"), "w", encoding="utf-8") as f:
        f.write(huong_dan_content)
    print("✓ Đã tạo file 'HUONG_DAN_CAI_DAT.txt'.")
    print(f"💡 Tất cả các file cài đặt máy con nằm trong: {update_folder_path}\n")

def run_git_commands(git_repo_url, commit_message, is_force):
    """Thực hiện các lệnh git để push code"""
    print("\n-----------------------------------------")
    print(" ĐANG THỰC HIỆN CÁC LỆNH GIT UPLOAD...")
    print("-----------------------------------------")
    
    try:
        # Kiểm tra xem máy có cài Git chưa
        subprocess.run(["git", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    except (FileNotFoundError, subprocess.CalledProcessError):
        print("❌ Lỗi: Máy tính của bạn chưa được cài đặt phần mềm Git hoặc chưa được thêm vào PATH.")
        print("-> Vui lòng cài đặt Git tại: https://git-scm.com/")
        return False

    # 1. Khởi tạo git nếu chưa có
    if not os.path.exists(".git"):
        print("📁 Chưa phát hiện thư mục .git. Tiến hành khởi tạo Git cục bộ...")
        subprocess.run(["git", "init"], check=True)
        subprocess.run(["git", "remote", "add", "origin", git_repo_url], check=True)
    else:
        # Đã có git, cập nhật remote origin
        print("✓ Đã phát hiện thư mục .git. Đang cập nhật URL remote origin...")
        subprocess.run(["git", "remote", "set-url", "origin", git_repo_url], check=True)

    try:
        # 2. Add files
        print("⚙️ Đang thêm các file vào Git Stage...")
        subprocess.run(["git", "add", "."], check=True)
        
        # 3. Commit
        print(f"⚙️ Đang tạo bản ghi commit: '{commit_message}'...")
        # Sử dụng git commit, nếu không có gì thay đổi thì bỏ qua hoặc thông báo
        result = subprocess.run(["git", "commit", "-m", commit_message], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode != 0:
            if "nothing to commit" in result.stdout or "nothing to commit" in result.stderr:
                print("✓ Không có thay đổi nào mới để commit.")
            else:
                print(f"⚠️ Cảnh báo commit: {result.stderr.strip()}")
        else:
            print("✓ Đã tạo bản ghi commit thành công.")
            
        # 4. Rename branch thành main
        subprocess.run(["git", "branch", "-M", "main"], check=True)
        
        # 5. Push lên git
        if is_force:
            print("🚀 ĐANG THỰC HIỆN FORCE PUSH (Như phần mềm mới tinh, ghi đè toàn bộ lịch sử)...")
            push_cmd = ["git", "push", "-u", "origin", "main", "--force"]
        else:
            print("🚀 ĐANG THỰC HIỆN NORMAL PUSH...")
            push_cmd = ["git", "push", "-u", "origin", "main"]
            
        push_result = subprocess.run(push_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if push_result.returncode == 0:
            print("\n=========================================")
            print(" 🎉 UPLOAD CODE LÊN GITHUB THÀNH CÔNG!")
            print(f" 🔗 Link Repo: {git_repo_url}")
            print("=========================================")
            return True
        else:
            print("\n❌ LỖI PUSH CODE LÊN GITHUB:")
            print(push_result.stderr.strip())
            print("\n💡 Gợi ý xử lý lỗi:")
            print("1. Kiểm tra xem bạn đã tạo repository trống trên GitHub chưa.")
            print("2. Đảm bảo tài khoản Git của bạn có quyền ghi (write permission) vào repository này.")
            print("3. Nếu là lần đầu tiên, hãy đăng nhập GitHub qua trình duyệt/credential manager.")
            if not is_force:
                print("4. Nếu kho lưu trữ đã có code từ trước, bạn có thể chọn chế độ 'Force Push' để ghi đè.")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"❌ Lỗi lệnh Git: {e}")
        return False
    except Exception as e:
        print(f"❌ Lỗi không xác định: {e}")
        return False

def main():
    print("=================================================================")
    print("      CÔNG CỤ UPLOAD CODE LÊN GIT & TẠO AUTO UPDATE MÁY CON      ")
    print("=================================================================")
    
    # 1. Đọc Git URL đã lưu từ config/remote hoặc file
    saved_url = get_current_git_remote()
    if not saved_url and os.path.exists("repo_url.txt"):
        try:
            with open("repo_url.txt", "r", encoding="utf-8") as f:
                saved_url = f.read().strip()
        except:
            pass
            
    print(f"URL Git hiện tại: {saved_url if saved_url else '(Chưa cấu hình)'}")
    
    # 2. Nhập URL Git mới hoặc chọn mặc định
    try:
        url_input = input("Nhập URL Git Repository của bạn\n(Nhấn Enter để dùng URL hiện tại): ").strip()
    except KeyboardInterrupt:
        print("\nĐã hủy tác vụ.")
        return
        
    git_repo_url = url_input if url_input else saved_url
    
    if not git_repo_url:
        print("❌ Lỗi: Bạn phải cấu hình URL Git Repository.")
        input("Nhấn Enter để thoát...")
        return
        
    # Lưu lại URL vào file cục bộ
    try:
        with open("repo_url.txt", "w", encoding="utf-8") as f:
            f.write(git_repo_url)
    except:
        pass
        
    # 3. Tạo/Cập nhật .gitignore
    write_gitignore()
    
    # 4. Tạo thư mục cài đặt tự động cập nhật AutoUpdate
    create_auto_update_folder(git_repo_url)
    
    # 5. Hỏi tùy chọn Upload
    print("\nTÙY CHỌN UPLOAD LÊN GITHUB:")
    print(" [1] Force Push (Upload như phần mềm MỚI TINH - đè tất cả lịch sử trên GitHub nếu có)")
    print(" [2] Normal Push (Upload cập nhật thông thường - giữ nguyên lịch sử)")
    print(" [3] Chỉ tạo thư mục cài đặt AutoUpdate cục bộ (Không upload lên GitHub)")
    
    try:
        choice = input("Nhập lựa chọn của bạn (mặc định [2]): ").strip()
    except KeyboardInterrupt:
        print("\nĐã hủy tác vụ.")
        return
        
    if choice == "3":
        print("\n✓ Đã hoàn tất tạo các file cài đặt AutoUpdate cục bộ.")
        print("Bây giờ bạn có thể nén thư mục 'AutoUpdate - ...' để gửi cho khách hàng.")
        input("Nhấn Enter để thoát...")
        return
        
    is_force = (choice == "1")
    
    try:
        commit_msg = input("Nhập nội dung commit (Nhấn Enter để dùng mặc định: 'Initial/Update commit'): ").strip()
    except KeyboardInterrupt:
        print("\nĐã hủy tác vụ.")
        return
        
    if not commit_msg:
        commit_msg = "Initial/Update commit"
        
    success = run_git_commands(git_repo_url, commit_msg, is_force)
    
    if success:
        print("\n👉 BƯỚC TIẾP THEO CHO KHÁCH HÀNG:")
        print(f"1. Gửi thư mục 'AutoUpdate - {os.path.basename(os.path.dirname(os.path.abspath(__file__)))}' cho khách hàng.")
        print("2. Khách hàng chỉ cần làm theo file HUONG_DAN_CAI_DAT.txt để chạy.")
        print("   (Chạy Cai_Dat_Thu_Vien.bat lần đầu, rồi chạy Chay_Tool.bat để tự động tải code về chạy).")
    
    print("\n=================================================================")
    input("Nhấn Enter để hoàn tất và thoát...")

if __name__ == "__main__":
    main()
