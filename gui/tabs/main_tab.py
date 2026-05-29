"""WhatsApp Sender Pro — Main Tab builder module."""
import customtkinter as ctk
from tkinter import ttk, messagebox
import json
import os
import time
import datetime
import threading
from gui.theme import COLORS
from gui.components import RichTextFrame, AttachmentManager
from utils.logger import logger

def build_main_tab(self, frame: ctk.CTkFrame) -> None:
    """Build the main sending tab with 3 columns: Left (Auto-Reply & Received), Middle (Numbers), Right (Message & Attachments)."""
    self.tab_frames["main"] = frame

    # Three-column layout
    frame.grid_columnconfigure(0, weight=3, minsize=320)  # Left Column: Auto Reply & Received Messages
    frame.grid_columnconfigure(1, weight=3, minsize=360)  # Middle Column: Whatsapp Numbers List
    frame.grid_columnconfigure(2, weight=4, minsize=400)  # Right Column: Message & Attachments
    frame.grid_rowconfigure(0, weight=1)

    # =======================================================================
    # HELPER METHODS FOR AUTO-REPLY RULES (Attached to self dynamically)
    # =======================================================================
    def _load_auto_reply_rules():
        path = os.path.join("data", "auto_reply_rules.json")
        if not os.path.exists(path):
            # Create a default rules file if it doesn't exist
            defaults = [
                {"rule_name": "ترحيب", "keywords": "مرحبا, سلام, هلا", "reply": "أهلاً بك! كيف يمكنني مساعدتك اليوم؟", "enabled": True},
                {"rule_name": "الأسعار", "keywords": "سعر, اسعار, بكم", "reply": "أسعار باقاتنا تبدأ من 20 دولار شهرياً فقط. لمزيد من التفاصيل يرجى التواصل معنا.", "enabled": True}
            ]
            os.makedirs("data", exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(defaults, f, ensure_ascii=False, indent=4)
            return defaults
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as exc:
            logger.debug("Could not load auto reply rules: %s", exc)
            return []

    def _save_auto_reply_rules(rules):
        path = os.path.join("data", "auto_reply_rules.json")
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(rules, f, ensure_ascii=False, indent=4)
        except Exception as exc:
            logger.debug("Could not save auto reply rules: %s", exc)

    def _refresh_auto_reply_rules_table():
        if not hasattr(self, "auto_reply_rules_tree"):
            return
        for item in self.auto_reply_rules_tree.get_children():
            self.auto_reply_rules_tree.delete(item)
        rules = _load_auto_reply_rules()
        for r in rules:
            status_txt = self.tr("status_connected") if r.get("enabled", True) else self.tr("status_disconnected")
            self.auto_reply_rules_tree.insert("", "end", values=(r.get("rule_name", ""), r.get("keywords", ""), status_txt))

    def _on_rule_double_click(event):
        selected = self.auto_reply_rules_tree.selection()
        if not selected:
            return
        item = selected[0]
        rule_name = self.auto_reply_rules_tree.item(item, "values")[0]
        rules = _load_auto_reply_rules()
        for r in rules:
            if r.get("rule_name") == rule_name:
                r["enabled"] = not r.get("enabled", True)
                break
        _save_auto_reply_rules(rules)
        _refresh_auto_reply_rules_table()

    def _open_add_rule_dialog():
        win = ctk.CTkToplevel(self)
        win.title(self.tr("btn_add_rule"))
        win.geometry("420x360")
        win.resizable(False, False)
        win.grab_set()
        win.transient(self)
        
        win.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() - 420) // 2
        y = self.winfo_y() + (self.winfo_height() - 360) // 2
        win.geometry(f"+{x}+{y}")
        
        is_ar = self.current_lang.get() == "ar"
        anchor_val = "e" if is_ar else "w"
        side_lbl = "right" if is_ar else "left"
        side_opp = "left" if is_ar else "right"
        
        ctk.CTkLabel(win, text=self.tr("btn_add_rule"), font=("Segoe UI", 14, "bold"), text_color=COLORS["primary"]).pack(pady=15)
        
        ctk.CTkLabel(win, text=self.tr("lbl_rules_name") + ":", font=("Segoe UI", 11, "bold")).pack(anchor=anchor_val, padx=25, pady=(5, 2))
        entry_name = ctk.CTkEntry(win, height=32)
        entry_name.pack(fill="x", padx=25)
        
        ctk.CTkLabel(win, text=self.tr("lbl_keywords") + ":", font=("Segoe UI", 11, "bold")).pack(anchor=anchor_val, padx=25, pady=(10, 2))
        entry_kws = ctk.CTkEntry(win, height=32, placeholder_text="مرحبا, سلام, هلا")
        entry_kws.pack(fill="x", padx=25)
        
        ctk.CTkLabel(win, text=self.tr("tab_message") + ":", font=("Segoe UI", 11, "bold")).pack(anchor=anchor_val, padx=25, pady=(10, 2))
        entry_reply = ctk.CTkEntry(win, height=32)
        entry_reply.pack(fill="x", padx=25)
        
        btn_row = ctk.CTkFrame(win, fg_color="transparent")
        btn_row.pack(fill="x", padx=25, pady=(20, 10))
        
        def save():
            name = entry_name.get().strip()
            kws = entry_kws.get().strip()
            reply = entry_reply.get().strip()
            if not name or not kws or not reply:
                messagebox.showwarning(self.tr("msg_alert"), "Please fill all fields / يرجى ملء جميع الحقول")
                return
            
            rules = _load_auto_reply_rules()
            rules.append({
                "rule_name": name,
                "keywords": kws,
                "reply": reply,
                "enabled": True
            })
            _save_auto_reply_rules(rules)
            _refresh_auto_reply_rules_table()
            win.destroy()
            
        ctk.CTkButton(btn_row, text=self.tr("dialog_btn_import"), fg_color=COLORS["primary"], text_color="#FFFFFF", font=("Segoe UI", 11, "bold"), width=100, command=save).pack(side=side_lbl, padx=5)
        ctk.CTkButton(btn_row, text=self.tr("dialog_btn_cancel"), fg_color=COLORS["secondary"], hover_color=COLORS["secondary_hover"], text_color=COLORS["secondary_text"], width=80, command=win.destroy).pack(side=side_opp, padx=5)

    def _delete_selected_rule():
        selected = self.auto_reply_rules_tree.selection()
        if not selected:
            return
        item = selected[0]
        rule_name = self.auto_reply_rules_tree.item(item, "values")[0]
        
        if messagebox.askyesno(self.tr("msg_confirm"), f"Delete rule '{rule_name}'? / هل تريد حذف هذه القاعدة؟"):
            rules = _load_auto_reply_rules()
            rules = [r for r in rules if r.get("rule_name") != rule_name]
            _save_auto_reply_rules(rules)
            _refresh_auto_reply_rules_table()

    def _run_auto_reply_loop():
        """Periodically check unread chats and reply automatically based on rules."""
        if not hasattr(self, "auto_reply_enabled") or not self.auto_reply_enabled.get():
            self.after(3000, _run_auto_reply_loop)
            return

        if not self.bot or not self.bot.driver:
            self.after(3000, _run_auto_reply_loop)
            return

        if not self.bot.is_logged_in():
            self.after(3000, _run_auto_reply_loop)
            return

        if self.is_running:
            self.after(3000, _run_auto_reply_loop)
            return

        def worker():
            try:
                unread_chats = self.bot.get_unread_chats()
                if not unread_chats:
                    return

                rules = _load_auto_reply_rules()
                enabled_rules = [r for r in rules if r.get("enabled", True)]
                if not enabled_rules:
                    return

                for chat in unread_chats:
                    if self.is_running:
                        break
                    if not self.auto_reply_enabled.get():
                        break

                    if self.bot.open_chat_element(chat):
                        time.sleep(1.5)
                        sender_name = self.bot.get_active_chat_name()
                        last_msg = self.bot.read_last_message()
                        if not last_msg:
                            continue

                        matched_reply = None
                        for rule in enabled_rules:
                            keywords = [kw.strip().lower() for kw in rule.get("keywords", "").split(",") if kw.strip()]
                            last_msg_lower = last_msg.lower()
                            if any(kw in last_msg_lower for kw in keywords):
                                matched_reply = rule.get("reply", "")
                                break

                        if matched_reply:
                            self.bot.reply_to_current_chat(matched_reply)
                            self.log(f"🤖 [Auto Reply] Sent to {sender_name}: {matched_reply}")
                            
                            # Add to received table
                            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            if hasattr(self, "received_messages_tree"):
                                self._run_on_ui(lambda: self.received_messages_tree.insert("", 0, values=(now, sender_name, last_msg)))
            except Exception as exc:
                logger.debug("Error in auto reply loop worker: %s", exc)

        threading.Thread(target=worker, daemon=True).start()
        self.after(5000, _run_auto_reply_loop)

    # Attach helper methods to self dynamically
    self._load_auto_reply_rules = _load_auto_reply_rules
    self._save_auto_reply_rules = _save_auto_reply_rules
    self._refresh_auto_reply_rules_table = _refresh_auto_reply_rules_table
    self._on_rule_double_click = _on_rule_double_click
    self._open_add_rule_dialog = _open_add_rule_dialog
    self._delete_selected_rule = _delete_selected_rule
    self._run_auto_reply_loop = _run_auto_reply_loop

    # =======================================================================
    # COLUMN 0: Left Column (Auto-Reply chatbot rules & Received messages list)
    # =======================================================================
    col_left = ctk.CTkFrame(frame, corner_radius=8, border_width=1, border_color=COLORS["border"])
    col_left.grid(row=0, column=0, sticky="nsew", padx=3, pady=5)
    col_left.grid_rowconfigure(0, weight=1)  # Auto reply
    col_left.grid_rowconfigure(1, weight=1)  # Received message
    col_left.grid_columnconfigure(0, weight=1)

    # --- Upper Card: Auto Reply Rules ---
    card_rules = ctk.CTkFrame(col_left, fg_color="transparent")
    card_rules.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
    card_rules.grid_rowconfigure(1, weight=1)
    card_rules.grid_columnconfigure(0, weight=1)

    hdr_left = ctk.CTkFrame(card_rules, fg_color="transparent", height=35)
    hdr_left.grid(row=0, column=0, sticky="ew", pady=(2, 5))
    
    lbl_left = ctk.CTkLabel(hdr_left, text="🤖 " + self.tr("tab_auto_reply_rules"), font=("Segoe UI", 14, "bold"), text_color=COLORS["primary"])
    lbl_left.pack(side="right", padx=5)

    self.auto_reply_enabled = ctk.BooleanVar(value=False)
    self.switch_auto_reply = ctk.CTkSwitch(
        hdr_left, text="", variable=self.auto_reply_enabled,
        progress_color=COLORS["primary"],
        command=lambda: self.log("🤖 تفعيل الرد الآلي: " + str(self.auto_reply_enabled.get()))
    )
    self.switch_auto_reply.pack(side="left", padx=5)

    # Auto Reply Treeview
    rules_table_frame = ctk.CTkFrame(card_rules, fg_color="transparent")
    rules_table_frame.grid(row=1, column=0, sticky="nsew", pady=5)

    rules_cols = ("rule_name", "keywords", "status")
    self.auto_reply_rules_tree = ttk.Treeview(rules_table_frame, columns=rules_cols, show="headings", height=6)
    self.auto_reply_rules_tree.heading("rule_name", text=self.tr("lbl_rules_name"))
    self.auto_reply_rules_tree.heading("keywords", text=self.tr("lbl_keywords"))
    self.auto_reply_rules_tree.heading("status", text=self.tr("lbl_status"))

    self.auto_reply_rules_tree.column("rule_name", width=90, anchor="e")
    self.auto_reply_rules_tree.column("keywords", width=120, anchor="e")
    self.auto_reply_rules_tree.column("status", width=70, anchor="center")

    rules_scroll = ctk.CTkScrollbar(rules_table_frame, command=self.auto_reply_rules_tree.yview)
    self.auto_reply_rules_tree.configure(yscrollcommand=rules_scroll.set)
    rules_scroll.pack(side="right", fill="y")
    self.auto_reply_rules_tree.pack(side="left", fill="both", expand=True)

    # Rules double click binding
    self.auto_reply_rules_tree.bind("<Double-1>", self._on_rule_double_click)

    # Rules Add/Del Buttons
    rules_btns = ctk.CTkFrame(card_rules, fg_color="transparent", height=30)
    rules_btns.grid(row=2, column=0, sticky="ew", pady=(2, 2))

    self.btn_add_rule = ctk.CTkButton(
        rules_btns, text="+ " + self.tr("btn_add_rule"), font=("Segoe UI", 11, "bold"),
        width=100, height=28, corner_radius=6,
        fg_color=COLORS["success"], hover_color=COLORS["primary_hover"],
        text_color="#FFFFFF", command=self._open_add_rule_dialog
    )
    self.btn_add_rule.pack(side="right", padx=5)

    self.btn_del_rule = ctk.CTkButton(
        rules_btns, text="- " + self.tr("btn_delete_rule"), font=("Segoe UI", 11, "bold"),
        width=70, height=28, corner_radius=6,
        fg_color=COLORS["danger"], hover_color=COLORS["danger_hover"],
        text_color="#FFFFFF", command=self._delete_selected_rule
    )
    self.btn_del_rule.pack(side="right", padx=5)

    # --- Lower Card: Received Messages ---
    card_received = ctk.CTkFrame(col_left, fg_color="transparent")
    card_received.grid(row=1, column=0, sticky="nsew", padx=8, pady=8)
    card_received.grid_rowconfigure(1, weight=1)
    card_received.grid_columnconfigure(0, weight=1)

    hdr_received = ctk.CTkFrame(card_received, fg_color="transparent", height=35)
    hdr_received.grid(row=0, column=0, sticky="ew", pady=(2, 5))

    lbl_received = ctk.CTkLabel(hdr_received, text="📥 " + self.tr("tab_received_messages"), font=("Segoe UI", 14, "bold"), text_color=COLORS["primary"])
    lbl_received.pack(side="right", padx=5)

    # Received Messages Treeview
    rec_table_frame = ctk.CTkFrame(card_received, fg_color="transparent")
    rec_table_frame.grid(row=1, column=0, sticky="nsew", pady=5)

    rec_cols = ("date", "sender", "message")
    self.received_messages_tree = ttk.Treeview(rec_table_frame, columns=rec_cols, show="headings", height=6)
    self.received_messages_tree.heading("date", text=self.tr("lbl_date"))
    self.received_messages_tree.heading("sender", text=self.tr("lbl_sender"))
    self.received_messages_tree.heading("message", text=self.tr("lbl_message"))

    self.received_messages_tree.column("date", width=110, anchor="center")
    self.received_messages_tree.column("sender", width=100, anchor="e")
    self.received_messages_tree.column("message", width=140, anchor="e")

    rec_scroll = ctk.CTkScrollbar(rec_table_frame, command=self.received_messages_tree.yview)
    self.received_messages_tree.configure(yscrollcommand=rec_scroll.set)
    rec_scroll.pack(side="right", fill="y")
    self.received_messages_tree.pack(side="left", fill="both", expand=True)

    # Load and refresh rules list initially
    _refresh_auto_reply_rules_table()
    
    # Start background auto reply daemon loop
    self.after(3000, self._run_auto_reply_loop)

    # =======================================================================
    # COLUMN 1: Middle Column (Whatsapp Numbers List)
    # =======================================================================
    col_mid = ctk.CTkFrame(frame, corner_radius=8, border_width=1, border_color=COLORS["border"])
    col_mid.grid(row=0, column=1, sticky="nsew", padx=3, pady=5)
    col_mid.grid_rowconfigure(3, weight=1)
    col_mid.grid_columnconfigure(0, weight=1)

    # Header for WhatsApp Numbers
    hdr_mid = ctk.CTkFrame(col_mid, fg_color="transparent", height=35)
    hdr_mid.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
    
    lbl_mid = ctk.CTkLabel(hdr_mid, text="📋 " + self.tr("tab_whatsapp_numbers"), font=("Segoe UI", 14, "bold"), text_color=COLORS["primary"])
    lbl_mid.pack(side="right", padx=5)

    # Table Toolbar for imports & number edit
    tbl_toolbar = ctk.CTkFrame(col_mid, fg_color="transparent", height=32)
    tbl_toolbar.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 5))

    # Import shortcut button
    self.btn_check = ctk.CTkButton(
        tbl_toolbar, text=self.tr("btn_check_numbers"), font=("Segoe UI", 11, "bold"),
        width=95, height=28, corner_radius=6,
        fg_color=COLORS["info"], hover_color=COLORS["accent_hover"],
        text_color="#000000",
        command=self._check_numbers_action,
    )
    self.btn_check.pack(side="right", padx=3)

    self.btn_import_shortcut = ctk.CTkButton(
        tbl_toolbar, text=self.tr("btn_import_numbers"), font=("Segoe UI", 11, "bold"),
        width=100, height=28, corner_radius=6,
        fg_color=COLORS["secondary"], hover_color=COLORS["secondary_hover"],
        text_color=COLORS["secondary_text"],
        command=self._open_import_dialog
    )
    self.btn_import_shortcut.pack(side="right", padx=3)

    # Number Generator shortcut
    self.btn_gen_shortcut = ctk.CTkButton(
        tbl_toolbar, text=self.tr("btn_num_generator"), font=("Segoe UI", 11),
        width=90, height=28, corner_radius=6,
        fg_color=COLORS["secondary"], hover_color=COLORS["secondary_hover"],
        text_color=COLORS["secondary_text"],
        command=self._open_number_generator
    )
    self.btn_gen_shortcut.pack(side="right", padx=3)

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
        text_color="#FFFFFF",
        command=self._add_manual_number_dialog
    )
    self.btn_tbl_add.pack(side="left", padx=2)

    # Secret hidden contacts entry for full backwards compatibility
    self.contacts_entry = ctk.CTkEntry(col_mid, width=1)
    self.contacts_entry.grid(row=0, column=0, sticky="w", padx=5)
    self.contacts_entry.grid_remove()

    # ── Group Selection Row (Saved Groups) ──
    source_frame = ctk.CTkFrame(col_mid, fg_color="transparent", height=35)
    source_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=(2, 5))
    
    # Segmented Button to choose between File/Manual and Saved Group
    self.source_mode_var = ctk.StringVar(value=self.tr("source_file_manual"))
    self.source_mode_seg = ctk.CTkSegmentedButton(
        source_frame,
        values=[self.tr("source_file_manual"), self.tr("source_saved_group")],
        variable=self.source_mode_var,
        command=self._on_source_mode_change,
        selected_color=COLORS["primary"],
        selected_hover_color=COLORS["primary_hover"],
        unselected_color=COLORS["secondary"],
        text_color=COLORS["text_main"],
        height=28
    )
    self.source_mode_seg.pack(side="left", padx=5)
    
    self.lbl_select_group = ctk.CTkLabel(source_frame, text=self.tr("lbl_saved_groups"), font=("Segoe UI", 11, "bold"))
    
    self.main_group_select = ctk.CTkComboBox(
        source_frame, width=160, height=28,
        command=self._on_main_group_select,
        fg_color=COLORS["card_bg"],
        border_color=COLORS["border"],
        button_color=COLORS["primary"],
        button_hover_color=COLORS["primary_hover"],
        text_color=COLORS["text_main"],
        dropdown_fg_color=COLORS["card_bg"],
        dropdown_text_color=COLORS["text_main"]
    )
    
    self.btn_refresh_combo = ctk.CTkButton(
        source_frame, text="🔄", font=("Segoe UI", 11),
        width=28, height=28, corner_radius=6,
        fg_color=COLORS["secondary"], hover_color=COLORS["secondary_hover"],
        text_color=COLORS["secondary_text"],
        command=self._refresh_main_group_combobox
    )

    # Numbers Treeview Table (styled with white background and black text)
    table_frame = ctk.CTkFrame(col_mid, fg_color="transparent")
    table_frame.grid(row=3, column=0, sticky="nsew", padx=10, pady=5)
    
    columns = ("name", "phone", "var1", "status")
    self.progress_tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=15)
    self.progress_tree.heading("name", text=self.tr("col_name"))
    self.progress_tree.heading("phone", text=self.tr("col_number"))
    self.progress_tree.heading("var1", text=self.tr("dialog_var1").replace(" field", "").replace(" حقل", ""))
    self.progress_tree.heading("status", text=self.tr("col_status"))
    
    self.progress_tree.column("name", width=110, anchor="e")
    self.progress_tree.column("phone", width=110, anchor="center")
    self.progress_tree.column("var1", width=80, anchor="e")
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
    self.total_counts_label.grid(row=4, column=0, sticky="ew", padx=15, pady=(2, 2))

    # Progress bar
    self.progress_bar = ctk.CTkProgressBar(col_mid, height=8, corner_radius=4, progress_color=COLORS["primary"])
    self.progress_bar.grid(row=5, column=0, sticky="ew", padx=15, pady=(2, 2))
    self.progress_bar.set(0)

    # Progress status and counter
    prog_detail_frame = ctk.CTkFrame(col_mid, fg_color="transparent")
    prog_detail_frame.grid(row=6, column=0, sticky="ew", padx=15, pady=(2, 8))
    
    self.status_label = ctk.CTkLabel(
        prog_detail_frame, text=self.tr("msg_ready_status"),
        font=("Segoe UI", 11), text_color=COLORS["text_muted"]
    )
    self.status_label.pack(side="right")
    
    self.counter_label = ctk.CTkLabel(
        prog_detail_frame, text="✅ 0 | ❌ 0 | 🚫 0",
        font=("Segoe UI", 11, "bold"), text_color=COLORS["primary"]
    )
    self.counter_label.pack(side="left")

    # =======================================================================
    # COLUMN 2: Right Column (Message editor & attachments & Send Buttons)
    # =======================================================================
    col_right = ctk.CTkFrame(frame, corner_radius=8, border_width=1, border_color=COLORS["border"])
    col_right.grid(row=0, column=2, sticky="nsew", padx=3, pady=5)
    col_right.grid_rowconfigure(0, weight=3)  # Message Editor
    col_right.grid_rowconfigure(1, weight=2)  # Attachments
    col_right.grid_rowconfigure(2, weight=0)  # Buttons Action
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
    
    # Message box editor inside tab1 (white background, black text style applied via applied palette)
    self.message_editor = RichTextFrame(tab1, colors=COLORS, fg_color="#FFFFFF", corner_radius=8)
    self.message_editor.pack(fill="both", expand=True)
    self.message_textbox = self.message_editor.text_box
    self.msg_text = self.message_textbox

    # Spintax and text option checkboxes below editor
    chk_frame = ctk.CTkFrame(pane_msg, fg_color="transparent", height=30)
    chk_frame.grid(row=2, column=0, sticky="ew", pady=(2, 2))

    self.send_text_var = ctk.BooleanVar(value=False)
    ctk.CTkCheckBox(
        chk_frame,
        text=self.tr("chk_send_text_caption"),
        variable=self.send_text_var,
        font=("Segoe UI", 11),
    ).pack(side="right", padx=5)

    self.spin_text_var = ctk.BooleanVar(value=self.config.get("enable_spintax", True))
    ctk.CTkCheckBox(chk_frame, text=self.tr("chk_spintax"),
                    variable=self.spin_text_var,
                    font=("Segoe UI", 11)).pack(side="right", padx=5)

    self.preview_spintax_btn = ctk.CTkButton(
        chk_frame, text=self.tr("btn_preview"),
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
    self.attachment_manager = AttachmentManager(pane_atts, colors=COLORS, fg_color=COLORS["card_bg"], corner_radius=8, tr=self.tr)
    self.attachment_manager.grid(row=1, column=0, sticky="nsew", pady=2)

    # --- Bottom Actions: Large Sending Buttons (Brings Visual WOW) ---
    btn_row_send = ctk.CTkFrame(col_right, fg_color="transparent")
    btn_row_send.grid(row=2, column=0, sticky="ew", padx=10, pady=(10, 15))
    
    # Redefine sending control buttons inside this tab space for stunning layout
    self.btn_start = ctk.CTkButton(
        btn_row_send, text="🚀 " + self.tr("btn_send_now"),
        font=("Segoe UI", 13, "bold"),
        height=38, corner_radius=8,
        fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"],
        text_color="#FFFFFF",
        command=self._start_action
    )
    self.btn_start.pack(side="right", fill="x", expand=True, padx=4)

    self.btn_schedule = ctk.CTkButton(
        btn_row_send, text="📅 " + self.tr("btn_schedule_campaign"),
        font=("Segoe UI", 12, "bold"),
        height=38, corner_radius=8,
        fg_color=COLORS["secondary"], hover_color=COLORS["secondary_hover"],
        text_color=COLORS["secondary_text"],
        command=self._schedule_action
    )
    self.btn_schedule.pack(side="right", fill="x", expand=True, padx=4)

    self.btn_stop = ctk.CTkButton(
        btn_row_send, text="🛑 " + self.tr("btn_pause_send"),
        font=("Segoe UI", 12, "bold"),
        height=38, corner_radius=8,
        fg_color=COLORS["danger"], hover_color=COLORS["danger_hover"],
        text_color="#FFFFFF",
        state="disabled",
        command=self._stop_action
    )
    self.btn_stop.pack(side="left", fill="x", expand=True, padx=4)
