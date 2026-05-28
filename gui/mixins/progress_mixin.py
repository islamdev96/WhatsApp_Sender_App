"""WhatsApp Sender Pro — Progress window and status updates."""
import customtkinter as ctk
from tkinter import filedialog, messagebox, ttk
import re
import threading
import queue
import time
import random
import os
import csv
import datetime
import json

from gui.theme import COLORS, FONTS, ERROR_CATALOG
from utils.logger import logger


class ProgressMixin:
    """Mixin: Progress window and status updates."""

    def _open_progress_window_blind(self, total, mode="send"):
        def _do():
            if self.progress_win and self.progress_win.winfo_exists():
                try:
                    self.progress_win.destroy()
                except Exception as exc:
                    logger.debug("Could not destroy existing progress window: %s", exc)
            title_map = {
                "send": "متابعة الإرسال",
                "workflow": "متابعة سير العمل",
                "check": "فحص الأرقام",
            }
            title_text = title_map.get(mode, "متابعة العملية")
            self.progress_title_text = title_text
            self.progress_metric_labels = {}
            self.progress_win = ctk.CTkToplevel(self)
            self.progress_win.title(title_text)
            self.progress_win.geometry("1080x720")
            self.progress_win.minsize(980, 600)
            self.progress_win.grab_set()
            self.progress_win.protocol("WM_DELETE_WINDOW", self._close_progress_window)
            
            # Focus
            self.progress_win.after(100, self.progress_win.lift)

            # Main Container
            main_cont = ctk.CTkFrame(self.progress_win, corner_radius=0, fg_color=COLORS["bg_dark"])
            main_cont.pack(fill="both", expand=True)

            # 1. Top Header (Counters)
            header = ctk.CTkFrame(main_cont, corner_radius=10, fg_color=COLORS["card_bg"])
            header.pack(fill="x", padx=15, pady=(15, 10))
            
            # Title & Counter
            top_row = ctk.CTkFrame(header, fg_color="transparent")
            top_row.pack(fill="x", padx=15, pady=(10, 5))
            
            self.progress_count_label = ctk.CTkLabel(
                top_row, text=f"{title_text} (0/{total})",
                font=("Segoe UI", 16, "bold"), text_color=COLORS["text_main"]
            )
            self.progress_count_label.pack(side="left")
            
            status_chip = ctk.CTkLabel(
                top_row, text="جاري",
                font=("Segoe UI", 12, "bold"), text_color=COLORS["bg_dark"],
                fg_color=COLORS["primary"], corner_radius=6, padx=10, pady=2
            )
            status_chip.pack(side="right")
            self.progress_state_label = status_chip

            metrics_row = ctk.CTkFrame(header, fg_color="transparent")
            metrics_row.pack(fill="x", padx=15, pady=(4, 8))
            metric_defs = [
                ("processed", "تمت المعالجة", COLORS["info"], "0"),
                ("sent", "عنده واتساب" if mode == "check" else "تم الإرسال", COLORS["success"], "0"),
                ("failed", "فشل", COLORS["danger"], "0"),
                ("invalid", "بدون واتساب", COLORS["warning"], "0"),
                ("remaining", "متبقي", COLORS["text_muted"], str(total)),
                ("eta", "وقت تقريبي", COLORS["accent"], "--"),
            ]
            metrics_row.grid_columnconfigure(tuple(range(len(metric_defs))), weight=1)
            for idx, (key, label, color, value) in enumerate(metric_defs):
                card = ctk.CTkFrame(metrics_row, corner_radius=8, fg_color=COLORS["bg_dark"])
                card.grid(row=0, column=idx, padx=4, pady=2, sticky="ew")
                ctk.CTkLabel(
                    card, text=label, font=("Segoe UI", 11),
                    text_color=COLORS["text_muted"]
                ).pack(pady=(8, 1))
                value_label = ctk.CTkLabel(
                    card, text=value, font=("Segoe UI", 20, "bold"),
                    text_color=color
                )
                value_label.pack(pady=(0, 8))
                self.progress_metric_labels[key] = value_label

            # Progress Bar (Thick & Green)
            self.progress_bar_small = ctk.CTkProgressBar(header, height=20, corner_radius=0,
                                                         progress_color="#00E676", # Bright Neon Green
                                                         border_color=COLORS["border"], border_width=1)
            self.progress_bar_small.pack(fill="x", expand=True, padx=15, pady=(5, 15))
            self.progress_bar_small.set(0)

            # 2. Data Grid (Treeview)
            table_frame = ctk.CTkFrame(main_cont, corner_radius=10, fg_color=COLORS["card_bg"])
            table_frame.pack(fill="both", expand=True, padx=15, pady=(0, 10))

            columns = ("phone", "name", "date", "status", "message")
            self.popup_progress_tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=15)
            
            self.popup_progress_tree.heading("phone", text="الرقم")
            self.popup_progress_tree.heading("name", text="الاسم / الخطوة")
            self.popup_progress_tree.heading("date", text="الوقت")
            self.popup_progress_tree.heading("status", text="الحالة")
            self.popup_progress_tree.heading("message", text="التفاصيل")
            
            self.popup_progress_tree.column("phone", width=190, anchor="w")
            self.popup_progress_tree.column("name", width=180, anchor="w")
            self.popup_progress_tree.column("date", width=150, anchor="center")
            self.popup_progress_tree.column("status", width=120, anchor="center")
            self.popup_progress_tree.column("message", width=360, anchor="w")

            # Styling the Treeview
            style = ttk.Style(self.progress_win)
            try:
                style.theme_use("clam")
            except Exception as exc:
                logger.debug("Could not apply progress Treeview theme: %s", exc)
            
            bg_color = COLORS["bg_dark"]
            fg_color = COLORS["text_main"]
            row_height = 30
            
            style.configure(
                "Treeview",
                background=bg_color,
                foreground=fg_color,
                fieldbackground=bg_color,
                rowheight=row_height,
                font=("Segoe UI", 11),
                borderwidth=0
            )
            style.configure("Treeview.Heading", font=("Segoe UI", 11, "bold"), background=COLORS["card_bg"], foreground=COLORS["text_main"])
            style.map("Treeview", background=[("selected", COLORS["primary"])], foreground=[("selected", "black")])

            # Tags for coloring rows (Text color)
            self.popup_progress_tree.tag_configure("success", foreground="#00E676") # Green
            self.popup_progress_tree.tag_configure("failed", foreground="#FF3D00")  # Red
            self.popup_progress_tree.tag_configure("waiting", foreground=COLORS["text_muted"])
            self.popup_progress_tree.tag_configure("invalid", foreground="#FFA500") # Orange
            self.popup_progress_tree.tag_configure("stopped", foreground=COLORS["info"])

            tree_scroll = ctk.CTkScrollbar(table_frame, command=self.popup_progress_tree.yview)
            self.popup_progress_tree.configure(yscrollcommand=tree_scroll.set)
            self.popup_progress_tree.pack(side="left", fill="both", expand=True, padx=2, pady=2)
            tree_scroll.pack(side="right", fill="y", padx=2, pady=2)

            # 3. Footer Controls
            footer = ctk.CTkFrame(main_cont, corner_radius=10, fg_color=COLORS["card_bg"], height=60)
            footer.pack(fill="x", padx=15, pady=(0, 15))
            
            self.progress_status_label = ctk.CTkLabel(
                footer, text="جاهز للبدء...", font=("Segoe UI", 12), text_color=COLORS["text_muted"]
            )
            self.progress_status_label.pack(side="left", padx=20, pady=15)

            # Buttons (Black background as per screenshot)
            btn_style = {"width": 100, "height": 32, "font": ("Segoe UI", 12, "bold")}
            
            ctk.CTkButton(footer, text="Close", fg_color="black", hover_color="#333333", border_color=COLORS["border"], border_width=1,
                          command=self._close_progress_window, **btn_style).pack(side="right", padx=10)
                          
            self.pause_btn = ctk.CTkButton(footer, text="Pause", fg_color="black", hover_color="#333333", border_color=COLORS["border"], border_width=1,
                                           text_color="white", command=self._toggle_pause, **btn_style)
            self.pause_btn.pack(side="right", padx=5)
            
            ctk.CTkButton(footer, text="Export", fg_color="black", hover_color="#333333", border_color=COLORS["border"], border_width=1,
                          command=self._export_last_report, **btn_style).pack(side="right", padx=5)

        self._run_on_ui(_do)

    def _add_progress_row_blind(self, row_values, tag="waiting"):
        # row_values = [phone, type, time, status, message]
        # Prepend icon to phone (ID)
        icon = ""
        if tag == "success": icon = "OK "
        elif tag == "failed": icon = "FAIL "
        elif tag == "invalid": icon = "NO WA "
        elif tag == "stopped": icon = "STOP "
        elif tag == "waiting": icon = "... "
        
        new_values = list(row_values)
        while len(new_values) < 5:
            new_values.append("")
        new_values[0] = f"{icon}{new_values[0]}"
        
        def _do():
            try:
                if self.popup_progress_tree and self.popup_progress_tree.winfo_exists():
                    self.popup_progress_tree.insert("", "0", values=new_values, tags=(tag,))
            except Exception as exc:
                logger.debug("Could not add row to progress tree: %s", exc)
        self._run_on_ui(_do)

    def _update_progress_header_blind(self, processed, total, current_phone=None, current_name=None, eta=None, status_text=None):
        def _do():
            try:
                remaining = max(total - processed, 0)
                title_text = getattr(self, "progress_title_text", "متابعة العملية")
                if self.progress_count_label and self.progress_count_label.winfo_exists():
                    self.progress_count_label.configure(text=f"{title_text} ({processed}/{total})")
                if self.progress_bar_small and self.progress_bar_small.winfo_exists():
                    self.progress_bar_small.set(processed / total if total else 0)
                metric_values = {
                    "processed": processed,
                    "sent": self.sent,
                    "failed": self.failed,
                    "invalid": self.invalid,
                    "remaining": remaining,
                    "eta": self._format_progress_eta(eta),
                }
                for key, value in metric_values.items():
                    label = self.progress_metric_labels.get(key)
                    if label and label.winfo_exists():
                        label.configure(text=str(value))
                if self.progress_status_label and self.progress_status_label.winfo_exists():
                    if status_text:
                        text = status_text
                    elif current_phone and current_name:
                        text = f"جاري العمل على: {current_name} - {current_phone}"
                    elif current_phone:
                        text = f"جاري العمل على: {current_phone}"
                    else:
                        text = "جاري العمل..."
                    self.progress_status_label.configure(text=text)
            except Exception as exc:
                logger.debug("Could not update progress header: %s", exc)
        self._run_on_ui(_do)

