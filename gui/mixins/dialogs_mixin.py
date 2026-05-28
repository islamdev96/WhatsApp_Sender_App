"""WhatsApp Sender Pro — Modal dialog windows (import, number generator, bulk add)."""
import customtkinter as ctk
from tkinter import filedialog, messagebox, ttk
import time
import os
import csv
import datetime

from gui.theme import COLORS
from utils.logger import logger


class DialogsMixin:
    """Mixin: Modal dialog windows (import, number generator, bulk add)."""

    def _open_import_dialog(self):
        """Open the advanced CSV/Excel import dialog with column mapping."""
        win = ctk.CTkToplevel(self)
        win.title(self.tr("dialog_import_title"))
        win.geometry("900x620")
        win.minsize(880, 580)
        win.grab_set()

        file_var = ctk.StringVar(value="")
        header_var = ctk.BooleanVar(value=True)
        custom_delim_var = ctk.BooleanVar(value=False)
        delim_var = ctk.StringVar(value=",")
        dedup_var = ctk.BooleanVar(value=True)

        headers = []
        preview_rows = []

        # Top: File picker
        file_frame = ctk.CTkFrame(win, corner_radius=10)
        file_frame.pack(fill="x", padx=15, pady=(15, 8))
        ctk.CTkLabel(file_frame, text=self.tr("dialog_select_file") + ":", font=ctk.CTkFont(size=12, weight="bold")).pack(side="right", padx=10)
        file_entry = ctk.CTkEntry(file_frame, textvariable=file_var, height=32, corner_radius=8)
        file_entry.pack(side="right", fill="x", expand=True, padx=10, pady=8)

        def _browse_file():
            path = filedialog.askopenfilename(filetypes=[("CSV/Excel", "*.csv;*.xlsx;*.xls;*.txt")])
            if path:
                file_var.set(path)
                _load_preview()

        ctk.CTkButton(file_frame, text=self.tr("dialog_browse"), width=90, height=32,
                      fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"],
                      command=_browse_file).pack(side="left", padx=10)

        # Settings
        settings_frame = ctk.CTkFrame(win, corner_radius=10)
        settings_frame.pack(fill="x", padx=15, pady=(0, 8))
        ctk.CTkLabel(settings_frame, text=self.tr("dialog_settings"), font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="e", padx=12, pady=(8, 4))

        settings_row = ctk.CTkFrame(settings_frame, fg_color="transparent")
        settings_row.pack(fill="x", padx=10, pady=(0, 8))
        ctk.CTkCheckBox(settings_row, text=self.tr("dialog_use_first_row"), variable=header_var,
                        command=lambda: _load_preview()).pack(side="right", padx=6)
        ctk.CTkCheckBox(settings_row, text=self.tr("dialog_custom_delimiter"), variable=custom_delim_var,
                        command=lambda: _load_preview()).pack(side="right", padx=6)
        delim_entry = ctk.CTkEntry(settings_row, textvariable=delim_var, width=60, height=28)
        delim_entry.pack(side="right", padx=6)
        ctk.CTkCheckBox(settings_row, text=self.tr("dialog_remove_duplications"), variable=dedup_var).pack(side="right", padx=6)
        ctk.CTkButton(settings_row, text="↻ Refresh", height=28,
                      fg_color=COLORS["secondary"], hover_color=COLORS["secondary_hover"],
                      text_color=COLORS["secondary_text"],
                      command=lambda: _load_preview()).pack(side="left", padx=6)

        # Field Mapping
        mapping_frame = ctk.CTkFrame(win, corner_radius=10)
        mapping_frame.pack(fill="x", padx=15, pady=(0, 8))
        ctk.CTkLabel(mapping_frame, text=self.tr("dialog_assign_fields"), font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="e", padx=12, pady=(8, 4))

        map_row = ctk.CTkFrame(mapping_frame, fg_color="transparent")
        map_row.pack(fill="x", padx=10, pady=(0, 8))

        def _make_field(label, var):
            frame = ctk.CTkFrame(map_row, fg_color="transparent")
            frame.pack(side="right", padx=6)
            ctk.CTkLabel(frame, text=label, font=ctk.CTkFont(size=11)).pack()
            menu = ctk.CTkOptionMenu(frame, values=["—"], variable=var, width=120,
                                     fg_color=COLORS["bg_dark"], text_color=COLORS["text_main"],
                                     button_color=COLORS["primary"], button_hover_color=COLORS["primary_hover"],
                                     dropdown_fg_color=COLORS["card_bg"], dropdown_text_color=COLORS["text_main"])
            menu.pack()
            return menu

        name_var = ctk.StringVar(value="—")
        phone_var = ctk.StringVar(value="—")
        var1_var = ctk.StringVar(value="—")
        var2_var = ctk.StringVar(value="—")
        var3_var = ctk.StringVar(value="—")
        var4_var = ctk.StringVar(value="—")
        var5_var = ctk.StringVar(value="—")

        menus = {
            "name": _make_field(self.tr("dialog_name_field"), name_var),
            "phone": _make_field(self.tr("dialog_number_field"), phone_var),
            "var1": _make_field(self.tr("dialog_var1"), var1_var),
            "var2": _make_field(self.tr("dialog_var2"), var2_var),
            "var3": _make_field(self.tr("dialog_var3"), var3_var),
            "var4": _make_field(self.tr("dialog_var4"), var4_var),
            "var5": _make_field(self.tr("dialog_var5"), var5_var),
        }

        # Preview
        preview_frame = ctk.CTkFrame(win, corner_radius=10)
        preview_frame.pack(fill="both", expand=True, padx=15, pady=(0, 8))
        ctk.CTkLabel(preview_frame, text="معاينة البيانات (أول 30 صف)", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="e", padx=12, pady=(8, 4))
        preview_list = ctk.CTkScrollableFrame(preview_frame, corner_radius=8)
        preview_list.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        def _set_menu_values(values):
            vals = ["—"] + values
            for m in menus.values():
                m.configure(values=vals)

        def _guess_field(headers_list):
            def find(keys):
                for h in headers_list:
                    hl = h.lower()
                    for k in keys:
                        if k in hl:
                            return h
                return "—"
            
            guessed = {
                "name": find(["name", "full", "given", "اسم", "الاسم"]),
                "phone": find(["phone", "mobile", "number", "رقم", "هاتف", "phone 1 - value"]),
                "var1": find(["var1", "var 1", "variable1", "v1", "custom1"]),
                "var2": find(["var2", "var 2", "variable2", "v2", "custom2"]),
                "var3": find(["var3", "var 3", "variable3", "v3", "custom3"]),
                "var4": find(["var4", "var 4", "variable4", "v4", "custom4"]),
                "var5": find(["var5", "var 5", "variable5", "v5", "custom5"]),
            }

            # Smart fallback heuristics if phone is not matched by keyword
            if guessed["phone"] == "—" and headers_list:
                # Heuristic 1: If there is only one column in the file, it must be the phone number!
                if len(headers_list) == 1:
                    guessed["phone"] = headers_list[0]
                else:
                    # Heuristic 2: Analyze the preview rows to find the column that looks like phone numbers.
                    best_col = None
                    max_phone_score = 0
                    for col_idx, col_name in enumerate(headers_list):
                        score = 0
                        # Check up to 10 rows in preview
                        for r in preview_rows[:10]:
                            if col_idx < len(r):
                                val = str(r[col_idx]).strip()
                                # Clean value from common formatting like +, -, spaces
                                val_clean = val.replace("+", "").replace("-", "").replace(" ", "").replace("(", "").replace(")", "")
                                # Phone number is typically numeric, length between 7 and 15
                                if val_clean.isdigit() and 7 <= len(val_clean) <= 15:
                                    score += 1
                        if score > max_phone_score:
                            max_phone_score = score
                            best_col = col_name
                    
                    if best_col:
                        guessed["phone"] = best_col
                    else:
                        # Heuristic 3: Check if the header itself looks like a phone number
                        for col_name in headers_list:
                            val_clean = str(col_name).strip().replace("+", "").replace("-", "").replace(" ", "").replace("(", "").replace(")", "")
                            if val_clean.isdigit() and 7 <= len(val_clean) <= 15:
                                guessed["phone"] = col_name
                                break

            # Smart fallback for name
            if guessed["name"] == "—" and headers_list:
                # If there are multiple columns and one is already guessed as phone,
                # let's guess the other column as name if it's not phone and not already matched.
                for col in headers_list:
                    if col != guessed["phone"] and col not in [guessed["var1"], guessed["var2"], guessed["var3"], guessed["var4"], guessed["var5"]]:
                        # A column containing non-digit values is likely a name
                        alpha_score = 0
                        for r in preview_rows[:5]:
                            try:
                                col_idx = headers_list.index(col)
                                if col_idx < len(r):
                                    val = str(r[col_idx]).strip()
                                    if any(c.isalpha() for c in val) and not val.replace("+","").replace("-","").isdigit():
                                        alpha_score += 1
                            except Exception as exc:
                                logger.debug("Could not inspect preview row for name-column guess: %s", exc)
                        if alpha_score >= 2:
                            guessed["name"] = col
                            break
                            
            return guessed

        def _render_preview():
            for w in preview_list.winfo_children():
                w.destroy()
            if not headers:
                ctk.CTkLabel(preview_list, text="لا توجد بيانات للعرض",
                             font=ctk.CTkFont(size=11), text_color=COLORS["text_muted"]).pack(pady=10)
                return
            max_cols = min(len(headers), 8)
            head_row = ctk.CTkFrame(preview_list, fg_color=COLORS["card_bg"])
            head_row.pack(fill="x", pady=2)
            for i in range(max_cols):
                ctk.CTkLabel(head_row, text=headers[i], width=120, anchor="e",
                             font=ctk.CTkFont(size=11, weight="bold")).pack(side="right", padx=2)
            for row in preview_rows:
                r = ctk.CTkFrame(preview_list, fg_color="transparent")
                r.pack(fill="x", pady=1)
                for i in range(max_cols):
                    val = row[i] if i < len(row) else ""
                    ctk.CTkLabel(r, text=str(val), width=120, anchor="e",
                                 font=ctk.CTkFont(size=10)).pack(side="right", padx=2)

        def _read_csv(path):
            import csv
            rows = []
            delim = None
            if custom_delim_var.get() and delim_var.get().strip():
                delim = delim_var.get().strip()
            try:
                with open(path, "r", encoding="utf-8-sig", errors="ignore") as f:
                    sample = f.read(2048)
                    f.seek(0)
                    if not delim:
                        try:
                            dialect = csv.Sniffer().sniff(sample, delimiters=[",", ";", "\t", "|"])
                            delim = dialect.delimiter
                        except Exception as exc:
                            logger.debug("Could not sniff CSV delimiter for %s: %s", path, exc)
                            delim = ","
                    reader = csv.reader(f, delimiter=delim)
                    for row in reader:
                        rows.append(row)
            except Exception as exc:
                logger.warning("Could not read CSV preview from %s: %s", path, exc)
                rows = []
            return rows

        def _read_excel(path):
            try:
                import openpyxl
                wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
                ws = wb.active
                rows = []
                for row in ws.iter_rows(values_only=True):
                    rows.append([str(c) if c is not None else "" for c in row])
                wb.close()
                return rows
            except Exception as exc:
                logger.warning("Could not read Excel preview from %s: %s", path, exc)
                return []

        def _load_preview():
            nonlocal headers, preview_rows
            path = file_var.get().strip()
            headers = []
            preview_rows = []
            if not path or not os.path.exists(path):
                _render_preview()
                return
            ext = os.path.splitext(path)[1].lower()
            rows = _read_excel(path) if ext in (".xlsx", ".xls") else _read_csv(path)
            if not rows:
                _render_preview()
                return
            if header_var.get():
                headers = [h.strip() if h else f"Col{i+1}" for i, h in enumerate(rows[0])]
                data_rows = rows[1:]
            else:
                headers = [f"Col{i+1}" for i in range(len(rows[0]))]
                data_rows = rows
            preview_rows = data_rows[:30]
            _set_menu_values(headers)
            guess = _guess_field(headers)
            name_var.set(guess["name"])
            phone_var.set(guess["phone"])
            var1_var.set(guess["var1"])
            var2_var.set(guess["var2"])
            var3_var.set(guess["var3"])
            var4_var.set(guess["var4"])
            var5_var.set(guess["var5"])
            _render_preview()

        def _read_all_rows(path):
            ext = os.path.splitext(path)[1].lower()
            return _read_excel(path) if ext in (".xlsx", ".xls") else _read_csv(path)

        def _import_now():
            path = file_var.get().strip()
            if not path or not os.path.exists(path):
                messagebox.showerror("خطأ", "يرجى اختيار ملف صالح.")
                return

            rows = _read_all_rows(path)
            if not rows:
                messagebox.showerror("خطأ", "تعذر قراءة الملف.")
                return

            if header_var.get():
                hdrs = [h.strip() if h else f"Col{i+1}" for i, h in enumerate(rows[0])]
                data_rows = rows[1:]
            else:
                hdrs = [f"Col{i+1}" for i in range(len(rows[0]))]
                data_rows = rows

            def col_index(col_name):
                if not col_name or col_name == "—":
                    return None
                try:
                    return hdrs.index(col_name)
                except ValueError:
                    return None

            idx_name = col_index(name_var.get())
            idx_phone = col_index(phone_var.get())
            idx_v1 = col_index(var1_var.get())
            idx_v2 = col_index(var2_var.get())
            idx_v3 = col_index(var3_var.get())
            idx_v4 = col_index(var4_var.get())
            idx_v5 = col_index(var5_var.get())

            from utils.helpers import normalize_phone

            contacts = []
            seen = set()
            invalid = 0
            for row in data_rows:
                phone_raw = row[idx_phone] if idx_phone is not None and idx_phone < len(row) else ""
                phone = normalize_phone(phone_raw, default_country_code=self.config.get("default_country_code", "20"))
                if not phone:
                    invalid += 1
                    continue
                if dedup_var.get() and phone in seen:
                    continue
                seen.add(phone)

                name = row[idx_name] if idx_name is not None and idx_name < len(row) else ""
                c = {
                    "name": str(name).strip() if name is not None else "",
                    "phone": phone,
                }
                if idx_v1 is not None and idx_v1 < len(row):
                    c["var1"] = str(row[idx_v1]) if row[idx_v1] is not None else ""
                if idx_v2 is not None and idx_v2 < len(row):
                    c["var2"] = str(row[idx_v2]) if row[idx_v2] is not None else ""
                if idx_v3 is not None and idx_v3 < len(row):
                    c["var3"] = str(row[idx_v3]) if row[idx_v3] is not None else ""
                if idx_v4 is not None and idx_v4 < len(row):
                    c["var4"] = str(row[idx_v4]) if row[idx_v4] is not None else ""
                if idx_v5 is not None and idx_v5 < len(row):
                    c["var5"] = str(row[idx_v5]) if row[idx_v5] is not None else ""
                contacts.append(c)

            if not contacts:
                messagebox.showwarning("تنبيه", "لم يتم العثور على أرقام صالحة.")
                return

            imports_dir = os.path.join(os.getcwd(), "data", "imports")
            os.makedirs(imports_dir, exist_ok=True)
            filename = f"import_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            filepath = os.path.join(imports_dir, filename)

            import csv as _csv
            with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
                writer = _csv.DictWriter(f, fieldnames=["Name", "Phone", "Var1", "Var2", "Var3", "Var4", "Var5"])
                writer.writeheader()
                for c in contacts:
                    writer.writerow({
                        "Name": c.get("name", ""),
                        "Phone": c.get("phone", ""),
                        "Var1": c.get("var1", ""),
                        "Var2": c.get("var2", ""),
                        "Var3": c.get("var3", ""),
                        "Var4": c.get("var4", ""),
                        "Var5": c.get("var5", ""),
                    })

            self.contacts_entry.delete(0, "end")
            self.contacts_entry.insert(0, filepath)
            self.config.set("last_contacts_file", filepath)
            self.config.save()
            self._update_contact_count(filepath)

            messagebox.showinfo("تم", f"تم الاستيراد: {len(contacts)} رقم\nغير صالح: {invalid}")
            win.destroy()

        # Bottom buttons
        btn_row = ctk.CTkFrame(win, fg_color="transparent")
        btn_row.pack(fill="x", padx=15, pady=(0, 15))
        ctk.CTkButton(btn_row, text=self.tr("dialog_btn_cancel"), width=90, height=32,
                      fg_color=COLORS["secondary"], hover_color=COLORS["secondary_hover"],
                      text_color=COLORS["secondary_text"],
                      command=win.destroy).pack(side="left", padx=6)
        ctk.CTkButton(btn_row, text=self.tr("dialog_btn_import"), width=100, height=32,
                      fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"],
                      command=_import_now).pack(side="left", padx=6)

        _load_preview()

    def _open_number_generator(self):
        """Open the sequential phone number generator dialog."""
        win = ctk.CTkToplevel(self)
        win.title("مولد أرقام")
        win.geometry("520x420")
        win.minsize(480, 400)
        win.grab_set()

        cc_var = ctk.StringVar(value="20")
        base_var = ctk.StringVar(value="10")
        start_var = ctk.StringVar(value="00000000")
        end_var = ctk.StringVar(value="00000010")
        pad_var = ctk.StringVar(value="8")
        name_prefix_var = ctk.StringVar(value="Lead")

        preview_box = ctk.CTkTextbox(win, height=180, corner_radius=10,
                                     font=ctk.CTkFont(size=11),
                                     fg_color=COLORS["bg_dark"])
        preview_box.pack(fill="both", expand=True, padx=12, pady=(10, 8))

        def _render_preview(numbers):
            preview_box.delete("1.0", "end")
            for n in numbers[:50]:
                preview_box.insert("end", f"{n}\n")

        def _generate_numbers():
            try:
                cc = cc_var.get().strip()
                base = base_var.get().strip()
                pad = int(pad_var.get().strip() or "0")
                start = int(start_var.get().strip())
                end = int(end_var.get().strip())
            except Exception as exc:
                logger.debug("Invalid generated-number range input: %s", exc)
                messagebox.showerror("خطأ", "تحقق من القيم المدخلة.")
                return []
            if start > end:
                start, end = end, start
            numbers = []
            for i in range(start, end + 1):
                body = str(i).zfill(pad) if pad > 0 else str(i)
                numbers.append(f"{cc}{base}{body}")
            return numbers

        def _refresh_preview():
            nums = _generate_numbers()
            _render_preview(nums)

        def _save_and_use():
            nums = _generate_numbers()
            if not nums:
                return
            imports_dir = os.path.join(os.getcwd(), "data", "imports")
            os.makedirs(imports_dir, exist_ok=True)
            filename = f"generated_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            filepath = os.path.join(imports_dir, filename)

            import csv as _csv
            with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
                writer = _csv.DictWriter(f, fieldnames=["Name", "Phone"])
                writer.writeheader()
                prefix = name_prefix_var.get().strip() or "Lead"
                for idx, n in enumerate(nums, start=1):
                    writer.writerow({"Name": f"{prefix} {idx}", "Phone": n})

            self.contacts_entry.delete(0, "end")
            self.contacts_entry.insert(0, filepath)
            self.config.set("last_contacts_file", filepath)
            self.config.save()
            messagebox.showinfo("تم", f"تم توليد {len(nums)} رقم.")
            win.destroy()

        form = ctk.CTkFrame(win, corner_radius=10)
        form.pack(fill="x", padx=12, pady=(0, 8))

        def _row(label, var):
            r = ctk.CTkFrame(form, fg_color="transparent")
            r.pack(fill="x", padx=8, pady=4)
            ctk.CTkLabel(r, text=label, width=120, anchor="e").pack(side="right")
            ctk.CTkEntry(r, textvariable=var, height=28).pack(side="right", fill="x", expand=True, padx=6)

        _row("رمز الدولة", cc_var)
        _row("بداية الرقم", start_var)
        _row("نهاية الرقم", end_var)
        _row("طول الجزء", pad_var)
        _row("بداية إضافية", base_var)
        _row("اسم افتراضي", name_prefix_var)

        btns = ctk.CTkFrame(win, fg_color="transparent")
        btns.pack(fill="x", padx=12, pady=(0, 12))
        ctk.CTkButton(btns, text="معاينة", width=90, height=30,
                      fg_color=COLORS["secondary"], hover_color=COLORS["secondary_hover"],
                      text_color=COLORS["secondary_text"],
                      command=_refresh_preview).pack(side="left", padx=6)
        ctk.CTkButton(btns, text="حفظ واستخدام", width=110, height=30,
                      fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"],
                      command=_save_and_use).pack(side="left", padx=6)

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

