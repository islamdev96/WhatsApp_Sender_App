"""WhatsApp Sender Pro — Tab builder methods (main, groups, templates, settings, log)."""
import customtkinter as ctk
from tkinter import filedialog, messagebox, ttk

from gui.theme import COLORS
from utils.logger import logger
from utils.helpers import read_contacts_auto
from gui.components import RichTextFrame, AttachmentManager


class TabBuildersMixin:
    """Mixin: Tab builder methods (main, groups, templates, settings, log)."""

    def _build_tab_main(self):
        """Build the main sending tab: contacts table, message editor, attachments."""
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
            tbl_toolbar, text=self.tr("btn_check_numbers"), font=("Segoe UI", 11, "bold"),
            width=100, height=28, corner_radius=6,
            fg_color=COLORS["info"], hover_color=COLORS["accent_hover"],
            text_color="#000000",
            command=self._check_numbers_action,
        )
        self.btn_check.pack(side="right", padx=5)

        self.btn_import_shortcut = ctk.CTkButton(
            tbl_toolbar, text=self.tr("btn_import_numbers"), font=("Segoe UI", 11, "bold"),
            width=110, height=28, corner_radius=6,
            fg_color=COLORS["secondary"], hover_color=COLORS["secondary_hover"],
            text_color=COLORS["secondary_text"],
            command=self._open_import_dialog
        )
        self.btn_import_shortcut.pack(side="right", padx=5)

        # Number Generator shortcut
        self.btn_gen_shortcut = ctk.CTkButton(
            tbl_toolbar, text=self.tr("btn_num_generator"), font=("Segoe UI", 11),
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
        # Initially hidden, will be shown if "مجموعة محفوظة" is selected
        
        self.main_group_select = ctk.CTkComboBox(
            source_frame, width=180, height=28,
            command=self._on_main_group_select,
            fg_color=COLORS["card_bg"],
            border_color=COLORS["border"],
            button_color=COLORS["primary"],
            button_hover_color=COLORS["primary_hover"],
            text_color=COLORS["text_main"],
            dropdown_fg_color=COLORS["card_bg"],
            dropdown_text_color=COLORS["text_main"]
        )
        # Initially hidden
        
        self.btn_refresh_combo = ctk.CTkButton(
            source_frame, text="🔄", font=("Segoe UI", 11),
            width=28, height=28, corner_radius=6,
            fg_color=COLORS["secondary"], hover_color=COLORS["secondary_hover"],
            text_color=COLORS["secondary_text"],
            command=self._refresh_main_group_combobox
        )
        # Initially hidden

        # Numbers Treeview Table
        table_frame = ctk.CTkFrame(col_mid, fg_color="transparent")
        table_frame.grid(row=3, column=0, sticky="nsew", padx=10, pady=5)
        
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


    # ─── Groups Tab ───────────────────────────────────────────────────────

    def _build_tab_groups(self):
        """Build the contact groups management tab."""
        frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.tab_frames["groups"] = frame

        is_ar = self.current_lang.get() == "ar"
        anchor_val = "e" if is_ar else "w"
        header = ctk.CTkLabel(frame, text=self.tr("groups_header"),
                              font=ctk.CTkFont(size=20, weight="bold"))
        header.pack(anchor=anchor_val, padx=25, pady=(20, 5))

        desc = ctk.CTkLabel(frame, text=self.tr("groups_desc"),
                            font=ctk.CTkFont(size=12), text_color=COLORS["text_muted"])
        desc.pack(anchor=anchor_val, padx=25, pady=(0, 12))

        body = ctk.CTkFrame(frame, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=20, pady=5)
        body.grid_columnconfigure(0, weight=2)
        body.grid_columnconfigure(1, weight=3)
        body.grid_rowconfigure(0, weight=1)

        # LEFT: Group list
        list_frame = ctk.CTkFrame(body, corner_radius=12)
        list_frame.grid(row=0, column=1, padx=(0, 8), pady=5, sticky="nsew")

        ctk.CTkLabel(list_frame, text=self.tr("groups_label"),
                     font=ctk.CTkFont(size=13, weight="bold")).pack(anchor=anchor_val, padx=12, pady=(10, 5))

        self.groups_listbox = ctk.CTkScrollableFrame(list_frame, corner_radius=8)
        self.groups_listbox.pack(fill="both", expand=True, padx=10, pady=(0, 5))

        grp_btn_row = ctk.CTkFrame(list_frame, fg_color="transparent")
        grp_btn_row.pack(fill="x", padx=10, pady=(0, 10))
        ctk.CTkButton(grp_btn_row, text=self.tr("groups_btn_delete"), width=75, height=32,
                      fg_color=COLORS["danger"], hover_color=COLORS["danger_hover"],
                      command=self._delete_group).pack(side="left", padx=3)
        ctk.CTkButton(grp_btn_row, text=self.tr("groups_btn_send"), width=120, height=32,
                      fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"],
                      command=self._send_to_group).pack(side="left", padx=3)

        # RIGHT: Group editor
        edit_frame = ctk.CTkFrame(body, corner_radius=12)
        edit_frame.grid(row=0, column=0, padx=(8, 0), pady=5, sticky="nsew")

        ctk.CTkLabel(edit_frame, text=self.tr("groups_name_label"),
                     font=ctk.CTkFont(size=13)).pack(anchor=anchor_val, padx=12, pady=(12, 3))
        self.group_name_entry = ctk.CTkEntry(edit_frame, height=36, corner_radius=8,
                                             placeholder_text=self.tr("groups_name_placeholder"))
        self.group_name_entry.pack(fill="x", padx=12, pady=(0, 8))

        # Import file
        import_row = ctk.CTkFrame(edit_frame, fg_color="transparent")
        import_row.pack(fill="x", padx=12, pady=3)
        side_lbl = "right" if is_ar else "left"
        side_opposite = "left" if is_ar else "right"
        self.group_import_entry = ctk.CTkEntry(import_row, height=34, corner_radius=8,
                                               placeholder_text=self.tr("groups_file_placeholder"))
        self.group_import_entry.pack(side=side_lbl, fill="x", expand=True, padx=(8, 0))
        ctk.CTkButton(import_row, text=self.tr("groups_btn_choose"), width=70, height=34,
                      fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"],
                      command=self._browse_group_file).pack(side=side_opposite)

        btn_row2 = ctk.CTkFrame(edit_frame, fg_color="transparent")
        btn_row2.pack(fill="x", padx=12, pady=5)
        ctk.CTkButton(btn_row2, text=self.tr("groups_btn_create_import"), height=38,
                      fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"],
                      font=ctk.CTkFont(size=13, weight="bold"),
                      command=self._create_group_and_import).pack(fill="x", pady=2)
        ctk.CTkButton(btn_row2, text=self.tr("groups_btn_add_contacts"), height=34,
                      fg_color=COLORS["info"],
                      font=ctk.CTkFont(size=12),
                      command=self._add_contacts_to_group).pack(fill="x", pady=2)

        # Contacts preview
        ctk.CTkLabel(edit_frame, text=self.tr("groups_contacts_label"),
                     font=ctk.CTkFont(size=13)).pack(anchor=anchor_val, padx=12, pady=(10, 3))
                     
        # Search & Single Contact Actions toolbar above Treeview
        contact_tools = ctk.CTkFrame(edit_frame, fg_color="transparent", height=32)
        contact_tools.pack(fill="x", padx=12, pady=(0, 5))
        
        self.group_contact_search = ctk.CTkEntry(
            contact_tools, placeholder_text=self.tr("groups_search_placeholder"), height=28, font=("Segoe UI", 11)
        )
        self.group_contact_search.pack(side=side_lbl, fill="x", expand=True, padx=(0, 5))
        self.group_contact_search.bind("<KeyRelease>", self._filter_group_contacts)
        
        self.btn_add_single_contact = ctk.CTkButton(
            contact_tools, text=self.tr("groups_btn_add_contact"), font=("Segoe UI", 11, "bold"),
            fg_color=COLORS["success"], hover_color=COLORS["primary_hover"],
            text_color="#000000", width=95, height=28, corner_radius=6,
            command=self._on_add_single_contact_click
        )
        self.btn_add_single_contact.pack(side=side_opposite, padx=2)
        
        self.btn_del_single_contact = ctk.CTkButton(
            contact_tools, text=self.tr("groups_btn_del_contact"), font=("Segoe UI", 11, "bold"),
            fg_color=COLORS["danger"], hover_color=COLORS["danger_hover"],
            text_color="#FFFFFF", width=95, height=28, corner_radius=6,
            command=self._on_delete_single_contact_click
        )
        self.btn_del_single_contact.pack(side=side_opposite, padx=2)

        tree_frame = ctk.CTkFrame(edit_frame, fg_color="transparent")
        tree_frame.pack(fill="both", expand=True, padx=12, pady=(0, 5))
        
        columns = ("name", "phone")
        self.group_contacts_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=8)
        self.group_contacts_tree.heading("name", text=self.tr("groups_col_name"))
        self.group_contacts_tree.heading("phone", text=self.tr("groups_col_phone"))
        self.group_contacts_tree.column("name", width=150, anchor="e")
        self.group_contacts_tree.column("phone", width=150, anchor="center")
        
        tree_scroll = ctk.CTkScrollbar(tree_frame, command=self.group_contacts_tree.yview)
        self.group_contacts_tree.configure(yscrollcommand=tree_scroll.set)
        tree_scroll.pack(side="right", fill="y")
        self.group_contacts_tree.pack(side="left", fill="both", expand=True)

        self.group_info_label = ctk.CTkLabel(edit_frame, text="",
                                             font=ctk.CTkFont(size=11),
                                             text_color=COLORS["text_muted"])
        self.group_info_label.pack(anchor="e", padx=12, pady=(0, 10))

        self._refresh_groups_list()

    # ─── GMaps Scraper Tab ────────────────────────────────────────────────

    # ─── Warmer Tab ───────────────────────────────────────────────────────

    # ─── Templates Tab ────────────────────────────────────────────────────

    def _build_tab_templates(self):
        """Build the message templates management tab."""
        frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.tab_frames["templates"] = frame

        is_ar = self.current_lang.get() == "ar"
        anchor_val = "e" if is_ar else "w"
        header = ctk.CTkLabel(frame, text=self.tr("templates_header"),
                              font=ctk.CTkFont(size=20, weight="bold"))
        header.pack(anchor=anchor_val, padx=25, pady=(20, 10))

        desc = ctk.CTkLabel(frame, text=self.tr("templates_desc"),
                            font=ctk.CTkFont(size=12), text_color=COLORS["text_muted"])
        desc.pack(anchor=anchor_val, padx=25, pady=(0, 15))

        body = ctk.CTkFrame(frame, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=20, pady=5)
        body.grid_columnconfigure(0, weight=2)
        body.grid_columnconfigure(1, weight=3)
        body.grid_rowconfigure(0, weight=1)

        # LEFT: Template list
        list_frame = ctk.CTkFrame(body, corner_radius=12)
        list_frame.grid(row=0, column=1, padx=(0, 8), pady=5, sticky="nsew")

        ctk.CTkLabel(list_frame, text=self.tr("templates_saved"),
                     font=ctk.CTkFont(size=13, weight="bold")).pack(anchor=anchor_val, padx=12, pady=(10, 5))

        self.templates_listbox = ctk.CTkScrollableFrame(list_frame, corner_radius=8)
        self.templates_listbox.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        btn_row = ctk.CTkFrame(list_frame, fg_color="transparent")
        btn_row.pack(fill="x", padx=10, pady=(0, 10))
        ctk.CTkButton(btn_row, text=self.tr("templates_btn_delete"), width=80, height=32,
                      fg_color=COLORS["danger"], hover_color=COLORS["danger_hover"],
                      command=self._delete_template).pack(side="left", padx=3)
        ctk.CTkButton(btn_row, text=self.tr("templates_btn_load"), width=80, height=32,
                      fg_color=COLORS["info"],
                      command=self._load_template).pack(side="left", padx=3)

        # RIGHT: Editor
        edit_frame = ctk.CTkFrame(body, corner_radius=12)
        edit_frame.grid(row=0, column=0, padx=(8, 0), pady=5, sticky="nsew")

        ctk.CTkLabel(edit_frame, text=self.tr("templates_name_label"),
                     font=ctk.CTkFont(size=13)).pack(anchor=anchor_val, padx=12, pady=(12, 3))
        self.template_name_entry = ctk.CTkEntry(edit_frame, height=36, corner_radius=8,
                                                placeholder_text=self.tr("templates_name_placeholder"))
        self.template_name_entry.pack(fill="x", padx=12, pady=(0, 8))

        ctk.CTkLabel(edit_frame, text=self.tr("templates_body_label"),
                     font=ctk.CTkFont(size=13)).pack(anchor=anchor_val, padx=12, pady=(5, 3))
        self.template_body_textbox = ctk.CTkTextbox(edit_frame, height=200, corner_radius=8,
                                                    font=ctk.CTkFont(size=13))
        self.template_body_textbox.pack(fill="both", expand=True, padx=12, pady=(0, 8))

        ctk.CTkButton(edit_frame, text=self.tr("templates_btn_save"), height=40,
                      fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"],
                      font=ctk.CTkFont(size=13, weight="bold"),
                      command=self._save_template).pack(fill="x", padx=12, pady=(5, 12))

        self._refresh_templates_list()

    # ─── Settings Tab ─────────────────────────────────────────────────────

    def _build_tab_settings(self):
        """Build the settings tab with proxy, safety, and display options."""
        frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.tab_frames["settings"] = frame

        is_ar = self.current_lang.get() == "ar"
        anchor_val = "e" if is_ar else "w"
        side_lbl = "right" if is_ar else "left"
        side_opposite = "left" if is_ar else "right"

        header = ctk.CTkLabel(frame, text=self.tr("settings_header"),
                              font=ctk.CTkFont(size=20, weight="bold"))
        header.pack(anchor=anchor_val, padx=25, pady=(20, 15))

        scroll = ctk.CTkScrollableFrame(frame, corner_radius=12)
        scroll.pack(fill="both", expand=True, padx=20, pady=(0, 15))

        # Delay Settings
        delay_card = ctk.CTkFrame(scroll, corner_radius=10)
        delay_card.pack(fill="x", padx=10, pady=8)
        ctk.CTkLabel(delay_card, text=self.tr("settings_delay_title"),
                     font=ctk.CTkFont(size=14, weight="bold")).pack(anchor=anchor_val, padx=15, pady=(10, 5))

        delay_row = ctk.CTkFrame(delay_card, fg_color="transparent")
        delay_row.pack(fill="x", padx=15, pady=(0, 12))

        ctk.CTkLabel(delay_row, text=self.tr("settings_from"), font=ctk.CTkFont(size=12)).pack(side=side_lbl, padx=(5, 0))
        self.delay_min_entry = ctk.CTkEntry(delay_row, width=70, height=34, corner_radius=8,
                                            justify="center")
        self.delay_min_entry.pack(side=side_lbl, padx=5)
        self.delay_min_entry.insert(0, str(self.config.get("delay_min", 8)))

        ctk.CTkLabel(delay_row, text=self.tr("settings_to"), font=ctk.CTkFont(size=12)).pack(side=side_lbl, padx=(5, 0))
        self.delay_max_entry = ctk.CTkEntry(delay_row, width=70, height=34, corner_radius=8,
                                            justify="center")
        self.delay_max_entry.pack(side=side_lbl, padx=5)
        self.delay_max_entry.insert(0, str(self.config.get("delay_max", 25)))

        # Batch Settings
        batch_card = ctk.CTkFrame(scroll, corner_radius=10)
        batch_card.pack(fill="x", padx=10, pady=8)
        ctk.CTkLabel(batch_card, text=self.tr("settings_batch_title"),
                     font=ctk.CTkFont(size=14, weight="bold")).pack(anchor=anchor_val, padx=15, pady=(10, 5))

        batch_row1 = ctk.CTkFrame(batch_card, fg_color="transparent")
        batch_row1.pack(fill="x", padx=15, pady=(0, 5))
        ctk.CTkLabel(batch_row1, text=self.tr("settings_after_every"), font=ctk.CTkFont(size=12)).pack(side=side_lbl, padx=(5, 0))
        self.batch_size_entry = ctk.CTkEntry(batch_row1, width=70, height=34, corner_radius=8,
                                             justify="center")
        self.batch_size_entry.pack(side=side_lbl, padx=5)
        self.batch_size_entry.insert(0, str(self.config.get("batch_size", 30)))

        batch_row2 = ctk.CTkFrame(batch_card, fg_color="transparent")
        batch_row2.pack(fill="x", padx=15, pady=(0, 12))
        ctk.CTkLabel(batch_row2, text=self.tr("settings_pause_from"), font=ctk.CTkFont(size=12)).pack(side=side_lbl, padx=(5, 0))
        self.batch_min_entry = ctk.CTkEntry(batch_row2, width=70, height=34, corner_radius=8,
                                            justify="center")
        self.batch_min_entry.pack(side=side_lbl, padx=5)
        self.batch_min_entry.insert(0, str(self.config.get("batch_pause_min", 180)))

        ctk.CTkLabel(batch_row2, text=self.tr("settings_to"), font=ctk.CTkFont(size=12)).pack(side=side_lbl, padx=(5, 0))
        self.batch_max_entry = ctk.CTkEntry(batch_row2, width=70, height=34, corner_radius=8,
                                            justify="center")
        self.batch_max_entry.pack(side=side_lbl, padx=5)
        self.batch_max_entry.insert(0, str(self.config.get("batch_pause_max", 240)))

        # Reliability Settings
        reliability_card = ctk.CTkFrame(scroll, corner_radius=10)
        reliability_card.pack(fill="x", padx=10, pady=8)
        ctk.CTkLabel(reliability_card, text=self.tr("settings_reliability_title"),
                     font=ctk.CTkFont(size=14, weight="bold")).pack(anchor=anchor_val, padx=15, pady=(10, 5))

        r1 = ctk.CTkFrame(reliability_card, fg_color="transparent")
        r1.pack(fill="x", padx=15, pady=(0, 5))
        ctk.CTkLabel(r1, text=self.tr("settings_retry_count"), font=ctk.CTkFont(size=12)).pack(side=side_lbl, padx=(5, 0))
        self.retry_count_entry = ctk.CTkEntry(r1, width=70, height=34, corner_radius=8, justify="center")
        self.retry_count_entry.pack(side=side_lbl, padx=5)
        self.retry_count_entry.insert(0, str(self.config.get("max_retries", 2)))

        r2 = ctk.CTkFrame(reliability_card, fg_color="transparent")
        r2.pack(fill="x", padx=15, pady=(0, 5))
        ctk.CTkLabel(r2, text=self.tr("settings_retry_delay_from"), font=ctk.CTkFont(size=12)).pack(side=side_lbl, padx=(5, 0))
        self.retry_min_entry = ctk.CTkEntry(r2, width=70, height=34, corner_radius=8, justify="center")
        self.retry_min_entry.pack(side=side_lbl, padx=5)
        self.retry_min_entry.insert(0, str(self.config.get("retry_delay_min", 3)))

        ctk.CTkLabel(r2, text=self.tr("settings_to"), font=ctk.CTkFont(size=12)).pack(side=side_lbl, padx=(5, 0))
        self.retry_max_entry = ctk.CTkEntry(r2, width=70, height=34, corner_radius=8, justify="center")
        self.retry_max_entry.pack(side=side_lbl, padx=5)
        self.retry_max_entry.insert(0, str(self.config.get("retry_delay_max", 6)))

        r3 = ctk.CTkFrame(reliability_card, fg_color="transparent")
        r3.pack(fill="x", padx=15, pady=(0, 12))
        ctk.CTkLabel(r3, text=self.tr("settings_max_fail"), font=ctk.CTkFont(size=12)).pack(side=side_lbl, padx=(5, 0))
        self.max_fail_entry = ctk.CTkEntry(r3, width=70, height=34, corner_radius=8, justify="center")
        self.max_fail_entry.pack(side=side_lbl, padx=5)
        self.max_fail_entry.insert(0, str(self.config.get("max_consecutive_failures", 5)))

        # Rotation Settings (Multi-Account Rotation)
        rotation_card = ctk.CTkFrame(scroll, corner_radius=10)
        rotation_card.pack(fill="x", padx=10, pady=8)
        ctk.CTkLabel(rotation_card, text=self.tr("settings_rotation_title"),
                     font=ctk.CTkFont(size=14, weight="bold")).pack(anchor=anchor_val, padx=15, pady=(10, 5))

        rot_row1 = ctk.CTkFrame(rotation_card, fg_color="transparent")
        rot_row1.pack(fill="x", padx=15, pady=(0, 5))
        self.rotation_enabled_var = ctk.BooleanVar(value=self.config.get("rotation_enabled", False))
        ctk.CTkCheckBox(rot_row1, text=self.tr("settings_rotation_enabled"), 
                        variable=self.rotation_enabled_var, font=ctk.CTkFont(size=12)).pack(side=side_lbl, padx=5)

        rot_row2 = ctk.CTkFrame(rotation_card, fg_color="transparent")
        rot_row2.pack(fill="x", padx=15, pady=(0, 12))
        ctk.CTkLabel(rot_row2, text=self.tr("settings_rotation_interval"), font=ctk.CTkFont(size=12)).pack(side=side_lbl, padx=(5, 0))
        self.rotation_interval_entry = ctk.CTkEntry(rot_row2, width=70, height=34, corner_radius=8, justify="center")
        self.rotation_interval_entry.pack(side=side_lbl, padx=5)
        self.rotation_interval_entry.insert(0, str(self.config.get("rotation_interval", 50)))

        # General Settings (New)
        general_card = ctk.CTkFrame(scroll, corner_radius=10)
        general_card.pack(fill="x", padx=10, pady=8)
        ctk.CTkLabel(general_card, text=self.tr("settings_general_title"),
                     font=ctk.CTkFont(size=14, weight="bold")).pack(anchor=anchor_val, padx=15, pady=(10, 5))

        g1 = ctk.CTkFrame(general_card, fg_color="transparent")
        g1.pack(fill="x", padx=15, pady=(0, 12))
        ctk.CTkLabel(g1, text=self.tr("settings_default_country_code"), font=ctk.CTkFont(size=12)).pack(side=side_lbl, padx=(5, 0))
        self.country_code_entry = ctk.CTkEntry(g1, width=70, height=34, corner_radius=8, justify="center")
        self.country_code_entry.pack(side=side_lbl, padx=5)
        self.country_code_entry.insert(0, str(self.config.get("default_country_code", "20")))

        # Proxy & VPN Settings Card
        # Proxy & VPN Settings Card
        proxy_card = ctk.CTkFrame(scroll, corner_radius=10)
        proxy_card.pack(fill="x", padx=10, pady=8)
        ctk.CTkLabel(proxy_card, text=self.tr("settings_proxy_title"),
                     font=ctk.CTkFont(size=14, weight="bold")).pack(anchor=anchor_val, padx=15, pady=(10, 5))

        # Checkbox and Type row
        chk_row = ctk.CTkFrame(proxy_card, fg_color="transparent")
        chk_row.pack(fill="x", padx=15, pady=(0, 5))
        
        self.proxy_enabled_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(chk_row, text=self.tr("settings_proxy_enabled"), variable=self.proxy_enabled_var,
                        font=ctk.CTkFont(size=12)).pack(side=side_lbl, padx=5)
                        
        self.proxy_type_var = ctk.StringVar(value="HTTP")
        ctk.CTkLabel(chk_row, text=self.tr("settings_proxy_type"), font=ctk.CTkFont(size=12)).pack(side=side_opposite, padx=(5, 0))
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
        self.proxy_type_menu.pack(side=side_opposite, padx=5)

        # Host and Port row
        addr_row = ctk.CTkFrame(proxy_card, fg_color="transparent")
        addr_row.pack(fill="x", padx=15, pady=5)
        
        ctk.CTkLabel(addr_row, text=self.tr("settings_proxy_host"), font=ctk.CTkFont(size=12)).pack(side=side_lbl, padx=(5, 0))
        self.proxy_host_entry = ctk.CTkEntry(addr_row, width=200, height=34, corner_radius=8,
                                             placeholder_text="e.g. 192.168.1.1 or proxy.com")
        self.proxy_host_entry.pack(side=side_lbl, padx=5)
        
        ctk.CTkLabel(addr_row, text=self.tr("settings_proxy_port"), font=ctk.CTkFont(size=12)).pack(side=side_lbl, padx=(5, 0))
        self.proxy_port_entry = ctk.CTkEntry(addr_row, width=80, height=34, corner_radius=8,
                                            justify="center", placeholder_text="8080")
        self.proxy_port_entry.pack(side=side_lbl, padx=5)

        # Auth credentials row
        auth_row = ctk.CTkFrame(proxy_card, fg_color="transparent")
        auth_row.pack(fill="x", padx=15, pady=5)
        
        ctk.CTkLabel(auth_row, text=self.tr("settings_proxy_username"), font=ctk.CTkFont(size=12)).pack(side=side_lbl, padx=(5, 0))
        self.proxy_username_entry = ctk.CTkEntry(auth_row, width=120, height=34, corner_radius=8,
                                                 placeholder_text="Username")
        self.proxy_username_entry.pack(side=side_lbl, padx=5)
        
        ctk.CTkLabel(auth_row, text=self.tr("settings_proxy_password"), font=ctk.CTkFont(size=12)).pack(side=side_lbl, padx=(5, 0))
        self.proxy_password_entry = ctk.CTkEntry(auth_row, width=120, height=34, corner_radius=8,
                                                 show="*", placeholder_text="Password")
        self.proxy_password_entry.pack(side=side_lbl, padx=5)

        # Action/Test connection row
        action_row = ctk.CTkFrame(proxy_card, fg_color="transparent")
        action_row.pack(fill="x", padx=15, pady=(5, 10))
        
        self.test_proxy_btn = ctk.CTkButton(
            action_row,
            text=self.tr("settings_test_proxy"),
            width=120,
            height=32,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._test_proxy_connection
        )
        self.test_proxy_btn.pack(side=side_lbl, padx=5)
        
        self.proxy_status_label = ctk.CTkLabel(
            action_row,
            text=self.tr("settings_proxy_status"),
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_muted"]
        )
        self.proxy_status_label.pack(side=side_opposite, padx=5)

        # Fingerprint section separator
        sep = ctk.CTkFrame(proxy_card, height=2, fg_color=COLORS["border"])
        sep.pack(fill="x", padx=15, pady=8)
        
        ctk.CTkLabel(proxy_card, text=self.tr("settings_fingerprint_title"),
                     font=ctk.CTkFont(size=13, weight="bold")).pack(anchor=anchor_val, padx=15, pady=(2, 5))

        # Fingerprint toggle row
        fp_toggle_row = ctk.CTkFrame(proxy_card, fg_color="transparent")
        fp_toggle_row.pack(fill="x", padx=15, pady=2)
        
        self.fp_enabled_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(fp_toggle_row, text=self.tr("settings_fingerprint_enabled"), 
                        variable=self.fp_enabled_var, font=ctk.CTkFont(size=12)).pack(side=side_lbl, padx=5)

        # Fingerprint values display row
        fp_row = ctk.CTkFrame(proxy_card, fg_color="transparent")
        fp_row.pack(fill="x", padx=15, pady=5)
        
        # User-Agent read-only entry
        ctk.CTkLabel(fp_row, text=self.tr("settings_fingerprint_ua"), font=ctk.CTkFont(size=11)).pack(side=side_lbl, padx=(5, 0))
        self.fp_ua_entry = ctk.CTkEntry(fp_row, width=280, height=28, corner_radius=6, font=ctk.CTkFont(size=10))
        self.fp_ua_entry.pack(side=side_lbl, padx=5)
        
        # Resolution entry
        ctk.CTkLabel(fp_row, text=self.tr("settings_fingerprint_res"), font=ctk.CTkFont(size=11)).pack(side=side_lbl, padx=(5, 0))
        self.fp_res_entry = ctk.CTkEntry(fp_row, width=80, height=28, corner_radius=6, justify="center", font=ctk.CTkFont(size=11))
        self.fp_res_entry.pack(side=side_lbl, padx=5)
        
        # Generate new fingerprint button
        self.fp_gen_btn = ctk.CTkButton(
            fp_row,
            text=self.tr("settings_fingerprint_gen"),
            width=90,
            height=28,
            fg_color=COLORS["secondary"],
            hover_color=COLORS["secondary_hover"],
            text_color=COLORS["secondary_text"],
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self._generate_new_profile_fingerprint
        )
        self.fp_gen_btn.pack(side=side_opposite, padx=5)

        # Save Button
        ctk.CTkButton(scroll, text=self.tr("settings_save"), height=42,
                      font=ctk.CTkFont(size=14, weight="bold"),
                      fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"],
                      command=self._save_settings).pack(fill="x", padx=10, pady=15)

        # Scheduled Campaigns Queue Card
        self._build_schedule_queue_card(scroll)

    # ─── Log Tab ──────────────────────────────────────────────────────────

    def _build_tab_log(self):
        """Build the event log/diagnostic tab."""
        frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.tab_frames["log"] = frame

        is_ar = self.current_lang.get() == "ar"
        side_lbl = "right" if is_ar else "left"
        side_opposite = "left" if is_ar else "right"
        justify_val = "right" if is_ar else "left"

        header_row = ctk.CTkFrame(frame, fg_color="transparent")
        header_row.pack(fill="x", padx=20, pady=(15, 5))

        ctk.CTkLabel(
            header_row,
            text="📋 " + self.tr("log_header"),
            font=ctk.CTkFont(size=20, weight="bold"),
        ).pack(side=side_lbl)

        ctk.CTkButton(
            header_row,
            text=self.tr("log_btn_open_file"),
            width=110,
            height=32,
            fg_color=COLORS["secondary"],
            hover_color=COLORS["secondary_hover"],
            command=self._open_log_file,
        ).pack(side=side_opposite, padx=4)

        ctk.CTkButton(
            header_row,
            text=self.tr("log_btn_clear"),
            width=80,
            height=32,
            fg_color=COLORS["danger"],
            hover_color=COLORS["danger_hover"],
            command=self._clear_log,
        ).pack(side=side_opposite, padx=4)

        hint = ctk.CTkLabel(
            frame,
            text=self.tr("log_hint"),
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_muted"],
            wraplength=900,
            justify=justify_val,
        )
        hint.pack(fill="x", padx=20, pady=(0, 6))

        self.log_textbox = ctk.CTkTextbox(
            frame,
            font=ctk.CTkFont(family="Consolas", size=12),
            corner_radius=12,
            state="disabled",
        )
        self.log_textbox.pack(fill="both", expand=True, padx=20, pady=(5, 15))
        self.log(self.tr("log_ready_msg"))

    # ═══════════════════════════════════════════════════════════════════════
    #  UI HELPERS
    # ═══════════════════════════════════════════════════════════════════════

    def _create_file_row(self, parent, label_text, entry_attr, browse_cmd):
        """Create a labeled file path input row with browse button."""
        is_ar = self.current_lang.get() == "ar"
        side_lbl = "right" if is_ar else "left"
        anchor_val = "e" if is_ar else "w"

        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=15, pady=4)
        
        ctk.CTkLabel(row, text=label_text, width=100, anchor=anchor_val, font=("Segoe UI", 12, "bold"),
                     text_color=COLORS["text_muted"]).pack(side=side_lbl, padx=(5, 0))
        
        entry = ctk.CTkEntry(row, placeholder_text=self.tr("btn_select_file").replace("📂 ", ""), height=35, 
                             corner_radius=8, font=("Segoe UI", 12), border_color=COLORS["border"],
                             fg_color=COLORS["bg_dark"], text_color=COLORS["text_main"])
        entry.pack(side=side_lbl, fill="x", expand=True, padx=5)
        setattr(self, entry_attr, entry)
        
        ctk.CTkButton(row, text="📂", width=40, height=35,
                      fg_color=COLORS["secondary"], hover_color=COLORS["secondary_hover"],
                      text_color=COLORS["secondary_text"],
                      font=("Segoe UI", 14),
                      command=browse_cmd).pack(side=side_lbl)

    def _refresh_templates_list(self):
        """Reload the templates list from storage."""
        for w in self.templates_listbox.winfo_children():
            w.destroy()
            
        templates = self.templates.get_all()
        if not templates:
            ctk.CTkLabel(self.templates_listbox, text=self.tr("templates_no_templates"), 
                         font=("Segoe UI", 12), text_color=COLORS["text_muted"]).pack(pady=20)
            return

        is_ar = self.current_lang.get() == "ar"
        side_lbl = "right" if is_ar else "left"
        side_opposite = "left" if is_ar else "right"
        anchor_val = "e" if is_ar else "w"
        justify_val = "right" if is_ar else "left"

        for t in templates:
            card = ctk.CTkFrame(self.templates_listbox, fg_color=COLORS["card_bg"], corner_radius=10)
            card.pack(fill="x", pady=5, padx=5)
            
            # Header
            head = ctk.CTkFrame(card, fg_color="transparent", height=30)
            head.pack(fill="x", padx=10, pady=(8, 0))
            
            ctk.CTkLabel(head, text=t["name"], font=("Segoe UI", 13, "bold"), 
                         text_color=COLORS["primary"]).pack(side=side_lbl)
            
            ctk.CTkLabel(head, text=t["updated"], font=("Segoe UI", 10), 
                         text_color=COLORS["text_muted"]).pack(side=side_opposite)
            
            # Body Preview
            body_prev = t["body"][:60] + "..." if len(t["body"]) > 60 else t["body"]
            ctk.CTkLabel(card, text=body_prev, font=("Segoe UI", 11), 
                         text_color=COLORS["text_muted"], anchor=anchor_val, justify=justify_val).pack(fill="x", padx=10, pady=(5, 10))
            
            # Actions
            actions = ctk.CTkFrame(card, fg_color="transparent", height=30)
            actions.pack(fill="x", padx=10, pady=(0, 10))
            
            ctk.CTkButton(actions, text=self.tr("templates_btn_select"), width=60, height=24, 
                          fg_color=COLORS["primary"], font=("Segoe UI", 11, "bold"), text_color="black",
                          command=lambda n=t["name"]: self._select_template(n)).pack(side=side_opposite, padx=2)
            
            ctk.CTkButton(actions, text=self.tr("templates_btn_del_short"), width=50, height=24, 
                          fg_color=COLORS["danger"], hover_color=COLORS["danger_hover"],
                          text_color="#FFFFFF",
                          font=("Segoe UI", 11),
                          command=lambda n=t["name"]: self._delete_template_by_name(n)).pack(side=side_opposite, padx=2)

    def _select_template(self, name):
        """Select a template by name and load its body into the editor."""
        t = self.templates.get_by_name(name)
        if t:
            self.template_name_entry.delete(0, "end")
            self.template_name_entry.insert(0, t["name"])
            self.template_body_textbox.delete("1.0", "end")
            self.template_body_textbox.insert("1.0", t["body"])

    def _save_template(self):
        """Save the current message as a named template."""
        name = self.template_name_entry.get().strip()
        body = self.template_body_textbox.get("1.0", "end").strip()
        if not name:
            messagebox.showwarning(self.tr("msg_alert"), self.tr("msg_enter_template_name"))
            return
        if not body:
            messagebox.showwarning(self.tr("msg_alert"), self.tr("msg_enter_template_body"))
            return
        self.templates.add(name, body)
        self._refresh_templates_list()
        messagebox.showinfo(self.tr("msg_done"), self.tr("msg_template_saved").format(name=name))

    def _delete_template(self):
        """Delete the currently selected template."""
        name = self.template_name_entry.get().strip()
        if not name:
            return
        if messagebox.askyesno(self.tr("msg_confirm"), self.tr("msg_confirm_delete_template").format(name=name)):
            self.templates.delete(name)
            self.template_name_entry.delete(0, "end")
            self.template_body_textbox.delete("1.0", "end")
            self._refresh_templates_list()

    def _load_template(self):
        """Load the selected template body into the message editor."""
        name = self.template_name_entry.get().strip()
        t = self.templates.get_by_name(name)
        if t:
            self.message_textbox.delete("1.0", "end")
            self.message_textbox.insert("1.0", t["body"])
            self._switch_tab("main")
            messagebox.showinfo(self.tr("msg_done"), self.tr("msg_template_loaded").format(name=name))
        else:
            messagebox.showwarning(self.tr("msg_alert"), self.tr("msg_select_template"))

    # ═══════════════════════════════════════════════════════════════════════
    #  GROUPS MANAGEMENT
    # ═══════════════════════════════════════════════════════════════════════

    def _refresh_groups_list(self):
        """Reload the contact groups list from storage."""
        self._refresh_main_group_combobox()
        for w in self.groups_listbox.winfo_children():
            w.destroy()
        
        groups = self.contacts_mgr.get_all()
        if not groups:
            ctk.CTkLabel(self.groups_listbox, text=self.tr("groups_no_groups"), 
                         font=("Segoe UI", 12), text_color=COLORS["text_muted"]).pack(pady=20)
            return

        is_ar = self.current_lang.get() == "ar"
        anchor_val = "e" if is_ar else "w"

        for g in groups:
            count = len(g.get("contacts", []))
            text = f"👥 {g['name']}  ({count})"
            
            btn = ctk.CTkButton(self.groups_listbox, text=text,
                                font=("Segoe UI", 13),
                                fg_color=COLORS["secondary"],
                                hover_color=COLORS["secondary_hover"],
                                text_color=COLORS["secondary_text"],
                                anchor=anchor_val, height=42, corner_radius=8,
                                command=lambda name=g["name"]: self._select_group(name))
            btn.pack(fill="x", pady=3)

    def _select_group(self, name):
        """Select a group and display its contact count and load into the treeview."""
        self.group_name_entry.delete(0, "end")
        self.group_name_entry.insert(0, name)
        g = self.contacts_mgr.get_by_name(name)
        if g:
            # Store full list for local filtering
            self._current_group_contacts = g.get("contacts", [])
            
            # Clear search bar when selecting a new group
            self.group_contact_search.delete(0, "end")
            
            # Refresh tree view
            self._filter_group_contacts()

    def _browse_group_file(self):
        """Browse for a contacts file to import into a group."""
        path = filedialog.askopenfilename(filetypes=[
            (self.tr("file_filter_contacts"), "*.csv;*.xlsx;*.xls;*.txt"),
            ("CSV", "*.csv"),
            ("Excel", "*.xlsx;*.xls"),
            ("Text", "*.txt"),
        ])
        if path:
            self.group_import_entry.delete(0, "end")
            self.group_import_entry.insert(0, path)

    def _create_group_and_import(self):
        """Create a new group and import contacts from a file."""
        name = self.group_name_entry.get().strip()
        if not name:
            messagebox.showwarning(self.tr("msg_alert"), self.tr("msg_enter_group_name"))
            return
        file_path = self.group_import_entry.get().strip()
        contacts = read_contacts_auto(file_path, default_country_code=self.config.get("default_country_code", "20")) if file_path else []
        if self.contacts_mgr.get_by_name(name):
            messagebox.showwarning(self.tr("msg_alert"), self.tr("msg_group_exists").format(name=name))
            return
        self.contacts_mgr.create_group(name, contacts)
        self._refresh_groups_list()
        self._select_group(name)
        count = len(contacts)
        messagebox.showinfo(self.tr("msg_done"), self.tr("msg_group_created").format(name=name, count=count))

    def _add_contacts_to_group(self):
        """Add contacts from a file to the selected group."""
        name = self.group_name_entry.get().strip()
        if not name or not self.contacts_mgr.get_by_name(name):
            messagebox.showwarning(self.tr("msg_alert"), self.tr("msg_select_existing_group"))
            return
        file_path = self.group_import_entry.get().strip()
        if not file_path:
            messagebox.showwarning(self.tr("msg_alert"), self.tr("msg_select_csv_file"))
            return
        contacts = read_contacts_auto(file_path, default_country_code=self.config.get("default_country_code", "20"))
        if not contacts:
            messagebox.showwarning(self.tr("msg_alert"), self.tr("msg_no_valid_contacts"))
            return
        added = self.contacts_mgr.add_contacts(name, contacts)
        self._refresh_groups_list()
        self._select_group(name)
        messagebox.showinfo(self.tr("msg_done"), self.tr("msg_contacts_added").format(added=added, name=name))

    def _delete_group(self):
        """Delete the currently selected contact group."""
        name = self.group_name_entry.get().strip()
        if not name:
            return
        if messagebox.askyesno(self.tr("msg_confirm"), self.tr("msg_confirm_delete_group").format(name=name)):
            self.contacts_mgr.delete_group(name)
            self.group_name_entry.delete(0, "end")
            for w in self.group_contacts_list.winfo_children():
                w.destroy()
            self.group_info_label.configure(text="")
            self._refresh_groups_list()

    def _send_to_group(self):
        """Start sending to all contacts in the selected group."""
        name = self.group_name_entry.get().strip()
        g = self.contacts_mgr.get_by_name(name) if name else None
        if not g or not g["contacts"]:
            messagebox.showwarning(self.tr("msg_alert"), self.tr("msg_select_group_with_contacts"))
            return
        # Switch to main tab and start with these contacts
        self._switch_tab("main")
        self.contacts_entry.delete(0, "end")
        self.contacts_entry.insert(0, f"[GROUP:{name}]")
        messagebox.showinfo(self.tr("msg_done"), self.tr("msg_group_selected").format(name=name, count=len(g['contacts'])))

    # ════════════════════════════════════════════════════════════
    #  WORKFLOWS
    # ════════════════════════════════════════════════════════════


    # ═══════════════════════════════════════════════════════════════════════
    #  SCHEDULING
    # ═══════════════════════════════════════════════════════════════════════


    # ═══════════════════════════════════════════════════════════════════════
    #  ANALYTICS TAB
    # ═══════════════════════════════════════════════════════════════════════


    def _refresh_numbers_table(self, contacts):
        """Reload the numbers preview table from contacts list."""
        for item in self.progress_tree.get_children():
            self.progress_tree.delete(item)
        for c in contacts:
            name = c.get("name") or self.tr("default_contact_name")
            phone = c.get("phone") or ""
            var1 = c.get("var1") or c.get("variable1") or ""
            self.progress_tree.insert("", "end", values=(name, phone, var1, self.tr("pending_status")), tags=("pending",))
        self._update_contacts_count_from_tree()

    def _update_contacts_count_from_tree(self):
        """Update the contacts count label from the table rows."""
        total = len(self.progress_tree.get_children())
        self.total_counts_label.configure(text=self.tr("lbl_groups_count_contacts").format(total=total))

    def _show_import_popup_menu(self):
        """Show the import options popup menu (file, manual, bulk, generate)."""
        import tkinter as tk
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label=self.tr("popup_import_excel"), command=self._browse_contacts)
        menu.add_command(label=self.tr("popup_import_group"), command=self._open_import_dialog)
        menu.add_command(label=self.tr("popup_num_gen"), command=self._open_number_generator)
        try:
            x = self.btn_tbl_menu.winfo_rootx()
            y = self.btn_tbl_menu.winfo_rooty() + self.btn_tbl_menu.winfo_height()
            menu.post(x, y)
        except Exception as exc:
            logger.debug("Could not show import popup menu: %s", exc)

    def _remove_selected_table_number(self):
        """Remove the selected row from the numbers table."""
        selected = self.progress_tree.selection()
        if not selected:
            self._show_dialog("warning", self.tr("msg_alert"), self.tr("msg_select_row"))
            return
        for item in selected:
            self.progress_tree.delete(item)
        self._update_contacts_count_from_tree()

    def _show_numbers_context_menu(self, event):
        """Show the right-click context menu on the numbers table."""
        try:
            self.numbers_context_menu.post(event.x_root, event.y_root)
        except Exception as exc:
            logger.debug("Could not show numbers context menu: %s", exc)

    def _clear_numbers_table(self):
        """Clear all rows from the numbers preview table."""
        for item in self.progress_tree.get_children():
            self.progress_tree.delete(item)
        self._update_contacts_count_from_tree()
        self.log(self.tr("msg_list_cleared"))

    def _show_attachments_popup_menu(self):
        """Show the attachments add popup menu."""
        import tkinter as tk
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label=self.tr("popup_add_image"), command=lambda: self.attachment_manager.add_attachment("image"))
        menu.add_command(label=self.tr("popup_add_doc"), command=lambda: self.attachment_manager.add_attachment("document"))
        menu.add_command(label=self.tr("popup_add_audio"), command=lambda: self.attachment_manager.add_attachment("audio"))
        menu.add_separator()
        menu.add_command(label=self.tr("popup_clear_attach"), command=lambda: self.attachment_manager.clear())
        try:
            x = self.btn_atts_menu.winfo_rootx()
            y = self.btn_atts_menu.winfo_rooty() + self.btn_atts_menu.winfo_height()
            menu.post(x, y)
        except Exception as exc:
            logger.debug("Could not show attachments popup menu: %s", exc)

    def _build_schedule_queue_card(self, parent):
        """Build the Scheduled Campaigns Queue table card inside Settings tab."""
        queue_card = ctk.CTkFrame(parent, corner_radius=10)
        queue_card.pack(fill="x", padx=10, pady=8)

        is_ar = self.current_lang.get() == "ar"
        side_lbl = "right" if is_ar else "left"
        side_opposite = "left" if is_ar else "right"
        anchor_val = "e" if is_ar else "w"

        # Header Row
        hdr = ctk.CTkFrame(queue_card, fg_color="transparent")
        hdr.pack(fill="x", padx=15, pady=(10, 5))

        ctk.CTkLabel(hdr, text=self.tr("schedule_header"),
                     font=ctk.CTkFont(size=14, weight="bold")).pack(side=side_lbl)

        refresh_btn = ctk.CTkButton(
            hdr, text=self.tr("schedule_btn_refresh"), width=90, height=26,
            fg_color="transparent", hover_color=COLORS["bg_dark"],
            text_color=COLORS["text_main"], font=ctk.CTkFont(size=11),
            command=self._refresh_schedule_queue
        )
        refresh_btn.pack(side=side_opposite)

        # Table Row using ttk.Treeview
        tbl_frame = ctk.CTkFrame(queue_card, fg_color="transparent")
        tbl_frame.pack(fill="x", padx=15, pady=5)

        columns = ("id", "name", "time", "target", "status")
        self.schedule_tree = ttk.Treeview(tbl_frame, columns=columns, show="headings", height=5)
        
        self.schedule_tree.heading("id", text="ID")
        self.schedule_tree.heading("name", text=self.tr("schedule_col_name"))
        self.schedule_tree.heading("time", text=self.tr("schedule_col_time"))
        self.schedule_tree.heading("target", text=self.tr("schedule_col_target"))
        self.schedule_tree.heading("status", text=self.tr("col_status"))

        self.schedule_tree.column("id", width=40, anchor="center")
        self.schedule_tree.column("name", width=150, anchor=anchor_val)
        self.schedule_tree.column("time", width=120, anchor="center")
        self.schedule_tree.column("target", width=100, anchor=anchor_val)
        self.schedule_tree.column("status", width=80, anchor="center")

        # Scrollbar
        scroll_y = ttk.Scrollbar(tbl_frame, orient="vertical", command=self.schedule_tree.yview)
        self.schedule_tree.configure(yscrollcommand=scroll_y.set)
        
        self.schedule_tree.pack(side=side_lbl, fill="both", expand=True)
        scroll_y.pack(side=side_opposite, fill="y")

        # Action Buttons Row
        btn_row = ctk.CTkFrame(queue_card, fg_color="transparent")
        btn_row.pack(fill="x", padx=15, pady=(5, 12))

        cancel_btn = ctk.CTkButton(
            btn_row, text=self.tr("schedule_btn_cancel"), width=110, height=30,
            fg_color=COLORS["danger"], hover_color=COLORS["danger_hover"],
            text_color="#FFFFFF", font=ctk.CTkFont(size=12, weight="bold"),
            command=self._cancel_selected_schedule
        )
        cancel_btn.pack(side=side_lbl, padx=5)

        delete_btn = ctk.CTkButton(
            btn_row, text=self.tr("schedule_btn_delete"), width=100, height=30,
            fg_color=COLORS["secondary"], hover_color=COLORS["danger_hover"],
            text_color=COLORS["secondary_text"], font=ctk.CTkFont(size=12),
            command=self._delete_selected_schedule
        )
        delete_btn.pack(side=side_lbl, padx=5)

        self._refresh_schedule_queue()

    def _refresh_schedule_queue(self):
        """Reload scheduled campaigns from DB and populate the schedule_tree."""
        if not hasattr(self, "schedule_tree"):
            return
        # Clear
        for item in self.schedule_tree.get_children():
            self.schedule_tree.delete(item)
            
        camps = self.scheduler.get_all_campaigns()
        
        # Color codes based on status
        self.schedule_tree.tag_configure("pending", foreground=COLORS.get("info", "#0284C7"))
        self.schedule_tree.tag_configure("sending", foreground=COLORS.get("primary", "#16A34A"))
        self.schedule_tree.tag_configure("completed", foreground="#16A34A")
        self.schedule_tree.tag_configure("failed", foreground=COLORS.get("danger", "#DC2626"))
        self.schedule_tree.tag_configure("cancelled", foreground=COLORS.get("text_muted", "#94A3B8"))

        for c in camps:
            target = c["group_name"] if c["group_name"] else self.tr("source_file_manual").replace("📂 ", "")
            status_map = {
                "pending": self.tr("status_pending"),
                "sending": self.tr("status_sending"),
                "completed": self.tr("status_completed"),
                "failed": self.tr("status_failed"),
                "cancelled": self.tr("status_cancelled")
            }
            status_txt = status_map.get(c["status"], c["status"])
            self.schedule_tree.insert(
                "", "end",
                values=(c["id"], c["name"], c["scheduled_time"], target, status_txt),
                tags=(c["status"],)
            )

    def _cancel_selected_schedule(self):
        """Cancel the selected campaign in the schedule table."""
        sel = self.schedule_tree.selection()
        if not sel:
            messagebox.showwarning(self.tr("msg_alert"), self.tr("msg_select_campaign"))
            return
        item_id = self.schedule_tree.item(sel[0], "values")[0]
        if messagebox.askyesno(self.tr("msg_confirm"), self.tr("msg_confirm_cancel_campaign").format(id=item_id)):
            self.scheduler.cancel_campaign(int(item_id))
            self._refresh_schedule_queue()

    def _delete_selected_schedule(self):
        """Delete the selected campaign from the schedule queue permanently."""
        sel = self.schedule_tree.selection()
        if not sel:
            messagebox.showwarning(self.tr("msg_alert"), self.tr("msg_select_campaign"))
            return
        item_id = self.schedule_tree.item(sel[0], "values")[0]
        if messagebox.askyesno(self.tr("msg_confirm"), self.tr("msg_confirm_delete_campaign").format(id=item_id)):
            self.scheduler.delete_campaign(int(item_id))
            self._refresh_schedule_queue()

    def _on_main_group_select(self, group_name: str):
        """Callback when a group is selected in the main tab dropdown."""
        if not group_name or group_name == self.tr("groups_select_dropdown"):
            return
        g = self.contacts_mgr.get_by_name(group_name)
        if g and g.get("contacts"):
            contacts = g["contacts"]
            self.contacts_entry.delete(0, "end")
            self.contacts_entry.insert(0, f"[GROUP:{group_name}]")
            self._refresh_numbers_table(contacts)
            self.log(self.tr("msg_group_contacts_loaded").format(count=len(contacts), name=group_name))

    def _refresh_main_group_combobox(self):
        """Refresh the group selection combobox values in the main tab."""
        if not hasattr(self, "main_group_select"):
            return
        group_names = [self.tr("groups_select_dropdown")] + self.contacts_mgr.get_names()
        self.main_group_select.configure(values=group_names)
        self.main_group_select.set(self.tr("groups_select_dropdown"))

    def _on_source_mode_change(self, mode: str):
        """Toggle UI elements based on selected source mode."""
        is_ar = self.current_lang.get() == "ar"
        side_lbl = "right" if is_ar else "left"
        
        # Check either the translated EN value or AR value
        is_saved_group = mode == self.tr("source_saved_group") or "مجموعة محفوظة" in mode or "Saved Group" in mode
        
        if is_saved_group:
            # Show group combobox
            self.lbl_select_group.pack(side=side_lbl, padx=5)
            self.main_group_select.pack(side=side_lbl, padx=5)
            self.btn_refresh_combo.pack(side=side_lbl, padx=2)
            self._refresh_main_group_combobox()
        else:
            # Hide group combobox
            self.lbl_select_group.pack_forget()
            self.main_group_select.pack_forget()
            self.btn_refresh_combo.pack_forget()
            # Clear main group select value
            self.main_group_select.set(self.tr("groups_select_dropdown"))
            self.contacts_entry.delete(0, "end")

    def _filter_group_contacts(self, event=None):
        """Filter and refresh the group contacts Treeview dynamically."""
        query = self.group_contact_search.get().strip().lower()
        
        # Clear Treeview
        for item in self.group_contacts_tree.get_children():
            self.group_contacts_tree.delete(item)
            
        if not hasattr(self, "_current_group_contacts") or not self._current_group_contacts:
            self.group_info_label.configure(text=self.tr("msg_contacts_count").format(count=0))
            return
            
        filtered = []
        for c in self._current_group_contacts:
            name = c.get("name", "") or ""
            phone = c.get("phone", "") or ""
            if not query or query in name.lower() or query in phone:
                filtered.append(c)
                self.group_contacts_tree.insert("", "end", values=(name, phone))
                
        total = len(self._current_group_contacts)
        filtered_count = len(filtered)
        if query:
            self.group_info_label.configure(text=self.tr("msg_contacts_filtered").format(filtered=filtered_count, total=total))
        else:
            group_name = self.group_name_entry.get().strip()
            g = self.contacts_mgr.get_by_name(group_name) if group_name else None
            updated = g.get("updated", "-") if g else "-"
            self.group_info_label.configure(text=self.tr("msg_contacts_count_updated").format(total=total, updated=updated))

    def _on_add_single_contact_click(self):
        """Open a small dialog to add a single contact to the currently selected group."""
        group_name = self.group_name_entry.get().strip()
        if not group_name or not self.contacts_mgr.get_by_name(group_name):
            messagebox.showwarning(self.tr("msg_alert"), self.tr("msg_select_group_to_add"))
            return
            
        win = ctk.CTkToplevel(self)
        win.title(self.tr("dialog_add_contact_title"))
        win.geometry("400x280")
        win.resizable(False, False)
        win.grab_set()
        
        # Center the window
        win.update_idletasks()
        width = win.winfo_width()
        height = win.winfo_height()
        x = (win.winfo_screenwidth() // 2) - (width // 2)
        y = (win.winfo_screenheight() // 2) - (height // 2)
        win.geometry(f"+{x}+{y}")
        
        is_ar = self.current_lang.get() == "ar"
        anchor_val = "e" if is_ar else "w"
        side_lbl = "right" if is_ar else "left"
        side_opposite = "left" if is_ar else "right"
        
        # Label Title
        ctk.CTkLabel(
            win, text=self.tr("dialog_add_contact_header").format(name=group_name),
            font=("Segoe UI", 13, "bold"), text_color=COLORS["primary"], justify="center"
        ).pack(pady=(15, 10))
        
        # Input Name
        lbl_name = ctk.CTkLabel(win, text=self.tr("col_name") + ":", font=("Segoe UI", 11, "bold"))
        lbl_name.pack(anchor=anchor_val, padx=30, pady=(5, 2))
        entry_name = ctk.CTkEntry(win, height=32, placeholder_text=self.tr("dialog_add_contact_name_placeholder"))
        entry_name.pack(fill="x", padx=30)
        
        # Input Phone
        lbl_phone = ctk.CTkLabel(win, text=self.tr("dialog_add_contact_phone_lbl"), font=("Segoe UI", 11, "bold"))
        lbl_phone.pack(anchor=anchor_val, padx=30, pady=(10, 2))
        entry_phone = ctk.CTkEntry(win, height=32, placeholder_text=self.tr("dialog_add_contact_phone_placeholder"))
        entry_phone.pack(fill="x", padx=30)
        
        # Button Action
        btn_row = ctk.CTkFrame(win, fg_color="transparent")
        btn_row.pack(fill="x", padx=30, pady=(20, 10))
        
        def _save():
            c_name = entry_name.get().strip()
            c_phone = entry_phone.get().strip()
            
            # Simple validations
            if not c_phone:
                messagebox.showwarning(self.tr("msg_alert"), self.tr("dialog_add_contact_err_phone"))
                return
            # Remove leading + if any
            if c_phone.startswith("+"):
                c_phone = c_phone[1:]
            if not c_phone.isdigit():
                messagebox.showwarning(self.tr("msg_alert"), self.tr("dialog_add_contact_err_digits"))
                return
                
            # If name is empty, use 'default_contact_name'
            if not c_name:
                c_name = self.tr("default_contact_name")
                
            # Call contact manager
            success = self.contacts_mgr.add_contact(group_name, c_phone, c_name)
            if success:
                messagebox.showinfo(self.tr("msg_done"), self.tr("dialog_add_contact_success").format(name=c_name))
                win.destroy()
                # Refresh group contacts list
                self._refresh_groups_list()
                self._select_group(group_name)
            else:
                messagebox.showwarning(self.tr("msg_alert"), self.tr("dialog_add_contact_exists"))
                
        btn_save = ctk.CTkButton(
            btn_row, text=self.tr("dialog_add_contact_save"), width=120, height=34,
            fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"],
            command=_save
        )
        btn_save.pack(side=side_lbl, padx=5)
        
        btn_cancel = ctk.CTkButton(
            btn_row, text=self.tr("dialog_btn_cancel"), width=80, height=34,
            fg_color=COLORS["secondary"], hover_color=COLORS["secondary_hover"],
            text_color=COLORS["secondary_text"],
            command=win.destroy
        )
        btn_cancel.pack(side=side_opposite, padx=5)

    def _on_delete_single_contact_click(self):
        """Delete the selected contact in the group contacts treeview."""
        group_name = self.group_name_entry.get().strip()
        if not group_name:
            return
            
        selection = self.group_contacts_tree.selection()
        if not selection:
            messagebox.showwarning(self.tr("msg_alert"), self.tr("dialog_del_contact_select"))
            return
            
        # Get selected phone number from tree item values
        vals = self.group_contacts_tree.item(selection[0], "values")
        contact_name = vals[0]
        phone = vals[1]
        
        if messagebox.askyesno(self.tr("dialog_del_contact_confirm_title"), self.tr("dialog_del_contact_confirm_msg").format(name=contact_name, phone=phone)):
            success = self.contacts_mgr.remove_contact(group_name, phone)
            if success:
                messagebox.showinfo(self.tr("msg_done"), self.tr("dialog_del_contact_success"))
                # Refresh group contacts list
                self._refresh_groups_list()
                self._select_group(group_name)
            else:
                messagebox.showerror(self.tr("msg_error"), self.tr("dialog_del_contact_error"))

