"""WhatsApp Sender Pro — Log Tab builder module."""
import customtkinter as ctk
from gui.theme import COLORS


def build_log_tab(self, frame: ctk.CTkFrame) -> None:
    """Build the event log/diagnostic tab."""
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
