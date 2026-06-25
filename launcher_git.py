# -*- coding: utf-8 -*-
"""
launcher_git.py - Trình khởi chạy tự động cập nhật qua Git
==========================================================
Chạy file này trên các máy con để tự động đồng bộ code từ kho lưu trữ Git.
"""

import sys
import os
import subprocess

# Đảm bảo in tiếng Việt và unicode ra Console Windows không bị lỗi
try:
    sys.stdout.reconfigure(encoding='utf-8')
except AttributeError:
    pass

# CẤU HÌNH ĐƯỜNG DẪN GIT CẬP NHẬT
GIT_REPO_URL = "https://github.com/congtygiaan2022-crypto/Gams-TiktokDownloader.git"

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
            print("=========================================\n")
            return
        except Exception as e:
            print(f"[!] Loi khoi tao Git: {e}")
            print("=========================================\n")
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
                print("\n[!] Phat hien thay doi ve thu vien can thiet.")
                print("Dang tu dong cai dat/cap nhat cac thu vien Python...")
                try:
                    subprocess.run(
                        [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
                        check=True
                    )
                    print("[OK] Thu vien da duoc cap nhat dong bo thanh cong.")
                except Exception as e:
                    print(f"[!] Loi cap nhat thu vien tu dong: {e}")
                    print("-> Ban co the chay thu cong file Cai_Dat_Thu_Vien.bat")
            
    except subprocess.TimeoutExpired:
        print("[!] Het thoi gian cho ket noi (Timeout). Bo qua cap nhat.")
    except FileNotFoundError:
        print("[ERROR] Loi: May tinh nay chua duoc cai dat phan mem Git.")
        print("-> Vui long tai va cai dat Git tai: https://git-scm.com/")
    except Exception as e:
        print(f"[!] Khong the cap nhat: {e}")
        
    print("=========================================\n")

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
        print(f"Loi khoi chay: {e}")
        input("Nhan Enter de thoat.")
