"""WhatsApp Sender Pro — Automation control methods (send, stop, pause, error mapping)."""
import customtkinter as ctk
from tkinter import filedialog, messagebox, ttk
import threading
import random
import os
import datetime

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

    def _show_sending_mode_dialog(self):
        """Professional sending-mode picker matching competitor apps."""
        import tkinter as tk

        dialog = ctk.CTkToplevel(self)
        dialog.title("Sending Mode | وضع الإرسال")
        dialog.geometry("520x360")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()

        # Centre on parent
        x = self.winfo_x() + (self.winfo_width() - 520) // 2
        y = self.winfo_y() + (self.winfo_height() - 360) // 2
        dialog.geometry(f"+{x}+{y}")

        frm = ctk.CTkFrame(dialog, fg_color="transparent")
        frm.pack(fill="both", expand=True, padx=25, pady=20)

        # Title
        title = ctk.CTkLabel(frm, text="اختر وضع الإرسال | Select your sending mode",
                             font=("Segoe UI", 16, "bold"))
        title.pack(anchor="w", pady=(0, 20))

        mode_var = tk.StringVar(value="safe")

        # ── Safe Mode Card ──
        safe_card = ctk.CTkFrame(frm, fg_color=COLORS.get("card_bg", "#1E293B"), corner_radius=10, border_width=2, border_color=COLORS.get("primary", "#00E676"))
        safe_card.pack(fill="x", pady=(0, 12))

        safe_top = ctk.CTkFrame(safe_card, fg_color="transparent")
        safe_top.pack(fill="x", padx=15, pady=(12, 4))

        safe_radio = ctk.CTkRadioButton(safe_top, text="الوضع الآمن | Safe Mode",
                                        font=("Segoe UI", 14, "bold"),
                                        variable=mode_var, value="safe")
        safe_radio.pack(side="left")

        safe_badge = ctk.CTkLabel(safe_top, text=" خطر الحظر منخفض ",
                                  font=("Segoe UI", 11, "bold"),
                                  fg_color="#16A34A", corner_radius=6,
                                  text_color="#FFFFFF")
        safe_badge.pack(side="right")

        safe_desc = ctk.CTkLabel(safe_card,
                                 text="يُفحص كل رقم على واتساب قبل الإرسال (أرقام غير مسجلة تُستبعد).\nاستخدم تأخيراً 30–120 ثانية مع الوسائط — لا يمكن ضمان عدم الحظر (سياسة واتساب).",
                                 font=("Segoe UI", 11),
                                 text_color=COLORS.get("text_muted", "#94A3B8"),
                                 justify="right", anchor="e")
        safe_desc.pack(fill="x", padx=15, pady=(0, 12))

        # ── Blind Mode Card ──
        blind_card = ctk.CTkFrame(frm, fg_color=COLORS.get("card_bg", "#1E293B"), corner_radius=10, border_width=2, border_color=COLORS.get("border", "#334155"))
        blind_card.pack(fill="x", pady=(0, 12))

        blind_top = ctk.CTkFrame(blind_card, fg_color="transparent")
        blind_top.pack(fill="x", padx=15, pady=(12, 4))

        blind_radio = ctk.CTkRadioButton(blind_top, text="الوضع العشوائي | Blind Mode",
                                         font=("Segoe UI", 14, "bold"),
                                         variable=mode_var, value="blind")
        blind_radio.pack(side="left")

        blind_badge = ctk.CTkLabel(blind_top, text=" خطر الحظر مرتفع ",
                                   font=("Segoe UI", 11, "bold"),
                                   fg_color="#DC2626", corner_radius=6,
                                   text_color="#FFFFFF")
        blind_badge.pack(side="right")

        blind_desc = ctk.CTkLabel(blind_card,
                                  text="يرسل إلى جميع الأرقام المستوردة بغض النظر عن صلاحيتها.\nلن يتم فحص الأرقام مسبقاً — سرعة أعلى لكن خطر الحظر مرتفع.",
                                  font=("Segoe UI", 11),
                                  text_color=COLORS.get("text_muted", "#94A3B8"),
                                  justify="right", anchor="e")
        blind_desc.pack(fill="x", padx=15, pady=(0, 12))

        # ── Buttons ──
        btn_frame = ctk.CTkFrame(frm, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(10, 0))

        btn_cancel = ctk.CTkButton(btn_frame, text="إلغاء | Cancel",
                                   font=("Segoe UI", 13, "bold"), width=130, height=38,
                                   fg_color=COLORS.get("danger", "#EF4444"),
                                   hover_color=COLORS.get("danger_hover", "#DC2626"),
                                   text_color="#FFFFFF",
                                   command=dialog.destroy)
        btn_cancel.pack(side="left", padx=(0, 10))

        def on_ok():
            chosen = mode_var.get()
            dialog.destroy()
            self._proceed_start_action(sending_mode=chosen)

        btn_ok = ctk.CTkButton(btn_frame, text="موافق | OK",
                               font=("Segoe UI", 13, "bold"), width=130, height=38,
                               fg_color=COLORS.get("primary", "#00E676"),
                               hover_color=COLORS.get("primary_hover", "#00C853"),
                               text_color="#000000",
                               command=on_ok)
        btn_ok.pack(side="right")

    def _proceed_start_action(self, sending_mode="safe"):
        """Actually start the campaign after the user picked a mode."""
        self.sending_mode = sending_mode
        if sending_mode == "safe":
            self.log("🛡️ تم اختيار الوضع الآمن (Safe Mode) — سيتم فحص الأرقام قبل الإرسال.")
        else:
            self.log("⚡ تم اختيار الوضع العشوائي (Blind Mode) — سيتم الإرسال لجميع الأرقام بدون فحص.")

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
            
            # Determine status
            c_status = "Completed" if not self.stop_event.is_set() else "Stopped"
            
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

