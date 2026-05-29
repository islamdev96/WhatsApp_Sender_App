"""WhatsApp Sender Pro — Groups Tab builder module."""
import customtkinter as ctk
from tkinter import ttk
from gui.theme import COLORS


def build_groups_tab(self, frame: ctk.CTkFrame) -> None:
    """Build the contact groups management tab."""
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
    self.group_info_label.pack(anchor=anchor_val, padx=12, pady=(0, 10))

    self._refresh_groups_list()
