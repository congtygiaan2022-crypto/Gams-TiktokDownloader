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

# ────────────────────────────────────────────────────────────
#  Palette
# ────────────────────────────────────────────────────────────
DARK = {
    "bg":        "#12121a",
    "panel":     "#1c1c2a",
    "card":      "#23233a",
    "border":    "#2e2e48",
    "fg":        "#e8e8f0",
    "fg2":       "#9090b0",
    "accent":    "#4ade80",      # green
    "accent2":   "#60a5fa",      # blue
    "warn":      "#fb923c",
    "danger":    "#f87171",
    "input_bg":  "#1a1a2e",
    "btn_neu":   "#2e2e48",
    "console_bg":"#0a0a12",
    "console_fg":"#4ade80",
}
LIGHT = {
    "bg":        "#f0f2f8",
    "panel":     "#ffffff",
    "card":      "#f8f9fc",
    "border":    "#d0d4e8",
    "fg":        "#1a1a2e",
    "fg2":       "#6060a0",
    "accent":    "#16a34a",
    "accent2":   "#2563eb",
    "warn":      "#ea580c",
    "danger":    "#dc2626",
    "input_bg":  "#ffffff",
    "btn_neu":   "#e2e6f0",
    "console_bg":"#1a1a2e",
    "console_fg":"#4ade80",
}


class GiaanTool:
    def __init__(self, root):
        self.root = root
        self.root.title("TikTok Automation — GiaanTesttool")
        self.root.geometry("1120x720")
        self.root.minsize(900, 600)
        self.root.configure(bg="#12121a")

        # ── state ──────────────────────────────────────────
        self.is_dark = getattr(config, 'IS_DARK', True)
        self.P = DARK if self.is_dark else LIGHT

        self.is_running       = False
        self.stop_requested   = False
        self.current_process  = None
        self._loaded_profiles = []
        self._profile_map     = {}
        self.channel_rows     = []

        active_profile_id = os.environ.get("ACTIVE_PROFILE_ID", "")
        if active_profile_id:
            self.channels_file = f"danhsachtiktok_{active_profile_id}.txt"
            self.error_file = f"kenhloi_{active_profile_id}.txt"
            self.history_file = f"lichsutaitiktok_{active_profile_id}.txt"
            profile_name = os.environ.get("ACTIVE_PROFILE_NAME", f"Profile {active_profile_id}")
            self.root.title(f"TikTok Automation — {profile_name}")
        else:
            self.channels_file = "danhsachtiktok.txt"
            self.error_file = "kenhloi.txt"
            self.history_file = "lichsutaitiktok.txt"

        # ── tk variables ───────────────────────────────────
        self.run_once           = tk.BooleanVar(value=getattr(config, 'RUN_ONCE', True))
        self.loop_count         = tk.IntVar(value=getattr(config, 'LOOP_COUNT', 5000))
        self.loop_delay         = tk.IntVar(value=getattr(config, 'LOOP_DELAY', 600))
        self.download_threads   = tk.IntVar(value=getattr(config, 'DOWNLOAD_THREADS', 3))
        self.download_path      = tk.StringVar(value=getattr(config, 'DOWNLOAD_PATH', 'downloads'))
        self.download_slideshow = tk.BooleanVar(value=getattr(config, 'DOWNLOAD_SLIDESHOW', True))
        self.extract_stats      = tk.BooleanVar(value=getattr(config, 'EXTRACT_STATS', True))
        self.max_videos         = tk.IntVar(value=getattr(config, 'MAX_VIDEOS_PER_CHANNEL', 10))

        self.browser_type         = tk.StringVar(value=getattr(config, 'BROWSER_TYPE', 'gemlogin'))
        self.gemlogin_api_url     = tk.StringVar(value=getattr(config, 'GEMLOGIN_API_URL', 'http://localhost:1010'))
        self.gpmlogin_api_url     = tk.StringVar(value=getattr(config, 'GPM_LOGIN_API_URL', 'http://localhost:60064'))
        self.donut_api_url        = tk.StringVar(value=getattr(config, 'DONUT_API_URL', 'http://127.0.0.1:10108'))
        self.donut_api_key        = tk.StringVar(value=getattr(config, 'DONUT_API_KEY', ''))
        self.selected_profile_id  = tk.StringVar(value=getattr(config, 'SELECTED_PROFILE_ID', ''))
        self.selected_profile_name= tk.StringVar(value=getattr(config, 'SELECTED_PROFILE_NAME', 'Tải video tiktok'))

        self.chrome_exe_path      = tk.StringVar(value=getattr(config, 'CHROME_EXE_PATH', ''))
        self.chrome_user_data_dir = tk.StringVar(value=getattr(config, 'CHROME_USER_DATA_DIR', ''))
        self.chrome_profile_name  = tk.StringVar(value=getattr(config, 'CHROME_PROFILE_NAME', 'Default'))
        self.chrome_debug_port    = tk.IntVar(value=getattr(config, 'CHROME_DEBUG_PORT', 9222))
        self.cococ_exe_path       = tk.StringVar(value=getattr(config, 'COCOC_EXE_PATH', ''))
        self.cococ_user_data_dir  = tk.StringVar(value=getattr(config, 'COCOC_USER_DATA_DIR', ''))
        self.cococ_profile_name   = tk.StringVar(value=getattr(config, 'COCOC_PROFILE_NAME', 'Default'))
        self.cococ_debug_port     = tk.IntVar(value=getattr(config, 'COCOC_DEBUG_PORT', 9223))

        self.rotate_profiles  = tk.BooleanVar(value=getattr(config, 'ROTATE_PROFILES', False))
        self.rotate_interval  = tk.IntVar(value=getattr(config, 'PROFILE_ROTATE_INTERVAL', 5))
        self.rotate_order     = tk.StringVar(value=getattr(config, 'PROFILE_ROTATE_ORDER', 'sequential'))

        # ── style ──────────────────────────────────────────
        self.style = ttk.Style()
        self.style.theme_use('clam')

        # ── build UI ───────────────────────────────────────
        self._build_ui()
        self._apply_theme()
        self._on_browser_type_change()

        # Save config on window close
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    # ═══════════════════════════════════════════════════════
    #  BUILD UI
    # ═══════════════════════════════════════════════════════
    def _build_ui(self):
        P = self.P

        # ─── top bar ───────────────────────────────────────
        topbar = tk.Frame(self.root, bg=P["panel"], height=56)
        topbar.pack(fill="x", side="top")
        topbar.pack_propagate(False)

        tk.Label(topbar, text="⬡", font=("Segoe UI", 20), bg=P["panel"],
                 fg=P["accent"]).pack(side="left", padx=(18, 4), pady=8)
        tk.Label(topbar, text="TikTok Automation", font=("Segoe UI", 15, "bold"),
                 bg=P["panel"], fg=P["fg"]).pack(side="left")
        tk.Label(topbar, text="  GiaanTesttool", font=("Segoe UI", 10),
                 bg=P["panel"], fg=P["fg2"]).pack(side="left", pady=(6, 0))

        # right controls on topbar
        self.btn_theme = tk.Button(
            topbar, text="🌙 Dark" if self.is_dark else "☀ Light",
            bg=P["btn_neu"], fg=P["fg"], relief="flat", cursor="hand2",
            font=("Segoe UI", 9), padx=10, pady=4,
            command=self._toggle_theme)
        self.btn_theme.pack(side="right", padx=12, pady=10)

        # ─── main body (left | right) ──────────────────────
        body = tk.Frame(self.root, bg=P["bg"])
        body.pack(fill="both", expand=True)

        # LEFT column  (fixed width)
        self.left = tk.Frame(body, bg=P["bg"], width=400)
        self.left.pack(side="left", fill="y", padx=(14, 6), pady=10)
        self.left.pack_propagate(False)

        # RIGHT column (stretches)
        self.right = tk.Frame(body, bg=P["bg"])
        self.right.pack(side="left", fill="both", expand=True, padx=(6, 14), pady=10)

        # ─── populate left ─────────────────────────────────
        self._card_settings(self.left)
        self._card_browser(self.left)
        self._card_run_mode(self.left)
        self._card_controls(self.left)

        # ─── populate right ────────────────────────────────
        self._card_quick_actions(self.right)
        self._card_backup_restore(self.right)
        self._build_notebook(self.right)

    # ═══════════════════════════════════════════════════════
    #  CARDS — left column
    # ═══════════════════════════════════════════════════════
    def _make_card(self, parent, title, icon=""):
        P = self.P
        outer = tk.Frame(parent, bg=P["card"],
                         highlightbackground=P["border"], highlightthickness=1)
        outer.pack(fill="x", pady=(0, 8))

        head = tk.Frame(outer, bg=P["border"], height=1)
        head.pack(fill="x")

        title_bar = tk.Frame(outer, bg=P["card"])
        title_bar.pack(fill="x", padx=12, pady=(8, 4))
        tk.Label(title_bar, text=f"{icon}  {title}" if icon else title,
                 font=("Segoe UI", 9, "bold"), bg=P["card"],
                 fg=P["accent2"]).pack(side="left")

        body = tk.Frame(outer, bg=P["card"])
        body.pack(fill="x", padx=12, pady=(2, 10))
        return body

    def _row(self, parent, label_text, widget_fn, label_width=16):
        """Helper: label + widget on one line."""
        P = self.P
        f = tk.Frame(parent, bg=P["card"])
        f.pack(fill="x", pady=3)
        tk.Label(f, text=label_text, width=label_width, anchor="w",
                 bg=P["card"], fg=P["fg2"],
                 font=("Segoe UI", 9)).pack(side="left")
        widget_fn(f)
        return f

    def _entry(self, parent, var, width=8):
        e = tk.Entry(parent, textvariable=var, width=width,
                     bg=self.P["input_bg"], fg=self.P["fg"],
                     insertbackground=self.P["fg"],
                     relief="flat", font=("Segoe UI", 9),
                     highlightthickness=1,
                     highlightbackground=self.P["border"],
                     highlightcolor=self.P["accent2"])
        e.pack(side="left", fill="x", expand=True, padx=(0, 4))
        e.bind("<FocusOut>", lambda event: self.save_config(show_msg=False, log_msg=False))
        return e

    def _btn(self, parent, text, cmd, color=None, side="left", padx=(0,0)):
        P = self.P
        bg = color or P["btn_neu"]
        fg = P["fg"] if not color else "#ffffff"
        b = tk.Button(parent, text=text, command=cmd, bg=bg, fg=fg,
                      relief="flat", cursor="hand2", font=("Segoe UI", 8),
                      padx=8, pady=3)
        b.pack(side=side, padx=padx)
        return b

    # ── card: Settings ──────────────────────────────────────
    def _card_settings(self, parent):
        body = self._make_card(parent, "Cấu hình chung", "⚙")

        self._row(body, "Luồng Download", lambda f:
            self._entry(f, self.download_threads, 5))
        self._row(body, "Video tối đa/kênh", lambda f:
            self._entry(f, self.max_videos, 5))

        # path row with browse button
        def path_row(f):
            self._entry(f, self.download_path)
            self._btn(f, "📂", self._browse_folder, color=self.P["btn_neu"])
        self._row(body, "Thư mục lưu", path_row)

        # checkboxes
        chk_f = tk.Frame(body, bg=self.P["card"])
        chk_f.pack(fill="x", pady=(4, 0))
        for text, var in [("Tải Slideshow/Ảnh", self.download_slideshow),
                          ("Lấy thống kê", self.extract_stats)]:
            cb = tk.Checkbutton(chk_f, text=text, variable=var,
                                bg=self.P["card"], fg=self.P["fg"],
                                selectcolor=self.P["input_bg"],
                                activebackground=self.P["card"],
                                activeforeground=self.P["fg"],
                                font=("Segoe UI", 9))
            cb.pack(side="left", padx=(0, 12))

        self._btn(body, "💾  Lưu Cấu Hình", self.save_config,
                  color=self.P["accent2"], side="right", padx=(0,0))

    # ── card: Browser ───────────────────────────────────────
    def _card_browser(self, parent):
        self.browser_card_body = self._make_card(parent, "Trình duyệt & Profile", "🌐")
        body = self.browser_card_body

        # ── browser type radio row 1 ──
        type_f = tk.Frame(body, bg=self.P["card"])
        type_f.pack(fill="x", pady=(0, 2))
        tk.Label(type_f, text="Loại:", width=16, anchor="w",
                 bg=self.P["card"], fg=self.P["fg2"],
                 font=("Segoe UI", 9)).pack(side="left")

        # ── browser type radio row 2 ──
        type_f2 = tk.Frame(body, bg=self.P["card"])
        type_f2.pack(fill="x", pady=(0, 6))
        tk.Label(type_f2, text="", width=16, anchor="w",
                 bg=self.P["card"], fg=self.P["fg2"],
                 font=("Segoe UI", 9)).pack(side="left")

        self._radio_buttons = []

        # Row 1: GemLogin, GPM Login, Donut
        for label, val, color in [
            ("GemLogin",  "gemlogin",  "#a78bfa"),
            ("GPM Login", "gpmlogin",  "#60a5fa"),
            ("Donut",     "donut",     "#f43f5e"),
        ]:
            rb = tk.Radiobutton(
                type_f, text=label, variable=self.browser_type, value=val,
                bg=self.P["card"], fg=color, selectcolor=self.P["input_bg"],
                activebackground=self.P["card"], activeforeground=color,
                font=("Segoe UI", 9, "bold"), cursor="hand2",
                command=self._on_browser_type_change)
            rb.pack(side="left", padx=(0, 8))
            self._radio_buttons.append(rb)

        # Row 2: Chrome, Cốc Cốc
        for label, val, color in [
            ("Chrome",    "chrome",    "#34d399"),
            ("Cốc Cốc",  "cococ",     "#fb923c"),
        ]:
            rb = tk.Radiobutton(
                type_f2, text=label, variable=self.browser_type, value=val,
                bg=self.P["card"], fg=color, selectcolor=self.P["input_bg"],
                activebackground=self.P["card"], activeforeground=color,
                font=("Segoe UI", 9, "bold"), cursor="hand2",
                command=self._on_browser_type_change)
            rb.pack(side="left", padx=(0, 8))
            self._radio_buttons.append(rb)

        # ── API section (GemLogin / GPM / Donut) ──
        self.sec_api = tk.Frame(body, bg=self.P["card"])

        def api_url_row(f):
            self.ent_api_url = self._entry(f, self.gemlogin_api_url)
            self._btn(f, "✔ Test", self._check_browser_api, color="#7c3aed")
        self.row_api_url = self._row(self.sec_api, "API URL", api_url_row)

        def api_key_row(f):
            self.ent_api_key = self._entry(f, self.donut_api_key)
        self.row_api_key = self._row(self.sec_api, "API Key / Token", api_key_row)

        def profile_row(f):
            self.cmb_profile = ttk.Combobox(f, state="readonly",
                                             font=("Segoe UI", 9), width=22)
            self.cmb_profile.pack(side="left", padx=(0, 4), fill="x", expand=True)
            self.cmb_profile.bind("<<ComboboxSelected>>", self._on_profile_selected)
            self._btn(f, "🔄 Tải", self._load_profiles, color="#0f766e")
        self.row_profile = self._row(self.sec_api, "Profile", profile_row)

        # rotate sub-row
        self.rot_f = tk.Frame(self.sec_api, bg=self.P["card"])
        self.rot_f.pack(fill="x", pady=3)
        self.cb_rotate = tk.Checkbutton(
            self.rot_f, text="Xoay profile sau mỗi", variable=self.rotate_profiles,
            bg=self.P["card"], fg=self.P["fg"], selectcolor=self.P["input_bg"],
            activebackground=self.P["card"], activeforeground=self.P["fg"],
            font=("Segoe UI", 9), command=self._on_rotate_toggle)
        self.cb_rotate.pack(side="left")
        tk.Spinbox(self.rot_f, textvariable=self.rotate_interval, from_=1, to=100,
                   width=4, bg=self.P["input_bg"], fg=self.P["fg"],
                   buttonbackground=self.P["btn_neu"], relief="flat",
                   font=("Segoe UI", 9)).pack(side="left", padx=4)
        tk.Label(self.rot_f, text="kênh", bg=self.P["card"], fg=self.P["fg2"],
                 font=("Segoe UI", 9)).pack(side="left")

        self.ord_f = tk.Frame(self.sec_api, bg=self.P["card"])
        self.ord_f.pack(fill="x", pady=(0, 2))
        tk.Label(self.ord_f, text="Thứ tự:", width=16, anchor="w",
                 bg=self.P["card"], fg=self.P["fg2"],
                 font=("Segoe UI", 9)).pack(side="left")
        for txt, val in [("Tuần tự", "sequential"), ("Ngẫu nhiên", "random")]:
            tk.Radiobutton(self.ord_f, text=txt, variable=self.rotate_order, value=val,
                           bg=self.P["card"], fg=self.P["fg"],
                           selectcolor=self.P["input_bg"],
                           activebackground=self.P["card"],
                           activeforeground=self.P["fg"],
                           font=("Segoe UI", 9)).pack(side="left", padx=(0,8))

        # ── Chrome section ──
        self.sec_chrome = tk.Frame(body, bg=self.P["card"])
        self._native_section(self.sec_chrome,
                             exe_var=self.chrome_exe_path,
                             data_var=self.chrome_user_data_dir,
                             prof_attr="cmb_chrome_profile",
                             prof_var=self.chrome_profile_name,
                             port_var=self.chrome_debug_port,
                             reload_fn=self._reload_chrome_profiles,
                             autodetect_fn=self._autodetect_chrome)

        # ── Cốc Cốc section ──
        self.sec_cococ = tk.Frame(body, bg=self.P["card"])
        self._native_section(self.sec_cococ,
                             exe_var=self.cococ_exe_path,
                             data_var=self.cococ_user_data_dir,
                             prof_attr="cmb_cococ_profile",
                             prof_var=self.cococ_profile_name,
                             port_var=self.cococ_debug_port,
                             reload_fn=self._reload_cococ_profiles,
                             autodetect_fn=self._autodetect_cococ)

    def _native_section(self, parent, exe_var, data_var, prof_attr,
                         prof_var, port_var, reload_fn, autodetect_fn):
        """Shared layout for Chrome and Cốc Cốc native sections."""
        P = self.P

        def exe_row(f):
            self._entry(f, exe_var)
            self._btn(f, "📂", lambda: self._browse_exe(exe_var), color=P["btn_neu"])
        self._row(parent, "Exe (tự tìm nếu trống)", exe_row, label_width=18)

        def data_row(f):
            self._entry(f, data_var)
            self._btn(f, "📂", lambda: self._browse_dir(data_var), color=P["btn_neu"])
        self._row(parent, "User Data (tự tìm nếu trống)", data_row, label_width=18)

        def prof_row(f):
            cmb = ttk.Combobox(f, textvariable=prof_var,
                               font=("Segoe UI", 9), width=16)
            cmb.pack(side="left", padx=(0, 4), fill="x", expand=True)
            cmb.bind("<<ComboboxSelected>>", lambda event: self.save_config(show_msg=False, log_msg=False))
            setattr(self, prof_attr, cmb)
            self._btn(f, "🔄 Đọc", reload_fn, color="#0f766e")
            tk.Label(f, text="Port:", bg=P["card"], fg=P["fg2"],
                     font=("Segoe UI", 9)).pack(side="left", padx=(6, 2))
            tk.Spinbox(f, textvariable=port_var, from_=9000, to=9999, width=6,
                       bg=P["input_bg"], fg=P["fg"],
                       buttonbackground=P["btn_neu"],
                       relief="flat", font=("Segoe UI", 9)).pack(side="left")
        self._row(parent, "Profile / Port", prof_row, label_width=18)

        # auto-detect button
        btn_f = tk.Frame(parent, bg=P["card"])
        btn_f.pack(fill="x", pady=(2, 0))
        self._btn(btn_f, "🔍  Tự Phát Hiện Exe & User Data",
                  autodetect_fn, color="#7c3aed")

    # ── card: Run Mode ──────────────────────────────────────
    def _card_run_mode(self, parent):
        body = self._make_card(parent, "Chế độ chạy", "🔁")
        P = self.P

        rb_f = tk.Frame(body, bg=P["card"])
        rb_f.pack(fill="x", pady=(0, 4))
        for text, val in [("Chạy 1 lần", True), ("Vòng lặp", False)]:
            tk.Radiobutton(rb_f, text=text, variable=self.run_once, value=val,
                           bg=P["card"], fg=P["fg"], selectcolor=P["input_bg"],
                           activebackground=P["card"], activeforeground=P["fg"],
                           font=("Segoe UI", 9)).pack(side="left", padx=(0, 16))

        self._row(body, "Số vòng lặp", lambda f:
            self._entry(f, self.loop_count, 6))
        self._row(body, "Delay (giây)", lambda f:
            self._entry(f, self.loop_delay, 6))

    # ── card: Controls ──────────────────────────────────────
    def _card_controls(self, parent):
        P = self.P
        f = tk.Frame(parent, bg=P["bg"])
        f.pack(fill="x", pady=(0, 8))

        self.btn_start = tk.Button(
            f, text="▶  BẮT ĐẦU", bg=P["accent"], fg="#0a1a0a",
            font=("Segoe UI", 11, "bold"), relief="flat", cursor="hand2",
            height=2, command=self.start_process)
        self.btn_start.pack(side="left", fill="x", expand=True, padx=(0, 5))

        self.btn_stop = tk.Button(
            f, text="■  DỪNG", bg="#4a1818", fg=P["danger"],
            font=("Segoe UI", 11, "bold"), relief="flat", cursor="hand2",
            height=2, state="disabled", command=self.stop_process)
        self.btn_stop.pack(side="right", fill="x", expand=True, padx=(5, 0))

        # Reset row
        btn_reset = tk.Button(
            parent, text="↻  Xóa Dữ Liệu (Reset)", bg="#2a1200",
            fg=P["warn"], relief="flat", cursor="hand2",
            font=("Segoe UI", 9), command=self.run_reset)
        btn_reset.pack(fill="x")

    # ═══════════════════════════════════════════════════════
    #  CARDS — right column
    # ═══════════════════════════════════════════════════════
    def _card_quick_actions(self, parent):
        body = self._make_card(parent, "Truy cập nhanh", "⚡")
        P = self.P

        actions = [
            ("📋  File Kênh",    lambda: self._open_file(self.channels_file), "#1e3a5f"),
            ("⚠  Kênh Lỗi",     lambda: self._open_file(self.error_file),         "#3a1a1a"),
            ("📜  Lịch Sử Tải", lambda: self._open_file(self.history_file), "#1a2e1a"),
            ("📁  Thư Mục",     self._open_download_folder,                      "#1a1a2e"),
        ]
        btn_row = tk.Frame(body, bg=P["card"])
        btn_row.pack(fill="x")
        for text, cmd, bg in actions:
            b = tk.Button(btn_row, text=text, command=cmd, bg=bg, fg=P["fg"],
                          relief="flat", cursor="hand2",
                          font=("Segoe UI", 9), padx=6, pady=6)
            b.pack(side="left", fill="x", expand=True, padx=(0, 4))

    def _card_backup_restore(self, parent):
        body = self._make_card(parent, "Sao Lưu & Khôi Phục Dữ Liệu", "💾")
        P = self.P

        btn_row = tk.Frame(body, bg=P["card"])
        btn_row.pack(fill="x")

        # Backup Button
        btn_backup = tk.Button(
            btn_row, text="📤 Sao Lưu Profile", bg="#059669", fg="#ffffff",
            relief="flat", cursor="hand2", font=("Segoe UI", 9, "bold"),
            padx=10, pady=6, command=self.backup_current_profile_ui
        )
        btn_backup.pack(side="left", fill="x", expand=True, padx=(0, 4))

        # Restore Button
        btn_restore = tk.Button(
            btn_row, text="📥 Khôi Phục Profile", bg="#d97706", fg="#ffffff",
            relief="flat", cursor="hand2", font=("Segoe UI", 9, "bold"),
            padx=10, pady=6, command=self.restore_current_profile_ui
        )
        btn_restore.pack(side="left", fill="x", expand=True, padx=(4, 0))

    def _card_console(self, parent):
        P = self.P
        outer = tk.Frame(parent, bg=P["card"],
                         highlightbackground=P["border"], highlightthickness=1)
        outer.pack(fill="both", expand=True)

        head = tk.Frame(outer, bg=P["card"])
        head.pack(fill="x", padx=12, pady=(8, 4))
        tk.Label(head, text="🖥  Log Hoạt Động", font=("Segoe UI", 9, "bold"),
                 bg=P["card"], fg=P["accent2"]).pack(side="left")

        # Status badge
        self.status_badge = tk.Label(head, text="⬤ Chờ", bg=P["card"],
                                      fg=P["fg2"], font=("Segoe UI", 9))
        self.status_badge.pack(side="right")

        # Clear button
        tk.Button(head, text="✕ Xóa log", bg=P["btn_neu"], fg=P["fg2"],
                  relief="flat", font=("Segoe UI", 8), cursor="hand2",
                  padx=6, pady=1,
                  command=lambda: (
                      self.console.config(state="normal"),
                      self.console.delete("1.0", "end"),
                      self.console.config(state="disabled")
                  )).pack(side="right", padx=6)

        self.console = tk.Text(
            outer, bg=P["console_bg"], fg=P["console_fg"],
            font=("Consolas", 9), state="disabled",
            relief="flat", padx=8, pady=6,
            insertbackground=P["console_fg"],
            selectbackground=P["border"])
        self.console.pack(fill="both", expand=True, padx=2, pady=(0, 2))

        # tags for colored log lines
        self.console.tag_config("ok",   foreground="#4ade80")
        self.console.tag_config("warn", foreground="#fb923c")
        self.console.tag_config("err",  foreground="#f87171")
        self.console.tag_config("info", foreground="#60a5fa")
        self.console.tag_config("dim",  foreground="#6060a0")

        # scrollbar
        sb = ttk.Scrollbar(outer, command=self.console.yview)
        self.console["yscrollcommand"] = sb.set

    # ═══════════════════════════════════════════════════════
    #  THEME
    # ═══════════════════════════════════════════════════════
    def _toggle_theme(self):
        self.is_dark = not self.is_dark
        self.P = DARK if self.is_dark else LIGHT
        label = "🌙 Dark" if self.is_dark else "☀ Light"
        self.btn_theme.config(text=label)
        self._apply_theme()

    def _apply_theme(self):
        P = self.P
        self.style.configure("TFrame",      background=P["bg"])
        self.style.configure("TLabel",      background=P["bg"], foreground=P["fg"])
        self.style.configure("TLabelframe", background=P["card"], foreground=P["fg"])
        self.style.configure("TLabelframe.Label", background=P["card"], foreground=P["fg"])
        self.style.configure("TCombobox",   fieldbackground=P["input_bg"],
                             background=P["btn_neu"], foreground=P["fg"],
                             selectbackground=P["border"],
                             arrowcolor=P["fg"])
        self.style.map("TCombobox",
                       fieldbackground=[("readonly", P["input_bg"])],
                       foreground=[("readonly", P["fg"])])
        
        # Style for Notebook & Tabs
        self.style.configure("TNotebook", background=P["bg"], borderwidth=0)
        self.style.configure("TNotebook.Tab",
                             background=P["card"],
                             foreground=P["fg2"],
                             padding=[12, 6],
                             font=("Segoe UI", 9, "bold"),
                             borderwidth=1,
                             lightcolor=P["border"],
                             darkcolor=P["border"])
        self.style.map("TNotebook.Tab",
                       background=[("selected", P["border"])],
                       foreground=[("selected", P["fg"])])

        self._retheme(self.root, P)

    def _retheme(self, widget, P):
        try:
            wc = widget.winfo_class()
            if wc in ("Frame", "Labelframe"):
                widget.configure(bg=P["bg"] if widget == self.root else P["card"])
            elif wc == "Label":
                widget.configure(bg=widget.master.cget("bg"), fg=P["fg"])
            elif wc in ("Radiobutton", "Checkbutton"):
                widget.configure(bg=widget.master.cget("bg"),
                                 selectcolor=P["input_bg"],
                                 activebackground=widget.master.cget("bg"))
        except Exception:
            pass
        for child in widget.winfo_children():
            self._retheme(child, P)

    # ═══════════════════════════════════════════════════════
    #  BROWSER LOGIC
    # ═══════════════════════════════════════════════════════
    def _on_browser_type_change(self):
        try:
            self.save_config(show_msg=False)
        except Exception:
            pass
        b = self.browser_type.get()
        is_api    = b in ("gemlogin", "gpmlogin", "donut")
        is_chrome = (b == "chrome")
        is_cococ  = (b == "cococ")

        # Hide API subrows first to rearrange order cleanly
        if hasattr(self, "row_api_url"): self.row_api_url.pack_forget()
        if hasattr(self, "row_api_key"): self.row_api_key.pack_forget()
        if hasattr(self, "row_profile"): self.row_profile.pack_forget()
        if hasattr(self, "rot_f"): self.rot_f.pack_forget()
        if hasattr(self, "ord_f"): self.ord_f.pack_forget()

        if is_api:
            if b == "gemlogin":
                url_var = self.gemlogin_api_url
            elif b == "gpmlogin":
                url_var = self.gpmlogin_api_url
            else: # donut
                url_var = self.donut_api_url
            self.ent_api_url.config(textvariable=url_var)

            # Repack in correct order
            self.row_api_url.pack(fill="x", pady=3)
            if b == "donut":
                self.row_api_key.pack(fill="x", pady=3)
            self.row_profile.pack(fill="x", pady=3)
            self.rot_f.pack(fill="x", pady=3)
            self.ord_f.pack(fill="x", pady=(0, 2))

        # show/hide sections
        self.sec_api.pack_forget()
        self.sec_chrome.pack_forget()
        self.sec_cococ.pack_forget()
        if is_api:
            self.sec_api.pack(fill="x")
            threading.Thread(target=self._load_profiles, daemon=True).start()
        elif is_chrome:
            self.sec_chrome.pack(fill="x")
            self._reload_chrome_profiles()
        else:
            self.sec_cococ.pack(fill="x")
            self._reload_cococ_profiles()

    def _on_rotate_toggle(self):
        pass  # options always visible

    def _on_profile_selected(self, event=None):
        name = self.cmb_profile.get()
        if name in self._profile_map:
            pid = self._profile_map[name]
            self.selected_profile_id.set(str(pid))
            self.selected_profile_name.set(name)
            self.log(f"✔ Chọn profile: {name}  (ID: {pid})", "ok")
            self.save_config(show_msg=False, log_msg=False)

    def _load_profiles(self):
        try:
            self.save_config(show_msg=False)
        except Exception:
            pass
        def _run():
            try:
                b_type  = self.browser_type.get()
                if b_type == "gemlogin":
                    api_url = self.gemlogin_api_url.get()
                elif b_type == "gpmlogin":
                    api_url = self.gpmlogin_api_url.get()
                else: # donut
                    api_url = self.donut_api_url.get()

                self.log(f"Đang tải profile từ {b_type}…", "info")
                import requests as _req

                if b_type == "gemlogin":
                    resp = _req.get(f"{api_url}/api/profiles", timeout=10)
                    resp.raise_for_status()
                    profiles = resp.json().get("data", [])
                elif b_type == "gpmlogin":
                    resp = _req.get(f"{api_url}/api/v3/profiles", timeout=10)
                    resp.raise_for_status()
                    data = resp.json()
                    profiles = data if isinstance(data, list) else data.get("data", [])
                else: # donut
                    headers = {'Content-Type': 'application/json'}
                    api_key = self.donut_api_key.get().strip()
                    if api_key:
                        headers['Authorization'] = f'Bearer {api_key}'
                    resp = _req.get(f"{api_url}/v1/profiles", headers=headers, timeout=10)
                    resp.raise_for_status()
                    data = resp.json()
                    if isinstance(data, list):
                        profiles = data
                    else:
                        self.log(f"Keys phản hồi từ Donut: {list(data.keys())}", "info")
                        profiles = (data.get("profiles") or data.get("data") or data.get("list") or data.get("items") or [])

                self._loaded_profiles = profiles
                self._profile_map = {}
                names = []
                for p in profiles:
                    pid  = str(p.get("id") or p.get("uuid") or p.get("profile_id") or "")
                    name = p.get("name") or pid or "Unknown"
                    self._profile_map[name] = pid
                    names.append(name)

                def _upd():
                    self.cmb_profile["values"] = names
                    saved = self.selected_profile_name.get()
                    if saved in names:
                        self.cmb_profile.set(saved)
                    elif names:
                        self.cmb_profile.current(0)
                        self._on_profile_selected()
                    self.log(f"✔ Đã tải {len(names)} profile.", "ok")
                self.root.after(0, _upd)
            except Exception as e:
                err_msg = f"✗ Lỗi tải profile: {e}"
                self.root.after(0, lambda: self.log(err_msg, "err"))
        threading.Thread(target=_run, daemon=True).start()

    def _check_browser_api(self):
        try:
            self.save_config(show_msg=False)
        except Exception:
            pass
        def _run():
            b_type  = self.browser_type.get()
            if b_type == "gemlogin":
                api_url = self.gemlogin_api_url.get()
                ep   = "/api/profiles"
                headers = {}
            elif b_type == "gpmlogin":
                api_url = self.gpmlogin_api_url.get()
                ep   = "/api/v3/profiles"
                headers = {}
            else: # donut
                api_url = self.donut_api_url.get()
                ep   = "/v1/profiles"
                headers = {}
                api_key = self.donut_api_key.get().strip()
                if api_key:
                    headers['Authorization'] = f'Bearer {api_key}'
            try:
                import requests as _req
                self.log(f"Kiểm tra {api_url}{ep}…", "info")
                resp = _req.get(f"{api_url}{ep}", headers=headers, timeout=5)
                if resp.status_code == 200:
                    self.root.after(0, lambda: messagebox.showinfo(
                        "✔ Thành công", f"Kết nối {b_type} thành công!"))
                    self.log(f"✔ {b_type} OK.", "ok")
                else:
                    self.log(f"✗ HTTP {resp.status_code}", "err")
            except Exception as e:
                err_msg = str(e)
                self.root.after(0, lambda: messagebox.showerror("Lỗi", err_msg))
                self.log(f"✗ {e}", "err")
        threading.Thread(target=_run, daemon=True).start()

    def _autodetect_chrome(self):
        """Tự phát hiện Chrome exe + User Data và điền vào fields."""
        def _run():
            from browser import Browser
            b = Browser()
            exe  = b._find_chrome_exe()
            data = b._find_chrome_user_data()
            def _upd():
                if exe:
                    self.chrome_exe_path.set(exe)
                    self.log(f"✔ Chrome exe: {exe}", "ok")
                else:
                    self.log("✗ Không tìm thấy Chrome exe.", "warn")
                if data:
                    self.chrome_user_data_dir.set(data)
                    self.log(f"✔ Chrome User Data: {data}", "ok")
                    self._reload_chrome_profiles()
                else:
                    self.log("✗ Không tìm thấy Chrome User Data.", "warn")
            self.root.after(0, _upd)
        threading.Thread(target=_run, daemon=True).start()

    def _autodetect_cococ(self):
        """Tự phát hiện Cốc Cốc exe + User Data và điền vào fields."""
        def _run():
            from browser import Browser
            b = Browser()
            exe  = b._find_cococ_exe()
            data = b._find_cococ_user_data()
            def _upd():
                if exe:
                    self.cococ_exe_path.set(exe)
                    self.log(f"✔ Cốc Cốc exe: {exe}", "ok")
                else:
                    self.log("✗ Không tìm thấy Cốc Cốc exe.", "warn")
                if data:
                    self.cococ_user_data_dir.set(data)
                    self.log(f"✔ Cốc Cốc User Data: {data}", "ok")
                    self._reload_cococ_profiles()
                else:
                    self.log("✗ Không tìm thấy Cốc Cốc User Data.", "warn")
            self.root.after(0, _upd)
        threading.Thread(target=_run, daemon=True).start()

    def _reload_chrome_profiles(self):
        self._reload_native_profiles(
            self.chrome_user_data_dir.get(),
            self.cmb_chrome_profile,
            self.chrome_profile_name,
            "Chrome")

    def _reload_cococ_profiles(self):
        self._reload_native_profiles(
            self.cococ_user_data_dir.get(),
            self.cmb_cococ_profile,
            self.cococ_profile_name,
            "Cốc Cốc")

    def _reload_native_profiles(self, user_data_dir, combobox, var, label):
        # Auto-find if empty
        if not user_data_dir or not os.path.isdir(user_data_dir):
            from browser import Browser
            b = Browser()
            found = (b._find_chrome_user_data() if label == "Chrome"
                     else b._find_cococ_user_data())
            if found:
                user_data_dir = found
                if label == "Chrome":
                    self.chrome_user_data_dir.set(found)
                else:
                    self.cococ_user_data_dir.set(found)
                self.log(f"✔ {label} User Data: {found}", "ok")
            else:
                self.log(f"✗ Không tìm thấy {label} User Data. Chọn thư mục thủ công.", "warn")
                return

        import json as _json
        profiles = []
        try:
            for item in os.listdir(user_data_dir):
                item_path = os.path.join(user_data_dir, item)
                if os.path.isdir(item_path) and (item == "Default" or item.startswith("Profile ")):
                    pref_file = os.path.join(item_path, "Preferences")
                    display = item
                    if os.path.exists(pref_file):
                        try:
                            with open(pref_file, 'r', encoding='utf-8', errors='ignore') as f:
                                prefs = _json.load(f)
                            name = prefs.get('profile', {}).get('name', '')
                            if name:
                                display = f"{name} ({item})"
                        except:
                            pass
                    profiles.append((display, item))
        except Exception as e:
            self.log(f"✗ Lỗi đọc profile {label}: {e}", "err")
            return

        if profiles:
            names = [d for d, _ in profiles]
            combobox["values"] = names
            saved = var.get()
            # try to find by dir name
            matched = next((d for d, k in profiles if k == saved or d == saved), None)
            combobox.set(matched or names[0])
            self.log(f"✔ {len(profiles)} profile {label}.", "ok")
        else:
            self.log(f"✗ Không có profile {label} nào trong thư mục đó.", "warn")

    # ═══════════════════════════════════════════════════════
    #  FILE / FOLDER HELPERS
    # ═══════════════════════════════════════════════════════
    def _base(self):
        return (os.path.dirname(sys.executable)
                if getattr(sys, 'frozen', False)
                else os.path.dirname(os.path.abspath(__file__)))

    def _open_file(self, filename):
        try:
            p = os.path.join(self._base(), filename)
            if not os.path.exists(p):
                open(p, 'w', encoding='utf-8').close()
            os.startfile(p)
        except Exception as e:
            messagebox.showerror("Lỗi", str(e))

    def _open_download_folder(self):
        try:
            path = self.download_path.get()
            if not os.path.isabs(path):
                path = os.path.join(self._base(), path)
            os.makedirs(path, exist_ok=True)
            os.startfile(path)
        except Exception as e:
            messagebox.showerror("Lỗi", str(e))

    def _browse_folder(self):
        d = filedialog.askdirectory()
        if d:
            self.download_path.set(d)

    def _browse_exe(self, var):
        p = filedialog.askopenfilename(filetypes=[("Executable", "*.exe"), ("All", "*.*")])
        if p:
            var.set(p)

    def _browse_dir(self, var):
        d = filedialog.askdirectory()
        if d:
            var.set(d)

    # ═══════════════════════════════════════════════════════
    #  SAVE CONFIG
    # ═══════════════════════════════════════════════════════
    def save_config(self, show_msg=True, log_msg=True):
        active_profile_id = os.environ.get("ACTIVE_PROFILE_ID", "")
        if active_profile_id:
            try:
                import json as _json
                settings = {
                    "DOWNLOAD_THREADS":       self.download_threads.get(),
                    "MAX_VIDEOS_PER_CHANNEL": self.max_videos.get(),
                    "DOWNLOAD_SLIDESHOW":     self.download_slideshow.get(),
                    "EXTRACT_STATS":          self.extract_stats.get(),
                    "DOWNLOAD_PATH":          self.download_path.get(),
                    "RUN_ONCE":               self.run_once.get(),
                    "LOOP_COUNT":             self.loop_count.get(),
                    "LOOP_DELAY":             self.loop_delay.get(),
                    "IS_DARK":                self.is_dark,

                    "BROWSER_TYPE":           self.browser_type.get(),
                    "GEMLOGIN_API_URL":       self.gemlogin_api_url.get(),
                    "GPM_LOGIN_API_URL":      self.gpmlogin_api_url.get(),
                    "DONUT_API_URL":          self.donut_api_url.get(),
                    "DONUT_API_KEY":          self.donut_api_key.get(),
                    "SELECTED_PROFILE_ID":    self.selected_profile_id.get(),
                    "SELECTED_PROFILE_NAME":  self.selected_profile_name.get(),

                    "CHROME_EXE_PATH":        self.chrome_exe_path.get(),
                    "CHROME_USER_DATA_DIR":   self.chrome_user_data_dir.get(),
                    "CHROME_PROFILE_NAME":    self.chrome_profile_name.get(),
                    "CHROME_DEBUG_PORT":      self.chrome_debug_port.get(),
                    "COCOC_EXE_PATH":         self.cococ_exe_path.get(),
                    "COCOC_USER_DATA_DIR":    self.cococ_user_data_dir.get(),
                    "COCOC_PROFILE_NAME":     self.cococ_profile_name.get(),
                    "COCOC_DEBUG_PORT":       self.cococ_debug_port.get(),

                    "ROTATE_PROFILES":         self.rotate_profiles.get(),
                    "PROFILE_ROTATE_INTERVAL": self.rotate_interval.get(),
                    "PROFILE_ROTATE_ORDER":    self.rotate_order.get()
                }

                cfg_json = os.path.join(self._base(), f"config_profile_{active_profile_id}.json")
                with open(cfg_json, "w", encoding="utf-8") as f:
                    _json.dump(settings, f, indent=4, ensure_ascii=False)

                if log_msg:
                    self.log(f"✔ Đã lưu cấu hình Profile {active_profile_id}.", "ok")
                if show_msg:
                    messagebox.showinfo("Thành công", f"Đã lưu cấu hình mới cho Profile {active_profile_id}!")
            except Exception as e:
                self.log(f"✗ Lỗi lưu cấu hình Profile: {e}", "err")
                if show_msg:
                    messagebox.showerror("Lỗi", str(e))
        else:
            try:
                cfg = os.path.join(self._base(), "config.py")
                with open(cfg, "r", encoding="utf-8") as f:
                    content = f.read()

                def _uoa(key, value, is_str=False):
                    nonlocal content
                    pattern = rf'^{re.escape(key)}\s*=.*'
                    if is_str:
                        repl = f'{key} = {repr(str(value))}'
                    else:
                        repl = f'{key} = {value}'
                    if re.search(pattern, content, flags=re.MULTILINE):
                        content = re.sub(pattern, lambda m: repl, content, flags=re.MULTILINE)
                    else:
                        content = content.rstrip() + f'\n{repl}\n'

                _uoa("DOWNLOAD_THREADS",      self.download_threads.get())
                _uoa("MAX_VIDEOS_PER_CHANNEL",self.max_videos.get())
                _uoa("DOWNLOAD_SLIDESHOW",    self.download_slideshow.get())
                _uoa("EXTRACT_STATS",         self.extract_stats.get())
                _uoa("DOWNLOAD_PATH",         self.download_path.get(), True)
                _uoa("RUN_ONCE",              self.run_once.get())
                _uoa("LOOP_COUNT",            self.loop_count.get())
                _uoa("LOOP_DELAY",            self.loop_delay.get())
                _uoa("IS_DARK",               self.is_dark)

                _uoa("BROWSER_TYPE",          self.browser_type.get(), True)
                _uoa("GEMLOGIN_API_URL",      self.gemlogin_api_url.get(), True)
                _uoa("GPM_LOGIN_API_URL",     self.gpmlogin_api_url.get(), True)
                _uoa("DONUT_API_URL",         self.donut_api_url.get(), True)
                _uoa("DONUT_API_KEY",         self.donut_api_key.get(), True)
                _uoa("SELECTED_PROFILE_ID",   self.selected_profile_id.get(), True)
                _uoa("SELECTED_PROFILE_NAME", self.selected_profile_name.get(), True)

                _uoa("CHROME_EXE_PATH",       self.chrome_exe_path.get(), True)
                _uoa("CHROME_USER_DATA_DIR",  self.chrome_user_data_dir.get(), True)
                _uoa("CHROME_PROFILE_NAME",   self.chrome_profile_name.get(), True)
                _uoa("CHROME_DEBUG_PORT",     self.chrome_debug_port.get())
                _uoa("COCOC_EXE_PATH",        self.cococ_exe_path.get(), True)
                _uoa("COCOC_USER_DATA_DIR",   self.cococ_user_data_dir.get(), True)
                _uoa("COCOC_PROFILE_NAME",    self.cococ_profile_name.get(), True)
                _uoa("COCOC_DEBUG_PORT",      self.cococ_debug_port.get())

                _uoa("ROTATE_PROFILES",       self.rotate_profiles.get())
                _uoa("PROFILE_ROTATE_INTERVAL", self.rotate_interval.get())
                _uoa("PROFILE_ROTATE_ORDER",  self.rotate_order.get(), True)

                with open(cfg, "w", encoding="utf-8") as f:
                    f.write(content)

                if log_msg:
                    self.log("✔ Đã lưu cấu hình.", "ok")
                if show_msg:
                    messagebox.showinfo("Thành công", "Đã lưu cấu hình mới!")
            except Exception as e:
                self.log(f"✗ Lỗi lưu: {e}", "err")
                if show_msg:
                    messagebox.showerror("Lỗi", str(e))

    def _on_close(self):
        try:
            self.save_config(show_msg=False, log_msg=False)
        except:
            pass
        self.root.destroy()



    # ═══════════════════════════════════════════════════════
    #  LOG
    # ═══════════════════════════════════════════════════════
    def log(self, message, tag="dim"):
        def _do():
            self.console.config(state="normal")
            ts = time.strftime("%H:%M:%S")
            self.console.insert("end", f"[{ts}] {message}\n", tag)
            self.console.see("end")
            self.console.config(state="disabled")
        self.root.after(0, _do)

    # ═══════════════════════════════════════════════════════
    #  START / STOP
    # ═══════════════════════════════════════════════════════
    def start_process(self):
        if self.is_running:
            return
        try:
            self.save_config(show_msg=False)
        except Exception:
            pass
        self.is_running = True
        self.stop_requested = False
        self.btn_start.config(state="disabled", bg="#2a3a2a")
        self.btn_stop.config(state="normal", bg="#3a1a1a")
        self.status_badge.config(text="⬤ Đang chạy", fg=self.P["accent"])
        threading.Thread(target=self._run_loop, daemon=True).start()

    def _run_loop(self):
        loops = 1 if self.run_once.get() else self.loop_count.get()
        delay = self.loop_delay.get()

        for i in range(loops):
            if self.stop_requested:
                break
            self.log(f"─── Vòng {i+1}/{loops} ───", "info")

            try:
                main_script = os.path.join(self._base(), "main.py")
                env = os.environ.copy()
                env["PYTHONIOENCODING"] = "utf-8"

                self.current_process = subprocess.Popen(
                    ["python", "-u", main_script],
                    cwd=self._base(),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    env=env,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )

                while True:
                    if self.stop_requested:
                        if self.current_process.poll() is None:
                            self.current_process.terminate()
                        break
                    line = self.current_process.stdout.readline()
                    if not line and self.current_process.poll() is not None:
                        break
                    if line:
                        stripped = line.strip()
                        tag = ("ok"   if "✓" in stripped or "OK" in stripped else
                               "err"  if "✗" in stripped or "Lỗi" in stripped or "ERROR" in stripped else
                               "warn" if "⚠" in stripped or "WARNING" in stripped else
                               "dim")
                        self.log(stripped, tag)

                self.current_process.wait()
                self.current_process = None

            except Exception as e:
                self.log(f"✗ Lỗi chạy script: {e}", "err")

            self._do_cleanup()

            if i < loops - 1 and not self.stop_requested:
                self.log(f"⏱ Chờ {delay}s…", "dim")
                for _ in range(delay):
                    if self.stop_requested:
                        break
                    time.sleep(1)

        self.is_running = False
        self.log("─── Hoàn tất ───", "info")
        self.root.after(0, self._reset_ui)

    def stop_process(self):
        self.stop_requested = True
        self.log("■ Đang yêu cầu dừng…", "warn")
        if self.current_process and self.current_process.poll() is None:
            try:
                self.current_process.terminate()
                self.log("✔ Đã ngắt tiến trình.", "ok")
            except Exception as e:
                self.log(f"✗ {e}", "err")
        self._do_cleanup()

    def _reset_ui(self):
        self.btn_start.config(state="normal",   bg=self.P["accent"])
        self.btn_stop.config( state="disabled", bg="#4a1818")
        self.status_badge.config(text="⬤ Chờ", fg=self.P["fg2"])

    def _do_cleanup(self):
        """Nhẹ nhàng đóng profile đang active (chỉ API browser)."""
        try:
            b_type = getattr(config, "BROWSER_TYPE", "gemlogin")
            if b_type in ("gemlogin", "gpmlogin", "donut"):
                if b_type == "gemlogin":
                    from gemlogin_api import GemLoginAPI
                    api = GemLoginAPI()
                elif b_type == "gpmlogin":
                    from gpm_login_api import GPMLoginAPI
                    api = GPMLoginAPI()
                else:
                    from donut_api import DonutAPI
                    api = DonutAPI()
                pid = getattr(config, "SELECTED_PROFILE_ID", "").strip()
                if pid:
                    try:
                        api.stop_profile(pid)
                    except:
                        pass
        except Exception:
            pass

    def run_reset(self):
        if messagebox.askyesno("Xác nhận", "Xóa hết Video và Lịch sử của Profile này?"):
            try:
                active_profile_id = os.environ.get("ACTIVE_PROFILE_ID", "")
                
                dl_path = self.download_path.get()
                hist_file = self.history_file
                queue_file = f"hangdoitiktok_{active_profile_id}.txt" if active_profile_id else "hangdoitiktok.txt"
                log_file = getattr(config, 'LOG_FILE', 'automation.log')
                
                import shutil
                if os.path.exists(dl_path):
                    shutil.rmtree(dl_path, ignore_errors=True)
                    self.log(f"✔ Đã xóa thư mục {dl_path}", "ok")
                
                for f in [hist_file, queue_file, log_file]:
                    if os.path.exists(f):
                        try:
                            os.remove(f)
                            self.log(f"✔ Đã xóa {f}", "ok")
                        except Exception as fe:
                            self.log(f"✗ Không thể xóa {f}: {fe}", "err")
                            
                self.log("✔ Đã reset dữ liệu cho Profile hiện tại.", "ok")
            except Exception as e:
                self.log(f"✗ Lỗi reset dữ liệu: {e}", "err")

    def backup_current_profile_ui(self):
        import zipfile
        import datetime
        import json as _json

        active_profile_id = os.environ.get("ACTIVE_PROFILE_ID", "")
        if not active_profile_id:
            messagebox.showerror("Lỗi", "Không phát hiện Profile ID đang hoạt động.")
            return

        profile_name = os.environ.get("ACTIVE_PROFILE_NAME", f"Profile {active_profile_id}")
        
        # Determine default backup filename
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_profile_name = "".join(c for c in profile_name if c.isalnum() or c in (' ', '_', '-')).strip().replace(' ', '_')
        default_filename = f"backup_{safe_profile_name}_{timestamp}.zip"
        
        backups_dir = os.path.join(self._base(), "backups")
        os.makedirs(backups_dir, exist_ok=True)

        file_path = filedialog.asksaveasfilename(
            title="Chọn nơi lưu bản sao lưu",
            initialdir=backups_dir,
            initialfile=default_filename,
            filetypes=[("ZIP files", "*.zip")],
            defaultextension=".zip"
        )
        
        if not file_path:
            return
            
        try:
            # File paths on system
            cfg_json = f"config_profile_{active_profile_id}.json"
            channels_file = self.channels_file
            error_file = self.error_file
            history_file = self.history_file
            queue_file = f"hangdoitiktok_{active_profile_id}.txt"
            cookies_file = f"cookies_{active_profile_id}.txt"
            
            # Create zip
            with zipfile.ZipFile(file_path, 'w', zipfile.ZIP_DEFLATED) as zip_ref:
                # Add config JSON
                if os.path.exists(cfg_json):
                    zip_ref.write(cfg_json, "config.json")
                    
                # Add Channels list
                if os.path.exists(channels_file):
                    zip_ref.write(channels_file, "channels.txt")

                # Add Error list
                if os.path.exists(error_file):
                    zip_ref.write(error_file, "errors.txt")

                # Add History list
                if os.path.exists(history_file):
                    zip_ref.write(history_file, "history.txt")

                # Add Queue list
                if os.path.exists(queue_file):
                    zip_ref.write(queue_file, "queue.txt")

                # Add Cookies file
                if os.path.exists(cookies_file):
                    zip_ref.write(cookies_file, "cookies.txt")
                    
                # Add metadata
                metadata = {
                    "profile_id": active_profile_id,
                    "profile_name": profile_name,
                    "backup_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "version": "1.0.0"
                }
                zip_ref.writestr("metadata.json", _json.dumps(metadata, indent=4, ensure_ascii=False))
                
            messagebox.showinfo("Thành công", f"Đã sao lưu Profile '{profile_name}' thành công!")
            self.log(f"✔ Đã sao lưu Profile '{profile_name}' vào tệp: {file_path}", "ok")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể tạo bản sao lưu: {e}")
            self.log(f"✗ Lỗi khi sao lưu Profile: {e}", "err")

    def restore_current_profile_ui(self):
        import zipfile
        import json as _json
        
        active_profile_id = os.environ.get("ACTIVE_PROFILE_ID", "")
        if not active_profile_id:
            messagebox.showerror("Lỗi", "Không phát hiện Profile ID đang hoạt động.")
            return

        profile_name = os.environ.get("ACTIVE_PROFILE_NAME", f"Profile {active_profile_id}")

        backups_dir = os.path.join(self._base(), "backups")
        os.makedirs(backups_dir, exist_ok=True)

        file_path = filedialog.askopenfilename(
            title="Chọn tệp sao lưu để khôi phục (.zip)",
            initialdir=backups_dir,
            filetypes=[("ZIP files", "*.zip")]
        )
        
        if not file_path:
            return
            
        try:
            # Verify zip content
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                file_list = zip_ref.namelist()
                
                # Check for metadata to show a nice prompt
                meta_info = ""
                meta_profile_name = ""
                if "metadata.json" in file_list:
                    try:
                        metadata = _json.loads(zip_ref.read("metadata.json").decode('utf-8'))
                        meta_profile_name = metadata.get('profile_name', '')
                        meta_info = f"\n- Profile gốc: {meta_profile_name}\n- Thời gian sao lưu: {metadata.get('backup_time')}"
                    except:
                        pass
                
                confirm = messagebox.askyesno(
                    "Xác nhận khôi phục",
                    f"Bạn có chắc chắn muốn khôi phục dữ liệu từ tệp sao lưu này?{meta_info}\n\n⚠️ HÀNH ĐỘNG NÀY SẼ GHI ĐÈ TOÀN BỘ cấu hình, danh sách kênh, lịch sử tải của Profile hiện tại '{profile_name}'!"
                )
                
                if not confirm:
                    return
                
                # Destination files
                cfg_json = f"config_profile_{active_profile_id}.json"
                channels_file = self.channels_file
                error_file = self.error_file
                history_file = self.history_file
                queue_file = f"hangdoitiktok_{active_profile_id}.txt"
                cookies_file = f"cookies_{active_profile_id}.txt"
                
                # Overwrite files from zip
                if "config.json" in file_list:
                    with open(cfg_json, 'wb') as f:
                        f.write(zip_ref.read("config.json"))
                    
                if "channels.txt" in file_list:
                    with open(channels_file, 'wb') as f:
                        f.write(zip_ref.read("channels.txt"))
                        
                if "errors.txt" in file_list:
                    with open(error_file, 'wb') as f:
                        f.write(zip_ref.read("errors.txt"))
                        
                if "history.txt" in file_list:
                    with open(history_file, 'wb') as f:
                        f.write(zip_ref.read("history.txt"))

                if "queue.txt" in file_list:
                    with open(queue_file, 'wb') as f:
                        f.write(zip_ref.read("queue.txt"))

                if "cookies.txt" in file_list:
                    with open(cookies_file, 'wb') as f:
                        f.write(zip_ref.read("cookies.txt"))

                # Cập nhật tên profile từ metadata (hỗ trợ chuyển máy tính)
                if meta_profile_name:
                    try:
                        config_path = "profiles_config.json"
                        if os.path.exists(config_path):
                            with open(config_path, "r", encoding="utf-8") as f:
                                prof_cfg = _json.load(f)
                            for p in prof_cfg.get("profiles", []):
                                if str(p.get("id")) == str(active_profile_id):
                                    p["name"] = meta_profile_name
                                    break
                            with open(config_path, "w", encoding="utf-8") as f:
                                _json.dump(prof_cfg, f, indent=4, ensure_ascii=False)
                            # Cập nhật biến môi trường và tiêu đề cửa sổ chính
                            os.environ["ACTIVE_PROFILE_NAME"] = meta_profile_name
                            self.root.title(f"TikTok Automation — {meta_profile_name}")
                    except Exception as pe:
                        print(f"Lỗi cập nhật tên profile: {pe}")
                        
            # Reload configuration into GUI
            if os.path.exists(cfg_json):
                with open(cfg_json, "r", encoding="utf-8") as f:
                    saved = _json.load(f)
                
                # Update all GUI variables immediately
                self.download_threads.set(saved.get("DOWNLOAD_THREADS", 3))
                self.max_videos.set(saved.get("MAX_VIDEOS_PER_CHANNEL", 10))
                self.download_slideshow.set(saved.get("DOWNLOAD_SLIDESHOW", True))
                self.extract_stats.set(saved.get("EXTRACT_STATS", True))
                self.download_path.set(saved.get("DOWNLOAD_PATH", "downloads"))
                self.run_once.set(saved.get("RUN_ONCE", True))
                self.loop_count.set(saved.get("LOOP_COUNT", 5000))
                self.loop_delay.set(saved.get("LOOP_DELAY", 600))
                
                self.browser_type.set(saved.get("BROWSER_TYPE", "gemlogin"))
                self.gemlogin_api_url.set(saved.get("GEMLOGIN_API_URL", "http://localhost:1010"))
                self.gpmlogin_api_url.set(saved.get("GPM_LOGIN_API_URL", "http://localhost:60064"))
                self.donut_api_url.set(saved.get("DONUT_API_URL", "http://127.0.0.1:10108"))
                self.donut_api_key.set(saved.get("DONUT_API_KEY", ""))
                self.selected_profile_id.set(saved.get("SELECTED_PROFILE_ID", ""))
                self.selected_profile_name.set(saved.get("SELECTED_PROFILE_NAME", ""))
                
                self.chrome_exe_path.set(saved.get("CHROME_EXE_PATH", ""))
                self.chrome_user_data_dir.set(saved.get("CHROME_USER_DATA_DIR", ""))
                self.chrome_profile_name.set(saved.get("CHROME_PROFILE_NAME", "Default"))
                self.chrome_debug_port.set(saved.get("CHROME_DEBUG_PORT", 9222))
                
                self.cococ_exe_path.set(saved.get("COCOC_EXE_PATH", ""))
                self.cococ_user_data_dir.set(saved.get("COCOC_USER_DATA_DIR", ""))
                self.cococ_profile_name.set(saved.get("COCOC_PROFILE_NAME", "Default"))
                self.cococ_debug_port.set(saved.get("COCOC_DEBUG_PORT", 9223))
                
                self.rotate_profiles.set(saved.get("ROTATE_PROFILES", False))
                self.rotate_interval.set(saved.get("PROFILE_ROTATE_INTERVAL", 5))
                self.rotate_order.set(saved.get("PROFILE_ROTATE_ORDER", "sequential"))
                
                # Apply theme if is_dark changed
                is_dark_saved = saved.get("IS_DARK", True)
                if is_dark_saved != self.is_dark:
                    self.is_dark = is_dark_saved
                    self.P = DARK if self.is_dark else LIGHT
                    self.btn_theme.config(text="🌙 Dark" if self.is_dark else "☀ Light")
                    self._apply_theme()
                
                # Update browser options dropdown
                self._on_browser_type_change()
                
            messagebox.showinfo("Thành công", f"Đã khôi phục dữ liệu cho Profile '{profile_name}' thành công!")
            self.log(f"✔ Đã khôi phục dữ liệu Profile '{profile_name}' từ tệp: {file_path}", "ok")
            self.refresh_channels_tab()
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể khôi phục dữ liệu: {e}")
            self.log(f"✗ Lỗi khi khôi phục Profile: {e}", "err")

    def _build_notebook(self, parent):
        P = self.P
        
        # Main notebook
        self.notebook = ttk.Notebook(parent)
        self.notebook.pack(fill="both", expand=True)

        # Tab 1: Channels list
        self.channels_tab = ttk.Frame(self.notebook, style="TFrame")
        self.notebook.add(self.channels_tab, text=" 📋 Danh Sách Kênh ")
        self._build_channels_tab()

        # Tab 2: Logs
        self.log_tab = ttk.Frame(self.notebook, style="TFrame")
        self.notebook.add(self.log_tab, text=" 🖥 Log Hoạt Động ")
        
        # Build console inside log_tab
        self._card_console(self.log_tab)
        
        # Initial load of channels
        self.refresh_channels_tab()

    def _build_channels_tab(self):
        P = self.P
        
        # 1. Top bar of channels tab
        top_f = tk.Frame(self.channels_tab, bg=P["bg"])
        top_f.pack(fill="x", padx=10, pady=(10, 5))
        
        lbl_title = tk.Label(top_f, text="QUẢN LÝ DANH SÁCH KÊNH & FOLDER LƯU TRỮ", font=("Segoe UI", 10, "bold"), bg=P["bg"], fg=P["fg"])
        lbl_title.pack(side="left")
        
        lbl_autosave = tk.Label(top_f, text="● Tự động lưu: Đang bật", fg=P["accent"], bg=P["bg"], font=("Segoe UI", 9, "italic"))
        lbl_autosave.pack(side="left", padx=15)
        
        # Refresh button
        btn_refresh = tk.Button(
            top_f, text="↻ Tải Lại", bg=P["btn_neu"], fg=P["fg"],
            activebackground=P["border"], activeforeground=P["accent"],
            relief="flat", cursor="hand2", font=("Segoe UI", 9, "bold"), padx=10, pady=4,
            command=self.refresh_channels_tab
        )
        btn_refresh.pack(side="right", padx=5)
        
        # Open txt file button
        btn_open_txt = tk.Button(
            top_f, text="📁 Mở File TXT", bg=P["btn_neu"], fg=P["fg"],
            activebackground=P["border"], activeforeground=P["accent"],
            relief="flat", cursor="hand2", font=("Segoe UI", 9, "bold"), padx=10, pady=4,
            command=lambda: self._open_file(self.channels_file)
        )
        btn_open_txt.pack(side="right", padx=5)

        # Separator line
        sep = tk.Frame(self.channels_tab, bg=P["border"], height=1)
        sep.pack(fill="x", padx=10, pady=5)

        # 3. Canvas & Scrollbar container
        list_container = tk.Frame(self.channels_tab, bg=P["bg"])
        list_container.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.channels_canvas = tk.Canvas(list_container, borderwidth=0, highlightthickness=0, bg=P["bg"])
        self.channels_canvas.pack(side="left", fill="both", expand=True)
        
        scrollbar = ttk.Scrollbar(list_container, orient="vertical", command=self.channels_canvas.yview)
        scrollbar.pack(side="right", fill="y")
        
        self.scrollable_frame = tk.Frame(self.channels_canvas, bg=P["bg"])
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.channels_canvas.configure(
                scrollregion=self.channels_canvas.bbox("all")
            )
        )
        
        canvas_window = self.channels_canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        
        def configure_canvas_width(event):
            self.channels_canvas.itemconfig(canvas_window, width=event.width)
            
        self.channels_canvas.bind("<Configure>", configure_canvas_width)
        self.channels_canvas.configure(yscrollcommand=scrollbar.set)
        
        # Mousewheel binding
        def _on_mousewheel(event):
            self.channels_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            
        def _bind_mw(event):
            self.channels_canvas.bind_all("<MouseWheel>", _on_mousewheel)
            
        def _unbind_mw(event):
            self.channels_canvas.unbind_all("<MouseWheel>")
            
        self.channels_canvas.bind("<Enter>", _bind_mw)
        self.channels_canvas.bind("<Leave>", _unbind_mw)
        
        # Configure columns
        self.scrollable_frame.columnconfigure(0, weight=0) # STT
        self.scrollable_frame.columnconfigure(1, weight=3) # URL
        self.scrollable_frame.columnconfigure(2, weight=2) # Folder
        self.scrollable_frame.columnconfigure(3, weight=0) # Status
        self.scrollable_frame.columnconfigure(4, weight=0) # Delete
        
        # Add static headers
        headers = ["STT", "Link Kênh TikTok", "Thư mục lưu video (Folder)", "Trạng thái", "Hành động"]
        for col_idx, text in enumerate(headers):
            lbl = tk.Label(self.scrollable_frame, text=text, font=("Segoe UI", 9, "bold"), bg=P["bg"], fg=P["fg2"])
            lbl.grid(row=0, column=col_idx, padx=5, pady=5)
            
        # 4. Bottom frame
        bottom_f = tk.Frame(self.channels_tab, bg=P["bg"])
        bottom_f.pack(fill="x", padx=10, pady=10)
        
        btn_add = tk.Button(
            bottom_f, text="＋ Thêm Kênh Mới", bg="#10b981", fg="white",
            activebackground="#059669", activeforeground="white",
            relief="flat", cursor="hand2", font=("Segoe UI", 9, "bold"), padx=15, pady=6,
            command=self.add_empty_channel_row
        )
        btn_add.pack(side="left", padx=5)

    def add_empty_channel_row(self):
        self.add_channel_row_ui(url="", folder="", status="")
        self.channels_canvas.update_idletasks()
        self.channels_canvas.yview_moveto(1.0)

    def refresh_channels_tab(self):
        if hasattr(self, 'channel_rows') and self.channel_rows:
            for row in self.channel_rows:
                row['stt_label'].destroy()
                row['url_entry'].destroy()
                row['folder_entry'].destroy()
                row['status_label'].destroy()
                row['delete_btn'].destroy()
            self.channel_rows.clear()
            
        channels = []
        if os.path.exists(self.channels_file):
            try:
                with open(self.channels_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.replace('\x00', '').strip()
                        if not line:
                            continue
                        parts = line.split('|')
                        url = parts[0].strip()
                        if not url:
                            continue
                        name = parts[1].strip() if len(parts) > 1 else ""
                        status = parts[2].strip() if len(parts) > 2 else ""
                        channels.append({'url': url, 'name': name, 'status': status})
            except Exception as e:
                self.log(f"✗ Lỗi đọc file kênh: {e}", "err")
                
        for i, ch in enumerate(channels):
            self.add_channel_row_ui(url=ch['url'], folder=ch['name'], status=ch['status'], row_num=i+1)

    def add_channel_row_ui(self, url="", folder="", status="", row_num=None):
        P = self.P
        if row_num is None:
            row_num = len(self.channel_rows) + 1
            
        grid_row = row_num
        
        stt_lbl = tk.Label(self.scrollable_frame, text=str(row_num), font=("Segoe UI", 9), bg=P["bg"], fg=P["fg2"])
        stt_lbl.grid(row=grid_row, column=0, padx=5, pady=5)
        
        url_var = tk.StringVar(value=url)
        url_ent = tk.Entry(
            self.scrollable_frame, textvariable=url_var,
            bg=P["input_bg"], fg=P["fg"], insertbackground=P["fg"],
            relief="flat", highlightbackground=P["border"], highlightthickness=1,
            font=("Segoe UI", 9)
        )
        url_ent.grid(row=grid_row, column=1, padx=5, pady=5, sticky="ew")
        
        folder_var = tk.StringVar(value=folder if folder else "")
        folder_ent = tk.Entry(
            self.scrollable_frame, textvariable=folder_var,
            bg=P["input_bg"], fg=P["fg"], insertbackground=P["fg"],
            relief="flat", highlightbackground=P["border"], highlightthickness=1,
            font=("Segoe UI", 9)
        )
        folder_ent.grid(row=grid_row, column=2, padx=5, pady=5, sticky="ew")
        
        status_text = status if status else "Chờ"
        status_fg = P["fg2"]
        if "die" in status.lower() or "lỗi" in status.lower():
            status_fg = "#ef4444"
        elif "live" in status.lower():
            status_fg = "#10b981"
            
        status_lbl = tk.Label(self.scrollable_frame, text=status_text, fg=status_fg, font=("Segoe UI", 9, "bold"), bg=P["bg"])
        status_lbl.grid(row=grid_row, column=3, padx=5, pady=5)
        
        def on_edit(*args):
            self.queue_save_channels()
            
        url_var.trace_add("write", on_edit)
        folder_var.trace_add("write", on_edit)
        
        delete_btn = tk.Button(
            self.scrollable_frame, 
            text="✕", 
            fg="white", 
            bg="#ef4444", 
            activebackground="#dc2626",
            relief="flat", 
            font=("Segoe UI", 8, "bold"),
            cursor="hand2",
            padx=5,
            command=lambda: self.delete_channel_row(row_num)
        )
        delete_btn.grid(row=grid_row, column=4, padx=5, pady=5)
        
        row_dict = {
            'stt': row_num,
            'stt_label': stt_lbl,
            'url_var': url_var,
            'url_entry': url_ent,
            'folder_var': folder_var,
            'folder_entry': folder_ent,
            'status_label': status_lbl,
            'delete_btn': delete_btn
        }
        self.channel_rows.append(row_dict)

    def delete_channel_row(self, row_num):
        idx_to_remove = -1
        for idx, row in enumerate(self.channel_rows):
            if row['stt'] == row_num:
                idx_to_remove = idx
                break
        
        if idx_to_remove != -1:
            row = self.channel_rows[idx_to_remove]
            row['stt_label'].destroy()
            row['url_entry'].destroy()
            row['folder_entry'].destroy()
            row['status_label'].destroy()
            row['delete_btn'].destroy()
            
            self.channel_rows.pop(idx_to_remove)
            
            for new_idx, rem_row in enumerate(self.channel_rows):
                new_row_num = new_idx + 1
                rem_row['stt'] = new_row_num
                rem_row['stt_label'].config(text=str(new_row_num))
                
                grid_row = new_row_num
                rem_row['stt_label'].grid(row=grid_row, column=0)
                rem_row['url_entry'].grid(row=grid_row, column=1)
                rem_row['folder_entry'].grid(row=grid_row, column=2)
                rem_row['status_label'].grid(row=grid_row, column=3)
                rem_row['delete_btn'].grid(row=grid_row, column=4)
                
                rem_row['delete_btn'].config(command=lambda r=new_row_num: self.delete_channel_row(r))
            
            self.save_channels_to_file()

    def queue_save_channels(self):
        if hasattr(self, '_save_channels_timer') and self._save_channels_timer:
            self.root.after_cancel(self._save_channels_timer)
        self._save_channels_timer = self.root.after(500, self.save_channels_to_file)

    def save_channels_to_file(self):
        channels = []
        for row in self.channel_rows:
            url = row['url_entry'].get().strip()
            folder = row['folder_entry'].get().strip()
            status = row['status_label'].cget("text").strip()
            if status == "Chờ":
                status = ""
            if url:
                channels.append({'url': url, 'name': folder, 'status': status})
        
        try:
            with open(self.channels_file, 'w', encoding='utf-8') as f:
                for ch in channels:
                    parts = [ch['url']]
                    if ch['name'] or ch['status']:
                        parts.append(ch['name'] or "")
                    if ch['status']:
                        parts.append(ch['status'])
                    f.write("|".join(parts) + "\n")
        except Exception as e:
            self.log(f"✗ Lỗi lưu file kênh: {e}", "err")


class ProfileSelector(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Chọn Profile Hoạt Động")
        self.geometry("560x480")
        self.resizable(False, False)
        self.configure(bg="#12121a")
        
        # Center the window
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'+{x}+{y}')
        
        self.config_path = "profiles_config.json"
        self.load_profiles()
        
        # Tiêu đề
        lbl_title = tk.Label(self, text="HỆ THỐNG QUẢN LÝ PROFILE", font=("Segoe UI", 16, "bold"), bg="#12121a", fg="#10b981")
        lbl_title.pack(pady=(25, 5))
        
        lbl_desc = tk.Label(self, text="Vui lòng chọn Profile để truy cập Dashboard riêng biệt:", font=("Segoe UI", 10), bg="#12121a", fg="#a3a3c2")
        lbl_desc.pack(pady=(0, 25))
        
        # Grid frame
        grid_frame = tk.Frame(self, bg="#12121a")
        grid_frame.pack(fill="both", expand=True, padx=40, pady=(0, 20))
        
        self.buttons = []
        for i, prof in enumerate(self.profiles):
            row = i // 2
            col = i % 2
            
            # Subframe for button + edit button
            item_frame = tk.Frame(grid_frame, bg="#12121a", pady=10, padx=10)
            item_frame.grid(row=row, column=col, sticky="nsew")
            
            # Select button
            btn_select = tk.Button(
                item_frame, text=prof['name'], font=("Segoe UI", 11, "bold"),
                bg="#1b1b26", fg="#f1f1f7", activebackground="#2c2c3e", activeforeground="#10b981",
                bd=0, height=2, width=16, cursor="hand2",
                highlightbackground="#2c2c3e", highlightthickness=1,
                command=lambda p=prof: self.select_profile(p)
            )
            btn_select.pack(side="left", fill="x", expand=True)
            self.buttons.append((btn_select, prof))
            
            # Hover effects
            def on_enter(e, btn=btn_select):
                btn.configure(bg="#2c2c3e")
            def on_leave(e, btn=btn_select):
                btn.configure(bg="#1b1b26")
                
            btn_select.bind("<Enter>", on_enter)
            btn_select.bind("<Leave>", on_leave)
            
            # Edit name button
            btn_edit = tk.Button(
                item_frame, text="✏️", font=("Segoe UI", 11),
                bg="#12121a", fg="#a3a3c2", activebackground="#12121a", activeforeground="#10b981",
                bd=0, cursor="hand2", padx=5,
                command=lambda idx=i: self.edit_profile_name(idx)
            )
            btn_edit.pack(side="right", padx=(8, 0))
            
        # Set grid weight
        for r in range(3):
            grid_frame.rowconfigure(r, weight=1)
        for c in range(2):
            grid_frame.columnconfigure(c, weight=1)
            
        self.selected_profile = None

    def load_profiles(self):
        if os.path.exists(self.config_path) and os.path.getsize(self.config_path) > 0:
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    self.config = json.load(f)
            except:
                self.config = self.get_default_config()
        else:
            self.config = self.get_default_config()
            self.save_profiles()
            
        self.profiles = self.config.get("profiles", [])

        # Tự động di chuyển dữ liệu cũ sang Profile 1 nếu chưa tồn tại
        try:
            cfg_json_1 = "config_profile_1.json"
            if not os.path.exists(cfg_json_1) or os.path.getsize(cfg_json_1) == 0:
                import config
                import shutil
                old_settings = {}
                keys = [
                    "DOWNLOAD_THREADS", "MAX_VIDEOS_PER_CHANNEL", "DOWNLOAD_SLIDESHOW",
                    "EXTRACT_STATS", "DOWNLOAD_PATH", "RUN_ONCE", "LOOP_COUNT", "LOOP_DELAY",
                    "IS_DARK", "BROWSER_TYPE", "GEMLOGIN_API_URL", "GPM_LOGIN_API_URL",
                    "DONUT_API_URL", "DONUT_API_KEY", "SELECTED_PROFILE_ID", "SELECTED_PROFILE_NAME",
                    "CHROME_EXE_PATH", "CHROME_USER_DATA_DIR", "CHROME_PROFILE_NAME", "CHROME_DEBUG_PORT",
                    "COCOC_EXE_PATH", "COCOC_USER_DATA_DIR", "COCOC_PROFILE_NAME", "COCOC_DEBUG_PORT",
                    "ROTATE_PROFILES", "PROFILE_ROTATE_INTERVAL", "PROFILE_ROTATE_ORDER"
                ]
                for k in keys:
                    if hasattr(config, k):
                        old_settings[k] = getattr(config, k)
                
                # Giữ nguyên cấu hình thư mục nếu họ tùy biến, ngược lại đổi thành downloads_1
                if old_settings.get("DOWNLOAD_PATH") == "downloads":
                    old_settings["DOWNLOAD_PATH"] = "downloads_1"
                
                with open(cfg_json_1, "w", encoding="utf-8") as f:
                    json.dump(old_settings, f, indent=4, ensure_ascii=False)
                
                # 2. Di chuyển các tệp dữ liệu kênh và lịch sử
                file_mapping = {
                    "danhsachtiktok.txt": "danhsachtiktok_1.txt",
                    "lichsutaitiktok.txt": "lichsutaitiktok_1.txt",
                    "kenhloi.txt": "kenhloi_1.txt",
                    "hangdoitiktok.txt": "hangdoitiktok_1.txt",
                    "cookies.txt": "cookies_1.txt"
                }
                for src, dst in file_mapping.items():
                    if os.path.exists(src) and not os.path.exists(dst):
                        try:
                            shutil.copy(src, dst)
                        except Exception as e:
                            print(f"Error copying {src} to {dst}: {e}")
                
                # 3. Di chuyển thư mục downloads cũ thành downloads_1
                if os.path.exists("downloads") and os.path.isdir("downloads") and not os.path.exists("downloads_1"):
                    try:
                        shutil.move("downloads", "downloads_1")
                    except Exception as e:
                        print(f"Error moving downloads: {e}")
        except Exception as ex:
            print(f"Lỗi khi di chuyển dữ liệu cũ sang Profile 1: {ex}")

    def get_default_config(self):
        return {
            "profiles": [
                {"id": 1, "name": "Profile 1"},
                {"id": 2, "name": "Profile 2"},
                {"id": 3, "name": "Profile 3"},
                {"id": 4, "name": "Profile 4"},
                {"id": 5, "name": "Profile 5"},
                {"id": 6, "name": "Profile 6"}
            ]
        }

    def save_profiles(self):
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving profiles config: {e}")

    def edit_profile_name(self, idx):
        current_name = self.profiles[idx]['name']
        new_name = simpledialog.askstring("Đổi tên Profile", f"Nhập tên mới cho {current_name}:", parent=self)
        if new_name and new_name.strip():
            self.profiles[idx]['name'] = new_name.strip()
            self.config['profiles'] = self.profiles
            self.save_profiles()
            self.buttons[idx][0].configure(text=new_name.strip())

    def select_profile(self, profile):
        self.selected_profile = profile
        self.destroy()


if __name__ == "__main__":
    from tkinter import simpledialog
    import json
    
    # 1. Khởi chạy giao diện chọn Profile trước
    selector = ProfileSelector()
    selector.mainloop()
    
    # 2. Nếu có profile được chọn -> Nạp cấu hình riêng và mở giao diện chính
    if selector.selected_profile:
        prof = selector.selected_profile
        os.environ["ACTIVE_PROFILE_ID"] = str(prof["id"])
        os.environ["ACTIVE_PROFILE_NAME"] = prof["name"]
        
        # Nạp lại cấu hình động trong config.py
        import config
        config.load_profile(prof["id"])
        
        # Mở app chính
        root = tk.Tk()
        app  = GiaanTool(root)
        root.mainloop()
