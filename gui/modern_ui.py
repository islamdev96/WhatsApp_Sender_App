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

from .components import RichTextFrame, AttachmentManager

from automation.whatsapp_bot import WhatsAppBot
from utils.helpers import read_contacts, read_contacts_auto
from utils.config_manager import ConfigManager
from utils.templates_manager import TemplatesManager
from utils.contacts_manager import ContactsManager
from utils.scheduler import Scheduler
from utils.campaign_manager import CampaignManager
from utils.workflow_manager import WorkflowManager

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
        self.scheduler = Scheduler()
        self.campaign_manager = CampaignManager()
        self.workflow_manager = WorkflowManager()

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

        # ── Profiles ──
        self.profiles_dir = os.path.join(os.getcwd(), self.config.get("profiles_dir", os.path.join("data", "profiles")))
        self.legacy_profile_dir = os.path.join(os.getcwd(), "chrome_profile")
        os.makedirs(self.profiles_dir, exist_ok=True)
        profile_name = self.config.get("profile_name", "Default")
        if profile_name != "Legacy":
            os.makedirs(os.path.join(self.profiles_dir, profile_name), exist_ok=True)
        self.profile_var = ctk.StringVar(value=profile_name)
        if profile_name == "Legacy" and os.path.exists(self.legacy_profile_dir):
            self.user_data_dir = self.legacy_profile_dir
        else:
            self.user_data_dir = os.path.join(self.profiles_dir, profile_name)

        # ── Build UI ──
        self._build_layout()
        self._load_saved_state()

        # ── UI Queue Processor ──
        self.after(50, self._process_ui_queue)

        # ── Background Status Monitor ──
        self._start_status_monitor()

        # ── Save on close ──
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _apply_palette(self, mode):
        palette = PALETTE_DARK if str(mode).lower() == "dark" else PALETTE_LIGHT
        COLORS.clear()
        COLORS.update(palette)

    def _refresh_theme(self):
        # Update key widgets after palette change
        if hasattr(self, "sidebar"):
            self.sidebar.configure(fg_color=COLORS["primary_dark"])
        if hasattr(self, "appearance_switch"):
            self.appearance_switch.configure(text_color=COLORS["text_main"])
        if hasattr(self, "status_card"):
            self.status_card.configure(fg_color=COLORS["bg_dark"])
        if hasattr(self, "session_status_label"):
            self.session_status_label.configure(text_color=COLORS["text_main"])
        if hasattr(self, "nav_buttons") and hasattr(self, "current_tab"):
            for nid, btn in self.nav_buttons.items():
                if nid == self.current_tab:
                    btn.configure(fg_color=COLORS["primary"], text_color="#000000", font=("Segoe UI", 14, "bold"))
                else:
                    btn.configure(fg_color="transparent", text_color=COLORS["text_muted"], font=("Segoe UI", 14))
        if hasattr(self, "attachment_manager"):
            self.attachment_manager.apply_theme(COLORS)
        if hasattr(self, "message_editor"):
            self.message_editor.apply_theme(COLORS)
        if hasattr(self, "workflow_step_editor"):
            self.workflow_step_editor.apply_theme(COLORS)
        if hasattr(self, "workflow_step_attachments"):
            self.workflow_step_attachments.apply_theme(COLORS)
        if hasattr(self, "progress_bar"):
            self.progress_bar.configure(progress_color=COLORS["primary"])
        if hasattr(self, "total_counts_label"):
            self.total_counts_label.configure(text_color=COLORS["text_muted"])
        if hasattr(self, "btn_start"):
            self.btn_start.configure(fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"], text_color="#000000")
        if hasattr(self, "btn_login"):
            self.btn_login.configure(fg_color=COLORS["secondary"], hover_color=COLORS["secondary_hover"], text_color=COLORS["secondary_text"])
        if hasattr(self, "btn_stop"):
            self.btn_stop.configure(fg_color=COLORS["danger"], hover_color=COLORS["danger_hover"], text_color="#FFFFFF")
        if hasattr(self, "btn_check"):
            self.btn_check.configure(fg_color=COLORS["info"], hover_color=COLORS["accent_hover"])
        if hasattr(self, "btn_schedule"):
            self.btn_schedule.configure(fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"])
        if hasattr(self, "btn_cancel_sched"):
            self.btn_cancel_sched.configure(fg_color=COLORS["danger"], hover_color=COLORS["danger_hover"])
        if hasattr(self, "workflow_menu"):
            self.workflow_menu.configure(
                fg_color=COLORS["card_bg"],
                button_color=COLORS["primary"],
                button_hover_color=COLORS["primary_hover"],
                text_color=COLORS["text_main"],
                dropdown_fg_color=COLORS["card_bg"],
                dropdown_text_color=COLORS["text_main"],
            )
        if hasattr(self, "workflow_name_entry"):
            self.workflow_name_entry.configure(
                fg_color=COLORS["bg_dark"],
                text_color=COLORS["text_main"],
                border_color=COLORS["border"],
            )
        if hasattr(self, "step_delay_min_entry"):
            self.step_delay_min_entry.configure(
                fg_color=COLORS["bg_dark"],
                text_color=COLORS["text_main"],
                border_color=COLORS["border"],
            )
        if hasattr(self, "step_delay_max_entry"):
            self.step_delay_max_entry.configure(
                fg_color=COLORS["bg_dark"],
                text_color=COLORS["text_main"],
                border_color=COLORS["border"],
            )

    # ═══════════════════════════════════════════════════════════════════════
    #  LAYOUT
    # ═══════════════════════════════════════════════════════════════════════
    def _build_layout(self):
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # ── Sidebar ──
        self._build_sidebar()

        # ── Main Content Area ──
        self.main_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, sticky="nsew")
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        # ── Tabs (frames) ──
        self.tab_frames = {}
        self._build_tab_main()
        self._build_tab_groups()
        self._build_tab_workflows()
        self._build_tab_templates()
        self._build_tab_settings()
        self._build_tab_analytics()
        self._build_tab_log()

        # Show main tab by default
        self._switch_tab("main")
        self._refresh_theme()

    # ─── Sidebar ──────────────────────────────────────────────────────────
    def _build_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=240, corner_radius=0,
                                    fg_color=COLORS["primary_dark"])
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(11, weight=1)

        # Logo / Title
        logo_label = ctk.CTkLabel(self.sidebar, text="⚡ WA Sender",
                                  font=("Segoe UI", 26, "bold"),
                                  text_color=COLORS["primary"])
        logo_label.grid(row=0, column=0, padx=20, pady=(35, 5))

        subtitle = ctk.CTkLabel(self.sidebar, text="PRO EDITION",
                                font=("Segoe UI", 10, "bold"),
                                text_color=COLORS["text_muted"])
        subtitle.grid(row=1, column=0, padx=20, pady=(0, 20))

        # Profile Selector
        self.profile_combo = ctk.CTkComboBox(self.sidebar, values=self._get_profiles(),
                                             variable=self.profile_var,
                                             command=self._on_profile_change,
                                             width=180, height=30,
                                             fg_color=COLORS["card_bg"],
                                             border_color=COLORS["border"],
                                             button_color=COLORS["primary"],
                                             button_hover_color=COLORS["primary_hover"],
                                             text_color=COLORS["text_main"],
                                             dropdown_fg_color=COLORS["card_bg"],
                                             dropdown_text_color=COLORS["text_main"])
        self.profile_combo.grid(row=2, column=0, padx=20, pady=(0, 20))
        
        # New Profile Button
        ctk.CTkButton(self.sidebar, text="+ حساب جديد", width=180, height=24,
                      fg_color=COLORS["secondary"], hover_color=COLORS["secondary_hover"],
                      text_color=COLORS["secondary_text"],
                      font=("Segoe UI", 11),
                      command=self._create_new_profile).grid(row=3, column=0, padx=20, pady=(0, 30))

        # Navigation Buttons
        nav_items = [
            ("🏠  الرئيسية", "main"),
            ("👥  المجموعات", "groups"),
            ("🧭  سير العمل", "workflows"),
            ("📝  القوالب", "templates"),
            ("📊  التحليلات", "analytics"),
            ("⚙️  الإعدادات", "settings"),
            ("📋  السجل", "log"),
        ]

        self.nav_buttons = {}
        for i, (text, tab_id) in enumerate(nav_items):
            btn = ctk.CTkButton(self.sidebar, text=text,
                                font=("Segoe UI", 14),
                                fg_color="transparent",
                                text_color=COLORS["text_muted"],
                                hover_color=COLORS["bg_dark"],
                                anchor="w",
                                height=50,
                                corner_radius=10,
                                command=lambda t=tab_id: self._switch_tab(t))
            btn.grid(row=i + 4, column=0, padx=15, pady=4, sticky="ew")
            self.nav_buttons[tab_id] = btn

        # Spacer
        # row 11 has weight=1

        # Appearance Toggle
        self.appearance_switch = ctk.CTkSwitch(self.sidebar, text="الوضع الداكن",
                                               font=ctk.CTkFont(size=12),
                                               text_color=COLORS["text_main"],
                                               command=self._toggle_appearance,
                                               onvalue="dark", offvalue="light")
        self.appearance_switch.grid(row=12, column=0, padx=20, pady=(10, 5))
        if self.config.get("appearance_mode", "dark") == "dark":
            self.appearance_switch.select()

        # Version
        ver_label = ctk.CTkLabel(self.sidebar, text="v2.5.0",
                                 font=ctk.CTkFont(size=10),
                                 text_color="#6C757D")
        ver_label.grid(row=13, column=0, padx=20, pady=(5, 15))

    def _switch_tab(self, tab_id):
        self.current_tab = tab_id
        for fid, frame in self.tab_frames.items():
            frame.grid_forget()
        self.tab_frames[tab_id].grid(row=0, column=0, sticky="nsew", padx=0, pady=0)

        # Highlight active nav
        for nid, btn in self.nav_buttons.items():
            if nid == tab_id:
                btn.configure(fg_color=COLORS["primary"], text_color="#000000", font=("Segoe UI", 14, "bold"))
            else:
                btn.configure(fg_color="transparent", text_color=COLORS["text_muted"], font=("Segoe UI", 14))

    # ─── Main Tab ─────────────────────────────────────────────────────────
    def _build_tab_main(self):
        frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.tab_frames["main"] = frame

        # ── Dashboard Stats Row ──
        dash = ctk.CTkFrame(frame, fg_color="transparent")
        dash.pack(fill="x", padx=20, pady=(15, 10))
        dash.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self.stat_cards = {}
        stats = [
            ("total", "📋 الإجمالي", "0", COLORS["info"]),
            ("success", "✅ نجاح", "0", COLORS["success"]),
            ("failed", "❌ فشل", "0", COLORS["danger"]),
            ("invalid", "🚫 بدون واتساب", "0", COLORS["warning"]),
        ]
        for i, (key, title, val, color) in enumerate(stats):
            card = ctk.CTkFrame(dash, corner_radius=16, height=100, fg_color=COLORS["card_bg"])
            card.grid(row=0, column=i, padx=8, pady=5, sticky="ew")
            card.grid_propagate(False)
            
            ctk.CTkLabel(card, text=title, font=("Segoe UI", 12),
                         text_color=COLORS["text_muted"]).pack(pady=(20, 5))
            val_label = ctk.CTkLabel(card, text=val,
                                     font=("Segoe UI", 32, "bold"),
                                     text_color=color)
            val_label.pack()
            self.stat_cards[key] = val_label

        # ── Two-Column Layout ──
        body = ctk.CTkFrame(frame, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=20, pady=5)
        body.grid_columnconfigure(0, weight=3)
        body.grid_columnconfigure(1, weight=2)
        body.grid_rowconfigure(0, weight=1)

        # LEFT: Message + Files
        left = ctk.CTkFrame(body, corner_radius=12)
        left.grid(row=0, column=0, padx=(0, 8), pady=5, sticky="nsew")

        # -- Files Section --
        files_label = ctk.CTkLabel(left, text="📁 الملفات والمرفقات", font=("Segoe UI", 14, "bold"), text_color=COLORS["text_main"])
        files_label.pack(anchor="e", padx=20, pady=(12, 10))

        # 1. Contacts
        self._create_file_row(left, "👥 ملف الأرقام", "contacts_entry", self._browse_contacts)
        ctk.CTkButton(left, text="📥 استيراد متقدم", height=30,
                      fg_color=COLORS["secondary"], hover_color=COLORS["secondary_hover"],
                      text_color=COLORS["secondary_text"],
                      font=ctk.CTkFont(size=12, weight="bold"),
                      command=self._open_import_dialog).pack(fill="x", padx=20, pady=(2, 4))

        # Contact count label
        self.contact_count_label = ctk.CTkLabel(left, text="", font=("Segoe UI", 11),
                                                 text_color=COLORS["text_muted"])
        self.contact_count_label.pack(anchor="e", padx=25, pady=(0, 4))
        ctk.CTkButton(left, text="🧮 مولد أرقام", height=30,
                      fg_color=COLORS["secondary"], hover_color=COLORS["secondary_hover"],
                      text_color=COLORS["secondary_text"],
                      font=ctk.CTkFont(size=12, weight="bold"),
                      command=self._open_number_generator).pack(fill="x", padx=20, pady=(0, 8))

        # Attachments Panel (New)
        self.attachment_manager = AttachmentManager(left, colors=COLORS, fg_color=COLORS["card_bg"], corner_radius=12)
        self.attachment_manager.pack(fill="x", padx=15, pady=(6, 10))

        # Message Section (New)
        self.message_editor = RichTextFrame(left, colors=COLORS, fg_color=COLORS["bg_dark"], corner_radius=12)
        self.message_editor.pack(fill="both", expand=True, padx=20, pady=(5, 10))
        self.message_textbox = self.message_editor.text_box # Alias for backward compatibility
        self.msg_text = self.message_editor.text_box # Alias

        ctk.CTkLabel(left, text="ملاحظة: لفصل رسائل متعددة استخدم --- بين كل رسالة",
                     font=("Segoe UI", 10), text_color=COLORS["text_muted"]).pack(anchor="e", padx=25, pady=(0, 8))
        



        


        # -- Checkboxes --
        chk_frame = ctk.CTkFrame(left, fg_color="transparent")
        chk_frame.pack(fill="x", padx=15, pady=(0, 12))

        self.send_text_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(chk_frame, text="إرسال النص مع أول مرفق",
                        variable=self.send_text_var,
                        font=ctk.CTkFont(size=12)).pack(side="right", padx=5)

        self.bg_mode_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(chk_frame, text="🖥️ تشغيل في الخلفية",
                        variable=self.bg_mode_var,
                        font=ctk.CTkFont(size=12)).pack(side="right", padx=5)

        self.spin_text_var = ctk.BooleanVar(value=self.config.get("enable_spintax", True))
        ctk.CTkCheckBox(chk_frame, text="🎲 تدوير النص (Spintax)",
                        variable=self.spin_text_var,
                        font=ctk.CTkFont(size=12)).pack(side="right", padx=5)

        self.preview_spintax_btn = ctk.CTkButton(
            chk_frame,
            text="🔍 معاينة الرسالة",
            width=90,
            height=26,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=COLORS["info"],
            hover_color=COLORS["accent_hover"],
            command=self._test_spintax
        )
        self.preview_spintax_btn.pack(side="left", padx=5)

        # RIGHT: Controls + Progress
        right = ctk.CTkFrame(body, corner_radius=12, fg_color=COLORS["card_bg"])
        right.grid(row=0, column=1, padx=(8, 0), pady=5, sticky="nsew")

        ctrl_label = ctk.CTkLabel(right, text="🎛️ التحكم", font=ctk.CTkFont(size=14, weight="bold"))
        ctrl_label.pack(anchor="e", padx=15, pady=4)

        # Status Card (Glow effect)
        self.status_card = ctk.CTkFrame(right, corner_radius=10, fg_color=COLORS["bg_dark"], height=46)
        self.status_card.pack(fill="x", padx=15, pady=(0, 15))
        self.status_card.pack_propagate(False)

        self.status_indicator = ctk.CTkLabel(self.status_card, text="●", font=("Segoe UI", 20), text_color=COLORS["danger"])
        self.status_indicator.pack(side="right", padx=(15, 5), pady=8)

        self.session_status_label = ctk.CTkLabel(
            self.status_card,
            text="الحالة: غير متصل",
            font=("Segoe UI", 13, "bold"),
            text_color=COLORS["text_main"],
            anchor="e"
        )
        self.session_status_label.pack(side="right", padx=(0, 15), pady=8)

        ctrl_frame = ctk.CTkFrame(right, fg_color="transparent")
        ctrl_frame.pack(fill="x", padx=15, pady=(0, 10))
        ctrl_frame.grid_columnconfigure((0, 1), weight=1)

        # 1. Login
        self.btn_login = ctk.CTkButton(ctrl_frame, text="🔑 فتح واتساب (Login)",
                                       font=("Segoe UI", 13, "bold"),
                                       height=42,
                                       fg_color=COLORS["secondary"],
                                       hover_color=COLORS["secondary_hover"],
                                       text_color=COLORS["secondary_text"],
                                       command=self._login_action)
        self.btn_login.grid(row=0, column=1, padx=(5, 0), pady=(0, 10), sticky="ew")

        # 2. Start
        self.btn_start = ctk.CTkButton(ctrl_frame, text="🚀 بدء الإرسال",
                                       font=("Segoe UI", 14, "bold"),
                                       height=42,
                                       fg_color=COLORS["primary"],
                                       text_color="#000000",
                                       hover_color=COLORS["primary_hover"],
                                       command=self._start_action)
        self.btn_start.grid(row=0, column=0, padx=(0, 5), pady=(0, 10), sticky="ew")

        # 3. Stop
        self.btn_stop = ctk.CTkButton(ctrl_frame, text="🛑 إيقاف مؤقت",
                                      font=("Segoe UI", 13, "bold"),
                                      height=38,
                                      fg_color=COLORS["danger"],
                                      hover_color=COLORS["danger_hover"],
                                      text_color="#FFFFFF",
                                      state="disabled",
                                      command=self._stop_action)
        self.btn_stop.grid(row=1, column=1, padx=(5, 0), pady=(0, 10), sticky="ew")

        # 4. Check Numbers
        self.btn_check = ctk.CTkButton(ctrl_frame, text="🔍 فحص الأرقام فقط",
                                       font=("Segoe UI", 12, "bold"),
                                       height=38,
                                       fg_color=COLORS["info"],
                                       hover_color=COLORS["accent_hover"],
                                       command=self._check_numbers_action)
        self.btn_check.grid(row=1, column=0, padx=(0, 5), pady=(0, 10), sticky="ew")

        self.use_valid_after_check_var = ctk.BooleanVar(value=self.config.get("use_valid_after_check", False))
        ctk.CTkCheckBox(ctrl_frame, text="استخدم الصالح فقط بعد الفحص",
                        variable=self.use_valid_after_check_var,
                        font=ctk.CTkFont(size=11)).grid(row=2, column=0, columnspan=2, padx=5, pady=(0, 10), sticky="e")

        # -- Workflow --
        wf_label = ctk.CTkLabel(right, text="🧭 سير العمل", font=ctk.CTkFont(size=13, weight="bold"))
        wf_label.pack(anchor="e", padx=15, pady=(4, 4))

        wf_row = ctk.CTkFrame(right, fg_color="transparent")
        wf_row.pack(fill="x", padx=15, pady=(0, 4))

        self.use_workflow_var = ctk.BooleanVar(value=self.config.get("use_workflow", False))
        ctk.CTkCheckBox(wf_row, text="تفعيل", variable=self.use_workflow_var,
                        font=ctk.CTkFont(size=11)).pack(side="right", padx=4)

        self.workflow_var = ctk.StringVar(value=self.config.get("last_workflow", ""))
        self.workflow_menu = ctk.CTkOptionMenu(
            wf_row,
            values=self._get_workflow_names(),
            variable=self.workflow_var,
            width=160,
            height=28,
            fg_color=COLORS["card_bg"],
            button_color=COLORS["primary"],
            button_hover_color=COLORS["primary_hover"],
            text_color=COLORS["text_main"],
            dropdown_fg_color=COLORS["card_bg"],
            dropdown_text_color=COLORS["text_main"],
        )
        self.workflow_menu.pack(side="left", padx=4)

        ctk.CTkButton(right, text="⚙️ إدارة سير العمل", height=28,
                      fg_color=COLORS["secondary"], hover_color=COLORS["secondary_hover"],
                      text_color=COLORS["secondary_text"],
                      font=ctk.CTkFont(size=11, weight="bold"),
                      command=lambda: self._switch_tab("workflows")).pack(fill="x", padx=15, pady=(0, 10))

        # -- Scheduling --
        sched_label = ctk.CTkLabel(right, text="🕒 جدولة الإرسال", font=ctk.CTkFont(size=13, weight="bold"))
        sched_label.pack(anchor="e", padx=15, pady=(12, 5))

        sched_row = ctk.CTkFrame(right, fg_color="transparent")
        sched_row.pack(fill="x", padx=15, pady=2)

        ctk.CTkLabel(sched_row, text="التاريخ:", font=ctk.CTkFont(size=11)).pack(side="right", padx=(3, 0))
        self.sched_date_entry = ctk.CTkEntry(sched_row, width=95, height=30, corner_radius=6,
                                             placeholder_text="YYYY-MM-DD", justify="center",
                                             font=ctk.CTkFont(size=11))
        self.sched_date_entry.pack(side="right", padx=3)

        ctk.CTkLabel(sched_row, text="الوقت:", font=ctk.CTkFont(size=11)).pack(side="right", padx=(3, 0))
        self.sched_time_entry = ctk.CTkEntry(sched_row, width=60, height=30, corner_radius=6,
                                             placeholder_text="HH:MM", justify="center",
                                             font=ctk.CTkFont(size=11))
        self.sched_time_entry.pack(side="right", padx=3)

        sched_btn_row = ctk.CTkFrame(right, fg_color="transparent")
        sched_btn_row.pack(fill="x", padx=15, pady=3)
        self.btn_schedule = ctk.CTkButton(sched_btn_row, text="⏰ جدولة", width=90, height=32,
                                          fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
                                          font=ctk.CTkFont(size=12, weight="bold"),
                                          command=self._schedule_send)
        self.btn_schedule.pack(side="right", padx=3)
        self.btn_cancel_sched = ctk.CTkButton(sched_btn_row, text="❌ إلغاء", width=80, height=32,
                                              fg_color=COLORS["danger"], hover_color=COLORS["danger_hover"],
                                              font=ctk.CTkFont(size=11),
                                              state="disabled",
                                              command=self._cancel_schedule)
        self.btn_cancel_sched.pack(side="right", padx=3)

        self.sched_status_label = ctk.CTkLabel(right, text="", font=ctk.CTkFont(size=11),
                                               text_color=COLORS["accent"])
        self.sched_status_label.pack(anchor="e", padx=15, pady=(0, 3))

        # -- Progress --
        prog_label = ctk.CTkLabel(right, text="📊 التقدم", font=ctk.CTkFont(size=13, weight="bold"))
        prog_label.pack(anchor="e", padx=15, pady=(10, 5))

        self.progress_bar = ctk.CTkProgressBar(right, height=14, corner_radius=7,
                                               progress_color=COLORS["primary"])
        self.progress_bar.pack(fill="x", padx=15, pady=5)
        self.progress_bar.set(0)

        self.status_label = ctk.CTkLabel(right, text="جاهز...",
                                         font=ctk.CTkFont(size=12),
                                         text_color=COLORS["text_muted"])
        self.status_label.pack(anchor="e", padx=15, pady=(2, 5))

        # -- Quick Counters --
        counter_frame = ctk.CTkFrame(right, fg_color="transparent")
        counter_frame.pack(fill="x", padx=15, pady=(5, 5))
        self.counter_label = ctk.CTkLabel(counter_frame, text="✅ 0 | ❌ 0 | 🚫 0",
                                          font=ctk.CTkFont(size=14, weight="bold"))
        self.counter_label.pack()
        self.total_counts_label = ctk.CTkLabel(counter_frame, text="الإجمالي: 0 | جهات: 0 | مجموعات: 0",
                                               font=ctk.CTkFont(size=11),
                                               text_color=COLORS["text_muted"])
        self.total_counts_label.pack()

        # -- Error Codes Button --
        ctk.CTkButton(right, text="📖 أكواد الأخطاء",
                      font=ctk.CTkFont(size=12),
                      fg_color=COLORS["accent"],
                      hover_color=COLORS["accent_hover"],
                      height=34, corner_radius=8,
                      command=self._show_error_codes).pack(fill="x", padx=15, pady=(8, 12))

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
        self.delay_min_entry.insert(0, str(self.config.get("delay_min", 30)))

        ctk.CTkLabel(delay_row, text="إلى:", font=ctk.CTkFont(size=12)).pack(side="right", padx=(5, 0))
        self.delay_max_entry = ctk.CTkEntry(delay_row, width=70, height=34, corner_radius=8,
                                            justify="center")
        self.delay_max_entry.pack(side="right", padx=5)
        self.delay_max_entry.insert(0, str(self.config.get("delay_max", 120)))

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

        ctk.CTkLabel(header_row, text="📋 سجل العمليات",
                     font=ctk.CTkFont(size=20, weight="bold")).pack(side="right")

        ctk.CTkButton(header_row, text="🗑️ مسح السجل", width=100, height=32,
                      fg_color=COLORS["danger"], hover_color=COLORS["danger_hover"],
                      command=self._clear_log).pack(side="left")

        self.log_textbox = ctk.CTkTextbox(frame, font=ctk.CTkFont(family="Consolas", size=12),
                                          corner_radius=12, state="disabled")
        self.log_textbox.pack(fill="both", expand=True, padx=20, pady=(5, 15))

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

    def log(self, message):
        ts = time.strftime('%H:%M:%S')

        def _do():
            self.log_textbox.configure(state="normal")
            self.log_textbox.insert("end", f"[{ts}] {message}\n")
            self.log_textbox.see("end")
            self.log_textbox.configure(state="disabled")
        self._run_on_ui(_do)
        try:
            os.makedirs(self.log_dir, exist_ok=True)
            with open(self.log_file_path, "a", encoding="utf-8") as f:
                f.write(f"[{ts}] {message}\n")
        except Exception:
            pass

    def _clear_log(self):
        self.log_textbox.configure(state="normal")
        self.log_textbox.delete("1.0", "end")
        self.log_textbox.configure(state="disabled")

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
        self.stat_cards["total"].configure(text=str(total))
        self.stat_cards["success"].configure(text=str(self.sent))
        self.stat_cards["failed"].configure(text=str(self.failed))
        self.stat_cards["invalid"].configure(text=str(self.invalid))
        self.counter_label.configure(text=f"✅ {self.sent} | ❌ {self.failed} | 🚫 {self.invalid}")

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
        """Update contact count label when a file is selected."""
        try:
            if not path:
                path = self.contacts_entry.get()
            if not path or not os.path.exists(path):
                self.contact_count_label.configure(text="")
                return
            from utils.helpers import read_contacts_auto
            contacts = read_contacts_auto(path, default_country_code=self.config.get("default_country_code", "20"))
            count = len(contacts)
            self.contact_count_label.configure(
                text=f"📊 {count} جهة اتصال" if count > 0 else "⚠️ لا توجد جهات اتصال"
            )
        except Exception:
            self.contact_count_label.configure(text="")

    def _open_import_dialog(self):
        win = ctk.CTkToplevel(self)
        win.title("استيراد الأرقام")
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
        ctk.CTkLabel(file_frame, text="اختر الملف:", font=ctk.CTkFont(size=12, weight="bold")).pack(side="right", padx=10)
        file_entry = ctk.CTkEntry(file_frame, textvariable=file_var, height=32, corner_radius=8)
        file_entry.pack(side="right", fill="x", expand=True, padx=10, pady=8)

        def _browse_file():
            path = filedialog.askopenfilename(filetypes=[("CSV/Excel", "*.csv;*.xlsx;*.xls;*.txt")])
            if path:
                file_var.set(path)
                _load_preview()

        ctk.CTkButton(file_frame, text="Browse", width=90, height=32,
                      fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"],
                      command=_browse_file).pack(side="left", padx=10)

        # Settings
        settings_frame = ctk.CTkFrame(win, corner_radius=10)
        settings_frame.pack(fill="x", padx=15, pady=(0, 8))
        ctk.CTkLabel(settings_frame, text="إعدادات", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="e", padx=12, pady=(8, 4))

        settings_row = ctk.CTkFrame(settings_frame, fg_color="transparent")
        settings_row.pack(fill="x", padx=10, pady=(0, 8))
        ctk.CTkCheckBox(settings_row, text="اعتبر أول صف عناوين", variable=header_var,
                        command=lambda: _load_preview()).pack(side="right", padx=6)
        ctk.CTkCheckBox(settings_row, text="فاصل مخصص", variable=custom_delim_var,
                        command=lambda: _load_preview()).pack(side="right", padx=6)
        delim_entry = ctk.CTkEntry(settings_row, textvariable=delim_var, width=60, height=28)
        delim_entry.pack(side="right", padx=6)
        ctk.CTkCheckBox(settings_row, text="إزالة التكرارات", variable=dedup_var).pack(side="right", padx=6)
        ctk.CTkButton(settings_row, text="تحديث المعاينة", height=28,
                      fg_color=COLORS["secondary"], hover_color=COLORS["secondary_hover"],
                      text_color=COLORS["secondary_text"],
                      command=lambda: _load_preview()).pack(side="left", padx=6)

        # Field Mapping
        mapping_frame = ctk.CTkFrame(win, corner_radius=10)
        mapping_frame.pack(fill="x", padx=15, pady=(0, 8))
        ctk.CTkLabel(mapping_frame, text="تعيين الحقول", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="e", padx=12, pady=(8, 4))

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
            "name": _make_field("الاسم", name_var),
            "phone": _make_field("الرقم", phone_var),
            "var1": _make_field("Var1", var1_var),
            "var2": _make_field("Var2", var2_var),
            "var3": _make_field("Var3", var3_var),
            "var4": _make_field("Var4", var4_var),
            "var5": _make_field("Var5", var5_var),
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
            return {
                "name": find(["name", "full", "given", "اسم", "الاسم"]),
                "phone": find(["phone", "mobile", "number", "رقم", "هاتف", "phone 1 - value"]),
                "var1": find(["var1", "var 1", "variable1", "v1", "custom1"]),
                "var2": find(["var2", "var 2", "variable2", "v2", "custom2"]),
                "var3": find(["var3", "var 3", "variable3", "v3", "custom3"]),
                "var4": find(["var4", "var 4", "variable4", "v4", "custom4"]),
                "var5": find(["var5", "var 5", "variable5", "v5", "custom5"]),
            }

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

            messagebox.showinfo("تم", f"تم الاستيراد: {len(contacts)} رقم\nغير صالح: {invalid}")
            win.destroy()

        # Bottom buttons
        btn_row = ctk.CTkFrame(win, fg_color="transparent")
        btn_row.pack(fill="x", padx=15, pady=(0, 15))
        ctk.CTkButton(btn_row, text="إلغاء", width=90, height=32,
                      fg_color=COLORS["secondary"], hover_color=COLORS["secondary_hover"],
                      text_color=COLORS["secondary_text"],
                      command=win.destroy).pack(side="left", padx=6)
        ctk.CTkButton(btn_row, text="استيراد", width=100, height=32,
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
    def _build_tab_workflows(self):
        frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.tab_frames["workflows"] = frame

        header = ctk.CTkLabel(frame, text="🧭 سير العمل (Workflows)",
                              font=ctk.CTkFont(size=20, weight="bold"))
        header.pack(anchor="e", padx=25, pady=(20, 10))

        body = ctk.CTkFrame(frame, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=20, pady=10)
        body.grid_columnconfigure(0, weight=1)
        body.grid_columnconfigure(1, weight=2)
        body.grid_rowconfigure(0, weight=1)

        # Left: Workflows list
        left = ctk.CTkFrame(body, corner_radius=12, fg_color=COLORS["card_bg"])
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=5)
        ctk.CTkLabel(left, text="القائمة", font=ctk.CTkFont(size=13, weight="bold"),
                     text_color=COLORS["text_main"]).pack(anchor="e", padx=12, pady=(10, 8))

        self.workflows_list_frame = ctk.CTkScrollableFrame(left, fg_color="transparent")
        self.workflows_list_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Right: Editor
        right = ctk.CTkFrame(body, corner_radius=12, fg_color=COLORS["card_bg"])
        right.grid(row=0, column=1, sticky="nsew", padx=(8, 0), pady=5)
        right.grid_columnconfigure(0, weight=1)

        name_row = ctk.CTkFrame(right, fg_color="transparent")
        name_row.pack(fill="x", padx=12, pady=(10, 6))
        ctk.CTkLabel(name_row, text="اسم سير العمل:", font=ctk.CTkFont(size=12)).pack(side="right", padx=4)
        self.workflow_name_entry = ctk.CTkEntry(name_row, height=30, corner_radius=6,
                                                fg_color=COLORS["bg_dark"], text_color=COLORS["text_main"],
                                                border_color=COLORS["border"])
        self.workflow_name_entry.pack(side="right", fill="x", expand=True, padx=4)

        # Steps list
        ctk.CTkLabel(right, text="الخطوات", font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=COLORS["text_main"]).pack(anchor="e", padx=12, pady=(4, 4))
        self.workflow_steps_frame = ctk.CTkScrollableFrame(right, height=140, fg_color="transparent")
        self.workflow_steps_frame.pack(fill="x", padx=12, pady=(0, 6))

        # Step editor
        ctk.CTkLabel(right, text="محرر الخطوة", font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=COLORS["text_main"]).pack(anchor="e", padx=12, pady=(6, 4))
        self.workflow_step_editor = RichTextFrame(right, colors=COLORS, fg_color=COLORS["bg_dark"], corner_radius=10)
        self.workflow_step_editor.pack(fill="x", padx=12, pady=(0, 6))

        self.workflow_step_attachments = AttachmentManager(right, colors=COLORS, fg_color=COLORS["bg_dark"], corner_radius=10)
        self.workflow_step_attachments.pack(fill="x", padx=12, pady=(0, 6))

        delay_row = ctk.CTkFrame(right, fg_color="transparent")
        delay_row.pack(fill="x", padx=12, pady=(0, 6))
        ctk.CTkLabel(delay_row, text="تأخير الخطوة (ثواني):", font=ctk.CTkFont(size=11)).pack(side="right", padx=4)
        self.step_delay_min_entry = ctk.CTkEntry(delay_row, width=60, height=28, corner_radius=6,
                                                 fg_color=COLORS["bg_dark"], text_color=COLORS["text_main"],
                                                 border_color=COLORS["border"], placeholder_text="min")
        self.step_delay_min_entry.pack(side="right", padx=4)
        self.step_delay_max_entry = ctk.CTkEntry(delay_row, width=60, height=28, corner_radius=6,
                                                 fg_color=COLORS["bg_dark"], text_color=COLORS["text_main"],
                                                 border_color=COLORS["border"], placeholder_text="max")
        self.step_delay_max_entry.pack(side="right", padx=4)

        step_btn_row = ctk.CTkFrame(right, fg_color="transparent")
        step_btn_row.pack(fill="x", padx=12, pady=(0, 6))
        ctk.CTkButton(step_btn_row, text="➕ إضافة/تحديث خطوة", height=30,
                      fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"],
                      font=ctk.CTkFont(size=12, weight="bold"),
                      command=self._add_or_update_step).pack(side="right", padx=4)
        ctk.CTkButton(step_btn_row, text="مسح الخطوة", height=30,
                      fg_color=COLORS["secondary"], hover_color=COLORS["secondary_hover"],
                      text_color=COLORS["secondary_text"],
                      font=ctk.CTkFont(size=12),
                      command=self._clear_step_editor).pack(side="right", padx=4)

        wf_btn_row = ctk.CTkFrame(right, fg_color="transparent")
        wf_btn_row.pack(fill="x", padx=12, pady=(0, 10))
        ctk.CTkButton(wf_btn_row, text="💾 حفظ سير العمل", height=34,
                      fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
                      font=ctk.CTkFont(size=12, weight="bold"),
                      command=self._save_workflow).pack(side="right", padx=4)
        ctk.CTkButton(wf_btn_row, text="🆕 جديد", height=34,
                      fg_color=COLORS["secondary"], hover_color=COLORS["secondary_hover"],
                      text_color=COLORS["secondary_text"],
                      font=ctk.CTkFont(size=12, weight="bold"),
                      command=self._new_workflow).pack(side="right", padx=4)
        ctk.CTkButton(wf_btn_row, text="✅ استخدام في الإرسال", height=34,
                      fg_color=COLORS["success"], hover_color=COLORS["primary_hover"],
                      font=ctk.CTkFont(size=12, weight="bold"),
                      command=self._use_workflow_in_main).pack(side="left", padx=4)

        self.workflow_steps = []
        self.workflow_edit_id = None
        self.workflow_step_edit_index = None
        self._refresh_workflow_list()
        self._render_workflow_steps()

    def _get_workflow_names(self):
        workflows = self.workflow_manager.get_all()
        self.workflow_cache = {w["name"]: w["id"] for w in workflows}
        names = list(self.workflow_cache.keys())
        return names if names else ["—"]

    def _refresh_workflow_menu(self):
        if not hasattr(self, "workflow_menu"):
            return
        names = self._get_workflow_names()
        self.workflow_menu.configure(values=names)
        cur = self.workflow_var.get().strip()
        if cur not in names:
            self.workflow_var.set(names[0])

    def _refresh_workflow_list(self):
        if not hasattr(self, "workflows_list_frame"):
            return
        for w in self.workflows_list_frame.winfo_children():
            w.destroy()
        workflows = self.workflow_manager.get_all()
        if not workflows:
            ctk.CTkLabel(self.workflows_list_frame, text="لا يوجد سير عمل محفوظ.",
                         font=("Segoe UI", 12), text_color=COLORS["text_muted"]).pack(pady=20)
            self._refresh_workflow_menu()
            return
        for wf in workflows:
            card = ctk.CTkFrame(self.workflows_list_frame, fg_color=COLORS["bg_dark"], corner_radius=10)
            card.pack(fill="x", pady=5, padx=5)

            head = ctk.CTkFrame(card, fg_color="transparent")
            head.pack(fill="x", padx=8, pady=(6, 0))
            ctk.CTkLabel(head, text=wf["name"], font=("Segoe UI", 12, "bold"),
                         text_color=COLORS["primary"]).pack(side="right")
            ctk.CTkLabel(head, text=f"خطوات: {wf['steps_count']}", font=("Segoe UI", 10),
                         text_color=COLORS["text_muted"]).pack(side="left")

            actions = ctk.CTkFrame(card, fg_color="transparent")
            actions.pack(fill="x", padx=8, pady=(4, 8))
            ctk.CTkButton(actions, text="فتح", width=50, height=24,
                          fg_color=COLORS["secondary"], hover_color=COLORS["secondary_hover"],
                          text_color=COLORS["secondary_text"],
                          command=lambda i=wf["id"]: self._load_workflow_into_editor(i)).pack(side="left", padx=2)
            ctk.CTkButton(actions, text="حذف", width=50, height=24,
                          fg_color=COLORS["danger"], hover_color=COLORS["danger_hover"],
                          text_color="#FFFFFF",
                          command=lambda i=wf["id"]: self._delete_workflow(i)).pack(side="left", padx=2)
        self._refresh_workflow_menu()

    def _render_workflow_steps(self):
        if not hasattr(self, "workflow_steps_frame"):
            return
        for w in self.workflow_steps_frame.winfo_children():
            w.destroy()
        if not self.workflow_steps:
            ctk.CTkLabel(self.workflow_steps_frame, text="لا توجد خطوات بعد.",
                         font=("Segoe UI", 11), text_color=COLORS["text_muted"]).pack(pady=10)
            return
        for idx, step in enumerate(self.workflow_steps):
            row = ctk.CTkFrame(self.workflow_steps_frame, fg_color="transparent")
            row.pack(fill="x", pady=2)
            preview = (step.get("body") or "").strip().replace("\n", " ")
            if len(preview) > 45:
                preview = preview[:42] + "..."
            att_count = len(step.get("attachments") or [])
            delay_txt = f"{step.get('delay_min', 0)}-{step.get('delay_max', 0)}s"
            ctk.CTkLabel(row, text=f"خطوة {idx+1}: {preview}",
                         font=("Segoe UI", 11), anchor="e").pack(side="right", padx=4)
            ctk.CTkLabel(row, text=f"مرفقات:{att_count} | تأخير:{delay_txt}",
                         font=("Segoe UI", 10), text_color=COLORS["text_muted"]).pack(side="left", padx=4)
            ctk.CTkButton(row, text="تعديل", width=50, height=24,
                          fg_color=COLORS["secondary"], hover_color=COLORS["secondary_hover"],
                          text_color=COLORS["secondary_text"],
                          command=lambda i=idx: self._edit_step(i)).pack(side="left", padx=2)
            ctk.CTkButton(row, text="حذف", width=50, height=24,
                          fg_color=COLORS["danger"], hover_color=COLORS["danger_hover"],
                          text_color="#FFFFFF",
                          command=lambda i=idx: self._delete_step(i)).pack(side="left", padx=2)

    def _load_workflow_into_editor(self, workflow_id):
        wf = self.workflow_manager.get(workflow_id)
        if not wf:
            return
        self.workflow_edit_id = wf["id"]
        self.workflow_name_entry.delete(0, "end")
        self.workflow_name_entry.insert(0, wf["name"])
        self.workflow_steps = wf.get("steps") or []
        self.workflow_step_edit_index = None
        self._clear_step_editor()
        self._render_workflow_steps()

    def _new_workflow(self):
        self.workflow_edit_id = None
        self.workflow_name_entry.delete(0, "end")
        self.workflow_steps = []
        self.workflow_step_edit_index = None
        self._clear_step_editor()
        self._render_workflow_steps()

    def _save_workflow(self):
        name = self.workflow_name_entry.get().strip()
        steps = self.workflow_steps or []
        if not name:
            messagebox.showwarning("تنبيه", "يرجى إدخال اسم سير العمل.")
            return
        if not steps:
            messagebox.showwarning("تنبيه", "يرجى إضافة خطوة واحدة على الأقل.")
            return
        ok, wf_id_or_msg = self.workflow_manager.save(name, steps, self.workflow_edit_id)
        if not ok:
            messagebox.showerror("خطأ", str(wf_id_or_msg))
            return
        self.workflow_edit_id = wf_id_or_msg
        self._refresh_workflow_list()
        self._refresh_workflow_menu()
        messagebox.showinfo("تم", "تم حفظ سير العمل.")

    def _delete_workflow(self, workflow_id):
        if messagebox.askyesno("تأكيد", "هل تريد حذف سير العمل؟"):
            self.workflow_manager.delete(workflow_id)
            if self.workflow_edit_id == workflow_id:
                self._new_workflow()
            self._refresh_workflow_list()
            self._refresh_workflow_menu()

    def _add_or_update_step(self):
        body = self.workflow_step_editor.get_text()
        attachments = self.workflow_step_attachments.get_attachments()
        delay_min = self.step_delay_min_entry.get().strip()
        delay_max = self.step_delay_max_entry.get().strip()
        try:
            delay_min = int(delay_min) if delay_min else 0
            delay_max = int(delay_max) if delay_max else 0
        except ValueError:
            messagebox.showerror("خطأ", "يرجى إدخال تأخير صحيح بالأرقام.")
            return
        if not body and not attachments:
            messagebox.showwarning("تنبيه", "الخطوة فارغة. أضف رسالة أو مرفقات.")
            return
        step_data = {
            "body": body,
            "attachments": attachments,
            "delay_min": delay_min,
            "delay_max": delay_max,
        }
        if self.workflow_step_edit_index is None:
            self.workflow_steps.append(step_data)
        else:
            self.workflow_steps[self.workflow_step_edit_index] = step_data
        self.workflow_step_edit_index = None
        self._clear_step_editor()
        self._render_workflow_steps()

    def _edit_step(self, index):
        if index < 0 or index >= len(self.workflow_steps):
            return
        step = self.workflow_steps[index]
        self.workflow_step_edit_index = index
        self.workflow_step_editor.set_text(step.get("body", ""))
        self.workflow_step_attachments.clear()
        for att in step.get("attachments") or []:
            path = att.get("path")
            type_ = att.get("type", "document")
            caption = att.get("caption", "")
            if path:
                self.workflow_step_attachments._add_item(path, type_)
                # set caption if exists
                try:
                    self.workflow_step_attachments.attachments[-1].caption_entry.delete(0, "end")
                    self.workflow_step_attachments.attachments[-1].caption_entry.insert(0, caption)
                except Exception:
                    pass
        self.step_delay_min_entry.delete(0, "end")
        self.step_delay_min_entry.insert(0, str(step.get("delay_min", 0)))
        self.step_delay_max_entry.delete(0, "end")
        self.step_delay_max_entry.insert(0, str(step.get("delay_max", 0)))

    def _delete_step(self, index):
        if index < 0 or index >= len(self.workflow_steps):
            return
        self.workflow_steps.pop(index)
        self._render_workflow_steps()

    def _clear_step_editor(self):
        self.workflow_step_editor.set_text("")
        self.workflow_step_attachments.clear()
        self.step_delay_min_entry.delete(0, "end")
        self.step_delay_max_entry.delete(0, "end")

    def _use_workflow_in_main(self):
        name = self.workflow_name_entry.get().strip()
        if not name:
            messagebox.showwarning("تنبيه", "اختر سير عمل أولاً.")
            return
        self.use_workflow_var.set(True)
        self.workflow_var.set(name)
        self._switch_tab("main")

    def _get_selected_workflow(self):
        if not hasattr(self, "workflow_var"):
            return None
        name = self.workflow_var.get().strip()
        if not name or name == "—":
            return None
        return self.workflow_manager.get_by_name(name)

    # ═══════════════════════════════════════════════════════════════════════
    #  SCHEDULING
    # ═══════════════════════════════════════════════════════════════════════
    def _schedule_send(self):
        date_str = self.sched_date_entry.get().strip()
        time_str = self.sched_time_entry.get().strip()
        if not date_str or not time_str:
            messagebox.showwarning("تنبيه", "يرجى إدخال التاريخ (YYYY-MM-DD) والوقت (HH:MM).")
            return
        try:
            target = datetime.datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
        except ValueError:
            messagebox.showerror("خطأ", "صيغة التاريخ أو الوقت غير صحيحة.\nاستخدم: YYYY-MM-DD HH:MM")
            return

        success, msg = self.scheduler.schedule(target, self._scheduled_start_callback)
        if success:
            self.log(f"⏰ {msg}")
            self.btn_schedule.configure(state="disabled")
            self.btn_cancel_sched.configure(state="normal")
            self.sched_status_label.configure(text=f"⏰ مجدول: {date_str} {time_str}")
            # Start countdown updater
            self._update_schedule_countdown()
        else:
            messagebox.showwarning("تنبيه", msg)

    def _cancel_schedule(self):
        self.scheduler.cancel()
        self.btn_schedule.configure(state="normal")
        self.btn_cancel_sched.configure(state="disabled")
        self.sched_status_label.configure(text="")
        self.log("❌ تم إلغاء الجدولة.")

    def _update_schedule_countdown(self):
        if not self.scheduler.is_scheduled:
            self.btn_schedule.configure(state="normal")
            self.btn_cancel_sched.configure(state="disabled")
            self.sched_status_label.configure(text="")
            return
        remaining = self.scheduler.get_remaining_text()
        if remaining:
            self.sched_status_label.configure(text=f"⏳ متبقي: {remaining}")
        self.after(1000, self._update_schedule_countdown)

    def _scheduled_start_callback(self):
        """Called by the scheduler when the scheduled time arrives."""
        self.log("⏰ حان موعد الإرسال المجدول!")
        self._run_on_ui(lambda: self.sched_status_label.configure(text=""))
        self._run_on_ui(lambda: self.btn_schedule.configure(state="normal"))
        self._run_on_ui(lambda: self.btn_cancel_sched.configure(state="disabled"))
        self._run_on_ui(self._start_thread)

    def _start_thread(self):
        try:
            self._start_action()
        except Exception as e:
            self.report_error("ERR-99", "خطأ غير متوقع أثناء بدء الإرسال.", detail=str(e), dialog=True)

    # ═══════════════════════════════════════════════════════════════════════
    #  ANALYTICS TAB
    # ═══════════════════════════════════════════════════════════════════════
    def _build_tab_analytics(self):
        frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.tab_frames["analytics"] = frame

        header = ctk.CTkLabel(frame, text="📊 التحليلات وسجل الحملات",
                              font=ctk.CTkFont(size=20, weight="bold"))
        header.pack(anchor="e", padx=25, pady=(20, 10))

        # Overall Stats
        stats_frame = ctk.CTkFrame(frame, corner_radius=16, fg_color=COLORS["card_bg"])
        stats_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        self.analytics_labels = {}
        
        # Grid layout for stats
        stats_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)
        
        items = [("total_campaigns", "حملات"), ("total_messages", "رسائل"), 
                 ("overall_success_rate", "نجاح %"), ("total_duration_minutes", "دقيقة")]
        
        for i, (key, title) in enumerate(items):
            f = ctk.CTkFrame(stats_frame, fg_color="transparent")
            f.grid(row=0, column=i, pady=20)
            ctk.CTkLabel(f, text=title, font=("Segoe UI", 13), text_color=COLORS["text_muted"]).pack()
            l = ctk.CTkLabel(f, text="0", font=("Segoe UI", 24, "bold"), text_color=COLORS["primary"])
            l.pack()
            self.analytics_labels[key] = l

        # Campaign History List
        ctk.CTkLabel(frame, text="سجل الحملات السابقة:", 
                     font=("Segoe UI", 14, "bold"), text_color=COLORS["text_muted"]).pack(anchor="e", padx=30, pady=(5, 5))
        
        self.campaigns_list = ctk.CTkScrollableFrame(frame, corner_radius=16, fg_color=COLORS["bg_dark"])
        self.campaigns_list.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        # Refresh Button
        ctk.CTkButton(frame, text="🔄 تحديث البيانات", height=32,
                      fg_color=COLORS["info"], command=self._refresh_analytics).pack(padx=20, pady=10)

        # Initial Load
        self._refresh_analytics()

    def _refresh_analytics(self):
        # Update Stats
        stats = self.campaign_manager.get_aggregate_stats()
        self.analytics_labels["total_campaigns"].configure(text=str(stats["total_campaigns"]))
        self.analytics_labels["total_messages"].configure(text=str(stats["total_messages"]))
        self.analytics_labels["overall_success_rate"].configure(text=f"{stats['overall_success_rate']}%")
        self.analytics_labels["total_duration_minutes"].configure(text=str(stats["total_duration_minutes"]))

        # Update List
        for w in self.campaigns_list.winfo_children():
            w.destroy()
            
        for c in self.campaign_manager.get_all():
            row = ctk.CTkFrame(self.campaigns_list, corner_radius=6)
            row.pack(fill="x", pady=2, padx=2)
            
            # Left: Action buttons
            btn_frame = ctk.CTkFrame(row, fg_color="transparent", width=100)
            btn_frame.pack(side="left", padx=5)
            
            ctk.CTkButton(btn_frame, text="csv", width=40, height=24, font=ctk.CTkFont(size=10),
                          fg_color=COLORS["success"], 
                          command=lambda p=c.get("csv_path"): self._open_csv(p)).pack(side="left", padx=2)
            
            ctk.CTkButton(btn_frame, text="🗑️", width=30, height=24, font=ctk.CTkFont(size=10),
                          fg_color=COLORS["danger"], hover_color=COLORS["danger_hover"],
                          command=lambda cid=c["id"]: self._delete_campaign(cid)).pack(side="left", padx=2)

            # Right: Info
            info_frame = ctk.CTkFrame(row, fg_color="transparent")
            info_frame.pack(side="right", fill="x", expand=True, padx=10, pady=5)
            
            name = c.get("name") or f"حملة #{c['id']}"
            date = c.get("date")
            rate = c.get("success_rate", 0)
            total = c.get("total", 0)
            
            header = ctk.CTkLabel(info_frame, text=f"{name} | {date}", 
                                  font=ctk.CTkFont(size=12, weight="bold"), anchor="e")
            header.pack(fill="x")
            
            sub = ctk.CTkLabel(info_frame, text=f"نجاح: {rate}% | إجمالي: {total} رسالة", 
                               font=ctk.CTkFont(size=11), text_color=COLORS["text_muted"], anchor="e")
            sub.pack(fill="x")

    def _delete_campaign(self, campaign_id):
        if messagebox.askyesno("تأكيد", "هل تريد حذف سجل هذه الحملة؟"):
            self.campaign_manager.delete_campaign(campaign_id)
            self._refresh_analytics()

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
        self.send_text_var.set(self.config.get("send_text_with_image", True))
        self.bg_mode_var.set(self.config.get("background_mode", False))
        self.spin_text_var.set(self.config.get("enable_spintax", True))
        if hasattr(self, "use_valid_after_check_var"):
            self.use_valid_after_check_var.set(self.config.get("use_valid_after_check", False))
        if hasattr(self, "use_workflow_var"):
            self.use_workflow_var.set(self.config.get("use_workflow", False))
        if hasattr(self, "workflow_var"):
            last_wf = self.config.get("last_workflow", "")
            if last_wf:
                self.workflow_var.set(last_wf)

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
        if hasattr(self, "use_workflow_var"):
            self.config.set("use_workflow", self.use_workflow_var.get())
        if hasattr(self, "workflow_var"):
            self.config.set("last_workflow", self.workflow_var.get())
        # Save window size
        self.config.set("window_width", self.winfo_width())
        self.config.set("window_height", self.winfo_height())
        self.config.save()

    def _on_close(self):
        self._save_current_state()
        self.scheduler.cancel()
        if self.bot:
            self.bot.close()
        self.destroy()


    def _close_progress_window(self):
        if self.progress_win and self.progress_win.winfo_exists():
            self.progress_win.destroy()
        self.progress_win = None
        self.progress_tree = None
        self.progress_count_label = None
        self.progress_status_label = None
        self.progress_bar_small = None
        self.progress_state_label = None
        self.progress_metric_labels = {}

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
            if hasattr(self, "pause_btn"):
                self.pause_btn.configure(text="Pause")
            self._set_progress_status("Resumed...")
        else:
            self.pause_event.set()
            self.is_paused = True
            if hasattr(self, "pause_btn"):
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
    def _login_action(self):
        if self.bot and self.bot.driver:
            self.bot.background_mode = False
            self.bot.bring_to_front()
            if self.bot.is_logged_in():
                self._set_session_status("الحالة: متصل", COLORS["success"])
            else:
                self._set_session_status("الحالة: غير متصل", COLORS["warning"])
            self.log("المتصفح مفتوح بالفعل.")
            return

        def run_login():
            try:
                self._set_session_status("الحالة: جاري فتح المتصفح...", COLORS["info"])
                self.log("جاري فتح المتصفح...")
                active_profile = self.config.get("profile_name", "Default")
                profile_proxies = self.config.get("profile_proxies", {})
                proxy_config = profile_proxies.get(active_profile, {"enabled": False})
                self.bot = WhatsAppBot(self.user_data_dir, proxy_config=proxy_config)
                self.bot.open_whatsapp()
                self.bot.background_mode = False
                self.bot.bring_to_front()
                self._set_session_status("الحالة: في انتظار تسجيل الدخول...", COLORS["warning"])
                self.log("يرجى فتح واتساب على الهاتف ومسح QR لتسجيل الدخول...")
                self.log("💡 تلميح: يرجى الانتظار 3 ثوانٍ بعد ظهور الباركود قبل مسحه بالهاتف لضمان استقرار الاتصال من المرة الأولى.")
                
                login_status = self.bot.wait_for_login(timeout=900)
                if login_status == "SUCCESS":
                    self.log("✅ تم تسجيل الدخول بنجاح!")
                    self._set_session_status("الحالة: متصل", COLORS["success"])
                    self._show_dialog("info", "تم", "تم تسجيل الدخول. يمكنك الآن الضغط على 'بدء الإرسال'.")
                    if self.pending_start_payload:
                        self.log("🚀 بدء الإرسال تلقائياً بعد تسجيل الدخول.")
                        self._run_on_ui(self._run_pending_start)
                    if self.pending_check_contacts:
                        pending_contacts = self.pending_check_contacts
                        self.pending_check_contacts = None
                        self.log("🔍 بدء فحص الأرقام تلقائياً بعد تسجيل الدخول.")
                        self._run_on_ui(lambda: self._check_numbers_action(pending_contacts))
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
        if not pending:
            return
        if isinstance(pending, dict) and pending.get("mode") == "workflow":
            wf = self.workflow_manager.get(pending.get("workflow_id"))
            if not wf:
                self.report_error("ERR-05", "سير العمل غير موجود.", dialog=True)
                return
            self._begin_send_workflow(pending.get("contacts", []), wf)
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
        contacts_input = self.contacts_entry.get().strip()
        contacts = []

        # 1. Check Group
        if contacts_input.startswith("[GROUP:") and contacts_input.endswith("]"):
            group_name = contacts_input[7:-1]
            g = self.contacts_mgr.get_by_name(group_name)
            if not g or not g.get("contacts"):
                self.report_error("ERR-03", f"المجموعة '{group_name}' فارغة أو غير موجودة.", dialog=True)
                return None
            contacts = g["contacts"]
            self.log(f"تم اختيار المجموعة: {group_name} ({len(contacts)} جهة اتصال)")
            self._update_total_counts(total=len(contacts), contacts_count=len(contacts), groups_count=1)
            return contacts

        # 2. Check File
        if contacts_input and os.path.exists(contacts_input):
            contacts = read_contacts_auto(contacts_input, default_country_code=self.config.get("default_country_code", "20"))
            if not contacts:
                self.report_error("ERR-06", "الملف فارغ أو لا يحتوي على أرقام صحيحة.", dialog=True)
                return None
            self.log(f"تم تحميل {len(contacts)} جهة اتصال من الملف.")
            self._update_total_counts(total=len(contacts), contacts_count=len(contacts), groups_count=0)
            return contacts

        self.report_error("ERR-05", "يرجى اختيار ملف أرقام صحيح أو مجموعة.", dialog=True)
        return None

    def _log_preflight(self, contacts, msg_template, attachments):
        msg_len = len(msg_template) if msg_template else 0
        if attachments:
            types = ", ".join([a.get("type", "file") for a in attachments])
        else:
            types = "بدون مرفقات"
        self.log(f"🧪 فحص قبل الإرسال: جهات={len(contacts)} | رسالة={msg_len} حرف | مرفقات={types}")

    def _log_preflight_workflow(self, contacts, workflow):
        steps_count = len(workflow.get("steps") or [])
        self.log(f"🧭 سير العمل: {workflow.get('name','')} | خطوات={steps_count} | جهات={len(contacts)}")

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

    def _begin_send(self, contacts, msg_template, attachments):
        if self.is_running:
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
        if hasattr(self, "pause_btn"):
            self.pause_btn.configure(text="Pause")

        self._open_progress_window_blind(len(contacts), mode="send")

        threading.Thread(
            target=self._run_automation,
            args=(contacts, msg_template, attachments),
            daemon=True
        ).start()

    def _begin_send_workflow(self, contacts, workflow):
        if self.is_running:
            return

        if self.bg_mode_var.get():
            self.bot.background_mode = True
            self.bot.minimize()
            self.log("🖥️ وضع الخلفية مفعل — المتصفح مُصغّر.")
        else:
            self.bot.background_mode = False
            self.bot.bring_to_front()

        self.is_running = True
        self.stop_event.clear()
        self.pause_event.clear()
        self.is_paused = False

        self._log_preflight_workflow(contacts, workflow)

        self.btn_start.configure(state="disabled")
        self.btn_stop.configure(state="normal")
        if hasattr(self, "btn_check"):
            self.btn_check.configure(state="disabled")
        self.progress_bar.set(0)
        self.status_label.configure(text="جاري العمل...")
        if hasattr(self, "pause_btn"):
            self.pause_btn.configure(text="Pause")

        self._open_progress_window_blind(len(contacts), mode="workflow")

        threading.Thread(
            target=self._run_workflow_automation,
            args=(contacts, workflow),
            daemon=True
        ).start()

    def _start_action(self):
        # Workflow mode
        if hasattr(self, "use_workflow_var") and self.use_workflow_var.get():
            workflow = self._get_selected_workflow()
            if not workflow or not workflow.get("steps"):
                self.report_error("ERR-05", "يرجى اختيار سير عمل يحتوي على خطوات.", dialog=True)
                return
            contacts = self._get_contacts_from_input()
            if not contacts:
                return
            self._save_current_state()

            if not self.bot or not self.bot.driver:
                auto_open = self.config.get("auto_open_login", True)
                if auto_open or messagebox.askyesno("تنبيه", "المتصفح غير مفتوح. هل تريد فتحه الآن؟"):
                    self.pending_start_payload = {
                        "mode": "workflow",
                        "contacts": contacts,
                        "workflow_id": workflow["id"],
                    }
                    self._set_session_status("الحالة: جاري فتح المتصفح...", COLORS["info"])
                    self._login_action()
                return

            if not self.bot.is_logged_in():
                self.bot.bring_to_front()
                self.report_error("ERR-21", dialog=True, level="warning")
                return

            self._set_session_status("الحالة: متصل", COLORS["success"])
            self._begin_send_workflow(contacts, workflow)
            return

        # Normal mode
        msg_template, attachments = self._prepare_content()
        if msg_template is None and attachments is None:
            return  # Error reported

        contacts = self._get_contacts_from_input()
        if not contacts:
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
                if hasattr(self, "pause_btn"):
                    self.pause_btn.configure(text="Pause")
            self.log("🛑 طلب إيقاف...")

    def _map_bot_error(self, res):
        if not res:
            return "ERR-99", "خطأ غير معروف.", None
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
            "ERR_ATTACH_BTN_NOT_FOUND":    ("ERR-06", "زر الإرفاق غير موجود.", None),
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
    def _run_workflow_automation(self, contacts, workflow):
        if not self.bot:
            return

        self.sent = 0
        self.failed = 0
        self.invalid = 0
        self.results_log = []

        total = len(contacts)
        start_time = datetime.datetime.now()

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
            batch_size, pause_min, pause_max, delay_min, delay_max = 50, 300, 600, 10, 20
            max_retries, retry_delay_min, retry_delay_max, max_consecutive_failures = 2, 3, 6, 5

        self.log(f"🧭 بدء سير العمل: {workflow.get('name','')} | جهات: {total}")
        steps = workflow.get("steps") or []
        consecutive_failures = 0

        retryable_errors = {
            "ERR_TIMEOUT",
            "ERR_CHAT_INPUT_NOT_FOUND",
            "ERR_ATTACH_BTN_NOT_FOUND",
            "ERR_FILE_INPUT_NOT_FOUND",
            "ERR_SEND_BTN_NOT_FOUND",
            "ERR_SEND_BTN_TIMEOUT",
            "ERR_TEXT_SEND",
        }

        for i, c in enumerate(contacts):
            if self.stop_event.is_set():
                break
            while self.pause_event.is_set() and not self.stop_event.is_set():
                time.sleep(0.3)

            if i > 0 and i % batch_size == 0:
                pause_time = random.uniform(pause_min, pause_max)
                self.log(f"⏸ استراحة لمدة {int(pause_time)} ثانية...")
                time.sleep(pause_time)

            phone = c.get("phone")
            name = c.get("name", "عميل")

            processed = i + 1
            self._run_on_ui(lambda p=processed, t=total, n=name: self.status_label.configure(text=f"جاري الإرسال {p}/{t} إلى {n}..."))
            self._run_on_ui(lambda p=processed, t=total: self.progress_bar.set(p / t))
            elapsed = (datetime.datetime.now() - start_time).total_seconds()
            eta = None
            if processed > 0 and total > processed:
                eta = (elapsed / processed) * (total - processed)
            self._update_progress_header_blind(processed, total, phone, name, eta)

            if not phone:
                self.invalid += 1
                self.results_log.append({"phone": "N/A", "name": name, "status": "بدون واتساب", "error_code": "ERR-00", "timestamp": datetime.datetime.now()})
                self._add_progress_row_blind(["N/A", name, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "بدون رقم", "بيانات الرقم ناقصة"], tag="invalid")
                self._run_on_ui(self._update_stats)
                self._update_progress_header_blind(processed, total, phone, name, eta)
                continue

            if not self.bot.is_logged_in():
                self.report_error("ERR-21", dialog=True, level="warning")
                break

            contact_status = "SUCCESS"
            contact_error = "-"

            for s_idx, step in enumerate(steps):
                if self.stop_event.is_set():
                    contact_status = "STOPPED"
                    break

                body = step.get("body", "")
                step_attachments = step.get("attachments") or []
                if not body and not step_attachments:
                    continue

                msg_for_contact = self._apply_template(body, c)
                atts_for_contact = self._format_attachments_for_contact(step_attachments, c)
                segments = self._split_messages(msg_for_contact)
                primary_msg = segments[0] if segments else msg_for_contact
                extra_msgs = segments[1:] if segments else []

                res = None
                for attempt in range(max_retries + 1):
                    res = self.bot.send_message(
                        phone=phone,
                        name=name,
                        message_template=primary_msg,
                        extra_messages=extra_msgs,
                        attachments=atts_for_contact,
                        stop_event=self.stop_event,
                        send_text_with_image=self.send_text_var.get()
                    )
                    if res in ("SUCCESS", "INVALID", "STOPPED"):
                        break
                    is_retryable = res in retryable_errors or str(res).startswith("ERR_ATTACH_") or str(res).startswith("ERR_GENERAL")
                    if attempt < max_retries and is_retryable:
                        wait_s = random.uniform(retry_delay_min, retry_delay_max)
                        self.log(f"🔁 إعادة محاولة خطوة ({attempt + 1}/{max_retries}) بعد {int(wait_s)}ث | {phone} | {res}")
                        time.sleep(wait_s)
                        continue
                    break

                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                step_label = f"Step {s_idx + 1}"

                if res == "SUCCESS":
                    self._add_progress_row_blind([phone, f"{name} / {step_label}", timestamp, "تم", "تم إرسال الخطوة"], tag="success")
                elif res == "INVALID":
                    self._add_progress_row_blind([phone, f"{name} / {step_label}", timestamp, "بدون واتساب", "الرقم غير صالح أو لا يستخدم واتساب"], tag="invalid")
                    contact_status = "INVALID"
                    contact_error = "ERR-20"
                    break
                elif res == "STOPPED":
                    self._add_progress_row_blind([phone, f"{name} / {step_label}", timestamp, "توقف", "تم إيقاف العملية"], tag="stopped")
                    contact_status = "STOPPED"
                    break
                else:
                    self._add_progress_row_blind([phone, f"{name} / {step_label}", timestamp, "فشل", str(res)], tag="failed")
                    contact_status = "FAILED"
                    contact_error = res
                    break

                try:
                    s_min = int(step.get("delay_min", 0) or 0)
                    s_max = int(step.get("delay_max", 0) or 0)
                except ValueError:
                    s_min, s_max = 0, 0
                if s_max > 0:
                    time.sleep(random.uniform(s_min, max(s_min, s_max)))

            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if contact_status == "SUCCESS":
                self.sent += 1
                self.results_log.append({"phone": phone, "name": name, "status": "نجاح", "error_code": "-", "timestamp": timestamp})
                consecutive_failures = 0
            elif contact_status == "INVALID":
                self.invalid += 1
                self.results_log.append({"phone": phone, "name": name, "status": "بدون واتساب", "error_code": "ERR-20", "timestamp": timestamp})
                consecutive_failures = 0
            elif contact_status == "STOPPED":
                self.results_log.append({"phone": phone, "name": name, "status": "توقف", "error_code": "-", "timestamp": timestamp})
                break
            else:
                self.failed += 1
                err_code = contact_error if str(contact_error).startswith("ERR") else "ERR-UNKNOWN"
                self.results_log.append({"phone": phone, "name": name, "status": "فشل", "error_code": err_code, "timestamp": timestamp})
                consecutive_failures += 1
                if consecutive_failures >= max_consecutive_failures:
                    self.log(f"⛔ تم الإيقاف تلقائيًا بعد {consecutive_failures} فشل متتالي لتقليل المخاطر.")
                    self.stop_event.set()
                    break

            self._run_on_ui(self._update_stats)
            self._update_progress_header_blind(processed, total, phone, name, eta)
            time.sleep(random.uniform(delay_min, delay_max))

        end_time = datetime.datetime.now()
        duration = end_time - start_time
        csv_path = self._generate_final_report(duration)
        self.last_report_path = csv_path

        self.campaign_manager.add_campaign(
            name=f"Workflow {workflow.get('name','')} | {start_time.strftime('%Y-%m-%d %H:%M')}",
            total=total,
            sent=self.sent,
            failed=self.failed,
            invalid=self.invalid,
            duration_seconds=int(duration.total_seconds()),
            results_log=self.results_log,
            csv_path=csv_path
        )
        self._run_on_ui(self._refresh_analytics)

        try:
            if self.bg_mode_var.get():
                self.bot.minimize()
            else:
                self.bot.bring_to_front()

            if self.stop_event.is_set():
                self.log("🛑 تم إيقاف العملية.")
            else:
                self.log("🏁 انتهت العملية.")
                self._run_on_ui(lambda: self.progress_bar.set(1.0))

        except Exception as e:
            self.report_error("ERR-99", "حدث خطأ عام أثناء الإرسال.", detail=str(e), dialog=True)
        finally:
            self.is_running = False
            self.pause_event.clear()
            self.is_paused = False
            self._run_on_ui(lambda: self.btn_start.configure(state="normal"))
            self._run_on_ui(lambda: self.btn_stop.configure(state="disabled"))
            if hasattr(self, "btn_check"):
                self._run_on_ui(lambda: self.btn_check.configure(state="normal"))
            if hasattr(self, "pause_btn"):
                self._run_on_ui(lambda: self.pause_btn.configure(text="Pause"))
            self._run_on_ui(lambda: self.status_label.configure(text="جاهز..."))

    def _run_automation(self, contacts, msg_template, attachments):
        if not self.bot:
            return

        self.sent = 0
        self.failed = 0
        self.invalid = 0
        self.results_log = []
        
        total = len(contacts)
        start_time = datetime.datetime.now()

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
            batch_size, pause_min, pause_max, delay_min, delay_max = 50, 300, 600, 10, 20
            max_retries, retry_delay_min, retry_delay_max, max_consecutive_failures = 2, 3, 6, 5

        self.log(f"🚀 بدء إرسال {total} رسالة...")
        consecutive_failures = 0
        retryable_errors = {
            "ERR_TIMEOUT",
            "ERR_CHAT_INPUT_NOT_FOUND",
            "ERR_ATTACH_BTN_NOT_FOUND",
            "ERR_FILE_INPUT_NOT_FOUND",
            "ERR_SEND_BTN_NOT_FOUND",
            "ERR_SEND_BTN_TIMEOUT",
            "ERR_TEXT_SEND",
        }

        for i, c in enumerate(contacts):
            if self.stop_event.is_set():
                break
            while self.pause_event.is_set() and not self.stop_event.is_set():
                time.sleep(0.3)

            # Batch pause
            if i > 0 and i % batch_size == 0:
                pause_time = random.uniform(pause_min, pause_max)
                self.log(f"⏸ استراحة لمدة {int(pause_time)} ثانية...")
                time.sleep(pause_time)

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

            if not phone:
                self.invalid += 1
                self.results_log.append({"phone": "N/A", "name": name, "status": "INVALID", "error_code": "ERR-00", "timestamp": datetime.datetime.now()})
                self._add_progress_row_blind(["N/A", name, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "بدون رقم", "بيانات الرقم ناقصة"], tag="invalid")
                self._run_on_ui(self._update_stats)
                self._update_progress_header_blind(processed, total, phone, name, eta)
                continue

            # Ensure still logged in
            if not self.bot.is_logged_in():
                self.report_error("ERR-21", dialog=True, level="warning")
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
                res = self.bot.send_message(
                    phone=phone,
                    name=name,
                    message_template=primary_msg,
                    extra_messages=extra_msgs,
                    attachments=atts_for_contact,
                    stop_event=self.stop_event,
                    send_text_with_image=self.send_text_var.get()
                )
                if res in ("SUCCESS", "INVALID", "STOPPED"):
                    break
                is_retryable = res in retryable_errors or str(res).startswith("ERR_ATTACH_") or str(res).startswith("ERR_GENERAL")
                if attempt < max_retries and is_retryable:
                    wait_s = random.uniform(retry_delay_min, retry_delay_max)
                    self.log(f"🔁 إعادة محاولة ({attempt + 1}/{max_retries}) بعد {int(wait_s)}ث | {phone} | {res}")
                    time.sleep(wait_s)
                    continue
                break
            
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            if res == "SUCCESS":
                self.sent += 1
                self.log(f"✅ تم الإرسال لـ {name}")
                self.results_log.append({"phone": phone, "name": name, "status": "نجاح", "error_code": "-", "timestamp": timestamp})
                self._add_progress_row_blind([phone, name, timestamp, "تم", "تم الإرسال"], tag="success")
                consecutive_failures = 0
            elif res == "INVALID":
                self.invalid += 1
                self.log(f"🚫 [ERR-20] الرقم {phone} غير صحيح.")
                self.results_log.append({"phone": phone, "name": name, "status": "بدون واتساب", "error_code": "ERR-20", "timestamp": timestamp})
                self._add_progress_row_blind([phone, name, timestamp, "بدون واتساب", "الرقم غير صالح أو لا يستخدم واتساب"], tag="invalid")
                consecutive_failures = 0
            elif res == "STOPPED":
                self.results_log.append({"phone": phone, "name": name, "status": "توقف", "error_code": "-", "timestamp": timestamp})
                self._add_progress_row_blind([phone, name, timestamp, "توقف", "تم إيقاف العملية"], tag="stopped")
                break
            else:
                self.failed += 1
                err_code = res if res.startswith("ERR") else "ERR-UNKNOWN"
                self.log(f"❌ فشل: {phone} | {res}")
                self.results_log.append({"phone": phone, "name": name, "status": "فشل", "error_code": err_code, "timestamp": timestamp})
                self._add_progress_row_blind([phone, name, timestamp, "فشل", str(res)], tag="failed")
                consecutive_failures += 1
                if consecutive_failures >= max_consecutive_failures:
                    self.log(f"⛔ تم الإيقاف تلقائياً بعد {consecutive_failures} فشل متتالي لتقليل المخاطر.")
                    self.stop_event.set()
                    break

            self._run_on_ui(self._update_stats)
            self._update_progress_header_blind(processed, total, phone, name, eta)
            
            # Delay
            time.sleep(random.uniform(delay_min, delay_max))

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
        self._run_on_ui(self._refresh_analytics)

        try:
            if self.bg_mode_var.get():
                self.bot.minimize()
            else:
                self.bot.bring_to_front()

            if self.stop_event.is_set():
                self.log("🛑 تم إيقاف العملية.")
            else:
                self.log("🏁 انتهت العملية.")
                self._run_on_ui(lambda: self.progress_bar.set(1.0))

        except Exception as e:
            self.report_error("ERR-99", "حدث خطأ عام أثناء الإرسال.", detail=str(e), dialog=True)
        finally:
            self.is_running = False
            self.pause_event.clear()
            self.is_paused = False
            self._run_on_ui(lambda: self.btn_start.configure(state="normal"))
            self._run_on_ui(lambda: self.btn_stop.configure(state="disabled"))
            if hasattr(self, "btn_check"):
                self._run_on_ui(lambda: self.btn_check.configure(state="normal"))
            if hasattr(self, "pause_btn"):
                self._run_on_ui(lambda: self.pause_btn.configure(text="Pause"))
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
            time.sleep(random.uniform(1.5, 3.0))

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
            self.progress_tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=15)
            
            self.progress_tree.heading("phone", text="الرقم")
            self.progress_tree.heading("name", text="الاسم / الخطوة")
            self.progress_tree.heading("date", text="الوقت")
            self.progress_tree.heading("status", text="الحالة")
            self.progress_tree.heading("message", text="التفاصيل")
            
            self.progress_tree.column("phone", width=190, anchor="w")
            self.progress_tree.column("name", width=180, anchor="w")
            self.progress_tree.column("date", width=150, anchor="center")
            self.progress_tree.column("status", width=120, anchor="center")
            self.progress_tree.column("message", width=360, anchor="w")

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
            self.progress_tree.tag_configure("success", foreground="#00E676") # Green
            self.progress_tree.tag_configure("failed", foreground="#FF3D00")  # Red
            self.progress_tree.tag_configure("waiting", foreground=COLORS["text_muted"])
            self.progress_tree.tag_configure("invalid", foreground="#FFA500") # Orange
            self.progress_tree.tag_configure("stopped", foreground=COLORS["info"])

            tree_scroll = ctk.CTkScrollbar(table_frame, command=self.progress_tree.yview)
            self.progress_tree.configure(yscrollcommand=tree_scroll.set)
            self.progress_tree.pack(side="left", fill="both", expand=True, padx=2, pady=2)
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
            if self.progress_tree:
                self.progress_tree.insert("", "0", values=new_values, tags=(tag,))
        self._run_on_ui(_do)

    def _update_progress_header_blind(self, processed, total, current_phone=None, current_name=None, eta=None, status_text=None):
        def _do():
            remaining = max(total - processed, 0)
            title_text = getattr(self, "progress_title_text", "متابعة العملية")
            if self.progress_count_label:
                self.progress_count_label.configure(text=f"{title_text} ({processed}/{total})")
            if self.progress_bar_small:
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
                if label:
                    label.configure(text=str(value))
            if self.progress_status_label:
                if status_text:
                    text = status_text
                elif current_phone and current_name:
                    text = f"جاري العمل على: {current_name} - {current_phone}"
                elif current_phone:
                    text = f"جاري العمل على: {current_phone}"
                else:
                    text = "جاري العمل..."
                self.progress_status_label.configure(text=text)
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

