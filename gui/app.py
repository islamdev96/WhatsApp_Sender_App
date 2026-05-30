"""
WhatsApp Sender Pro — Main Application Window.
Built with CustomTkinter for a professional UI.
"""
import customtkinter as ctk
from tkinter import messagebox, ttk
import threading
import queue
import time
import os
import datetime
import json

from gui.theme import COLORS, PALETTE_DARK, PALETTE_LIGHT, ERROR_CATALOG
from gui.mixins import (
    TabBuildersMixin,
    AutomationMixin,
    ContactsMixin,
    ReportingMixin,
    DialogsMixin,
    ProgressMixin,
)

from automation.bot import WhatsAppBot
from utils.config_manager import ConfigManager
from utils.templates_manager import TemplatesManager
from utils.contacts_manager import ContactsManager
from utils.campaign_manager import CampaignManager
from utils.event_log import format_event
from utils.logger import logger


class ModernWhatsAppApp(
    TabBuildersMixin,
    AutomationMixin,
    ContactsMixin,
    ReportingMixin,
    DialogsMixin,
    ProgressMixin,
    ctk.CTk,
):
    def __init__(self):
        super().__init__()
        self.withdraw()

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
        self.title("Auto WhatsApp Business Sender Turbo Pro v17.0 Full")
        w = self.config.get("window_width", 1000)
        h = self.config.get("window_height", 700)
        self.geometry(f"{w}x{h}")
        self.minsize(900, 650)

        # ── State Variables ──
        self.bot = None
        self.active_bots = {}
        self.parallel_stats = {}
        self.stats_lock = threading.Lock()
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
            with open(os.path.join("data", "locales.json"), "r", encoding="utf-8") as f:
                self.locales = json.load(f)
        except Exception as e:
            print(f"Error loading locales: {e}")
            
        self.current_lang = ctk.StringVar(value=self.config.get("language", "ar"))

        # ── Start Scheduler Engine ──
        from utils.scheduler import Scheduler
        self.scheduler = Scheduler()
        self.scheduler.start(self._run_scheduled_campaign_callback)

        # ── Build Layout ──
        self._build_layout()

        # ── Start UI Queue Processor ──
        self.after(50, self._process_ui_queue)

        # ── Show Splash Screen ──
        self._show_splash_screen()

    def _show_splash_screen(self):
        """Displays a premium borderless splash screen for 2.5 seconds before launching the main window."""
        # Create a frameless splash window
        splash = ctk.CTkToplevel(self)
        splash.overrideredirect(True)
        splash.configure(fg_color=COLORS.get("bg_dark", "#0F172A"))
        
        # Size and position of splash screen
        width, height = 500, 360
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        splash.geometry(f"{width}x{height}+{x}+{y}")
        
        # Load and render premium vector logo
        from PIL import Image
        logo_path = os.path.join("data", "app_logo.png")
        if os.path.exists(logo_path):
            try:
                pil_img = Image.open(logo_path)
                logo_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(160, 160))
                lbl_logo = ctk.CTkLabel(splash, image=logo_img, text="")
                lbl_logo.pack(pady=(35, 10))
            except Exception as e:
                logger.debug("Could not load splash logo: %s", e)
                ctk.CTkLabel(splash, text="🟢", font=("Segoe UI", 48)).pack(pady=(45, 15))
        else:
            ctk.CTkLabel(splash, text="🟢", font=("Segoe UI", 48)).pack(pady=(45, 15))
            
        # App Title & Description
        ctk.CTkLabel(
            splash, text="Auto WhatsApp Business Sender Turbo Pro", 
            font=("Segoe UI", 16, "bold"), text_color=COLORS.get("primary", "#00E676")
        ).pack(pady=(5, 2))
        
        ctk.CTkLabel(
            splash, text="V17.0 Full Standalone Edition", 
            font=("Segoe UI", 11), text_color=COLORS.get("text_muted", "#64748B")
        ).pack(pady=0)
        
        # Indeterminate pulse progress bar
        progress = ctk.CTkProgressBar(splash, width=320, height=5, progress_color=COLORS.get("primary", "#00E676"))
        progress.pack(pady=25)
        progress.configure(mode="indeterminate")
        progress.start()
        
        # Loading caption
        is_ar = self.current_lang.get() == "ar"
        caption_txt = "جاري تحميل المكونات وتجهيز المتصفح..." if is_ar else "Loading components and browser setup..."
        lbl_cap = ctk.CTkLabel(splash, text=caption_txt, font=("Segoe UI", 10, "italic"), text_color=COLORS.get("text_muted", "#64748B"))
        lbl_cap.pack()
        
        # Graceful callback to deiconify main app window
        def close_splash():
            try:
                splash.destroy()
            except Exception:
                pass
            self.deiconify()
            
        self.after(2500, close_splash)

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

        # Configure ttk.Style for all Treeviews to match our modern high-contrast palette
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception as exc:
            logger.debug("Could not apply ttk clam theme: %s", exc)

        primary_color = COLORS["primary"]

        style.configure(
            "Treeview",
            background=COLORS["card_bg"],
            foreground=COLORS["text_main"],
            fieldbackground=COLORS["card_bg"],
            rowheight=28,
            font=("Segoe UI", 10),
            borderwidth=0
        )
        style.configure(
            "Treeview.Heading",
            font=("Segoe UI", 10, "bold"),
            background=COLORS["bg_dark"],
            foreground=COLORS["text_main"],
            borderwidth=1,
            relief="flat"
        )
        style.map(
            "Treeview.Heading",
            background=[("active", COLORS["border"]), ("!active", COLORS["bg_dark"])],
            foreground=[("active", COLORS["text_main"]), ("!active", COLORS["text_main"])]
        )
        style.map(
            "Treeview",
            background=[("selected", primary_color)],
            foreground=[("selected", "#000000" if primary_color in ("#00E676", "#00FF9D") else "#FFFFFF")]
        )


    def _refresh_theme(self):
        # Update key widgets after palette change
        if hasattr(self, "topbar_frame"):
            self.topbar_frame.configure(fg_color=COLORS.get("topbar_bg", COLORS["primary_dark"]))
        if hasattr(self, "sidebar_frame"):
            self.sidebar_frame.configure(fg_color=COLORS.get("sidebar_bg", "#075E54"))
        if hasattr(self, "bottom_bar"):
            self.bottom_bar.configure(fg_color=COLORS["primary_dark"])
        if hasattr(self, "session_status_label"):
            self.session_status_label.configure(text_color=COLORS["text_muted"])
        if hasattr(self, "nav_buttons") and hasattr(self, "current_tab"):
            is_dark = ctk.get_appearance_mode().lower() == "dark"
            for nid, btn in self.nav_buttons.items():
                if nid == self.current_tab:
                    active_text = COLORS.get("primary", "#00FF9D") if is_dark else "#FFFFFF"
                    btn.configure(
                        fg_color=COLORS.get("sidebar_active", "#1C2A4A"),
                        text_color=active_text
                    )
                else:
                    inactive_text = COLORS.get("text_muted", "#94A3B8") if is_dark else COLORS.get("sidebar_text", "#E9EDEF")
                    btn.configure(
                        fg_color="transparent",
                        text_color=inactive_text
                    )
        if hasattr(self, "attachment_manager"):
            self.attachment_manager.apply_theme(COLORS)
        if hasattr(self, "message_editor"):
            self.message_editor.apply_theme(COLORS)
        if hasattr(self, "btn_start"):
            self.btn_start.configure(fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"], text_color="#FFFFFF")
        if hasattr(self, "btn_stop"):
            self.btn_stop.configure(fg_color=COLORS["danger"], hover_color=COLORS["danger_hover"], text_color="#FFFFFF")

        if hasattr(self, "btn_theme_toggle"):
            is_dark = ctk.get_appearance_mode().lower() == "dark"
            is_ar = self.current_lang.get() == "ar"
            theme_txt = ("☀️ Light" if is_dark else "🌙 Dark") if not is_ar else ("☀️ مضيء" if is_dark else "🌙 مظلم")
            self.btn_theme_toggle.configure(text=theme_txt, fg_color=COLORS["card_bg"], text_color=COLORS["text_main"])
        if hasattr(self, "btn_lang_toggle"):
            lang_txt = "🇬🇧 EN" if self.current_lang.get() == "ar" else "🇸🇦 AR"
            self.btn_lang_toggle.configure(text=lang_txt, fg_color=COLORS["card_bg"], text_color=COLORS["text_main"])

    # ═══════════════════════════════════════════════════════════════════════
    #  LAYOUT
    # ═══════════════════════════════════════════════════════════════════════

    def _build_layout(self):
        """Build the main application layout: sidebar menu + content area."""

        # Instantiate backward compatibility state variables
        self.bg_mode_var = ctk.BooleanVar(value=self.config.get("background_mode", False))
        self.use_valid_after_check_var = ctk.BooleanVar(value=self.config.get("use_valid_after_check", False))
        self.turbo_mode_var = ctk.BooleanVar(value=self.config.get("turbo_mode", False))

        # Main window grid structure:
        # Row 0: Top Bar
        # Row 1: Middle Frame (Sidebar + Content Area)
        # Row 2: Bottom Status Bar
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=0)
        self.grid_columnconfigure(0, weight=1)

        # ── 1. Native Windows Menu Bar ──
        self._build_menu_bar()

        # ── 2. Top Bar ──
        self._build_top_bar()

        # ── 3. Middle Frame (Sidebar + Main Frame) ──
        self.middle_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.middle_frame.grid(row=1, column=0, sticky="nsew")
        self.middle_frame.grid_rowconfigure(0, weight=1)
        self.middle_frame.grid_columnconfigure(0, weight=0) # Sidebar column
        self.middle_frame.grid_columnconfigure(1, weight=1) # Content column

        # ── 4. Build Sidebar Frame ──
        self._build_sidebar()

        # ── 5. Main Content Frame ──
        self.main_frame = ctk.CTkFrame(self.middle_frame, corner_radius=0, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, sticky="nsew")
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        # ── 6. Bottom Status Bar ──
        self._build_bottom_bar()

        # ── Tabs (frames) ──
        self.tab_frames = {}
        self._build_tab_main()
        self._build_tab_groups()
        self._build_tab_templates()
        self._build_tab_settings()
        self._build_tab_log()
        self._build_tab_campaigns()
        self._build_tab_auto_reply()
        self._build_tab_received()
        self._build_tab_filter()
        self._build_tab_warmer()
        self._build_tab_workflows()
        self._build_tab_gmaps()

        # Show main tab by default
        self._switch_tab("main")
        self._refresh_theme()

    # ─── native Windows Menu Bar ──────────────────────────────────────────────

    def _build_menu_bar(self):
        """Build the left sidebar navigation with tab buttons."""
        import tkinter as tk
        menu_bar = tk.Menu(self)
        
        # 1. File Menu
        file_menu = tk.Menu(menu_bar, tearoff=0)
        file_menu.add_command(label=self.tr("menu_file_open"), command=self._browse_contacts)
        file_menu.add_command(label=self.tr("menu_file_import"), command=self._open_import_dialog)
        file_menu.add_separator()
        file_menu.add_command(label=self.tr("menu_file_save_template"), command=self._save_template)
        file_menu.add_separator()
        file_menu.add_command(label=self.tr("menu_file_exit"), command=self._on_close)
        menu_bar.add_cascade(label=self.tr("menu_file"), menu=file_menu)

        # 2. Edit Menu
        edit_menu = tk.Menu(menu_bar, tearoff=0)
        edit_menu.add_command(label=self.tr("menu_edit_num_gen"), command=self._open_number_generator)
        edit_menu.add_separator()
        edit_menu.add_command(label=self.tr("menu_edit_clear_msg"), command=lambda: self.message_editor.set_text(""))
        edit_menu.add_command(label=self.tr("menu_edit_clear_attach"), command=lambda: self.attachment_manager.clear())
        menu_bar.add_cascade(label=self.tr("menu_edit"), menu=edit_menu)

        # 3. View Menu
        view_menu = tk.Menu(menu_bar, tearoff=0)
        view_menu.add_command(label=self.tr("menu_view_toggle_dark"), command=self._toggle_appearance_menu)
        menu_bar.add_cascade(label=self.tr("menu_view"), menu=view_menu)

        # 4. Settings Menu
        settings_menu = tk.Menu(menu_bar, tearoff=0)
        settings_menu.add_command(label=self.tr("menu_settings_send_delay"), command=lambda: self._open_sending_settings_dialog(self.tr("tab_sending_settings")))
        settings_menu.add_command(label=self.tr("menu_settings_proxy"), command=lambda: self._open_sending_settings_dialog(self.tr("tab_proxy_safety")))
        menu_bar.add_cascade(label=self.tr("menu_settings"), menu=settings_menu)

        # 5. Tools Menu
        tools_menu = tk.Menu(menu_bar, tearoff=0)
        tools_menu.add_command(label=self.tr("menu_tools_contacts"), command=lambda: self._switch_tab("groups"))
        tools_menu.add_command(label=self.tr("menu_tools_check_nums"), command=lambda: self._check_numbers_action())
        menu_bar.add_cascade(label=self.tr("menu_tools"), menu=tools_menu)

        # 6. Help Menu
        help_menu = tk.Menu(menu_bar, tearoff=0)
        help_menu.add_command(label=self.tr("menu_help_guide"), command=self._show_help_dialog)
        help_menu.add_command(label=self.tr("menu_help_log"), command=lambda: self._switch_tab("log"))
        help_menu.add_separator()
        help_menu.add_command(label=self.tr("menu_help_about"), command=self._show_about_dialog)
        menu_bar.add_cascade(label=self.tr("menu_help"), menu=help_menu)

        self.configure(menu=menu_bar)

    # ─── Top Header Bar ──────────────────────────────────────────────

    def _build_top_bar(self):
        """Build the top header with branding, profile, theme, and language controls."""
        self.topbar_frame = ctk.CTkFrame(self, height=60, corner_radius=0, fg_color=COLORS.get("topbar_bg", COLORS["primary_dark"]))
        self.topbar_frame.grid(row=0, column=0, sticky="ew")
        self.topbar_frame.grid_propagate(False)

        is_ar = self.current_lang.get() == "ar"
        side_lbl = "right" if is_ar else "left"
        side_opp = "left" if is_ar else "right"

        # App Logo / Branding
        branding_frame = ctk.CTkFrame(self.topbar_frame, fg_color="transparent")
        branding_frame.pack(side=side_lbl, fill="y", padx=15)
        
        logo_label = ctk.CTkLabel(branding_frame, text="🟢", font=("Segoe UI", 16))
        logo_label.pack(side=side_lbl, padx=5, pady=15)
        
        title_label = ctk.CTkLabel(
            branding_frame, text="Auto WhatsApp Business Sender Turbo Pro v17.0",
            font=("Segoe UI", 13, "bold"), text_color=COLORS["text_main"]
        )
        title_label.pack(side=side_lbl, padx=5, pady=15)

        # Controls Container
        controls_container = ctk.CTkFrame(self.topbar_frame, fg_color="transparent")
        controls_container.pack(side=side_opp, fill="y", padx=10)

        # Profile Selector
        lbl_profile = ctk.CTkLabel(controls_container, text=self.tr("lbl_account") + ":", font=("Segoe UI", 11), text_color=COLORS["text_muted"])
        lbl_profile.pack(side=side_lbl, padx=5, pady=15)

        self.profile_combo = ctk.CTkComboBox(
            controls_container, values=self._get_profiles(),
            variable=self.profile_var,
            command=self._on_profile_change,
            width=120, height=32,
            fg_color=COLORS["card_bg"],
            border_color=COLORS["border"],
            button_color=COLORS["primary"],
            button_hover_color=COLORS["primary_hover"],
            text_color=COLORS["text_main"],
            dropdown_fg_color=COLORS["card_bg"],
            dropdown_text_color=COLORS["text_main"]
        )
        self.profile_combo.pack(side=side_lbl, padx=3, pady=14)
        
        self.btn_add_profile = ctk.CTkButton(
            controls_container, text="➕", font=("Segoe UI", 11, "bold"),
            width=28, height=32, corner_radius=6,
            fg_color=COLORS["secondary"], hover_color=COLORS["secondary_hover"],
            text_color=COLORS["secondary_text"],
            command=self._on_add_profile_click
        )
        self.btn_add_profile.pack(side=side_lbl, padx=3, pady=14)

        # Separator
        sep = ctk.CTkLabel(controls_container, text="|", text_color=COLORS["border"])
        sep.pack(side=side_lbl, padx=8, pady=15)

        # Turbo Mode Switch
        turbo_txt = "🚀 Turbo" if not is_ar else "🚀 توربو"
        self.turbo_switch = ctk.CTkSwitch(
            controls_container, text=turbo_txt,
            variable=self.turbo_mode_var,
            command=self._toggle_turbo_mode,
            progress_color=COLORS["primary"],
            text_color=COLORS["text_main"],
            font=("Segoe UI", 11, "bold")
        )
        self.turbo_switch.pack(side=side_lbl, padx=8, pady=15)

        # Language Toggle Button
        lang_text = "🇬🇧 EN" if is_ar else "🇸🇦 AR"
        self.btn_lang_toggle = ctk.CTkButton(
            controls_container, text=lang_text,
            font=("Segoe UI", 11, "bold"),
            width=55, height=32, corner_radius=8,
            fg_color=COLORS["card_bg"], hover_color=COLORS["border"],
            text_color=COLORS["text_main"],
            command=self._toggle_language
        )
        self.btn_lang_toggle.pack(side=side_lbl, padx=5, pady=14)

        # Theme Toggle Button
        theme_icon = "☀️ Light" if self.config.get("appearance_mode", "dark") == "dark" else "🌙 Dark"
        if is_ar:
            theme_icon = "☀️ مضيء" if self.config.get("appearance_mode", "dark") == "dark" else "🌙 مظلم"
            
        self.btn_theme_toggle = ctk.CTkButton(
            controls_container, text=theme_icon,
            font=("Segoe UI", 11, "bold"),
            width=75, height=32, corner_radius=8,
            fg_color=COLORS["card_bg"], hover_color=COLORS["border"],
            text_color=COLORS["text_main"],
            command=self._toggle_appearance_menu
        )
        self.btn_theme_toggle.pack(side=side_lbl, padx=5, pady=14)

    # ─── Left Sidebar Navigation ──────────────────────────────────────────────

    def _build_sidebar(self):
        """Build the left sidebar vertical navigation menu."""
        self.sidebar_frame = ctk.CTkFrame(
            self.middle_frame, width=220, corner_radius=0,
            fg_color=COLORS.get("sidebar_bg", "#075E54")
        )
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_propagate(False)

        nav_container = ctk.CTkScrollableFrame(
            self.sidebar_frame, fg_color="transparent", corner_radius=0,
            scrollbar_button_color=COLORS.get("sidebar_separator", "#0A7A6B"),
            scrollbar_button_hover_color=COLORS.get("sidebar_hover", "#064E46")
        )
        nav_container.pack(fill="both", expand=True, padx=5, pady=(10, 5))

        sidebar_items = [
            ("open_whatsapp", "🌐", self._login_action),
            ("new_campaign", "📣", "main"),
            ("sent_campaigns", "📊", "campaigns"),
            ("auto_reply", "🤖", "auto_reply"),
            ("received", "📥", "received"),
            ("filter_numbers", "🔍", "filter"),
            ("groups_grabber", "👥", "groups"),
            ("gmaps", "🗺️", "gmaps"),
            ("warmer", "🔥", "warmer"),
            ("workflows", "🧭", "workflows"),
            ("templates", "📝", "templates"),
            ("settings", "⚙️", self._open_sending_settings_dialog),
            ("log", "📋", "log"),
            ("help", "❓", self._show_help_dialog),
        ]

        self.nav_buttons = {}
        for key, emoji, target in sidebar_items:
            btn_text = f"{emoji} {self.tr(key)}"
            
            if isinstance(target, str):
                cmd = lambda t=target: self._switch_tab(t)
            else:
                cmd = target

            btn = ctk.CTkButton(
                nav_container, text=btn_text,
                font=("Segoe UI", 11, "bold"),
                anchor="w",
                height=38,
                corner_radius=6,
                fg_color="transparent",
                text_color=COLORS.get("sidebar_text", "#FFFFFF"),
                hover_color=COLORS.get("sidebar_hover", "#064E46"),
                command=cmd
            )
            btn.pack(fill="x", pady=2, padx=5)
            
            if isinstance(target, str):
                self.nav_buttons[target] = btn

        logout_btn = ctk.CTkButton(
            self.sidebar_frame, text="🔴 " + self.tr("logout"),
            font=("Segoe UI", 12, "bold"),
            height=40,
            corner_radius=8,
            fg_color="#D32F2F", hover_color="#B71C1C",
            text_color="#FFFFFF",
            command=self._logout_action
        )
        logout_btn.pack(side="bottom", fill="x", padx=10, pady=10)

    def _toggle_turbo_mode(self):
        """Toggle turbo speed mode on/off."""
        is_turbo = self.turbo_mode_var.get()
        self.config.set("turbo_mode", is_turbo)
        self.config.save()
        if is_turbo:
            self.log("🚀 تم تفعيل وضع توربو السريع! تم تقليل الفواصل الزمنية إلى الحد الأدنى.")
            if hasattr(self, "delay_min_entry"):
                self.delay_min_entry.delete(0, "end")
                self.delay_min_entry.insert(0, "1")
            if hasattr(self, "delay_max_entry"):
                self.delay_max_entry.delete(0, "end")
                self.delay_max_entry.insert(0, "3")
        else:
            self.log("ℹ️ تم إيقاف وضع توربو. تم استعادة السرعة الطبيعية.")
            if hasattr(self, "delay_min_entry"):
                self.delay_min_entry.delete(0, "end")
                self.delay_min_entry.insert(0, "8")
            if hasattr(self, "delay_max_entry"):
                self.delay_max_entry.delete(0, "end")
                self.delay_max_entry.insert(0, "15")

    def _open_sending_settings_dialog(self, initial_tab=None):
        """Open the unified sending settings dialog containing all application settings in one single place."""
        import tkinter as tk
        from tkinter import Listbox, messagebox
        from gui.tabs.settings_tab import build_settings_tab
        
        dialog = ctk.CTkToplevel(self)
        dialog.title(self.tr("dialog_settings_title"))
        dialog.geometry("750x640")
        dialog.resizable(False, False)
        dialog.transient(self)

        # Center on parent and update to ensure full layout map before grab
        dialog.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() - 750) // 2
        y = self.winfo_y() + (self.winfo_height() - 640) // 2
        dialog.geometry(f"+{x}+{y}")
        dialog.update()
        dialog.grab_set()

        # Tabview
        tabview = ctk.CTkTabview(dialog, segmented_button_selected_color=COLORS["primary"],
                                 segmented_button_selected_hover_color=COLORS["primary_hover"],
                                 segmented_button_unselected_color=COLORS["secondary"],
                                 text_color=COLORS["text_main"])
        tabview.pack(fill="both", expand=True, padx=15, pady=10)

        # Tab names translated using locales.json
        tab_conn = tabview.add(self.tr("tab_connection"))
        tab_send = tabview.add(self.tr("tab_sending_settings"))
        tab_friend = tabview.add(self.tr("tab_friendly_sending"))
        tab_proxy = tabview.add(self.tr("tab_proxy_safety"))
        tab_queue = tabview.add(self.tr("tab_scheduled_queue"))

        # Build Proxy & Safety and Scheduled Queue
        build_settings_tab(self, tab_proxy)
        self._build_schedule_queue_card(tab_queue)
        self._refresh_schedule_queue()

        if initial_tab:
            try:
                tabview.set(initial_tab)
            except Exception as e:
                logger.debug("Could not set initial settings tab: %s", e)

        # =======================================================================
        # TAB 1: Connection
        # =======================================================================
        # Use pack with propagate and expand to avoid unmapped .place layout issues
        conn_frame = ctk.CTkFrame(tab_conn, border_width=1, border_color=COLORS["border"], fg_color="transparent", width=360, height=130)
        conn_frame.pack_propagate(False)
        conn_frame.pack(expand=True, padx=20, pady=20)
        
        lbl_conn_speed = ctk.CTkLabel(conn_frame, text=self.tr("settings_conn_speed"), font=("Segoe UI", 12, "bold"))
        lbl_conn_speed.pack(anchor="w", padx=25, pady=(15, 5))

        preset_var = ctk.StringVar(value=self.tr("speed_normal"))
        try:
            curr_min = int(self.delay_min_entry.get())
            if curr_min >= 20: preset_var.set(self.tr("speed_very_slow"))
            elif curr_min >= 12: preset_var.set(self.tr("speed_slow"))
            elif curr_min >= 8: preset_var.set(self.tr("speed_normal"))
            elif curr_min >= 4: preset_var.set(self.tr("speed_fast"))
            else: preset_var.set(self.tr("speed_very_fast"))
        except Exception:
            preset_var.set(self.tr("speed_normal"))

        presets_list = [
            self.tr("speed_very_slow"),
            self.tr("speed_slow"),
            self.tr("speed_normal"),
            self.tr("speed_fast"),
            self.tr("speed_very_fast")
        ]
        combo_preset = ctk.CTkComboBox(
            conn_frame, values=presets_list, variable=preset_var,
            height=34, width=310,
            fg_color=COLORS["card_bg"], border_color=COLORS["border"],
            button_color=COLORS["primary"], button_hover_color=COLORS["primary_hover"],
            text_color=COLORS["text_main"], dropdown_fg_color=COLORS["card_bg"],
            dropdown_text_color=COLORS["text_main"]
        )
        combo_preset.pack(padx=25, pady=5)

        # =======================================================================
        # TAB 2: Sending Settings
        # =======================================================================
        tab_send.grid_columnconfigure(0, weight=1)

        # Delay between messages frame
        delay_frame = ctk.CTkFrame(tab_send, border_width=1, border_color=COLORS["border"], fg_color="transparent")
        delay_frame.pack(fill="x", padx=20, pady=15)
        
        lbl_delay = ctk.CTkLabel(delay_frame, text=self.tr("settings_delay_title"), font=("Segoe UI", 12, "bold"), text_color=COLORS["primary"])
        lbl_delay.pack(anchor="w", padx=15, pady=(10, 5))

        row_delay = ctk.CTkFrame(delay_frame, fg_color="transparent")
        row_delay.pack(fill="x", padx=15, pady=5)

        ctk.CTkLabel(row_delay, text=self.tr("settings_wait_between"), font=("Segoe UI", 11)).pack(side="left", padx=5)
        entry_min = ctk.CTkEntry(row_delay, width=80, height=28, justify="center")
        entry_min.pack(side="left", padx=5)
        try:
            entry_min.insert(0, self.delay_min_entry.get())
        except Exception:
            entry_min.insert(0, "8")
        ctk.CTkLabel(row_delay, text=self.tr("settings_seconds"), font=("Segoe UI", 11)).pack(side="left", padx=5)

        ctk.CTkLabel(row_delay, text=self.tr("settings_and"), font=("Segoe UI", 11)).pack(side="left", padx=5)
        entry_max = ctk.CTkEntry(row_delay, width=80, height=28, justify="center")
        entry_max.pack(side="left", padx=5)
        try:
            entry_max.insert(0, self.delay_max_entry.get())
        except Exception:
            entry_max.insert(0, "15")
        ctk.CTkLabel(row_delay, text=self.tr("settings_seconds"), font=("Segoe UI", 11)).pack(side="left", padx=5)

        # Sleep settings
        sleep_enabled = ctk.BooleanVar(value=self.config.get("sleep_enabled", True))
        
        chk_sleep = ctk.CTkCheckBox(
            delay_frame, text=self.tr("settings_activate_sleep"),
            variable=sleep_enabled, font=("Segoe UI", 11, "bold")
        )
        chk_sleep.pack(anchor="w", padx=20, pady=10)

        sleep_sub_frame = ctk.CTkFrame(delay_frame, border_width=1, border_color=COLORS["border"], fg_color="transparent")
        sleep_sub_frame.pack(fill="x", padx=20, pady=(0, 15))

        row_sleep1 = ctk.CTkFrame(sleep_sub_frame, fg_color="transparent")
        row_sleep1.pack(fill="x", padx=15, pady=5)
        ctk.CTkLabel(row_sleep1, text=self.tr("settings_after"), font=("Segoe UI", 11), width=60, anchor="w").pack(side="left", padx=5)
        entry_sleep_size = ctk.CTkEntry(row_sleep1, width=80, height=28, justify="center")
        entry_sleep_size.pack(side="left", padx=5)
        try:
            entry_sleep_size.insert(0, self.batch_size_entry.get())
        except Exception:
            entry_sleep_size.insert(0, "30")
        ctk.CTkLabel(row_sleep1, text=self.tr("settings_messages"), font=("Segoe UI", 11)).pack(side="left", padx=5)

        row_sleep2 = ctk.CTkFrame(sleep_sub_frame, fg_color="transparent")
        row_sleep2.pack(fill="x", padx=15, pady=5)
        ctk.CTkLabel(row_sleep2, text=self.tr("settings_for"), font=("Segoe UI", 11), width=60, anchor="w").pack(side="left", padx=5)
        entry_sleep_max = ctk.CTkEntry(row_sleep2, width=80, height=28, justify="center")
        entry_sleep_max.pack(side="left", padx=5)
        try:
            entry_sleep_max.insert(0, self.batch_max_entry.get())
        except Exception:
            entry_sleep_max.insert(0, "240")
        ctk.CTkLabel(row_sleep2, text=self.tr("settings_seconds"), font=("Segoe UI", 11)).pack(side="left", padx=5)

        def toggle_sleep_entries():
            state = "normal" if sleep_enabled.get() else "disabled"
            entry_sleep_size.configure(state=state)
            entry_sleep_max.configure(state=state)

        chk_sleep.configure(command=toggle_sleep_entries)
        toggle_sleep_entries()

        # =======================================================================
        # TAB 3: Friendly sending
        # =======================================================================
        list_container = ctk.CTkFrame(tab_friend, fg_color="transparent")
        list_container.pack(fill="x", padx=10, pady=5)
        list_container.grid_columnconfigure(0, weight=1)
        list_container.grid_columnconfigure(1, weight=1)

        # Column 1: Common Whatsapp Accounts List
        col1_frame = ctk.CTkFrame(list_container, fg_color="transparent")
        col1_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        
        ctk.CTkLabel(col1_frame, text=self.tr("settings_friendly_accounts"), font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=5)
        
        listbox_accounts = Listbox(col1_frame, height=6, bg="#FFFFFF", fg="#000000",
                                   selectbackground=COLORS["primary"], selectforeground="#FFFFFF",
                                   borderwidth=1, relief="solid", highlightthickness=0)
        listbox_accounts.pack(fill="x", padx=5, pady=2)

        btn_row_acc = ctk.CTkFrame(col1_frame, fg_color="transparent")
        btn_row_acc.pack(fill="x", padx=5, pady=2)

        def add_acc():
            win_input = ctk.CTkInputDialog(text=self.tr("lbl_number") + ":", title=self.tr("settings_friendly_accounts"))
            val = win_input.get_input()
            if val and val.strip():
                listbox_accounts.insert("end", val.strip())

        def del_acc():
            sel = listbox_accounts.curselection()
            if sel:
                listbox_accounts.delete(sel[0])

        ctk.CTkButton(btn_row_acc, text=self.tr("btn_add_rule"), width=70, height=26, fg_color=COLORS["secondary"], hover_color=COLORS["secondary_hover"], text_color=COLORS["text_main"], command=add_acc).pack(side="left", padx=2)
        ctk.CTkButton(btn_row_acc, text=self.tr("groups_btn_delete"), width=70, height=26, fg_color=COLORS["secondary"], hover_color=COLORS["secondary_hover"], text_color=COLORS["text_main"], command=del_acc).pack(side="left", padx=2)

        # Column 2: Messages Dictionary List
        col2_frame = ctk.CTkFrame(list_container, fg_color="transparent")
        col2_frame.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")

        ctk.CTkLabel(col2_frame, text=self.tr("settings_friendly_messages"), font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=5)

        listbox_dict = Listbox(col2_frame, height=6, bg="#FFFFFF", fg="#000000",
                               selectbackground=COLORS["primary"], selectforeground="#FFFFFF",
                               borderwidth=1, relief="solid", highlightthickness=0)
        listbox_dict.pack(fill="x", padx=5, pady=2)

        btn_row_dict = ctk.CTkFrame(col2_frame, fg_color="transparent")
        btn_row_dict.pack(fill="x", padx=5, pady=2)

        def add_dict_msg():
            win_input = ctk.CTkInputDialog(text=self.tr("lbl_message") + ":", title=self.tr("settings_friendly_messages"))
            val = win_input.get_input()
            if val and val.strip():
                listbox_dict.insert("end", val.strip())

        def del_dict_msg():
            sel = listbox_dict.curselection()
            if sel:
                listbox_dict.delete(sel[0])

        ctk.CTkButton(btn_row_dict, text=self.tr("btn_add_rule"), width=70, height=26, fg_color=COLORS["secondary"], hover_color=COLORS["secondary_hover"], text_color=COLORS["text_main"], command=add_dict_msg).pack(side="left", padx=2)
        ctk.CTkButton(btn_row_dict, text=self.tr("groups_btn_delete"), width=70, height=26, fg_color=COLORS["secondary"], hover_color=COLORS["secondary_hover"], text_color=COLORS["text_main"], command=del_dict_msg).pack(side="left", padx=2)

        # Load existing data into listboxes
        saved_accounts = self.config.get("friendly_numbers_list", ["201012345678", "201112345678"])
        saved_messages = self.config.get("friendly_messages_list", ["سلام كيف حالك؟", "الحمد لله تمام", "أهلاً بك"])
        for acc in saved_accounts:
            listbox_accounts.insert("end", acc)
        for msg in saved_messages:
            listbox_dict.insert("end", msg)

        # Checkbox & Frame
        friendly_enabled = ctk.BooleanVar(value=self.config.get("friendly_enabled", False))
        
        chk_friendly = ctk.CTkCheckBox(
            tab_friend, text=self.tr("settings_activate_friendly"),
            variable=friendly_enabled, font=("Segoe UI", 11, "bold")
        )
        chk_friendly.pack(anchor="w", padx=15, pady=10)

        friendly_sub_frame = ctk.CTkFrame(tab_friend, border_width=1, border_color=COLORS["border"], fg_color="transparent")
        friendly_sub_frame.pack(fill="x", padx=15, pady=(0, 10))

        row_f1 = ctk.CTkFrame(friendly_sub_frame, fg_color="transparent")
        row_f1.pack(fill="x", padx=15, pady=3)
        ctk.CTkLabel(row_f1, text=self.tr("settings_after"), font=("Segoe UI", 11), width=60, anchor="w").pack(side="left", padx=5)
        entry_f_after = ctk.CTkEntry(row_f1, width=80, height=26, justify="center")
        entry_f_after.pack(side="left", padx=5)
        entry_f_after.insert(0, str(self.config.get("friendly_after", 5)))
        ctk.CTkLabel(row_f1, text=self.tr("settings_messages"), font=("Segoe UI", 11)).pack(side="left", padx=5)

        row_f2 = ctk.CTkFrame(friendly_sub_frame, fg_color="transparent")
        row_f2.pack(fill="x", padx=15, pady=3)
        ctk.CTkLabel(row_f2, text=self.tr("settings_count"), font=("Segoe UI", 11), width=60, anchor="w").pack(side="left", padx=5)
        entry_f_count = ctk.CTkEntry(row_f2, width=80, height=26, justify="center")
        entry_f_count.pack(side="left", padx=5)
        entry_f_count.insert(0, str(self.config.get("friendly_count", 15)))

        row_f3 = ctk.CTkFrame(friendly_sub_frame, fg_color="transparent")
        row_f3.pack(fill="x", padx=15, pady=3)
        ctk.CTkLabel(row_f3, text=self.tr("settings_wait"), font=("Segoe UI", 11), width=60, anchor="w").pack(side="left", padx=5)
        entry_f_wait = ctk.CTkEntry(row_f3, width=80, height=26, justify="center")
        entry_f_wait.pack(side="left", padx=5)
        entry_f_wait.insert(0, str(self.config.get("friendly_wait", 1)))
        ctk.CTkLabel(row_f3, text=self.tr("settings_seconds"), font=("Segoe UI", 11)).pack(side="left", padx=5)

        # Muted caption
        lbl_caption = ctk.CTkLabel(
            friendly_sub_frame, text=self.tr("settings_friendly_note"),
            font=("Segoe UI", 9, "italic"), text_color=COLORS["text_muted"]
        )
        lbl_caption.pack(anchor="w", padx=15, pady=(5, 10))

        def toggle_friendly_entries():
            state = "normal" if friendly_enabled.get() else "disabled"
            entry_f_after.configure(state=state)
            entry_f_count.configure(state=state)
            entry_f_wait.configure(state=state)

        chk_friendly.configure(command=toggle_friendly_entries)
        toggle_friendly_entries()

        # =======================================================================
        # SAVE & CANCEL ACTIONS
        # =======================================================================
        def save_all():
            # Update Preset speeds
            val = preset_var.get()
            if val == self.tr("speed_very_slow"):
                val_min, val_max = 20, 30
            elif val == self.tr("speed_slow"):
                val_min, val_max = 12, 22
            elif val == self.tr("speed_normal"):
                val_min, val_max = 8, 15
            elif val == self.tr("speed_fast"):
                val_min, val_max = 4, 8
            else: # Very Fast
                val_min, val_max = 2, 4
            
            # Save Delays
            try:
                min_v = int(entry_min.get())
                max_v = int(entry_max.get())
                self.delay_min_entry.delete(0, "end")
                self.delay_min_entry.insert(0, str(min_v))
                self.delay_max_entry.delete(0, "end")
                self.delay_max_entry.insert(0, str(max_v))
                self.config.set("delay_min", min_v)
                self.config.set("delay_max", max_v)
            except ValueError:
                pass

            # Save Sleep Limits
            try:
                b_size = int(entry_sleep_size.get())
                b_max = int(entry_sleep_max.get())
                self.batch_size_entry.delete(0, "end")
                self.batch_size_entry.insert(0, str(b_size))
                self.batch_max_entry.delete(0, "end")
                self.batch_max_entry.insert(0, str(b_max))
                self.config.set("batch_size", b_size)
                self.config.set("batch_pause_max", b_max)
            except ValueError:
                pass

            # Extract data from Listboxes
            accs = list(listbox_accounts.get(0, "end"))
            msgs = list(listbox_dict.get(0, "end"))

            # Save Friendly details
            try:
                f_after = int(entry_f_after.get())
                f_count = int(entry_f_count.get())
                f_wait = int(entry_f_wait.get())
                self.config.set("friendly_after", f_after)
                self.config.set("friendly_count", f_count)
                self.config.set("friendly_wait", f_wait)
            except ValueError:
                pass

            self.config.set("sleep_enabled", sleep_enabled.get())
            self.config.set("friendly_enabled", friendly_enabled.get())
            self.config.set("friendly_numbers_list", accs)
            self.config.set("friendly_messages_list", msgs)
            self.config.set("friendly_numbers", ",".join(accs))
            self.config.set("friendly_messages", ",".join(msgs))
            
            # Now call the original settings save method to validate and commit config
            self._save_settings()
            
            self.config.save()
            self.log("⚙️ Sending Settings saved successfully!")
            dialog.destroy()
            self._ensure_background_settings_exist()

        btn_row = ctk.CTkFrame(dialog, fg_color="transparent", height=45)
        btn_row.pack(fill="x", side="bottom", padx=15, pady=15)

        btn_close = ctk.CTkButton(
            btn_row, text=self.tr("dialog_btn_close"), font=("Segoe UI", 12, "bold"),
            width=100, height=34, fg_color=COLORS["secondary"], hover_color=COLORS["secondary_hover"],
            text_color=COLORS["text_main"],
            command=save_all
        )
        btn_close.pack(side="right", padx=5)

    def _toggle_language(self):
        """Switch the application language between Arabic and English instantly."""
        new_lang = "en" if self.current_lang.get() == "ar" else "ar"
        self.current_lang.set(new_lang)
        self.config.set("language", new_lang)
        self.config.save()
        
        # Preserve current state
        active_tab = self.current_tab if hasattr(self, "current_tab") else "main"
        
        status_text = self.session_status_label.cget("text") if hasattr(self, "session_status_label") else ""
        status_color = None
        if hasattr(self, "status_indicator"):
            try:
                status_color = self.status_indicator.cget("text_color")
            except Exception:
                pass
                
        contacts = []
        if hasattr(self, "progress_tree") and self.progress_tree:
            for item in self.progress_tree.get_children():
                vals = self.progress_tree.item(item, "values")
                if len(vals) >= 3:
                    contacts.append({
                        "name": vals[0],
                        "phone": vals[1],
                        "var1": vals[2]
                    })
                    
        # Completely rebuild the UI with the new language
        self._rebuild_ui()
        
        # Restore tab, status, and contacts
        self._switch_tab(active_tab)
        if status_text:
            self._set_session_status(status_text, status_color)
        if contacts:
            self._refresh_numbers_table(contacts)

    def _rebuild_ui(self):
        """Completely rebuild the UI to apply language changes instantly."""
        self._save_current_state()
        
        if hasattr(self, "topbar_frame") and self.topbar_frame:
            try:
                self.topbar_frame.destroy()
            except Exception:
                pass
        if hasattr(self, "middle_frame") and self.middle_frame:
            try:
                self.middle_frame.destroy()
            except Exception:
                pass
        if hasattr(self, "bottom_bar") and self.bottom_bar:
            try:
                self.bottom_bar.destroy()
            except Exception:
                pass
                
        self._build_layout()
        self._load_saved_state()

    # ─── Bottom Status Bar ───────────────────────────────────────────────────

    def _build_bottom_bar(self):
        # Bottom Bar Container Frame
        """Build the bottom status bar with session info and stats."""
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
            text=self.tr("status_bar_disconnected"),
            font=("Segoe UI", 12),
            text_color=COLORS["text_muted"]
        )
        self.session_status_label.pack(side="left", padx=5)

    def _switch_tab(self, tab_id):
        """Switch visible tab and highlight the active menu button in the sidebar."""
        self.current_tab = tab_id
        for fid, frame in list(self.tab_frames.items()):
            try:
                if frame.winfo_exists():
                    frame.grid_forget()
                else:
                    # Remove destroyed frames so they don't cause issues again
                    del self.tab_frames[fid]
            except Exception:
                pass
        if tab_id in self.tab_frames and self.tab_frames[tab_id].winfo_exists():
            self.tab_frames[tab_id].grid(row=0, column=0, sticky="nsew", padx=0, pady=0)

        # Highlight active nav item in the sidebar
        is_dark = ctk.get_appearance_mode().lower() == "dark"
        for nid, btn in self.nav_buttons.items():
            if nid == tab_id:
                active_text = COLORS.get("primary", "#00FF9D") if is_dark else "#FFFFFF"
                btn.configure(
                    fg_color=COLORS.get("sidebar_active", "#1C2A4A"),
                    text_color=active_text
                )
            else:
                inactive_text = COLORS.get("text_muted", "#94A3B8") if is_dark else COLORS.get("sidebar_text", "#E9EDEF")
                btn.configure(
                    fg_color="transparent",
                    text_color=inactive_text
                )

    # ─── Main Tab (3-Column Workspace) ───────────────────────────────────────

    def _process_ui_queue(self):
        """Process pending UI updates from background threads."""
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
        """Schedule a function to run on the main UI thread."""
        self.ui_queue.put(fn)

    def _set_session_status(self, text, color=None):
        """Update the session status indicator text and color."""
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
                        except Exception as exc:
                            logger.debug("Session status monitor could not inspect browser state: %s", exc)
                            status = "closed"
                    else:
                        status = "offline"

                    if status != last_status:
                        last_status = status
                        self._run_on_ui(lambda s=status: self._update_session_status_from_monitor(s))
                except Exception as exc:
                    logger.debug("Session status monitor iteration failed: %s", exc)

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
            except Exception as exc:
                logger.debug("Could not write UI log line to stderr: %s", exc)

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
        except Exception as exc:
            logger.debug("Could not append UI log line to %s: %s", self.log_file_path, exc)

    def _on_bot_event(self, level, message, detail=None):
        """Callback from WhatsAppBot — same stream as UI log + terminal."""
        self.log(format_event(level, message, detail))

    def _open_log_file(self):
        """Open the application log file in the default text editor."""
        try:
            os.makedirs(self.log_dir, exist_ok=True)
            if os.path.exists(self.log_file_path):
                os.startfile(self.log_file_path)
            else:
                messagebox.showinfo("السجل", "لا يوجد ملف سجل بعد. ابدأ إرسالاً أولاً.")
        except Exception as e:
            messagebox.showerror("خطأ", str(e))

    def _clear_log(self):
        """Clear the event log display."""
        self.log_textbox.configure(state="normal")
        self.log_textbox.delete("1.0", "end")
        self.log_textbox.configure(state="disabled")
        self.log("تم مسح السجل.", level="INFO")

    def _agent_debug_log(self, hypothesis_id, location, message, data=None):
        # #region agent log
        """Log a detailed diagnostic entry for debugging automation issues."""
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
        except Exception as exc:
            logger.debug("Could not write agent debug log: %s", exc)
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
        """Show an info, warning, or error dialog on the UI thread."""
        def _do():
            if kind == "info":
                messagebox.showinfo(title, message)
            elif kind == "warning":
                messagebox.showwarning(title, message)
            else:
                messagebox.showerror(title, message)
        self._run_on_ui(_do)

    def report_error(self, code, message=None, detail=None, dialog=True, level="error"):
        """Report an error by code with optional dialog and log entry."""
        base_message = message or ERROR_CATALOG.get(code, "حدث خطأ غير معروف.")
        log_message = f"[{code}] {base_message}"
        if detail:
            log_message += f" | {detail}"
        self.log(log_message)
        if dialog:
            dialog_message = f"{base_message}\n\nالكود: {code}"
            self._show_dialog(level, "تنبيه" if level == "warning" else "خطأ", dialog_message)

    def _update_stats(self):
        """Refresh the sent/failed/invalid counters in the bottom bar."""
        total = self.sent + self.failed + self.invalid
        if hasattr(self, "stat_cards") and self.stat_cards:
            try:
                self.stat_cards["total"].configure(text=str(total))
                self.stat_cards["success"].configure(text=str(self.sent))
                self.stat_cards["failed"].configure(text=str(self.failed))
                self.stat_cards["invalid"].configure(text=str(self.invalid))
            except Exception as exc:
                logger.debug("Could not update stat cards: %s", exc)
        if hasattr(self, "counter_label") and self.counter_label and self.counter_label.winfo_exists():
            try:
                self.counter_label.configure(text=f"✅ {self.sent} | ❌ {self.failed} | 🚫 {self.invalid}")
            except Exception as exc:
                logger.debug("Could not update counter label: %s", exc)

    def _update_total_counts(self, total=0, contacts_count=0, groups_count=0):
        """Update total/contacts/groups counters in the bottom bar."""
        if hasattr(self, "total_counts_label"):
            self.total_counts_label.configure(
                text=f"الإجمالي: {total} | جهات: {contacts_count} | مجموعات: {groups_count}"
            )

    def _show_error_codes(self):
        """Display the error code reference dialog."""
        lines = [f"{code} — {desc}" for code, desc in ERROR_CATALOG.items()]
        self._show_dialog("info", "أكواد الأخطاء", "\n".join(lines))

    # ═══════════════════════════════════════════════════════════════════════
    #  FILE BROWSE
    # ═══════════════════════════════════════════════════════════════════════

    def _open_csv(self, path):
        """Open a CSV file in the system default application."""
        if path and os.path.exists(path):
            os.startfile(path)
        else:
            messagebox.showerror("خطأ", "ملف التقرير غير موجود.")

    # ═══════════════════════════════════════════════════════════════════════
    #  SETTINGS
    # ═══════════════════════════════════════════════════════════════════════

    def _ensure_background_settings_exist(self):
        """Ensure all background settings entries exist in memory on a hidden frame to prevent campaigns from crashing."""
        if not hasattr(self, "hidden_settings_frame"):
            self.hidden_settings_frame = ctk.CTkFrame(self)
        
        # Instantiate any missing entry/variable with saved config values
        if not hasattr(self, "delay_min_entry") or not self.delay_min_entry.winfo_exists():
            self.delay_min_entry = ctk.CTkEntry(self.hidden_settings_frame)
            self.delay_min_entry.insert(0, str(self.config.get("delay_min", 8)))
            
        if not hasattr(self, "delay_max_entry") or not self.delay_max_entry.winfo_exists():
            self.delay_max_entry = ctk.CTkEntry(self.hidden_settings_frame)
            self.delay_max_entry.insert(0, str(self.config.get("delay_max", 25)))
            
        if not hasattr(self, "batch_size_entry") or not self.batch_size_entry.winfo_exists():
            self.batch_size_entry = ctk.CTkEntry(self.hidden_settings_frame)
            self.batch_size_entry.insert(0, str(self.config.get("batch_size", 30)))
            
        if not hasattr(self, "batch_min_entry") or not self.batch_min_entry.winfo_exists():
            self.batch_min_entry = ctk.CTkEntry(self.hidden_settings_frame)
            self.batch_min_entry.insert(0, str(self.config.get("batch_pause_min", 180)))
            
        if not hasattr(self, "batch_max_entry") or not self.batch_max_entry.winfo_exists():
            self.batch_max_entry = ctk.CTkEntry(self.hidden_settings_frame)
            self.batch_max_entry.insert(0, str(self.config.get("batch_pause_max", 240)))

    def _save_settings(self):
        """Save all settings from the settings tab to config."""
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
        """Toggle between dark and light mode."""
        mode = self.appearance_switch.get()
        ctk.set_appearance_mode(mode)
        self.config.set_and_save("appearance_mode", mode)
        self._apply_palette(mode)
        self._refresh_theme()
        messagebox.showinfo("تم", "تم تغيير المظهر.")

    def _load_saved_state(self):
        # Load last used files
        """Restore UI state (contacts path, message, attachments) from config."""
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
        """Persist current UI state to config for next session."""
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
        """Handle application shutdown: save state, cleanup, destroy window."""
        if hasattr(self, "scheduler"):
            self.scheduler.stop()
        self._save_current_state()
        if self.bot:
            try:
                self.bot.close()
            except Exception:
                pass
        for p, active_bot in list(self.active_bots.items()):
            try:
                active_bot.close()
            except Exception:
                pass
        try:
            from utils.helpers import cleanup_old_reports
            cleanup_old_reports(max_age_days=30)
        except Exception as cleanup_exc:
            logger.debug("Automatic report cleanup failed: %s", cleanup_exc)
        self.destroy()


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

    def _check_and_cleanup_dead_bot(self):
        """Check if self.bot has a dead/closed browser and set self.bot to None if so."""
        if self.bot:
            is_alive = False
            if self.bot.driver:
                try:
                    is_alive = len(self.bot.driver.window_handles) > 0
                except Exception:
                    is_alive = False
            if not is_alive:
                try:
                    self.bot.close()
                except Exception:
                    pass
                self.bot = None

    def _login_action(self):
        # Check if the bot exists and the driver is actively open (has windows)
        """Initialize the browser and start the login process."""
        self._check_and_cleanup_dead_bot()
        is_active = self.bot is not None

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
        """Execute a queued send/check action after login completes."""
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
        """List available browser profile directories."""
        try:
            profiles = [d for d in os.listdir(self.profiles_dir) if os.path.isdir(os.path.join(self.profiles_dir, d))]
            if os.path.exists(self.legacy_profile_dir) and "Legacy" not in profiles:
                profiles.append("Legacy")
            return profiles
        except Exception as exc:
            logger.debug("Could not list profiles, falling back to Default: %s", exc)
            return ["Default"]

    def _on_add_profile_click(self):
        """Create a new browser profile folder and refresh combobox."""
        dialog = ctk.CTkInputDialog(text="أدخل اسم الحساب الجديد (بالأحرف الإنجليزية فقط):", title="إضافة حساب جديد")
        name = dialog.get_input()
        if not name:
            return
        name = name.strip()
        if not all(c.isalnum() or c in "-_" for c in name):
            messagebox.showerror("خطأ", "اسم الحساب غير صالح. يرجى استخدام الحروف والأرقام فقط.")
            return
        profile_path = os.path.join(self.profiles_dir, name)
        if os.path.exists(profile_path):
            messagebox.showwarning("تنبيه", "هذا الحساب موجود بالفعل.")
            return
        try:
            os.makedirs(profile_path, exist_ok=True)
            self.profile_combo.configure(values=self._get_profiles())
            self.profile_var.set(name)
            self._on_profile_change(name)
            messagebox.showinfo("تم", f"تم إنشاء الحساب '{name}' بنجاح وتبديل النشط إليه.")
        except Exception as exc:
            messagebox.showerror("خطأ", f"تعذر إنشاء الحساب: {exc}")

    def _on_profile_change(self, choice):
        """Handle profile selection change — update paths and proxy settings."""
        self._check_and_cleanup_dead_bot()
        if self.bot is not None:
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
        """Create a new browser profile directory."""
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

    def _load_profile_proxy_settings(self, profile_name):
        """Load proxy configuration for the selected profile."""
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
        """Test the configured proxy connection in a background thread."""
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
        """Generate a random browser fingerprint for the profile."""
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

    def _show_help_dialog(self):
        """Display the help/documentation dialog."""
        self._show_dialog("info", "دليل الاستخدام والمساعدة", "دليل الاستخدام:\n1. قم بفتح تطبيق WhatsApp وسجل الدخول باستخدام رمز الاستجابة السريعة (QR Code).\n2. استورد الأرقام باستخدام زر الاستيراد أو قم بإدخالها يدوياً.\n3. اكتب الرسالة في المحرر وأضف أي ملفات مرفقة إن وجدت.\n4. اضغط على زر 'ارسل الآن' لبدء الحملة الإعلانية.")

    def _show_about_dialog(self):
        """Display the about dialog with version info."""
        self._show_dialog("info", "حول البرنامج", "WhatsApp Sender Pro\nالإصدار v17.0\nمطور ومحسن لتوفير أقصى درجات الحماية والسرعة.\nالبرنامج يدعم حماية بصمة المتصفح ونظام منع الحظر التلقائي الذكي.")

    def _logout_action(self):
        """Log out of WhatsApp by closing the browser session."""
        if self.bot:
            try:
                self.bot.close()
            except Exception as exc:
                logger.debug("Could not close bot during logout: %s", exc)
            self.bot = None
            self.session_status_label.configure(text="Disconnected | Not Ready | Account: N/A")
            self.status_indicator.configure(text_color=COLORS["danger"])
            self.log("🚪 تم تسجيل الخروج بنجاح وإغلاق المتصفح.")
            self._show_dialog("info", "تسجيل الخروج", "تم تسجيل الخروج وإغلاق متصفح WhatsApp بنجاح.")
        else:
            self._show_dialog("warning", "تسجيل الخروج", "المتصفح مغلق بالفعل.")

    def _toggle_appearance_menu(self):
        """Toggle appearance from the menu bar."""
        current_mode = ctk.get_appearance_mode().lower()
        new_mode = "light" if current_mode == "dark" else "dark"
        ctk.set_appearance_mode(new_mode)
        self.config.set("appearance_mode", new_mode)
        self._apply_palette(new_mode)
        self._refresh_theme()

    # â”€â”€â”€ GMaps Scraper Methods â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


