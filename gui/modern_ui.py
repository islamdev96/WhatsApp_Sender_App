"""
WhatsApp Sender Pro — Modern UI
Built with CustomTkinter for a professional, world-class look and feel.
Features: Dark/Light mode, tabbed interface, dashboard, templates, settings persistence.
"""
import customtkinter as ctk
from tkinter import filedialog, messagebox
import threading
import queue
import time
import random
import os
import csv
import datetime

from automation.whatsapp_bot import WhatsAppBot
from utils.helpers import read_contacts, read_contacts_auto
from utils.config_manager import ConfigManager
from utils.templates_manager import TemplatesManager
from utils.contacts_manager import ContactsManager
from utils.scheduler import Scheduler
from utils.campaign_manager import CampaignManager

# ─── Color Palette (Premium) ────────────────────────────────────────────────
COLORS = {
    # Main branding
    "primary":       "#00E676",      # Bright Neon Green
    "primary_hover": "#00C853",      # Deep Emerald
    "primary_dark":  "#050505",      # Very Dark Background (Sidebar)
    
    # Status colors
    "danger":        "#FF3D00",      # Vibrant Red
    "danger_hover":  "#DD2C00",
    "warning":       "#FF9100",      # Deep Orange
    "success":       "#00E676",
    "info":          "#2979FF",      # Bright Blue
    
    # UI Elements (Dark Mode focused)
    "card_bg":       "#1A1A1A",      # Dark Card Background
    "bg_dark":       "#121212",      # Main Background
    "text_main":     "#FFFFFF",
    "text_muted":    "#B0BEC5",
    "accent":        "#651FFF",      # Deep Purple Accent
    "border":        "#333333",
}

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
    "ERR-09": "ملف الصورة غير موجود أو غير صالح.",
    "ERR-06": "زر الإرفاق غير موجود.",
    "ERR-07": "زر الإرسال لم يظهر في الوقت المحدد.",
    "ERR-08": "فشل رفع الصورة أو كتابة الكابشن.",
    "ERR-10": "انتهت مهلة تحميل المحادثة.",
    "ERR-20": "الرقم غير صحيح أو ليس لديه واتساب.",
    "ERR-21": "لم يتم تسجيل الدخول بعد.",
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

        # ── Appearance ──
        mode = self.config.get("appearance_mode", "dark")
        ctk.set_appearance_mode(mode)
        ctk.set_default_color_theme("green")

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
        self.user_data_dir = os.path.join(os.getcwd(), "chrome_profile")

        # ── Build UI ──
        self._build_layout()
        self._load_saved_state()

        # ── UI Queue Processor ──
        self.after(50, self._process_ui_queue)

        # ── Save on close ──
        self.protocol("WM_DELETE_WINDOW", self._on_close)

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
        self._build_tab_templates()
        self._build_tab_settings()
        self._build_tab_analytics()
        self._build_tab_log()

        # Show main tab by default
        self._switch_tab("main")

    # ─── Sidebar ──────────────────────────────────────────────────────────
    def _build_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=240, corner_radius=0,
                                    fg_color=COLORS["primary_dark"])
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(9, weight=1)

        # Logo / Title
        logo_label = ctk.CTkLabel(self.sidebar, text="⚡ WA Sender",
                                  font=("Segoe UI", 26, "bold"),
                                  text_color=COLORS["primary"])
        logo_label.grid(row=0, column=0, padx=20, pady=(35, 5))

        subtitle = ctk.CTkLabel(self.sidebar, text="PRO EDITION",
                                font=("Segoe UI", 10, "bold"),
                                text_color=COLORS["text_muted"])
        subtitle.grid(row=1, column=0, padx=20, pady=(0, 35))

        # Navigation Buttons
        nav_items = [
            ("🏠  الرئيسية", "main"),
            ("👥  المجموعات", "groups"),
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
            btn.grid(row=i + 2, column=0, padx=15, pady=4, sticky="ew")
            self.nav_buttons[tab_id] = btn

        # Spacer
        # row 8 has weight=1

        # Appearance Toggle
        self.appearance_switch = ctk.CTkSwitch(self.sidebar, text="الوضع الداكن",
                                               font=ctk.CTkFont(size=12),
                                               text_color="white",
                                               command=self._toggle_appearance,
                                               onvalue="dark", offvalue="light")
        self.appearance_switch.grid(row=10, column=0, padx=20, pady=(10, 5))
        if self.config.get("appearance_mode", "dark") == "dark":
            self.appearance_switch.select()

        # Version
        ver_label = ctk.CTkLabel(self.sidebar, text="v2.5.0",
                                 font=ctk.CTkFont(size=10),
                                 text_color="#6C757D")
        ver_label.grid(row=11, column=0, padx=20, pady=(5, 15))

    def _switch_tab(self, tab_id):
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

        # 2. Image
        self._create_file_row(left, "📷 صورة", "image_entry", self._browse_image)

        # 3. Video
        self._create_file_row(left, "🎥 فيديو", "video_entry", self._browse_video)

        # 4. Document
        self._create_file_row(left, "📄 مستند (PDF/Doc)", "doc_entry", self._browse_document)

        # -- Message Section --
        # -- Message Input --
        ctk.CTkLabel(left, text="نص الرسالة:", font=("Segoe UI", 13, "bold"),
                     text_color=COLORS["text_main"]).pack(anchor="e", padx=25)
        
        self.msg_text = ctk.CTkTextbox(left, height=180, corner_radius=12,
                                       font=("Segoe UI", 13), border_color=COLORS["border"],
                                       fg_color=COLORS["bg_dark"])
        self.msg_text.pack(fill="both", expand=True, padx=20, pady=(5, 10))

        # -- Checkboxes --
        chk_frame = ctk.CTkFrame(left, fg_color="transparent")
        chk_frame.pack(fill="x", padx=15, pady=(0, 12))

        self.send_text_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(chk_frame, text="إرسال نص مع الصورة",
                        variable=self.send_text_var,
                        font=ctk.CTkFont(size=12)).pack(side="right", padx=5)

        self.bg_mode_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(chk_frame, text="🖥️ تشغيل في الخلفية",
                        variable=self.bg_mode_var,
                        font=ctk.CTkFont(size=12)).pack(side="right", padx=5)

        # RIGHT: Controls + Progress
        right = ctk.CTkFrame(body, corner_radius=12)
        right.grid(row=0, column=1, padx=(8, 0), pady=5, sticky="nsew")

        ctrl_label = ctk.CTkLabel(right, text="🎛️ التحكم", font=ctk.CTkFont(size=14, weight="bold"))
        ctrl_label.pack(anchor="e", padx=15, pady=4)

        ctrl_frame = ctk.CTkFrame(right, fg_color="transparent")
        ctrl_frame.pack(fill="x", padx=15, pady=(0, 10))

        # 1. Login
        self.btn_login = ctk.CTkButton(ctrl_frame, text="🔑 فتح واتساب (Login)",
                                       font=("Segoe UI", 13, "bold"),
                                       height=40,
                                       fg_color=COLORS["card_bg"],
                                       hover_color=COLORS["border"],
                                       border_width=1, border_color=COLORS["primary"],
                                       image=None, compound="right",
                                       command=self._login_action)
        self.btn_login.pack(fill="x", pady=(0, 10))

        # 2. Start
        self.btn_start = ctk.CTkButton(ctrl_frame, text="🚀 بدء الإرسال",
                                       font=("Segoe UI", 14, "bold"),
                                       height=45,
                                       fg_color=COLORS["primary"],
                                       text_color="#000000",
                                       hover_color=COLORS["primary_hover"],
                                       command=self._start_action)
        self.btn_start.pack(fill="x", pady=(0, 10))

        # 3. Stop
        self.btn_stop = ctk.CTkButton(ctrl_frame, text="🛑 إيقاف مؤقت",
                                      font=("Segoe UI", 13, "bold"),
                                      height=40,
                                      fg_color=COLORS["card_bg"],
                                      hover_color=COLORS["danger"],
                                      border_width=1, border_color=COLORS["danger"],
                                      state="disabled",
                                      command=self._stop_action)
        self.btn_stop.pack(fill="x", pady=(0, 10))

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
                                          fg_color=COLORS["accent"], hover_color="#5A4BD1",
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

        # -- Error Codes Button --
        ctk.CTkButton(right, text="📖 أكواد الأخطاء",
                      font=ctk.CTkFont(size=12),
                      fg_color=COLORS["accent"],
                      hover_color="#5A4BD1",
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

    def log(self, message):
        def _do():
            self.log_textbox.configure(state="normal")
            self.log_textbox.insert("end", f"[{time.strftime('%H:%M:%S')}] {message}\n")
            self.log_textbox.see("end")
            self.log_textbox.configure(state="disabled")
        self._run_on_ui(_do)

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
                      fg_color=COLORS["card_bg"], hover_color=COLORS["primary"],
                      font=("Segoe UI", 14),
                      command=browse_cmd).pack(side="right")

    def _browse_contacts(self):
        path = filedialog.askopenfilename(filetypes=[("Contacts", "*.csv;*.xlsx;*.xls")])
        if path:
            self.contacts_entry.delete(0, "end")
            self.contacts_entry.insert(0, path)

    def _browse_image(self):
        path = filedialog.askopenfilename(filetypes=[("Images", "*.jpg;*.jpeg;*.png")])
        if path:
            self.image_entry.delete(0, "end")
            self.image_entry.insert(0, path)

    def _browse_video(self):
        path = filedialog.askopenfilename(filetypes=[("Video", "*.mp4;*.mkv;*.avi;*.3gp")])
        if path:
            self.video_entry.delete(0, "end")
            self.video_entry.insert(0, path)

    def _browse_document(self):
        path = filedialog.askopenfilename(filetypes=[("Documents", "*.pdf;*.docx;*.pptx;*.xlsx;*.txt;*.zip;*.rar")])
        if path:
            self.doc_entry.delete(0, "end")
            self.doc_entry.insert(0, path)

    def _browse_video(self):
        path = filedialog.askopenfilename(filetypes=[("Video", "*.mp4;*.mkv;*.avi;*.3gp")])
        if path:
            self.video_entry.delete(0, "end")
            self.video_entry.insert(0, path)

    def _browse_document(self):
        path = filedialog.askopenfilename(filetypes=[("Documents", "*.pdf;*.docx;*.pptx;*.xlsx;*.txt;*.zip;*.rar")])
        if path:
            self.doc_entry.delete(0, "end")
            self.doc_entry.insert(0, path)

    # ═══════════════════════════════════════════════════════════════════════
    #  TEMPLATES MANAGEMENT
    # ═══════════════════════════════════════════════════════════════════════
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
                          fg_color=COLORS["card_bg"], hover_color=COLORS["danger"], 
                          border_width=1, border_color=COLORS["danger"],
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
                                fg_color=COLORS["card_bg"],
                                hover_color=COLORS["border"],
                                text_color=COLORS["text_main"],
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
            ("جهات الاتصال", "*.csv;*.xlsx;*.xls"),
            ("CSV", "*.csv"),
            ("Excel", "*.xlsx;*.xls"),
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
        contacts = read_contacts_auto(file_path) if file_path else []
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
        contacts = read_contacts_auto(file_path)
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
            self.config.save()
            messagebox.showinfo("تم", "تم حفظ الإعدادات بنجاح.")
        except ValueError:
            messagebox.showerror("خطأ", "يرجى إدخال أرقام صحيحة في جميع الحقول.")

    def _toggle_appearance(self):
        mode = self.appearance_switch.get()
        ctk.set_appearance_mode(mode)
        self.config.set_and_save("appearance_mode", mode)

    def _load_saved_state(self):
        # Load last used files
        last_csv = self.config.get("last_contacts_file", "")
        if last_csv and os.path.exists(last_csv):
            self.contacts_entry.insert(0, last_csv)
        else:
            def_csv = os.path.join(os.getcwd(), "contacts.csv")
            if os.path.exists(def_csv):
                self.contacts_entry.insert(0, def_csv)

        last_img = self.config.get("last_image_file", "")
        if last_img and os.path.exists(last_img):
            self.image_entry.insert(0, last_img)
        else:
            def_img = os.path.join(os.getcwd(), "offer.jpg")
            if os.path.exists(def_img):
                self.image_entry.insert(0, def_img)

        self.video_entry.insert(0, self.config.get("last_video_file", ""))
        self.doc_entry.insert(0, self.config.get("last_doc_file", ""))

        # Load last message
        last_msg = self.config.get("last_message", "")
        if last_msg:
            self.message_textbox.insert("1.0", last_msg)

        # Load checkboxes
        self.send_text_var.set(self.config.get("send_text_with_image", True))
        self.bg_mode_var.set(self.config.get("background_mode", False))

    def _save_current_state(self):
        self.config.set("last_contacts_file", self.contacts_entry.get())
        self.config.set("last_image_file", self.image_entry.get())
        self.config.set("last_video_file", self.video_entry.get())
        self.config.set("last_doc_file", self.doc_entry.get())
        self.config.set("last_message", self.message_textbox.get("1.0", "end").strip())
        self.config.set("send_text_with_image", self.send_text_var.get())
        self.config.set("background_mode", self.bg_mode_var.get())
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

    # ═══════════════════════════════════════════════════════════════════════
    #  BOT ACTIONS
    # ═══════════════════════════════════════════════════════════════════════
    def _login_action(self):
        if self.bot and self.bot.driver:
            self.bot.background_mode = False
            self.bot.bring_to_front()
            self.log("المتصفح مفتوح بالفعل.")
            return

        def run_login():
            try:
                self.log("جاري فتح المتصفح...")
                self.bot = WhatsAppBot(self.user_data_dir)
                self.bot.open_whatsapp()
                self.bot.background_mode = False
                self.bot.bring_to_front()
                self.log("يرجى فتح واتساب على الهاتف ومسح QR لتسجيل الدخول...")
                if self.bot.wait_for_login(timeout=120):
                    self.log("✅ تم تسجيل الدخول بنجاح!")
                    self._show_dialog("info", "تم", "تم تسجيل الدخول. يمكنك الآن الضغط على 'بدء الإرسال'.")
                else:
                    self.report_error("ERR-02", dialog=True, level="warning")
            except Exception as e:
                self.report_error("ERR-01", detail=str(e), dialog=True)

        threading.Thread(target=run_login, daemon=True).start()

    def _prepare_content(self):
        msg_template = self.message_textbox.get("1.0", "end").strip()
        attachments = []

        # 1. Image
        img = self.image_entry.get().strip()
        if img and os.path.exists(img):
            attachments.append({"type": "image", "path": img})
        elif img:
            self.report_error("ERR-09", f"الصورة غير موجودة: {img}", dialog=True)
            return None, None

        # 2. Video
        vid = self.video_entry.get().strip()
        if vid and os.path.exists(vid):
            attachments.append({"type": "video", "path": vid})
        elif vid:
            self.report_error("ERR-09", f"الفيديو غير موجود: {vid}", dialog=True)
            return None, None

        # 3. Document
        doc = self.doc_entry.get().strip()
        if doc and os.path.exists(doc):
            attachments.append({"type": "document", "path": doc})
        elif doc:
            self.report_error("ERR-09", f"المستند غير موجود: {doc}", dialog=True)
            return None, None

        # Check if empty
        if not msg_template and not attachments:
            self.report_error("ERR-04", "يرجى كتابة نص الرسالة أو اختيار مرفق.", dialog=True, level="warning")
            return None, None

        return msg_template, attachments

    def _start_action(self):
        msg_template, attachments = self._prepare_content()
        if msg_template is None and attachments is None:
            return  # Error reported

        contacts_input = self.contacts_entry.get().strip()
        contacts = []

        # 1. Check Group
        if contacts_input.startswith("[GROUP:") and contacts_input.endswith("]"):
            group_name = contacts_input[7:-1]
            g = self.contacts_mgr.get_by_name(group_name)
            if not g or not g.get("contacts"):
                self.report_error("ERR-03", f"المجموعة '{group_name}' فارغة أو غير موجودة.", dialog=True)
                return
            contacts = g["contacts"]
            self.log(f"تم اختيار المجموعة: {group_name} ({len(contacts)} جهة اتصال)")
            
        # 2. Check File
        elif contacts_input and os.path.exists(contacts_input):
            contacts = read_contacts_auto(contacts_input)
            if not contacts:
                self.report_error("ERR-06", "الملف فارغ أو لا يحتوي على أرقام صحيحة.", dialog=True)
                return
            self.log(f"تم تحميل {len(contacts)} جهة اتصال من الملف.")
            
        else:
             self.report_error("ERR-05", "يرجى اختيار ملف أرقام صحيح أو مجموعة.", dialog=True)
             return

        self._save_current_state()
        
        # 3. Check Bot & Login
        if not self.bot or not self.bot.driver:
            if messagebox.askyesno("تنبيه", "المتصفح غير مفتوح. هل تريد فتحه الآن؟"):
                self._login_action()
            return
            
        if not self.bot.is_logged_in():
            self.bot.bring_to_front()
            self.report_error("ERR-21", dialog=True, level="warning")
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
        
        self.btn_start.configure(state="disabled")
        self.btn_stop.configure(state="normal")
        self.progress_bar.set(0)
        self.status_label.configure(text="جاري العمل...")

        threading.Thread(target=self._run_automation, 
                         args=(contacts, msg_template, attachments),
                         daemon=True).start()

    def _stop_action(self):
        if messagebox.askyesno("تأكيد", "هل تريد إيقاف العملية؟"):
            self.stop_event.set()
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

        # Batch settings
        try:
            batch_size = int(self.batch_size_entry.get())
            pause_min = int(self.batch_min_entry.get())
            pause_max = int(self.batch_max_entry.get())
            delay_min = int(self.delay_min_entry.get())
            delay_max = int(self.delay_max_entry.get())
        except ValueError:
            batch_size, pause_min, pause_max, delay_min, delay_max = 50, 300, 600, 10, 20

        self.log(f"🚀 بدء إرسال {total} رسالة...")

        for i, c in enumerate(contacts):
            if self.stop_event.is_set():
                break

            # Batch pause
            if i > 0 and i % batch_size == 0:
                pause_time = random.uniform(pause_min, pause_max)
                self.log(f"⏸ استراحة لمدة {int(pause_time)} ثانية...")
                time.sleep(pause_time)

            phone = c.get("phone")
            name = c.get("name", "عميل")
            
            processed = i + 1
            self._run_on_ui(lambda: self.status_label.configure(text=f"جاري إرسال {processed}/{total} إلى {name}..."))
            self._run_on_ui(lambda: self.progress_bar.set(processed / total))

            if not phone:
                self.invalid += 1
                self.results_log.append({"phone": "N/A", "name": name, "status": "INVALID", "error_code": "ERR-00", "timestamp": datetime.datetime.now()})
                self._run_on_ui(self._update_stats)
                continue

            # Send Message + Attachments
            # We assume bot.send_message is updated to valid signature
            res = self.bot.send_message(
                phone=phone,
                name=name,
                message_template=msg_template,
                attachments=attachments,
                stop_event=self.stop_event
            )
            
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            if res == "SUCCESS":
                self.sent += 1
                self.log(f"✅ تم الإرسال لـ {name}")
                self.results_log.append({"phone": phone, "name": name, "status": "نجاح", "error_code": "-", "timestamp": timestamp})
            elif res == "INVALID":
                self.invalid += 1
                self.log(f"🚫 [ERR-20] الرقم {phone} غير صحيح.")
                self.results_log.append({"phone": phone, "name": name, "status": "بدون واتساب", "error_code": "ERR-20", "timestamp": timestamp})
            elif res == "STOPPED":
                self.results_log.append({"phone": phone, "name": name, "status": "توقف", "error_code": "-", "timestamp": timestamp})
                break
            else:
                self.failed += 1
                err_code = res if res.startswith("ERR") else "ERR-UNKNOWN"
                self.log(f"❌ فشل: {phone} | {res}")
                self.results_log.append({"phone": phone, "name": name, "status": "فشل", "error_code": err_code, "timestamp": timestamp})

            self._run_on_ui(self._update_stats)
            
            # Delay
            time.sleep(random.uniform(delay_min, delay_max))

        end_time = datetime.datetime.now()
        duration = end_time - start_time
        
        # Save Campaign
        csv_path = self._generate_final_report(duration)
        
        # Determine status
        c_status = "Completed" if not self.stop_event.is_set() else "Stopped"
        
        # Save to history
        self.campaign_manager.add_campaign(
            name=f"Campaign {start_time.strftime('%Y-%m-%d %H:%M')}",
            total=total,
            sent=self.sent,
            failed=self.failed,
            invalid=self.invalid,
            duration=str(duration).split('.')[0],
            status=c_status,
            csv_path=csv_path,
            errors={r["error_code"]: 1 for r in self.results_log if r["status"] == "فشل"}
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
            self._run_on_ui(lambda: self.btn_start.configure(state="normal"))
            self._run_on_ui(lambda: self.btn_stop.configure(state="disabled"))
            self._run_on_ui(lambda: self.status_label.configure(text="جاهز..."))

    # ═══════════════════════════════════════════════════════════════════════
    #  REPORT
    # ═══════════════════════════════════════════════════════════════════════
    def _generate_final_report(self, duration):
        total = self.sent + self.failed + self.invalid
        if total == 0:
            return

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
