"""WhatsApp Sender Pro — Sent Campaigns Tab builder module.

Displays campaign history with stats, details, and export capabilities.
"""
import customtkinter as ctk
from tkinter import ttk, filedialog, messagebox
import os
import csv
import datetime

from gui.theme import COLORS
from utils.logger import logger


def build_campaigns_tab(self, frame: ctk.CTkFrame) -> None:
    """Build the Sent Campaigns tab with history table, stats cards, and export."""
    self.tab_frames["campaigns"] = frame

    is_ar = self.current_lang.get() == "ar"
    anchor_val = "e" if is_ar else "w"
    side_lbl = "right" if is_ar else "left"
    side_opp = "left" if is_ar else "right"

    # ── Header ──
    header = ctk.CTkLabel(frame, text=self.tr("campaigns_header"),
                          font=ctk.CTkFont(size=20, weight="bold"))
    header.pack(anchor=anchor_val, padx=25, pady=(20, 5))

    desc = ctk.CTkLabel(frame, text=self.tr("campaigns_desc"),
                        font=ctk.CTkFont(size=12), text_color=COLORS["text_muted"])
    desc.pack(anchor=anchor_val, padx=25, pady=(0, 10))

    # ── Stats Cards Row ──
    stats_frame = ctk.CTkFrame(frame, fg_color="transparent")
    stats_frame.pack(fill="x", padx=20, pady=(0, 10))

    def _make_stat_card(parent, title, value, color):
        card = ctk.CTkFrame(parent, corner_radius=12, height=80, width=180)
        card.pack_propagate(False)
        card.pack(side="left", expand=True, fill="x", padx=5)
        ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=11),
                     text_color=COLORS["text_muted"]).pack(anchor="w", padx=15, pady=(12, 0))
        ctk.CTkLabel(card, text=str(value), font=ctk.CTkFont(size=22, weight="bold"),
                     text_color=color).pack(anchor="w", padx=15, pady=(2, 10))
        return card

    # Load campaign stats
    campaigns = self.campaign_manager.get_all()
    total_campaigns = len(campaigns)
    total_sent = sum(c.get("sent", 0) for c in campaigns)
    total_failed = sum(c.get("failed", 0) for c in campaigns)
    success_rate = f"{(total_sent / max(total_sent + total_failed, 1)) * 100:.0f}%"

    self._camp_card_total = _make_stat_card(stats_frame, self.tr("campaigns_stat_total"), total_campaigns, COLORS["primary"])
    self._camp_card_sent = _make_stat_card(stats_frame, self.tr("campaigns_stat_sent"), total_sent, "#2E7D32")
    self._camp_card_failed = _make_stat_card(stats_frame, self.tr("campaigns_stat_failed"), total_failed, COLORS["danger"])
    self._camp_card_rate = _make_stat_card(stats_frame, self.tr("campaigns_stat_rate"), success_rate, COLORS["info"])

    # ── Campaigns Table ──
    table_frame = ctk.CTkFrame(frame, corner_radius=12)
    table_frame.pack(fill="both", expand=True, padx=20, pady=5)

    columns = ("id", "name", "date", "total", "sent", "failed", "rate", "status")
    self.campaigns_tree = ttk.Treeview(
        table_frame, columns=columns, show="headings",
        selectmode="browse", height=12
    )

    col_config = [
        ("id", self.tr("campaigns_col_id"), 50),
        ("name", self.tr("campaigns_col_name"), 180),
        ("date", self.tr("campaigns_col_date"), 150),
        ("total", self.tr("campaigns_col_total"), 80),
        ("sent", self.tr("campaigns_col_sent"), 80),
        ("failed", self.tr("campaigns_col_failed"), 80),
        ("rate", self.tr("campaigns_col_rate"), 80),
        ("status", self.tr("campaigns_col_status"), 100),
    ]

    for col_id, heading, width in col_config:
        self.campaigns_tree.heading(col_id, text=heading)
        self.campaigns_tree.column(col_id, width=width, anchor="center")

    # Scrollbar
    scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.campaigns_tree.yview)
    self.campaigns_tree.configure(yscrollcommand=scrollbar.set)

    self.campaigns_tree.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=10)
    scrollbar.pack(side="right", fill="y", padx=(0, 10), pady=10)

    # Status tag colors
    self.campaigns_tree.tag_configure("completed", foreground="#2E7D32")
    self.campaigns_tree.tag_configure("failed", foreground="#C62828")
    self.campaigns_tree.tag_configure("running", foreground="#F57C00")

    # ── Action Buttons Row ──
    btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
    btn_frame.pack(fill="x", padx=20, pady=(5, 15))

    ctk.CTkButton(
        btn_frame, text=self.tr("campaigns_btn_refresh"),
        font=ctk.CTkFont(size=12, weight="bold"),
        width=140, height=38, corner_radius=8,
        fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"],
        text_color="#FFFFFF",
        command=lambda: _refresh_campaigns()
    ).pack(side=side_lbl, padx=5)

    ctk.CTkButton(
        btn_frame, text=self.tr("campaigns_btn_export"),
        font=ctk.CTkFont(size=12),
        width=140, height=38, corner_radius=8,
        fg_color=COLORS["secondary"], hover_color=COLORS["secondary_hover"],
        text_color=COLORS["secondary_text"],
        command=lambda: _export_campaigns()
    ).pack(side=side_lbl, padx=5)

    ctk.CTkButton(
        btn_frame, text=self.tr("campaigns_btn_delete"),
        font=ctk.CTkFont(size=12),
        width=120, height=38, corner_radius=8,
        fg_color=COLORS["danger"], hover_color=COLORS["danger_hover"],
        text_color="#FFFFFF",
        command=lambda: _delete_campaign()
    ).pack(side=side_opp, padx=5)

    # ═══════════════════════════════════════════════════════════════
    # Internal Functions
    # ═══════════════════════════════════════════════════════════════

    def _refresh_campaigns():
        """Reload campaigns from storage."""
        for item in self.campaigns_tree.get_children():
            self.campaigns_tree.delete(item)

        campaigns = self.campaign_manager.get_all()
        for idx, camp in enumerate(campaigns, 1):
            total = camp.get("total", 0)
            sent = camp.get("sent", 0)
            failed = camp.get("failed", 0)
            rate = f"{(sent / max(total, 1)) * 100:.0f}%" if total else "0%"
            status_key = camp.get("status", "completed")
            status_text = self.tr(f"status_{status_key}") if status_key else self.tr("status_completed")
            tag = status_key if status_key in ("completed", "failed", "running") else "completed"

            self.campaigns_tree.insert("", "end", values=(
                camp.get("id", idx),
                camp.get("name", f"Campaign {idx}"),
                camp.get("date", "—"),
                total, sent, failed, rate, status_text
            ), tags=(tag,))

    def _export_campaigns():
        """Export campaign history to CSV."""
        items = self.campaigns_tree.get_children()
        if not items:
            messagebox.showinfo(self.tr("msg_alert"), self.tr("campaigns_no_data"))
            return

        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv")],
            initialfile=f"campaigns_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )
        if not filepath:
            return

        try:
            with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow(["ID", "Name", "Date", "Total", "Sent", "Failed", "Rate", "Status"])
                for item_id in items:
                    writer.writerow(self.campaigns_tree.item(item_id, "values"))
            messagebox.showinfo(self.tr("msg_done"), self.tr("campaigns_exported"))
        except Exception as exc:
            logger.debug("Campaign export error: %s", exc)
            messagebox.showerror(self.tr("msg_error"), str(exc))

    def _delete_campaign():
        """Delete selected campaign."""
        selected = self.campaigns_tree.selection()
        if not selected:
            messagebox.showinfo(self.tr("msg_alert"), self.tr("msg_select_campaign"))
            return

        vals = self.campaigns_tree.item(selected[0], "values")
        camp_id = vals[0]
        if messagebox.askyesno(self.tr("msg_confirm"),
                               self.tr("msg_confirm_delete_campaign").format(id=camp_id)):
            self.campaigns_tree.delete(selected[0])
            try:
                self.campaign_manager.delete(int(camp_id))
            except Exception:
                pass

    # Initial load
    _refresh_campaigns()
