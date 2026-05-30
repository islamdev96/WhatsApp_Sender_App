"""WhatsApp Sender Pro — Numbers Filter Tab builder module.

Provides a dedicated tab for filtering/validating WhatsApp numbers.
Users can import numbers, run validation checks, view results with
status indicators, and export valid/invalid numbers separately.
"""
import customtkinter as ctk
from tkinter import ttk, filedialog, messagebox
import threading
import os
import csv
import datetime

from gui.theme import COLORS
from utils.logger import logger


def build_numbers_filter_tab(self, frame: ctk.CTkFrame) -> None:
    """Build the Numbers Filter tab with import, validation table, progress, and export."""
    self.tab_frames["filter"] = frame

    is_ar = self.current_lang.get() == "ar"
    anchor_val = "e" if is_ar else "w"
    side_lbl = "right" if is_ar else "left"
    side_opp = "left" if is_ar else "right"

    # ── Header ──
    header_frame = ctk.CTkFrame(frame, fg_color="transparent")
    header_frame.pack(fill="x", padx=20, pady=(15, 5))

    ctk.CTkLabel(
        header_frame, text=self.tr("filter_header"),
        font=ctk.CTkFont(size=20, weight="bold")
    ).pack(side=side_lbl, padx=5)

    ctk.CTkLabel(
        header_frame, text=self.tr("filter_desc"),
        font=ctk.CTkFont(size=12), text_color=COLORS["text_muted"]
    ).pack(side=side_lbl, padx=15)

    # ── Import & Controls Row ──
    controls_frame = ctk.CTkFrame(frame, corner_radius=12)
    controls_frame.pack(fill="x", padx=20, pady=(10, 5))

    ctrl_inner = ctk.CTkFrame(controls_frame, fg_color="transparent")
    ctrl_inner.pack(fill="x", padx=15, pady=12)

    # Import from file button
    ctk.CTkButton(
        ctrl_inner, text=self.tr("filter_btn_import"),
        font=ctk.CTkFont(size=12, weight="bold"),
        width=160, height=36, corner_radius=8,
        fg_color=COLORS["secondary"], hover_color=COLORS["secondary_hover"],
        text_color=COLORS["secondary_text"],
        command=lambda: _import_numbers_for_filter()
    ).pack(side=side_lbl, padx=5)

    # Import from main list button
    ctk.CTkButton(
        ctrl_inner, text=self.tr("filter_btn_from_main"),
        font=ctk.CTkFont(size=12),
        width=180, height=36, corner_radius=8,
        fg_color=COLORS["secondary"], hover_color=COLORS["secondary_hover"],
        text_color=COLORS["secondary_text"],
        command=lambda: _import_from_main_list()
    ).pack(side=side_lbl, padx=5)

    # Manual add button
    ctk.CTkButton(
        ctrl_inner, text=self.tr("filter_btn_add_manual"),
        font=ctk.CTkFont(size=12),
        width=140, height=36, corner_radius=8,
        fg_color=COLORS["secondary"], hover_color=COLORS["secondary_hover"],
        text_color=COLORS["secondary_text"],
        command=lambda: _add_manual_number()
    ).pack(side=side_lbl, padx=5)

    # Clear all button
    ctk.CTkButton(
        ctrl_inner, text=self.tr("filter_btn_clear"),
        font=ctk.CTkFont(size=12),
        width=100, height=36, corner_radius=8,
        fg_color=COLORS["danger"], hover_color=COLORS["danger_hover"],
        text_color="#FFFFFF",
        command=lambda: _clear_filter_table()
    ).pack(side=side_opp, padx=5)

    # ── Numbers Table ──
    table_frame = ctk.CTkFrame(frame, corner_radius=12)
    table_frame.pack(fill="both", expand=True, padx=20, pady=5)

    columns = ("number", "status", "check_time")
    self.filter_tree = ttk.Treeview(
        table_frame, columns=columns, show="headings",
        selectmode="extended", height=15
    )
    self.filter_tree.heading("number", text=self.tr("col_number"))
    self.filter_tree.heading("status", text=self.tr("filter_col_status"))
    self.filter_tree.heading("check_time", text=self.tr("filter_col_time"))

    self.filter_tree.column("number", width=250, anchor="center")
    self.filter_tree.column("status", width=150, anchor="center")
    self.filter_tree.column("check_time", width=200, anchor="center")

    # Scrollbar
    scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.filter_tree.yview)
    self.filter_tree.configure(yscrollcommand=scrollbar.set)

    self.filter_tree.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=10)
    scrollbar.pack(side="right", fill="y", padx=(0, 10), pady=10)

    # Tag colors for statuses
    self.filter_tree.tag_configure("valid", foreground="#2E7D32")
    self.filter_tree.tag_configure("invalid", foreground="#C62828")
    self.filter_tree.tag_configure("pending", foreground="#F57C00")
    self.filter_tree.tag_configure("unknown", foreground="#757575")

    # ── Progress & Stats Row ──
    progress_frame = ctk.CTkFrame(frame, corner_radius=12)
    progress_frame.pack(fill="x", padx=20, pady=5)

    prog_inner = ctk.CTkFrame(progress_frame, fg_color="transparent")
    prog_inner.pack(fill="x", padx=15, pady=10)

    # Stats labels
    stats_frame = ctk.CTkFrame(prog_inner, fg_color="transparent")
    stats_frame.pack(side=side_lbl, padx=5)

    self.filter_total_lbl = ctk.CTkLabel(
        stats_frame, text=self.tr("filter_total").format(count=0),
        font=ctk.CTkFont(size=12, weight="bold")
    )
    self.filter_total_lbl.pack(side="left", padx=8)

    self.filter_valid_lbl = ctk.CTkLabel(
        stats_frame, text=self.tr("filter_valid").format(count=0),
        font=ctk.CTkFont(size=12, weight="bold"), text_color="#2E7D32"
    )
    self.filter_valid_lbl.pack(side="left", padx=8)

    self.filter_invalid_lbl = ctk.CTkLabel(
        stats_frame, text=self.tr("filter_invalid").format(count=0),
        font=ctk.CTkFont(size=12, weight="bold"), text_color="#C62828"
    )
    self.filter_invalid_lbl.pack(side="left", padx=8)

    self.filter_pending_lbl = ctk.CTkLabel(
        stats_frame, text=self.tr("filter_pending_count").format(count=0),
        font=ctk.CTkFont(size=12), text_color="#F57C00"
    )
    self.filter_pending_lbl.pack(side="left", padx=8)

    # Progress bar
    self.filter_progress = ctk.CTkProgressBar(
        prog_inner, width=300, height=14,
        progress_color=COLORS["primary"],
        fg_color=COLORS["border"]
    )
    self.filter_progress.pack(side=side_opp, padx=10)
    self.filter_progress.set(0)

    # ── Action Buttons Row ──
    action_frame = ctk.CTkFrame(frame, fg_color="transparent")
    action_frame.pack(fill="x", padx=20, pady=(5, 15))

    # Start Filter button
    self.filter_start_btn = ctk.CTkButton(
        action_frame, text=self.tr("filter_btn_start"),
        font=ctk.CTkFont(size=14, weight="bold"),
        width=180, height=42, corner_radius=10,
        fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"],
        text_color="#FFFFFF",
        command=lambda: _start_filter()
    )
    self.filter_start_btn.pack(side=side_lbl, padx=5)

    # Stop Filter button
    self.filter_stop_btn = ctk.CTkButton(
        action_frame, text=self.tr("filter_btn_stop"),
        font=ctk.CTkFont(size=14, weight="bold"),
        width=140, height=42, corner_radius=10,
        fg_color=COLORS["danger"], hover_color=COLORS["danger_hover"],
        text_color="#FFFFFF",
        state="disabled",
        command=lambda: _stop_filter()
    )
    self.filter_stop_btn.pack(side=side_lbl, padx=5)

    # Export Valid
    ctk.CTkButton(
        action_frame, text=self.tr("filter_btn_export_valid"),
        font=ctk.CTkFont(size=12, weight="bold"),
        width=150, height=42, corner_radius=10,
        fg_color="#2E7D32", hover_color="#1B5E20",
        text_color="#FFFFFF",
        command=lambda: _export_numbers("valid")
    ).pack(side=side_opp, padx=5)

    # Export Invalid
    ctk.CTkButton(
        action_frame, text=self.tr("filter_btn_export_invalid"),
        font=ctk.CTkFont(size=12, weight="bold"),
        width=150, height=42, corner_radius=10,
        fg_color="#C62828", hover_color="#B71C1C",
        text_color="#FFFFFF",
        command=lambda: _export_numbers("invalid")
    ).pack(side=side_opp, padx=5)

    # Export All
    ctk.CTkButton(
        action_frame, text=self.tr("filter_btn_export_all"),
        font=ctk.CTkFont(size=12),
        width=130, height=42, corner_radius=10,
        fg_color=COLORS["secondary"], hover_color=COLORS["secondary_hover"],
        text_color=COLORS["secondary_text"],
        command=lambda: _export_numbers("all")
    ).pack(side=side_opp, padx=5)

    # ═══════════════════════════════════════════════════════════════════
    # Internal Functions
    # ═══════════════════════════════════════════════════════════════════

    # Track filter state
    self._filter_stop_event = threading.Event()
    self._filter_running = False

    def _update_filter_stats():
        """Recount items and update stat labels."""
        total = len(self.filter_tree.get_children())
        valid = len([i for i in self.filter_tree.get_children()
                     if self.filter_tree.item(i, "tags") and "valid" in self.filter_tree.item(i, "tags")])
        invalid = len([i for i in self.filter_tree.get_children()
                       if self.filter_tree.item(i, "tags") and "invalid" in self.filter_tree.item(i, "tags")])
        pending = total - valid - invalid

        self.filter_total_lbl.configure(text=self.tr("filter_total").format(count=total))
        self.filter_valid_lbl.configure(text=self.tr("filter_valid").format(count=valid))
        self.filter_invalid_lbl.configure(text=self.tr("filter_invalid").format(count=invalid))
        self.filter_pending_lbl.configure(text=self.tr("filter_pending_count").format(count=pending))

        if total > 0:
            self.filter_progress.set((valid + invalid) / total)
        else:
            self.filter_progress.set(0)

    def _import_numbers_for_filter():
        """Import numbers from CSV/Excel file into the filter table."""
        filetypes = [
            ("Contacts", "*.csv;*.xlsx;*.xls;*.txt"),
            ("All files", "*.*")
        ]
        filepath = filedialog.askopenfilename(
            title=self.tr("dialog_select_file"),
            filetypes=filetypes
        )
        if not filepath:
            return

        try:
            from utils.helpers import read_contacts_auto
            contacts = read_contacts_auto(filepath)
            count = 0
            for c in contacts:
                phone = str(c.get("phone", c.get("Phone", ""))).strip()
                if phone:
                    # Avoid duplicates
                    existing = [self.filter_tree.item(i, "values")[0]
                                for i in self.filter_tree.get_children()]
                    if phone not in existing:
                        self.filter_tree.insert(
                            "", "end", values=(phone, self.tr("filter_status_pending"), "—"),
                            tags=("pending",)
                        )
                        count += 1
            _update_filter_stats()
            self.log(f"📥 {self.tr('filter_imported')} {count}")
        except Exception as exc:
            logger.debug("Filter import error: %s", exc)
            messagebox.showerror(self.tr("msg_error"), str(exc))

    def _import_from_main_list():
        """Import numbers from the main campaign numbers table."""
        if not hasattr(self, "numbers_tree"):
            return
        count = 0
        existing = [self.filter_tree.item(i, "values")[0]
                    for i in self.filter_tree.get_children()]
        for item in self.numbers_tree.get_children():
            vals = self.numbers_tree.item(item, "values")
            phone = str(vals[1]).strip() if len(vals) > 1 else ""
            if phone and phone not in existing:
                self.filter_tree.insert(
                    "", "end", values=(phone, self.tr("filter_status_pending"), "—"),
                    tags=("pending",)
                )
                count += 1
        _update_filter_stats()
        self.log(f"📥 {self.tr('filter_from_main')} {count}")

    def _add_manual_number():
        """Add a single number manually via input dialog."""
        dialog = ctk.CTkInputDialog(
            text=self.tr("dialog_add_contact_phone_lbl"),
            title=self.tr("filter_btn_add_manual")
        )
        val = dialog.get_input()
        if val and val.strip():
            phone = val.strip().replace("+", "")
            existing = [self.filter_tree.item(i, "values")[0]
                        for i in self.filter_tree.get_children()]
            if phone not in existing:
                self.filter_tree.insert(
                    "", "end", values=(phone, self.tr("filter_status_pending"), "—"),
                    tags=("pending",)
                )
                _update_filter_stats()

    def _clear_filter_table():
        """Clear all items from the filter table."""
        for item in self.filter_tree.get_children():
            self.filter_tree.delete(item)
        _update_filter_stats()

    def _start_filter():
        """Start the number validation process in a background thread."""
        items = self.filter_tree.get_children()
        pending_items = [i for i in items
                         if self.filter_tree.item(i, "tags") and "pending" in self.filter_tree.item(i, "tags")]
        if not pending_items:
            messagebox.showinfo(self.tr("msg_alert"), self.tr("filter_no_pending"))
            return

        if not self.bot:
            messagebox.showwarning(self.tr("msg_alert"), self.tr("filter_need_login"))
            return

        self._filter_stop_event.clear()
        self._filter_running = True
        self.filter_start_btn.configure(state="disabled")
        self.filter_stop_btn.configure(state="normal")

        def _filter_thread():
            import time
            import random
            for item_id in pending_items:
                if self._filter_stop_event.is_set():
                    break

                vals = self.filter_tree.item(item_id, "values")
                phone = vals[0]

                try:
                    # Use the bot's number checking capability
                    is_valid = self.bot.check_number_exists(phone)
                    now = datetime.datetime.now().strftime("%H:%M:%S")
                    if is_valid:
                        self._run_on_ui(lambda iid=item_id, t=now: (
                            self.filter_tree.item(iid, values=(phone, self.tr("filter_status_valid"), t), tags=("valid",)),
                        ))
                    else:
                        self._run_on_ui(lambda iid=item_id, t=now: (
                            self.filter_tree.item(iid, values=(phone, self.tr("filter_status_invalid"), t), tags=("invalid",)),
                        ))
                except Exception as exc:
                    now = datetime.datetime.now().strftime("%H:%M:%S")
                    logger.debug("Filter check error for %s: %s", phone, exc)
                    self._run_on_ui(lambda iid=item_id, t=now: (
                        self.filter_tree.item(iid, values=(phone, self.tr("filter_status_error"), t), tags=("invalid",)),
                    ))

                self._run_on_ui(lambda: _update_filter_stats())
                # Random delay to avoid detection
                time.sleep(random.uniform(2, 5))

            self._filter_running = False
            self._run_on_ui(lambda: self.filter_start_btn.configure(state="normal"))
            self._run_on_ui(lambda: self.filter_stop_btn.configure(state="disabled"))
            self._run_on_ui(lambda: _update_filter_stats())
            self._run_on_ui(lambda: self.log(f"✅ {self.tr('filter_complete')}"))

        t = threading.Thread(target=_filter_thread, daemon=True)
        t.start()

    def _stop_filter():
        """Stop the running filter process."""
        self._filter_stop_event.set()
        self.filter_stop_btn.configure(state="disabled")
        self.log(f"🛑 {self.tr('filter_stopped')}")

    def _export_numbers(export_type):
        """Export filtered numbers to a CSV file."""
        items = self.filter_tree.get_children()
        if not items:
            messagebox.showinfo(self.tr("msg_alert"), self.tr("filter_no_data"))
            return

        rows = []
        for item_id in items:
            vals = self.filter_tree.item(item_id, "values")
            tags = self.filter_tree.item(item_id, "tags")
            phone = vals[0]
            status = vals[1]

            if export_type == "valid" and "valid" not in tags:
                continue
            elif export_type == "invalid" and "invalid" not in tags:
                continue
            rows.append({"Phone": phone, "Status": status})

        if not rows:
            messagebox.showinfo(self.tr("msg_alert"), self.tr("filter_no_matching"))
            return

        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv")],
            initialfile=f"filtered_{export_type}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )
        if not filepath:
            return

        try:
            with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.DictWriter(f, fieldnames=["Phone", "Status"])
                writer.writeheader()
                writer.writerows(rows)
            messagebox.showinfo(self.tr("msg_done"), self.tr("filter_exported").format(count=len(rows)))
            self.log(f"📤 {self.tr('filter_exported').format(count=len(rows))}")
        except Exception as exc:
            logger.debug("Filter export error: %s", exc)
            messagebox.showerror(self.tr("msg_error"), str(exc))
