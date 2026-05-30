"""WhatsApp Sender Pro — Phone number generator dialog module."""
import customtkinter as ctk
from tkinter import messagebox
import os
import csv
import datetime

from gui.theme import COLORS
from utils.logger import logger


class NumberGeneratorDialog(ctk.CTkToplevel):
    """Sequential phone number generator dialog."""

    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        
        self.title("مولد أرقام")
        self.geometry("520x420")
        self.minsize(480, 400)
        self.grab_set()

        # Center dialog relative to parent
        self.update_idletasks()
        x = self.parent.winfo_x() + (self.parent.winfo_width() - 520) // 2
        y = self.parent.winfo_y() + (self.parent.winfo_height() - 420) // 2
        self.geometry(f"+{x}+{y}")

        self.cc_var = ctk.StringVar(value="20")
        self.base_var = ctk.StringVar(value="10")
        self.start_var = ctk.StringVar(value="00000000")
        self.end_var = ctk.StringVar(value="00000010")
        self.pad_var = ctk.StringVar(value="8")
        self.name_prefix_var = ctk.StringVar(value="Lead")

        self.preview_box = ctk.CTkTextbox(
            self, height=180, corner_radius=10,
            font=ctk.CTkFont(size=11), fg_color=COLORS["bg_dark"]
        )
        self.preview_box.pack(fill="both", expand=True, padx=12, pady=(10, 8))

        form = ctk.CTkFrame(self, corner_radius=10)
        form.pack(fill="x", padx=12, pady=(0, 8))

        self._row(form, "رمز الدولة", self.cc_var)
        self._row(form, "بداية الرقم", self.start_var)
        self._row(form, "نهاية الرقم", self.end_var)
        self._row(form, "طول الجزء", self.pad_var)
        self._row(form, "بداية إضافية", self.base_var)
        self._row(form, "اسم افتراضي", self.name_prefix_var)

        btns = ctk.CTkFrame(self, fg_color="transparent")
        btns.pack(fill="x", padx=12, pady=(0, 12))
        
        ctk.CTkButton(
            btns, text="معاينة", width=90, height=30,
            fg_color=COLORS["secondary"], hover_color=COLORS["secondary_hover"],
            text_color=COLORS["secondary_text"], command=self._refresh_preview
        ).pack(side="left", padx=6)
        
        ctk.CTkButton(
            btns, text="حفظ واستخدام", width=110, height=30,
            fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"],
            command=self._save_and_use
        ).pack(side="left", padx=6)

    def _row(self, parent_frame, label, var):
        r = ctk.CTkFrame(parent_frame, fg_color="transparent")
        r.pack(fill="x", padx=8, pady=4)
        ctk.CTkLabel(r, text=label, width=120, anchor="e").pack(side="right")
        ctk.CTkEntry(r, textvariable=var, height=28).pack(side="right", fill="x", expand=True, padx=6)

    def _render_preview(self, numbers):
        self.preview_box.delete("1.0", "end")
        for n in numbers[:50]:
            self.preview_box.insert("end", f"{n}\n")

    def _generate_numbers(self):
        try:
            cc = self.cc_var.get().strip()
            base = self.base_var.get().strip()
            pad = int(self.pad_var.get().strip() or "0")
            start = int(self.start_var.get().strip())
            end = int(self.end_var.get().strip())
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

    def _refresh_preview(self):
        nums = self._generate_numbers()
        self._render_preview(nums)

    def _save_and_use(self):
        nums = self._generate_numbers()
        if not nums:
            return

        imports_dir = os.path.join(os.getcwd(), "data", "imports")
        os.makedirs(imports_dir, exist_ok=True)
        filename = f"generated_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        filepath = os.path.join(imports_dir, filename)

        with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=["Name", "Phone"])
            writer.writeheader()
            prefix = self.name_prefix_var.get().strip() or "Lead"
            for idx, n in enumerate(nums, start=1):
                writer.writerow({"Name": f"{prefix} {idx}", "Phone": n})

        self.parent.contacts_entry.delete(0, "end")
        self.parent.contacts_entry.insert(0, filepath)
        self.parent.config.set("last_contacts_file", filepath)
        self.parent.config.save()
        messagebox.showinfo("تم", f"تم توليد {len(nums)} رقم.")
        self.destroy()
