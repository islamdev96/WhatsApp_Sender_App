"""WhatsApp Sender Pro — Contact loading, filtering, template application, and spintax."""
from tkinter import filedialog, messagebox
import re
import random
import os

from utils.helpers import read_contacts_auto


class ContactsMixin:
    """Mixin: Contact loading, filtering, template application, and spintax."""

    def _browse_contacts(self):
        """Open the premium 'Import From File' dialog window."""
        self._open_import_dialog()

    def _parse_imported_file(self, path, use_header=True, custom_delim=False, delim_char=","):
        """Parses the selected file and returns (headers, rows)."""
        import csv
        import os
        from utils.logger import logger
        
        headers = []
        rows = []
        
        ext = os.path.splitext(path)[1].lower()
        if ext in ('.xlsx', '.xls'):
            try:
                import openpyxl
                wb = openpyxl.load_workbook(path, data_only=True, read_only=True)
                ws = wb.active
                
                all_rows = []
                for r in ws.iter_rows(values_only=True):
                    all_rows.append([str(val).strip() if val is not None else "" for val in r])
                
                wb.close()
                
                if not all_rows:
                    return [], []
                    
                if use_header:
                    headers = all_rows[0]
                    rows = all_rows[1:]
                else:
                    headers = [f"Column {i+1}" for i in range(len(all_rows[0]))]
                    rows = all_rows
            except Exception as e:
                logger.error(f"Error parsing excel preview: {e}")
                return [], []
                
        elif ext == '.txt':
            try:
                content = ""
                for encoding in ('utf-8', 'utf-8-sig', 'cp1256', 'latin-1'):
                    try:
                        with open(path, 'r', encoding=encoding) as f:
                            content = f.read()
                        break
                    except:
                        continue
                if not content:
                    return [], []
                    
                lines = [l.strip() for l in content.splitlines() if l.strip()]
                delim = delim_char if custom_delim else None
                
                parsed_rows = []
                max_cols = 1
                for line in lines:
                    if delim:
                        parts = [p.strip() for p in line.split(delim)]
                    else:
                        parts = [p.strip() for p in re.split(r'[\t,;]', line)]
                    parsed_rows.append(parts)
                    max_cols = max(max_cols, len(parts))
                    
                for r in parsed_rows:
                    if len(r) < max_cols:
                        r.extend([""] * (max_cols - len(r)))
                        
                if use_header and len(parsed_rows) > 0:
                    headers = parsed_rows[0]
                    rows = parsed_rows[1:]
                else:
                    headers = [f"Column {i+1}" for i in range(max_cols)]
                    rows = parsed_rows
            except Exception as e:
                logger.error(f"Error parsing TXT preview: {e}")
                return [], []
        else: # CSV
            try:
                content = ""
                for encoding in ('utf-8', 'utf-8-sig', 'cp1256', 'latin-1'):
                    try:
                        with open(path, 'r', encoding=encoding) as f:
                            content = f.read()
                        break
                    except:
                        continue
                if not content:
                    return [], []
                    
                delim = delim_char if custom_delim else None
                if not delim:
                    if ";" in content and "," not in content:
                        delim = ";"
                    elif "\t" in content:
                        delim = "\t"
                    else:
                        delim = ","
                        
                lines = content.splitlines()
                reader = csv.reader(lines, delimiter=delim)
                parsed_rows = []
                max_cols = 1
                for r in reader:
                    if not r:
                        continue
                    parsed_rows.append([val.strip() for val in r])
                    max_cols = max(max_cols, len(r))
                    
                for r in parsed_rows:
                    if len(r) < max_cols:
                        r.extend([""] * (max_cols - len(r)))
                        
                if use_header and len(parsed_rows) > 0:
                    headers = parsed_rows[0]
                    rows = parsed_rows[1:]
                else:
                    headers = [f"Column {i+1}" for i in range(max_cols)]
                    rows = parsed_rows
            except Exception as e:
                logger.error(f"Error parsing CSV preview: {e}")
                return [], []
                
        return headers, rows

    def _open_import_dialog(self):
        """Open a beautiful, premium, custom 'Import From File' popup dialog matching the target screenshots perfectly."""
        import tkinter as tk
        from tkinter import ttk, messagebox
        import customtkinter as ctk
        from gui.theme import COLORS
        
        dialog = ctk.CTkToplevel(self)
        dialog.title(self.tr("import_dialog_title") if self.current_lang.get() != "ar" else "استيراد جهات الاتصال من ملف")
        dialog.geometry("900x680")
        dialog.resizable(True, True)
        dialog.transient(self)

        is_ar = self.current_lang.get() == "ar"
        anchor_val = "e" if is_ar else "w"
        side_lbl = "right" if is_ar else "left"
        side_opposite = "left" if is_ar else "right"

        # Center on parent
        dialog.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() - 900) // 2
        y = self.winfo_y() + (self.winfo_height() - 680) // 2
        dialog.geometry(f"+{x}+{y}")
        dialog.update()
        dialog.grab_set()

        def refresh_preview(headers, rows):
            # Clear old columns and entries
            preview_tree.delete(*preview_tree.get_children())
            preview_tree["columns"] = headers
            
            # Setup columns and headings
            for h in headers:
                preview_tree.heading(h, text=h, anchor="w")
                preview_tree.column(h, width=120, anchor="w")
                
            # Populate rows (limit to 100 rows for preview performance)
            for r in rows[:100]:
                preview_tree.insert("", "end", values=r)

        def populate_dropdowns(headers):
            # Populates the 7 Comboboxes with file headers
            combo_choices = ["None"] + headers
            
            combo_name.configure(values=combo_choices)
            combo_number.configure(values=combo_choices)
            combo_var1.configure(values=combo_choices)
            combo_var2.configure(values=combo_choices)
            combo_var3.configure(values=combo_choices)
            combo_var4.configure(values=combo_choices)
            combo_var5.configure(values=combo_choices)
            
            # Reset values to None first
            combo_name.set("None")
            combo_number.set("None")
            combo_var1.set("None")
            combo_var2.set("None")
            combo_var3.set("None")
            combo_var4.set("None")
            combo_var5.set("None")
            
            # Smart auto-mapping
            for h in headers:
                h_lower = h.lower().strip()
                if h_lower in ("name", "given name", "اسم", "الاسم", "username", "customer"):
                    combo_name.set(h)
                elif h_lower in ("phone", "mobile", "number", "رقم", "هاتف", "جوال", "phone 1 - value"):
                    combo_number.set(h)
                elif h_lower in ("var1", "v1", "variable1"):
                    combo_var1.set(h)
                elif h_lower in ("var2", "v2", "variable2"):
                    combo_var2.set(h)
                elif h_lower in ("var3", "v3", "variable3"):
                    combo_var3.set(h)
                elif h_lower in ("var4", "v4", "variable4"):
                    combo_var4.set(h)
                elif h_lower in ("var5", "v5", "variable5"):
                    combo_var5.set(h)
                    
            # Fallback auto-mapping
            if combo_name.get() == "None" and len(headers) >= 1:
                combo_name.set(headers[0])
            if combo_number.get() == "None" and len(headers) >= 2:
                combo_number.set(headers[1])
            elif combo_number.get() == "None" and len(headers) == 1:
                combo_number.set(headers[0])

        def on_browse():
            path = filedialog.askopenfilename(filetypes=[("Contacts", "*.csv;*.xlsx;*.xls;*.txt")])
            if path:
                import_path_entry.delete(0, "end")
                import_path_entry.insert(0, path)
                
                headers, rows = self._parse_imported_file(
                    path,
                    use_header=use_header_var.get(),
                    custom_delim=custom_delimiter_var.get(),
                    delim_char=delimiter_entry.get()
                )
                
                if headers:
                    populate_dropdowns(headers)
                    refresh_preview(headers, rows)
                else:
                    messagebox.showerror("Error" if not is_ar else "خطأ", "Could not parse columns from the selected file." if not is_ar else "تعذر قراءة الأعمدة والبيانات من الملف المختار.")

        def on_settings_changed(*args):
            path = import_path_entry.get().strip()
            if path and os.path.exists(path):
                headers, rows = self._parse_imported_file(
                    path,
                    use_header=use_header_var.get(),
                    custom_delim=custom_delimiter_var.get(),
                    delim_char=delimiter_entry.get()
                )
                if headers:
                    populate_dropdowns(headers)
                    refresh_preview(headers, rows)

        def on_import():
            path = import_path_entry.get().strip()
            if not path or not os.path.exists(path):
                messagebox.showwarning("تنبيه", "يرجى اختيار ملف صالح أولاً.")
                return
                
            headers, rows = self._parse_imported_file(
                path,
                use_header=use_header_var.get(),
                custom_delim=custom_delimiter_var.get(),
                delim_char=delimiter_entry.get()
            )
            
            if not headers:
                messagebox.showerror("خطأ", "تعذر تحليل الملف المختار.")
                return
                
            name_col = combo_name.get()
            num_col = combo_number.get()
            v1_col = combo_var1.get()
            v2_col = combo_var2.get()
            v3_col = combo_var3.get()
            v4_col = combo_var4.get()
            v5_col = combo_var5.get()
            
            if num_col == "None":
                messagebox.showwarning("تحذير", "يرجى اختيار عمود الهاتف (Number field) لإتمام عملية الاستيراد.")
                return
                
            try:
                name_idx = headers.index(name_col) if name_col != "None" else None
                num_idx = headers.index(num_col)
                v1_idx = headers.index(v1_col) if v1_col != "None" else None
                v2_idx = headers.index(v2_col) if v2_col != "None" else None
                v3_idx = headers.index(v3_col) if v3_col != "None" else None
                v4_idx = headers.index(v4_col) if v4_col != "None" else None
                v5_idx = headers.index(v5_col) if v5_col != "None" else None
            except ValueError:
                messagebox.showerror("خطأ", "حدث خطأ أثناء تحديد الأعمدة المحددة.")
                return
                
            contacts = []
            seen = set()
            default_cc = self.config.get("default_country_code", "20")
            
            for r in rows:
                if len(r) <= num_idx:
                    continue
                phone_raw = r[num_idx]
                name_raw = r[name_idx] if name_idx is not None and name_idx < len(r) else "عميل"
                
                from utils.helpers.phone import _normalize_phone
                phone = _normalize_phone(phone_raw, default_cc)
                if not phone:
                    continue
                    
                if remove_dup_var.get():
                    if phone in seen:
                        continue
                    seen.add(phone)
                    
                c = {"phone": phone, "name": name_raw.strip()}
                
                if v1_idx is not None and v1_idx < len(r): c["var1"] = r[v1_idx]
                if v2_idx is not None and v2_idx < len(r): c["var2"] = r[v2_idx]
                if v3_idx is not None and v3_idx < len(r): c["var3"] = r[v3_idx]
                if v4_idx is not None and v4_idx < len(r): c["var4"] = r[v4_idx]
                if v5_idx is not None and v5_idx < len(r): c["var5"] = r[v5_idx]
                
                contacts.append(c)
                
            if not contacts:
                messagebox.showwarning("تنبيه", "لم يتم العثور على أرقام صالحة للاستيراد.")
                return
                
            self._refresh_numbers_table(contacts)
            self.contacts_entry.delete(0, "end")
            self.contacts_entry.insert(0, path)
            self._update_contact_count(path)
            
            dialog.destroy()
            messagebox.showinfo("تم الاستيراد" if not is_ar else "نجاح", f"تم استيراد {len(contacts)} جهة اتصال بنجاح!" if is_ar else f"Successfully imported {len(contacts)} contacts!")

        # Top layout split
        top_panel = ctk.CTkFrame(dialog, fg_color="transparent")
        top_panel.pack(fill="x", padx=15, pady=10)

        # Import File Card
        file_card = ctk.CTkFrame(top_panel, corner_radius=10)
        file_card.pack(side=side_lbl, fill="both", expand=True, padx=5, pady=5)
        
        ctk.CTkLabel(file_card, text=self.tr("import_dialog_file_title") if not is_ar else "ملف الاستيراد", 
                     font=ctk.CTkFont(size=13, weight="bold"), text_color=COLORS["primary"]).pack(anchor=anchor_val, padx=15, pady=(10, 2))
        ctk.CTkLabel(file_card, text="Select file to import:" if not is_ar else "اختر ملف للاستيراد:", 
                     font=ctk.CTkFont(size=11), text_color=COLORS["text_muted"]).pack(anchor=anchor_val, padx=15, pady=(2, 5))
                     
        row_browse = ctk.CTkFrame(file_card, fg_color="transparent")
        row_browse.pack(fill="x", padx=15, pady=5)
        
        import_path_entry = ctk.CTkEntry(row_browse, height=34, placeholder_text="c:/path/to/contacts.xlsx")
        import_path_entry.pack(side=side_lbl, fill="x", expand=True, padx=2)
        
        btn_browse_file = ctk.CTkButton(
            row_browse, text="Browse" if not is_ar else "تصفح",
            width=80, height=34, fg_color=COLORS["secondary"], hover_color=COLORS["secondary_hover"],
            text_color=COLORS["secondary_text"], font=ctk.CTkFont(size=12, weight="bold"),
            command=on_browse
        )
        btn_browse_file.pack(side=side_opposite, padx=2)
        
        lbl_warn = ctk.CTkLabel(
            file_card, 
            text="To avoid errors, please import files in correct structure (XLSX, CSV, TXT)" if not is_ar else "لتفادي الأخطاء، يرجى استيراد الملف بالتنسيق الصحيح (XLSX, CSV, TXT)",
            font=ctk.CTkFont(size=10), text_color=COLORS["text_muted"]
        )
        lbl_warn.pack(anchor=anchor_val, padx=15, pady=(2, 10))

        # Settings Card
        settings_card = ctk.CTkFrame(top_panel, corner_radius=10, width=320)
        settings_card.pack(side=side_opposite, fill="both", padx=5, pady=5)
        
        ctk.CTkLabel(settings_card, text="Settings" if not is_ar else "خيارات الاستيراد", 
                     font=ctk.CTkFont(size=13, weight="bold"), text_color=COLORS["primary"]).pack(anchor=anchor_val, padx=15, pady=(10, 5))
                     
        use_header_var = ctk.BooleanVar(value=True)
        chk_header = ctk.CTkCheckBox(settings_card, text="Use first row as header" if not is_ar else "الصف الأول يحتوي على العناوين",
                                     variable=use_header_var, font=ctk.CTkFont(size=11), command=on_settings_changed)
        chk_header.pack(anchor=anchor_val, padx=15, pady=4)
        
        remove_dup_var = ctk.BooleanVar(value=True)
        chk_dup = ctk.CTkCheckBox(settings_card, text="Remove duplications" if not is_ar else "إزالة الأرقام المكررة تلقائياً",
                                  variable=remove_dup_var, font=ctk.CTkFont(size=11))
        chk_dup.pack(anchor=anchor_val, padx=15, pady=4)
        
        row_delim = ctk.CTkFrame(settings_card, fg_color="transparent")
        row_delim.pack(fill="x", padx=15, pady=4)
        
        custom_delimiter_var = ctk.BooleanVar(value=False)
        chk_delim = ctk.CTkCheckBox(row_delim, text="Custom delimiter" if not is_ar else "محدد مخصص",
                                    variable=custom_delimiter_var, font=ctk.CTkFont(size=11), command=on_settings_changed)
        chk_delim.pack(side=side_lbl, padx=2)
        
        delimiter_entry = ctk.CTkEntry(row_delim, width=40, height=26, justify="center")
        delimiter_entry.insert(0, ",")
        delimiter_entry.pack(side=side_lbl, padx=5)
        delimiter_entry.bind("<KeyRelease>", lambda e: on_settings_changed())

        # Assign Fields Card
        assign_card = ctk.CTkFrame(dialog, corner_radius=10)
        assign_card.pack(fill="x", padx=15, pady=5)
        
        ctk.CTkLabel(assign_card, text="Assign Fields" if not is_ar else "تعيين الحقول وتطابق البيانات", 
                     font=ctk.CTkFont(size=13, weight="bold"), text_color=COLORS["primary"]).pack(anchor=anchor_val, padx=15, pady=(10, 5))
                     
        row_combos = ctk.CTkFrame(assign_card, fg_color="transparent")
        row_combos.pack(fill="x", padx=10, pady=(2, 12))
        
        fields_config = [
            ("Name field" if not is_ar else "حقل الاسم", "combo_name"),
            ("Number field" if not is_ar else "حقل الرقم", "combo_number"),
            ("Var1 field" if not is_ar else "حقل المتغير 1", "combo_var1"),
            ("Var2 field" if not is_ar else "حقل المتغير 2", "combo_var2"),
            ("Var3 field" if not is_ar else "حقل المتغير 3", "combo_var3"),
            ("Var4 field" if not is_ar else "حقل المتغير 4", "combo_var4"),
            ("Var5 field" if not is_ar else "حقل المتغير 5", "combo_var5"),
        ]
        
        combos = {}
        for idx, (label_text, combo_name_key) in enumerate(fields_config):
            row_combos.grid_columnconfigure(idx, weight=1)
            cell = ctk.CTkFrame(row_combos, fg_color="transparent")
            cell.grid(row=0, column=idx, padx=4, pady=2, sticky="ew")
            
            ctk.CTkLabel(cell, text=label_text, font=ctk.CTkFont(size=10), text_color=COLORS["text_muted"]).pack(anchor="center", pady=1)
            
            combobox = ctk.CTkOptionMenu(
                cell, values=["None"], width=100, height=28,
                fg_color=COLORS["card_bg"], button_color=COLORS["primary"],
                button_hover_color=COLORS["primary_hover"], text_color=COLORS["text_main"],
                dropdown_fg_color=COLORS["card_bg"], dropdown_text_color=COLORS["text_main"]
            )
            combobox.set("None")
            combobox.pack(fill="x", pady=2)
            combos[combo_name_key] = combobox
            
        combo_name = combos["combo_name"]
        combo_number = combos["combo_number"]
        combo_var1 = combos["combo_var1"]
        combo_var2 = combos["combo_var2"]
        combo_var3 = combos["combo_var3"]
        combo_var4 = combos["combo_var4"]
        combo_var5 = combos["combo_var5"]

        # Grid/Preview Card
        preview_card = ctk.CTkFrame(dialog, corner_radius=10)
        preview_card.pack(fill="both", expand=True, padx=15, pady=10)
        
        ctk.CTkLabel(preview_card, text="File Preview" if not is_ar else "معاينة حية لبيانات الملف المختار", 
                     font=ctk.CTkFont(size=13, weight="bold"), text_color=COLORS["primary"]).pack(anchor=anchor_val, padx=15, pady=(10, 5))
                     
        tbl_frame = ctk.CTkFrame(preview_card, fg_color="transparent")
        tbl_frame.pack(fill="both", expand=True, padx=15, pady=(2, 15))
        
        preview_tree = ttk.Treeview(tbl_frame, show="headings", height=10)
        
        scroll_x = ttk.Scrollbar(tbl_frame, orient="horizontal", command=preview_tree.xview)
        scroll_y = ttk.Scrollbar(tbl_frame, orient="vertical", command=preview_tree.yview)
        preview_tree.configure(xscrollcommand=scroll_x.set, yscrollcommand=scroll_y.set)
        
        preview_tree.pack(side="top", fill="both", expand=True)
        scroll_x.pack(side="bottom", fill="x")
        scroll_y.pack(side="right", fill="y")

        # Bottom Actions Panel
        bottom_row = ctk.CTkFrame(dialog, fg_color="transparent", height=45)
        bottom_row.pack(fill="x", side="bottom", padx=15, pady=15)
        
        btn_import = ctk.CTkButton(
            bottom_row, text="Import" if not is_ar else "استيراد البيانات",
            width=140, height=36, fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"],
            font=ctk.CTkFont(size=12, weight="bold"),
            command=on_import
        )
        btn_import.pack(side=side_opposite, padx=5)
        
        btn_cancel = ctk.CTkButton(
            bottom_row, text="Cancel" if not is_ar else "إلغاء الأمر",
            width=100, height=36, fg_color=COLORS["secondary"], hover_color=COLORS["secondary_hover"],
            text_color=COLORS["secondary_text"], font=ctk.CTkFont(size=12, weight="bold"),
            command=dialog.destroy
        )
        btn_cancel.pack(side=side_opposite, padx=5)

    def _update_contact_count(self, path=None):
        """Update contact count label and load contacts into the numbers table."""
        try:
            if not path:
                path = self.contacts_entry.get()
            if not path or not os.path.exists(path):
                return
            contacts = read_contacts_auto(path, default_country_code=self.config.get("default_country_code", "20"))
            
            # Refresh the Treeview numbers table
            self._refresh_numbers_table(contacts)
            
            if hasattr(self, "contact_count_label") and self.contact_count_label:
                count = len(contacts)
                self.contact_count_label.configure(
                    text=f"📊 {count} جهة اتصال" if count > 0 else "⚠️ لا توجد جهات اتصال"
                )
        except Exception as e:
            self.log(f"⚠️ خطأ أثناء تحديث قائمة الأرقام: {e}")

    def _prepare_content(self):
        """Prepare message text and attachments from the UI inputs."""
        msg_template = self.message_textbox.get("1.0", "end").strip()
        # Get attachments from the new manager
        raw_attachments = self.attachment_manager.get_attachments()
        attachments = []

        for att in raw_attachments:
            path = att.get("path", "").strip()
            if not path:
                continue
            if not os.path.exists(path):
                self.report_error("ERR-09", f"الملف غير موجود: {path}", dialog=True)
                return None, None
            
            # Map to format expected by bot
            att_type = att.get("type", "document")
            ext = os.path.splitext(path)[1].lower()
            
            # Auto-correct type based on file extension to avoid sending images as documents (thumbnails)
            if att_type == "document":
                if ext in [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"]:
                    att_type = "image"
                elif ext in [".mp4", ".avi", ".mov", ".mkv", ".3gp"]:
                    att_type = "video"

            item = {
                "type": att_type,
                "path": path,
                "caption": att.get("caption", "").strip()
            }
            attachments.append(item)

        # Check if empty
        if not msg_template and not attachments:
            self.report_error("ERR-04", "يرجى كتابة نص الرسالة أو اختيار مرفق.", dialog=True, level="warning")
            return None, None

        return msg_template, attachments

    def _get_contacts_from_input(self):
        # Retrieve contacts directly from our progress_tree Treeview!
        """Load contacts from the selected file or numbers table."""
        children = self.progress_tree.get_children()
        if not children:
            contacts_input = self.contacts_entry.get().strip()
            if not contacts_input:
                self.report_error("ERR-05", "يرجى استيراد أو إدخال أرقام أولاً.", dialog=True)
                return None
            
            # Standard fallback (file or group loading)
            contacts = []
            if contacts_input.startswith("[GROUP:") and contacts_input.endswith("]"):
                group_name = contacts_input[7:-1]
                g = self.contacts_mgr.get_by_name(group_name)
                if not g or not g.get("contacts"):
                    self.report_error("ERR-03", f"المجموعة '{group_name}' فارغة أو غير موجودة.", dialog=True)
                    return None
                contacts = g["contacts"]
            elif os.path.exists(contacts_input):
                contacts = read_contacts_auto(contacts_input, default_country_code=self.config.get("default_country_code", "20"))
            
            if not contacts:
                self.report_error("ERR-05", "يرجى استيراد أرقام صحيحة أولاً.", dialog=True)
                return None
            
            # Load these fallback contacts into the Treeview
            self._refresh_numbers_table(contacts)
            children = self.progress_tree.get_children()

        contacts = []
        for item in children:
            vals = self.progress_tree.item(item, "values")
            if len(vals) >= 2:
                name = vals[0]
                phone = vals[1]
                var1 = vals[2] if len(vals) > 2 else ""
                contacts.append({
                    "name": name,
                    "phone": phone,
                    "var1": var1,
                    "tree_item_id": item # Storing item ID for live updates!
                })
        
        self.log(f"📋 تم جلب {len(contacts)} جهة اتصال جاهزة للإرسال.")
        return contacts

    def _log_preflight(self, contacts, msg_template, attachments):
        """Log pre-flight info before starting automation."""
        msg_len = len(msg_template) if msg_template else 0
        if attachments:
            types = ", ".join([a.get("type", "file") for a in attachments])
        else:
            types = "بدون مرفقات"
        self.log(f"🧪 فحص قبل الإرسال: جهات={len(contacts)} | رسالة={msg_len} حرف | مرفقات={types}")


    def _apply_template(self, text, contact):
        """Apply variable substitution to a message template for a contact."""
        if not text:
            return ""
        out = str(text)
        mapping = {
            "name": contact.get("name", ""),
            "phone": contact.get("phone", ""),
            "var1": contact.get("var1", ""),
            "var2": contact.get("var2", ""),
            "var3": contact.get("var3", ""),
            "var4": contact.get("var4", ""),
            "var5": contact.get("var5", ""),
        }
        for k, v in mapping.items():
            out = out.replace("{" + k + "}", str(v) if v is not None else "")
        if self.spin_text_var.get():
            out = self._apply_spintax(out)
        return out

    def _apply_spintax(self, text):
        # Only replace braces that contain a '|', so {name} stays intact.
        """Resolve spintax expressions {option1|option2} with random picks."""
        pattern = re.compile(r"\{([^{}]*\|[^{}]*)\}")
        prev = None
        while prev != text:
            prev = text

            def _pick(match):
                opts = match.group(1).split("|")
                return random.choice(opts).strip()

            text = pattern.sub(_pick, text)
        return text

    def _test_spintax(self):
        """Preview spintax resolution in a dialog window."""
        text = self.message_textbox.get("1.0", "end").strip()
        if not text:
            messagebox.showwarning("تنبيه", "يرجى كتابة نص الرسالة أولاً لتجربة التدوير/المتغيرات.")
            return

        dummy_contact = {
            "name": "محمد أحمد",
            "phone": "966500000000",
            "var1": "منتج مميز",
            "var2": "100 ريال",
            "var3": "خصم 20%",
            "var4": "الرمز: AB12",
            "var5": "شحن مجاني",
        }

        # Apply variables and spintax
        v1 = self._apply_template(text, dummy_contact)
        v2 = self._apply_template(text, dummy_contact)

        info_text = "✨ معاينة حية للرسالة (باستخدام بيانات تجريبية):\n"
        info_text += "──────────────────────────\n"
        info_text += f"👤 الاسم: {dummy_contact['name']} | 📱 الهاتف: {dummy_contact['phone']}\n"
        if "{var1}" in text or "{var2}" in text or "{var3}" in text or "{var4}" in text or "{var5}" in text:
            info_text += f"🏷️ المتغيرات التجريبية: v1={dummy_contact['var1']}, v2={dummy_contact['var2']}\n"
        info_text += "──────────────────────────\n\n"

        if self.spin_text_var.get() and ("{" in text and "|" in text):
            info_text += "🔹 الاحتمال الأول:\n"
            info_text += f"« {v1} »\n\n"
            info_text += "🔹 الاحتمال الثاني (تدوير عشوائي):\n"
            info_text += f"« {v2} »\n"
        else:
            info_text += "📝 الرسالة المعاينة:\n"
            info_text += f"« {v1} »\n"

        messagebox.showinfo("معاينة الرسالة الحية", info_text)

    def _format_attachments_for_contact(self, attachments, contact):
        """Apply per-contact variable substitution to attachment paths."""
        if not attachments:
            return []
        formatted = []
        for att in attachments:
            item = {"type": att.get("type", "document"), "path": att.get("path")}
            cap = att.get("caption")
            if cap:
                item["caption"] = self._apply_template(cap, contact)
            formatted.append(item)
        return formatted

    def _split_messages(self, text):
        """Split a multi-message text by the === separator."""
        if not text:
            return []
        parts = re.split(r"\n\s*---\s*\n", text)
        return [p.strip() for p in parts if p.strip()]

    def _filter_contacts_safe_mode(self, contacts):
        """Pre-validate numbers on WhatsApp before bulk send (Safe Mode)."""
        if not contacts or not self.bot:
            return contacts
        validated = []
        total = len(contacts)
        self.log(f"🛡️ الوضع الآمن: جاري فحص {total} رقم على واتساب...")
        for i, c in enumerate(contacts):
            if self.stop_event.is_set():
                break
            phone = c.get("phone")
            if not phone:
                continue
            res = self.bot.check_number(phone, stop_event=self.stop_event)
            if res == "VALID":
                validated.append(c)
            elif res == "INVALID":
                self.log(f"🚫 تم استبعاد {phone} (بدون واتساب)")
            elif res == "STOPPED":
                break
            else:
                self.log(f"⚠️ تعذر التحقق من {phone} ({res}) — سيتم تخطيه")
        self.log(f"🛡️ الوضع الآمن: {len(validated)}/{total} رقم صالح للإرسال.")
        return validated

    def _check_campaign_safety(self, contact_count, attachments):
        """Warn or auto-fix delays when campaign settings are too aggressive."""
        from utils.safety import assess_campaign_settings

        try:
            delay_min = int(self.delay_min_entry.get())
            delay_max = int(self.delay_max_entry.get())
            batch_size = int(self.batch_size_entry.get())
            pause_min = int(self.batch_min_entry.get())
        except ValueError:
            return True

        has_media = bool(attachments)
        report = assess_campaign_settings(
            contact_count, delay_min, delay_max, batch_size, pause_min, has_media
        )
        if not report.get("warnings"):
            return True

        body = "\n".join(f"• {w}" for w in report["warnings"])
        body += (
            f"\n\nمقترح: تأخير {int(report['suggested_delay_min'])}–"
            f"{int(report['suggested_delay_max'])} ثانية بين الرسائل."
        )
        body += "\n\nنعم = تطبيق الإعدادات المقترحة والمتابعة\nلا = المتابعة كما هي\nإلغاء = إيقاف"

        choice = messagebox.askyesnocancel("تحذير — تقليل مخاطر الحظر", body)
        if choice is None:
            return False
        if choice:
            self.delay_min_entry.delete(0, "end")
            self.delay_min_entry.insert(0, str(int(report["suggested_delay_min"])))
            self.delay_max_entry.delete(0, "end")
            self.delay_max_entry.insert(0, str(int(report["suggested_delay_max"])))
            if pause_min < 60:
                self.batch_min_entry.delete(0, "end")
                self.batch_min_entry.insert(0, "60")
            self.config.set("delay_min", int(report["suggested_delay_min"]))
            self.config.set("delay_max", int(report["suggested_delay_max"]))
            self.config.save()
            self.log("✅ تم تطبيق إعدادات تأخير أكثر أماناً للحملة.")
        return True

