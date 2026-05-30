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

