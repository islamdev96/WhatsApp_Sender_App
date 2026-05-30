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
    """Build the main sending tab with 2 columns: Left (Whatsapp Numbers List), Right (Message & Attachments)."""
    self.tab_frames["main"] = frame

    # Two-column layout
    frame.grid_columnconfigure(0, weight=4, minsize=400)  # Left Column: Whatsapp Numbers List
    frame.grid_columnconfigure(1, weight=5, minsize=500)  # Right Column: Message & Attachments
    frame.grid_rowconfigure(0, weight=1)

    # ── Left Column: WhatsApp Numbers List ──
    col_mid = ctk.CTkFrame(frame, fg_color=COLORS["card_bg"], corner_radius=12)
    col_mid.grid(row=0, column=0, sticky="nsew", padx=(10, 5), pady=10)
    col_mid.grid_rowconfigure(2, weight=1)
    col_mid.grid_columnconfigure(0, weight=1)

    hdr_mid = ctk.CTkFrame(col_mid, fg_color="transparent", height=36)
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
    col_right.grid(row=0, column=1, sticky="nsew", padx=3, pady=5)
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
