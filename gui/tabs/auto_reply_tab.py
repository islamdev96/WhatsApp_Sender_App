"""WhatsApp Sender Pro — Auto Reply Tab builder module.

Standalone tab for managing auto-reply chatbot rules.
"""
import customtkinter as ctk
from tkinter import ttk, messagebox
import json
import os
import threading
import time
import datetime

from gui.theme import COLORS
from utils.logger import logger


def build_auto_reply_tab(self, frame: ctk.CTkFrame) -> None:
    """Build the Auto Reply tab with rules table, add/delete/toggle, and settings."""
    self.tab_frames["auto_reply"] = frame

    is_ar = self.current_lang.get() == "ar"
    anchor_val = "e" if is_ar else "w"
    side_lbl = "right" if is_ar else "left"
    side_opp = "left" if is_ar else "right"

    # ── Header ──
    header = ctk.CTkLabel(frame, text=self.tr("auto_reply_header"),
                          font=ctk.CTkFont(size=20, weight="bold"))
    header.pack(anchor=anchor_val, padx=25, pady=(20, 5))

    desc = ctk.CTkLabel(frame, text=self.tr("auto_reply_desc"),
                        font=ctk.CTkFont(size=12), text_color=COLORS["text_muted"])
    desc.pack(anchor=anchor_val, padx=25, pady=(0, 10))

    # ── Enable/Disable Toggle ──
    toggle_frame = ctk.CTkFrame(frame, fg_color="transparent")
    toggle_frame.pack(fill="x", padx=25, pady=(0, 5))

    self.auto_reply_enabled_var = ctk.BooleanVar(value=self.config.get("auto_reply_enabled", True))
    ctk.CTkSwitch(
        toggle_frame, text=self.tr("auto_reply_enable"),
        variable=self.auto_reply_enabled_var,
        font=ctk.CTkFont(size=13, weight="bold"),
        onvalue=True, offvalue=False,
        progress_color=COLORS["primary"],
        command=lambda: self.config.set("auto_reply_enabled", self.auto_reply_enabled_var.get())
    ).pack(side=side_lbl, padx=5)

    # ── Rules Table ──
    table_frame = ctk.CTkFrame(frame, corner_radius=12)
    table_frame.pack(fill="both", expand=True, padx=20, pady=5)

    columns = ("rule_name", "keywords", "reply", "status")
    self.auto_reply_tree = ttk.Treeview(
        table_frame, columns=columns, show="headings",
        selectmode="browse", height=12
    )

    self.auto_reply_tree.heading("rule_name", text=self.tr("lbl_rules_name"))
    self.auto_reply_tree.heading("keywords", text=self.tr("lbl_keywords"))
    self.auto_reply_tree.heading("reply", text=self.tr("auto_reply_col_reply"))
    self.auto_reply_tree.heading("status", text=self.tr("lbl_status"))

    self.auto_reply_tree.column("rule_name", width=150, anchor="center")
    self.auto_reply_tree.column("keywords", width=200, anchor="center")
    self.auto_reply_tree.column("reply", width=300, anchor="w")
    self.auto_reply_tree.column("status", width=100, anchor="center")

    scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.auto_reply_tree.yview)
    self.auto_reply_tree.configure(yscrollcommand=scrollbar.set)

    self.auto_reply_tree.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=10)
    scrollbar.pack(side="right", fill="y", padx=(0, 10), pady=10)

    self.auto_reply_tree.tag_configure("enabled", foreground="#2E7D32")
    self.auto_reply_tree.tag_configure("disabled", foreground="#C62828")

    # Double-click to toggle rule
    self.auto_reply_tree.bind("<Double-1>", lambda e: _toggle_rule())

    # ── Action Buttons ──
    btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
    btn_frame.pack(fill="x", padx=20, pady=(5, 15))

    ctk.CTkButton(
        btn_frame, text=self.tr("btn_add_rule"),
        font=ctk.CTkFont(size=12, weight="bold"),
        width=140, height=38, corner_radius=8,
        fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"],
        text_color="#FFFFFF",
        command=lambda: _open_add_rule_dialog()
    ).pack(side=side_lbl, padx=5)

    ctk.CTkButton(
        btn_frame, text=self.tr("auto_reply_btn_edit"),
        font=ctk.CTkFont(size=12),
        width=120, height=38, corner_radius=8,
        fg_color=COLORS["secondary"], hover_color=COLORS["secondary_hover"],
        text_color=COLORS["secondary_text"],
        command=lambda: _edit_rule()
    ).pack(side=side_lbl, padx=5)

    ctk.CTkButton(
        btn_frame, text=self.tr("btn_delete_rule"),
        font=ctk.CTkFont(size=12),
        width=120, height=38, corner_radius=8,
        fg_color=COLORS["danger"], hover_color=COLORS["danger_hover"],
        text_color="#FFFFFF",
        command=lambda: _delete_rule()
    ).pack(side=side_opp, padx=5)

    # ═══════════════════════════════════════════════════════════════
    # Internal Functions
    # ═══════════════════════════════════════════════════════════════

    def _load_rules():
        path = os.path.join("data", "auto_reply_rules.json")
        if not os.path.exists(path):
            defaults = [
                {"rule_name": "ترحيب", "keywords": "مرحبا, سلام, هلا",
                 "reply": "أهلاً بك! كيف يمكنني مساعدتك اليوم؟", "enabled": True},
                {"rule_name": "الأسعار", "keywords": "سعر, اسعار, بكم",
                 "reply": "أسعار باقاتنا تبدأ من 20 دولار شهرياً.", "enabled": True}
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

    def _save_rules(rules):
        path = os.path.join("data", "auto_reply_rules.json")
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(rules, f, ensure_ascii=False, indent=4)
        except Exception as exc:
            logger.debug("Could not save auto reply rules: %s", exc)

    def _refresh_table():
        for item in self.auto_reply_tree.get_children():
            self.auto_reply_tree.delete(item)
        rules = _load_rules()
        for r in rules:
            enabled = r.get("enabled", True)
            status_txt = self.tr("status_connected") if enabled else self.tr("status_disconnected")
            tag = "enabled" if enabled else "disabled"
            self.auto_reply_tree.insert("", "end", values=(
                r.get("rule_name", ""),
                r.get("keywords", ""),
                r.get("reply", "")[:80],
                status_txt
            ), tags=(tag,))

    def _toggle_rule():
        selected = self.auto_reply_tree.selection()
        if not selected:
            return
        rule_name = self.auto_reply_tree.item(selected[0], "values")[0]
        rules = _load_rules()
        for r in rules:
            if r.get("rule_name") == rule_name:
                r["enabled"] = not r.get("enabled", True)
                break
        _save_rules(rules)
        _refresh_table()

    def _open_add_rule_dialog():
        win = ctk.CTkToplevel(self)
        win.title(self.tr("btn_add_rule"))
        win.geometry("450x380")
        win.transient(self)
        win.grab_set()

        ctk.CTkLabel(win, text=self.tr("lbl_rules_name"),
                     font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=20, pady=(15, 3))
        name_entry = ctk.CTkEntry(win, height=36, corner_radius=8)
        name_entry.pack(fill="x", padx=20, pady=(0, 8))

        ctk.CTkLabel(win, text=self.tr("lbl_keywords"),
                     font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=20, pady=(5, 3))
        keywords_entry = ctk.CTkEntry(win, height=36, corner_radius=8,
                                       placeholder_text="keyword1, keyword2, ...")
        keywords_entry.pack(fill="x", padx=20, pady=(0, 8))

        ctk.CTkLabel(win, text=self.tr("auto_reply_col_reply"),
                     font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=20, pady=(5, 3))
        reply_box = ctk.CTkTextbox(win, height=100, corner_radius=8)
        reply_box.pack(fill="x", padx=20, pady=(0, 10))

        def _save():
            name = name_entry.get().strip()
            keywords = keywords_entry.get().strip()
            reply = reply_box.get("1.0", "end").strip()
            if not name or not keywords or not reply:
                messagebox.showwarning(self.tr("msg_alert"), self.tr("auto_reply_fill_all"))
                return
            rules = _load_rules()
            rules.append({"rule_name": name, "keywords": keywords, "reply": reply, "enabled": True})
            _save_rules(rules)
            _refresh_table()
            win.destroy()

        ctk.CTkButton(win, text=self.tr("dialog_add_contact_save"),
                      font=ctk.CTkFont(size=13, weight="bold"),
                      height=38, corner_radius=8,
                      fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"],
                      command=_save).pack(fill="x", padx=20, pady=10)

    def _edit_rule():
        selected = self.auto_reply_tree.selection()
        if not selected:
            messagebox.showinfo(self.tr("msg_alert"), self.tr("auto_reply_select_rule"))
            return
        vals = self.auto_reply_tree.item(selected[0], "values")
        rule_name = vals[0]
        rules = _load_rules()
        target_rule = None
        for r in rules:
            if r.get("rule_name") == rule_name:
                target_rule = r
                break
        if not target_rule:
            return

        win = ctk.CTkToplevel(self)
        win.title(self.tr("auto_reply_btn_edit"))
        win.geometry("450x380")
        win.transient(self)
        win.grab_set()

        ctk.CTkLabel(win, text=self.tr("lbl_rules_name"),
                     font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=20, pady=(15, 3))
        name_entry = ctk.CTkEntry(win, height=36, corner_radius=8)
        name_entry.pack(fill="x", padx=20, pady=(0, 8))
        name_entry.insert(0, target_rule.get("rule_name", ""))

        ctk.CTkLabel(win, text=self.tr("lbl_keywords"),
                     font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=20, pady=(5, 3))
        keywords_entry = ctk.CTkEntry(win, height=36, corner_radius=8)
        keywords_entry.pack(fill="x", padx=20, pady=(0, 8))
        keywords_entry.insert(0, target_rule.get("keywords", ""))

        ctk.CTkLabel(win, text=self.tr("auto_reply_col_reply"),
                     font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=20, pady=(5, 3))
        reply_box = ctk.CTkTextbox(win, height=100, corner_radius=8)
        reply_box.pack(fill="x", padx=20, pady=(0, 10))
        reply_box.insert("1.0", target_rule.get("reply", ""))

        def _update():
            new_name = name_entry.get().strip()
            new_keywords = keywords_entry.get().strip()
            new_reply = reply_box.get("1.0", "end").strip()
            if not new_name or not new_keywords or not new_reply:
                messagebox.showwarning(self.tr("msg_alert"), self.tr("auto_reply_fill_all"))
                return
            target_rule["rule_name"] = new_name
            target_rule["keywords"] = new_keywords
            target_rule["reply"] = new_reply
            _save_rules(rules)
            _refresh_table()
            win.destroy()

        ctk.CTkButton(win, text=self.tr("dialog_add_contact_save"),
                      font=ctk.CTkFont(size=13, weight="bold"),
                      height=38, corner_radius=8,
                      fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"],
                      command=_update).pack(fill="x", padx=20, pady=10)

    def _delete_rule():
        selected = self.auto_reply_tree.selection()
        if not selected:
            messagebox.showinfo(self.tr("msg_alert"), self.tr("auto_reply_select_rule"))
            return
        rule_name = self.auto_reply_tree.item(selected[0], "values")[0]
        if messagebox.askyesno(self.tr("msg_confirm"),
                               self.tr("auto_reply_confirm_delete").format(name=rule_name)):
            rules = _load_rules()
            rules = [r for r in rules if r.get("rule_name") != rule_name]
            _save_rules(rules)
            _refresh_table()

    # Initial load
    _refresh_table()

    def _run_auto_reply_loop():
        """Periodically check unread chats and reply automatically based on rules."""
        if not hasattr(self, "auto_reply_enabled_var") or not self.auto_reply_enabled_var.get():
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

                rules = _load_rules()
                enabled_rules = [r for r in rules if r.get("enabled", True)]
                if not enabled_rules:
                    return

                for chat in unread_chats:
                    if self.is_running:
                        break
                    if not self.auto_reply_enabled_var.get():
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
                            
                            # Add to received messages tab list if function exists
                            if hasattr(self, "_add_received_message_func"):
                                self._add_received_message_func(sender_name, last_msg)
            except Exception as exc:
                logger.debug("Error in auto reply loop worker: %s", exc)

        threading.Thread(target=worker, daemon=True).start()
        self.after(5000, _run_auto_reply_loop)

    # Start loop
    self.after(3000, _run_auto_reply_loop)
