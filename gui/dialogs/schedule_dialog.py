"""WhatsApp Sender Pro — Campaign Date-Time Scheduler Picker Dialog module."""
import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import datetime

from gui.theme import COLORS
from utils.logger import logger


class ScheduleCampaignDialog(ctk.CTkToplevel):
    """Campaign Scheduler date-time picker dialog."""

    def __init__(self, parent, contacts, msg_template, attachments):
        super().__init__(parent)
        self.parent = parent
        self.contacts = contacts
        self.msg_template = msg_template
        self.attachments = attachments

        self.title("📅 جدولة الحملة | Schedule Campaign")
        self.geometry("520x460")
        self.resizable(False, False)
        self.transient(self.parent)
        self.grab_set()

        # Center on parent
        self.update_idletasks()
        x = self.parent.winfo_x() + (self.parent.winfo_width() - 520) // 2
        y = self.parent.winfo_y() + (self.parent.winfo_height() - 460) // 2
        self.geometry(f"+{x}+{y}")

        frm = ctk.CTkFrame(self, fg_color="transparent")
        frm.pack(fill="both", expand=True, padx=25, pady=20)

        # Title
        title = ctk.CTkLabel(
            frm, text="📅 جدولة الحملة الجديدة | Schedule New Campaign",
            font=("Segoe UI", 16, "bold"), text_color=COLORS.get("primary", "#00E676")
        )
        title.pack(anchor="w", pady=(0, 15))

        # Campaign Name Entry
        ctk.CTkLabel(frm, text="اسم الحملة / Campaign Name:", font=("Segoe UI", 12)).pack(anchor="e", pady=(5, 2))
        self.user_edited_name = False
        future_dt = datetime.datetime.now() + datetime.timedelta(minutes=10)
        is_ar = self.parent.current_lang.get() == "ar"
        if is_ar:
            default_name = f"حملة مجدولة - {future_dt.strftime('%Y-%m-%d %H:%M')}"
        else:
            default_name = f"Scheduled Campaign - {future_dt.strftime('%Y-%m-%d %H:%M')}"
            
        self.name_entry = ctk.CTkEntry(frm, height=36)
        self.name_entry.insert(0, default_name)
        self.name_entry.pack(fill="x", pady=(0, 10))
        self.name_entry.bind("<Key>", self._on_name_entry_typed)

        # DateTime Selection Row
        picker_frame = ctk.CTkFrame(frm, fg_color="transparent")
        picker_frame.pack(fill="x", pady=10)

        # Day
        self.day_var = tk.StringVar(value=str(future_dt.day))
        ctk.CTkLabel(picker_frame, text="اليوم / Day:", font=("Segoe UI", 11)).grid(row=0, column=4, padx=5, sticky="e")
        self.day_combo = ctk.CTkComboBox(picker_frame, width=70, values=[str(d) for d in range(1, 32)], variable=self.day_var)
        self.day_combo.grid(row=1, column=4, padx=5)
        self.day_combo.set(str(future_dt.day))

        # Month
        self.month_var = tk.StringVar(value=str(future_dt.month))
        ctk.CTkLabel(picker_frame, text="الشهر / Month:", font=("Segoe UI", 11)).grid(row=0, column=3, padx=5, sticky="e")
        self.month_combo = ctk.CTkComboBox(picker_frame, width=75, values=[str(m) for m in range(1, 13)], variable=self.month_var)
        self.month_combo.grid(row=1, column=3, padx=5)
        self.month_combo.set(str(future_dt.month))

        # Year
        self.year_var = tk.StringVar(value=str(future_dt.year))
        ctk.CTkLabel(picker_frame, text="السنة / Year:", font=("Segoe UI", 11)).grid(row=0, column=2, padx=5, sticky="e")
        self.year_combo = ctk.CTkComboBox(picker_frame, width=80, values=[str(future_dt.year), str(future_dt.year + 1)], variable=self.year_var)
        self.year_combo.grid(row=1, column=2, padx=5)
        self.year_combo.set(str(future_dt.year))

        # Hour
        self.hour_var = tk.StringVar(value=str(future_dt.hour))
        ctk.CTkLabel(picker_frame, text="الساعة / Hour:", font=("Segoe UI", 11)).grid(row=0, column=1, padx=5, sticky="e")
        self.hour_combo = ctk.CTkComboBox(picker_frame, width=70, values=[str(h) for h in range(24)], variable=self.hour_var)
        self.hour_combo.grid(row=1, column=1, padx=5)
        self.hour_combo.set(str(future_dt.hour))

        # Minute
        self.minute_var = tk.StringVar(value=str(future_dt.minute))
        ctk.CTkLabel(picker_frame, text="الدقيقة / Min:", font=("Segoe UI", 11)).grid(row=0, column=0, padx=5, sticky="e")
        self.minute_combo = ctk.CTkComboBox(picker_frame, width=70, values=[str(m) for m in range(60)], variable=self.minute_var)
        self.minute_combo.grid(row=1, column=0, padx=5)
        self.minute_combo.set(str(future_dt.minute))

        # Sending Mode selector
        ctk.CTkLabel(frm, text="وضع الإرسال / Sending Mode:", font=("Segoe UI", 12)).pack(anchor="e", pady=(15, 2))
        self.mode_var = tk.StringVar(value="safe")
        
        mode_frame = ctk.CTkFrame(frm, fg_color=COLORS.get("card_bg", "#1E293B"), corner_radius=8, height=45)
        mode_frame.pack(fill="x", pady=(0, 15))
        
        r_safe = ctk.CTkRadioButton(mode_frame, text="الوضع الآمن (Safe Mode)", variable=self.mode_var, value="safe")
        r_safe.pack(side="right", padx=15, pady=8)
        
        r_blind = ctk.CTkRadioButton(mode_frame, text="الوضع العشوائي (Blind Mode)", variable=self.mode_var, value="blind")
        r_blind.pack(side="left", padx=15, pady=8)

        # Action Buttons
        btn_frame = ctk.CTkFrame(frm, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(20, 0))

        btn_cancel = ctk.CTkButton(
            btn_frame, text="إلغاء | Cancel",
            font=("Segoe UI", 13, "bold"), width=130, height=38,
            fg_color=COLORS.get("danger", "#EF4444"),
            hover_color=COLORS.get("danger_hover", "#DC2626"),
            text_color="#FFFFFF", command=self.destroy
        )
        btn_cancel.pack(side="left", padx=(0, 10))

        btn_ok = ctk.CTkButton(
            btn_frame, text="تأكيد الجدولة | Schedule",
            font=("Segoe UI", 13, "bold"), width=150, height=38,
            fg_color=COLORS.get("primary", "#00E676"),
            hover_color=COLORS.get("primary_hover", "#00C853"),
            text_color="#000000", command=self._on_schedule
        )
        btn_ok.pack(side="right")

        # Traces for auto-updating Campaign Name on date-time changes
        self.day_var.trace_add("write", self._update_campaign_name_automatically)
        self.month_var.trace_add("write", self._update_campaign_name_automatically)
        self.year_var.trace_add("write", self._update_campaign_name_automatically)
        self.hour_var.trace_add("write", self._update_campaign_name_automatically)
        self.minute_var.trace_add("write", self._update_campaign_name_automatically)

    def _on_schedule(self):
        try:
            target_year = int(self.year_combo.get())
            target_month = int(self.month_combo.get())
            target_day = int(self.day_combo.get())
            target_hour = int(self.hour_combo.get())
            target_minute = int(self.minute_combo.get())
            
            target_dt = datetime.datetime(target_year, target_month, target_day, target_hour, target_minute)
        except ValueError:
            messagebox.showerror("خطأ", "التاريخ والوقت المحدد غير صالح.")
            return

        if target_dt <= datetime.datetime.now():
            messagebox.showerror("خطأ", "يرجى تحديد تاريخ ووقت في المستقبل.")
            return

        name = self.name_entry.get().strip()
        if not name:
            name = f"حملة مجدولة - {target_dt.strftime('%Y-%m-%d %H:%M')}"

        # If contacts is loaded from a group inside contacts_entry, get that group name
        c_input = self.parent.contacts_entry.get().strip()
        group_name = None
        if c_input.startswith("[GROUP:") and c_input.endswith("]"):
            group_name = c_input[7:-1]

        # Save scheduled campaign in DB
        self.parent.scheduler.schedule_campaign(
            name=name,
            scheduled_time=target_dt,
            message=self.msg_template,
            attachments=self.attachments,
            group_name=group_name,
            contacts=self.contacts if not group_name else None,
            sending_mode=self.mode_var.get()
        )

        self.destroy()
        messagebox.showinfo("تمت الجدولة", f"تمت جدولة الحملة '{name}' بنجاح في {target_dt.strftime('%Y-%m-%d %H:%M')}.")
        self.parent.log(f"📅 تم جدولة حملة جديدة: {name} في {target_dt.strftime('%Y-%m-%d %H:%M')}")

    def _on_name_entry_typed(self, event):
        self.user_edited_name = True

    def _update_campaign_name_automatically(self, *args):
        if hasattr(self, "user_edited_name") and self.user_edited_name:
            return
            
        try:
            day = self.day_combo.get().strip()
            month = self.month_combo.get().strip()
            year = self.year_combo.get().strip()
            hour = self.hour_combo.get().strip()
            minute = self.minute_combo.get().strip()
            
            # Skip update if any value is empty
            if not day or not month or not year or not hour or not minute:
                return
                
            # Pad values nicely
            d_str = f"{int(day):02d}"
            m_str = f"{int(month):02d}"
            y_str = f"{int(year)}"
            h_str = f"{int(hour):02d}"
            min_str = f"{int(minute):02d}"
            
            is_ar = self.parent.current_lang.get() == "ar"
            if is_ar:
                formatted_name = f"حملة مجدولة - {y_str}-{m_str}-{d_str} {h_str}:{min_str}"
            else:
                formatted_name = f"Scheduled Campaign - {y_str}-{m_str}-{d_str} {h_str}:{min_str}"
                
            self.name_entry.delete(0, "end")
            self.name_entry.insert(0, formatted_name)
        except Exception as e:
            logger.debug("Failed to auto update campaign name: %s", e)
