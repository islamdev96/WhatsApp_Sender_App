"""WhatsApp Sender Pro — Workflows Tab builder module.

Provides a drip campaign / workflow builder for creating
multi-step automated messaging sequences.
"""
import customtkinter as ctk
from tkinter import ttk, messagebox
import json
import os
import datetime

from gui.theme import COLORS
from utils.logger import logger


def build_workflows_tab(self, frame: ctk.CTkFrame) -> None:
    """Build the Workflows tab with drip sequence builder and saved workflows list."""
    self.tab_frames["workflows"] = frame

    is_ar = self.current_lang.get() == "ar"
    anchor_val = "e" if is_ar else "w"
    side_lbl = "right" if is_ar else "left"
    side_opp = "left" if is_ar else "right"

    # ── Header ──
    header = ctk.CTkLabel(frame, text=self.tr("workflows_header"),
                          font=ctk.CTkFont(size=20, weight="bold"))
    header.pack(anchor=anchor_val, padx=25, pady=(20, 5))

    desc = ctk.CTkLabel(frame, text=self.tr("workflows_desc"),
                        font=ctk.CTkFont(size=12), text_color=COLORS["text_muted"])
    desc.pack(anchor=anchor_val, padx=25, pady=(0, 10))

    # ── Main body: 2 columns ──
    body = ctk.CTkFrame(frame, fg_color="transparent")
    body.pack(fill="both", expand=True, padx=20, pady=5)
    body.grid_columnconfigure(0, weight=2)
    body.grid_columnconfigure(1, weight=3)
    body.grid_rowconfigure(0, weight=1)

    # ── LEFT: Saved Workflows List ──
    left_frame = ctk.CTkFrame(body, corner_radius=12)
    left_frame.grid(row=0, column=0, padx=(0, 5), pady=5, sticky="nsew")

    ctk.CTkLabel(left_frame, text=self.tr("workflows_saved"),
                 font=ctk.CTkFont(size=14, weight="bold")).pack(anchor=anchor_val, padx=15, pady=(12, 5))

    self.workflows_listbox = ctk.CTkScrollableFrame(left_frame, corner_radius=8)
    self.workflows_listbox.pack(fill="both", expand=True, padx=10, pady=5)

    btn_row_wf = ctk.CTkFrame(left_frame, fg_color="transparent")
    btn_row_wf.pack(fill="x", padx=10, pady=(0, 10))

    ctk.CTkButton(btn_row_wf, text=self.tr("workflows_btn_new"),
                  width=100, height=32, corner_radius=8,
                  fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"],
                  text_color="#FFFFFF",
                  command=lambda: _new_workflow()).pack(side=side_lbl, padx=3)
    ctk.CTkButton(btn_row_wf, text=self.tr("groups_btn_delete"),
                  width=80, height=32, corner_radius=8,
                  fg_color=COLORS["danger"], hover_color=COLORS["danger_hover"],
                  text_color="#FFFFFF",
                  command=lambda: _delete_workflow()).pack(side=side_lbl, padx=3)

    # ── RIGHT: Workflow Editor ──
    right_frame = ctk.CTkFrame(body, corner_radius=12)
    right_frame.grid(row=0, column=1, padx=(5, 0), pady=5, sticky="nsew")

    ctk.CTkLabel(right_frame, text=self.tr("workflows_editor"),
                 font=ctk.CTkFont(size=14, weight="bold")).pack(anchor=anchor_val, padx=15, pady=(12, 5))

    # Workflow name
    name_row = ctk.CTkFrame(right_frame, fg_color="transparent")
    name_row.pack(fill="x", padx=15, pady=3)
    ctk.CTkLabel(name_row, text=self.tr("workflows_name"),
                 font=ctk.CTkFont(size=12)).pack(side=side_lbl, padx=5)
    self.workflow_name_entry = ctk.CTkEntry(name_row, height=32, corner_radius=8,
                                             placeholder_text=self.tr("workflows_name_placeholder"))
    self.workflow_name_entry.pack(side=side_lbl, fill="x", expand=True, padx=5)

    # Steps table
    ctk.CTkLabel(right_frame, text=self.tr("workflows_steps"),
                 font=ctk.CTkFont(size=13, weight="bold")).pack(anchor=anchor_val, padx=15, pady=(10, 3))

    steps_table_frame = ctk.CTkFrame(right_frame, fg_color="transparent")
    steps_table_frame.pack(fill="both", expand=True, padx=15, pady=5)

    columns = ("step", "type", "content", "delay")
    self.workflow_steps_tree = ttk.Treeview(
        steps_table_frame, columns=columns, show="headings",
        selectmode="browse", height=6
    )
    self.workflow_steps_tree.heading("step", text="#")
    self.workflow_steps_tree.heading("type", text=self.tr("workflows_col_type"))
    self.workflow_steps_tree.heading("content", text=self.tr("workflows_col_content"))
    self.workflow_steps_tree.heading("delay", text=self.tr("workflows_col_delay"))

    self.workflow_steps_tree.column("step", width=40, anchor="center")
    self.workflow_steps_tree.column("type", width=100, anchor="center")
    self.workflow_steps_tree.column("content", width=250, anchor="w")
    self.workflow_steps_tree.column("delay", width=100, anchor="center")

    self.workflow_steps_tree.pack(fill="both", expand=True)

    # Step action buttons
    step_btn_row = ctk.CTkFrame(right_frame, fg_color="transparent")
    step_btn_row.pack(fill="x", padx=15, pady=5)

    ctk.CTkButton(step_btn_row, text=self.tr("workflows_btn_add_step"),
                  width=120, height=30, corner_radius=8,
                  fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"],
                  text_color="#FFFFFF",
                  command=lambda: _add_step()).pack(side=side_lbl, padx=3)
    ctk.CTkButton(step_btn_row, text=self.tr("workflows_btn_del_step"),
                  width=100, height=30, corner_radius=8,
                  fg_color=COLORS["danger"], hover_color=COLORS["danger_hover"],
                  text_color="#FFFFFF",
                  command=lambda: _delete_step()).pack(side=side_lbl, padx=3)
    ctk.CTkButton(step_btn_row, text=self.tr("workflows_btn_save"),
                  width=120, height=30, corner_radius=8,
                  fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
                  text_color="#FFFFFF",
                  command=lambda: _save_workflow()).pack(side=side_opp, padx=3)

    # ═══════════════════════════════════════════════════════════════
    # Internal Functions
    # ═══════════════════════════════════════════════════════════════

    def _workflows_path():
        return os.path.join("data", "workflows.json")

    def _load_workflows():
        path = _workflows_path()
        if not os.path.exists(path):
            return []
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def _save_workflows(workflows):
        os.makedirs("data", exist_ok=True)
        with open(_workflows_path(), "w", encoding="utf-8") as f:
            json.dump(workflows, f, ensure_ascii=False, indent=4)

    def _refresh_workflow_list():
        for w in self.workflows_listbox.winfo_children():
            w.destroy()
        workflows = _load_workflows()
        if not workflows:
            ctk.CTkLabel(self.workflows_listbox, text=self.tr("workflows_no_saved"),
                         font=ctk.CTkFont(size=12), text_color=COLORS["text_muted"]).pack(pady=20)
            return
        for wf in workflows:
            btn = ctk.CTkButton(
                self.workflows_listbox,
                text=f"🧭 {wf.get('name', 'Workflow')} ({len(wf.get('steps', []))} steps)",
                font=ctk.CTkFont(size=12),
                height=36, corner_radius=8,
                fg_color=COLORS["secondary"], hover_color=COLORS["secondary_hover"],
                text_color=COLORS["text_main"],
                anchor="w",
                command=lambda w=wf: _load_workflow(w)
            )
            btn.pack(fill="x", padx=5, pady=2)

    def _load_workflow(wf):
        self.workflow_name_entry.delete(0, "end")
        self.workflow_name_entry.insert(0, wf.get("name", ""))
        for item in self.workflow_steps_tree.get_children():
            self.workflow_steps_tree.delete(item)
        for idx, step in enumerate(wf.get("steps", []), 1):
            self.workflow_steps_tree.insert("", "end", values=(
                idx,
                step.get("type", "Message"),
                step.get("content", "")[:60],
                step.get("delay", "0h")
            ))

    def _new_workflow():
        self.workflow_name_entry.delete(0, "end")
        for item in self.workflow_steps_tree.get_children():
            self.workflow_steps_tree.delete(item)

    def _add_step():
        win = ctk.CTkToplevel(self)
        win.title(self.tr("workflows_btn_add_step"))
        win.geometry("420x320")
        win.transient(self)
        win.grab_set()

        ctk.CTkLabel(win, text=self.tr("workflows_col_type"),
                     font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=20, pady=(15, 3))
        type_var = ctk.StringVar(value="Message")
        ctk.CTkOptionMenu(win, values=["Message", "Image", "Document", "Wait"],
                          variable=type_var, width=200).pack(fill="x", padx=20, pady=(0, 8))

        ctk.CTkLabel(win, text=self.tr("workflows_col_content"),
                     font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=20, pady=(5, 3))
        content_box = ctk.CTkTextbox(win, height=80, corner_radius=8)
        content_box.pack(fill="x", padx=20, pady=(0, 8))

        ctk.CTkLabel(win, text=self.tr("workflows_col_delay"),
                     font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=20, pady=(5, 3))
        delay_row = ctk.CTkFrame(win, fg_color="transparent")
        delay_row.pack(fill="x", padx=20, pady=(0, 10))
        delay_entry = ctk.CTkEntry(delay_row, width=80, height=30, justify="center")
        delay_entry.pack(side="left", padx=5)
        delay_entry.insert(0, "1")
        delay_unit = ctk.CTkOptionMenu(delay_row, values=["Minutes", "Hours", "Days"], width=100)
        delay_unit.pack(side="left", padx=5)

        def _save_step():
            step_count = len(self.workflow_steps_tree.get_children()) + 1
            content = content_box.get("1.0", "end").strip()
            delay_text = f"{delay_entry.get()}{delay_unit.get()[0].lower()}"
            self.workflow_steps_tree.insert("", "end", values=(
                step_count, type_var.get(), content[:60], delay_text
            ))
            win.destroy()

        ctk.CTkButton(win, text=self.tr("dialog_add_contact_save"),
                      height=36, corner_radius=8,
                      fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"],
                      command=_save_step).pack(fill="x", padx=20, pady=8)

    def _delete_step():
        selected = self.workflow_steps_tree.selection()
        if selected:
            self.workflow_steps_tree.delete(selected[0])

    def _save_workflow():
        name = self.workflow_name_entry.get().strip()
        if not name:
            messagebox.showwarning(self.tr("msg_alert"), self.tr("workflows_enter_name"))
            return
        steps = []
        for item in self.workflow_steps_tree.get_children():
            vals = self.workflow_steps_tree.item(item, "values")
            steps.append({
                "type": vals[1],
                "content": vals[2],
                "delay": vals[3]
            })
        if not steps:
            messagebox.showwarning(self.tr("msg_alert"), self.tr("workflows_add_steps"))
            return

        workflows = _load_workflows()
        # Update existing or add new
        existing = [w for w in workflows if w.get("name") == name]
        if existing:
            existing[0]["steps"] = steps
            existing[0]["updated"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        else:
            workflows.append({
                "name": name,
                "steps": steps,
                "created": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                "updated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            })
        _save_workflows(workflows)
        _refresh_workflow_list()
        messagebox.showinfo(self.tr("msg_done"), self.tr("workflows_saved_msg").format(name=name))

    def _delete_workflow():
        name = self.workflow_name_entry.get().strip()
        if not name:
            messagebox.showinfo(self.tr("msg_alert"), self.tr("workflows_select_first"))
            return
        if messagebox.askyesno(self.tr("msg_confirm"),
                               self.tr("workflows_confirm_delete").format(name=name)):
            workflows = _load_workflows()
            workflows = [w for w in workflows if w.get("name") != name]
            _save_workflows(workflows)
            _new_workflow()
            _refresh_workflow_list()

    # Initial load
    _refresh_workflow_list()
