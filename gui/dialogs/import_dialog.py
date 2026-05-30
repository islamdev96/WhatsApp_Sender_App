"""WhatsApp Sender Pro — Advanced CSV/Excel import Dialog with column-mapping and real-time preview."""
import customtkinter as ctk
from tkinter import filedialog, messagebox, ttk
import os
import datetime
import csv

from gui.theme import COLORS
from utils.logger import logger
from utils.helpers import normalize_phone


class ImportDialog(ctk.CTkToplevel):
    """Advanced CSV/Excel import dialog with column mapping and live preview heuristics."""

    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        
        self.title(self.parent.tr("dialog_import_title"))
        self.geometry("900x620")
        self.minsize(880, 580)
        self.grab_set()

        # Center dialog relative to parent
        self.update_idletasks()
        x = self.parent.winfo_x() + (self.parent.winfo_width() - 900) // 2
        y = self.parent.winfo_y() + (self.parent.winfo_height() - 620) // 2
        self.geometry(f"+{x}+{y}")

        self.file_var = ctk.StringVar(value="")
        self.header_var = ctk.BooleanVar(value=True)
        self.custom_delim_var = ctk.BooleanVar(value=False)
        self.delim_var = ctk.StringVar(value=",")
        self.dedup_var = ctk.BooleanVar(value=True)

        self.headers = []
        self.preview_rows = []

        # Top: File picker
        file_frame = ctk.CTkFrame(self, corner_radius=10)
        file_frame.pack(fill="x", padx=15, pady=(15, 8))
        
        ctk.CTkLabel(
            file_frame, text=self.parent.tr("dialog_select_file") + ":", 
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(side="right", padx=10)
        
        file_entry = ctk.CTkEntry(file_frame, textvariable=self.file_var, height=32, corner_radius=8)
        file_entry.pack(side="right", fill="x", expand=True, padx=10, pady=8)

        ctk.CTkButton(
            file_frame, text=self.parent.tr("dialog_browse"), width=90, height=32,
            fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"],
            command=self._browse_file
        ).pack(side="left", padx=10)

        # Settings
        settings_frame = ctk.CTkFrame(self, corner_radius=10)
        settings_frame.pack(fill="x", padx=15, pady=(0, 8))
        
        ctk.CTkLabel(
            settings_frame, text=self.parent.tr("dialog_settings"), 
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor="e", padx=12, pady=(8, 4))

        settings_row = ctk.CTkFrame(settings_frame, fg_color="transparent")
        settings_row.pack(fill="x", padx=10, pady=(0, 8))
        
        ctk.CTkCheckBox(
            settings_row, text=self.parent.tr("dialog_use_first_row"), 
            variable=self.header_var, command=self._load_preview
        ).pack(side="right", padx=6)
        
        ctk.CTkCheckBox(
            settings_row, text=self.parent.tr("dialog_custom_delimiter"), 
            variable=self.custom_delim_var, command=self._load_preview
        ).pack(side="right", padx=6)
        
        delim_entry = ctk.CTkEntry(settings_row, textvariable=self.delim_var, width=60, height=28)
        delim_entry.pack(side="right", padx=6)
        
        ctk.CTkCheckBox(
            settings_row, text=self.parent.tr("dialog_remove_duplications"), 
            variable=self.dedup_var
        ).pack(side="right", padx=6)
        
        ctk.CTkButton(
            settings_row, text="↻ Refresh", height=28,
            fg_color=COLORS["secondary"], hover_color=COLORS["secondary_hover"],
            text_color=COLORS["secondary_text"], command=self._load_preview
        ).pack(side="left", padx=6)

        # Field Mapping
        mapping_frame = ctk.CTkFrame(self, corner_radius=10)
        mapping_frame.pack(fill="x", padx=15, pady=(0, 8))
        
        ctk.CTkLabel(
            mapping_frame, text=self.parent.tr("dialog_assign_fields"), 
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor="e", padx=12, pady=(8, 4))

        self.map_row = ctk.CTkFrame(mapping_frame, fg_color="transparent")
        self.map_row.pack(fill="x", padx=10, pady=(0, 8))

        self.name_var = ctk.StringVar(value="—")
        self.phone_var = ctk.StringVar(value="—")
        self.var1_var = ctk.StringVar(value="—")
        self.var2_var = ctk.StringVar(value="—")
        self.var3_var = ctk.StringVar(value="—")
        self.var4_var = ctk.StringVar(value="—")
        self.var5_var = ctk.StringVar(value="—")

        self.menus = {
            "name": self._make_field(self.parent.tr("dialog_name_field"), self.name_var),
            "phone": self._make_field(self.parent.tr("dialog_number_field"), self.phone_var),
            "var1": self._make_field(self.parent.tr("dialog_var1"), self.var1_var),
            "var2": self._make_field(self.parent.tr("dialog_var2"), self.var2_var),
            "var3": self._make_field(self.parent.tr("dialog_var3"), self.var3_var),
            "var4": self._make_field(self.parent.tr("dialog_var4"), self.var4_var),
            "var5": self._make_field(self.parent.tr("dialog_var5"), self.var5_var),
        }

        # Preview
        preview_frame = ctk.CTkFrame(self, corner_radius=10)
        preview_frame.pack(fill="both", expand=True, padx=15, pady=(0, 8))
        
        ctk.CTkLabel(
            preview_frame, text="معاينة البيانات (أول 30 صف)", 
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor="e", padx=12, pady=(8, 4))
        
        self.preview_list = ctk.CTkScrollableFrame(preview_frame, corner_radius=8)
        self.preview_list.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Bottom buttons
        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(fill="x", padx=15, pady=(0, 15))
        
        ctk.CTkButton(
            btn_row, text=self.parent.tr("dialog_btn_cancel"), width=90, height=32,
            fg_color=COLORS["secondary"], hover_color=COLORS["secondary_hover"],
            text_color=COLORS["secondary_text"], command=self.destroy
        ).pack(side="left", padx=6)
        
        ctk.CTkButton(
            btn_row, text=self.parent.tr("dialog_btn_import"), width=100, height=32,
            fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"],
            command=self._import_now
        ).pack(side="left", padx=6)

        self._load_preview()

    def _make_field(self, label, var):
        frame = ctk.CTkFrame(self.map_row, fg_color="transparent")
        frame.pack(side="right", padx=6)
        ctk.CTkLabel(frame, text=label, font=ctk.CTkFont(size=11)).pack()
        menu = ctk.CTkOptionMenu(
            frame, values=["—"], variable=var, width=120,
            fg_color=COLORS["bg_dark"], text_color=COLORS["text_main"],
            button_color=COLORS["primary"], button_hover_color=COLORS["primary_hover"],
            dropdown_fg_color=COLORS["card_bg"], dropdown_text_color=COLORS["text_main"]
        )
        menu.pack()
        return menu

    def _browse_file(self):
        path = filedialog.askopenfilename(filetypes=[("CSV/Excel", "*.csv;*.xlsx;*.xls;*.txt")])
        if path:
            self.file_var.set(path)
            self._load_preview()

    def _set_menu_values(self, values):
        vals = ["—"] + values
        for m in self.menus.values():
            m.configure(values=vals)

    def _guess_field(self, headers_list):
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
                    for r in self.preview_rows[:10]:
                        if col_idx < len(r):
                            val = str(r[col_idx]).strip()
                            val_clean = val.replace("+", "").replace("-", "").replace(" ", "").replace("(", "").replace(")", "")
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
            for col in headers_list:
                if col != guessed["phone"] and col not in [guessed["var1"], guessed["var2"], guessed["var3"], guessed["var4"], guessed["var5"]]:
                    alpha_score = 0
                    for r in self.preview_rows[:5]:
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

    def _render_preview(self):
        for w in self.preview_list.winfo_children():
            w.destroy()
        if not self.headers:
            ctk.CTkLabel(
                self.preview_list, text="لا توجد بيانات للعرض",
                font=ctk.CTkFont(size=11), text_color=COLORS["text_muted"]
            ).pack(pady=10)
            return
        max_cols = min(len(self.headers), 8)
        head_row = ctk.CTkFrame(self.preview_list, fg_color=COLORS["card_bg"])
        head_row.pack(fill="x", pady=2)
        for i in range(max_cols):
            ctk.CTkLabel(
                head_row, text=self.headers[i], width=120, anchor="e",
                font=ctk.CTkFont(size=11, weight="bold")
            ).pack(side="right", padx=2)
        for row in self.preview_rows:
            r = ctk.CTkFrame(self.preview_list, fg_color="transparent")
            r.pack(fill="x", pady=1)
            for i in range(max_cols):
                val = row[i] if i < len(row) else ""
                ctk.CTkLabel(
                    r, text=str(val), width=120, anchor="e",
                    font=ctk.CTkFont(size=10)
                ).pack(side="right", padx=2)

    def _read_csv(self, path):
        rows = []
        delim = None
        if self.custom_delim_var.get() and self.delim_var.get().strip():
            delim = self.delim_var.get().strip()
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

    def _read_excel(self, path):
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

    def _load_preview(self):
        path = self.file_var.get().strip()
        self.headers = []
        self.preview_rows = []
        if not path or not os.path.exists(path):
            self._render_preview()
            return
        ext = os.path.splitext(path)[1].lower()
        rows = self._read_excel(path) if ext in (".xlsx", ".xls") else self._read_csv(path)
        if not rows:
            self._render_preview()
            return
        if self.header_var.get():
            self.headers = [h.strip() if h else f"Col{i+1}" for i, h in enumerate(rows[0])]
            data_rows = rows[1:]
        else:
            self.headers = [f"Col{i+1}" for i in range(len(rows[0]))]
            data_rows = rows
        self.preview_rows = data_rows[:30]
        self._set_menu_values(self.headers)
        guess = self._guess_field(self.headers)
        self.name_var.set(guess["name"])
        self.phone_var.set(guess["phone"])
        self.var1_var.set(guess["var1"])
        self.var2_var.set(guess["var2"])
        self.var3_var.set(guess["var3"])
        self.var4_var.set(guess["var4"])
        self.var5_var.set(guess["var5"])
        self._render_preview()

    def _read_all_rows(self, path):
        ext = os.path.splitext(path)[1].lower()
        return self._read_excel(path) if ext in (".xlsx", ".xls") else self._read_csv(path)

    def _import_now(self):
        path = self.file_var.get().strip()
        if not path or not os.path.exists(path):
            messagebox.showerror("خطأ", "يرجى اختيار ملف صالح.")
            return

        rows = self._read_all_rows(path)
        if not rows:
            messagebox.showerror("خطأ", "تعذر قراءة الملف.")
            return

        if self.header_var.get():
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

        idx_name = col_index(self.name_var.get())
        idx_phone = col_index(self.phone_var.get())
        idx_v1 = col_index(self.var1_var.get())
        idx_v2 = col_index(self.var2_var.get())
        idx_v3 = col_index(self.var3_var.get())
        idx_v4 = col_index(self.var4_var.get())
        idx_v5 = col_index(self.var5_var.get())

        contacts = []
        seen = set()
        invalid = 0
        for row in data_rows:
            phone_raw = row[idx_phone] if idx_phone is not None and idx_phone < len(row) else ""
            phone = normalize_phone(phone_raw, default_country_code=self.parent.config.get("default_country_code", "20"))
            if not phone:
                invalid += 1
                continue
            if self.dedup_var.get() and phone in seen:
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

        with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=["Name", "Phone", "Var1", "Var2", "Var3", "Var4", "Var5"])
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

        self.parent.contacts_entry.delete(0, "end")
        self.parent.contacts_entry.insert(0, filepath)
        self.parent.config.set("last_contacts_file", filepath)
        self.parent.config.save()
        self.parent._update_contact_count(filepath)

        messagebox.showinfo("تم", f"تم الاستيراد: {len(contacts)} رقم\nغير صالح: {invalid}")
        self.destroy()
