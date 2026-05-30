"""WhatsApp Sender Pro — Received Messages Tab builder module.

Standalone tab for viewing incoming WhatsApp messages.
"""
import customtkinter as ctk
from tkinter import ttk
import datetime

from gui.theme import COLORS
from utils.logger import logger


def build_received_tab(self, frame: ctk.CTkFrame) -> None:
    """Build the Received Messages tab with incoming message log and search."""
    self.tab_frames["received"] = frame

    is_ar = self.current_lang.get() == "ar"
    anchor_val = "e" if is_ar else "w"
    side_lbl = "right" if is_ar else "left"
    side_opp = "left" if is_ar else "right"

    # ── Header ──
    header = ctk.CTkLabel(frame, text=self.tr("received_header"),
                          font=ctk.CTkFont(size=20, weight="bold"))
    header.pack(anchor=anchor_val, padx=25, pady=(20, 5))

    desc = ctk.CTkLabel(frame, text=self.tr("received_desc"),
                        font=ctk.CTkFont(size=12), text_color=COLORS["text_muted"])
    desc.pack(anchor=anchor_val, padx=25, pady=(0, 10))

    # ── Search Bar ──
    search_frame = ctk.CTkFrame(frame, fg_color="transparent")
    search_frame.pack(fill="x", padx=20, pady=(0, 5))

    self.received_search_entry = ctk.CTkEntry(
        search_frame, height=36, corner_radius=8,
        placeholder_text=self.tr("received_search_placeholder"),
        font=ctk.CTkFont(size=12)
    )
    self.received_search_entry.pack(side=side_lbl, fill="x", expand=True, padx=(0, 10))
    self.received_search_entry.bind("<KeyRelease>", lambda e: _filter_messages())

    ctk.CTkButton(
        search_frame, text=self.tr("received_btn_refresh"),
        font=ctk.CTkFont(size=12),
        width=120, height=36, corner_radius=8,
        fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"],
        text_color="#FFFFFF",
        command=lambda: _refresh_received()
    ).pack(side=side_opp, padx=5)

    # ── Messages Table ──
    table_frame = ctk.CTkFrame(frame, corner_radius=12)
    table_frame.pack(fill="both", expand=True, padx=20, pady=5)

    columns = ("date", "sender", "message")
    self.received_tree = ttk.Treeview(
        table_frame, columns=columns, show="headings",
        selectmode="browse", height=15
    )

    self.received_tree.heading("date", text=self.tr("lbl_date"))
    self.received_tree.heading("sender", text=self.tr("lbl_sender"))
    self.received_tree.heading("message", text=self.tr("lbl_message"))

    self.received_tree.column("date", width=150, anchor="center")
    self.received_tree.column("sender", width=180, anchor="center")
    self.received_tree.column("message", width=400, anchor="w")

    scrollbar = ctk.CTkScrollbar(table_frame, command=self.received_tree.yview)
    self.received_tree.configure(yscrollcommand=scrollbar.set)

    self.received_tree.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=10)
    scrollbar.pack(side="right", fill="y", padx=(0, 10), pady=10)

    # ── Stats Footer ──
    footer_frame = ctk.CTkFrame(frame, fg_color="transparent")
    footer_frame.pack(fill="x", padx=20, pady=(5, 15))

    self.received_count_lbl = ctk.CTkLabel(
        footer_frame, text=self.tr("received_count").format(count=0),
        font=ctk.CTkFont(size=12), text_color=COLORS["text_muted"]
    )
    self.received_count_lbl.pack(side=side_lbl, padx=10)

    ctk.CTkButton(
        footer_frame, text=self.tr("received_btn_clear"),
        font=ctk.CTkFont(size=12),
        width=120, height=36, corner_radius=8,
        fg_color=COLORS["danger"], hover_color=COLORS["danger_hover"],
        text_color="#FFFFFF",
        command=lambda: _clear_received()
    ).pack(side=side_opp, padx=5)

    ctk.CTkButton(
        footer_frame, text=self.tr("received_btn_export"),
        font=ctk.CTkFont(size=12),
        width=120, height=36, corner_radius=8,
        fg_color=COLORS["secondary"], hover_color=COLORS["secondary_hover"],
        text_color=COLORS["secondary_text"],
        command=lambda: _export_received()
    ).pack(side=side_opp, padx=5)

    # ═══════════════════════════════════════════════════════════════
    # Internal Functions
    # ═══════════════════════════════════════════════════════════════

    # Store received messages in memory
    if not hasattr(self, "_received_messages"):
        self._received_messages = []

    def _refresh_received():
        """Reload received messages into the table."""
        for item in self.received_tree.get_children():
            self.received_tree.delete(item)
        for msg in self._received_messages:
            self.received_tree.insert("", "end", values=(
                msg.get("date", ""),
                msg.get("sender", ""),
                msg.get("message", "")[:100]
            ))
        self.received_count_lbl.configure(
            text=self.tr("received_count").format(count=len(self._received_messages))
        )

    def _filter_messages():
        """Filter messages by search query."""
        query = self.received_search_entry.get().strip().lower()
        for item in self.received_tree.get_children():
            self.received_tree.delete(item)
        for msg in self._received_messages:
            sender = msg.get("sender", "").lower()
            text = msg.get("message", "").lower()
            if not query or query in sender or query in text:
                self.received_tree.insert("", "end", values=(
                    msg.get("date", ""),
                    msg.get("sender", ""),
                    msg.get("message", "")[:100]
                ))

    def _clear_received():
        """Clear all received messages."""
        self._received_messages.clear()
        _refresh_received()

    def _export_received():
        """Export received messages to CSV."""
        if not self._received_messages:
            return
        from tkinter import filedialog
        import csv
        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv")],
            initialfile=f"received_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )
        if not filepath:
            return
        try:
            with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.DictWriter(f, fieldnames=["date", "sender", "message"])
                writer.writeheader()
                writer.writerows(self._received_messages)
            self.log(f"📤 Exported {len(self._received_messages)} received messages")
        except Exception as exc:
            logger.debug("Received export error: %s", exc)

    # Method to add received messages (called from chatbot/automation)
    def _add_received_message(sender, message):
        self._received_messages.append({
            "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
            "sender": sender,
            "message": message
        })
        _refresh_received()

    self._add_received_message_func = _add_received_message

    # Initial load
    _refresh_received()
