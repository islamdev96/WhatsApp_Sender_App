"""WhatsApp Sender Pro — Account Warmer Tab builder module.

Provides tools to warm up WhatsApp accounts by sending natural
conversational messages to friendly contacts periodically.
"""
import customtkinter as ctk
from tkinter import ttk, messagebox, Listbox
import threading
import datetime

from gui.theme import COLORS
from utils.logger import logger


def build_warmer_tab(self, frame: ctk.CTkFrame) -> None:
    """Build the Account Warmer tab with friendly contacts, message templates, and session log."""
    self.tab_frames["warmer"] = frame

    is_ar = self.current_lang.get() == "ar"
    anchor_val = "e" if is_ar else "w"
    side_lbl = "right" if is_ar else "left"
    side_opp = "left" if is_ar else "right"

    # ── Header ──
    header = ctk.CTkLabel(frame, text=self.tr("warmer_header"),
                          font=ctk.CTkFont(size=20, weight="bold"))
    header.pack(anchor=anchor_val, padx=25, pady=(20, 5))

    desc = ctk.CTkLabel(frame, text=self.tr("warmer_desc"),
                        font=ctk.CTkFont(size=12), text_color=COLORS["text_muted"])
    desc.pack(anchor=anchor_val, padx=25, pady=(0, 10))

    # ── Main body: 2 columns ──
    body = ctk.CTkFrame(frame, fg_color="transparent")
    body.pack(fill="both", expand=True, padx=20, pady=5)
    body.grid_columnconfigure(0, weight=1)
    body.grid_columnconfigure(1, weight=1)
    body.grid_rowconfigure(0, weight=1)

    # ── LEFT: Warmer Contacts ──
    left_frame = ctk.CTkFrame(body, corner_radius=12)
    left_frame.grid(row=0, column=0, padx=(0, 5), pady=5, sticky="nsew")

    ctk.CTkLabel(left_frame, text=self.tr("warmer_contacts_title"),
                 font=ctk.CTkFont(size=14, weight="bold")).pack(anchor=anchor_val, padx=15, pady=(12, 5))

    warmer_contacts_listbox = Listbox(
        left_frame, height=8, bg="#FFFFFF", fg="#000000",
        selectbackground=COLORS["primary"], selectforeground="#FFFFFF",
        borderwidth=1, relief="solid", highlightthickness=0,
        font=("Segoe UI", 11)
    )
    warmer_contacts_listbox.pack(fill="both", expand=True, padx=15, pady=5)

    # Load saved warmer contacts
    saved_contacts = self.config.get("warmer_contacts", [])
    for c in saved_contacts:
        warmer_contacts_listbox.insert("end", c)

    btn_row_contacts = ctk.CTkFrame(left_frame, fg_color="transparent")
    btn_row_contacts.pack(fill="x", padx=15, pady=(0, 10))

    def _add_warmer_contact():
        dialog = ctk.CTkInputDialog(text=self.tr("warmer_add_contact_prompt"), title=self.tr("warmer_contacts_title"))
        val = dialog.get_input()
        if val and val.strip():
            warmer_contacts_listbox.insert("end", val.strip())

    def _del_warmer_contact():
        sel = warmer_contacts_listbox.curselection()
        if sel:
            warmer_contacts_listbox.delete(sel[0])

    ctk.CTkButton(btn_row_contacts, text=self.tr("btn_add_rule"), width=80, height=30,
                  fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"],
                  text_color="#FFFFFF", command=_add_warmer_contact).pack(side=side_lbl, padx=3)
    ctk.CTkButton(btn_row_contacts, text=self.tr("groups_btn_delete"), width=80, height=30,
                  fg_color=COLORS["danger"], hover_color=COLORS["danger_hover"],
                  text_color="#FFFFFF", command=_del_warmer_contact).pack(side=side_lbl, padx=3)

    # ── Messages section in left frame ──
    ctk.CTkLabel(left_frame, text=self.tr("warmer_messages_title"),
                 font=ctk.CTkFont(size=14, weight="bold")).pack(anchor=anchor_val, padx=15, pady=(10, 5))

    warmer_msg_listbox = Listbox(
        left_frame, height=5, bg="#FFFFFF", fg="#000000",
        selectbackground=COLORS["primary"], selectforeground="#FFFFFF",
        borderwidth=1, relief="solid", highlightthickness=0,
        font=("Segoe UI", 11)
    )
    warmer_msg_listbox.pack(fill="both", expand=True, padx=15, pady=5)

    saved_msgs = self.config.get("warmer_messages", [
        "السلام عليكم، كيف حالك؟",
        "مرحبا! شو أخبارك اليوم؟",
        "{مرحبا|أهلاً|هلا} {كيف حالك|شلونك|إيش أخبارك}؟"
    ])
    for m in saved_msgs:
        warmer_msg_listbox.insert("end", m)

    btn_row_msgs = ctk.CTkFrame(left_frame, fg_color="transparent")
    btn_row_msgs.pack(fill="x", padx=15, pady=(0, 12))

    def _add_warmer_msg():
        dialog = ctk.CTkInputDialog(text=self.tr("warmer_add_msg_prompt"), title=self.tr("warmer_messages_title"))
        val = dialog.get_input()
        if val and val.strip():
            warmer_msg_listbox.insert("end", val.strip())

    def _del_warmer_msg():
        sel = warmer_msg_listbox.curselection()
        if sel:
            warmer_msg_listbox.delete(sel[0])

    ctk.CTkButton(btn_row_msgs, text=self.tr("btn_add_rule"), width=80, height=30,
                  fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"],
                  text_color="#FFFFFF", command=_add_warmer_msg).pack(side=side_lbl, padx=3)
    ctk.CTkButton(btn_row_msgs, text=self.tr("groups_btn_delete"), width=80, height=30,
                  fg_color=COLORS["danger"], hover_color=COLORS["danger_hover"],
                  text_color="#FFFFFF", command=_del_warmer_msg).pack(side=side_lbl, padx=3)

    # ── RIGHT: Settings + Session Log ──
    right_frame = ctk.CTkFrame(body, corner_radius=12)
    right_frame.grid(row=0, column=1, padx=(5, 0), pady=5, sticky="nsew")

    ctk.CTkLabel(right_frame, text=self.tr("warmer_settings_title"),
                 font=ctk.CTkFont(size=14, weight="bold")).pack(anchor=anchor_val, padx=15, pady=(12, 5))

    # Interval setting
    interval_row = ctk.CTkFrame(right_frame, fg_color="transparent")
    interval_row.pack(fill="x", padx=15, pady=3)
    ctk.CTkLabel(interval_row, text=self.tr("warmer_interval"),
                 font=ctk.CTkFont(size=12)).pack(side=side_lbl, padx=5)
    self.warmer_interval_entry = ctk.CTkEntry(interval_row, width=80, height=30, justify="center")
    self.warmer_interval_entry.pack(side=side_lbl, padx=5)
    self.warmer_interval_entry.insert(0, str(self.config.get("warmer_interval", 30)))
    ctk.CTkLabel(interval_row, text=self.tr("warmer_minutes"),
                 font=ctk.CTkFont(size=12)).pack(side=side_lbl, padx=5)

    # Daily limit setting
    limit_row = ctk.CTkFrame(right_frame, fg_color="transparent")
    limit_row.pack(fill="x", padx=15, pady=3)
    ctk.CTkLabel(limit_row, text=self.tr("warmer_daily_limit"),
                 font=ctk.CTkFont(size=12)).pack(side=side_lbl, padx=5)
    self.warmer_limit_entry = ctk.CTkEntry(limit_row, width=80, height=30, justify="center")
    self.warmer_limit_entry.pack(side=side_lbl, padx=5)
    self.warmer_limit_entry.insert(0, str(self.config.get("warmer_daily_limit", 20)))
    ctk.CTkLabel(limit_row, text=self.tr("settings_messages"),
                 font=ctk.CTkFont(size=12)).pack(side=side_lbl, padx=5)

    # Use Spintax checkbox
    self.warmer_spintax_var = ctk.BooleanVar(value=self.config.get("warmer_use_spintax", True))
    ctk.CTkCheckBox(right_frame, text=self.tr("warmer_use_spintax"),
                    variable=self.warmer_spintax_var,
                    font=ctk.CTkFont(size=12)).pack(anchor=anchor_val, padx=20, pady=8)

    # Session log
    ctk.CTkLabel(right_frame, text=self.tr("warmer_session_log"),
                 font=ctk.CTkFont(size=14, weight="bold")).pack(anchor=anchor_val, padx=15, pady=(10, 5))

    self.warmer_log_box = ctk.CTkTextbox(right_frame, height=150, corner_radius=8,
                                          font=ctk.CTkFont(size=11),
                                          fg_color=COLORS["bg_dark"])
    self.warmer_log_box.pack(fill="both", expand=True, padx=15, pady=(0, 10))
    self.warmer_log_box.configure(state="disabled")

    # ── Action Buttons ──
    action_frame = ctk.CTkFrame(frame, fg_color="transparent")
    action_frame.pack(fill="x", padx=20, pady=(5, 15))

    self._warmer_running = False
    self._warmer_stop_event = threading.Event()

    def _start_warmer():
        contacts = list(warmer_contacts_listbox.get(0, "end"))
        messages = list(warmer_msg_listbox.get(0, "end"))
        if not contacts:
            messagebox.showwarning(self.tr("msg_alert"), self.tr("warmer_no_contacts"))
            return
        if not messages:
            messagebox.showwarning(self.tr("msg_alert"), self.tr("warmer_no_messages"))
            return
        if not self.bot:
            messagebox.showwarning(self.tr("msg_alert"), self.tr("filter_need_login"))
            return

        # Save settings
        self.config.set("warmer_contacts", contacts)
        self.config.set("warmer_messages", messages)
        try:
            self.config.set("warmer_interval", int(self.warmer_interval_entry.get()))
            self.config.set("warmer_daily_limit", int(self.warmer_limit_entry.get()))
        except ValueError:
            pass
        self.config.set("warmer_use_spintax", self.warmer_spintax_var.get())
        self.config.save()

        self._warmer_running = True
        self._warmer_stop_event.clear()
        self.warmer_start_btn.configure(state="disabled")
        self.warmer_stop_btn.configure(state="normal")

        def _warmer_log(msg):
            self._run_on_ui(lambda: (
                self.warmer_log_box.configure(state="normal"),
                self.warmer_log_box.insert("end", f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {msg}\n"),
                self.warmer_log_box.see("end"),
                self.warmer_log_box.configure(state="disabled"),
            ))

        def _warmer_thread():
            import time
            import random
            from utils.helpers.text import resolve_spintax

            interval = int(self.warmer_interval_entry.get()) * 60
            daily_limit = int(self.warmer_limit_entry.get())
            use_spintax = self.warmer_spintax_var.get()
            sent_count = 0

            _warmer_log(self.tr("warmer_started"))

            while not self._warmer_stop_event.is_set() and sent_count < daily_limit:
                contact = random.choice(contacts)
                message = random.choice(messages)
                if use_spintax:
                    message = resolve_spintax(message)

                try:
                    self.bot.send_message(contact, message)
                    sent_count += 1
                    _warmer_log(f"✅ → {contact}: {message[:50]}...")
                except Exception as exc:
                    _warmer_log(f"❌ {contact}: {exc}")

                # Wait interval
                for _ in range(interval):
                    if self._warmer_stop_event.is_set():
                        break
                    time.sleep(1)

            self._warmer_running = False
            self._run_on_ui(lambda: self.warmer_start_btn.configure(state="normal"))
            self._run_on_ui(lambda: self.warmer_stop_btn.configure(state="disabled"))
            _warmer_log(self.tr("warmer_finished").format(count=sent_count))

        t = threading.Thread(target=_warmer_thread, daemon=True)
        t.start()

    def _stop_warmer():
        self._warmer_stop_event.set()
        self.warmer_stop_btn.configure(state="disabled")

    self.warmer_start_btn = ctk.CTkButton(
        action_frame, text=self.tr("warmer_btn_start"),
        font=ctk.CTkFont(size=14, weight="bold"),
        width=180, height=42, corner_radius=10,
        fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"],
        text_color="#FFFFFF", command=_start_warmer
    )
    self.warmer_start_btn.pack(side=side_lbl, padx=5)

    self.warmer_stop_btn = ctk.CTkButton(
        action_frame, text=self.tr("warmer_btn_stop"),
        font=ctk.CTkFont(size=14, weight="bold"),
        width=140, height=42, corner_radius=10,
        fg_color=COLORS["danger"], hover_color=COLORS["danger_hover"],
        text_color="#FFFFFF", state="disabled", command=_stop_warmer
    )
    self.warmer_stop_btn.pack(side=side_lbl, padx=5)
