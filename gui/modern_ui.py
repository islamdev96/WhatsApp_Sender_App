"""
WhatsApp Sender Pro — Modern UI
Built with CustomTkinter for a professional, world-class look and feel.
Features: Dark/Light mode, tabbed interface, dashboard, templates, settings persistence.
"""
import customtkinter as ctk
from tkinter import filedialog, messagebox, ttk
import re
import threading
import queue
import time
import random
import os
import csv
import datetime
import json

from .components import RichTextFrame, AttachmentManager

from automation.whatsapp_bot import WhatsAppBot
from utils.helpers import read_contacts, read_contacts_auto
from utils.config_manager import ConfigManager
from utils.templates_manager import TemplatesManager
from utils.contacts_manager import ContactsManager
from utils.campaign_manager import CampaignManager
from utils.event_log import format_event

# ─── Color Palette (Premium) ────────────────────────────────────────────────
PALETTE_DARK = {
    # Main branding
    "primary":       "#00E676",  # Neon Green
    "primary_hover": "#00C853",
    "primary_dark":  "#0A0F16",  # Sidebar / base (Deeper Slate)

    # Status colors
    "danger":        "#FF3D00",
    "danger_hover":  "#DD2C00",
    "warning":       "#FFB020",
    "success":       "#00E676",
    "success_hover": "#00C853",
    "info":          "#38BDF8",

    # UI Elements
    "card_bg":       "#151E2E",
    "bg_dark":       "#0F172A",
    "text_main":     "#F8FAFC",
    "text_muted":    "#94A3B8",
    "accent":        "#22D3EE",
    "accent_hover":  "#06B6D4",
    "border":        "#263145",
    "secondary":     "#1F2937",
    "secondary_hover":"#2A3A52",
    "secondary_text":"#E5E7EB",
}

PALETTE_LIGHT = {
    # Main branding
    "primary":       "#00B15D",
    "primary_hover": "#009E52",
    "primary_dark":  "#FFFFFF",  # Sidebar / base in light mode

    # Status colors
    "danger":        "#DC2626",
    "danger_hover":  "#B91C1C",
    "warning":       "#F59E0B",
    "success":       "#16A34A",
    "success_hover": "#15803D",
    "info":          "#0284C7",

    # UI Elements
    "card_bg":       "#F1F5F9",
    "bg_dark":       "#FFFFFF",
    "text_main":     "#0F172A",
    "text_muted":    "#64748B",
    "accent":        "#0EA5E9",
    "accent_hover":  "#0284C7",
    "border":        "#E2E8F0",
    "secondary":     "#E2E8F0",
    "secondary_hover":"#CBD5E1",
    "secondary_text":"#0F172A",
}

# Active palette (filled at runtime based on appearance mode)
COLORS = {}

# ─── Typography & Styling ─────────────────────────────────────────────────────
FONTS = {
    "header": ("Segoe UI", 24, "bold"),
    "sub_header": ("Segoe UI", 16, "bold"),
    "body": ("Segoe UI", 13),
    "body_bold": ("Segoe UI", 13, "bold"),
    "small": ("Segoe UI", 11),
    "mono": ("Consolas", 12),
}

ERROR_CATALOG = {
    "ERR-01": "تعذر تشغيل المتصفح. اغلق كل نوافذ Chrome ثم أعد المحاولة.",
    "ERR-02": "المتصفح لا يستجيب للأتمتة أو انتهت مهلة تسجيل الدخول.",
    "ERR-03": "مشكلة في ملف الأرقام (غير موجود/مفتوح/أعمدة غير صحيحة).",
    "ERR-04": "نص الرسالة فارغ.",
    "ERR-05": "يرجى اختيار ملف أرقام صحيح أو مجموعة.",
    "ERR-09": "ملف الصورة غير موجود أو غير صالح.",
    "ERR-06": "زر الإرفاق غير موجود.",
    "ERR-07": "زر الإرسال لم يظهر في الوقت المحدد.",
    "ERR-08": "فشل رفع الصورة أو كتابة الكابشن.",
    "ERR-10": "انتهت مهلة تحميل المحادثة.",
    "ERR-20": "الرقم غير صحيح أو ليس لديه واتساب.",
    "ERR-21": "لم يتم تسجيل الدخول بعد.",
    "ERR-11": "ملف المتصفح الشخصي قيد الاستخدام حالياً. يرجى إغلاق أي متصفح كروم آخر مفتوح بواسطة هذا الحساب وإعادة المحاولة.",
    "ERR-99": "خطأ غير متوقع.",
}


class ModernWhatsAppApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # ── Config & Templates & Groups ──
        self.config = ConfigManager()
        self.templates = TemplatesManager()
        self.contacts_mgr = ContactsManager()
        self.campaign_manager = CampaignManager()

        # ── Appearance ──
        mode = self.config.get("appearance_mode", "dark")
        ctk.set_appearance_mode(mode)
        ctk.set_default_color_theme("green")
        self._apply_palette(mode)

        # ── Window Setup ──
        self.title("WhatsApp Sender Pro")
        w = self.config.get("window_width", 1000)
        h = self.config.get("window_height", 700)
        self.geometry(f"{w}x{h}")
        self.minsize(900, 650)

        # ── State Variables ──
        self.bot = None
        self.is_running = False
        self.stop_event = threading.Event()
        self.ui_queue = queue.Queue()
        self.results_log = []
        self.sent = 0
        self.failed = 0
        self.invalid = 0
        self.pending_start_payload = None
        self.pending_check_contacts = None
        self.is_checking = False
        self.log_dir = os.path.join(os.getcwd(), "reports", "logs")
        self.log_file_path = os.path.join(self.log_dir, f"app_{datetime.datetime.now().strftime('%Y%m%d')}.log")
        self.pause_event = threading.Event()
        self.is_paused = False
        self.progress_win = None
        self.progress_tree = None
        self.progress_count_label = None
        self.progress_status_label = None
        self.progress_bar_small = None
        self.progress_state_label = None
        self.progress_metric_labels = {}
        self.last_report_path = None
        self._log_to_terminal = True

        # ── Profiles ──
        self.profiles_dir = os.path.join(os.getcwd(), self.config.get("profiles_dir", os.path.join("data", "profiles")))
        self.legacy_profile_dir = os.path.join(os.getcwd(), "chrome_profile")
        os.makedirs(self.profiles_dir, exist_ok=True)
        profile_name = self.config.get("profile_name", "Default")
        if profile_name != "Legacy":
            os.makedirs(os.path.join(self.profiles_dir, profile_name), exist_ok=True)
            self.user_data_dir = os.path.join(self.profiles_dir, profile_name)
        else:
            self.user_data_dir = self.legacy_profile_dir

        self.profile_var = ctk.StringVar(value=profile_name)

        # ── Language (i18n) ──
        import json
        self.locales = {}
        try:
            with open("locales.json", "r", encoding="utf-8") as f:
                self.locales = json.load(f)
        except Exception as e:
            print(f"Error loading locales: {e}")
            
        self.current_lang = ctk.StringVar(value=self.config.get("language", "ar"))

        # ── Build Layout ──
        self._build_layout()

        # ── Start UI Queue Processor ──
        self.after(50, self._process_ui_queue)

    def tr(self, key):
        """Translate a key based on current language."""
        lang = self.current_lang.get()
        if lang not in self.locales:
            lang = "en"
        return self.locales.get(lang, {}).get(key, key)

    def _apply_palette(self, mode):
        palette = PALETTE_DARK if str(mode).lower() == "dark" else PALETTE_LIGHT
        COLORS.clear()
        COLORS.update(palette)

        # Configure ttk.Style for all Treeviews to match our modern palette
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass

        bg_color = COLORS["bg_dark"]
        fg_color = COLORS["text_main"]
        card_bg = COLORS["card_bg"]
        border_color = COLORS["border"]
        primary_color = COLORS["primary"]

        style.configure(
            "Treeview",
            background=bg_color,
            foreground=fg_color,
            fieldbackground=bg_color,
            rowheight=28,
            font=("Segoe UI", 10),
            borderwidth=0
        )
        style.configure(
            "Treeview.Heading",
            font=("Segoe UI", 10, "bold"),
            background=card_bg,
            foreground=fg_color,
            borderwidth=1,
            relief="flat"
        )
        style.map(
            "Treeview",
            background=[("selected", primary_color)],
            foreground=[("selected", "#000000" if str(mode).lower() == "dark" else "#FFFFFF")]
        )


    def _refresh_theme(self):
        # Update key widgets after palette change
        if hasattr(self, "toolbar_frame"):
            self.toolbar_frame.configure(fg_color=COLORS["primary_dark"])
        if hasattr(self, "bottom_bar"):
            self.bottom_bar.configure(fg_color=COLORS["primary_dark"])
        if hasattr(self, "session_status_label"):
            self.session_status_label.configure(text_color=COLORS["text_muted"])
        if hasattr(self, "nav_buttons") and hasattr(self, "current_tab"):
            for nid, btn in self.nav_buttons.items():
                if nid == self.current_tab:
                    btn.configure(fg_color=COLORS["primary"], text_color="#000000", font=("Segoe UI", 11, "bold"))
                else:
                    btn.configure(fg_color="transparent", text_color=COLORS["text_muted"], font=("Segoe UI", 11))
        if hasattr(self, "attachment_manager"):
            self.attachment_manager.apply_theme(COLORS)
        if hasattr(self, "message_editor"):
            self.message_editor.apply_theme(COLORS)
        if hasattr(self, "btn_start"):
            self.btn_start.configure(fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"], text_color="#000000")
        if hasattr(self, "btn_stop"):
            self.btn_stop.configure(fg_color=COLORS["danger"], hover_color=COLORS["danger_hover"], text_color="#FFFFFF")

    # ═══════════════════════════════════════════════════════════════════════
    #  LAYOUT
    # ═══════════════════════════════════════════════════════════════════════
    def _build_layout(self):
        import tkinter as tk
        import json

        # Instantiate backward compatibility state variables
        self.bg_mode_var = ctk.BooleanVar(value=self.config.get("background_mode", False))
        self.use_valid_after_check_var = ctk.BooleanVar(value=self.config.get("use_valid_after_check", False))
        # Configure Main Grid Rows (Toolbar -> Main Area -> Bottom Bar)
        self.grid_rowconfigure(0, weight=0)  # Top Toolbar
        self.grid_rowconfigure(1, weight=1)  # Main Content
        self.grid_rowconfigure(2, weight=0)  # Bottom Status Bar
        self.grid_columnconfigure(0, weight=1)

        # ── 1. Native Windows Menu Bar ──
        self._build_menu_bar()

        # ── 2. Top Horizontal Toolbar ──
        self._build_top_toolbar()

        # ── 3. Main Content Frame ──
        self.main_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_frame.grid(row=1, column=0, sticky="nsew")
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        # ── 4. Bottom Status Bar ──
        self._build_bottom_bar()

        # ── Tabs (frames) ──
        self.tab_frames = {}
        self._build_tab_main()
        self._build_tab_groups()
        self._build_tab_templates()
        self._build_tab_settings()
        self._build_tab_log()

        # Show main tab by default
        self._switch_tab("main")
        self._refresh_theme()

    # ─── native Windows Menu Bar ──────────────────────────────────────────────
    def _build_menu_bar(self):
        import tkinter as tk
        menu_bar = tk.Menu(self)
        
        # 1. File Menu (ملف)
        file_menu = tk.Menu(menu_bar, tearoff=0)
        file_menu.add_command(label="📁 فتح ملف الأرقام...", command=self._browse_contacts)
        file_menu.add_command(label="📥 استيراد متقدم...", command=self._open_import_dialog)
        file_menu.add_separator()
        file_menu.add_command(label="💾 حفظ القالب الحالي", command=self._save_template)
        file_menu.add_separator()
        file_menu.add_command(label="🚪 خروج", command=self._on_close)
        menu_bar.add_cascade(label="ملف", menu=file_menu)

        # 2. Edit Menu (تعديل)
        edit_menu = tk.Menu(menu_bar, tearoff=0)
        edit_menu.add_command(label="🧮 مولد أرقام جديد...", command=self._open_number_generator)
        edit_menu.add_separator()
        edit_menu.add_command(label="🗑️ مسح الرسالة", command=lambda: self.message_editor.set_text(""))
        edit_menu.add_command(label="🗑️ مسح المرفقات", command=lambda: self.attachment_manager.clear())
        menu_bar.add_cascade(label="تعديل", menu=edit_menu)

        # 3. View Menu (رأي)
        view_menu = tk.Menu(menu_bar, tearoff=0)
        view_menu.add_command(label="🌗 تبديل الوضع الداكن/الفاتح", command=self._toggle_appearance_menu)
        menu_bar.add_cascade(label="رأي", menu=view_menu)

        # 4. Settings Menu (الإعدادات)
        settings_menu = tk.Menu(menu_bar, tearoff=0)
        settings_menu.add_command(label="⚙️ إعدادات الإرسال والتأخير...", command=lambda: self._switch_tab("settings"))
        settings_menu.add_command(label="🛡️ إعدادات البروكسي وحماية بصمة المتصفح...", command=lambda: self._switch_tab("settings"))
        menu_bar.add_cascade(label="الإعدادات", menu=settings_menu)

        # 5. Tools Menu (أدوات)
        tools_menu = tk.Menu(menu_bar, tearoff=0)
        tools_menu.add_command(label="👥 مجموعات جهات الاتصال", command=lambda: self._switch_tab("groups"))
        tools_menu.add_command(label="🔍 فحص الأرقام", command=lambda: self._check_numbers_action())
        menu_bar.add_cascade(label="أدوات", menu=tools_menu)

        # 6. Help Menu (مساعدة)
        help_menu = tk.Menu(menu_bar, tearoff=0)
        help_menu.add_command(label="📖 دليل الاستخدام والمساعدة...", command=self._show_help_dialog)
        help_menu.add_command(label="📋 سجل الأحداث والتشخيص", command=lambda: self._switch_tab("log"))
        help_menu.add_separator()
        help_menu.add_command(label="ℹ️ حول البرنامج", command=self._show_about_dialog)
        menu_bar.add_cascade(label="مساعدة", menu=help_menu)

        self.configure(menu=menu_bar)

    # ─── Top Horizontal Toolbar ──────────────────────────────────────────────
    def _build_top_toolbar(self):
        # Toolbar Main Container Frame
        self.toolbar_frame = ctk.CTkFrame(self, height=72, corner_radius=0, fg_color=COLORS["primary_dark"])
        self.toolbar_frame.grid(row=0, column=0, sticky="ew")
        self.toolbar_frame.grid_propagate(False)

        tb_content = ctk.CTkFrame(self.toolbar_frame, fg_color="transparent")
        tb_content.pack(fill="both", expand=True, padx=10, pady=5)

        # 1. Login / Open WhatsApp button
        self.btn_tb_login = ctk.CTkButton(
            tb_content, text=self.tr("open_whatsapp"),
            font=("Segoe UI", 11, "bold"),
            width=95, height=52, corner_radius=8,
            fg_color=COLORS["secondary"], hover_color=COLORS["secondary_hover"],
            text_color=COLORS["secondary_text"],
            command=self._login_action
        )
        self.btn_tb_login.pack(side="right", padx=3)

        # 2. Tabs Navigation Buttons
        nav_items = [
            (self.tr("new_campaign"), "main"),
            (self.tr("groups_grabber"), "groups"),
            (self.tr("templates"), "templates"),
            (self.tr("settings"), "settings"),
            ("الأحداث", "log"),
        ]

        self.nav_buttons = {}
        for text, tab_id in nav_items:
            btn = ctk.CTkButton(
                tb_content, text=text,
                font=("Segoe UI", 11),
                width=90, height=52, corner_radius=8,
                fg_color="transparent",
                text_color=COLORS["text_muted"],
                hover_color=COLORS["bg_dark"],
                command=lambda t=tab_id: self._switch_tab(t)
            )
            btn.pack(side="right", padx=3)
            self.nav_buttons[tab_id] = btn

        # 3. Help Shortcut Button
        self.btn_tb_help = ctk.CTkButton(
            tb_content, text=self.tr("help"),
            font=("Segoe UI", 11),
            width=70, height=52, corner_radius=8,
            fg_color="transparent",
            text_color=COLORS["text_muted"],
            hover_color=COLORS["bg_dark"],
            command=self._show_help_dialog
        )
        self.btn_tb_help.pack(side="right", padx=3)

        # 4. Red Logout button (placed far left)
        self.btn_tb_logout = ctk.CTkButton(
            tb_content, text=self.tr("logout"),
            font=("Segoe UI", 12, "bold"),
            width=110, height=40, corner_radius=8,
            fg_color="#D32F2F", hover_color="#B71C1C",
            text_color="#FFFFFF",
            command=self._logout_action
        )
        self.btn_tb_logout.pack(side="left", padx=10, pady=6)

        # 5. Profile selector combobox (placed next to logout)
        self.profile_combo = ctk.CTkComboBox(
            tb_content, values=self._get_profiles(),
            variable=self.profile_var,
            command=self._on_profile_change,
            width=120, height=36,
            fg_color=COLORS["card_bg"],
            border_color=COLORS["border"],
            button_color=COLORS["primary"],
            button_hover_color=COLORS["primary_hover"],
            text_color=COLORS["text_main"],
            dropdown_fg_color=COLORS["card_bg"],
            dropdown_text_color=COLORS["text_main"]
        )
        self.profile_combo.pack(side="left", padx=5, pady=8)
        
        lbl_profile = ctk.CTkLabel(tb_content, text="Account:", font=("Segoe UI", 11), text_color=COLORS["text_muted"])
        lbl_profile.pack(side="left", padx=2)
        
        # 6. Language Toggle Button
        lang_text = "🇬🇧 EN" if self.current_lang.get() == "ar" else "🇸🇦 AR"
        self.btn_lang_toggle = ctk.CTkButton(
            tb_content, text=lang_text,
            font=("Segoe UI", 12, "bold"),
            width=60, height=36, corner_radius=8,
            fg_color=COLORS["card_bg"], hover_color=COLORS["border"],
            text_color=COLORS["text_main"],
            command=self._toggle_language
        )
        self.btn_lang_toggle.pack(side="left", padx=15, pady=8)

    def _toggle_language(self):
        new_lang = "en" if self.current_lang.get() == "ar" else "ar"
        self.current_lang.set(new_lang)
        self.config.set("language", new_lang)
        messagebox.showinfo("Language Changed", "Language has been changed. Please restart the application to apply the changes.")

    # ─── Bottom Status Bar ───────────────────────────────────────────────────
    def _build_bottom_bar(self):
        # Bottom Bar Container Frame
        self.bottom_bar = ctk.CTkFrame(self, height=45, corner_radius=0, fg_color=COLORS["primary_dark"])
        self.bottom_bar.grid(row=2, column=0, sticky="ew")
        self.bottom_bar.grid_propagate(False)

        # Left status text
        status_frame = ctk.CTkFrame(self.bottom_bar, fg_color="transparent")
        status_frame.pack(side="left", fill="y", padx=15, pady=2)

        self.status_indicator = ctk.CTkLabel(status_frame, text="●", font=("Segoe UI", 16), text_color=COLORS["danger"])
        self.status_indicator.pack(side="left", padx=5)

        self.session_status_label = ctk.CTkLabel(
            status_frame,
            text="Disconnected | Not Ready | Account: N/A",
            font=("Segoe UI", 12),
            text_color=COLORS["text_muted"]
        )
        self.session_status_label.pack(side="left", padx=5)

        # Live scheduled campaign indicator
        # Right Action Buttons
        actions_frame = ctk.CTkFrame(self.bottom_bar, fg_color="transparent")
        actions_frame.pack(side="right", fill="y", padx=15, pady=2)

        # Send Now Button
        self.btn_start = ctk.CTkButton(
            actions_frame, text="✈️ " + self.tr("btn_send_now"),
            font=("Segoe UI", 13, "bold"),
            width=125, height=32, corner_radius=6,
            fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"],
            text_color="#000000",
            command=self._start_action
        )
        self.btn_start.pack(side="right", padx=5)

        # 4. Pause / Stop Button
        self.btn_stop = ctk.CTkButton(
            actions_frame, text="🛑 " + self.tr("btn_pause_send"),
            font=("Segoe UI", 12, "bold"),
            width=100, height=32, corner_radius=6,
            fg_color=COLORS["danger"], hover_color=COLORS["danger_hover"],
            text_color="#FFFFFF",
            state="disabled",
            command=self._stop_action
        )
        self.btn_stop.pack(side="right", padx=5)

    def _switch_tab(self, tab_id):
        self.current_tab = tab_id
        for fid, frame in self.tab_frames.items():
            frame.grid_forget()
        self.tab_frames[tab_id].grid(row=0, column=0, sticky="nsew", padx=0, pady=0)

        # Highlight active nav item
        for nid, btn in self.nav_buttons.items():
            if nid == tab_id:
                btn.configure(fg_color=COLORS["primary"], text_color="#000000", font=("Segoe UI", 11, "bold"))
            else:
                btn.configure(fg_color="transparent", text_color=COLORS["text_muted"], font=("Segoe UI", 11))

    # ─── Main Tab (3-Column Workspace) ───────────────────────────────────────
    def _build_tab_main(self):
        frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.tab_frames["main"] = frame

        # Two columns: numbers | message + attachments
        frame.grid_columnconfigure(0, weight=2, minsize=360)
        frame.grid_columnconfigure(1, weight=2, minsize=400)
        frame.grid_rowconfigure(0, weight=1)

        # =======================================================================
        # COLUMN 0: Numbers list
        # =======================================================================
        col_mid = ctk.CTkFrame(frame, corner_radius=8, border_width=1, border_color=COLORS["border"])
        col_mid.grid(row=0, column=0, sticky="nsew", padx=3, pady=5)
        col_mid.grid_rowconfigure(2, weight=1)
        col_mid.grid_columnconfigure(0, weight=1)

        # Header for WhatsApp Numbers
        hdr_mid = ctk.CTkFrame(col_mid, fg_color="transparent", height=35)
        hdr_mid.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        
        lbl_mid = ctk.CTkLabel(hdr_mid, text="📋 " + self.tr("tab_whatsapp_numbers"), font=("Segoe UI", 15, "bold"), text_color=COLORS["primary"])
        lbl_mid.pack(side="right", padx=5)

        # Table Toolbar for imports & number edit
        tbl_toolbar = ctk.CTkFrame(col_mid, fg_color="transparent", height=32)
        tbl_toolbar.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 5))

        # Import shortcut button
        self.btn_check = ctk.CTkButton(
            tbl_toolbar, text="🔍 فحص الأرقام", font=("Segoe UI", 11, "bold"),
            width=100, height=28, corner_radius=6,
            fg_color=COLORS["info"], hover_color=COLORS["accent_hover"],
            text_color="#000000",
            command=self._check_numbers_action,
        )
        self.btn_check.pack(side="right", padx=5)

        self.btn_import_shortcut = ctk.CTkButton(
            tbl_toolbar, text="📥 استيراد الأرقام", font=("Segoe UI", 11, "bold"),
            width=110, height=28, corner_radius=6,
            fg_color=COLORS["secondary"], hover_color=COLORS["secondary_hover"],
            text_color=COLORS["secondary_text"],
            command=self._open_import_dialog
        )
        self.btn_import_shortcut.pack(side="right", padx=5)

        # Number Generator shortcut
        self.btn_gen_shortcut = ctk.CTkButton(
            tbl_toolbar, text="🧮 مولد الأرقام", font=("Segoe UI", 11),
            width=95, height=28, corner_radius=6,
            fg_color=COLORS["secondary"], hover_color=COLORS["secondary_hover"],
            text_color=COLORS["secondary_text"],
            command=self._open_number_generator
        )
        self.btn_gen_shortcut.pack(side="right", padx=5)

        # Hamburger Menu for import options
        self.btn_tbl_menu = ctk.CTkButton(
            tbl_toolbar, text="☰", font=("Segoe UI", 14),
            width=30, height=28, corner_radius=6,
            fg_color="transparent", hover_color=COLORS["bg_dark"],
            text_color=COLORS["text_main"],
            command=self._show_import_popup_menu
        )
        self.btn_tbl_menu.pack(side="left", padx=2)

        # Delete selected number button
        self.btn_tbl_del = ctk.CTkButton(
            tbl_toolbar, text="-", font=("Segoe UI", 16, "bold"),
            width=30, height=28, corner_radius=6,
            fg_color=COLORS["danger"], hover_color=COLORS["danger_hover"],
            text_color="#FFFFFF",
            command=self._remove_selected_table_number
        )
        self.btn_tbl_del.pack(side="left", padx=2)

        # Add manual number button
        self.btn_tbl_add = ctk.CTkButton(
            tbl_toolbar, text="+", font=("Segoe UI", 14, "bold"),
            width=30, height=28, corner_radius=6,
            fg_color=COLORS["success"], hover_color=COLORS["primary_hover"],
            text_color="#000000",
            command=self._add_manual_number_dialog
        )
        self.btn_tbl_add.pack(side="left", padx=2)

        # Secret hidden contacts entry for full backwards compatibility
        self.contacts_entry = ctk.CTkEntry(col_mid, width=1)
        self.contacts_entry.grid(row=0, column=0, sticky="w", padx=5)
        self.contacts_entry.grid_remove()  # Hidden but instantiated!

        # Numbers Treeview Table
        table_frame = ctk.CTkFrame(col_mid, fg_color="transparent")
        table_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=5)
        
        columns = ("name", "phone", "var1", "status")
        self.progress_tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=15)
        self.progress_tree.heading("name", text=self.tr("col_name"))
        self.progress_tree.heading("phone", text=self.tr("col_number"))
        self.progress_tree.heading("var1", text=self.tr("dialog_var1").replace(" field", "").replace(" حقل", ""))
        self.progress_tree.heading("status", text=self.tr("col_status"))
        
        self.progress_tree.column("name", width=120, anchor="e")
        self.progress_tree.column("phone", width=120, anchor="center")
        self.progress_tree.column("var1", width=90, anchor="e")
        self.progress_tree.column("status", width=70, anchor="center")
        
        self.progress_tree.tag_configure("pending", foreground=COLORS["text_muted"])
        self.progress_tree.tag_configure("sending", foreground=COLORS["accent"])
        self.progress_tree.tag_configure("success", foreground=COLORS["success"])
        self.progress_tree.tag_configure("failed", foreground=COLORS["danger"])
        self.progress_tree.tag_configure("invalid", foreground=COLORS["warning"])
        
        tbl_scroll = ctk.CTkScrollbar(table_frame, command=self.progress_tree.yview)
        self.progress_tree.configure(yscrollcommand=tbl_scroll.set)
        tbl_scroll.pack(side="right", fill="y")
        self.progress_tree.pack(side="left", fill="both", expand=True)

        # Right-click context menu for Numbers Table
        from tkinter import Menu
        self.numbers_context_menu = Menu(self, tearoff=0)
        self.numbers_context_menu.add_command(label="📥 " + self.tr("menu_imports_from_files"), command=self._open_import_dialog)
        self.numbers_context_menu.add_command(label="✍️ " + self.tr("menu_manual_imports"), command=self._add_bulk_manual_numbers_dialog)
        self.numbers_context_menu.add_separator()
        self.numbers_context_menu.add_command(label="🗑️ " + self.tr("menu_clear_list"), command=self._clear_numbers_table)
        
        self.progress_tree.bind("<Button-3>", self._show_numbers_context_menu)

        # Stats footer for numbers
        self.total_counts_label = ctk.CTkLabel(
            col_mid, text=f"{self.tr('lbl_groups')} 0 | {self.tr('lbl_contacts')} 0 | {self.tr('lbl_total')} 0",
            font=("Segoe UI", 11), text_color=COLORS["text_muted"]
        )
        self.total_counts_label.grid(row=3, column=0, sticky="ew", padx=15, pady=(2, 2))

        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(col_mid, height=8, corner_radius=4, progress_color=COLORS["primary"])
        self.progress_bar.grid(row=4, column=0, sticky="ew", padx=15, pady=(2, 2))
        self.progress_bar.set(0)

        # Progress status and counter
        prog_detail_frame = ctk.CTkFrame(col_mid, fg_color="transparent")
        prog_detail_frame.grid(row=5, column=0, sticky="ew", padx=15, pady=(2, 8))
        
        self.status_label = ctk.CTkLabel(
            prog_detail_frame, text="جاهز...",
            font=("Segoe UI", 11), text_color=COLORS["text_muted"]
        )
        self.status_label.pack(side="right")
        
        self.counter_label = ctk.CTkLabel(
            prog_detail_frame, text="✅ 0 | ❌ 0 | 🚫 0",
            font=("Segoe UI", 11, "bold"), text_color=COLORS["primary"]
        )
        self.counter_label.pack(side="left")


        # =======================================================================
        # COLUMN 1: Message editor & attachments
        # =======================================================================
        col_right = ctk.CTkFrame(frame, corner_radius=8, border_width=1, border_color=COLORS["border"])
        col_right.grid(row=0, column=1, sticky="nsew", padx=3, pady=5)
        col_right.grid_rowconfigure(0, weight=3)  # Message Editor
        col_right.grid_rowconfigure(1, weight=2)  # Attachments
        col_right.grid_columnconfigure(0, weight=1)

        # --- Top sub-pane: Message Editor ---
        pane_msg = ctk.CTkFrame(col_right, corner_radius=0, fg_color="transparent")
        pane_msg.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        pane_msg.grid_rowconfigure(1, weight=1)
        pane_msg.grid_columnconfigure(0, weight=1)

        # Message editor tabs
        msg_tabview = ctk.CTkTabview(pane_msg, height=220, corner_radius=8,
                                    segmented_button_selected_color=COLORS["primary"],
                                    segmented_button_selected_hover_color=COLORS["primary_hover"],
                                    segmented_button_unselected_color=COLORS["secondary"],
                                    text_color=COLORS["text_main"])
        msg_tabview.grid(row=1, column=0, sticky="nsew", pady=2)
        
        tab1 = msg_tabview.add(self.tr("tab_message") + " 1")
        
        # Message box editor inside tab1
        self.message_editor = RichTextFrame(tab1, colors=COLORS, fg_color=COLORS["bg_dark"], corner_radius=8)
        self.message_editor.pack(fill="both", expand=True)
        self.message_textbox = self.message_editor.text_box
        self.msg_text = self.message_textbox

        # Spintax and text option checkboxes below editor
        chk_frame = ctk.CTkFrame(pane_msg, fg_color="transparent", height=30)
        chk_frame.grid(row=2, column=0, sticky="ew", pady=(2, 2))

        self.send_text_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            chk_frame,
            text="إرسال النص كوصف مع أول مرفق (وضع مدمج — غير موصى به)",
            variable=self.send_text_var,
            font=("Segoe UI", 11),
        ).pack(side="right", padx=5)

        self.spin_text_var = ctk.BooleanVar(value=self.config.get("enable_spintax", True))
        ctk.CTkCheckBox(chk_frame, text="🎲 تدوير النص (Spintax)",
                        variable=self.spin_text_var,
                        font=("Segoe UI", 11)).pack(side="right", padx=5)

        self.preview_spintax_btn = ctk.CTkButton(
            chk_frame, text="🔍 معاينة",
            width=70, height=24, font=("Segoe UI", 11, "bold"),
            fg_color=COLORS["info"], hover_color=COLORS["accent_hover"],
            command=self._test_spintax
        )
        self.preview_spintax_btn.pack(side="left", padx=5)

        # --- Bottom sub-pane: Attachments ---
        pane_atts = ctk.CTkFrame(col_right, corner_radius=0, fg_color="transparent")
        pane_atts.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        pane_atts.grid_rowconfigure(1, weight=1)
        pane_atts.grid_columnconfigure(0, weight=1)

        # Attachment header
        hdr_atts = ctk.CTkFrame(pane_atts, fg_color="transparent", height=30)
        hdr_atts.grid(row=0, column=0, sticky="ew", pady=(2, 2))
        
        lbl_atts = ctk.CTkLabel(hdr_atts, text="📎 " + self.tr("lbl_attach_files"), font=("Segoe UI", 13, "bold"), text_color=COLORS["primary"])
        lbl_atts.pack(side="right", padx=5)

        # Hamburger Menu on the right for attachments
        self.btn_atts_menu = ctk.CTkButton(
            hdr_atts, text="☰", font=("Segoe UI", 12),
            width=26, height=24, corner_radius=4,
            fg_color="transparent", hover_color=COLORS["bg_dark"],
            text_color=COLORS["text_main"],
            command=self._show_attachments_popup_menu
        )
        self.btn_atts_menu.pack(side="left", padx=2)

        # Attachment list manager
        self.attachment_manager = AttachmentManager(pane_atts, colors=COLORS, fg_color=COLORS["card_bg"], corner_radius=8)
        self.attachment_manager.grid(row=1, column=0, sticky="nsew", pady=2)



    # ─── Groups Tab ───────────────────────────────────────────────────────
    def _build_tab_groups(self):
        frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.tab_frames["groups"] = frame

        header = ctk.CTkLabel(frame, text="👥 مجموعات جهات الاتصال",
                              font=ctk.CTkFont(size=20, weight="bold"))
        header.pack(anchor="e", padx=25, pady=(20, 5))

        desc = ctk.CTkLabel(frame, text="أنشئ مجموعات واستورد جهات اتصال من CSV أو Excel — ثم أرسل لأي مجموعة مباشرة.",
                            font=ctk.CTkFont(size=12), text_color=COLORS["text_muted"])
        desc.pack(anchor="e", padx=25, pady=(0, 12))

        body = ctk.CTkFrame(frame, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=20, pady=5)
        body.grid_columnconfigure(0, weight=2)
        body.grid_columnconfigure(1, weight=3)
        body.grid_rowconfigure(0, weight=1)

        # LEFT: Group list
        list_frame = ctk.CTkFrame(body, corner_radius=12)
        list_frame.grid(row=0, column=1, padx=(0, 8), pady=5, sticky="nsew")

        ctk.CTkLabel(list_frame, text="المجموعات",
                     font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="e", padx=12, pady=(10, 5))

        self.groups_listbox = ctk.CTkScrollableFrame(list_frame, corner_radius=8)
        self.groups_listbox.pack(fill="both", expand=True, padx=10, pady=(0, 5))

        grp_btn_row = ctk.CTkFrame(list_frame, fg_color="transparent")
        grp_btn_row.pack(fill="x", padx=10, pady=(0, 10))
        ctk.CTkButton(grp_btn_row, text="🗑️ حذف", width=75, height=32,
                      fg_color=COLORS["danger"], hover_color=COLORS["danger_hover"],
                      command=self._delete_group).pack(side="left", padx=3)
        ctk.CTkButton(grp_btn_row, text="📤 إرسال للمجموعة", width=120, height=32,
                      fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"],
                      command=self._send_to_group).pack(side="left", padx=3)

        # RIGHT: Group editor
        edit_frame = ctk.CTkFrame(body, corner_radius=12)
        edit_frame.grid(row=0, column=0, padx=(8, 0), pady=5, sticky="nsew")

        ctk.CTkLabel(edit_frame, text="اسم المجموعة:",
                     font=ctk.CTkFont(size=13)).pack(anchor="e", padx=12, pady=(12, 3))
        self.group_name_entry = ctk.CTkEntry(edit_frame, height=36, corner_radius=8,
                                             placeholder_text="مثلاً: عملاء القاهرة")
        self.group_name_entry.pack(fill="x", padx=12, pady=(0, 8))

        # Import file
        import_row = ctk.CTkFrame(edit_frame, fg_color="transparent")
        import_row.pack(fill="x", padx=12, pady=3)
        self.group_import_entry = ctk.CTkEntry(import_row, height=34, corner_radius=8,
                                               placeholder_text="ملف CSV / Excel ...")
        self.group_import_entry.pack(side="right", fill="x", expand=True, padx=(8, 0))
        ctk.CTkButton(import_row, text="📂 اختر", width=70, height=34,
                      fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"],
                      command=self._browse_group_file).pack(side="right")

        btn_row2 = ctk.CTkFrame(edit_frame, fg_color="transparent")
        btn_row2.pack(fill="x", padx=12, pady=5)
        ctk.CTkButton(btn_row2, text="➕ إنشاء واستيراد", height=38,
                      fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"],
                      font=ctk.CTkFont(size=13, weight="bold"),
                      command=self._create_group_and_import).pack(fill="x", pady=2)
        ctk.CTkButton(btn_row2, text="📥 إضافة جهات اتصال لمجموعة موجودة", height=34,
                      fg_color=COLORS["info"],
                      font=ctk.CTkFont(size=12),
                      command=self._add_contacts_to_group).pack(fill="x", pady=2)

        # Contacts preview
        ctk.CTkLabel(edit_frame, text="جهات الاتصال في المجموعة:",
                     font=ctk.CTkFont(size=13)).pack(anchor="e", padx=12, pady=(10, 3))
        self.group_contacts_list = ctk.CTkScrollableFrame(edit_frame, corner_radius=8, height=150)
        self.group_contacts_list.pack(fill="both", expand=True, padx=12, pady=(0, 5))

        self.group_info_label = ctk.CTkLabel(edit_frame, text="",
                                             font=ctk.CTkFont(size=11),
                                             text_color=COLORS["text_muted"])
        self.group_info_label.pack(anchor="e", padx=12, pady=(0, 10))

        self._refresh_groups_list()

    # ─── GMaps Scraper Tab ────────────────────────────────────────────────

    # ─── Warmer Tab ───────────────────────────────────────────────────────

    # ─── Templates Tab ────────────────────────────────────────────────────
    def _build_tab_templates(self):
        frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.tab_frames["templates"] = frame

        header = ctk.CTkLabel(frame, text="📝 قوالب الرسائل",
                              font=ctk.CTkFont(size=20, weight="bold"))
        header.pack(anchor="e", padx=25, pady=(20, 10))

        desc = ctk.CTkLabel(frame, text="احفظ رسائلك الجاهزة واستدعها بسرعة. المتغيرات: {name}, {phone}, {date}",
                            font=ctk.CTkFont(size=12), text_color=COLORS["text_muted"])
        desc.pack(anchor="e", padx=25, pady=(0, 15))

        body = ctk.CTkFrame(frame, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=20, pady=5)
        body.grid_columnconfigure(0, weight=2)
        body.grid_columnconfigure(1, weight=3)
        body.grid_rowconfigure(0, weight=1)

        # LEFT: Template list
        list_frame = ctk.CTkFrame(body, corner_radius=12)
        list_frame.grid(row=0, column=1, padx=(0, 8), pady=5, sticky="nsew")

        ctk.CTkLabel(list_frame, text="القوالب المحفوظة",
                     font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="e", padx=12, pady=(10, 5))

        self.templates_listbox = ctk.CTkScrollableFrame(list_frame, corner_radius=8)
        self.templates_listbox.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        btn_row = ctk.CTkFrame(list_frame, fg_color="transparent")
        btn_row.pack(fill="x", padx=10, pady=(0, 10))
        ctk.CTkButton(btn_row, text="🗑️ حذف", width=80, height=32,
                      fg_color=COLORS["danger"], hover_color=COLORS["danger_hover"],
                      command=self._delete_template).pack(side="left", padx=3)
        ctk.CTkButton(btn_row, text="📥 تحميل", width=80, height=32,
                      fg_color=COLORS["info"],
                      command=self._load_template).pack(side="left", padx=3)

        # RIGHT: Editor
        edit_frame = ctk.CTkFrame(body, corner_radius=12)
        edit_frame.grid(row=0, column=0, padx=(8, 0), pady=5, sticky="nsew")

        ctk.CTkLabel(edit_frame, text="اسم القالب:",
                     font=ctk.CTkFont(size=13)).pack(anchor="e", padx=12, pady=(12, 3))
        self.template_name_entry = ctk.CTkEntry(edit_frame, height=36, corner_radius=8,
                                                placeholder_text="مثال: رسالة رمضان")
        self.template_name_entry.pack(fill="x", padx=12, pady=(0, 8))

        ctk.CTkLabel(edit_frame, text="نص القالب:",
                     font=ctk.CTkFont(size=13)).pack(anchor="e", padx=12, pady=(5, 3))
        self.template_body_textbox = ctk.CTkTextbox(edit_frame, height=200, corner_radius=8,
                                                    font=ctk.CTkFont(size=13))
        self.template_body_textbox.pack(fill="both", expand=True, padx=12, pady=(0, 8))

        ctk.CTkButton(edit_frame, text="💾 حفظ القالب", height=40,
                      fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"],
                      font=ctk.CTkFont(size=13, weight="bold"),
                      command=self._save_template).pack(fill="x", padx=12, pady=(5, 12))

        self._refresh_templates_list()

    # ─── Settings Tab ─────────────────────────────────────────────────────
    def _build_tab_settings(self):
        frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.tab_frames["settings"] = frame

        header = ctk.CTkLabel(frame, text="⚙️ الإعدادات",
                              font=ctk.CTkFont(size=20, weight="bold"))
        header.pack(anchor="e", padx=25, pady=(20, 15))

        scroll = ctk.CTkScrollableFrame(frame, corner_radius=12)
        scroll.pack(fill="both", expand=True, padx=20, pady=(0, 15))

        # Delay Settings
        delay_card = ctk.CTkFrame(scroll, corner_radius=10)
        delay_card.pack(fill="x", padx=10, pady=8)
        ctk.CTkLabel(delay_card, text="⏱ تأخير بين الرسائل (ثانية)",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="e", padx=15, pady=(10, 5))

        delay_row = ctk.CTkFrame(delay_card, fg_color="transparent")
        delay_row.pack(fill="x", padx=15, pady=(0, 12))

        ctk.CTkLabel(delay_row, text="من:", font=ctk.CTkFont(size=12)).pack(side="right", padx=(5, 0))
        self.delay_min_entry = ctk.CTkEntry(delay_row, width=70, height=34, corner_radius=8,
                                            justify="center")
        self.delay_min_entry.pack(side="right", padx=5)
        self.delay_min_entry.insert(0, str(self.config.get("delay_min", 8)))

        ctk.CTkLabel(delay_row, text="إلى:", font=ctk.CTkFont(size=12)).pack(side="right", padx=(5, 0))
        self.delay_max_entry = ctk.CTkEntry(delay_row, width=70, height=34, corner_radius=8,
                                            justify="center")
        self.delay_max_entry.pack(side="right", padx=5)
        self.delay_max_entry.insert(0, str(self.config.get("delay_max", 25)))

        # Batch Settings
        batch_card = ctk.CTkFrame(scroll, corner_radius=10)
        batch_card.pack(fill="x", padx=10, pady=8)
        ctk.CTkLabel(batch_card, text="🔁 استراحة دورية",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="e", padx=15, pady=(10, 5))

        batch_row1 = ctk.CTkFrame(batch_card, fg_color="transparent")
        batch_row1.pack(fill="x", padx=15, pady=(0, 5))
        ctk.CTkLabel(batch_row1, text="بعد كل (رسالة):", font=ctk.CTkFont(size=12)).pack(side="right", padx=(5, 0))
        self.batch_size_entry = ctk.CTkEntry(batch_row1, width=70, height=34, corner_radius=8,
                                             justify="center")
        self.batch_size_entry.pack(side="right", padx=5)
        self.batch_size_entry.insert(0, str(self.config.get("batch_size", 30)))

        batch_row2 = ctk.CTkFrame(batch_card, fg_color="transparent")
        batch_row2.pack(fill="x", padx=15, pady=(0, 12))
        ctk.CTkLabel(batch_row2, text="استراحة من:", font=ctk.CTkFont(size=12)).pack(side="right", padx=(5, 0))
        self.batch_min_entry = ctk.CTkEntry(batch_row2, width=70, height=34, corner_radius=8,
                                            justify="center")
        self.batch_min_entry.pack(side="right", padx=5)
        self.batch_min_entry.insert(0, str(self.config.get("batch_pause_min", 180)))

        ctk.CTkLabel(batch_row2, text="إلى:", font=ctk.CTkFont(size=12)).pack(side="right", padx=(5, 0))
        self.batch_max_entry = ctk.CTkEntry(batch_row2, width=70, height=34, corner_radius=8,
                                            justify="center")
        self.batch_max_entry.pack(side="right", padx=5)
        self.batch_max_entry.insert(0, str(self.config.get("batch_pause_max", 240)))

        # Reliability Settings
        reliability_card = ctk.CTkFrame(scroll, corner_radius=10)
        reliability_card.pack(fill="x", padx=10, pady=8)
        ctk.CTkLabel(reliability_card, text="🧠 اعتمادية الإرسال",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="e", padx=15, pady=(10, 5))

        r1 = ctk.CTkFrame(reliability_card, fg_color="transparent")
        r1.pack(fill="x", padx=15, pady=(0, 5))
        ctk.CTkLabel(r1, text="عدد إعادة المحاولة:", font=ctk.CTkFont(size=12)).pack(side="right", padx=(5, 0))
        self.retry_count_entry = ctk.CTkEntry(r1, width=70, height=34, corner_radius=8, justify="center")
        self.retry_count_entry.pack(side="right", padx=5)
        self.retry_count_entry.insert(0, str(self.config.get("max_retries", 2)))

        r2 = ctk.CTkFrame(reliability_card, fg_color="transparent")
        r2.pack(fill="x", padx=15, pady=(0, 5))
        ctk.CTkLabel(r2, text="تأخير إعادة المحاولة من:", font=ctk.CTkFont(size=12)).pack(side="right", padx=(5, 0))
        self.retry_min_entry = ctk.CTkEntry(r2, width=70, height=34, corner_radius=8, justify="center")
        self.retry_min_entry.pack(side="right", padx=5)
        self.retry_min_entry.insert(0, str(self.config.get("retry_delay_min", 3)))

        ctk.CTkLabel(r2, text="إلى:", font=ctk.CTkFont(size=12)).pack(side="right", padx=(5, 0))
        self.retry_max_entry = ctk.CTkEntry(r2, width=70, height=34, corner_radius=8, justify="center")
        self.retry_max_entry.pack(side="right", padx=5)
        self.retry_max_entry.insert(0, str(self.config.get("retry_delay_max", 6)))

        r3 = ctk.CTkFrame(reliability_card, fg_color="transparent")
        r3.pack(fill="x", padx=15, pady=(0, 12))
        ctk.CTkLabel(r3, text="حد الفشل المتتالي:", font=ctk.CTkFont(size=12)).pack(side="right", padx=(5, 0))
        self.max_fail_entry = ctk.CTkEntry(r3, width=70, height=34, corner_radius=8, justify="center")
        self.max_fail_entry.pack(side="right", padx=5)
        self.max_fail_entry.insert(0, str(self.config.get("max_consecutive_failures", 5)))

        # Rotation Settings (Multi-Account Rotation)
        rotation_card = ctk.CTkFrame(scroll, corner_radius=10)
        rotation_card.pack(fill="x", padx=10, pady=8)
        ctk.CTkLabel(rotation_card, text="🔄 التدوير التلقائي للحسابات",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="e", padx=15, pady=(10, 5))

        rot_row1 = ctk.CTkFrame(rotation_card, fg_color="transparent")
        rot_row1.pack(fill="x", padx=15, pady=(0, 5))
        self.rotation_enabled_var = ctk.BooleanVar(value=self.config.get("rotation_enabled", False))
        ctk.CTkCheckBox(rot_row1, text="تفعيل التبديل التلقائي بين كل الحسابات المحفوظة أثناء الإرسال", 
                        variable=self.rotation_enabled_var, font=ctk.CTkFont(size=12)).pack(side="right", padx=5)

        rot_row2 = ctk.CTkFrame(rotation_card, fg_color="transparent")
        rot_row2.pack(fill="x", padx=15, pady=(0, 12))
        ctk.CTkLabel(rot_row2, text="التبديل إلى حساب جديد بعد إرسال (رسالة):", font=ctk.CTkFont(size=12)).pack(side="right", padx=(5, 0))
        self.rotation_interval_entry = ctk.CTkEntry(rot_row2, width=70, height=34, corner_radius=8, justify="center")
        self.rotation_interval_entry.pack(side="right", padx=5)
        self.rotation_interval_entry.insert(0, str(self.config.get("rotation_interval", 50)))

        # General Settings (New)
        general_card = ctk.CTkFrame(scroll, corner_radius=10)
        general_card.pack(fill="x", padx=10, pady=8)
        ctk.CTkLabel(general_card, text="⚙️ إعدادات عامة",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="e", padx=15, pady=(10, 5))

        g1 = ctk.CTkFrame(general_card, fg_color="transparent")
        g1.pack(fill="x", padx=15, pady=(0, 12))
        ctk.CTkLabel(g1, text="رمز الدولة الافتراضي (دون +):", font=ctk.CTkFont(size=12)).pack(side="right", padx=(5, 0))
        self.country_code_entry = ctk.CTkEntry(g1, width=70, height=34, corner_radius=8, justify="center")
        self.country_code_entry.pack(side="right", padx=5)
        self.country_code_entry.insert(0, str(self.config.get("default_country_code", "20")))

        # Proxy & VPN Settings Card
        proxy_card = ctk.CTkFrame(scroll, corner_radius=10)
        proxy_card.pack(fill="x", padx=10, pady=8)
        ctk.CTkLabel(proxy_card, text="🛡️ إعدادات البروكسي والخصوصية (Proxy & Privacy Settings)",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="e", padx=15, pady=(10, 5))

        # Checkbox and Type row
        chk_row = ctk.CTkFrame(proxy_card, fg_color="transparent")
        chk_row.pack(fill="x", padx=15, pady=(0, 5))
        
        self.proxy_enabled_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(chk_row, text="تفعيل اتصال البروكسي", variable=self.proxy_enabled_var,
                        font=ctk.CTkFont(size=12)).pack(side="right", padx=5)
                        
        self.proxy_type_var = ctk.StringVar(value="HTTP")
        ctk.CTkLabel(chk_row, text="النوع:", font=ctk.CTkFont(size=12)).pack(side="left", padx=(5, 0))
        self.proxy_type_menu = ctk.CTkOptionMenu(
            chk_row,
            values=["HTTP", "SOCKS5"],
            variable=self.proxy_type_var,
            width=90,
            height=28,
            fg_color=COLORS["card_bg"],
            button_color=COLORS["primary"],
            button_hover_color=COLORS["primary_hover"],
            text_color=COLORS["text_main"],
            dropdown_fg_color=COLORS["card_bg"],
            dropdown_text_color=COLORS["text_main"],
        )
        self.proxy_type_menu.pack(side="left", padx=5)

        # Host and Port row
        addr_row = ctk.CTkFrame(proxy_card, fg_color="transparent")
        addr_row.pack(fill="x", padx=15, pady=5)
        
        ctk.CTkLabel(addr_row, text="العنوان (IP/Host):", font=ctk.CTkFont(size=12)).pack(side="right", padx=(5, 0))
        self.proxy_host_entry = ctk.CTkEntry(addr_row, width=200, height=34, corner_radius=8,
                                             placeholder_text="e.g. 192.168.1.1 or proxy.com")
        self.proxy_host_entry.pack(side="right", padx=5)
        
        ctk.CTkLabel(addr_row, text="المنفذ (Port):", font=ctk.CTkFont(size=12)).pack(side="right", padx=(5, 0))
        self.proxy_port_entry = ctk.CTkEntry(addr_row, width=80, height=34, corner_radius=8,
                                            justify="center", placeholder_text="8080")
        self.proxy_port_entry.pack(side="right", padx=5)

        # Auth credentials row
        auth_row = ctk.CTkFrame(proxy_card, fg_color="transparent")
        auth_row.pack(fill="x", padx=15, pady=5)
        
        ctk.CTkLabel(auth_row, text="المستخدم (اختياري):", font=ctk.CTkFont(size=12)).pack(side="right", padx=(5, 0))
        self.proxy_username_entry = ctk.CTkEntry(auth_row, width=120, height=34, corner_radius=8,
                                                 placeholder_text="Username")
        self.proxy_username_entry.pack(side="right", padx=5)
        
        ctk.CTkLabel(auth_row, text="كلمة المرور (اختياري):", font=ctk.CTkFont(size=12)).pack(side="right", padx=(5, 0))
        self.proxy_password_entry = ctk.CTkEntry(auth_row, width=120, height=34, corner_radius=8,
                                                 show="*", placeholder_text="Password")
        self.proxy_password_entry.pack(side="right", padx=5)

        # Action/Test connection row
        action_row = ctk.CTkFrame(proxy_card, fg_color="transparent")
        action_row.pack(fill="x", padx=15, pady=(5, 10))
        
        self.test_proxy_btn = ctk.CTkButton(
            action_row,
            text="⚡ فحص الاتصال",
            width=120,
            height=32,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._test_proxy_connection
        )
        self.test_proxy_btn.pack(side="right", padx=5)
        
        self.proxy_status_label = ctk.CTkLabel(
            action_row,
            text="الحالة: لم يتم الفحص",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_muted"]
        )
        self.proxy_status_label.pack(side="left", padx=5)

        # Fingerprint section separator
        sep = ctk.CTkFrame(proxy_card, height=2, fg_color=COLORS["border"])
        sep.pack(fill="x", padx=15, pady=8)
        
        ctk.CTkLabel(proxy_card, text="🛡️ بصمة المتصفح وحماية الهوية (Identity Protection)",
                     font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="e", padx=15, pady=(2, 5))

        # Fingerprint toggle row
        fp_toggle_row = ctk.CTkFrame(proxy_card, fg_color="transparent")
        fp_toggle_row.pack(fill="x", padx=15, pady=2)
        
        self.fp_enabled_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(fp_toggle_row, text="تغيير بصمة المتصفح (User-Agent & Viewport) للحساب", 
                        variable=self.fp_enabled_var, font=ctk.CTkFont(size=12)).pack(side="right", padx=5)

        # Fingerprint values display row
        fp_row = ctk.CTkFrame(proxy_card, fg_color="transparent")
        fp_row.pack(fill="x", padx=15, pady=5)
        
        # User-Agent read-only entry
        ctk.CTkLabel(fp_row, text="User-Agent:", font=ctk.CTkFont(size=11)).pack(side="right", padx=(5, 0))
        self.fp_ua_entry = ctk.CTkEntry(fp_row, width=280, height=28, corner_radius=6, font=ctk.CTkFont(size=10))
        self.fp_ua_entry.pack(side="right", padx=5)
        
        # Resolution entry
        ctk.CTkLabel(fp_row, text="الأبعاد:", font=ctk.CTkFont(size=11)).pack(side="right", padx=(5, 0))
        self.fp_res_entry = ctk.CTkEntry(fp_row, width=80, height=28, corner_radius=6, justify="center", font=ctk.CTkFont(size=11))
        self.fp_res_entry.pack(side="right", padx=5)
        
        # Generate new fingerprint button
        self.fp_gen_btn = ctk.CTkButton(
            fp_row,
            text="🔄 توليد جديدة",
            width=90,
            height=28,
            fg_color=COLORS["secondary"],
            hover_color=COLORS["secondary_hover"],
            text_color=COLORS["secondary_text"],
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self._generate_new_profile_fingerprint
        )
        self.fp_gen_btn.pack(side="left", padx=5)

        # Save Button
        ctk.CTkButton(scroll, text="💾 حفظ الإعدادات", height=42,
                      font=ctk.CTkFont(size=14, weight="bold"),
                      fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"],
                      command=self._save_settings).pack(fill="x", padx=10, pady=15)

    # ─── Log Tab ──────────────────────────────────────────────────────────
    def _build_tab_log(self):
        frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.tab_frames["log"] = frame

        header_row = ctk.CTkFrame(frame, fg_color="transparent")
        header_row.pack(fill="x", padx=20, pady=(15, 5))

        ctk.CTkLabel(
            header_row,
            text="📋 سجل الأحداث والتشخيص",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).pack(side="right")

        ctk.CTkButton(
            header_row,
            text="📂 فتح ملف السجل",
            width=110,
            height=32,
            fg_color=COLORS["secondary"],
            hover_color=COLORS["secondary_hover"],
            command=self._open_log_file,
        ).pack(side="left", padx=4)

        ctk.CTkButton(
            header_row,
            text="🗑️ مسح",
            width=80,
            height=32,
            fg_color=COLORS["danger"],
            hover_color=COLORS["danger_hover"],
            command=self._clear_log,
        ).pack(side="left", padx=4)

        hint = ctk.CTkLabel(
            frame,
            text="كل خطوة من البوت والإرسال تظهر هنا وفي التيرمنال (python main.py). عند مشكلة الصور ابحث عن ERROR أو «لم يُعثر على حقل».",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_muted"],
            wraplength=900,
            justify="right",
        )
        hint.pack(fill="x", padx=20, pady=(0, 6))

        self.log_textbox = ctk.CTkTextbox(
            frame,
            font=ctk.CTkFont(family="Consolas", size=12),
            corner_radius=12,
            state="disabled",
        )
        self.log_textbox.pack(fill="both", expand=True, padx=20, pady=(5, 15))
        self.log("✅ سجل التشخيص جاهز — شغّل الحملة وراقب الأحداث هنا.")

    # ═══════════════════════════════════════════════════════════════════════
    #  UI HELPERS
    # ═══════════════════════════════════════════════════════════════════════
    def _process_ui_queue(self):
        while True:
            try:
                fn = self.ui_queue.get_nowait()
            except queue.Empty:
                break
            try:
                fn()
            except Exception as e:
                import sys
                print(f"Error in UI queue callback: {e}", file=sys.stderr)
            finally:
                self.ui_queue.task_done()
        self.after(50, self._process_ui_queue)

    def _run_on_ui(self, fn):
        self.ui_queue.put(fn)

    def _set_session_status(self, text, color=None):
        def _do():
            if not hasattr(self, "session_status_label"):
                return
            self.session_status_label.configure(
                text=text,
                text_color=COLORS["text_main"],
            )
            if hasattr(self, "status_indicator"):
                self.status_indicator.configure(
                    text_color=color or COLORS["text_muted"]
                )
        self._run_on_ui(_do)

    def _start_status_monitor(self):
        """Starts a background monitor thread to keep session status updated."""
        def monitor_loop():
            last_status = None
            while True:
                time.sleep(3)
                try:
                    if self.bot and self.bot.driver:
                        # Check if browser was closed
                        try:
                            handles = self.bot.driver.window_handles
                            if not handles:
                                status = "closed"
                            else:
                                logged = self.bot.is_logged_in()
                                status = "connected" if logged else "waiting"
                        except Exception:
                            status = "closed"
                    else:
                        status = "offline"

                    if status != last_status:
                        last_status = status
                        self._run_on_ui(lambda s=status: self._update_session_status_from_monitor(s))
                except Exception:
                    pass

        threading.Thread(target=monitor_loop, daemon=True).start()

    def _update_session_status_from_monitor(self, status):
        """Updates the GUI status label safely from the background monitor."""
        if self.is_running or self.is_checking:
            return  # Do not overwrite status text during active campaigns or contact checks
            
        if status == "connected":
            self._set_session_status("الحالة: متصل", COLORS["success"])
        elif status == "waiting":
            self._set_session_status("الحالة: في انتظار تسجيل الدخول...", COLORS["warning"])
        elif status == "closed" or status == "offline":
            self._set_session_status("الحالة: غير متصل", COLORS["danger"])

    def log(self, message, level="INFO"):
        line = format_event(level, message) if not str(message).startswith("[") else message

        if self._log_to_terminal:
            try:
                import sys
                print(line, file=sys.stderr, flush=True)
            except Exception:
                pass

        def _do():
            if not hasattr(self, "log_textbox"):
                return
            self.log_textbox.configure(state="normal")
            self.log_textbox.insert("end", line + "\n")
            self.log_textbox.see("end")
            self.log_textbox.configure(state="disabled")
        self._run_on_ui(_do)
        try:
            os.makedirs(self.log_dir, exist_ok=True)
            with open(self.log_file_path, "a", encoding="utf-8") as f:
                f.write(line + "\n")
        except Exception:
            pass

    def _on_bot_event(self, level, message, detail=None):
        """Callback from WhatsAppBot — same stream as UI log + terminal."""
        self.log(format_event(level, message, detail))

    def _open_log_file(self):
        try:
            os.makedirs(self.log_dir, exist_ok=True)
            if os.path.exists(self.log_file_path):
                os.startfile(self.log_file_path)
            else:
                messagebox.showinfo("السجل", "لا يوجد ملف سجل بعد. ابدأ إرسالاً أولاً.")
        except Exception as e:
            messagebox.showerror("خطأ", str(e))

    def _clear_log(self):
        self.log_textbox.configure(state="normal")
        self.log_textbox.delete("1.0", "end")
        self.log_textbox.configure(state="disabled")
        self.log("تم مسح السجل.", level="INFO")

    def _agent_debug_log(self, hypothesis_id, location, message, data=None):
        # #region agent log
        try:
            log_path = os.path.join(os.getcwd(), "debug-364cc6.log")
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(
                    json.dumps(
                        {
                            "sessionId": "364cc6",
                            "hypothesisId": hypothesis_id,
                            "location": location,
                            "message": message,
                            "data": data or {},
                            "timestamp": int(time.time() * 1000),
                        },
                        ensure_ascii=False,
                    )
                    + "\n"
                )
        except Exception:
            pass
        # #endregion

    def _on_login_success(self):
        """After WhatsApp login: auto-continue pending send/check without blocking dialogs."""
        self.log("✅ تم تسجيل الدخول بنجاح!")
        self._set_session_status("الحالة: متصل", COLORS["success"])
        has_send = bool(self.pending_start_payload)
        has_check = bool(self.pending_check_contacts)
        self._agent_debug_log(
            "H1",
            "modern_ui.py:_on_login_success",
            "login_success",
            {"has_pending_send": has_send, "has_pending_check": has_check},
        )
        if has_send:
            self.log("🚀 بدء الإرسال تلقائياً بعد تسجيل الدخول.")
            self._run_on_ui(self._run_pending_start)
        elif has_check:
            pending_contacts = self.pending_check_contacts
            self.pending_check_contacts = None
            self.log("🔍 بدء فحص الأرقام تلقائياً بعد تسجيل الدخول.")
            self._run_on_ui(lambda: self._check_numbers_action(pending_contacts))
        else:
            self.log("✅ تم تسجيل الدخول — يمكنك الضغط على «بدء الإرسال» متى شئت.")

    def _show_dialog(self, kind, title, message):
        def _do():
            if kind == "info":
                messagebox.showinfo(title, message)
            elif kind == "warning":
                messagebox.showwarning(title, message)
            else:
                messagebox.showerror(title, message)
        self._run_on_ui(_do)

    def report_error(self, code, message=None, detail=None, dialog=True, level="error"):
        base_message = message or ERROR_CATALOG.get(code, "حدث خطأ غير معروف.")
        log_message = f"[{code}] {base_message}"
        if detail:
            log_message += f" | {detail}"
        self.log(log_message)
        if dialog:
            dialog_message = f"{base_message}\n\nالكود: {code}"
            self._show_dialog(level, "تنبيه" if level == "warning" else "خطأ", dialog_message)

    def _update_stats(self):
        total = self.sent + self.failed + self.invalid
        if hasattr(self, "stat_cards") and self.stat_cards:
            try:
                self.stat_cards["total"].configure(text=str(total))
                self.stat_cards["success"].configure(text=str(self.sent))
                self.stat_cards["failed"].configure(text=str(self.failed))
                self.stat_cards["invalid"].configure(text=str(self.invalid))
            except Exception:
                pass
        if hasattr(self, "counter_label") and self.counter_label and self.counter_label.winfo_exists():
            try:
                self.counter_label.configure(text=f"✅ {self.sent} | ❌ {self.failed} | 🚫 {self.invalid}")
            except Exception:
                pass

    def _update_total_counts(self, total=0, contacts_count=0, groups_count=0):
        if hasattr(self, "total_counts_label"):
            self.total_counts_label.configure(
                text=f"الإجمالي: {total} | جهات: {contacts_count} | مجموعات: {groups_count}"
            )

    def _show_error_codes(self):
        lines = [f"{code} — {desc}" for code, desc in ERROR_CATALOG.items()]
        self._show_dialog("info", "أكواد الأخطاء", "\n".join(lines))

    # ═══════════════════════════════════════════════════════════════════════
    #  FILE BROWSE
    # ═══════════════════════════════════════════════════════════════════════
    def _create_file_row(self, parent, label_text, entry_attr, browse_cmd):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=15, pady=4)
        
        ctk.CTkLabel(row, text=label_text, width=100, anchor="e", font=("Segoe UI", 12, "bold"),
                     text_color=COLORS["text_muted"]).pack(side="right", padx=(5, 0))
        
        entry = ctk.CTkEntry(row, placeholder_text="اختر الملف...", height=35, 
                             corner_radius=8, font=("Segoe UI", 12), border_color=COLORS["border"],
                             fg_color=COLORS["bg_dark"], text_color=COLORS["text_main"])
        entry.pack(side="right", fill="x", expand=True, padx=5)
        setattr(self, entry_attr, entry)
        
        ctk.CTkButton(row, text="📂", width=40, height=35,
                      fg_color=COLORS["secondary"], hover_color=COLORS["secondary_hover"],
                      text_color=COLORS["secondary_text"],
                      font=("Segoe UI", 14),
                      command=browse_cmd).pack(side="right")

    def _browse_contacts(self):
        path = filedialog.askopenfilename(filetypes=[("Contacts", "*.csv;*.xlsx;*.xls;*.txt")])
        if path:
            self.contacts_entry.delete(0, "end")
            self.contacts_entry.insert(0, path)
            self._update_contact_count(path)

    def _update_contact_count(self, path=None):
        """Update contact count label and load contacts into the numbers table."""
        try:
            if not path:
                path = self.contacts_entry.get()
            if not path or not os.path.exists(path):
                return
            from utils.helpers import read_contacts_auto
            contacts = read_contacts_auto(path, default_country_code=self.config.get("default_country_code", "20"))
            
            # Refresh the Treeview numbers table
            self._refresh_numbers_table(contacts)
            
            if hasattr(self, "contact_count_label") and self.contact_count_label:
                count = len(contacts)
                self.contact_count_label.configure(
                    text=f"📊 {count} جهة اتصال" if count > 0 else "⚠️ لا توجد جهات اتصال"
                )
        except Exception as e:
            self.log(f"⚠️ خطأ أثناء تحديث قائمة الأرقام: {e}")

    def _open_import_dialog(self):
        win = ctk.CTkToplevel(self)
        win.title(self.tr("dialog_import_title"))
        win.geometry("900x620")
        win.minsize(880, 580)
        win.grab_set()

        file_var = ctk.StringVar(value="")
        header_var = ctk.BooleanVar(value=True)
        custom_delim_var = ctk.BooleanVar(value=False)
        delim_var = ctk.StringVar(value=",")
        dedup_var = ctk.BooleanVar(value=True)

        headers = []
        preview_rows = []

        # Top: File picker
        file_frame = ctk.CTkFrame(win, corner_radius=10)
        file_frame.pack(fill="x", padx=15, pady=(15, 8))
        ctk.CTkLabel(file_frame, text=self.tr("dialog_select_file") + ":", font=ctk.CTkFont(size=12, weight="bold")).pack(side="right", padx=10)
        file_entry = ctk.CTkEntry(file_frame, textvariable=file_var, height=32, corner_radius=8)
        file_entry.pack(side="right", fill="x", expand=True, padx=10, pady=8)

        def _browse_file():
            path = filedialog.askopenfilename(filetypes=[("CSV/Excel", "*.csv;*.xlsx;*.xls;*.txt")])
            if path:
                file_var.set(path)
                _load_preview()

        ctk.CTkButton(file_frame, text=self.tr("dialog_browse"), width=90, height=32,
                      fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"],
                      command=_browse_file).pack(side="left", padx=10)

        # Settings
        settings_frame = ctk.CTkFrame(win, corner_radius=10)
        settings_frame.pack(fill="x", padx=15, pady=(0, 8))
        ctk.CTkLabel(settings_frame, text=self.tr("dialog_settings"), font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="e", padx=12, pady=(8, 4))

        settings_row = ctk.CTkFrame(settings_frame, fg_color="transparent")
        settings_row.pack(fill="x", padx=10, pady=(0, 8))
        ctk.CTkCheckBox(settings_row, text=self.tr("dialog_use_first_row"), variable=header_var,
                        command=lambda: _load_preview()).pack(side="right", padx=6)
        ctk.CTkCheckBox(settings_row, text=self.tr("dialog_custom_delimiter"), variable=custom_delim_var,
                        command=lambda: _load_preview()).pack(side="right", padx=6)
        delim_entry = ctk.CTkEntry(settings_row, textvariable=delim_var, width=60, height=28)
        delim_entry.pack(side="right", padx=6)
        ctk.CTkCheckBox(settings_row, text=self.tr("dialog_remove_duplications"), variable=dedup_var).pack(side="right", padx=6)
        ctk.CTkButton(settings_row, text="↻ Refresh", height=28,
                      fg_color=COLORS["secondary"], hover_color=COLORS["secondary_hover"],
                      text_color=COLORS["secondary_text"],
                      command=lambda: _load_preview()).pack(side="left", padx=6)

        # Field Mapping
        mapping_frame = ctk.CTkFrame(win, corner_radius=10)
        mapping_frame.pack(fill="x", padx=15, pady=(0, 8))
        ctk.CTkLabel(mapping_frame, text=self.tr("dialog_assign_fields"), font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="e", padx=12, pady=(8, 4))

        map_row = ctk.CTkFrame(mapping_frame, fg_color="transparent")
        map_row.pack(fill="x", padx=10, pady=(0, 8))

        def _make_field(label, var):
            frame = ctk.CTkFrame(map_row, fg_color="transparent")
            frame.pack(side="right", padx=6)
            ctk.CTkLabel(frame, text=label, font=ctk.CTkFont(size=11)).pack()
            menu = ctk.CTkOptionMenu(frame, values=["—"], variable=var, width=120,
                                     fg_color=COLORS["bg_dark"], text_color=COLORS["text_main"],
                                     button_color=COLORS["primary"], button_hover_color=COLORS["primary_hover"],
                                     dropdown_fg_color=COLORS["card_bg"], dropdown_text_color=COLORS["text_main"])
            menu.pack()
            return menu

        name_var = ctk.StringVar(value="—")
        phone_var = ctk.StringVar(value="—")
        var1_var = ctk.StringVar(value="—")
        var2_var = ctk.StringVar(value="—")
        var3_var = ctk.StringVar(value="—")
        var4_var = ctk.StringVar(value="—")
        var5_var = ctk.StringVar(value="—")

        menus = {
            "name": _make_field(self.tr("dialog_name_field"), name_var),
            "phone": _make_field(self.tr("dialog_number_field"), phone_var),
            "var1": _make_field(self.tr("dialog_var1"), var1_var),
            "var2": _make_field(self.tr("dialog_var2"), var2_var),
            "var3": _make_field(self.tr("dialog_var3"), var3_var),
            "var4": _make_field(self.tr("dialog_var4"), var4_var),
            "var5": _make_field(self.tr("dialog_var5"), var5_var),
        }

        # Preview
        preview_frame = ctk.CTkFrame(win, corner_radius=10)
        preview_frame.pack(fill="both", expand=True, padx=15, pady=(0, 8))
        ctk.CTkLabel(preview_frame, text="معاينة البيانات (أول 30 صف)", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="e", padx=12, pady=(8, 4))
        preview_list = ctk.CTkScrollableFrame(preview_frame, corner_radius=8)
        preview_list.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        def _set_menu_values(values):
            vals = ["—"] + values
            for m in menus.values():
                m.configure(values=vals)

        def _guess_field(headers_list):
            def find(keys):
                for h in headers_list:
                    hl = h.lower()
                    for k in keys:
                        if k in hl:
                            return h
                return "—"
            
            guessed = {
                "name": find(["name", "full", "given", "اسم", "الاسم"]),
                "phone": find(["phone", "mobile", "number", "رقم", "هاتف", "phone 1 - value"]),
                "var1": find(["var1", "var 1", "variable1", "v1", "custom1"]),
                "var2": find(["var2", "var 2", "variable2", "v2", "custom2"]),
                "var3": find(["var3", "var 3", "variable3", "v3", "custom3"]),
                "var4": find(["var4", "var 4", "variable4", "v4", "custom4"]),
                "var5": find(["var5", "var 5", "variable5", "v5", "custom5"]),
            }

            # Smart fallback heuristics if phone is not matched by keyword
            if guessed["phone"] == "—" and headers_list:
                # Heuristic 1: If there is only one column in the file, it must be the phone number!
                if len(headers_list) == 1:
                    guessed["phone"] = headers_list[0]
                else:
                    # Heuristic 2: Analyze the preview rows to find the column that looks like phone numbers.
                    best_col = None
                    max_phone_score = 0
                    for col_idx, col_name in enumerate(headers_list):
                        score = 0
                        # Check up to 10 rows in preview
                        for r in preview_rows[:10]:
                            if col_idx < len(r):
                                val = str(r[col_idx]).strip()
                                # Clean value from common formatting like +, -, spaces
                                val_clean = val.replace("+", "").replace("-", "").replace(" ", "").replace("(", "").replace(")", "")
                                # Phone number is typically numeric, length between 7 and 15
                                if val_clean.isdigit() and 7 <= len(val_clean) <= 15:
                                    score += 1
                        if score > max_phone_score:
                            max_phone_score = score
                            best_col = col_name
                    
                    if best_col:
                        guessed["phone"] = best_col
                    else:
                        # Heuristic 3: Check if the header itself looks like a phone number
                        for col_name in headers_list:
                            val_clean = str(col_name).strip().replace("+", "").replace("-", "").replace(" ", "").replace("(", "").replace(")", "")
                            if val_clean.isdigit() and 7 <= len(val_clean) <= 15:
                                guessed["phone"] = col_name
                                break

            # Smart fallback for name
            if guessed["name"] == "—" and headers_list:
                # If there are multiple columns and one is already guessed as phone,
                # let's guess the other column as name if it's not phone and not already matched.
                for col in headers_list:
                    if col != guessed["phone"] and col not in [guessed["var1"], guessed["var2"], guessed["var3"], guessed["var4"], guessed["var5"]]:
                        # A column containing non-digit values is likely a name
                        alpha_score = 0
                        for r in preview_rows[:5]:
                            try:
                                col_idx = headers_list.index(col)
                                if col_idx < len(r):
                                    val = str(r[col_idx]).strip()
                                    if any(c.isalpha() for c in val) and not val.replace("+","").replace("-","").isdigit():
                                        alpha_score += 1
                            except:
                                pass
                        if alpha_score >= 2:
                            guessed["name"] = col
                            break
                            
            return guessed

        def _render_preview():
            for w in preview_list.winfo_children():
                w.destroy()
            if not headers:
                ctk.CTkLabel(preview_list, text="لا توجد بيانات للعرض",
                             font=ctk.CTkFont(size=11), text_color=COLORS["text_muted"]).pack(pady=10)
                return
            max_cols = min(len(headers), 8)
            head_row = ctk.CTkFrame(preview_list, fg_color=COLORS["card_bg"])
            head_row.pack(fill="x", pady=2)
            for i in range(max_cols):
                ctk.CTkLabel(head_row, text=headers[i], width=120, anchor="e",
                             font=ctk.CTkFont(size=11, weight="bold")).pack(side="right", padx=2)
            for row in preview_rows:
                r = ctk.CTkFrame(preview_list, fg_color="transparent")
                r.pack(fill="x", pady=1)
                for i in range(max_cols):
                    val = row[i] if i < len(row) else ""
                    ctk.CTkLabel(r, text=str(val), width=120, anchor="e",
                                 font=ctk.CTkFont(size=10)).pack(side="right", padx=2)

        def _read_csv(path):
            import csv
            rows = []
            delim = None
            if custom_delim_var.get() and delim_var.get().strip():
                delim = delim_var.get().strip()
            try:
                with open(path, "r", encoding="utf-8-sig", errors="ignore") as f:
                    sample = f.read(2048)
                    f.seek(0)
                    if not delim:
                        try:
                            dialect = csv.Sniffer().sniff(sample, delimiters=[",", ";", "\t", "|"])
                            delim = dialect.delimiter
                        except Exception:
                            delim = ","
                    reader = csv.reader(f, delimiter=delim)
                    for row in reader:
                        rows.append(row)
            except Exception:
                rows = []
            return rows

        def _read_excel(path):
            try:
                import openpyxl
                wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
                ws = wb.active
                rows = []
                for row in ws.iter_rows(values_only=True):
                    rows.append([str(c) if c is not None else "" for c in row])
                wb.close()
                return rows
            except Exception:
                return []

        def _load_preview():
            nonlocal headers, preview_rows
            path = file_var.get().strip()
            headers = []
            preview_rows = []
            if not path or not os.path.exists(path):
                _render_preview()
                return
            ext = os.path.splitext(path)[1].lower()
            rows = _read_excel(path) if ext in (".xlsx", ".xls") else _read_csv(path)
            if not rows:
                _render_preview()
                return
            if header_var.get():
                headers = [h.strip() if h else f"Col{i+1}" for i, h in enumerate(rows[0])]
                data_rows = rows[1:]
            else:
                headers = [f"Col{i+1}" for i in range(len(rows[0]))]
                data_rows = rows
            preview_rows = data_rows[:30]
            _set_menu_values(headers)
            guess = _guess_field(headers)
            name_var.set(guess["name"])
            phone_var.set(guess["phone"])
            var1_var.set(guess["var1"])
            var2_var.set(guess["var2"])
            var3_var.set(guess["var3"])
            var4_var.set(guess["var4"])
            var5_var.set(guess["var5"])
            _render_preview()

        def _read_all_rows(path):
            ext = os.path.splitext(path)[1].lower()
            return _read_excel(path) if ext in (".xlsx", ".xls") else _read_csv(path)

        def _import_now():
            path = file_var.get().strip()
            if not path or not os.path.exists(path):
                messagebox.showerror("خطأ", "يرجى اختيار ملف صالح.")
                return

            rows = _read_all_rows(path)
            if not rows:
                messagebox.showerror("خطأ", "تعذر قراءة الملف.")
                return

            if header_var.get():
                hdrs = [h.strip() if h else f"Col{i+1}" for i, h in enumerate(rows[0])]
                data_rows = rows[1:]
            else:
                hdrs = [f"Col{i+1}" for i in range(len(rows[0]))]
                data_rows = rows

            def col_index(col_name):
                if not col_name or col_name == "—":
                    return None
                try:
                    return hdrs.index(col_name)
                except ValueError:
                    return None

            idx_name = col_index(name_var.get())
            idx_phone = col_index(phone_var.get())
            idx_v1 = col_index(var1_var.get())
            idx_v2 = col_index(var2_var.get())
            idx_v3 = col_index(var3_var.get())
            idx_v4 = col_index(var4_var.get())
            idx_v5 = col_index(var5_var.get())

            from utils.helpers import normalize_phone

            contacts = []
            seen = set()
            invalid = 0
            for row in data_rows:
                phone_raw = row[idx_phone] if idx_phone is not None and idx_phone < len(row) else ""
                phone = normalize_phone(phone_raw, default_country_code=self.config.get("default_country_code", "20"))
                if not phone:
                    invalid += 1
                    continue
                if dedup_var.get() and phone in seen:
                    continue
                seen.add(phone)

                name = row[idx_name] if idx_name is not None and idx_name < len(row) else ""
                c = {
                    "name": str(name).strip() if name is not None else "",
                    "phone": phone,
                }
                if idx_v1 is not None and idx_v1 < len(row):
                    c["var1"] = str(row[idx_v1]) if row[idx_v1] is not None else ""
                if idx_v2 is not None and idx_v2 < len(row):
                    c["var2"] = str(row[idx_v2]) if row[idx_v2] is not None else ""
                if idx_v3 is not None and idx_v3 < len(row):
                    c["var3"] = str(row[idx_v3]) if row[idx_v3] is not None else ""
                if idx_v4 is not None and idx_v4 < len(row):
                    c["var4"] = str(row[idx_v4]) if row[idx_v4] is not None else ""
                if idx_v5 is not None and idx_v5 < len(row):
                    c["var5"] = str(row[idx_v5]) if row[idx_v5] is not None else ""
                contacts.append(c)

            if not contacts:
                messagebox.showwarning("تنبيه", "لم يتم العثور على أرقام صالحة.")
                return

            imports_dir = os.path.join(os.getcwd(), "data", "imports")
            os.makedirs(imports_dir, exist_ok=True)
            filename = f"import_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            filepath = os.path.join(imports_dir, filename)

            import csv as _csv
            with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
                writer = _csv.DictWriter(f, fieldnames=["Name", "Phone", "Var1", "Var2", "Var3", "Var4", "Var5"])
                writer.writeheader()
                for c in contacts:
                    writer.writerow({
                        "Name": c.get("name", ""),
                        "Phone": c.get("phone", ""),
                        "Var1": c.get("var1", ""),
                        "Var2": c.get("var2", ""),
                        "Var3": c.get("var3", ""),
                        "Var4": c.get("var4", ""),
                        "Var5": c.get("var5", ""),
                    })

            self.contacts_entry.delete(0, "end")
            self.contacts_entry.insert(0, filepath)
            self.config.set("last_contacts_file", filepath)
            self.config.save()
            self._update_contact_count(filepath)

            messagebox.showinfo("تم", f"تم الاستيراد: {len(contacts)} رقم\nغير صالح: {invalid}")
            win.destroy()

        # Bottom buttons
        btn_row = ctk.CTkFrame(win, fg_color="transparent")
        btn_row.pack(fill="x", padx=15, pady=(0, 15))
        ctk.CTkButton(btn_row, text=self.tr("dialog_btn_cancel"), width=90, height=32,
                      fg_color=COLORS["secondary"], hover_color=COLORS["secondary_hover"],
                      text_color=COLORS["secondary_text"],
                      command=win.destroy).pack(side="left", padx=6)
        ctk.CTkButton(btn_row, text=self.tr("dialog_btn_import"), width=100, height=32,
                      fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"],
                      command=_import_now).pack(side="left", padx=6)

        _load_preview()

    def _open_number_generator(self):
        win = ctk.CTkToplevel(self)
        win.title("مولد أرقام")
        win.geometry("520x420")
        win.minsize(480, 400)
        win.grab_set()

        cc_var = ctk.StringVar(value="20")
        base_var = ctk.StringVar(value="10")
        start_var = ctk.StringVar(value="00000000")
        end_var = ctk.StringVar(value="00000010")
        pad_var = ctk.StringVar(value="8")
        name_prefix_var = ctk.StringVar(value="Lead")

        preview_box = ctk.CTkTextbox(win, height=180, corner_radius=10,
                                     font=ctk.CTkFont(size=11),
                                     fg_color=COLORS["bg_dark"])
        preview_box.pack(fill="both", expand=True, padx=12, pady=(10, 8))

        def _render_preview(numbers):
            preview_box.delete("1.0", "end")
            for n in numbers[:50]:
                preview_box.insert("end", f"{n}\n")

        def _generate_numbers():
            try:
                cc = cc_var.get().strip()
                base = base_var.get().strip()
                pad = int(pad_var.get().strip() or "0")
                start = int(start_var.get().strip())
                end = int(end_var.get().strip())
            except Exception:
                messagebox.showerror("خطأ", "تحقق من القيم المدخلة.")
                return []
            if start > end:
                start, end = end, start
            numbers = []
            for i in range(start, end + 1):
                body = str(i).zfill(pad) if pad > 0 else str(i)
                numbers.append(f"{cc}{base}{body}")
            return numbers

        def _refresh_preview():
            nums = _generate_numbers()
            _render_preview(nums)

        def _save_and_use():
            nums = _generate_numbers()
            if not nums:
                return
            imports_dir = os.path.join(os.getcwd(), "data", "imports")
            os.makedirs(imports_dir, exist_ok=True)
            filename = f"generated_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            filepath = os.path.join(imports_dir, filename)

            import csv as _csv
            with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
                writer = _csv.DictWriter(f, fieldnames=["Name", "Phone"])
                writer.writeheader()
                prefix = name_prefix_var.get().strip() or "Lead"
                for idx, n in enumerate(nums, start=1):
                    writer.writerow({"Name": f"{prefix} {idx}", "Phone": n})

            self.contacts_entry.delete(0, "end")
            self.contacts_entry.insert(0, filepath)
            self.config.set("last_contacts_file", filepath)
            self.config.save()
            messagebox.showinfo("تم", f"تم توليد {len(nums)} رقم.")
            win.destroy()

        form = ctk.CTkFrame(win, corner_radius=10)
        form.pack(fill="x", padx=12, pady=(0, 8))

        def _row(label, var):
            r = ctk.CTkFrame(form, fg_color="transparent")
            r.pack(fill="x", padx=8, pady=4)
            ctk.CTkLabel(r, text=label, width=120, anchor="e").pack(side="right")
            ctk.CTkEntry(r, textvariable=var, height=28).pack(side="right", fill="x", expand=True, padx=6)

        _row("رمز الدولة", cc_var)
        _row("بداية الرقم", start_var)
        _row("نهاية الرقم", end_var)
        _row("طول الجزء", pad_var)
        _row("بداية إضافية", base_var)
        _row("اسم افتراضي", name_prefix_var)

        btns = ctk.CTkFrame(win, fg_color="transparent")
        btns.pack(fill="x", padx=12, pady=(0, 12))
        ctk.CTkButton(btns, text="معاينة", width=90, height=30,
                      fg_color=COLORS["secondary"], hover_color=COLORS["secondary_hover"],
                      text_color=COLORS["secondary_text"],
                      command=_refresh_preview).pack(side="left", padx=6)
        ctk.CTkButton(btns, text="حفظ واستخدام", width=110, height=30,
                      fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"],
                      command=_save_and_use).pack(side="left", padx=6)

    def _refresh_templates_list(self):
        for w in self.templates_listbox.winfo_children():
            w.destroy()
            
        templates = self.templates.get_all()
        if not templates:
            ctk.CTkLabel(self.templates_listbox, text="لا توجد قوالب محفوظة.", 
                         font=("Segoe UI", 12), text_color=COLORS["text_muted"]).pack(pady=20)
            return

        for t in templates:
            card = ctk.CTkFrame(self.templates_listbox, fg_color=COLORS["card_bg"], corner_radius=10)
            card.pack(fill="x", pady=5, padx=5)
            
            # Header
            head = ctk.CTkFrame(card, fg_color="transparent", height=30)
            head.pack(fill="x", padx=10, pady=(8, 0))
            
            ctk.CTkLabel(head, text=t["name"], font=("Segoe UI", 13, "bold"), 
                         text_color=COLORS["primary"]).pack(side="right")
            
            ctk.CTkLabel(head, text=t["updated"], font=("Segoe UI", 10), 
                         text_color=COLORS["text_muted"]).pack(side="left")
            
            # Body Preview
            body_prev = t["body"][:60] + "..." if len(t["body"]) > 60 else t["body"]
            ctk.CTkLabel(card, text=body_prev, font=("Segoe UI", 11), 
                         text_color=COLORS["text_muted"], anchor="e", justify="right").pack(fill="x", padx=10, pady=(5, 10))
            
            # Actions
            actions = ctk.CTkFrame(card, fg_color="transparent", height=30)
            actions.pack(fill="x", padx=10, pady=(0, 10))
            
            ctk.CTkButton(actions, text="اختيار", width=60, height=24, 
                          fg_color=COLORS["primary"], font=("Segoe UI", 11, "bold"), text_color="black",
                          command=lambda n=t["name"]: self._select_template(n)).pack(side="left", padx=2)
            
            ctk.CTkButton(actions, text="حذف", width=50, height=24, 
                          fg_color=COLORS["danger"], hover_color=COLORS["danger_hover"],
                          text_color="#FFFFFF",
                          font=("Segoe UI", 11),
                          command=lambda n=t["name"]: self._delete_template_by_name(n)).pack(side="left", padx=2)

    def _select_template(self, name):
        t = self.templates.get_by_name(name)
        if t:
            self.template_name_entry.delete(0, "end")
            self.template_name_entry.insert(0, t["name"])
            self.template_body_textbox.delete("1.0", "end")
            self.template_body_textbox.insert("1.0", t["body"])

    def _save_template(self):
        name = self.template_name_entry.get().strip()
        body = self.template_body_textbox.get("1.0", "end").strip()
        if not name:
            messagebox.showwarning("تنبيه", "يرجى إدخال اسم القالب.")
            return
        if not body:
            messagebox.showwarning("تنبيه", "يرجى إدخال نص القالب.")
            return
        self.templates.add(name, body)
        self._refresh_templates_list()
        messagebox.showinfo("تم", f"تم حفظ القالب: {name}")

    def _delete_template(self):
        name = self.template_name_entry.get().strip()
        if not name:
            return
        if messagebox.askyesno("تأكيد", f"هل تريد حذف القالب '{name}'؟"):
            self.templates.delete(name)
            self.template_name_entry.delete(0, "end")
            self.template_body_textbox.delete("1.0", "end")
            self._refresh_templates_list()

    def _load_template(self):
        name = self.template_name_entry.get().strip()
        t = self.templates.get_by_name(name)
        if t:
            self.message_textbox.delete("1.0", "end")
            self.message_textbox.insert("1.0", t["body"])
            self._switch_tab("main")
            messagebox.showinfo("تم", f"تم تحميل القالب '{name}' إلى الرسالة.")
        else:
            messagebox.showwarning("تنبيه", "يرجى اختيار قالب أولاً.")

    # ═══════════════════════════════════════════════════════════════════════
    #  GROUPS MANAGEMENT
    # ═══════════════════════════════════════════════════════════════════════
    def _refresh_groups_list(self):
        for w in self.groups_listbox.winfo_children():
            w.destroy()
        
        groups = self.contacts_mgr.get_all()
        if not groups:
            ctk.CTkLabel(self.groups_listbox, text="لا توجد مجموعات بعد", 
                         font=("Segoe UI", 12), text_color=COLORS["text_muted"]).pack(pady=20)
            return

        for g in groups:
            count = len(g.get("contacts", []))
            text = f"📁 {g['name']}  ({count})"
            
            btn = ctk.CTkButton(self.groups_listbox, text=text,
                                font=("Segoe UI", 13),
                                fg_color=COLORS["secondary"],
                                hover_color=COLORS["secondary_hover"],
                                text_color=COLORS["secondary_text"],
                                anchor="e", height=42, corner_radius=8,
                                command=lambda name=g["name"]: self._select_group(name))
            btn.pack(fill="x", pady=3)

    def _select_group(self, name):
        self.group_name_entry.delete(0, "end")
        self.group_name_entry.insert(0, name)
        g = self.contacts_mgr.get_by_name(name)
        if g:
            for w in self.group_contacts_list.winfo_children():
                w.destroy()
            for c in g["contacts"][:50]:  # Show first 50
                ctk.CTkLabel(self.group_contacts_list,
                             text=f"{c.get('name', '-')}  |  {c.get('phone', '-')}",
                             font=ctk.CTkFont(size=11),
                             anchor="e").pack(fill="x", padx=5, pady=1)
            total = len(g["contacts"])
            extra = f" (عرض أول 50 من {total})" if total > 50 else ""
            self.group_info_label.configure(text=f"📊 {total} جهة اتصال{extra} | آخر تحديث: {g.get('updated', '-')}")

    def _browse_group_file(self):
        path = filedialog.askopenfilename(filetypes=[
            ("جهات الاتصال", "*.csv;*.xlsx;*.xls;*.txt"),
            ("CSV", "*.csv"),
            ("Excel", "*.xlsx;*.xls"),
            ("Text", "*.txt"),
        ])
        if path:
            self.group_import_entry.delete(0, "end")
            self.group_import_entry.insert(0, path)

    def _create_group_and_import(self):
        name = self.group_name_entry.get().strip()
        if not name:
            messagebox.showwarning("تنبيه", "يرجى إدخال اسم المجموعة.")
            return
        file_path = self.group_import_entry.get().strip()
        contacts = read_contacts_auto(file_path, default_country_code=self.config.get("default_country_code", "20")) if file_path else []
        if self.contacts_mgr.get_by_name(name):
            messagebox.showwarning("تنبيه", f"المجموعة '{name}' موجودة بالفعل. استخدم 'إضافة جهات اتصال'.")
            return
        self.contacts_mgr.create_group(name, contacts)
        self._refresh_groups_list()
        self._select_group(name)
        count = len(contacts)
        messagebox.showinfo("تم", f"تم إنشاء المجموعة '{name}' مع {count} جهة اتصال.")

    def _add_contacts_to_group(self):
        name = self.group_name_entry.get().strip()
        if not name or not self.contacts_mgr.get_by_name(name):
            messagebox.showwarning("تنبيه", "يرجى اختيار مجموعة موجودة أولاً.")
            return
        file_path = self.group_import_entry.get().strip()
        if not file_path:
            messagebox.showwarning("تنبيه", "يرجى اختيار ملف CSV / Excel.")
            return
        contacts = read_contacts_auto(file_path, default_country_code=self.config.get("default_country_code", "20"))
        if not contacts:
            messagebox.showwarning("تنبيه", "لم يتم العثور على جهات اتصال صالحة في الملف.")
            return
        added = self.contacts_mgr.add_contacts(name, contacts)
        self._refresh_groups_list()
        self._select_group(name)
        messagebox.showinfo("تم", f"تم إضافة {added} جهة اتصال جديدة إلى '{name}'.")

    def _delete_group(self):
        name = self.group_name_entry.get().strip()
        if not name:
            return
        if messagebox.askyesno("تأكيد", f"هل تريد حذف المجموعة '{name}'؟"):
            self.contacts_mgr.delete_group(name)
            self.group_name_entry.delete(0, "end")
            for w in self.group_contacts_list.winfo_children():
                w.destroy()
            self.group_info_label.configure(text="")
            self._refresh_groups_list()

    def _send_to_group(self):
        name = self.group_name_entry.get().strip()
        g = self.contacts_mgr.get_by_name(name) if name else None
        if not g or not g["contacts"]:
            messagebox.showwarning("تنبيه", "يرجى اختيار مجموعة تحتوي على جهات اتصال.")
            return
        # Switch to main tab and start with these contacts
        self._switch_tab("main")
        self.contacts_entry.delete(0, "end")
        self.contacts_entry.insert(0, f"[GROUP:{name}]")
        messagebox.showinfo("تم", f"تم تحديد مجموعة '{name}' ({len(g['contacts'])} جهة). اضغط 'بدء الإرسال'.")

    # ════════════════════════════════════════════════════════════
    #  WORKFLOWS
    # ════════════════════════════════════════════════════════════















    # ═══════════════════════════════════════════════════════════════════════
    #  SCHEDULING
    # ═══════════════════════════════════════════════════════════════════════






    # ═══════════════════════════════════════════════════════════════════════
    #  ANALYTICS TAB
    # ═══════════════════════════════════════════════════════════════════════



    def _open_csv(self, path):
        if path and os.path.exists(path):
            os.startfile(path)
        else:
            messagebox.showerror("خطأ", "ملف التقرير غير موجود.")

    # ═══════════════════════════════════════════════════════════════════════
    #  SETTINGS
    # ═══════════════════════════════════════════════════════════════════════
    def _save_settings(self):
        try:
            self.config.set("delay_min", int(self.delay_min_entry.get()))
            self.config.set("delay_max", int(self.delay_max_entry.get()))
            self.config.set("batch_size", int(self.batch_size_entry.get()))
            self.config.set("batch_pause_min", int(self.batch_min_entry.get()))
            self.config.set("batch_pause_max", int(self.batch_max_entry.get()))
            self.config.set("max_retries", int(self.retry_count_entry.get()))
            self.config.set("retry_delay_min", int(self.retry_min_entry.get()))
            self.config.set("retry_delay_max", int(self.retry_max_entry.get()))
            self.config.set("max_consecutive_failures", int(self.max_fail_entry.get()))
            
            # Rotation Settings
            if hasattr(self, "rotation_enabled_var"):
                self.config.set("rotation_enabled", self.rotation_enabled_var.get())
                self.config.set("rotation_interval", int(self.rotation_interval_entry.get()))
            
            # Save default country code
            cc_raw = self.country_code_entry.get().strip().replace("+", "")
            if not cc_raw:
                cc_raw = "20"
            elif not cc_raw.isdigit():
                messagebox.showerror("خطأ", "كود الدولة يجب أن يتكون من أرقام فقط (مثال: 20 أو 966).")
                return
            self.config.set("default_country_code", cc_raw)

            if hasattr(self, "proxy_enabled_var"):
                current_profile = self.config.get("profile_name", "Default")
                profile_proxies = self.config.get("profile_proxies", {})
                profile_proxies[current_profile] = {
                    "enabled": self.proxy_enabled_var.get(),
                    "type": self.proxy_type_var.get(),
                    "host": self.proxy_host_entry.get().strip(),
                    "port": self.proxy_port_entry.get().strip(),
                    "username": self.proxy_username_entry.get().strip(),
                    "password": self.proxy_password_entry.get().strip(),
                    "fingerprint_enabled": self.fp_enabled_var.get(),
                    "user_agent": self.fp_ua_entry.get().strip(),
                    "resolution": self.fp_res_entry.get().strip()
                }
                self.config.set("profile_proxies", profile_proxies)

            self.config.save()
            messagebox.showinfo("تم", "تم حفظ الإعدادات بنجاح.")
        except ValueError:
            messagebox.showerror("خطأ", "يرجى إدخال أرقام صحيحة في جميع الحقول.")

    def _toggle_appearance(self):
        mode = self.appearance_switch.get()
        ctk.set_appearance_mode(mode)
        self.config.set_and_save("appearance_mode", mode)
        self._apply_palette(mode)
        self._refresh_theme()
        messagebox.showinfo("تم", "تم تغيير المظهر.")

    def _load_saved_state(self):
        # Load last used files
        last_csv = self.config.get("last_contacts_file", "")
        if last_csv and os.path.exists(last_csv):
            self.contacts_entry.insert(0, last_csv)
        else:
            def_csv = os.path.join(os.getcwd(), "contacts.csv")
            if os.path.exists(def_csv):
                self.contacts_entry.insert(0, def_csv)

        if hasattr(self, "attachment_manager"):
            self.attachment_manager.clear()
            saved_attachments = self.config.get("last_attachments", [])
            if isinstance(saved_attachments, list):
                for att in saved_attachments:
                    path = str(att.get("path", "")).strip()
                    type_ = str(att.get("type", "document") or "document")
                    caption = str(att.get("caption", "") or "")
                    if path and os.path.exists(path):
                        self.attachment_manager._add_item(path, type_, caption)

            legacy_files = [
                ("last_image_file", "image"),
                ("last_video_file", "video"),
                ("last_doc_file", "document"),
            ]
            if not self.attachment_manager.get_attachments():
                for key, type_ in legacy_files:
                    path = str(self.config.get(key, "") or "").strip()
                    if path and os.path.exists(path):
                        self.attachment_manager._add_item(path, type_)


        # Load last message
        last_msg = self.config.get("last_message", "")
        if last_msg:
            self.message_textbox.insert("1.0", last_msg)

        # Load checkboxes
        self.send_text_var.set(self.config.get("send_text_with_image", False))
        self.bg_mode_var.set(self.config.get("background_mode", False))
        self.spin_text_var.set(self.config.get("enable_spintax", True))
        if hasattr(self, "use_valid_after_check_var"):
            self.use_valid_after_check_var.set(self.config.get("use_valid_after_check", False))

        # Load profile proxy settings at startup
        profile_name = self.config.get("profile_name", "Default")
        self._load_profile_proxy_settings(profile_name)

    def _save_current_state(self):
        self.config.set("last_contacts_file", self.contacts_entry.get())
        self.config.set("last_message", self.message_textbox.get("1.0", "end").strip())
        attachments = self.attachment_manager.get_attachments() if hasattr(self, "attachment_manager") else []
        self.config.set("last_attachments", attachments)
        self.config.set("last_image_file", next((a.get("path", "") for a in attachments if a.get("type") == "image"), ""))
        self.config.set("last_video_file", next((a.get("path", "") for a in attachments if a.get("type") == "video"), ""))
        self.config.set("last_doc_file", next((a.get("path", "") for a in attachments if a.get("type") == "document"), ""))
        self.config.set("send_text_with_image", self.send_text_var.get())
        self.config.set("background_mode", self.bg_mode_var.get())
        self.config.set("enable_spintax", self.spin_text_var.get())
        if hasattr(self, "use_valid_after_check_var"):
            self.config.set("use_valid_after_check", self.use_valid_after_check_var.get())
        # Save window size
        self.config.set("window_width", self.winfo_width())
        self.config.set("window_height", self.winfo_height())
        self.config.save()

    def _on_close(self):
        self._save_current_state()
        if self.bot:
            self.bot.close()
        self.destroy()


    def _close_progress_window(self):
        if self.is_running or self.is_checking:
            if messagebox.askyesno("تأكيد", "عملية الإرسال/الفحص لا تزال جارية. هل تريد إيقاف العملية وإغلاق هذه الشاشة؟"):
                self.stop_event.set()
                if self.pause_event.is_set():
                    self.pause_event.clear()
                    self.is_paused = False
                self.log("🛑 طلب إيقاف وإغلاق من شاشة المتابعة...")
            else:
                return  # Do not close

        if self.progress_win and self.progress_win.winfo_exists():
            try:
                self.progress_win.destroy()
            except Exception:
                pass
        self.progress_win = None
        self.popup_progress_tree = None
        self.progress_count_label = None
        self.progress_status_label = None
        self.progress_bar_small = None
        self.progress_state_label = None
        self.progress_metric_labels = {}
        self.pause_btn = None

    def _export_last_report(self):
        if self.last_report_path and os.path.exists(self.last_report_path):
            self._open_csv(self.last_report_path)
        else:
            messagebox.showinfo("تنبيه", "لا يوجد تقرير للتصدير بعد.")

    def _toggle_pause(self):
        if not self.is_running:
            return
        if self.is_paused:
            self.pause_event.clear()
            self.is_paused = False
            if getattr(self, "pause_btn", None) and self.pause_btn.winfo_exists():
                self.pause_btn.configure(text="Pause")
            self._set_progress_status("Resumed...")
        else:
            self.pause_event.set()
            self.is_paused = True
            if getattr(self, "pause_btn", None) and self.pause_btn.winfo_exists():
                self.pause_btn.configure(text="Resume")
            self._set_progress_status("Paused")

    def _set_progress_status(self, text):
        def _do():
            if self.progress_status_label:
                self.progress_status_label.configure(text=text)
        self._run_on_ui(_do)


    # ═══════════════════════════════════════════════════════════════════════
    #  BOT ACTIONS
    # ═══════════════════════════════════════════════════════════════════════
    def _wait_for_login_worker(self):
        """Background: wait for QR scan on an already-open browser."""
        try:
            login_status = self.bot.wait_for_login(timeout=900)
            if login_status == "SUCCESS":
                self._on_login_success()
            elif login_status == "CLOSED":
                self.log("ℹ️ تم إغلاق متصفح تسجيل الدخول أو إيقافه بواسطة المستخدم.")
                self._set_session_status("الحالة: غير متصل", COLORS["danger"])
                self.pending_start_payload = None
                self.pending_check_contacts = None
            else:
                self.report_error("ERR-02", dialog=True, level="warning")
                self._set_session_status("الحالة: غير متصل", COLORS["danger"])
                self.pending_start_payload = None
                self.pending_check_contacts = None
        except Exception as e:
            self.report_error("ERR-01", detail=str(e), dialog=True)
            self._set_session_status("الحالة: غير متصل", COLORS["danger"])
            self.pending_start_payload = None
            self.pending_check_contacts = None

    def _login_action(self):
        # Check if the bot exists and the driver is actively open (has windows)
        is_active = False
        if self.bot and self.bot.driver:
            try:
                is_active = len(self.bot.driver.window_handles) > 0
            except Exception:
                is_active = False

        if is_active:
            self.bot.background_mode = False
            self.bot.bring_to_front()
            has_pending = bool(self.pending_start_payload or self.pending_check_contacts)
            self._agent_debug_log(
                "H2",
                "modern_ui.py:_login_action",
                "browser_already_active",
                {
                    "logged_in": bool(self.bot.is_logged_in()),
                    "has_pending": has_pending,
                },
            )
            if self.bot.is_logged_in():
                self._on_login_success()
                return
            self._set_session_status("الحالة: في انتظار تسجيل الدخول...", COLORS["warning"])
            if has_pending:
                self.log("⏳ المتصفح مفتوح — انتظار مسح QR ثم متابعة الإرسال تلقائياً...")
                threading.Thread(target=self._wait_for_login_worker, daemon=True).start()
                return
            self.log("المتصفح مفتوح بالفعل — أكمل تسجيل الدخول من واتساب ويب.")
            return

        def run_login():
            try:
                self._set_session_status("الحالة: جاري فتح المتصفح...", COLORS["info"])
                self.log("جاري فتح المتصفح...")
                active_profile = self.config.get("profile_name", "Default")
                profile_proxies = self.config.get("profile_proxies", {})
                proxy_config = profile_proxies.get(active_profile, {"enabled": False})
                self.bot = WhatsAppBot(
                    self.user_data_dir,
                    proxy_config=proxy_config,
                    on_event=self._on_bot_event,
                )
                self.bot.open_whatsapp()
                self.bot.background_mode = False
                self.bot.bring_to_front()
                self._set_session_status("الحالة: في انتظار تسجيل الدخول...", COLORS["warning"])
                self.log("يرجى فتح واتساب على الهاتف ومسح QR لتسجيل الدخول...")
                self.log("💡 تلميح: يرجى الانتظار 3 ثوانٍ بعد ظهور الباركود قبل مسحه بالهاتف لضمان استقرار الاتصال من المرة الأولى.")
                
                login_status = self.bot.wait_for_login(timeout=900)
                if login_status == "SUCCESS":
                    self._on_login_success()
                elif login_status == "CLOSED":
                    self.log("ℹ️ تم إغلاق متصفح تسجيل الدخول أو إيقافه بواسطة المستخدم.")
                    self._set_session_status("الحالة: غير متصل", COLORS["danger"])
                    self.pending_start_payload = None
                    self.pending_check_contacts = None
                else:  # "TIMEOUT"
                    self.report_error("ERR-02", dialog=True, level="warning")
                    self._set_session_status("الحالة: غير متصل", COLORS["danger"])
                    self.pending_start_payload = None
                    self.pending_check_contacts = None
            except Exception as e:
                if "ERR_PROFILE_LOCKED" in str(e):
                    self.report_error("ERR-11", dialog=True)
                else:
                    self.report_error("ERR-01", detail=str(e), dialog=True)
                self._set_session_status("الحالة: غير متصل", COLORS["danger"])
                self.pending_start_payload = None
                self.pending_check_contacts = None

        threading.Thread(target=run_login, daemon=True).start()

    def _run_pending_start(self):
        pending = self.pending_start_payload
        self.pending_start_payload = None
        self._agent_debug_log(
            "H3",
            "modern_ui.py:_run_pending_start",
            "run_pending_start",
            {"has_pending": bool(pending), "is_running": bool(self.is_running)},
        )
        if not pending:
            return
        if isinstance(pending, tuple):
            self._begin_send(*pending)

    def _get_profiles(self):
        try:
            profiles = [d for d in os.listdir(self.profiles_dir) if os.path.isdir(os.path.join(self.profiles_dir, d))]
            if os.path.exists(self.legacy_profile_dir) and "Legacy" not in profiles:
                profiles.append("Legacy")
            return profiles
        except:
            return ["Default"]

    def _on_profile_change(self, choice):
        if self.bot and self.bot.driver:
            messagebox.showwarning("تنبيه", "لا يمكن تغيير الحساب أثناء تشغيل المتصفح. يرجى إغلاق المتصفح أولاً.")
            if self.user_data_dir == self.legacy_profile_dir:
                self.profile_var.set("Legacy")
            else:
                self.profile_var.set(os.path.basename(self.user_data_dir))
            return

        # Save current proxy fields to the old profile configuration
        if hasattr(self, "proxy_enabled_var"):
            old_profile = self.config.get("profile_name", "Default")
            profile_proxies = self.config.get("profile_proxies", {})
            profile_proxies[old_profile] = {
                "enabled": self.proxy_enabled_var.get(),
                "type": self.proxy_type_var.get(),
                "host": self.proxy_host_entry.get().strip(),
                "port": self.proxy_port_entry.get().strip(),
                "username": self.proxy_username_entry.get().strip(),
                "password": self.proxy_password_entry.get().strip(),
                "fingerprint_enabled": self.fp_enabled_var.get(),
                "user_agent": self.fp_ua_entry.get().strip(),
                "resolution": self.fp_res_entry.get().strip()
            }
            self.config.set("profile_proxies", profile_proxies)

        if choice == "Legacy" and os.path.exists(self.legacy_profile_dir):
            self.user_data_dir = self.legacy_profile_dir
        else:
            os.makedirs(os.path.join(self.profiles_dir, choice), exist_ok=True)
            self.user_data_dir = os.path.join(self.profiles_dir, choice)
        self.config.set("profile_name", choice)
        self.config.set("profiles_dir", os.path.relpath(self.profiles_dir, os.getcwd()))
        self.config.save()
        self.log(f"👤 تم تغيير الملف الشخصي إلى: {choice}")

        # Load new profile proxy settings
        if hasattr(self, "proxy_enabled_var"):
            self._load_profile_proxy_settings(choice)

    def _create_new_profile(self):
        dialog = ctk.CTkInputDialog(text="أدخل اسم الحساب الجديد:", title="حساب جديد")
        name = dialog.get_input()
        if name:
            safe_name = "".join([c for c in name if c.isalnum() or c in (' ', '_', '-')]).strip()
            if not safe_name:
                return
            new_path = os.path.join(self.profiles_dir, safe_name)
            if not os.path.exists(new_path):
                os.makedirs(new_path)
                self.profile_combo.configure(values=self._get_profiles())
                self.profile_var.set(safe_name)
                self._on_profile_change(safe_name)
                self.log(f"✨ تم إنشاء حساب جديد: {safe_name}")
            else:
                messagebox.showerror("خطأ", "هذا الاسم موجود بالفعل.")

    def _prepare_content(self):
        msg_template = self.message_textbox.get("1.0", "end").strip()
        # Get attachments from the new manager
        raw_attachments = self.attachment_manager.get_attachments()
        attachments = []

        for att in raw_attachments:
            path = att.get("path", "").strip()
            if not path:
                continue
            if not os.path.exists(path):
                self.report_error("ERR-09", f"الملف غير موجود: {path}", dialog=True)
                return None, None
            
            # Map to format expected by bot
            att_type = att.get("type", "document")
            ext = os.path.splitext(path)[1].lower()
            
            # Auto-correct type based on file extension to avoid sending images as documents (thumbnails)
            if att_type == "document":
                if ext in [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"]:
                    att_type = "image"
                elif ext in [".mp4", ".avi", ".mov", ".mkv", ".3gp"]:
                    att_type = "video"

            item = {
                "type": att_type,
                "path": path,
                "caption": att.get("caption", "").strip()
            }
            attachments.append(item)

        # Check if empty
        if not msg_template and not attachments:
            self.report_error("ERR-04", "يرجى كتابة نص الرسالة أو اختيار مرفق.", dialog=True, level="warning")
            return None, None

        return msg_template, attachments

    def _get_contacts_from_input(self):
        # Retrieve contacts directly from our progress_tree Treeview!
        children = self.progress_tree.get_children()
        if not children:
            contacts_input = self.contacts_entry.get().strip()
            if not contacts_input:
                self.report_error("ERR-05", "يرجى استيراد أو إدخال أرقام أولاً.", dialog=True)
                return None
            
            # Standard fallback (file or group loading)
            contacts = []
            if contacts_input.startswith("[GROUP:") and contacts_input.endswith("]"):
                group_name = contacts_input[7:-1]
                g = self.contacts_mgr.get_by_name(group_name)
                if not g or not g.get("contacts"):
                    self.report_error("ERR-03", f"المجموعة '{group_name}' فارغة أو غير موجودة.", dialog=True)
                    return None
                contacts = g["contacts"]
            elif os.path.exists(contacts_input):
                from utils.helpers import read_contacts_auto
                contacts = read_contacts_auto(contacts_input, default_country_code=self.config.get("default_country_code", "20"))
            
            if not contacts:
                self.report_error("ERR-05", "يرجى استيراد أرقام صحيحة أولاً.", dialog=True)
                return None
            
            # Load these fallback contacts into the Treeview
            self._refresh_numbers_table(contacts)
            children = self.progress_tree.get_children()

        contacts = []
        for item in children:
            vals = self.progress_tree.item(item, "values")
            if len(vals) >= 2:
                name = vals[0]
                phone = vals[1]
                var1 = vals[2] if len(vals) > 2 else ""
                contacts.append({
                    "name": name,
                    "phone": phone,
                    "var1": var1,
                    "tree_item_id": item # Storing item ID for live updates!
                })
        
        self.log(f"📋 تم جلب {len(contacts)} جهة اتصال جاهزة للإرسال.")
        return contacts

    def _log_preflight(self, contacts, msg_template, attachments):
        msg_len = len(msg_template) if msg_template else 0
        if attachments:
            types = ", ".join([a.get("type", "file") for a in attachments])
        else:
            types = "بدون مرفقات"
        self.log(f"🧪 فحص قبل الإرسال: جهات={len(contacts)} | رسالة={msg_len} حرف | مرفقات={types}")


    def _apply_template(self, text, contact):
        if not text:
            return ""
        out = str(text)
        mapping = {
            "name": contact.get("name", ""),
            "phone": contact.get("phone", ""),
            "var1": contact.get("var1", ""),
            "var2": contact.get("var2", ""),
            "var3": contact.get("var3", ""),
            "var4": contact.get("var4", ""),
            "var5": contact.get("var5", ""),
        }
        for k, v in mapping.items():
            out = out.replace("{" + k + "}", str(v) if v is not None else "")
        if self.spin_text_var.get():
            out = self._apply_spintax(out)
        return out

    def _apply_spintax(self, text):
        # Only replace braces that contain a '|', so {name} stays intact.
        pattern = re.compile(r"\{([^{}]*\|[^{}]*)\}")
        prev = None
        while prev != text:
            prev = text

            def _pick(match):
                opts = match.group(1).split("|")
                return random.choice(opts).strip()

            text = pattern.sub(_pick, text)
        return text

    def _test_spintax(self):
        text = self.message_textbox.get("1.0", "end").strip()
        if not text:
            messagebox.showwarning("تنبيه", "يرجى كتابة نص الرسالة أولاً لتجربة التدوير/المتغيرات.")
            return

        dummy_contact = {
            "name": "محمد أحمد",
            "phone": "966500000000",
            "var1": "منتج مميز",
            "var2": "100 ريال",
            "var3": "خصم 20%",
            "var4": "الرمز: AB12",
            "var5": "شحن مجاني",
        }

        # Apply variables and spintax
        v1 = self._apply_template(text, dummy_contact)
        v2 = self._apply_template(text, dummy_contact)

        info_text = "✨ معاينة حية للرسالة (باستخدام بيانات تجريبية):\n"
        info_text += "──────────────────────────\n"
        info_text += f"👤 الاسم: {dummy_contact['name']} | 📱 الهاتف: {dummy_contact['phone']}\n"
        if "{var1}" in text or "{var2}" in text or "{var3}" in text or "{var4}" in text or "{var5}" in text:
            info_text += f"🏷️ المتغيرات التجريبية: v1={dummy_contact['var1']}, v2={dummy_contact['var2']}\n"
        info_text += "──────────────────────────\n\n"

        if self.spin_text_var.get() and ("{" in text and "|" in text):
            info_text += "🔹 الاحتمال الأول:\n"
            info_text += f"« {v1} »\n\n"
            info_text += "🔹 الاحتمال الثاني (تدوير عشوائي):\n"
            info_text += f"« {v2} »\n"
        else:
            info_text += "📝 الرسالة المعاينة:\n"
            info_text += f"« {v1} »\n"

        messagebox.showinfo("معاينة الرسالة الحية", info_text)

    def _format_attachments_for_contact(self, attachments, contact):
        if not attachments:
            return []
        formatted = []
        for att in attachments:
            item = {"type": att.get("type", "document"), "path": att.get("path")}
            cap = att.get("caption")
            if cap:
                item["caption"] = self._apply_template(cap, contact)
            formatted.append(item)
        return formatted

    def _split_messages(self, text):
        if not text:
            return []
        parts = re.split(r"\n\s*---\s*\n", text)
        return [p.strip() for p in parts if p.strip()]

    def _filter_contacts_safe_mode(self, contacts):
        """Pre-validate numbers on WhatsApp before bulk send (Safe Mode)."""
        if not contacts or not self.bot:
            return contacts
        validated = []
        total = len(contacts)
        self.log(f"🛡️ الوضع الآمن: جاري فحص {total} رقم على واتساب...")
        for i, c in enumerate(contacts):
            if self.stop_event.is_set():
                break
            phone = c.get("phone")
            if not phone:
                continue
            res = self.bot.check_number(phone, stop_event=self.stop_event)
            if res == "VALID":
                validated.append(c)
            elif res == "INVALID":
                self.log(f"🚫 تم استبعاد {phone} (بدون واتساب)")
            elif res == "STOPPED":
                break
            else:
                self.log(f"⚠️ تعذر التحقق من {phone} ({res}) — سيتم تخطيه")
        self.log(f"🛡️ الوضع الآمن: {len(validated)}/{total} رقم صالح للإرسال.")
        return validated

    def _check_campaign_safety(self, contact_count, attachments):
        """Warn or auto-fix delays when campaign settings are too aggressive."""
        from utils.safety import assess_campaign_settings

        try:
            delay_min = int(self.delay_min_entry.get())
            delay_max = int(self.delay_max_entry.get())
            batch_size = int(self.batch_size_entry.get())
            pause_min = int(self.batch_min_entry.get())
        except ValueError:
            return True

        has_media = bool(attachments)
        report = assess_campaign_settings(
            contact_count, delay_min, delay_max, batch_size, pause_min, has_media
        )
        if not report.get("warnings"):
            return True

        body = "\n".join(f"• {w}" for w in report["warnings"])
        body += (
            f"\n\nمقترح: تأخير {int(report['suggested_delay_min'])}–"
            f"{int(report['suggested_delay_max'])} ثانية بين الرسائل."
        )
        body += "\n\nنعم = تطبيق الإعدادات المقترحة والمتابعة\nلا = المتابعة كما هي\nإلغاء = إيقاف"

        choice = messagebox.askyesnocancel("تحذير — تقليل مخاطر الحظر", body)
        if choice is None:
            return False
        if choice:
            self.delay_min_entry.delete(0, "end")
            self.delay_min_entry.insert(0, str(int(report["suggested_delay_min"])))
            self.delay_max_entry.delete(0, "end")
            self.delay_max_entry.insert(0, str(int(report["suggested_delay_max"])))
            if pause_min < 60:
                self.batch_min_entry.delete(0, "end")
                self.batch_min_entry.insert(0, "60")
            self.config.set("delay_min", int(report["suggested_delay_min"]))
            self.config.set("delay_max", int(report["suggested_delay_max"]))
            self.config.save()
            self.log("✅ تم تطبيق إعدادات تأخير أكثر أماناً للحملة.")
        return True

    def _begin_send(self, contacts, msg_template, attachments):
        self._agent_debug_log(
            "H4",
            "modern_ui.py:_begin_send",
            "begin_send_called",
            {"contact_count": len(contacts) if contacts else 0, "is_running": bool(self.is_running)},
        )
        if self.is_running:
            return

        if getattr(self, "sending_mode", None) == "safe":
            contacts = self._filter_contacts_safe_mode(contacts)
            if not contacts:
                self.report_error("ERR-05", "لا توجد أرقام صالحة للإرسال بعد الفحص.", dialog=True)
                return

        # 4. Apply background mode
        if self.bg_mode_var.get():
            self.bot.background_mode = True
            self.bot.minimize()
            self.log("🖥️ وضع الخلفية مفعّل — المتصفح مُصغّر.")
        else:
            self.bot.background_mode = False
            self.bot.bring_to_front()

        # 5. Start Thread
        self.is_running = True
        self._switch_tab("log")
        self.log("📋 سجل التشخيص — كل خطوات البوت تظهر هنا وفي التيرمنال.", level="INFO")
        self.stop_event.clear()
        self.pause_event.clear()
        self.is_paused = False

        self._log_preflight(contacts, msg_template, attachments)

        self.btn_start.configure(state="disabled")
        self.btn_stop.configure(state="normal")
        if hasattr(self, "btn_check"):
            self.btn_check.configure(state="disabled")
        self.progress_bar.set(0)
        self.status_label.configure(text="جاري العمل...")
        if getattr(self, "pause_btn", None) and self.pause_btn.winfo_exists():
            self.pause_btn.configure(text="Pause")

        self._open_progress_window_blind(len(contacts), mode="send")

        threading.Thread(
            target=self._run_automation,
            args=(contacts, msg_template, attachments),
            daemon=True
        ).start()


    def _start_action(self):
        """Show Sending Mode dialog, then proceed with the campaign."""
        self._show_sending_mode_dialog()

    def _show_sending_mode_dialog(self):
        """Professional sending-mode picker matching competitor apps."""
        import tkinter as tk

        dialog = ctk.CTkToplevel(self)
        dialog.title("Sending Mode | وضع الإرسال")
        dialog.geometry("520x360")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()

        # Centre on parent
        x = self.winfo_x() + (self.winfo_width() - 520) // 2
        y = self.winfo_y() + (self.winfo_height() - 360) // 2
        dialog.geometry(f"+{x}+{y}")

        frm = ctk.CTkFrame(dialog, fg_color="transparent")
        frm.pack(fill="both", expand=True, padx=25, pady=20)

        # Title
        title = ctk.CTkLabel(frm, text="اختر وضع الإرسال | Select your sending mode",
                             font=("Segoe UI", 16, "bold"))
        title.pack(anchor="w", pady=(0, 20))

        mode_var = tk.StringVar(value="safe")

        # ── Safe Mode Card ──
        safe_card = ctk.CTkFrame(frm, fg_color=COLORS.get("card_bg", "#1E293B"), corner_radius=10, border_width=2, border_color=COLORS.get("primary", "#00E676"))
        safe_card.pack(fill="x", pady=(0, 12))

        safe_top = ctk.CTkFrame(safe_card, fg_color="transparent")
        safe_top.pack(fill="x", padx=15, pady=(12, 4))

        safe_radio = ctk.CTkRadioButton(safe_top, text="الوضع الآمن | Safe Mode",
                                        font=("Segoe UI", 14, "bold"),
                                        variable=mode_var, value="safe")
        safe_radio.pack(side="left")

        safe_badge = ctk.CTkLabel(safe_top, text=" خطر الحظر منخفض ",
                                  font=("Segoe UI", 11, "bold"),
                                  fg_color="#16A34A", corner_radius=6,
                                  text_color="#FFFFFF")
        safe_badge.pack(side="right")

        safe_desc = ctk.CTkLabel(safe_card,
                                 text="يُفحص كل رقم على واتساب قبل الإرسال (أرقام غير مسجلة تُستبعد).\nاستخدم تأخيراً 30–120 ثانية مع الوسائط — لا يمكن ضمان عدم الحظر (سياسة واتساب).",
                                 font=("Segoe UI", 11),
                                 text_color=COLORS.get("text_muted", "#94A3B8"),
                                 justify="right", anchor="e")
        safe_desc.pack(fill="x", padx=15, pady=(0, 12))

        # ── Blind Mode Card ──
        blind_card = ctk.CTkFrame(frm, fg_color=COLORS.get("card_bg", "#1E293B"), corner_radius=10, border_width=2, border_color=COLORS.get("border", "#334155"))
        blind_card.pack(fill="x", pady=(0, 12))

        blind_top = ctk.CTkFrame(blind_card, fg_color="transparent")
        blind_top.pack(fill="x", padx=15, pady=(12, 4))

        blind_radio = ctk.CTkRadioButton(blind_top, text="الوضع العشوائي | Blind Mode",
                                         font=("Segoe UI", 14, "bold"),
                                         variable=mode_var, value="blind")
        blind_radio.pack(side="left")

        blind_badge = ctk.CTkLabel(blind_top, text=" خطر الحظر مرتفع ",
                                   font=("Segoe UI", 11, "bold"),
                                   fg_color="#DC2626", corner_radius=6,
                                   text_color="#FFFFFF")
        blind_badge.pack(side="right")

        blind_desc = ctk.CTkLabel(blind_card,
                                  text="يرسل إلى جميع الأرقام المستوردة بغض النظر عن صلاحيتها.\nلن يتم فحص الأرقام مسبقاً — سرعة أعلى لكن خطر الحظر مرتفع.",
                                  font=("Segoe UI", 11),
                                  text_color=COLORS.get("text_muted", "#94A3B8"),
                                  justify="right", anchor="e")
        blind_desc.pack(fill="x", padx=15, pady=(0, 12))

        # ── Buttons ──
        btn_frame = ctk.CTkFrame(frm, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(10, 0))

        btn_cancel = ctk.CTkButton(btn_frame, text="إلغاء | Cancel",
                                   font=("Segoe UI", 13, "bold"), width=130, height=38,
                                   fg_color=COLORS.get("danger", "#EF4444"),
                                   hover_color=COLORS.get("danger_hover", "#DC2626"),
                                   text_color="#FFFFFF",
                                   command=dialog.destroy)
        btn_cancel.pack(side="left", padx=(0, 10))

        def on_ok():
            chosen = mode_var.get()
            dialog.destroy()
            self._proceed_start_action(sending_mode=chosen)

        btn_ok = ctk.CTkButton(btn_frame, text="موافق | OK",
                               font=("Segoe UI", 13, "bold"), width=130, height=38,
                               fg_color=COLORS.get("primary", "#00E676"),
                               hover_color=COLORS.get("primary_hover", "#00C853"),
                               text_color="#000000",
                               command=on_ok)
        btn_ok.pack(side="right")

    def _proceed_start_action(self, sending_mode="safe"):
        """Actually start the campaign after the user picked a mode."""
        self.sending_mode = sending_mode
        if sending_mode == "safe":
            self.log("🛡️ تم اختيار الوضع الآمن (Safe Mode) — سيتم فحص الأرقام قبل الإرسال.")
        else:
            self.log("⚡ تم اختيار الوضع العشوائي (Blind Mode) — سيتم الإرسال لجميع الأرقام بدون فحص.")

        msg_template, attachments = self._prepare_content()
        if msg_template is None and attachments is None:
            return  # Error reported

        contacts = self._get_contacts_from_input()
        if not contacts:
            return
        if not self._check_campaign_safety(len(contacts), attachments):
            return
        if not self._warn_media_send_settings(attachments):
            return

        self._save_current_state()
        
        # 3. Check Bot & Login
        if not self.bot or not self.bot.driver:
            auto_open = self.config.get("auto_open_login", True)
            if auto_open or messagebox.askyesno("تنبيه", "المتصفح غير مفتوح. هل تريد فتحه الآن؟"):
                self.pending_start_payload = (contacts, msg_template, attachments)
                self._set_session_status("الحالة: جاري فتح المتصفح...", COLORS["info"])
                self._login_action()
            return

        if not self.bot.is_logged_in():
            self.bot.bring_to_front()
            self.report_error("ERR-21", dialog=True, level="warning")
            return

        self._set_session_status("الحالة: متصل", COLORS["success"])
        self._begin_send(contacts, msg_template, attachments)

    def _check_numbers_action(self, contacts_override=None):
        if self.is_running or self.is_checking:
            return
        contacts = contacts_override or self._get_contacts_from_input()
        if not contacts:
            return

        if not self.bot or not self.bot.driver:
            auto_open = self.config.get("auto_open_login", True)
            if auto_open or messagebox.askyesno("تنبيه", "المتصفح غير مفتوح. هل تريد فتحه الآن؟"):
                self.pending_check_contacts = contacts
                self._set_session_status("الحالة: جاري فتح المتصفح...", COLORS["info"])
                self._login_action()
            return

        if not self.bot.is_logged_in():
            self.bot.bring_to_front()
            self.report_error("ERR-21", dialog=True, level="warning")
            return

        self._set_session_status("الحالة: متصل", COLORS["success"])
        self.is_checking = True
        self.stop_event.clear()
        self.btn_start.configure(state="disabled")
        self.btn_check.configure(state="disabled")
        self.btn_stop.configure(state="normal")
        self.progress_bar.set(0)
        self._open_progress_window_blind(len(contacts), mode="check")
        self.status_label.configure(text="جاري فحص الأرقام...")

        threading.Thread(
            target=self._run_number_check,
            args=(contacts,),
            daemon=True
        ).start()

    def _stop_action(self):
        if messagebox.askyesno("تأكيد", "هل تريد إيقاف العملية؟"):
            self.stop_event.set()
            if self.pause_event.is_set():
                self.pause_event.clear()
                self.is_paused = False
                if getattr(self, "pause_btn", None) and self.pause_btn.winfo_exists():
                    self.pause_btn.configure(text="Pause")
            self.log("🛑 طلب إيقاف...")

    def _warn_media_send_settings(self, attachments):
        """Advise user before campaigns with media attachments."""
        if not attachments:
            return True
        if getattr(self, "send_text_var", None) and self.send_text_var.get():
            self.send_text_var.set(False)
            self.log(
                "ℹ️ تم إلغاء «الوضع المدمج» تلقائياً — سيتم إرسال الصورة ثم النص منفصلين (أكثر استقراراً).",
                level="INFO",
            )
        if getattr(self, "bg_mode_var", None) and self.bg_mode_var.get():
            messagebox.showwarning(
                "وضع الخلفية",
                "مع المرفقات (صور/فيديو) يُفضّل إيقاف «وضع الخلفية» "
                "وإبقاء نافذة واتساب ظاهرة لتقليل فشل الإرفاق والنقر.",
            )
        return True

    def _recover_bot_before_retry(self, attachments):
        if not self.bot:
            return
        try:
            if attachments and hasattr(self.bot, "recover_compose_state"):
                self.bot.recover_compose_state(stop_event=self.stop_event)
            if attachments and not self.bg_mode_var.get():
                self.bot.bring_to_front()
        except Exception:
            pass

    def _map_bot_error(self, res):
        if not res:
            return "ERR-99", "خطأ غير معروف.", None
        if str(res).startswith("ERR_TEXT_SEND"):
            detail = res.split(":", 1)[1].strip() if ":" in res else ""
            tip = (
                "تأكد من إغلاق معاينة الصورة/قائمة الإرفاق، وإبقاء نافذة واتساب ظاهرة "
                "(لا تستخدم وضع الخلفية مع الوسائط)."
            )
            return "ERR-07", "فشل إرسال النص بعد المرفق.", f"{detail} — {tip}" if detail else tip
        if res.startswith("ERR_IMAGE_FLOW:"):
            detail = res.split(":", 1)[1].strip()
            return "ERR-08", "فشل إرسال الصورة.", detail
        if res.startswith("ERR_ATTACH_"):
            parts = res.split(":", 1)
            atype = parts[0].replace("ERR_ATTACH_", "")
            detail = parts[1].strip() if len(parts) > 1 else ""
            return "ERR-08", f"فشل إرفاق ملف ({atype}).", detail
        if res.startswith("ERR_GENERAL:"):
            detail = res.split(":", 1)[1].strip()
            if "timeout" in detail.lower():
                return "ERR-10", "انتهت مهلة تحميل المحادثة.", detail
            return "ERR-99", "خطأ غير متوقع أثناء المعالجة.", detail
        mapping = {
            "ERR_NOT_READY":               ("ERR-01", "المتصفح غير جاهز.", None),
            "ERR_EMPTY_MESSAGE":           ("ERR-04", "لا يوجد نص للإرسال.", None),
            "ERR_CHAT_INPUT_NOT_FOUND":    ("ERR-07", "صندوق كتابة الرسالة غير موجود.", None),
            "ERR_ATTACH_BTN_NOT_FOUND":    (
                "ERR-06",
                "زر الإرفاق (+) غير ظاهر في التذييل.",
                "انتظر تحميل المحادثة، أغلق البحث/المعاينة، وأبقِ نافذة واتساب مفتوحة.",
            ),
            "ERR_FILE_INPUT_NOT_FOUND":    ("ERR-08", "حقل رفع الصورة غير موجود.", None),
            "ERR_CAPTION_BOX_NOT_FOUND":   ("ERR-08", "صندوق كتابة الكابشن غير موجود.", None),
            "ERR_FINAL_SEND_BTN_NOT_FOUND":("ERR-07", "زر الإرسال النهائي لم يظهر.", None),
            "ERR_SEND_BTN_TIMEOUT":        ("ERR-07", "زر الإرسال لم يظهر في الوقت المحدد.", None),
            "ERR_TIMEOUT":                 ("ERR-10", "انتهت مهلة تحميل المحادثة.", None),
        }
        return mapping.get(res, ("ERR-99", f"خطأ غير معروف ({res})", None))

    # ═══════════════════════════════════════════════════════════════════════
    #  MAIN AUTOMATION LOOP
    # ═══════════════════════════════════════════════════════════════════════

    def _run_automation(self, contacts, msg_template, attachments):
        if not self.bot:
            return

        self.sent = 0
        self.failed = 0
        self.invalid = 0
        self.results_log = []
        
        total = len(contacts)
        start_time = datetime.datetime.now()

        try:
            # Batch settings
            try:
                batch_size = int(self.batch_size_entry.get())
                pause_min = int(self.batch_min_entry.get())
                pause_max = int(self.batch_max_entry.get())
                delay_min = int(self.delay_min_entry.get())
                delay_max = int(self.delay_max_entry.get())
                max_retries = int(self.config.get("max_retries", 2))
                retry_delay_min = int(self.config.get("retry_delay_min", 3))
                retry_delay_max = int(self.config.get("retry_delay_max", 6))
                max_consecutive_failures = int(self.config.get("max_consecutive_failures", 5))
            except ValueError:
                batch_size, pause_min, pause_max, delay_min, delay_max = 30, 60, 120, 30, 120
                max_retries, retry_delay_min, retry_delay_max, max_consecutive_failures = 1, 3, 6, 5

            self.log(f"🚀 بدء إرسال {total} رسالة...")
            consecutive_failures = 0
            retryable_errors = {
                "ERR_TIMEOUT",
                "ERR_CHAT_INPUT_NOT_FOUND",
                "ERR_ATTACH_BTN_NOT_FOUND",
                "ERR_FILE_INPUT_NOT_FOUND",
                "ERR_STICKER_PANEL_OPENED",
                "ERR_SEND_BTN_NOT_FOUND",
                "ERR_SEND_BTN_TIMEOUT",
                "ERR_TEXT_SEND",
            }
            attach_only_errors = {
                "ERR_FILE_INPUT_NOT_FOUND",
                "ERR_STICKER_PANEL_OPENED",
                "ERR_DOC_BTN_NOT_FOUND",
                "ERR_PHOTO_BTN_NOT_FOUND",
            }
            retry_full_navigation = bool(self.config.get("retry_full_navigation", False))

            for i, c in enumerate(contacts):
                if self.stop_event.is_set():
                    break
                while self.pause_event.is_set() and not self.stop_event.is_set():
                    self.stop_event.wait(0.3)

                # Batch pause (interruptible)
                if i > 0 and i % batch_size == 0:
                    pause_time = random.uniform(pause_min, pause_max)
                    self.log(f"⏸ استراحة لمدة {int(pause_time)} ثانية...")
                    if self.stop_event.wait(pause_time):
                        break

                # Account Rotation Logic
                rotation_enabled = self.config.get("rotation_enabled", False)
                try:
                    rotation_interval = int(self.config.get("rotation_interval", 50))
                except ValueError:
                    rotation_interval = 50

                if rotation_enabled and i > 0 and i % rotation_interval == 0:
                    self.log("🔄 التبديل التلقائي للحساب التالي (تدوير الحسابات)...")
                    profiles = self._get_profiles()
                    current_profile = self.config.get("profile_name", "Default")
                    if profiles and len(profiles) > 1:
                        try:
                            curr_idx = profiles.index(current_profile)
                            next_idx = (curr_idx + 1) % len(profiles)
                        except ValueError:
                            next_idx = 0
                        next_profile = profiles[next_idx]
                        self.log(f"🔄 التبديل من حساب {current_profile} إلى {next_profile}...")
                        self._run_on_ui(lambda p=next_profile: self._on_profile_change(p))
                        
                        try:
                            if self.bot:
                                self.bot.close()
                        except Exception:
                            pass
                        
                        # Wait a bit before opening the new one
                        if self.stop_event.wait(2.0):
                            break

                        # We need to wait for _on_profile_change to actually execute on UI thread
                        if self.stop_event.wait(1.0):
                            break

                        # Start new bot
                        proxy_config = self.config.get("profile_proxies", {}).get(next_profile)
                        from automation.whatsapp_bot import WhatsAppBot
                        self.bot = WhatsAppBot(
                            self.user_data_dir,
                            proxy_config,
                            on_event=self._on_bot_event,
                        )
                        self.bot.setup_driver(start_minimized=self.bg_mode_var.get())
                        self.bot.open_whatsapp()
                        self.log("⏳ انتظار تسجيل الدخول للحساب الجديد...")
                        if not self.bot.wait_for_login():
                            self.log("❌ فشل تسجيل الدخول للحساب الجديد. سيتم إيقاف الإرسال.")
                            self.stop_event.set()
                            break
                        self.log("✅ تم الدخول بنجاح. استئناف الإرسال...")
                    else:
                        self.log("⚠️ إعداد التدوير مفعل، لكن لا يوجد حسابات أخرى محفوظة للتبديل إليها.")

                phone = c.get("phone")
                name = c.get("name", "عميل")
                
                processed = i + 1
                self._run_on_ui(lambda p=processed, t=total, n=name: self.status_label.configure(text=f"جاري إرسال {p}/{t} إلى {n}..."))
                self._run_on_ui(lambda p=processed, t=total: self.progress_bar.set(p / t))
                elapsed = (datetime.datetime.now() - start_time).total_seconds()
                eta = None
                if processed > 0 and total > processed:
                    eta = (elapsed / processed) * (total - processed)
                self._update_progress_header_blind(processed, total, phone, name, eta)

                # Mark row as sending in the Treeview table live!
                tree_item_id = c.get("tree_item_id")
                if tree_item_id:
                    self._run_on_ui(lambda item=tree_item_id, n=name, ph=phone, v=c.get("var1", ""): self.progress_tree.item(item, values=(n, ph, v, "🔄 إرسال..."), tags=("sending",)))

                if not phone:
                    self.invalid += 1
                    self.results_log.append({"phone": "N/A", "name": name, "status": "INVALID", "error_code": "ERR-00", "timestamp": datetime.datetime.now()})
                    self._add_progress_row_blind(["N/A", name, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "بدون رقم", "بيانات الرقم ناقصة"], tag="invalid")
                    self._run_on_ui(self._update_stats)
                    self._update_progress_header_blind(processed, total, phone, name, eta)
                    if tree_item_id:
                        self._run_on_ui(lambda item=tree_item_id, n=name, v=c.get("var1", ""): self.progress_tree.item(item, values=(n, "N/A", v, "🚫 بدون رقم"), tags=("invalid",)))
                    continue

                # Ensure still logged in
                if not self.bot.is_logged_in():
                    self.report_error("ERR-21", dialog=True, level="warning")
                    if tree_item_id:
                        self._run_on_ui(lambda item=tree_item_id, n=name, ph=phone, v=c.get("var1", ""): self.progress_tree.item(item, values=(n, ph, v, "⏳ معلق"), tags=("pending",)))
                    break

                # Prepare personalized content
                msg_for_contact = self._apply_template(msg_template, c)
                atts_for_contact = self._format_attachments_for_contact(attachments, c)
                segments = self._split_messages(msg_for_contact)
                primary_msg = segments[0] if segments else msg_for_contact
                extra_msgs = segments[1:] if segments else []

                # Send Message + Attachments with retries
                res = None
                for attempt in range(max_retries + 1):
                    skip_nav = (
                        attempt > 0
                        and atts_for_contact
                        and not retry_full_navigation
                        and res in attach_only_errors
                    )
                    res = self.bot.send_message(
                        phone=phone,
                        name=name,
                        message_template=primary_msg,
                        extra_messages=extra_msgs,
                        attachments=atts_for_contact,
                        stop_event=self.stop_event,
                        send_text_with_image=self.send_text_var.get(),
                        skip_open_chat=skip_nav,
                    )
                    if res in ("SUCCESS", "INVALID", "STOPPED"):
                        break
                    is_retryable = (
                        res in retryable_errors
                        or str(res).startswith("ERR_ATTACH_")
                        or str(res).startswith("ERR_TEXT_SEND")
                        or str(res).startswith("ERR_GENERAL")
                    )
                    if attempt < max_retries and is_retryable:
                        wait_s = random.uniform(retry_delay_min, retry_delay_max)
                        retry_mode = "مرفق فقط" if skip_nav else "كامل"
                        self.log(f"🔁 إعادة محاولة ({attempt + 1}/{max_retries}) [{retry_mode}] بعد {int(wait_s)}ث | {phone} | {res}")
                        self._recover_bot_before_retry(atts_for_contact)
                        if self.stop_event.wait(wait_s):
                            break
                        continue
                    break
                
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                if res == "SUCCESS":
                    self.sent += 1
                    self.log(f"✅ تم الإرسال لـ {name}")
                    self.results_log.append({"phone": phone, "name": name, "status": "نجاح", "error_code": "-", "timestamp": timestamp})
                    self._add_progress_row_blind([phone, name, timestamp, "تم", "تم الإرسال"], tag="success")
                    consecutive_failures = 0
                    if tree_item_id:
                        self._run_on_ui(lambda item=tree_item_id, n=name, ph=phone, v=c.get("var1", ""): self.progress_tree.item(item, values=(n, ph, v, "✅ نجاح"), tags=("success",)))
                elif res == "INVALID":
                    self.invalid += 1
                    self.log(f"⏭️ تخطي {phone} — الرقم غير مسجل على واتساب (تم إغلاق النافذة تلقائياً).")
                    self.results_log.append({"phone": phone, "name": name, "status": "بدون واتساب", "error_code": "ERR-20", "timestamp": timestamp})
                    self._add_progress_row_blind([phone, name, timestamp, "بدون واتساب", "غير موجود على واتساب — تم التخطي"], tag="invalid")
                    consecutive_failures = 0
                    if tree_item_id:
                        self._run_on_ui(lambda item=tree_item_id, n=name, ph=phone, v=c.get("var1", ""): self.progress_tree.item(item, values=(n, ph, v, "🚫 غير صالح"), tags=("invalid",)))
                elif res == "STOPPED":
                    self.results_log.append({"phone": phone, "name": name, "status": "توقف", "error_code": "-", "timestamp": timestamp})
                    self._add_progress_row_blind([phone, name, timestamp, "توقف", "تم إيقاف العملية"], tag="stopped")
                    if tree_item_id:
                        self._run_on_ui(lambda item=tree_item_id, n=name, ph=phone, v=c.get("var1", ""): self.progress_tree.item(item, values=(n, ph, v, "⚠️ توقف"), tags=("pending",)))
                    break
                else:
                    self.failed += 1
                    err_code = res if res.startswith("ERR") else "ERR-UNKNOWN"
                    self.log(f"❌ فشل: {phone} | {res}")
                    self.results_log.append({"phone": phone, "name": name, "status": "فشل", "error_code": err_code, "timestamp": timestamp})
                    self._add_progress_row_blind([phone, name, timestamp, "فشل", str(res)], tag="failed")
                    consecutive_failures += 1
                    if tree_item_id:
                        self._run_on_ui(lambda item=tree_item_id, n=name, ph=phone, v=c.get("var1", ""): self.progress_tree.item(item, values=(n, ph, v, "❌ فشل"), tags=("failed",)))
                    if consecutive_failures >= max_consecutive_failures:
                        self.log(f"⛔ تم الإيقاف تلقائياً بعد {consecutive_failures} فشل متتالي لتقليل المخاطر.")
                        self.stop_event.set()
                        break

                self._run_on_ui(self._update_stats)
                self._update_progress_header_blind(processed, total, phone, name, eta)
                
                # Delay (interruptible)
                # Human-like delay: mostly fast, occasionally slower to avoid detection
                d_fast = random.uniform(delay_min * 0.3, delay_min * 0.7)
                d_mid = random.uniform(delay_min * 0.7, (delay_min + delay_max) / 2)
                d_slow = random.uniform((delay_min + delay_max) / 2, delay_max)
                chosen_delay = random.choices([d_fast, d_mid, d_slow], weights=[70, 20, 10], k=1)[0]
                if self.stop_event.wait(chosen_delay):
                    break

            end_time = datetime.datetime.now()
            duration = end_time - start_time
            
            # Save Campaign
            csv_path = self._generate_final_report(duration)
            self.last_report_path = csv_path
            
            # Determine status
            c_status = "Completed" if not self.stop_event.is_set() else "Stopped"
            
            # Save to history
            self.campaign_manager.add_campaign(
                name=f"Campaign {start_time.strftime('%Y-%m-%d %H:%M')}",
                total=total,
                sent=self.sent,
                failed=self.failed,
                invalid=self.invalid,
                duration_seconds=int(duration.total_seconds()),
                results_log=self.results_log,
                csv_path=csv_path
            )
            try:
                if self.bg_mode_var.get():
                    self.bot.minimize()
                else:
                    self.bot.bring_to_front()
            except Exception:
                pass

            if self.stop_event.is_set():
                self.log("🛑 تم إيقاف العملية.")
            else:
                self.log("🏁 انتهت العملية.")
                self._run_on_ui(lambda: self.progress_bar.set(1.0))

        except Exception as e:
            self.log(f"⚠️ [ERR-99] خطأ غير متوقع في خيط الإرسال: {e}")
        finally:
            self.is_running = False
            self.pause_event.clear()
            self.is_paused = False
            self._run_on_ui(lambda: self.btn_start.configure(state="normal"))
            self._run_on_ui(lambda: self.btn_stop.configure(state="disabled"))
            if hasattr(self, "btn_check"):
                self._run_on_ui(lambda: self.btn_check.configure(state="normal"))
            if getattr(self, "pause_btn", None):
                self._run_on_ui(lambda: self.pause_btn.configure(text="Pause") if getattr(self, "pause_btn", None) and self.pause_btn.winfo_exists() else None)
            self._run_on_ui(lambda: self.status_label.configure(text="جاهز..."))

    def _run_number_check(self, contacts):
        if not self.bot:
            return
        self.sent = 0
        self.failed = 0
        self.invalid = 0
        self.results_log = []

        total = len(contacts)
        start_time = datetime.datetime.now()

        try:
            self.log(f"🔍 بدء فحص {total} رقم...")

            for i, c in enumerate(contacts):
                if self.stop_event.is_set():
                    break
                phone = c.get("phone")
                name = c.get("name", "عميل")

                processed = i + 1
                self._run_on_ui(lambda p=processed, t=total, n=name: self.status_label.configure(text=f"فحص {p}/{t} - {n}"))
                self._run_on_ui(lambda p=processed, t=total: self.progress_bar.set(p / t))
                elapsed = (datetime.datetime.now() - start_time).total_seconds()
                eta = None
                if processed > 0 and total > processed:
                    eta = (elapsed / processed) * (total - processed)
                self._update_progress_header_blind(processed, total, phone, name, eta)

                if not phone:
                    self.invalid += 1
                    self.results_log.append({"phone": "N/A", "name": name, "status": "غير صالح", "error_code": "ERR-00", "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
                    self._add_progress_row_blind(["N/A", name, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "بدون رقم", "بيانات الرقم ناقصة"], tag="invalid")
                    self._run_on_ui(self._update_stats)
                    self._update_progress_header_blind(processed, total, phone, name, eta)
                    continue

                res = self.bot.check_number(phone=phone, stop_event=self.stop_event)
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                if res == "VALID":
                    self.sent += 1
                    self.log(f"✅ صالح: {phone} | {name}")
                    self.results_log.append({"phone": phone, "name": name, "status": "صالح", "error_code": "-", "timestamp": timestamp})
                    self._add_progress_row_blind([phone, name, timestamp, "عنده واتساب", "صالح للإرسال"], tag="success")
                elif res == "INVALID":
                    self.invalid += 1
                    self.log(f"🚫 غير صالح: {phone}")
                    self.results_log.append({"phone": phone, "name": name, "status": "غير صالح", "error_code": "ERR-20", "timestamp": timestamp})
                    self._add_progress_row_blind([phone, name, timestamp, "بدون واتساب", "الرقم غير صالح أو لا يستخدم واتساب"], tag="invalid")
                elif res == "STOPPED":
                    self.results_log.append({"phone": phone, "name": name, "status": "توقف", "error_code": "-", "timestamp": timestamp})
                    self._add_progress_row_blind([phone, name, timestamp, "توقف", "تم إيقاف الفحص"], tag="stopped")
                    break
                else:
                    self.failed += 1
                    self.log(f"⚠️ تعذر الفحص: {phone} | {res}")
                    self.results_log.append({"phone": phone, "name": name, "status": "فشل", "error_code": res, "timestamp": timestamp})
                    self._add_progress_row_blind([phone, name, timestamp, "فشل", str(res)], tag="failed")

                self._run_on_ui(self._update_stats)
                self._update_progress_header_blind(processed, total, phone, name, eta)
                if self.stop_event.wait(random.uniform(1.5, 3.0)):
                    break

            report_path, valid_path, invalid_path = self._save_number_check_report()
            if self.stop_event.is_set():
                self.log("🛑 تم إيقاف الفحص.")
            else:
                self.log("🏁 انتهى فحص الأرقام.")
                if report_path:
                    self.log(f"📄 تقرير الفحص: {report_path}")
                if valid_path:
                    self.log(f"✅ ملف الأرقام الصالحة: {valid_path}")
                if invalid_path:
                    self.log(f"🚫 ملف الأرقام غير الصالحة: {invalid_path}")
                if valid_path and hasattr(self, "use_valid_after_check_var") and self.use_valid_after_check_var.get():
                    self.contacts_entry.delete(0, "end")
                    self.contacts_entry.insert(0, valid_path)
                    self._update_total_counts(total=self.sent, contacts_count=self.sent, groups_count=0)
                    self.log("✨ تم تعيين ملف الأرقام الصالحة كملف الإرسال الحالي.")

        except Exception as e:
            self.log(f"⚠️ [ERR-99] خطأ غير متوقع في خيط فحص الأرقام: {e}")
        finally:
            self.is_checking = False
            self.stop_event.clear()
            self._run_on_ui(lambda: self.btn_start.configure(state="normal"))
            self._run_on_ui(lambda: self.btn_check.configure(state="normal"))
            self._run_on_ui(lambda: self.btn_stop.configure(state="disabled"))
            self._run_on_ui(lambda: self.status_label.configure(text="جاهز..."))

    def _save_number_check_report(self):
        if not self.results_log:
            return None, None, None
        try:
            reports_dir = os.path.join(os.getcwd(), "reports", "number_checks")
            os.makedirs(reports_dir, exist_ok=True)
            filename = f"number_check_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            filepath = os.path.join(reports_dir, filename)

            with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.DictWriter(f, fieldnames=["phone", "name", "status", "error_code", "timestamp"])
                writer.writeheader()
                writer.writerows(self.results_log)
            valid_rows = [r for r in self.results_log if str(r.get("status", "")).strip() in ("صالح", "VALID")]
            invalid_rows = [r for r in self.results_log if str(r.get("status", "")).strip() in ("غير صالح", "INVALID")]

            valid_path = None
            invalid_path = None
            if valid_rows:
                valid_name = f"valid_numbers_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                valid_path = os.path.join(reports_dir, valid_name)
                with open(valid_path, 'w', newline='', encoding='utf-8-sig') as f:
                    writer = csv.DictWriter(f, fieldnames=["phone", "name"])
                    writer.writeheader()
                    for r in valid_rows:
                        writer.writerow({"phone": r.get("phone"), "name": r.get("name")})

            if invalid_rows:
                invalid_name = f"invalid_numbers_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                invalid_path = os.path.join(reports_dir, invalid_name)
                with open(invalid_path, 'w', newline='', encoding='utf-8-sig') as f:
                    writer = csv.DictWriter(f, fieldnames=["phone", "name", "error_code"])
                    writer.writeheader()
                    for r in invalid_rows:
                        writer.writerow({"phone": r.get("phone"), "name": r.get("name"), "error_code": r.get("error_code")})

            return filepath, valid_path, invalid_path
        except Exception:
            return None, None, None

    # ═══════════════════════════════════════════════════════════════════════
    #  REPORT
    # ═══════════════════════════════════════════════════════════════════════
    def _generate_final_report(self, duration):
        total = self.sent + self.failed + self.invalid
        if total == 0:
            return None

        pct_ok = (self.sent / total * 100)
        pct_fail = (self.failed / total * 100)
        pct_inv = (self.invalid / total * 100)

        mins, secs = divmod(int(duration.total_seconds()), 60)
        hrs, mins = divmod(mins, 60)
        if hrs:
            dur_text = f"{hrs} ساعة {mins} دقيقة {secs} ثانية"
        elif mins:
            dur_text = f"{mins} دقيقة {secs} ثانية"
        else:
            dur_text = f"{secs} ثانية"

        csv_path = self._save_report_csv()
        csv_note = f"\n\n📄 تم حفظ التقرير:\n{csv_path}" if csv_path else ""

        summary = (
            f"📊 تقرير الإرسال النهائي\n"
            f"{'─' * 35}\n"
            f"📋 الإجمالي: {total}\n"
            f"✅ نجاح: {self.sent} ({pct_ok:.1f}%)\n"
            f"❌ فشل: {self.failed} ({pct_fail:.1f}%)\n"
            f"🚫 بدون واتساب: {self.invalid} ({pct_inv:.1f}%)\n"
            f"⏱ المدة: {dur_text}"
            f"{csv_note}"
        )

        self.log(f"\n📊 التقرير النهائي: ✅{self.sent} | ❌{self.failed} | 🚫{self.invalid} | ⏱{dur_text}")
        self._show_dialog("info", "تقرير الإرسال", summary)
        return csv_path

    def _save_report_csv(self):
        if not self.results_log:
            return None
        try:
            reports_dir = os.path.join(os.getcwd(), "reports")
            os.makedirs(reports_dir, exist_ok=True)
            filename = f"report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            filepath = os.path.join(reports_dir, filename)

            with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.DictWriter(f, fieldnames=["phone", "name", "status", "error_code", "timestamp"])
                writer.writeheader()
                writer.writerows(self.results_log)

            self.log(f"📄 تم حفظ التقرير في: {filepath}")
            return filepath
        except Exception as e:
            self.log(f"⚠ تعذر حفظ التقرير: {e}")
            return None

    # ═══════════════════════════════════════════════════════════════════════
    #  PRO VERSION PROGRESS WINDOW (APPENDED)
    # ═══════════════════════════════════════════════════════════════════════

    # ═══════════════════════════════════════════════════════════════════════
    #  BLIND MODE PROGRESS WINDOW (BENCHMARK MATCH)
    # ═══════════════════════════════════════════════════════════════════════
    def _format_progress_eta(self, seconds):
        if seconds is None:
            return "--"
        try:
            seconds = int(max(0, seconds))
        except Exception:
            return "--"
        minutes, secs = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        if hours:
            return f"{hours}س {minutes}د"
        if minutes:
            return f"{minutes}د {secs}ث"
        return f"{secs}ث"

    def _open_progress_window_blind(self, total, mode="send"):
        def _do():
            if self.progress_win and self.progress_win.winfo_exists():
                try:
                    self.progress_win.destroy()
                except Exception:
                    pass
            title_map = {
                "send": "متابعة الإرسال",
                "workflow": "متابعة سير العمل",
                "check": "فحص الأرقام",
            }
            title_text = title_map.get(mode, "متابعة العملية")
            self.progress_title_text = title_text
            self.progress_metric_labels = {}
            self.progress_win = ctk.CTkToplevel(self)
            self.progress_win.title(title_text)
            self.progress_win.geometry("1080x720")
            self.progress_win.minsize(980, 600)
            self.progress_win.grab_set()
            self.progress_win.protocol("WM_DELETE_WINDOW", self._close_progress_window)
            
            # Focus
            self.progress_win.after(100, self.progress_win.lift)

            # Main Container
            main_cont = ctk.CTkFrame(self.progress_win, corner_radius=0, fg_color=COLORS["bg_dark"])
            main_cont.pack(fill="both", expand=True)

            # 1. Top Header (Counters)
            header = ctk.CTkFrame(main_cont, corner_radius=10, fg_color=COLORS["card_bg"])
            header.pack(fill="x", padx=15, pady=(15, 10))
            
            # Title & Counter
            top_row = ctk.CTkFrame(header, fg_color="transparent")
            top_row.pack(fill="x", padx=15, pady=(10, 5))
            
            self.progress_count_label = ctk.CTkLabel(
                top_row, text=f"{title_text} (0/{total})",
                font=("Segoe UI", 16, "bold"), text_color=COLORS["text_main"]
            )
            self.progress_count_label.pack(side="left")
            
            status_chip = ctk.CTkLabel(
                top_row, text="جاري",
                font=("Segoe UI", 12, "bold"), text_color=COLORS["bg_dark"],
                fg_color=COLORS["primary"], corner_radius=6, padx=10, pady=2
            )
            status_chip.pack(side="right")
            self.progress_state_label = status_chip

            metrics_row = ctk.CTkFrame(header, fg_color="transparent")
            metrics_row.pack(fill="x", padx=15, pady=(4, 8))
            metric_defs = [
                ("processed", "تمت المعالجة", COLORS["info"], "0"),
                ("sent", "عنده واتساب" if mode == "check" else "تم الإرسال", COLORS["success"], "0"),
                ("failed", "فشل", COLORS["danger"], "0"),
                ("invalid", "بدون واتساب", COLORS["warning"], "0"),
                ("remaining", "متبقي", COLORS["text_muted"], str(total)),
                ("eta", "وقت تقريبي", COLORS["accent"], "--"),
            ]
            metrics_row.grid_columnconfigure(tuple(range(len(metric_defs))), weight=1)
            for idx, (key, label, color, value) in enumerate(metric_defs):
                card = ctk.CTkFrame(metrics_row, corner_radius=8, fg_color=COLORS["bg_dark"])
                card.grid(row=0, column=idx, padx=4, pady=2, sticky="ew")
                ctk.CTkLabel(
                    card, text=label, font=("Segoe UI", 11),
                    text_color=COLORS["text_muted"]
                ).pack(pady=(8, 1))
                value_label = ctk.CTkLabel(
                    card, text=value, font=("Segoe UI", 20, "bold"),
                    text_color=color
                )
                value_label.pack(pady=(0, 8))
                self.progress_metric_labels[key] = value_label

            # Progress Bar (Thick & Green)
            self.progress_bar_small = ctk.CTkProgressBar(header, height=20, corner_radius=0,
                                                         progress_color="#00E676", # Bright Neon Green
                                                         border_color=COLORS["border"], border_width=1)
            self.progress_bar_small.pack(fill="x", expand=True, padx=15, pady=(5, 15))
            self.progress_bar_small.set(0)

            # 2. Data Grid (Treeview)
            table_frame = ctk.CTkFrame(main_cont, corner_radius=10, fg_color=COLORS["card_bg"])
            table_frame.pack(fill="both", expand=True, padx=15, pady=(0, 10))

            columns = ("phone", "name", "date", "status", "message")
            self.popup_progress_tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=15)
            
            self.popup_progress_tree.heading("phone", text="الرقم")
            self.popup_progress_tree.heading("name", text="الاسم / الخطوة")
            self.popup_progress_tree.heading("date", text="الوقت")
            self.popup_progress_tree.heading("status", text="الحالة")
            self.popup_progress_tree.heading("message", text="التفاصيل")
            
            self.popup_progress_tree.column("phone", width=190, anchor="w")
            self.popup_progress_tree.column("name", width=180, anchor="w")
            self.popup_progress_tree.column("date", width=150, anchor="center")
            self.popup_progress_tree.column("status", width=120, anchor="center")
            self.popup_progress_tree.column("message", width=360, anchor="w")

            # Styling the Treeview
            style = ttk.Style(self.progress_win)
            try:
                style.theme_use("clam")
            except:
                pass
            
            bg_color = COLORS["bg_dark"]
            fg_color = COLORS["text_main"]
            row_height = 30
            
            style.configure(
                "Treeview",
                background=bg_color,
                foreground=fg_color,
                fieldbackground=bg_color,
                rowheight=row_height,
                font=("Segoe UI", 11),
                borderwidth=0
            )
            style.configure("Treeview.Heading", font=("Segoe UI", 11, "bold"), background=COLORS["card_bg"], foreground=COLORS["text_main"])
            style.map("Treeview", background=[("selected", COLORS["primary"])], foreground=[("selected", "black")])

            # Tags for coloring rows (Text color)
            self.popup_progress_tree.tag_configure("success", foreground="#00E676") # Green
            self.popup_progress_tree.tag_configure("failed", foreground="#FF3D00")  # Red
            self.popup_progress_tree.tag_configure("waiting", foreground=COLORS["text_muted"])
            self.popup_progress_tree.tag_configure("invalid", foreground="#FFA500") # Orange
            self.popup_progress_tree.tag_configure("stopped", foreground=COLORS["info"])

            tree_scroll = ctk.CTkScrollbar(table_frame, command=self.popup_progress_tree.yview)
            self.popup_progress_tree.configure(yscrollcommand=tree_scroll.set)
            self.popup_progress_tree.pack(side="left", fill="both", expand=True, padx=2, pady=2)
            tree_scroll.pack(side="right", fill="y", padx=2, pady=2)

            # 3. Footer Controls
            footer = ctk.CTkFrame(main_cont, corner_radius=10, fg_color=COLORS["card_bg"], height=60)
            footer.pack(fill="x", padx=15, pady=(0, 15))
            
            self.progress_status_label = ctk.CTkLabel(
                footer, text="جاهز للبدء...", font=("Segoe UI", 12), text_color=COLORS["text_muted"]
            )
            self.progress_status_label.pack(side="left", padx=20, pady=15)

            # Buttons (Black background as per screenshot)
            btn_style = {"width": 100, "height": 32, "font": ("Segoe UI", 12, "bold")}
            
            ctk.CTkButton(footer, text="Close", fg_color="black", hover_color="#333333", border_color=COLORS["border"], border_width=1,
                          command=self._close_progress_window, **btn_style).pack(side="right", padx=10)
                          
            self.pause_btn = ctk.CTkButton(footer, text="Pause", fg_color="black", hover_color="#333333", border_color=COLORS["border"], border_width=1,
                                           text_color="white", command=self._toggle_pause, **btn_style)
            self.pause_btn.pack(side="right", padx=5)
            
            ctk.CTkButton(footer, text="Export", fg_color="black", hover_color="#333333", border_color=COLORS["border"], border_width=1,
                          command=self._export_last_report, **btn_style).pack(side="right", padx=5)

        self._run_on_ui(_do)

    def _add_progress_row_blind(self, row_values, tag="waiting"):
        # row_values = [phone, type, time, status, message]
        # Prepend icon to phone (ID)
        icon = ""
        if tag == "success": icon = "OK "
        elif tag == "failed": icon = "FAIL "
        elif tag == "invalid": icon = "NO WA "
        elif tag == "stopped": icon = "STOP "
        elif tag == "waiting": icon = "... "
        
        new_values = list(row_values)
        while len(new_values) < 5:
            new_values.append("")
        new_values[0] = f"{icon}{new_values[0]}"
        
        def _do():
            try:
                if self.popup_progress_tree and self.popup_progress_tree.winfo_exists():
                    self.popup_progress_tree.insert("", "0", values=new_values, tags=(tag,))
            except Exception:
                pass
        self._run_on_ui(_do)

    def _update_progress_header_blind(self, processed, total, current_phone=None, current_name=None, eta=None, status_text=None):
        def _do():
            try:
                remaining = max(total - processed, 0)
                title_text = getattr(self, "progress_title_text", "متابعة العملية")
                if self.progress_count_label and self.progress_count_label.winfo_exists():
                    self.progress_count_label.configure(text=f"{title_text} ({processed}/{total})")
                if self.progress_bar_small and self.progress_bar_small.winfo_exists():
                    self.progress_bar_small.set(processed / total if total else 0)
                metric_values = {
                    "processed": processed,
                    "sent": self.sent,
                    "failed": self.failed,
                    "invalid": self.invalid,
                    "remaining": remaining,
                    "eta": self._format_progress_eta(eta),
                }
                for key, value in metric_values.items():
                    label = self.progress_metric_labels.get(key)
                    if label and label.winfo_exists():
                        label.configure(text=str(value))
                if self.progress_status_label and self.progress_status_label.winfo_exists():
                    if status_text:
                        text = status_text
                    elif current_phone and current_name:
                        text = f"جاري العمل على: {current_name} - {current_phone}"
                    elif current_phone:
                        text = f"جاري العمل على: {current_phone}"
                    else:
                        text = "جاري العمل..."
                    self.progress_status_label.configure(text=text)
            except Exception:
                pass
        self._run_on_ui(_do)

    def _load_profile_proxy_settings(self, profile_name):
        profile_proxies = self.config.get("profile_proxies", {})
        prof_config = profile_proxies.get(profile_name, {
            "enabled": False,
            "type": "HTTP",
            "host": "",
            "port": "",
            "username": "",
            "password": "",
            "fingerprint_enabled": True,
            "user_agent": "",
            "resolution": ""
        })
        
        self.proxy_enabled_var.set(prof_config.get("enabled", False))
        self.proxy_type_var.set(prof_config.get("type", "HTTP"))
        
        self.proxy_host_entry.delete(0, "end")
        self.proxy_host_entry.insert(0, prof_config.get("host", ""))
        
        self.proxy_port_entry.delete(0, "end")
        self.proxy_port_entry.insert(0, prof_config.get("port", ""))
        
        self.proxy_username_entry.delete(0, "end")
        self.proxy_username_entry.insert(0, prof_config.get("username", ""))
        
        self.proxy_password_entry.delete(0, "end")
        self.proxy_password_entry.insert(0, prof_config.get("password", ""))
        
        # Load fingerprint settings
        self.fp_enabled_var.set(prof_config.get("fingerprint_enabled", True))
        
        ua = prof_config.get("user_agent", "").strip()
        res = prof_config.get("resolution", "").strip()
        if not ua or not res:
            from utils.helpers import generate_random_fingerprint
            fp = generate_random_fingerprint()
            ua = fp["user_agent"]
            res = fp["resolution"]
            
        self.fp_ua_entry.delete(0, "end")
        self.fp_ua_entry.insert(0, ua)
        
        self.fp_res_entry.delete(0, "end")
        self.fp_res_entry.insert(0, res)
        
        self.proxy_status_label.configure(text="الحالة: لم يتم الفحص", text_color=COLORS["text_muted"])

    def _test_proxy_connection(self):
        proxy_type = self.proxy_type_var.get().lower()
        host = self.proxy_host_entry.get().strip()
        port = self.proxy_port_entry.get().strip()
        user = self.proxy_username_entry.get().strip()
        pwd = self.proxy_password_entry.get().strip()
        
        if not host or not port:
            messagebox.showerror("خطأ", "يرجى إدخال عنوان البروكسي والمنفذ (Host & Port).")
            return
            
        self.proxy_status_label.configure(text="جاري فحص الاتصال...", text_color=COLORS["warning"])
        self.test_proxy_btn.configure(state="disabled")
        
        def run_test():
            from utils.helpers import check_proxy
            success, info = check_proxy(proxy_type, host, port, user, pwd)
            
            def update_ui():
                self.test_proxy_btn.configure(state="normal")
                if success:
                    ip = info.get("ip", "Unknown")
                    country = info.get("country", "Unknown")
                    city = info.get("city", "")
                    loc = f"{country} ({city})" if city else country
                    self.proxy_status_label.configure(
                        text=f"🟢 متصل | IP: {ip} | الدولة: {loc}",
                        text_color=COLORS["success"]
                    )
                else:
                    err = info.get("error", "فشل غير معروف")
                    self.proxy_status_label.configure(
                        text=f"🔴 فشل الاتصال: {err}",
                        text_color=COLORS["danger"]
                    )
            
            self._run_on_ui(update_ui)
            
        threading.Thread(target=run_test, daemon=True).start()

    def _generate_new_profile_fingerprint(self):
        from utils.helpers import generate_random_fingerprint
        fp = generate_random_fingerprint()
        
        self.fp_ua_entry.delete(0, "end")
        self.fp_ua_entry.insert(0, fp["user_agent"])
        
        self.fp_res_entry.delete(0, "end")
        self.fp_res_entry.insert(0, fp["resolution"])

    # ═══════════════════════════════════════════════════════════════════════
    #  AUTO RESPONDER ACTIONS & LOGIC
    # ═══════════════════════════════════════════════════════════════════════








    # ═══════════════════════════════════════════════════════════════════════
    #  TABLES & UTILS HELPERS
    # ═══════════════════════════════════════════════════════════════════════
    def _refresh_numbers_table(self, contacts):
        for item in self.progress_tree.get_children():
            self.progress_tree.delete(item)
        for c in contacts:
            name = c.get("name") or "عميل"
            phone = c.get("phone") or ""
            var1 = c.get("var1") or c.get("variable1") or ""
            self.progress_tree.insert("", "end", values=(name, phone, var1, "⏳ معلق"), tags=("pending",))
        self._update_contacts_count_from_tree()

    def _update_contacts_count_from_tree(self):
        total = len(self.progress_tree.get_children())
        self.total_counts_label.configure(text=f"مجموعات: 0 | جهات الاتصال: {total} | Total: {total}")

    def _show_import_popup_menu(self):
        import tkinter as tk
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label="📁 استيراد من ملف Excel/CSV...", command=self._browse_contacts)
        menu.add_command(label="👥 استيراد من مجموعة...", command=self._open_import_dialog)
        menu.add_command(label="🧮 مولد أرقام جديد...", command=self._open_number_generator)
        try:
            x = self.btn_tbl_menu.winfo_rootx()
            y = self.btn_tbl_menu.winfo_rooty() + self.btn_tbl_menu.winfo_height()
            menu.post(x, y)
        except Exception:
            pass

    def _remove_selected_table_number(self):
        selected = self.progress_tree.selection()
        if not selected:
            self._show_dialog("warning", "تنبيه", "يرجى تحديد صف واحد أو أكثر لحذفه.")
            return
        for item in selected:
            self.progress_tree.delete(item)
        self._update_contacts_count_from_tree()

    def _add_manual_number_dialog(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("إضافة رقم يدوي")
        dialog.geometry("380x280")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()

        x = self.winfo_x() + (self.winfo_width() - 380) // 2
        y = self.winfo_y() + (self.winfo_height() - 280) // 2
        dialog.geometry(f"+{x}+{y}")

        frm = ctk.CTkFrame(dialog, fg_color="transparent")
        frm.pack(fill="both", expand=True, padx=20, pady=20)

        lbl_phone = ctk.CTkLabel(frm, text="رقم الهاتف (مع رمز الدولة):", font=("Segoe UI", 11))
        lbl_phone.pack(anchor="e", pady=(0, 2))
        entry_phone = ctk.CTkEntry(frm, placeholder_text="مثال: 201012345678", justify="center")
        entry_phone.pack(fill="x", pady=(0, 10))

        lbl_name = ctk.CTkLabel(frm, text="الاسم:", font=("Segoe UI", 11))
        lbl_name.pack(anchor="e", pady=(0, 2))
        entry_name = ctk.CTkEntry(frm, placeholder_text="مثال: محمد أحمد", justify="right")
        entry_name.pack(fill="x", pady=(0, 10))

        lbl_var1 = ctk.CTkLabel(frm, text="المتغير 1 (اختياري):", font=("Segoe UI", 11))
        lbl_var1.pack(anchor="e", pady=(0, 2))
        entry_var1 = ctk.CTkEntry(frm, placeholder_text="مثال: قيمة مخصصة", justify="right")
        entry_var1.pack(fill="x", pady=(0, 15))

        def on_add():
            phone = entry_phone.get().strip()
            name = entry_name.get().strip() or "عميل"
            var1 = entry_var1.get().strip()
            if not phone:
                self._show_dialog("warning", "خطأ", "يرجى إدخال رقم الهاتف.")
                return
            
            from utils.helpers import normalize_phone
            cleaned_phone = normalize_phone(phone, self.config.get("default_country_code", "20"))
            if not cleaned_phone:
                self._show_dialog("warning", "خطأ", "رقم الهاتف غير صالح.")
                return
            
            self.progress_tree.insert("", "end", values=(name, cleaned_phone, var1, "⏳ معلق"), tags=("pending",))
            self._update_contacts_count_from_tree()
            dialog.destroy()

        btn_frm = ctk.CTkFrame(frm, fg_color="transparent")
        btn_frm.pack(fill="x")
        
        ctk.CTkButton(
            btn_frm, text="إلغاء", font=("Segoe UI", 11),
            width=80, height=28, fg_color=COLORS["danger"], hover_color=COLORS["danger_hover"],
            command=dialog.destroy
        ).pack(side="left")
        
        ctk.CTkButton(
            btn_frm, text="إضافة", font=("Segoe UI", 11, "bold"),
            width=100, height=28, fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"],
            text_color="#000000",
            command=on_add
        ).pack(side="right")

    def _show_numbers_context_menu(self, event):
        try:
            self.numbers_context_menu.post(event.x_root, event.y_root)
        except Exception:
            pass

    def _clear_numbers_table(self):
        for item in self.progress_tree.get_children():
            self.progress_tree.delete(item)
        self._update_contacts_count_from_tree()
        self.log("🗑️ تم مسح قائمة الأرقام بالكامل.")

    def _add_bulk_manual_numbers_dialog(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Manual Import | استيراد يدوي")
        dialog.geometry("540x580")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()

        # Center dialog
        x = self.winfo_x() + (self.winfo_width() - 540) // 2
        y = self.winfo_y() + (self.winfo_height() - 580) // 2
        dialog.geometry(f"+{x}+{y}")

        frm = ctk.CTkFrame(dialog, fg_color="transparent")
        frm.pack(fill="both", expand=True, padx=15, pady=15)

        # Header - Enter Contacts
        lbl_enter = ctk.CTkLabel(frm, text="Enter contacts | أدخل جهات الاتصال:", font=("Segoe UI", 12, "bold"))
        lbl_enter.pack(anchor="w", pady=(0, 2))

        # Textbox
        textbox = ctk.CTkTextbox(frm, height=130, font=("Consolas", 11))
        textbox.pack(fill="x", pady=(0, 2))

        # Enable undo
        try:
            textbox._textbox.configure(undo=True)
        except Exception:
            pass

        # Right-click context menu
        import tkinter as tk
        ctx_menu = tk.Menu(dialog, tearoff=0, font=("Segoe UI", 11))
        ctx_menu.add_command(label="تراجع (Undo)", command=lambda: _ctx_undo())
        ctx_menu.add_command(label="إعادة (Redo)", command=lambda: _ctx_redo())
        ctx_menu.add_separator()
        ctx_menu.add_command(label="قص (Cut)", command=lambda: textbox._textbox.event_generate("<<Cut>>"))
        ctx_menu.add_command(label="نسخ (Copy)", command=lambda: textbox._textbox.event_generate("<<Copy>>"))
        ctx_menu.add_command(label="لصق (Paste)", command=lambda: textbox._textbox.event_generate("<<Paste>>"))
        ctx_menu.add_command(label="حذف (Delete)", command=lambda: _ctx_delete())
        ctx_menu.add_separator()
        ctx_menu.add_command(label="تحديد الكل (Select All)", command=lambda: textbox._textbox.tag_add("sel", "1.0", "end"))

        def _ctx_undo():
            try: textbox._textbox.edit_undo()
            except: pass
        def _ctx_redo():
            try: textbox._textbox.edit_redo()
            except: pass
        def _ctx_delete():
            try: textbox._textbox.delete("sel.first", "sel.last")
            except: pass
        def _show_ctx(event):
            try: ctx_menu.tk_popup(event.x_root, event.y_root)
            finally: ctx_menu.grab_release()

        textbox.bind("<Button-3>", _show_ctx)

        # Help Label
        lbl_help = ctk.CTkLabel(
            frm, 
            text="Line per number. You can name by entering name, comma, then mobile (name,number)\nاكتب اسماً متبوعاً بفاصلة ثم الرقم في كل سطر (مثال: محمد أحمد,201012345678)",
            font=("Segoe UI", 9), 
            text_color=COLORS.get("text_muted", "#64748B"),
            justify="left"
        )
        lbl_help.pack(anchor="w", pady=(0, 10))

        # Validated label
        lbl_val = ctk.CTkLabel(frm, text="Validated contacts | جهات الاتصال التي تم التحقق منها:", font=("Segoe UI", 12, "bold"))
        lbl_val.pack(anchor="w", pady=(0, 2))

        # Treeview frame
        tree_frame = ctk.CTkFrame(frm, fg_color="transparent")
        tree_frame.pack(fill="both", expand=True, pady=(0, 5))

        # Validate Treeview
        validated_tree = ttk.Treeview(tree_frame, columns=("name", "phone"), show="headings", height=8)
        validated_tree.heading("name", text="Name | الاسم")
        validated_tree.heading("phone", text="Number | الرقم")
        validated_tree.column("name", width=220, anchor="w")
        validated_tree.column("phone", width=220, anchor="center")

        tree_scroll = ctk.CTkScrollbar(tree_frame, command=validated_tree.yview)
        validated_tree.configure(yscrollcommand=tree_scroll.set)
        
        tree_scroll.pack(side="right", fill="y")
        validated_tree.pack(side="left", fill="both", expand=True)

        # Stats labels
        stats_frame = ctk.CTkFrame(frm, fg_color="transparent")
        stats_frame.pack(fill="x", pady=(0, 10))

        lbl_total = ctk.CTkLabel(stats_frame, text="Total: 0", font=("Segoe UI", 11, "bold"))
        lbl_total.pack(side="left", padx=(0, 20))

        lbl_dup = ctk.CTkLabel(stats_frame, text="Duplication: 0", font=("Segoe UI", 11, "bold"), text_color=COLORS.get("danger", "#EF4444"))
        lbl_dup.pack(side="left")

        # Bottom Frame
        bottom_frame = ctk.CTkFrame(frm, fg_color="transparent")
        bottom_frame.pack(fill="x", pady=(10, 0))

        chk_remove_dup = ctk.CTkCheckBox(bottom_frame, text="Remove duplication | إزالة التكرار", font=("Segoe UI", 11))
        chk_remove_dup.pack(side="left", pady=5)
        chk_remove_dup.select()

        # Dialog State Variables
        dialog.parsed_contacts = []

        def _on_bulk_text_changed(event=None):
            raw_text = textbox.get("1.0", "end-1c")
            lines = raw_text.split("\n")
            
            parsed_list = []
            seen_numbers = set()
            dups_count = 0
            
            from utils.helpers import normalize_phone
            default_cc = self.config.get("default_country_code", "20")
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Parse name, number
                if "," in line:
                    parts = line.split(",", 1)
                    name = parts[0].strip() or "عميل"
                    phone_raw = parts[1].strip()
                else:
                    name = "عميل"
                    phone_raw = line.strip()
                
                cleaned_phone = normalize_phone(phone_raw, default_cc)
                if cleaned_phone:
                    if cleaned_phone in seen_numbers:
                        dups_count += 1
                    seen_numbers.add(cleaned_phone)
                    parsed_list.append((name, cleaned_phone))
            
            # Update treeview
            for item in validated_tree.get_children():
                validated_tree.delete(item)
                
            for name, phone in parsed_list:
                validated_tree.insert("", "end", values=(name, phone))
                
            lbl_total.configure(text=f"Total: {len(parsed_list)}")
            lbl_dup.configure(text=f"Duplication: {dups_count}")
            
            dialog.parsed_contacts = parsed_list

        # Bind key release to real-time validation
        textbox.bind("<KeyRelease>", _on_bulk_text_changed)

        def on_import():
            if not dialog.parsed_contacts:
                self._show_dialog("warning", "تنبيه", "لا توجد جهات اتصال صالحة للاستيراد.")
                return
            
            remove_dup = chk_remove_dup.get()
            imported_count = 0
            seen = set()
            
            # Fetch existing numbers to prevent duplicates if necessary, or just within this batch
            for name, phone in dialog.parsed_contacts:
                if remove_dup:
                    if phone in seen:
                        continue
                    seen.add(phone)
                
                self.progress_tree.insert("", "end", values=(name, phone, "", "⏳ معلق"), tags=("pending",))
                imported_count += 1
                
            self._update_contacts_count_from_tree()
            self.log(f"✍️ تم استيراد {imported_count} جهة اتصال يدوياً.")
            dialog.destroy()

        btn_import = ctk.CTkButton(
            bottom_frame, text="Import | استيراد", font=("Segoe UI", 11, "bold"),
            width=100, height=30, fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"],
            text_color="#000000",
            command=on_import
        )
        btn_import.pack(side="right", padx=(10, 0))

        btn_cancel = ctk.CTkButton(
            bottom_frame, text="Cancel | إلغاء", font=("Segoe UI", 11),
            width=90, height=30, fg_color=COLORS["danger"], hover_color=COLORS["danger_hover"],
            command=dialog.destroy
        )
        btn_cancel.pack(side="right")

    def _show_attachments_popup_menu(self):
        import tkinter as tk
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label="🖼️ إضافة صورة/فيديو...", command=lambda: self.attachment_manager.add_attachment("image"))
        menu.add_command(label="📄 إضافة ملف PDF/مستند...", command=lambda: self.attachment_manager.add_attachment("document"))
        menu.add_command(label="🎵 إضافة ملف صوتي...", command=lambda: self.attachment_manager.add_attachment("audio"))
        menu.add_separator()
        menu.add_command(label="🗑️ مسح المرفقات", command=lambda: self.attachment_manager.clear())
        try:
            x = self.btn_atts_menu.winfo_rootx()
            y = self.btn_atts_menu.winfo_rooty() + self.btn_atts_menu.winfo_height()
            menu.post(x, y)
        except Exception:
            pass

    def _show_help_dialog(self):
        self._show_dialog("info", "دليل الاستخدام والمساعدة", "دليل الاستخدام:\n1. قم بفتح تطبيق WhatsApp وسجل الدخول باستخدام رمز الاستجابة السريعة (QR Code).\n2. استورد الأرقام باستخدام زر الاستيراد أو قم بإدخالها يدوياً.\n3. اكتب الرسالة في المحرر وأضف أي ملفات مرفقة إن وجدت.\n4. اضغط على زر 'ارسل الآن' لبدء الحملة الإعلانية.")

    def _show_about_dialog(self):
        self._show_dialog("info", "حول البرنامج", "WhatsApp Sender Pro\nالإصدار v17.0\nمطور ومحسن لتوفير أقصى درجات الحماية والسرعة.\nالبرنامج يدعم حماية بصمة المتصفح ونظام منع الحظر التلقائي الذكي.")

    def _logout_action(self):
        if self.bot:
            try:
                self.bot.close()
            except Exception:
                pass
            self.bot = None
            self.session_status_label.configure(text="Disconnected | Not Ready | Account: N/A")
            self.status_indicator.configure(text_color=COLORS["danger"])
            self.log("🚪 تم تسجيل الخروج بنجاح وإغلاق المتصفح.")
            self._show_dialog("info", "تسجيل الخروج", "تم تسجيل الخروج وإغلاق متصفح WhatsApp بنجاح.")
        else:
            self._show_dialog("warning", "تسجيل الخروج", "المتصفح مغلق بالفعل.")

    def _toggle_appearance_menu(self):
        current_mode = ctk.get_appearance_mode().lower()
        new_mode = "light" if current_mode == "dark" else "dark"
        ctk.set_appearance_mode(new_mode)
        self.config.set("appearance_mode", new_mode)
        self._apply_palette(new_mode)
        self._refresh_theme()

    # â”€â”€â”€ GMaps Scraper Methods â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


