"""WhatsApp Sender Pro — Modal dialog windows (import, number generator, bulk add)."""
import customtkinter as ctk
from tkinter import filedialog, messagebox, ttk
import os
import datetime

from gui.theme import COLORS
from utils.logger import logger
from gui.dialogs import ImportDialog, NumberGeneratorDialog


class DialogsMixin:
    """Mixin: Modal dialog windows (import, number generator, bulk add)."""

    def _open_import_dialog(self):
        """Open the advanced CSV/Excel import dialog with column mapping."""
        ImportDialog(self)

    def _open_number_generator(self):
        """Open the sequential phone number generator dialog."""
        NumberGeneratorDialog(self)

    def _add_manual_number_dialog(self):
        """Open a dialog to manually add a single phone number."""
        dialog = ctk.CTkToplevel(self)
        dialog.title("إضافة رقم يدوي")
        dialog.geometry("380x280")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()

        x = self.winfo_x() + (self.winfo_width() - 380) // 2
        y = self.winfo_y() + (self.winfo_height() - 280) // 2
        dialog.geometry(f"+{x}+{y}")

        frm = ctk.CTkFrame(dialog, fg_color="transparent")
        frm.pack(fill="both", expand=True, padx=20, pady=20)

        lbl_phone = ctk.CTkLabel(frm, text="رقم الهاتف (مع رمز الدولة):", font=("Segoe UI", 11))
        lbl_phone.pack(anchor="e", pady=(0, 2))
        entry_phone = ctk.CTkEntry(frm, placeholder_text="مثال: 201012345678", justify="center")
        entry_phone.pack(fill="x", pady=(0, 10))

        lbl_name = ctk.CTkLabel(frm, text="الاسم:", font=("Segoe UI", 11))
        lbl_name.pack(anchor="e", pady=(0, 2))
        entry_name = ctk.CTkEntry(frm, placeholder_text="مثال: محمد أحمد", justify="right")
        entry_name.pack(fill="x", pady=(0, 10))

        lbl_var1 = ctk.CTkLabel(frm, text="المتغير 1 (اختياري):", font=("Segoe UI", 11))
        lbl_var1.pack(anchor="e", pady=(0, 2))
        entry_var1 = ctk.CTkEntry(frm, placeholder_text="مثال: قيمة مخصصة", justify="right")
        entry_var1.pack(fill="x", pady=(0, 15))

        def on_add():
            phone = entry_phone.get().strip()
            name = entry_name.get().strip() or "عميل"
            var1 = entry_var1.get().strip()
            if not phone:
                self._show_dialog("warning", "خطأ", "يرجى إدخال رقم الهاتف.")
                return
            
            from utils.helpers import normalize_phone
            cleaned_phone = normalize_phone(phone, self.config.get("default_country_code", "20"))
            if not cleaned_phone:
                self._show_dialog("warning", "خطأ", "رقم الهاتف غير صالح.")
                return
            
            self.progress_tree.insert("", "end", values=(name, cleaned_phone, var1, "⏳ معلق"), tags=("pending",))
            self._update_contacts_count_from_tree()
            dialog.destroy()

        btn_frm = ctk.CTkFrame(frm, fg_color="transparent")
        btn_frm.pack(fill="x")
        
        ctk.CTkButton(
            btn_frm, text="إلغاء", font=("Segoe UI", 11),
            width=80, height=28, fg_color=COLORS["danger"], hover_color=COLORS["danger_hover"],
            command=dialog.destroy
        ).pack(side="left")
        
        ctk.CTkButton(
            btn_frm, text="إضافة", font=("Segoe UI", 11, "bold"),
            width=100, height=28, fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"],
            text_color="#000000",
            command=on_add
        ).pack(side="right")

    def _add_bulk_manual_numbers_dialog(self):
        """Open a dialog to paste and import multiple numbers at once."""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Manual Import | استيراد يدوي")
        dialog.geometry("540x580")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()

        # Center dialog
        x = self.winfo_x() + (self.winfo_width() - 540) // 2
        y = self.winfo_y() + (self.winfo_height() - 580) // 2
        dialog.geometry(f"+{x}+{y}")

        frm = ctk.CTkFrame(dialog, fg_color="transparent")
        frm.pack(fill="both", expand=True, padx=15, pady=15)

        # Header - Enter Contacts
        lbl_enter = ctk.CTkLabel(frm, text="Enter contacts | أدخل جهات الاتصال:", font=("Segoe UI", 12, "bold"))
        lbl_enter.pack(anchor="w", pady=(0, 2))

        # Textbox
        textbox = ctk.CTkTextbox(frm, height=130, font=("Consolas", 11))
        textbox.pack(fill="x", pady=(0, 2))

        # Enable undo
        try:
            textbox._textbox.configure(undo=True)
        except Exception as exc:
            logger.debug("Could not enable undo for bulk manual textbox: %s", exc)

        # Right-click context menu
        import tkinter as tk
        ctx_menu = tk.Menu(dialog, tearoff=0, font=("Segoe UI", 11))
        ctx_menu.add_command(label="تراجع (Undo)", command=lambda: _ctx_undo())
        ctx_menu.add_command(label="إعادة (Redo)", command=lambda: _ctx_redo())
        ctx_menu.add_separator()
        ctx_menu.add_command(label="قص (Cut)", command=lambda: textbox._textbox.event_generate("<<Cut>>"))
        ctx_menu.add_command(label="نسخ (Copy)", command=lambda: textbox._textbox.event_generate("<<Copy>>"))
        ctx_menu.add_command(label="لصق (Paste)", command=lambda: textbox._textbox.event_generate("<<Paste>>"))
        ctx_menu.add_command(label="حذف (Delete)", command=lambda: _ctx_delete())
        ctx_menu.add_separator()
        ctx_menu.add_command(label="تحديد الكل (Select All)", command=lambda: textbox._textbox.tag_add("sel", "1.0", "end"))

        def _ctx_undo():
            try:
                textbox._textbox.edit_undo()
            except Exception as exc:
                logger.debug("Bulk manual undo ignored: %s", exc)
        def _ctx_redo():
            try:
                textbox._textbox.edit_redo()
            except Exception as exc:
                logger.debug("Bulk manual redo ignored: %s", exc)
        def _ctx_delete():
            try:
                textbox._textbox.delete("sel.first", "sel.last")
            except Exception as exc:
                logger.debug("Bulk manual delete ignored: %s", exc)
        def _show_ctx(event):
            try: ctx_menu.tk_popup(event.x_root, event.y_root)
            finally: ctx_menu.grab_release()

        textbox.bind("<Button-3>", _show_ctx)

        # Help Label
        lbl_help = ctk.CTkLabel(
            frm, 
            text="Line per number. You can name by entering name, comma, then mobile (name,number)\nاكتب اسماً متبوعاً بفاصلة ثم الرقم في كل سطر (مثال: محمد أحمد,201012345678)",
            font=("Segoe UI", 9), 
            text_color=COLORS.get("text_muted", "#64748B"),
            justify="left"
        )
        lbl_help.pack(anchor="w", pady=(0, 10))

        # Validated label
        lbl_val = ctk.CTkLabel(frm, text="Validated contacts | جهات الاتصال التي تم التحقق منها:", font=("Segoe UI", 12, "bold"))
        lbl_val.pack(anchor="w", pady=(0, 2))

        # Treeview frame
        tree_frame = ctk.CTkFrame(frm, fg_color="transparent")
        tree_frame.pack(fill="both", expand=True, pady=(0, 5))

        # Validate Treeview
        validated_tree = ttk.Treeview(tree_frame, columns=("name", "phone"), show="headings", height=8)
        validated_tree.heading("name", text="Name | الاسم")
        validated_tree.heading("phone", text="Number | الرقم")
        validated_tree.column("name", width=220, anchor="w")
        validated_tree.column("phone", width=220, anchor="center")

        tree_scroll = ctk.CTkScrollbar(tree_frame, command=validated_tree.yview)
        validated_tree.configure(yscrollcommand=tree_scroll.set)
        
        tree_scroll.pack(side="right", fill="y")
        validated_tree.pack(side="left", fill="both", expand=True)

        # Stats labels
        stats_frame = ctk.CTkFrame(frm, fg_color="transparent")
        stats_frame.pack(fill="x", pady=(0, 10))

        lbl_total = ctk.CTkLabel(stats_frame, text="Total: 0", font=("Segoe UI", 11, "bold"))
        lbl_total.pack(side="left", padx=(0, 20))

        lbl_dup = ctk.CTkLabel(stats_frame, text="Duplication: 0", font=("Segoe UI", 11, "bold"), text_color=COLORS.get("danger", "#EF4444"))
        lbl_dup.pack(side="left")

        # Bottom Frame
        bottom_frame = ctk.CTkFrame(frm, fg_color="transparent")
        bottom_frame.pack(fill="x", pady=(10, 0))

        chk_remove_dup = ctk.CTkCheckBox(bottom_frame, text="Remove duplication | إزالة التكرار", font=("Segoe UI", 11))
        chk_remove_dup.pack(side="left", pady=5)
        chk_remove_dup.select()

        # Dialog State Variables
        dialog.parsed_contacts = []

        def _on_bulk_text_changed(event=None):
            raw_text = textbox.get("1.0", "end-1c")
            lines = raw_text.split("\n")
            
            parsed_list = []
            seen_numbers = set()
            dups_count = 0
            
            from utils.helpers import normalize_phone
            default_cc = self.config.get("default_country_code", "20")
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Parse name, number
                if "," in line:
                    parts = line.split(",", 1)
                    name = parts[0].strip() or "عميل"
                    phone_raw = parts[1].strip()
                else:
                    name = "عميل"
                    phone_raw = line.strip()
                
                cleaned_phone = normalize_phone(phone_raw, default_cc)
                if cleaned_phone:
                    if cleaned_phone in seen_numbers:
                        dups_count += 1
                    seen_numbers.add(cleaned_phone)
                    parsed_list.append((name, cleaned_phone))
            
            # Update treeview
            for item in validated_tree.get_children():
                validated_tree.delete(item)
                
            for name, phone in parsed_list:
                validated_tree.insert("", "end", values=(name, phone))
                
            lbl_total.configure(text=f"Total: {len(parsed_list)}")
            lbl_dup.configure(text=f"Duplication: {dups_count}")
            
            dialog.parsed_contacts = parsed_list

        # Bind key release to real-time validation
        textbox.bind("<KeyRelease>", _on_bulk_text_changed)

        def on_import():
            if not dialog.parsed_contacts:
                self._show_dialog("warning", "تنبيه", "لا توجد جهات اتصال صالحة للاستيراد.")
                return
            
            remove_dup = chk_remove_dup.get()
            imported_count = 0
            seen = set()
            
            # Fetch existing numbers to prevent duplicates if necessary, or just within this batch
            for name, phone in dialog.parsed_contacts:
                if remove_dup:
                    if phone in seen:
                        continue
                    seen.add(phone)
                
                self.progress_tree.insert("", "end", values=(name, phone, "", "⏳ معلق"), tags=("pending",))
                imported_count += 1
                
            self._update_contacts_count_from_tree()
            self.log(f"✍️ تم استيراد {imported_count} جهة اتصال يدوياً.")
            dialog.destroy()

        btn_import = ctk.CTkButton(
            bottom_frame, text="Import | استيراد", font=("Segoe UI", 11, "bold"),
            width=100, height=30, fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"],
            text_color="#000000",
            command=on_import
        )
        btn_import.pack(side="right", padx=(10, 0))

        btn_cancel = ctk.CTkButton(
            bottom_frame, text="Cancel | إلغاء", font=("Segoe UI", 11),
            width=90, height=30, fg_color=COLORS["danger"], hover_color=COLORS["danger_hover"],
            command=dialog.destroy
        )
        btn_cancel.pack(side="right")

