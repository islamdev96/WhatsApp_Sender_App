"""WhatsApp Sender Pro — Software License Activation Window Dialog module."""
import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import sys

from gui.theme import COLORS
from utils.licensing import get_hwid, save_license_key


class ActivationDialog(ctk.CTk):
    """Premium standalone License Key Activation window."""

    def __init__(self):
        super().__init__()

        # Appearance & Themes
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("green")

        self.title("🔑 تفعيل ترخيص البرنامج | License Activation")
        self.geometry("520x420")
        self.resizable(False, False)

        # Center on screen
        self.update_idletasks()
        w = 520
        h = 420
        x = (self.winfo_screenwidth() - w) // 2
        y = (self.winfo_screenheight() - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

        # State Variable
        self.is_activated = False

        # Main Frame Container
        frm = ctk.CTkFrame(self, fg_color="#0F172A", corner_radius=0)
        frm.pack(fill="both", expand=True)

        # App Brand Header
        header_lbl = ctk.CTkLabel(
            frm, text="Auto WhatsApp Business Sender Turbo Pro",
            font=("Segoe UI", 16, "bold"), text_color="#00E676"
        )
        header_lbl.pack(pady=(30, 2))

        sub_lbl = ctk.CTkLabel(
            frm, text="V17.0 Full Standalone Edition",
            font=("Segoe UI", 10), text_color="#64748B"
        )
        sub_lbl.pack(pady=(0, 20))

        # HWID Container
        hwid_frame = ctk.CTkFrame(frm, fg_color="#1E293B", corner_radius=10, height=80)
        hwid_frame.pack_propagate(False)
        hwid_frame.pack(fill="x", padx=30, pady=10)

        ctk.CTkLabel(
            hwid_frame, text="كود جهازك الفريد / Your Hardware ID (HWID):",
            font=("Segoe UI", 11, "bold"), text_color="#94A3B8"
        ).pack(anchor="w", padx=15, pady=(8, 2))

        row_hwid = ctk.CTkFrame(hwid_frame, fg_color="transparent")
        row_hwid.pack(fill="x", padx=15, pady=0)

        self.hwid_val = get_hwid()
        self.entry_hwid = ctk.CTkEntry(
            row_hwid, height=28, font=("Consolas", 11, "bold"),
            fg_color="#0F172A", border_color="#334155", text_color="#38BDF8",
            justify="center"
        )
        self.entry_hwid.insert(0, self.hwid_val)
        self.entry_hwid.configure(state="readonly")
        self.entry_hwid.pack(side="left", fill="x", expand=True, padx=(0, 10))

        btn_copy = ctk.CTkButton(
            row_hwid, text="📋 Copy", width=70, height=28,
            fg_color="#00A884", hover_color="#008F6F", text_color="#FFFFFF",
            font=("Segoe UI", 11, "bold"), command=self._copy_hwid
        )
        btn_copy.pack(side="right")

        # License Key Entry Container
        key_frame = ctk.CTkFrame(frm, fg_color="transparent")
        key_frame.pack(fill="x", padx=30, pady=15)

        ctk.CTkLabel(
            key_frame, text="أدخل كود التفعيل / Enter Activation Key:",
            font=("Segoe UI", 11, "bold"), text_color="#E2E8F0"
        ).pack(anchor="w", pady=(0, 5))

        self.entry_key = ctk.CTkEntry(
            key_frame, height=36, placeholder_text="WSP-XXXX-XXXX-XXXX-XXXX",
            font=("Consolas", 12, "bold"), fg_color="#1E293B", border_color="#334155",
            text_color="#FFFFFF", justify="center"
        )
        self.entry_key.pack(fill="x")

        # Action Buttons
        btn_frame = ctk.CTkFrame(frm, fg_color="transparent")
        btn_frame.pack(fill="x", padx=30, pady=(25, 0))

        btn_exit = ctk.CTkButton(
            btn_frame, text="إغلاق | Exit", width=120, height=38,
            fg_color="#EF4444", hover_color="#DC2626", text_color="#FFFFFF",
            font=("Segoe UI", 12, "bold"), command=self._exit_app
        )
        btn_exit.pack(side="left")

        btn_activate = ctk.CTkButton(
            btn_frame, text="تفعيل | Activate", width=160, height=38,
            fg_color="#00E676", hover_color="#00C853", text_color="#000000",
            font=("Segoe UI", 12, "bold"), command=self._activate_now
        )
        btn_activate.pack(side="right")

        # Handle X window close safely
        self.protocol("WM_DELETE_WINDOW", self._exit_app)

    def _copy_hwid(self):
        self.clipboard_clear()
        self.clipboard_append(self.hwid_val)
        messagebox.showinfo("تم النسخ", "تم نسخ كود الجهاز الفريد (HWID) إلى الحافظة بنجاح.")

    def _activate_now(self):
        key = self.entry_key.get().strip()
        if not key:
            messagebox.showwarning("تنبيه", "يرجى إدخال مفتاح الترخيص الخاص بك.")
            return

        if save_license_key(key):
            messagebox.showinfo(
                "نجاح التفعيل",
                "تم تفعيل ترخيص البرنامج بنجاح! شكراً جزيلاً لك.\nسيتم الآن فتح التطبيق الرئيسي."
            )
            self.is_activated = True
            self.destroy()
        else:
            messagebox.showerror(
                "خطأ في التفعيل",
                "مفتاح الترخيص غير صالح لجهازك!\nيرجى التواصل مع الموزع/المطور للحصول على المفتاح الصحيح."
            )

    def _exit_app(self):
        sys.exit(0)
