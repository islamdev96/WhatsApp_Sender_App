"""WhatsApp Sender Pro — Automation control methods (send, stop, pause, error mapping)."""
import customtkinter as ctk
from tkinter import messagebox
import threading
import random
import os
import datetime
import time

from gui.theme import COLORS
from utils.logger import logger


class AutomationMixin:
    """Mixin: Automation control methods (send, stop, pause, error mapping)."""

    def _begin_send(self, contacts, msg_template, attachments):
        """Prepare and launch the sending automation thread."""
        self._agent_debug_log(
            "H4",
            "modern_ui.py:_begin_send",
            "begin_send_called",
            {"contact_count": len(contacts) if contacts else 0, "is_running": bool(self.is_running)},
        )
        if self.is_running:
            return

        if getattr(self, "sending_mode", None) == "safe":
            contacts = self._filter_contacts_safe_mode(contacts)
            if not contacts:
                self.report_error("ERR-05", "لا توجد أرقام صالحة للإرسال بعد الفحص.", dialog=True)
                return

        # 4. Apply background mode
        if self.bg_mode_var.get():
            self.bot.background_mode = True
            self.bot.minimize()
            self.log("🖥️ وضع الخلفية مفعّل — المتصفح مُصغّر.")
        else:
            self.bot.background_mode = False
            self.bot.bring_to_front()

        # 5. Start Thread
        self.is_running = True
        self._switch_tab("log")
        self.log("📋 سجل التشخيص — كل خطوات البوت تظهر هنا وفي التيرمنال.", level="INFO")
        self.stop_event.clear()
        self.pause_event.clear()
        self.is_paused = False

        self._log_preflight(contacts, msg_template, attachments)

        self.btn_start.configure(state="disabled")
        self.btn_stop.configure(state="normal")
        if hasattr(self, "btn_check"):
            self.btn_check.configure(state="disabled")
        self.progress_bar.set(0)
        self.status_label.configure(text="جاري العمل...")
        if getattr(self, "pause_btn", None) and self.pause_btn.winfo_exists():
            self.pause_btn.configure(text="Pause")

        self._open_progress_window_blind(len(contacts), mode="send")

        threading.Thread(
            target=self._run_automation,
            args=(contacts, msg_template, attachments),
            daemon=True
        ).start()


    def _start_action(self):
        """Show Sending Mode dialog, then proceed with the campaign."""
        self._show_sending_mode_dialog()

    def _schedule_action(self):
        """Opens a visual DateTime Picker dialog to schedule the campaign."""
        import tkinter as tk
        from tkinter import messagebox
        import datetime

        # 1. Prepare campaign content
        msg_template, attachments = self._prepare_content()
        if msg_template is None and attachments is None:
            return  # Error reported

        contacts = self._get_contacts_from_input()
        if not contacts:
            return

        dialog = ctk.CTkToplevel(self)
        dialog.title("📅 جدولة الحملة | Schedule Campaign")
        dialog.geometry("520x460")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()

        # Centre on parent
        x = self.winfo_x() + (self.winfo_width() - 520) // 2
        y = self.winfo_y() + (self.winfo_height() - 460) // 2
        dialog.geometry(f"+{x}+{y}")

        frm = ctk.CTkFrame(dialog, fg_color="transparent")
        frm.pack(fill="both", expand=True, padx=25, pady=20)

        # Title
        title = ctk.CTkLabel(frm, text="📅 جدولة الحملة الجديدة | Schedule New Campaign",
                             font=("Segoe UI", 16, "bold"), text_color=COLORS.get("primary", "#00E676"))
        title.pack(anchor="w", pady=(0, 15))

        # Campaign Name Entry
        ctk.CTkLabel(frm, text="اسم الحملة / Campaign Name:", font=("Segoe UI", 12)).pack(anchor="e", pady=(5, 2))
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        name_entry = ctk.CTkEntry(frm, height=36, placeholder_text=f"حملة مجدولة - {now_str}")
        name_entry.pack(fill="x", pady=(0, 10))

        # DateTime Selection Row
        picker_frame = ctk.CTkFrame(frm, fg_color="transparent")
        picker_frame.pack(fill="x", pady=10)

        # Year, Month, Day selectors
        now = datetime.datetime.now()
        
        # Day
        day_var = tk.StringVar(value=str(now.day))
        ctk.CTkLabel(picker_frame, text="اليوم / Day:", font=("Segoe UI", 11)).grid(row=0, column=4, padx=5, sticky="e")
        day_combo = ctk.CTkComboBox(picker_frame, width=70, values=[str(d) for d in range(1, 32)], variable=day_var)
        day_combo.grid(row=1, column=4, padx=5)

        # Month
        month_var = tk.StringVar(value=str(now.month))
        ctk.CTkLabel(picker_frame, text="الشهر / Month:", font=("Segoe UI", 11)).grid(row=0, column=3, padx=5, sticky="e")
        month_combo = ctk.CTkComboBox(picker_frame, width=75, values=[str(m) for m in range(1, 13)], variable=month_var)
        month_combo.grid(row=1, column=3, padx=5)

        # Year
        year_var = tk.StringVar(value=str(now.year))
        ctk.CTkLabel(picker_frame, text="السنة / Year:", font=("Segoe UI", 11)).grid(row=0, column=2, padx=5, sticky="e")
        year_combo = ctk.CTkComboBox(picker_frame, width=80, values=[str(now.year), str(now.year + 1)], variable=year_var)
        year_combo.grid(row=1, column=2, padx=5)

        # Hour
        hour_var = tk.StringVar(value=str(now.hour))
        ctk.CTkLabel(picker_frame, text="الساعة / Hour:", font=("Segoe UI", 11)).grid(row=0, column=1, padx=5, sticky="e")
        hour_combo = ctk.CTkComboBox(picker_frame, width=70, values=[str(h) for h in range(24)], variable=hour_var)
        hour_combo.grid(row=1, column=1, padx=5)

        # Minute
        minute_var = tk.StringVar(value=str(now.minute))
        ctk.CTkLabel(picker_frame, text="الدقيقة / Min:", font=("Segoe UI", 11)).grid(row=0, column=0, padx=5, sticky="e")
        minute_combo = ctk.CTkComboBox(picker_frame, width=70, values=[str(m) for m in range(60)], variable=minute_var)
        minute_combo.grid(row=1, column=0, padx=5)

        # Sending Mode selector
        ctk.CTkLabel(frm, text="وضع الإرسال / Sending Mode:", font=("Segoe UI", 12)).pack(anchor="e", pady=(15, 2))
        mode_var = tk.StringVar(value="safe")
        
        mode_frame = ctk.CTkFrame(frm, fg_color=COLORS.get("card_bg", "#1E293B"), corner_radius=8, height=45)
        mode_frame.pack(fill="x", pady=(0, 15))
        
        r_safe = ctk.CTkRadioButton(mode_frame, text="الوضع الآمن (Safe Mode)", variable=mode_var, value="safe")
        r_safe.pack(side="right", padx=15, pady=8)
        
        r_blind = ctk.CTkRadioButton(mode_frame, text="الوضع العشوائي (Blind Mode)", variable=mode_var, value="blind")
        r_blind.pack(side="left", padx=15, pady=8)

        # Action Buttons
        btn_frame = ctk.CTkFrame(frm, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(20, 0))

        btn_cancel = ctk.CTkButton(btn_frame, text="إلغاء | Cancel",
                                   font=("Segoe UI", 13, "bold"), width=130, height=38,
                                   fg_color=COLORS.get("danger", "#EF4444"),
                                   hover_color=COLORS.get("danger_hover", "#DC2626"),
                                   text_color="#FFFFFF",
                                   command=dialog.destroy)
        btn_cancel.pack(side="left", padx=(0, 10))

        def on_schedule():
            try:
                target_year = int(year_combo.get())
                target_month = int(month_combo.get())
                target_day = int(day_combo.get())
                target_hour = int(hour_combo.get())
                target_minute = int(minute_combo.get())
                
                target_dt = datetime.datetime(target_year, target_month, target_day, target_hour, target_minute)
            except ValueError:
                messagebox.showerror("خطأ", "التاريخ والوقت المحدد غير صالح.")
                return

            if target_dt <= datetime.datetime.now():
                messagebox.showerror("خطأ", "يرجى تحديد تاريخ ووقت في المستقبل.")
                return

            name = name_entry.get().strip()
            if not name:
                name = f"حملة مجدولة - {target_dt.strftime('%Y-%m-%d %H:%M')}"

            # If contacts is loaded from a group inside contacts_entry, get that group name
            c_input = self.contacts_entry.get().strip()
            group_name = None
            if c_input.startswith("[GROUP:") and c_input.endswith("]"):
                group_name = c_input[7:-1]

            # Save scheduled campaign in DB
            self.scheduler.schedule_campaign(
                name=name,
                scheduled_time=target_dt,
                message=msg_template,
                attachments=attachments,
                group_name=group_name,
                contacts=contacts if not group_name else None,
                sending_mode=mode_var.get()
            )

            dialog.destroy()
            messagebox.showinfo("تمت الجدولة", f"تمت جدولة الحملة '{name}' بنجاح في {target_dt.strftime('%Y-%m-%d %H:%M')}.")
            self.log(f"📅 تم جدولة حملة جديدة: {name} في {target_dt.strftime('%Y-%m-%d %H:%M')}")

        btn_ok = ctk.CTkButton(btn_frame, text="تأكيد الجدولة | Schedule",
                               font=("Segoe UI", 13, "bold"), width=150, height=38,
                               fg_color=COLORS.get("primary", "#00E676"),
                               hover_color=COLORS.get("primary_hover", "#00C853"),
                               text_color="#000000",
                               command=on_schedule)
        btn_ok.pack(side="right")

    def _show_sending_mode_dialog(self):
        """Premium campaign dispatch setup dialog. Select accounts, sending mode, and single/parallel dispatch."""
        import tkinter as tk
        from tkinter import messagebox

        dialog = ctk.CTkToplevel(self)
        dialog.title("🚀 تجهيز وإطلاق الحملة | Campaign Dispatch Setup")
        dialog.geometry("640x560")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()

        # Centre on parent
        x = self.winfo_x() + (self.winfo_width() - 640) // 2
        y = self.winfo_y() + (self.winfo_height() - 560) // 2
        dialog.geometry(f"+{x}+{y}")

        frm = ctk.CTkFrame(dialog, fg_color="transparent")
        frm.pack(fill="both", expand=True, padx=25, pady=20)

        # Title
        title = ctk.CTkLabel(frm, text="🚀 تجهيز وإطلاق الحملة | Campaign Dispatch Setup",
                             font=("Segoe UI", 16, "bold"), text_color=COLORS.get("primary", "#00E676"))
        title.pack(anchor="w", pady=(0, 15))

        # Main horizontal split
        split_frame = ctk.CTkFrame(frm, fg_color="transparent")
        split_frame.pack(fill="both", expand=True)
        split_frame.grid_columnconfigure(0, weight=1)
        split_frame.grid_columnconfigure(1, weight=1)

        # LEFT COLUMN: Sending Mode (Safe vs Blind)
        left_col = ctk.CTkFrame(split_frame, fg_color=COLORS.get("card_bg", "#1E293B"), corner_radius=10, border_width=1, border_color=COLORS.get("border", "#334155"))
        left_col.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")

        ctk.CTkLabel(left_col, text="⚙️ وضع الإرسال | Sending Mode", font=("Segoe UI", 13, "bold"), text_color=COLORS.get("primary", "#00E676")).pack(anchor="w", padx=15, pady=(12, 10))

        mode_var = tk.StringVar(value="safe")

        r_safe = ctk.CTkRadioButton(left_col, text="الوضع الآمن (Safe Mode)", variable=mode_var, value="safe", font=("Segoe UI", 12, "bold"))
        r_safe.pack(anchor="w", padx=20, pady=5)
        safe_desc = ctk.CTkLabel(left_col, text="فحص صلاحية الأرقام أولاً.\nتأخير آمن للحماية من الحظر.", font=("Segoe UI", 10), text_color=COLORS.get("text_muted", "#94A3B8"), justify="right", anchor="e")
        safe_desc.pack(anchor="w", padx=35, pady=(0, 12))

        r_blind = ctk.CTkRadioButton(left_col, text="الوضع العشوائي (Blind Mode)", variable=mode_var, value="blind", font=("Segoe UI", 12, "bold"))
        r_blind.pack(anchor="w", padx=20, pady=5)
        blind_desc = ctk.CTkLabel(left_col, text="إرسال فوري بدون فحص مسبق.\nأسرع بكثير لكن مخاطرة أعلى.", font=("Segoe UI", 10), text_color=COLORS.get("text_muted", "#94A3B8"), justify="right", anchor="e")
        blind_desc.pack(anchor="w", padx=35, pady=(0, 12))

        # RIGHT COLUMN: Active Profiles / Accounts
        right_col = ctk.CTkFrame(split_frame, fg_color=COLORS.get("card_bg", "#1E293B"), corner_radius=10, border_width=1, border_color=COLORS.get("border", "#334155"))
        right_col.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")

        ctk.CTkLabel(right_col, text="👥 الحسابات النشطة | Accounts", font=("Segoe UI", 13, "bold"), text_color=COLORS.get("primary", "#00E676")).pack(anchor="w", padx=15, pady=(12, 10))

        profiles_scroll = ctk.CTkScrollableFrame(right_col, height=180, fg_color="transparent")
        profiles_scroll.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        profiles = self._get_profiles()
        profile_vars = {}
        current_active = self.config.get("profile_name", "Default")

        for p in profiles:
            p_var = tk.BooleanVar(value=(p == current_active))
            chk = ctk.CTkCheckBox(profiles_scroll, text=f"👤 {p}", variable=p_var, font=("Segoe UI", 11))
            chk.pack(anchor="w", padx=10, pady=4)
            profile_vars[p] = p_var

        # Dispatch Mode Section
        dispatch_frame = ctk.CTkFrame(frm, fg_color=COLORS.get("card_bg", "#1E293B"), corner_radius=10, border_width=1, border_color=COLORS.get("border", "#334155"))
        dispatch_frame.pack(fill="x", pady=10)

        ctk.CTkLabel(dispatch_frame, text="⚡ طريقة التشغيل | Dispatch Execution Mode", font=("Segoe UI", 13, "bold"), text_color=COLORS.get("primary", "#00E676")).pack(anchor="w", padx=15, pady=(10, 5))

        dispatch_var = tk.StringVar(value="single")

        r_single = ctk.CTkRadioButton(dispatch_frame, text="إرسال فردي (Single / Sequential Mode)", variable=dispatch_var, value="single", font=("Segoe UI", 12))
        r_single.pack(anchor="w", padx=20, pady=4)

        r_parallel = ctk.CTkRadioButton(dispatch_frame, text="إرسال متوازي (Parallel Sending - تقسيم بالتساوي)", variable=dispatch_var, value="parallel", font=("Segoe UI", 12))
        r_parallel.pack(anchor="w", padx=20, pady=4)

        # Action Buttons
        btn_frame = ctk.CTkFrame(frm, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(15, 0))

        btn_cancel = ctk.CTkButton(btn_frame, text="إلغاء | Cancel",
                                   font=("Segoe UI", 13, "bold"), width=130, height=40,
                                   fg_color=COLORS.get("danger", "#EF4444"),
                                   hover_color=COLORS.get("danger_hover", "#DC2626"),
                                   text_color="#FFFFFF",
                                   command=dialog.destroy)
        btn_cancel.pack(side="left", padx=(0, 10))

        # Dynamic checkbox helper to set single vs parallel default
        def update_default_dispatch(*args):
            checked_count = sum(1 for p_var in profile_vars.values() if p_var.get())
            if checked_count > 1:
                dispatch_var.set("parallel")
            else:
                dispatch_var.set("single")

        for p_var in profile_vars.values():
            p_var.trace_add("write", update_default_dispatch)

        def on_ok():
            chosen_mode = mode_var.get()
            chosen_dispatch = dispatch_var.get()
            selected_profiles = [p for p, p_var in profile_vars.items() if p_var.get()]

            if not selected_profiles:
                messagebox.showerror("خطأ", "يرجى تحديد حساب إرسال واحد على الأقل.")
                return

            if chosen_dispatch == "parallel" and len(selected_profiles) < 2:
                messagebox.showwarning("تنبيه", "الإرسال بالتوازي يتطلب تحديد حسابين أو أكثر. تم التحويل التلقائي للوضع الفردي.")
                chosen_dispatch = "single"

            dialog.destroy()
            self._proceed_start_action(chosen_mode, chosen_dispatch, selected_profiles)

        btn_ok = ctk.CTkButton(btn_frame, text="بدء الحملة | Start",
                               font=("Segoe UI", 13, "bold"), width=150, height=40,
                               fg_color=COLORS.get("primary", "#00E676"),
                               hover_color=COLORS.get("primary_hover", "#00C853"),
                               text_color="#000000",
                               command=on_ok)
        btn_ok.pack(side="right")

    def _proceed_start_action(self, sending_mode="safe", dispatch_mode="single", selected_profiles=None):
        """Actually start the campaign after settings are selected."""
        self.sending_mode = sending_mode
        self.dispatch_mode = dispatch_mode
        self.selected_profiles = selected_profiles or [self.config.get("profile_name", "Default")]

        msg_template, attachments = self._prepare_content()
        if msg_template is None and attachments is None:
            return  # Error reported

        contacts = self._get_contacts_from_input()
        if not contacts:
            return
        if not self._check_campaign_safety(len(contacts), attachments):
            return
        if not self._warn_media_send_settings(attachments):
            return

        self._save_current_state()

        if dispatch_mode == "parallel":
            self.log(f"👥 تم بدء الحملة بالتوازي باستخدام {len(self.selected_profiles)} حسابات: {', '.join(self.selected_profiles)}")
            self._begin_parallel_send(contacts, msg_template, attachments)
        else:
            # Single Account Mode
            # Set the active profile to the single selected profile
            profile = self.selected_profiles[0]
            if profile != self.config.get("profile_name", "Default"):
                self._run_on_ui(lambda p=profile: self._on_profile_change(p))
            
            # Check Bot & Login
            if not self.bot or not self.bot.driver:
                auto_open = self.config.get("auto_open_login", True)
                if auto_open or messagebox.askyesno("تنبيه", "المتصفح غير مفتوح. هل تريد فتحه الآن؟"):
                    self.pending_start_payload = (contacts, msg_template, attachments)
                    self._set_session_status("الحالة: جاري فتح المتصفح...", COLORS["info"])
                    self._login_action()
                return

            if not self.bot.is_logged_in():
                self.bot.bring_to_front()
                self.report_error("ERR-21", dialog=True, level="warning")
                return

            self._set_session_status("الحالة: متصل", COLORS["success"])
            self._begin_send(contacts, msg_template, attachments)    
        # 3. Check Bot & Login
        if not self.bot or not self.bot.driver:
            auto_open = self.config.get("auto_open_login", True)
            if auto_open or messagebox.askyesno("تنبيه", "المتصفح غير مفتوح. هل تريد فتحه الآن؟"):
                self.pending_start_payload = (contacts, msg_template, attachments)
                self._set_session_status("الحالة: جاري فتح المتصفح...", COLORS["info"])
                self._login_action()
            return

        if not self.bot.is_logged_in():
            self.bot.bring_to_front()
            self.report_error("ERR-21", dialog=True, level="warning")
            return

        self._set_session_status("الحالة: متصل", COLORS["success"])
        self._begin_send(contacts, msg_template, attachments)

    def _stop_action(self):
        """Stop the running automation by setting the stop event."""
        if messagebox.askyesno("تأكيد", "هل تريد إيقاف العملية؟"):
            self.stop_event.set()
            if self.pause_event.is_set():
                self.pause_event.clear()
                self.is_paused = False
                if getattr(self, "pause_btn", None) and self.pause_btn.winfo_exists():
                    self.pause_btn.configure(text="Pause")
            self.log("🛑 طلب إيقاف...")

    def _check_numbers_action(self, contacts_override=None):
        """Start the number validity checking process."""
        if self.is_running or self.is_checking:
            return
        contacts = contacts_override or self._get_contacts_from_input()
        if not contacts:
            return

        if not self.bot or not self.bot.driver:
            auto_open = self.config.get("auto_open_login", True)
            if auto_open or messagebox.askyesno("تنبيه", "المتصفح غير مفتوح. هل تريد فتحه الآن؟"):
                self.pending_check_contacts = contacts
                self._set_session_status("الحالة: جاري فتح المتصفح...", COLORS["info"])
                self._login_action()
            return

        if not self.bot.is_logged_in():
            self.bot.bring_to_front()
            self.report_error("ERR-21", dialog=True, level="warning")
            return

        self._set_session_status("الحالة: متصل", COLORS["success"])
        self.is_checking = True
        self.stop_event.clear()
        self.btn_start.configure(state="disabled")
        self.btn_check.configure(state="disabled")
        self.btn_stop.configure(state="normal")
        self.progress_bar.set(0)
        self._open_progress_window_blind(len(contacts), mode="check")
        self.status_label.configure(text="جاري فحص الأرقام...")

        threading.Thread(
            target=self._run_number_check,
            args=(contacts,),
            daemon=True
        ).start()

    def _warn_media_send_settings(self, attachments):
        """Advise user before campaigns with media attachments."""
        if not attachments:
            return True
        if getattr(self, "send_text_var", None) and self.send_text_var.get():
            self.send_text_var.set(False)
            self.log(
                "ℹ️ تم إلغاء «الوضع المدمج» تلقائياً — سيتم إرسال الصورة ثم النص منفصلين (أكثر استقراراً).",
                level="INFO",
            )
        if getattr(self, "bg_mode_var", None) and self.bg_mode_var.get():
            messagebox.showwarning(
                "وضع الخلفية",
                "مع المرفقات (صور/فيديو) يُفضّل إيقاف «وضع الخلفية» "
                "وإبقاء نافذة واتساب ظاهرة لتقليل فشل الإرفاق والنقر.",
            )
        return True

    def _recover_bot_before_retry(self, attachments):
        """Attempt to recover the bot state before retrying a failed send."""
        if not self.bot:
            return
        try:
            if attachments and hasattr(self.bot, "recover_compose_state"):
                self.bot.recover_compose_state(stop_event=self.stop_event)
            if attachments and not self.bg_mode_var.get():
                self.bot.bring_to_front()
        except Exception as exc:
            logger.debug("Could not recover bot before retry: %s", exc)

    def _map_bot_error(self, res):
        """Map a bot error code to a user-friendly message."""
        if not res:
            return "ERR-99", "خطأ غير معروف.", None
        if str(res).startswith("ERR_TEXT_SEND"):
            detail = res.split(":", 1)[1].strip() if ":" in res else ""
            tip = (
                "تأكد من إغلاق معاينة الصورة/قائمة الإرفاق، وإبقاء نافذة واتساب ظاهرة "
                "(لا تستخدم وضع الخلفية مع الوسائط)."
            )
            return "ERR-07", "فشل إرسال النص بعد المرفق.", f"{detail} — {tip}" if detail else tip
        if res.startswith("ERR_IMAGE_FLOW:"):
            detail = res.split(":", 1)[1].strip()
            return "ERR-08", "فشل إرسال الصورة.", detail
        if res.startswith("ERR_ATTACH_"):
            parts = res.split(":", 1)
            atype = parts[0].replace("ERR_ATTACH_", "")
            detail = parts[1].strip() if len(parts) > 1 else ""
            return "ERR-08", f"فشل إرفاق ملف ({atype}).", detail
        if res.startswith("ERR_GENERAL:"):
            detail = res.split(":", 1)[1].strip()
            if "timeout" in detail.lower():
                return "ERR-10", "انتهت مهلة تحميل المحادثة.", detail
            return "ERR-99", "خطأ غير متوقع أثناء المعالجة.", detail
        mapping = {
            "ERR_NOT_READY":               ("ERR-01", "المتصفح غير جاهز.", None),
            "ERR_EMPTY_MESSAGE":           ("ERR-04", "لا يوجد نص للإرسال.", None),
            "ERR_CHAT_INPUT_NOT_FOUND":    ("ERR-07", "صندوق كتابة الرسالة غير موجود.", None),
            "ERR_ATTACH_BTN_NOT_FOUND":    (
                "ERR-06",
                "زر الإرفاق (+) غير ظاهر في التذييل.",
                "انتظر تحميل المحادثة، أغلق البحث/المعاينة، وأبقِ نافذة واتساب مفتوحة.",
            ),
            "ERR_FILE_INPUT_NOT_FOUND":    ("ERR-08", "حقل رفع الصورة غير موجود.", None),
            "ERR_CAPTION_BOX_NOT_FOUND":   ("ERR-08", "صندوق كتابة الكابشن غير موجود.", None),
            "ERR_FINAL_SEND_BTN_NOT_FOUND":("ERR-07", "زر الإرسال النهائي لم يظهر.", None),
            "ERR_SEND_BTN_TIMEOUT":        ("ERR-07", "زر الإرسال لم يظهر في الوقت المحدد.", None),
            "ERR_TIMEOUT":                 ("ERR-10", "انتهت مهلة تحميل المحادثة.", None),
        }
        return mapping.get(res, ("ERR-99", f"خطأ غير معروف ({res})", None))

    # ═══════════════════════════════════════════════════════════════════════
    #  MAIN AUTOMATION LOOP
    # ═══════════════════════════════════════════════════════════════════════

    def _run_automation(self, contacts, msg_template, attachments):
        """Main automation loop: iterate contacts and send messages."""
        if not self.bot:
            return

        self.sent = 0
        self.failed = 0
        self.invalid = 0
        self.results_log = []
        
        total = len(contacts)
        start_time = datetime.datetime.now()

        try:
            # Batch settings
            try:
                batch_size = int(self.batch_size_entry.get())
                pause_min = int(self.batch_min_entry.get())
                pause_max = int(self.batch_max_entry.get())
                delay_min = int(self.delay_min_entry.get())
                delay_max = int(self.delay_max_entry.get())
                max_retries = int(self.config.get("max_retries", 2))
                retry_delay_min = int(self.config.get("retry_delay_min", 3))
                retry_delay_max = int(self.config.get("retry_delay_max", 6))
                max_consecutive_failures = int(self.config.get("max_consecutive_failures", 5))
            except ValueError:
                batch_size, pause_min, pause_max, delay_min, delay_max = 30, 60, 120, 30, 120
                max_retries, retry_delay_min, retry_delay_max, max_consecutive_failures = 1, 3, 6, 5

            self.log(f"🚀 بدء إرسال {total} رسالة...")
            consecutive_failures = 0
            retryable_errors = {
                "ERR_TIMEOUT",
                "ERR_CHAT_INPUT_NOT_FOUND",
                "ERR_ATTACH_BTN_NOT_FOUND",
                "ERR_FILE_INPUT_NOT_FOUND",
                "ERR_STICKER_PANEL_OPENED",
                "ERR_SEND_BTN_NOT_FOUND",
                "ERR_SEND_BTN_TIMEOUT",
                "ERR_TEXT_SEND",
            }
            attach_only_errors = {
                "ERR_FILE_INPUT_NOT_FOUND",
                "ERR_STICKER_PANEL_OPENED",
                "ERR_DOC_BTN_NOT_FOUND",
                "ERR_PHOTO_BTN_NOT_FOUND",
            }
            retry_full_navigation = bool(self.config.get("retry_full_navigation", False))

            for i, c in enumerate(contacts):
                if self.stop_event.is_set():
                    break
                while self.pause_event.is_set() and not self.stop_event.is_set():
                    self.stop_event.wait(0.3)

                # Batch pause (interruptible)
                if i > 0 and i % batch_size == 0:
                    pause_time = random.uniform(pause_min, pause_max)
                    self.log(f"⏸ استراحة لمدة {int(pause_time)} ثانية...")
                    if self.stop_event.wait(pause_time):
                        break

                # Account Rotation Logic
                rotation_enabled = self.config.get("rotation_enabled", False)
                try:
                    rotation_interval = int(self.config.get("rotation_interval", 50))
                except ValueError:
                    rotation_interval = 50

                if rotation_enabled and i > 0 and i % rotation_interval == 0:
                    self.log("🔄 التبديل التلقائي للحساب التالي (تدوير الحسابات)...")
                    profiles = self._get_profiles()
                    current_profile = self.config.get("profile_name", "Default")
                    if profiles and len(profiles) > 1:
                        try:
                            curr_idx = profiles.index(current_profile)
                            next_idx = (curr_idx + 1) % len(profiles)
                        except ValueError:
                            next_idx = 0
                        next_profile = profiles[next_idx]
                        self.log(f"🔄 التبديل من حساب {current_profile} إلى {next_profile}...")
                        self._run_on_ui(lambda p=next_profile: self._on_profile_change(p))
                        
                        try:
                            if self.bot:
                                self.bot.close()
                        except Exception as exc:
                            logger.debug("Could not close bot during profile rotation: %s", exc)
                        
                        # Wait a bit before opening the new one
                        if self.stop_event.wait(2.0):
                            break

                        # We need to wait for _on_profile_change to actually execute on UI thread
                        if self.stop_event.wait(1.0):
                            break

                        # Start new bot
                        proxy_config = self.config.get("profile_proxies", {}).get(next_profile)
                        from automation.bot import WhatsAppBot
                        self.bot = WhatsAppBot(
                            self.user_data_dir,
                            proxy_config,
                            on_event=self._on_bot_event,
                        )
                        self.bot.setup_driver(start_minimized=self.bg_mode_var.get())
                        self.bot.open_whatsapp()
                        self.log("⏳ انتظار تسجيل الدخول للحساب الجديد...")
                        if not self.bot.wait_for_login():
                            self.log("❌ فشل تسجيل الدخول للحساب الجديد. سيتم إيقاف الإرسال.")
                            self.stop_event.set()
                            break
                        self.log("✅ تم الدخول بنجاح. استئناف الإرسال...")
                    else:
                        self.log("⚠️ إعداد التدوير مفعل، لكن لا يوجد حسابات أخرى محفوظة للتبديل إليها.")

                phone = c.get("phone")
                name = c.get("name", "عميل")
                
                processed = i + 1
                self._run_on_ui(lambda p=processed, t=total, n=name: self.status_label.configure(text=f"جاري إرسال {p}/{t} إلى {n}..."))
                self._run_on_ui(lambda p=processed, t=total: self.progress_bar.set(p / t))
                elapsed = (datetime.datetime.now() - start_time).total_seconds()
                eta = None
                if processed > 0 and total > processed:
                    eta = (elapsed / processed) * (total - processed)
                self._update_progress_header_blind(processed, total, phone, name, eta)

                # Mark row as sending in the Treeview table live!
                tree_item_id = c.get("tree_item_id")
                if tree_item_id:
                    self._run_on_ui(lambda item=tree_item_id, n=name, ph=phone, v=c.get("var1", ""): self.progress_tree.item(item, values=(n, ph, v, "🔄 إرسال..."), tags=("sending",)))

                if not phone:
                    self.invalid += 1
                    self.results_log.append({"phone": "N/A", "name": name, "status": "INVALID", "error_code": "ERR-00", "timestamp": datetime.datetime.now()})
                    self._add_progress_row_blind(["N/A", name, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "بدون رقم", "بيانات الرقم ناقصة"], tag="invalid")
                    self._run_on_ui(self._update_stats)
                    self._update_progress_header_blind(processed, total, phone, name, eta)
                    if tree_item_id:
                        self._run_on_ui(lambda item=tree_item_id, n=name, v=c.get("var1", ""): self.progress_tree.item(item, values=(n, "N/A", v, "🚫 بدون رقم"), tags=("invalid",)))
                    continue

                # Ensure still logged in
                if not self.bot.is_logged_in():
                    self.report_error("ERR-21", dialog=True, level="warning")
                    if tree_item_id:
                        self._run_on_ui(lambda item=tree_item_id, n=name, ph=phone, v=c.get("var1", ""): self.progress_tree.item(item, values=(n, ph, v, "⏳ معلق"), tags=("pending",)))
                    break

                # Prepare personalized content
                msg_for_contact = self._apply_template(msg_template, c)
                atts_for_contact = self._format_attachments_for_contact(attachments, c)
                segments = self._split_messages(msg_for_contact)
                primary_msg = segments[0] if segments else msg_for_contact
                extra_msgs = segments[1:] if segments else []

                # Send Message + Attachments with retries
                res = None
                for attempt in range(max_retries + 1):
                    skip_nav = (
                        attempt > 0
                        and atts_for_contact
                        and not retry_full_navigation
                        and res in attach_only_errors
                    )
                    res = self.bot.send_message(
                        phone=phone,
                        name=name,
                        message_template=primary_msg,
                        extra_messages=extra_msgs,
                        attachments=atts_for_contact,
                        stop_event=self.stop_event,
                        send_text_with_image=self.send_text_var.get(),
                        skip_open_chat=skip_nav,
                    )
                    if res in ("SUCCESS", "INVALID", "STOPPED"):
                        break
                    is_retryable = (
                        res in retryable_errors
                        or str(res).startswith("ERR_ATTACH_")
                        or str(res).startswith("ERR_TEXT_SEND")
                        or str(res).startswith("ERR_GENERAL")
                    )
                    if attempt < max_retries and is_retryable:
                        wait_s = random.uniform(retry_delay_min, retry_delay_max)
                        retry_mode = "مرفق فقط" if skip_nav else "كامل"
                        self.log(f"🔁 إعادة محاولة ({attempt + 1}/{max_retries}) [{retry_mode}] بعد {int(wait_s)}ث | {phone} | {res}")
                        self._recover_bot_before_retry(atts_for_contact)
                        if self.stop_event.wait(wait_s):
                            break
                        continue
                    break
                
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                if res == "SUCCESS":
                    self.sent += 1
                    self.log(f"✅ تم الإرسال لـ {name}")
                    self.results_log.append({"phone": phone, "name": name, "status": "نجاح", "error_code": "-", "timestamp": timestamp})
                    self._add_progress_row_blind([phone, name, timestamp, "تم", "تم الإرسال"], tag="success")
                    consecutive_failures = 0
                    if tree_item_id:
                        self._run_on_ui(lambda item=tree_item_id, n=name, ph=phone, v=c.get("var1", ""): self.progress_tree.item(item, values=(n, ph, v, "✅ نجاح"), tags=("success",)))
                elif res == "INVALID":
                    self.invalid += 1
                    self.log(f"⏭️ تخطي {phone} — الرقم غير مسجل على واتساب (تم إغلاق النافذة تلقائياً).")
                    self.results_log.append({"phone": phone, "name": name, "status": "بدون واتساب", "error_code": "ERR-20", "timestamp": timestamp})
                    self._add_progress_row_blind([phone, name, timestamp, "بدون واتساب", "غير موجود على واتساب — تم التخطي"], tag="invalid")
                    consecutive_failures = 0
                    if tree_item_id:
                        self._run_on_ui(lambda item=tree_item_id, n=name, ph=phone, v=c.get("var1", ""): self.progress_tree.item(item, values=(n, ph, v, "🚫 غير صالح"), tags=("invalid",)))
                elif res == "STOPPED":
                    self.results_log.append({"phone": phone, "name": name, "status": "توقف", "error_code": "-", "timestamp": timestamp})
                    self._add_progress_row_blind([phone, name, timestamp, "توقف", "تم إيقاف العملية"], tag="stopped")
                    if tree_item_id:
                        self._run_on_ui(lambda item=tree_item_id, n=name, ph=phone, v=c.get("var1", ""): self.progress_tree.item(item, values=(n, ph, v, "⚠️ توقف"), tags=("pending",)))
                    break
                else:
                    self.failed += 1
                    err_code = res if res.startswith("ERR") else "ERR-UNKNOWN"
                    self.log(f"❌ فشل: {phone} | {res}")
                    self.results_log.append({"phone": phone, "name": name, "status": "فشل", "error_code": err_code, "timestamp": timestamp})
                    self._add_progress_row_blind([phone, name, timestamp, "فشل", str(res)], tag="failed")
                    consecutive_failures += 1
                    if tree_item_id:
                        self._run_on_ui(lambda item=tree_item_id, n=name, ph=phone, v=c.get("var1", ""): self.progress_tree.item(item, values=(n, ph, v, "❌ فشل"), tags=("failed",)))
                    if consecutive_failures >= max_consecutive_failures:
                        self.log(f"⛔ تم الإيقاف تلقائياً بعد {consecutive_failures} فشل متتالي لتقليل المخاطر.")
                        self.stop_event.set()
                        break

                self._run_on_ui(self._update_stats)
                self._update_progress_header_blind(processed, total, phone, name, eta)
                
                # Delay (interruptible)
                # Human-like delay: mostly fast, occasionally slower to avoid detection
                d_fast = random.uniform(delay_min * 0.3, delay_min * 0.7)
                d_mid = random.uniform(delay_min * 0.7, (delay_min + delay_max) / 2)
                d_slow = random.uniform((delay_min + delay_max) / 2, delay_max)
                chosen_delay = random.choices([d_fast, d_mid, d_slow], weights=[70, 20, 10], k=1)[0]
                if self.stop_event.wait(chosen_delay):
                    break

            end_time = datetime.datetime.now()
            duration = end_time - start_time
            
            # Save Campaign
            csv_path = self._generate_final_report(duration)
            self.last_report_path = csv_path
            
            # Save to history
            self.campaign_manager.add_campaign(
                name=f"Campaign {start_time.strftime('%Y-%m-%d %H:%M')}",
                total=total,
                sent=self.sent,
                failed=self.failed,
                invalid=self.invalid,
                duration_seconds=int(duration.total_seconds()),
                results_log=self.results_log,
                csv_path=csv_path
            )
            try:
                if self.bg_mode_var.get():
                    self.bot.minimize()
                else:
                    self.bot.bring_to_front()
            except Exception as exc:
                logger.debug("Could not restore browser window state after campaign: %s", exc)

            if self.stop_event.is_set():
                self.log("🛑 تم إيقاف العملية.")
            else:
                self.log("🏁 انتهت العملية.")
                self._run_on_ui(lambda: self.progress_bar.set(1.0))

        except Exception as e:
            self.log(f"⚠️ [ERR-99] خطأ غير متوقع في خيط الإرسال: {e}")
        finally:
            self.is_running = False
            self.pause_event.clear()
            self.is_paused = False
            self._run_on_ui(lambda: self.btn_start.configure(state="normal"))
            self._run_on_ui(lambda: self.btn_stop.configure(state="disabled"))
            if hasattr(self, "btn_check"):
                self._run_on_ui(lambda: self.btn_check.configure(state="normal"))
            if getattr(self, "pause_btn", None):
                self._run_on_ui(lambda: self.pause_btn.configure(text="Pause") if getattr(self, "pause_btn", None) and self.pause_btn.winfo_exists() else None)
            self._run_on_ui(lambda: self.status_label.configure(text="جاهز..."))

    def _run_number_check(self, contacts):
        """Check phone number validity via WhatsApp."""
        if not self.bot:
            return
        self.sent = 0
        self.failed = 0
        self.invalid = 0
        self.results_log = []

        total = len(contacts)
        start_time = datetime.datetime.now()

        try:
            self.log(f"🔍 بدء فحص {total} رقم...")

            for i, c in enumerate(contacts):
                if self.stop_event.is_set():
                    break
                phone = c.get("phone")
                name = c.get("name", "عميل")

                processed = i + 1
                self._run_on_ui(lambda p=processed, t=total, n=name: self.status_label.configure(text=f"فحص {p}/{t} - {n}"))
                self._run_on_ui(lambda p=processed, t=total: self.progress_bar.set(p / t))
                elapsed = (datetime.datetime.now() - start_time).total_seconds()
                eta = None
                if processed > 0 and total > processed:
                    eta = (elapsed / processed) * (total - processed)
                self._update_progress_header_blind(processed, total, phone, name, eta)

                if not phone:
                    self.invalid += 1
                    self.results_log.append({"phone": "N/A", "name": name, "status": "غير صالح", "error_code": "ERR-00", "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
                    self._add_progress_row_blind(["N/A", name, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "بدون رقم", "بيانات الرقم ناقصة"], tag="invalid")
                    self._run_on_ui(self._update_stats)
                    self._update_progress_header_blind(processed, total, phone, name, eta)
                    continue

                res = self.bot.check_number(phone=phone, stop_event=self.stop_event)
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                if res == "VALID":
                    self.sent += 1
                    self.log(f"✅ صالح: {phone} | {name}")
                    self.results_log.append({"phone": phone, "name": name, "status": "صالح", "error_code": "-", "timestamp": timestamp})
                    self._add_progress_row_blind([phone, name, timestamp, "عنده واتساب", "صالح للإرسال"], tag="success")
                elif res == "INVALID":
                    self.invalid += 1
                    self.log(f"🚫 غير صالح: {phone}")
                    self.results_log.append({"phone": phone, "name": name, "status": "غير صالح", "error_code": "ERR-20", "timestamp": timestamp})
                    self._add_progress_row_blind([phone, name, timestamp, "بدون واتساب", "الرقم غير صالح أو لا يستخدم واتساب"], tag="invalid")
                elif res == "STOPPED":
                    self.results_log.append({"phone": phone, "name": name, "status": "توقف", "error_code": "-", "timestamp": timestamp})
                    self._add_progress_row_blind([phone, name, timestamp, "توقف", "تم إيقاف الفحص"], tag="stopped")
                    break
                else:
                    self.failed += 1
                    self.log(f"⚠️ تعذر الفحص: {phone} | {res}")
                    self.results_log.append({"phone": phone, "name": name, "status": "فشل", "error_code": res, "timestamp": timestamp})
                    self._add_progress_row_blind([phone, name, timestamp, "فشل", str(res)], tag="failed")

                self._run_on_ui(self._update_stats)
                self._update_progress_header_blind(processed, total, phone, name, eta)
                if self.stop_event.wait(random.uniform(1.5, 3.0)):
                    break

            report_path, valid_path, invalid_path = self._save_number_check_report()
            if self.stop_event.is_set():
                self.log("🛑 تم إيقاف الفحص.")
            else:
                self.log("🏁 انتهى فحص الأرقام.")
                if report_path:
                    self.log(f"📄 تقرير الفحص: {report_path}")
                if valid_path:
                    self.log(f"✅ ملف الأرقام الصالحة: {valid_path}")
                if invalid_path:
                    self.log(f"🚫 ملف الأرقام غير الصالحة: {invalid_path}")
                if valid_path and hasattr(self, "use_valid_after_check_var") and self.use_valid_after_check_var.get():
                    self.contacts_entry.delete(0, "end")
                    self.contacts_entry.insert(0, valid_path)
                    self._update_total_counts(total=self.sent, contacts_count=self.sent, groups_count=0)
                    self.log("✨ تم تعيين ملف الأرقام الصالحة كملف الإرسال الحالي.")

        except Exception as e:
            self.log(f"⚠️ [ERR-99] خطأ غير متوقع في خيط فحص الأرقام: {e}")
        finally:
            self.is_checking = False
            self.stop_event.clear()
            self._run_on_ui(lambda: self.btn_start.configure(state="normal"))
            self._run_on_ui(lambda: self.btn_check.configure(state="normal"))
            self._run_on_ui(lambda: self.btn_stop.configure(state="disabled"))
            self._run_on_ui(lambda: self.status_label.configure(text="جاهز..."))

    def _toggle_pause(self):
        """Toggle pause/resume of the running automation."""
        if not self.is_running:
            return
        if self.is_paused:
            self.pause_event.clear()
            self.is_paused = False
            if getattr(self, "pause_btn", None) and self.pause_btn.winfo_exists():
                self.pause_btn.configure(text="Pause")
            self._set_progress_status("Resumed...")
        else:
            self.pause_event.set()
            self.is_paused = True
            if getattr(self, "pause_btn", None) and self.pause_btn.winfo_exists():
                self.pause_btn.configure(text="Resume")
            self._set_progress_status("Paused")

    def _set_progress_status(self, text):
        """Update the progress window status text."""
        def _do():
            if self.progress_status_label:
                self.progress_status_label.configure(text=text)
        self._run_on_ui(_do)


    # ═══════════════════════════════════════════════════════════════════════
    #  BOT ACTIONS
    # ═══════════════════════════════════════════════════════════════════════

    def _close_progress_window(self):
        """Close and clean up the progress window."""
        if self.is_running or self.is_checking:
            if messagebox.askyesno("تأكيد", "عملية الإرسال/الفحص لا تزال جارية. هل تريد إيقاف العملية وإغلاق هذه الشاشة؟"):
                self.stop_event.set()
                if self.pause_event.is_set():
                    self.pause_event.clear()
                    self.is_paused = False
                self.log("🛑 طلب إيقاف وإغلاق من شاشة المتابعة...")
            else:
                return  # Do not close

        if self.progress_win and self.progress_win.winfo_exists():
            try:
                self.progress_win.destroy()
            except Exception as exc:
                logger.debug("Could not destroy progress window: %s", exc)
        self.progress_win = None
        self.popup_progress_tree = None
        self.progress_count_label = None
        self.progress_status_label = None
        self.progress_bar_small = None
        self.progress_state_label = None
        self.progress_metric_labels = {}
        self.pause_btn = None

    def _export_last_report(self):
        """Open the last generated report file."""
        if self.last_report_path and os.path.exists(self.last_report_path):
            self._open_csv(self.last_report_path)
        else:
            messagebox.showinfo("تنبيه", "لا يوجد تقرير للتصدير بعد.")

    def _run_scheduled_campaign_callback(
        self,
        campaign_name: str,
        contacts: list,
        message: str,
        attachments: list,
        sending_mode: str
    ) -> bool:
        """Callback triggered when a scheduled campaign is due in the background."""
        import time
        self.sending_mode = sending_mode
        self._run_on_ui(lambda: self.log(f"⏰ بدء تشغيل الحملة المجدولة تلقائياً: {campaign_name}"))
        
        # Check if already running a task
        if self.is_running or self.is_checking:
            self._run_on_ui(
                lambda: self.log(f"⚠️ تعذر تشغيل الحملة المجدولة {campaign_name} لأن هناك عملية جارية حالياً.")
            )
            return False

        # Open browser automatically if closed
        if not self.bot or not self.bot.driver:
            self._run_on_ui(lambda: self.log("🌐 فتح المتصفح تلقائياً لتسجيل الدخول للحملة المجدولة..."))
            self.pending_start_payload = (contacts, message, attachments)
            self._run_on_ui(self._login_action)
            
            # Wait up to 3 minutes for user to login
            for _ in range(180):
                if self.stop_event.is_set():
                    return False
                time.sleep(1.0)
                if self.bot and self.bot.is_logged_in():
                    break
            else:
                self._run_on_ui(lambda: self.log("❌ انتهت مهلة انتظار تسجيل الدخول. تم إلغاء الحملة المجدولة."))
                return False

        # Start campaign
        self._run_on_ui(lambda: self._begin_send(contacts, message, attachments))
        
        # Wait until done
        while self.is_running:
            time.sleep(1.0)
            
        return self.failed == 0

    def _begin_parallel_send(self, contacts, msg_template, attachments):
        """Prepare and launch the parallel multi-account automation threads."""
        if self.is_running:
            return

        self.is_running = True
        self.stop_event.clear()
        self.pause_event.clear()
        self.is_paused = False

        self.sent = 0
        self.failed = 0
        self.invalid = 0
        self.results_log = []

        self.btn_start.configure(state="disabled")
        self.btn_stop.configure(state="normal")
        if hasattr(self, "btn_check"):
            self.btn_check.configure(state="disabled")
        self.progress_bar.set(0)
        self.status_label.configure(text="جاري التشغيل بالتوازي...")

        # Open Parallel Progress Monitor Dashboard
        self._open_parallel_progress_window(self.selected_profiles, len(contacts))

        # Chunk contacts
        num_bots = len(self.selected_profiles)
        chunk_size = (len(contacts) + num_bots - 1) // num_bots
        
        self.parallel_stats = {}
        self.active_bots = {}

        # Log launch
        self.log(f"🚀 بدء تقسيم {len(contacts)} رقم على {num_bots} حسابات بالتوازي...")

        # Spawn threads
        threads = []
        for idx, p in enumerate(self.selected_profiles):
            chunk = contacts[idx * chunk_size : (idx + 1) * chunk_size]
            self.parallel_stats[p] = {
                "sent": 0,
                "failed": 0,
                "invalid": 0,
                "processed": 0,
                "total": len(chunk),
                "status": "تجهيز المتصفح..."
            }
            
            t = threading.Thread(
                target=self._run_parallel_bot_worker,
                args=(p, chunk, msg_template, attachments),
                daemon=True
            )
            threads.append(t)
            t.start()

        # Monitor thread to aggregate final results when all finish
        threading.Thread(
            target=self._monitor_parallel_campaign,
            args=(threads, len(contacts)),
            daemon=True
        ).start()

    def _run_parallel_bot_worker(self, profile, chunk, msg_template, attachments):
        """Worker thread running a single WhatsAppBot instance for a chunk of contacts."""
        if not chunk:
            self._update_parallel_bot_card(profile, "🏁 مكتمل (لا توجد أرقام)", 0, 0, 0, 0, 0)
            self._add_parallel_progress_row(profile, "-", "-", datetime.datetime.now().strftime("%H:%M:%S"), "مكتمل", "لا توجد جهات اتصال مخصصة لهذا الحساب.", "success")
            return

        from automation.bot import WhatsAppBot
        
        # Load profile proxy
        profile_proxies = self.config.get("profile_proxies", {})
        proxy_config = profile_proxies.get(profile, {"enabled": False})
        
        if profile != "Legacy":
            user_data_dir = os.path.join(self.profiles_dir, profile)
        else:
            user_data_dir = self.legacy_profile_dir

        # Initialize Bot
        bot = None
        try:
            bot = WhatsAppBot(
                user_data_dir=user_data_dir,
                proxy_config=proxy_config,
                on_event=None
            )
            self.active_bots[profile] = bot
            
            # Setup Selenium
            bot.setup_driver(start_minimized=self.bg_mode_var.get())
            self._update_parallel_bot_card(profile, "جاري فتح واتساب ويب...", 0, 0, 0, 0, len(chunk))
            bot.open_whatsapp()
            
            # Wait for Login
            self._update_parallel_bot_card(profile, "⏳ انتظار تسجيل الدخول...", 0, 0, 0, 0, len(chunk))
            self._add_parallel_progress_row(profile, "-", "-", datetime.datetime.now().strftime("%H:%M:%S"), "انتظار", "يرجى مسح الرمز QR في نافذة المتصفح المفتوحة.", "waiting")
            
            login_status = bot.wait_for_login(timeout=900)
            if login_status != "SUCCESS":
                status_txt = "فشل تسجيل الدخول" if login_status == "TIMEOUT" else "تم الإغلاق"
                self._update_parallel_bot_card(profile, f"❌ {status_txt}", 0, 0, 0, 0, len(chunk))
                self._add_parallel_progress_row(profile, "-", "-", datetime.datetime.now().strftime("%H:%M:%S"), "فشل", f"تعذر الاتصال بالحساب: {status_txt}", "failed")
                return

            self._update_parallel_bot_card(profile, "✅ متصل — جاري بدء الإرسال", 0, 0, 0, 0, len(chunk))
            self._add_parallel_progress_row(profile, "-", "-", datetime.datetime.now().strftime("%H:%M:%S"), "متصل", "تم تسجيل الدخول بنجاح. بدء إرسال الرسائل...", "success")

            # Load Batch & Delay parameters
            try:
                batch_size = int(self.batch_size_entry.get())
                pause_min = int(self.batch_min_entry.get())
                pause_max = int(self.batch_max_entry.get())
                delay_min = int(self.delay_min_entry.get())
                delay_max = int(self.delay_max_entry.get())
                max_retries = int(self.config.get("max_retries", 2))
                retry_delay_min = int(self.config.get("retry_delay_min", 3))
                retry_delay_max = int(self.config.get("retry_delay_max", 6))
                max_consecutive_failures = int(self.config.get("max_consecutive_failures", 5))
            except ValueError:
                batch_size, pause_min, pause_max, delay_min, delay_max = 30, 60, 120, 30, 120
                max_retries, retry_delay_min, retry_delay_max, max_consecutive_failures = 1, 3, 6, 5

            consecutive_failures = 0
            retryable_errors = {
                "ERR_TIMEOUT", "ERR_CHAT_INPUT_NOT_FOUND", "ERR_ATTACH_BTN_NOT_FOUND",
                "ERR_FILE_INPUT_NOT_FOUND", "ERR_STICKER_PANEL_OPENED", "ERR_SEND_BTN_NOT_FOUND",
                "ERR_SEND_BTN_TIMEOUT", "ERR_TEXT_SEND"
            }
            attach_only_errors = {"ERR_FILE_INPUT_NOT_FOUND", "ERR_STICKER_PANEL_OPENED", "ERR_DOC_BTN_NOT_FOUND", "ERR_PHOTO_BTN_NOT_FOUND"}
            retry_full_navigation = bool(self.config.get("retry_full_navigation", False))

            sent_count = 0
            failed_count = 0
            invalid_count = 0

            for i, c in enumerate(chunk):
                if self.stop_event.is_set():
                    break
                while self.pause_event.is_set() and not self.stop_event.is_set():
                    self.stop_event.wait(0.3)

                # Batch Pause
                if i > 0 and i % batch_size == 0:
                    pause_time = random.uniform(pause_min, pause_max)
                    self._update_parallel_bot_card(profile, f"⏸ استراحة ({int(pause_time)}ث)", sent_count, failed_count, invalid_count, i, len(chunk))
                    if self.stop_event.wait(pause_time):
                        break

                phone = c.get("phone")
                name = c.get("name", "عميل")
                processed = i + 1

                self._update_parallel_bot_card(profile, f"جاري الإرسال إلى {name}...", sent_count, failed_count, invalid_count, i, len(chunk))

                if not phone:
                    with self.stats_lock:
                        self.invalid += 1
                    invalid_count += 1
                    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    self._add_parallel_progress_row(profile, "N/A", name, timestamp, "بدون رقم", "بيانات الرقم ناقصة", "invalid")
                    self._update_parallel_bot_card(profile, "جاري الإرسال...", sent_count, failed_count, invalid_count, processed, len(chunk))
                    continue

                if not bot.is_logged_in():
                    self._add_parallel_progress_row(profile, phone, name, datetime.datetime.now().strftime("%H:%M:%S"), "فصل", "انقطع اتصال واتساب ويب", "failed")
                    break

                # Message Personalization
                msg_for_contact = self._apply_template(msg_template, c)
                atts_for_contact = self._format_attachments_for_contact(attachments, c)
                segments = self._split_messages(msg_for_contact)
                primary_msg = segments[0] if segments else msg_for_contact
                extra_msgs = segments[1:] if segments else []

                # Dispatch
                res = None
                for attempt in range(max_retries + 1):
                    skip_nav = (
                        attempt > 0
                        and atts_for_contact
                        and not retry_full_navigation
                        and res in attach_only_errors
                    )
                    res = bot.send_message(
                        phone=phone,
                        name=name,
                        message_template=primary_msg,
                        extra_messages=extra_msgs,
                        attachments=atts_for_contact,
                        stop_event=self.stop_event,
                        send_text_with_image=self.send_text_var.get(),
                        skip_open_chat=skip_nav,
                    )
                    if res in ("SUCCESS", "INVALID", "STOPPED"):
                        break
                    is_retryable = (
                        res in retryable_errors
                        or str(res).startswith("ERR_ATTACH_")
                        or str(res).startswith("ERR_TEXT_SEND")
                        or str(res).startswith("ERR_GENERAL")
                    )
                    if attempt < max_retries and is_retryable:
                        wait_s = random.uniform(retry_delay_min, retry_delay_max)
                        if self.stop_event.wait(wait_s):
                            break
                        continue
                    break

                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                if res == "SUCCESS":
                    with self.stats_lock:
                        self.sent += 1
                        self.results_log.append({"phone": phone, "name": name, "status": "نجاح", "error_code": "-", "timestamp": timestamp, "account": profile})
                    sent_count += 1
                    self._add_parallel_progress_row(profile, phone, name, timestamp, "نجاح", "تم الإرسال بنجاح", "success")
                    consecutive_failures = 0
                elif res == "INVALID":
                    with self.stats_lock:
                        self.invalid += 1
                        self.results_log.append({"phone": phone, "name": name, "status": "بدون واتساب", "error_code": "ERR-20", "timestamp": timestamp, "account": profile})
                    invalid_count += 1
                    self._add_parallel_progress_row(profile, phone, name, timestamp, "تخطي", "الرقم غير مسجل على واتساب", "invalid")
                    consecutive_failures = 0
                elif res == "STOPPED":
                    break
                else:
                    with self.stats_lock:
                        self.failed += 1
                        err_code = res if res.startswith("ERR") else "ERR-UNKNOWN"
                        self.results_log.append({"phone": phone, "name": name, "status": "فشل", "error_code": err_code, "timestamp": timestamp, "account": profile})
                    failed_count += 1
                    self._add_parallel_progress_row(profile, phone, name, timestamp, "فشل", str(res), "failed")
                    consecutive_failures += 1
                    if consecutive_failures >= max_consecutive_failures:
                        self._add_parallel_progress_row(profile, "-", "-", timestamp, "توقف تلقائي", f"توقف الحساب بعد {consecutive_failures} فشل متتالي", "stopped")
                        break

                self._update_parallel_bot_card(profile, "جاري الإرسال...", sent_count, failed_count, invalid_count, processed, len(chunk))

                # Human-like delay
                d_fast = random.uniform(delay_min * 0.3, delay_min * 0.7)
                d_mid = random.uniform(delay_min * 0.7, (delay_min + delay_max) / 2)
                d_slow = random.uniform((delay_min + delay_max) / 2, delay_max)
                chosen_delay = random.choices([d_fast, d_mid, d_slow], weights=[70, 20, 10], k=1)[0]
                if self.stop_event.wait(chosen_delay):
                    break

            # Finished chunk
            status_fin = "🛑 متوقف" if self.stop_event.is_set() else "🏁 مكتمل"
            self._update_parallel_bot_card(profile, status_fin, sent_count, failed_count, invalid_count, len(chunk), len(chunk))

        except Exception as exc:
            self._add_parallel_progress_row(profile, "-", "-", datetime.datetime.now().strftime("%H:%M:%S"), "خطأ", f"حدث خطأ غير متوقع: {exc}", "failed")
            self._update_parallel_bot_card(profile, "❌ خطأ غير متوقع", 0, 0, 0, 0, len(chunk))
        finally:
            if bot:
                try:
                    bot.close()
                except Exception:
                    pass
            self.active_bots.pop(profile, None)

    def _monitor_parallel_campaign(self, threads, total_contacts):
        """Monitor parallel threads and compile reports once all finish."""
        start_time = datetime.datetime.now()
        
        while any(t.is_alive() for t in threads):
            # Check stop_event or update aggregate progress
            elapsed = (datetime.datetime.now() - start_time).total_seconds()
            
            processed = 0
            with self.stats_lock:
                processed = self.sent + self.failed + self.invalid
                
            self._update_parallel_aggregate_header(processed, total_contacts, elapsed)
            time.sleep(1.0)

        # All finished!
        end_time = datetime.datetime.now()
        duration = end_time - start_time

        # Compile Consolidated Report
        csv_path = self._generate_final_report(duration)
        self.last_report_path = csv_path

        # Save to history
        self.campaign_manager.add_campaign(
            name=f"Consolidated Parallel Campaign {start_time.strftime('%Y-%m-%d %H:%M')}",
            total=total_contacts,
            sent=self.sent,
            failed=self.failed,
            invalid=self.invalid,
            duration_seconds=int(duration.total_seconds()),
            results_log=self.results_log,
            csv_path=csv_path
        )

        self.log(f"🏁 انتهت الحملة المتوازية بالكامل. إجمالي الإرسال الناجح: {self.sent} | الفاشل: {self.failed}")
        self._run_on_ui(lambda: self.progress_bar.set(1.0))
        self._run_on_ui(lambda: self.btn_start.configure(state="normal"))
        self._run_on_ui(lambda: self.btn_stop.configure(state="disabled"))
        if hasattr(self, "btn_check"):
            self._run_on_ui(lambda: self.btn_check.configure(state="normal"))
        self.is_running = False


