"""WhatsApp Sender Pro — Tab builder methods (all tabs)."""
import customtkinter as ctk
from tkinter import filedialog, messagebox, ttk

from gui.theme import COLORS
from utils.logger import logger
from utils.helpers import read_contacts_auto
from gui.components import RichTextFrame, AttachmentManager

from gui.tabs.main_tab import build_main_tab
from gui.tabs.groups_tab import build_groups_tab
from gui.tabs.templates_tab import build_templates_tab
from gui.tabs.settings_tab import build_settings_tab
from gui.tabs.log_tab import build_log_tab
from gui.tabs.campaigns_tab import build_campaigns_tab
from gui.tabs.auto_reply_tab import build_auto_reply_tab
from gui.tabs.received_tab import build_received_tab
from gui.tabs.numbers_filter_tab import build_numbers_filter_tab
from gui.tabs.warmer_tab import build_warmer_tab
from gui.tabs.workflows_tab import build_workflows_tab
from gui.tabs.gmaps_tab import build_gmaps_tab


class TabBuildersMixin:
    """Mixin: Tab builder methods for all application tabs."""

    def _build_tab_main(self):
        """Build the main sending tab: contacts table, message editor, attachments."""
        frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        build_main_tab(self, frame)

    def _build_tab_groups(self):
        """Build the contact groups management tab."""
        frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        build_groups_tab(self, frame)

    def _build_tab_templates(self):
        """Build the message templates management tab."""
        frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        build_templates_tab(self, frame)

    def _build_tab_settings(self):
        """Initialize settings inputs in-memory at startup to avoid runtime campaign crashes."""
        self._ensure_background_settings_exist()

    def _build_tab_log(self):
        """Build the event log/diagnostic tab."""
        frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        build_log_tab(self, frame)

    def _build_tab_campaigns(self):
        """Build the sent campaigns history tab."""
        frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        build_campaigns_tab(self, frame)

    def _build_tab_auto_reply(self):
        """Build the standalone auto-reply rules tab."""
        frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        build_auto_reply_tab(self, frame)

    def _build_tab_received(self):
        """Build the received messages tab."""
        frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        build_received_tab(self, frame)

    def _build_tab_filter(self):
        """Build the numbers filter/validation tab."""
        frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        build_numbers_filter_tab(self, frame)

    def _build_tab_warmer(self):
        """Build the account warmer tab."""
        frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        build_warmer_tab(self, frame)

    def _build_tab_workflows(self):
        """Build the workflows / drip campaigns tab."""
        frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        build_workflows_tab(self, frame)

    def _build_tab_gmaps(self):
        """Build the Google Maps scraper tab."""
        frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        build_gmaps_tab(self, frame)

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

