import tkinter as tk
from tkinter import messagebox, ttk, filedialog
import subprocess
import os
import sys
import threading
import time
import config
import re

# Fix DPI
try:
    from ctypes import windll
    windll.shcore.SetProcessDpiAwareness(1)
except:
    pass

class GiaanTool:
    def __init__(self, root):
        self.root = root
        self.root.title("GiaanTesttool - Automation")
        self.root.geometry("500x700") # Increased height
        self.root.configure(bg="#1e1e1e")
        
        # --- Variables ---
        self.run_once = tk.BooleanVar(value=getattr(config, 'RUN_ONCE', True))
        self.loop_count = tk.IntVar(value=getattr(config, 'LOOP_COUNT', 5))
        self.loop_delay = tk.IntVar(value=getattr(config, 'LOOP_DELAY', 60)) # seconds
        self.download_threads = tk.IntVar(value=config.DOWNLOAD_THREADS)
        self.check_threads = tk.IntVar(value=config.CHECK_THREADS)
        self.download_path = tk.StringVar(value=getattr(config, 'DOWNLOAD_PATH', 'downloads'))
        self.download_slideshow = tk.BooleanVar(value=getattr(config, 'DOWNLOAD_SLIDESHOW', True))
        self.extract_stats = tk.BooleanVar(value=getattr(config, 'EXTRACT_STATS', True))
        self.max_videos = tk.IntVar(value=getattr(config, 'MAX_VIDEOS_PER_CHANNEL', 10))
        
        self.is_running = False
        self.stop_requested = False
        self.current_process = None # Track subprocess
        self.is_dark = getattr(config, 'IS_DARK', True) # Load from config

        # --- Styles ---
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # --- GUI Layout ---
        self.create_header()
        self.create_settings_frame()
        self.create_quick_actions_frame()
        self.create_run_frame()
        self.create_control_frame()
        self.create_console()
        
        # Apply initial theme
        self.apply_theme()

    def create_header(self):
        # Header Container
        h_frame = tk.Frame(self.root)
        h_frame.pack(fill="x", pady=(20, 10))
        
        # Title (Centered) - Using grid to center with a side button
        h_frame.grid_columnconfigure(0, weight=1)
        h_frame.grid_columnconfigure(1, weight=0)
        h_frame.grid_columnconfigure(2, weight=1)

        self.header_label = tk.Label(h_frame, text="GiaanTesttool", font=("Segoe UI", 18, "bold"), fg="#4CAF50")
        self.header_label.grid(row=0, column=1)
        
        # Theme Button (Right aligned)
        self.btn_theme = tk.Button(h_frame, text="☀/🌙", font=("Segoe UI", 10), command=self.toggle_theme, relief="flat", cursor="hand2")
        self.btn_theme.grid(row=0, column=2, sticky="e", padx=20)
        
        self.sub_label = tk.Label(self.root, text="TikTok Automation Control Panel", font=("Segoe UI", 10), fg="#888")
        self.sub_label.pack(pady=(0, 20))

    def toggle_theme(self):
        self.is_dark = not self.is_dark
        self.apply_theme()

    def apply_theme(self):
        # Palettes
        if self.is_dark:
            bg_color = "#1e1e1e"
            fg_color = "#ffffff"
            input_bg = "#333333"
            btn_neutral_bg = "#555555"
        else:
            bg_color = "#f5f5f5"
            fg_color = "#222222"
            input_bg = "#ffffff"
            btn_neutral_bg = "#dddddd"

        # 1. Update Root & Frames
        self.root.configure(bg=bg_color)
        
        # Update TK widgets manually if needed (Labels that aren't TTK)
        # However, we used TTK for most structural things, but Header/Sub were TTK Label or TK Label?
        # In this updated code I used TK Label for Header so I can control it better or consistency.
        # Let's check: In create_header I used tk.Label for header_label.
        
        self.header_label.config(bg=bg_color)
        self.sub_label.config(bg=bg_color)
        self.btn_theme.config(bg=btn_neutral_bg, fg=fg_color)
        
        # 2. Update TTK Styles
        self.style.configure("TFrame", background=bg_color)
        self.style.configure("TLabel", background=bg_color, foreground=fg_color)
        self.style.configure("TLabelframe", background=bg_color, foreground=fg_color)
        self.style.configure("TLabelframe.Label", background=bg_color, foreground=fg_color)
        self.style.configure("Header.TLabel", background=bg_color, foreground="#4CAF50")
        
        # Update Radiobuttons
        # Radio buttons were Created as TK Radiobutton in create_run_frame
        # We need to access them. Best way is to rebuild or iterate.
        # Since I didn't store them in self list, I will iterate root children? No, too risky.
        # I will simpler: Re-configure Radiobuttons using a helper if possible, OR
        # Just update the specific style they use if they were TTK.
        # Actually, let's just make the background of Radiobuttons match.
        
        # Hacky fix for RadioButtons:
        for widget in self.root.winfo_children():
            self._recursive_theme_update(widget, bg_color, fg_color, input_bg, btn_neutral_bg)

    def _recursive_theme_update(self, widget, bg, fg, input_bg, btn_bg):
        try:
            wtype = widget.winfo_class()
            
            # Recursive
            for child in widget.winfo_children():
                self._recursive_theme_update(child, bg, fg, input_bg, btn_bg)
            
            # Apply Colors based on type
            if wtype in ('Frame', 'Labelframe'):
                widget.config(bg=bg)
            elif wtype == 'Label':
                # Skip Header Label if handled manually, but safe to overwrite bg, keep fg if special?
                # Header Label FG is green, handled separately or we ignore if it has specific color?
                if widget != self.header_label:
                     widget.config(bg=bg, fg=fg)
            elif wtype == 'Radiobutton':
                widget.config(bg=bg, fg=fg, selectcolor=input_bg, activebackground=bg, activeforeground=fg)
            elif wtype == 'Button':
                # Only update "neutral" buttons like Browse or Theme. 
                # Start/Stop/Save/QuickActions have specific colors.
                # Heuristic: If current bg is white/black/grey?
                # Easier: Only update specific buttons we know.
                # But here we made a recursive loop.
                # Let's SKIP buttons in recursive loop to avoid breaking Red/Green/Blue buttons.
                # Only Update "Browse" button? 
                pass 
                
        except:
            pass
            
    def create_settings_frame(self):
        frame = ttk.Labelframe(self.root, text="Cấu Hình Hiệu Năng & Lưu Trữ", padding=15)
        frame.pack(fill="x", padx=20, pady=5)
        
        # Threads
        f1 = ttk.Frame(frame)
        f1.pack(fill="x", pady=5)
        ttk.Label(f1, text="Số luồng Download:").pack(side="left")
        ttk.Entry(f1, textvariable=self.download_threads, width=5).pack(side="right")
        
        f2 = ttk.Frame(frame)
        f2.pack(fill="x", pady=5)
        ttk.Label(f2, text="Số luồng Check (Scrape):").pack(side="left")
        ttk.Entry(f2, textvariable=self.check_threads, width=5).pack(side="right")
        
        # Max Videos per Channel
        f2_2 = ttk.Frame(frame)
        f2_2.pack(fill="x", pady=5)
        ttk.Label(f2_2, text="Số video tối đa/kênh:").pack(side="left")
        ttk.Entry(f2_2, textvariable=self.max_videos, width=5).pack(side="right")

        # Features
        f4 = ttk.Frame(frame)
        f4.pack(fill="x", pady=5)
        ttk.Checkbutton(f4, text="Tải Slideshow/Ảnh", variable=self.download_slideshow).pack(side="left", padx=(0, 10))
        ttk.Checkbutton(f4, text="Lấy Thống Kê", variable=self.extract_stats).pack(side="left")

        # Path
        f3 = ttk.Frame(frame)
        f3.pack(fill="x", pady=5)
        ttk.Label(f3, text="Thư mục lưu video:").pack(anchor="w")
        
        f3_inner = ttk.Frame(f3)
        f3_inner.pack(fill="x", pady=2)
        ttk.Entry(f3_inner, textvariable=self.download_path).pack(side="left", fill="x", expand=True)
        tk.Button(f3_inner, text="Chọn...", command=self.browse_folder, bg="#555", fg="white", relief="flat").pack(side="right", padx=(5, 0))

        # Save Button
        btn_save = tk.Button(frame, text="Lưu Cấu Hình Dashboard", bg="#2196F3", fg="white", relief="flat", command=self.save_config)
        btn_save.pack(fill="x", pady=(10, 0))

    def create_quick_actions_frame(self):
        frame = ttk.Labelframe(self.root, text="Truy Cập Nhanh", padding=15)
        frame.pack(fill="x", padx=20, pady=5)
        
        btn_channels = tk.Button(frame, text="File Kênh", bg="#607D8B", fg="white", relief="flat", command=lambda: self.open_file("danhsachtiktok.txt"))
        btn_channels.pack(side="left", fill="x", expand=True, padx=(0, 2))
        
        btn_errors = tk.Button(frame, text="Kênh Lỗi", bg="#f44336", fg="white", relief="flat", command=lambda: self.open_file("kenhloi.txt"))
        btn_errors.pack(side="left", fill="x", expand=True, padx=2)
        
        btn_history = tk.Button(frame, text="Lịch Sử", bg="#607D8B", fg="white", relief="flat", command=lambda: self.open_file("lichsutaitiktok.txt"))
        btn_history.pack(side="left", fill="x", expand=True, padx=2)
        
        btn_folder = tk.Button(frame, text="Thư Mục", bg="#607D8B", fg="white", relief="flat", command=self.open_download_folder)
        btn_folder.pack(side="left", fill="x", expand=True, padx=(2, 0))

    def open_file(self, filename):
        try:
            # Resolve relative path
            base_path = os.path.dirname(os.path.abspath(__file__))
            full_path = os.path.join(base_path, filename)
            
            if not os.path.exists(full_path):
                 # Create if not exists so it opens blank
                 with open(full_path, 'w', encoding='utf-8') as f: pass
            os.startfile(full_path)
        except Exception as e:
            messagebox.showerror("Lỗi", str(e))

    def open_download_folder(self):
        try:
            path = self.download_path.get()
            # If path is relative, make it absolute
            if not os.path.isabs(path):
                base_path = os.path.dirname(os.path.abspath(__file__))
                path = os.path.join(base_path, path)

            if not os.path.exists(path):
                os.makedirs(path)
            os.startfile(path)
        except Exception as e:
            messagebox.showerror("Lỗi", str(e))

    def browse_folder(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.download_path.set(folder_selected)

    def create_run_frame(self):
        frame = ttk.Labelframe(self.root, text="Chế Độ Chạy", padding=15)
        frame.pack(fill="x", padx=20, pady=10)
        
        # Radio
        rb1 = tk.Radiobutton(frame, text="Chạy 1 lần (Single Run)", variable=self.run_once, value=True, bg="#1e1e1e", fg="white", selectcolor="#2b2b2b", activebackground="#1e1e1e", activeforeground="white")
        rb1.pack(anchor="w")
        
        rb2 = tk.Radiobutton(frame, text="Chạy vòng lặp (Loop)", variable=self.run_once, value=False, bg="#1e1e1e", fg="white", selectcolor="#2b2b2b", activebackground="#1e1e1e", activeforeground="white")
        rb2.pack(anchor="w", pady=(5, 0))
        
        # Loop Options
        opts = ttk.Frame(frame)
        opts.pack(fill="x", padx=20, pady=5)
        
        ttk.Label(opts, text="Số vòng lặp:").grid(row=0, column=0, sticky="w", padx=5)
        ttk.Entry(opts, textvariable=self.loop_count, width=5).grid(row=0, column=1)
        
        ttk.Label(opts, text="Delay (giây):").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        ttk.Entry(opts, textvariable=self.loop_delay, width=5).grid(row=1, column=1)

    def create_control_frame(self):
        frame = ttk.Frame(self.root)
        frame.pack(fill="x", padx=20, pady=10)
        
        self.btn_start = tk.Button(frame, text="▶ BẮT ĐẦU", bg="#4CAF50", fg="white", font=("Segoe UI", 12, "bold"), height=2, relief="flat", command=self.start_process)
        self.btn_start.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        self.btn_stop = tk.Button(frame, text="■ DỪNG", bg="#f44336", fg="white", font=("Segoe UI", 12, "bold"), height=2, relief="flat", command=self.stop_process, state="disabled")
        self.btn_stop.pack(side="right", fill="x", expand=True, padx=(5, 0))
        
        # Reset small button
        btn_reset = tk.Button(self.root, text="↻ Xóa Dữ Liệu (Reset)", bg="#FF9800", fg="white", relief="flat", command=self.run_reset)
        btn_reset.pack(pady=5)

    def create_console(self):
        frame = ttk.LabelFrame(self.root, text="Log Hoạt Động", padding=5)
        frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        self.console = tk.Text(frame, height=5, bg="#000", fg="#0f0", font=("Consolas", 9), state="disabled")
        self.console.pack(fill="both", expand=True)

    def log(self, message):
        self.console.config(state="normal")
        self.console.insert("end", f"[{time.strftime('%H:%M:%S')}] {message}\n")
        self.console.see("end")
        self.console.config(state="disabled")

    def save_config(self):
        try:
            # Read config file
            config_path = "config.py"
            with open(config_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Replace logic
            content = re.sub(r'DOWNLOAD_THREADS = \d+', f'DOWNLOAD_THREADS = {self.download_threads.get()}', content)
            content = re.sub(r'CHECK_THREADS = \d+', f'CHECK_THREADS = {self.check_threads.get()}', content)
            
            # Handle Max Videos
            if 'MAX_VIDEOS_PER_CHANNEL' in content:
                content = re.sub(r'MAX_VIDEOS_PER_CHANNEL = \d+', f'MAX_VIDEOS_PER_CHANNEL = {self.max_videos.get()}', content)
            else:
                content += f'\nMAX_VIDEOS_PER_CHANNEL = {self.max_videos.get()}'

            # Handle New Features
            if 'DOWNLOAD_SLIDESHOW' in content:
                content = re.sub(r'DOWNLOAD_SLIDESHOW = (True|False)', f'DOWNLOAD_SLIDESHOW = {self.download_slideshow.get()}', content)
            else:
                content += f'\nDOWNLOAD_SLIDESHOW = {self.download_slideshow.get()}'
                
            if 'EXTRACT_STATS' in content:
                content = re.sub(r'EXTRACT_STATS = (True|False)', f'EXTRACT_STATS = {self.extract_stats.get()}', content)
            else:
                content += f'\nEXTRACT_STATS = {self.extract_stats.get()}'
            
            # Handle Path (might not exist in regex if old file, but we added it)
            current_path = self.download_path.get().replace('\\', '\\\\') # Escape backslashes for python string
            if 'DOWNLOAD_PATH' in content:
                content = re.sub(r'DOWNLOAD_PATH = ".*?"', f'DOWNLOAD_PATH = "{current_path}"', content)
            else:
                content += f'\nDOWNLOAD_PATH = "{current_path}"'

            # --- Dashboard Specific Settings ---
            # Loop options
            if 'RUN_ONCE' in content:
                content = re.sub(r'RUN_ONCE = (True|False)', f'RUN_ONCE = {self.run_once.get()}', content)
            else: content += f'\nRUN_ONCE = {self.run_once.get()}'

            if 'LOOP_COUNT' in content:
                content = re.sub(r'LOOP_COUNT = \d+', f'LOOP_COUNT = {self.loop_count.get()}', content)
            else: content += f'\nLOOP_COUNT = {self.loop_count.get()}'

            if 'LOOP_DELAY' in content:
                content = re.sub(r'LOOP_DELAY = \d+', f'LOOP_DELAY = {self.loop_delay.get()}', content)
            else: content += f'\nLOOP_DELAY = {self.loop_delay.get()}'

            if 'IS_DARK' in content:
                content = re.sub(r'IS_DARK = (True|False)', f'IS_DARK = {self.is_dark}', content)
            else: content += f'\nIS_DARK = {self.is_dark}'
            
            with open(config_path, "w", encoding="utf-8") as f:
                f.write(content)
                
            # Reload module logic not needed if we run subprocess
            self.log("Đã lưu cấu hình thành công!")
            messagebox.showinfo("Thành công", "Đã lưu cấu hình mới!")
            
        except Exception as e:
            self.log(f"Lỗi lưu config: {e}")
            messagebox.showerror("Lỗi", str(e))


    # ... (skipping unchanged parts)

    def start_process(self):
        if self.is_running: return
        self.is_running = True
        self.stop_requested = False
        self.btn_start.config(state="disabled", bg="#666")
        self.btn_stop.config(state="normal", bg="#f44336")
        
        # Run in thread
        threading.Thread(target=self.run_logic, daemon=True).start()

    def run_logic(self):
        loops = 1 if self.run_once.get() else self.loop_count.get()
        delay = self.loop_delay.get()
        
        for i in range(loops):
            if self.stop_requested: break
            
            self.log(f"--- Bắt đầu vòng lặp {i+1}/{loops} ---")
            
            try:
                # Run main.py
                # Resolve path - Handle PyInstaller Frozen state
                if getattr(sys, 'frozen', False):
                    # Running in a bundle (EXE)
                    base_path = os.path.dirname(sys.executable)
                else:
                    # Running in normal Python script
                    base_path = os.path.dirname(os.path.abspath(__file__))
                
                main_script = os.path.join(base_path, "main.py")
                
                # Start process and track it
                self.current_process = subprocess.Popen(
                    ["python", "-u", main_script], # -u for unbuffered output
                    cwd=base_path, 
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.STDOUT, # Merge stderr into stdout to prevent deadlock
                    text=True, 
                    encoding='utf-8',
                    errors='replace', # Prevent crash on non-utf8 chars
                    creationflags=subprocess.CREATE_NO_WINDOW # Optional: Hide console window
                )
                
                # Stream output
                while True:
                    if self.stop_requested: # Check flag to kill immediately
                        if self.current_process.poll() is None:
                            self.current_process.terminate()
                        break

                    # Read line-by-line unbuffered
                    line = self.current_process.stdout.readline()
                    status = self.current_process.poll()
                    
                    if not line and status is not None:
                        break
                    if line:
                        self.log(line.strip())
                
                self.current_process.wait()
                self.current_process = None # Clear after finish
                
            except Exception as e:
                self.log(f"Lỗi chạy script: {e}")

            # Cleanup
            self.log("Đang dọn dẹp (Cleanup)...")
            self.aggressive_cleanup()
            
            if i < loops - 1:
                if self.stop_requested: break
                self.log(f"Đang chờ {delay} giây trước vòng lặp mới...")
                # Sleep in chunks to allow interruption
                for s in range(delay):
                    if self.stop_requested: break
                    time.sleep(1)
            
        self.is_running = False
        self.log("--- Hoàn tất ---")
        self.root.after(0, self.reset_ui)

    def stop_process(self):
        self.stop_requested = True
        self.log("Đang yêu cầu dừng NGAY LẬP TỨC...")
        
        # Force kill if process is running
        if self.current_process and self.current_process.poll() is None:
            try:
                self.current_process.terminate() # Or .kill() for stronger kill
                self.log("Đã ngắt tiến trình chạy.")
            except Exception as e:
                self.log(f"Lỗi ngắt tiến trình: {e}")
                
        self.aggressive_cleanup()
        # UI reset will happen in run_logic when loop breaks

    def reset_ui(self):
        self.btn_start.config(state="normal", bg="#4CAF50")
        self.btn_stop.config(state="disabled", bg="#666")

    def aggressive_cleanup(self):
        """Dọn dẹp nhẹ nhàng - Chỉ log lại thay vì kill process thô bạo"""
        self.log("Đang giải phóng tài nguyên trình duyệt...")
        # Đã loại bỏ taskkill /f /im để tránh lỗi các tool khác theo yêu cầu người dùng.
        # WebDriver.quit() trong main.py và api.stop_profile() sẽ đảm nhận việc đóng session.
        pass

    def run_reset(self):
        if messagebox.askyesno("Xác nhận", "Bạn có chắc chắn muốn xóa hết Video và Lịch sử không?"):
            try:
                subprocess.run("xoa_du_lieu.bat", shell=True)
                self.log("Đã Reset dữ liệu thành công.")
            except Exception as e:
                self.log(f"Lỗi reset: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = GiaanTool(root)
    root.mainloop()
