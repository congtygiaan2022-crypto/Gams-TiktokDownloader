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
        self._card_console(self.right)

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
            ("📋  File Kênh",    lambda: self._open_file("danhsachtiktok.txt"), "#1e3a5f"),
            ("⚠  Kênh Lỗi",     lambda: self._open_file("kenhloi.txt"),         "#3a1a1a"),
            ("📜  Lịch Sử Tải", lambda: self._open_file("lichsutaitiktok.txt"), "#1a2e1a"),
            ("📁  Thư Mục",     self._open_download_folder,                      "#1a1a2e"),
        ]
        btn_row = tk.Frame(body, bg=P["card"])
        btn_row.pack(fill="x")
        for text, cmd, bg in actions:
            b = tk.Button(btn_row, text=text, command=cmd, bg=bg, fg=P["fg"],
                          relief="flat", cursor="hand2",
                          font=("Segoe UI", 9), padx=6, pady=6)
            b.pack(side="left", fill="x", expand=True, padx=(0, 4))

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
        if messagebox.askyesno("Xác nhận", "Xóa hết Video và Lịch sử?"):
            try:
                bat = os.path.join(self._base(), "xoa_du_lieu.bat")
                subprocess.run(bat, shell=True, cwd=self._base())
                self.log("✔ Đã reset dữ liệu.", "ok")
            except Exception as e:
                self.log(f"✗ {e}", "err")


if __name__ == "__main__":
    root = tk.Tk()
    app  = GiaanTool(root)
    root.mainloop()
