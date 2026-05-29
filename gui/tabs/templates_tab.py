"""WhatsApp Sender Pro — Templates Tab builder module."""
import customtkinter as ctk
from gui.theme import COLORS


def build_templates_tab(self, frame: ctk.CTkFrame) -> None:
    """Build the message templates management tab."""
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
