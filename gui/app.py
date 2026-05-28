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
        except Exception as exc:
            logger.debug("Could not apply ttk clam theme: %s", exc)

        bg_color = COLORS["bg_dark"]
        fg_color = COLORS["text_main"]
        card_bg = COLORS["card_bg"]
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
        """Build the main application layout: sidebar menu + content area."""

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
        settings_menu.add_command(label=self.tr("menu_settings_send_delay"), command=lambda: self._switch_tab("settings"))
        settings_menu.add_command(label=self.tr("menu_settings_proxy"), command=lambda: self._switch_tab("settings"))
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

    # ─── Top Horizontal Toolbar ──────────────────────────────────────────────

    def _build_top_toolbar(self):
        # Toolbar Main Container Frame
        """Build the top toolbar with profile selector and action buttons."""
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
            (self.tr("tab_events"), "log"),
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
        
        self.btn_add_profile = ctk.CTkButton(
            tb_content, text="➕", font=("Segoe UI", 12, "bold"),
            width=28, height=36, corner_radius=6,
            fg_color=COLORS["secondary"], hover_color=COLORS["secondary_hover"],
            text_color=COLORS["secondary_text"],
            command=self._on_add_profile_click
        )
        self.btn_add_profile.pack(side="left", padx=2, pady=8)
        
        lbl_profile = ctk.CTkLabel(tb_content, text=self.tr("lbl_account"), font=("Segoe UI", 11), text_color=COLORS["text_muted"])
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
        
        if hasattr(self, "toolbar_frame") and self.toolbar_frame:
            try:
                self.toolbar_frame.destroy()
            except Exception:
                pass
        if hasattr(self, "main_frame") and self.main_frame:
            try:
                self.main_frame.destroy()
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

        # Schedule Button
        self.btn_schedule = ctk.CTkButton(
            actions_frame, text=self.tr("btn_schedule_campaign"),
            font=("Segoe UI", 12, "bold"),
            width=115, height=32, corner_radius=6,
            fg_color=COLORS["secondary"], hover_color=COLORS["secondary_hover"],
            text_color=COLORS["secondary_text"],
            command=self._schedule_action
        )
        self.btn_schedule.pack(side="right", padx=5)

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
        """Switch visible tab and highlight the active menu button."""
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

    def _login_action(self):
        # Check if the bot exists and the driver is actively open (has windows)
        """Initialize the browser and start the login process."""
        is_active = False
        if self.bot and self.bot.driver:
            try:
                is_active = len(self.bot.driver.window_handles) > 0
            except Exception as exc:
                logger.debug("Could not inspect browser window handles: %s", exc)
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


