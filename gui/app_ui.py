import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
import threading
import queue
import time
import random
import os
from automation.whatsapp_bot import WhatsAppBot
from utils.helpers import read_contacts, create_contacts_template

ERROR_CATALOG = {
    "ERR-01": "تعذر تشغيل المتصفح. اغلق كل نوافذ Chrome ثم أعد المحاولة.",
    "ERR-02": "المتصفح لا يستجيب للأتمتة أو انتهت مهلة تسجيل الدخول.",
    "ERR-03": "مشكلة في ملف الأرقام (غير موجود/مفتوح/أعمدة غير صحيحة).",
    "ERR-04": "نص الرسالة فارغ.",
    "ERR-09": "ملف الصورة غير موجود أو غير صالح.",
    "ERR-06": "زر الإرفاق غير موجود.",
    "ERR-07": "زر الإرسال لم يظهر في الوقت المحدد.",
    "ERR-08": "فشل رفع الصورة أو كتابة الكابشن.",
    "ERR-10": "انتهت مهلة تحميل المحادثة.",
    "ERR-20": "الرقم غير صحيح أو ليس لديه واتساب.",
    "ERR-21": "لم يتم تسجيل الدخول بعد.",
    "ERR-99": "خطأ غير متوقع.",
}

class WhatsAppSenderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("WhatsApp Sender Pro - مصنع النجمة")
        self.root.geometry("650x850")
        self.root.configure(bg="#f4f4f9")

        # Variables
        self.contacts_file_path = tk.StringVar()
        self.image_file_path = tk.StringVar()
        self.is_running = False
        self.bot = None
        self.stop_event = threading.Event()
        self.ui_queue = queue.Queue()
        self.send_text_with_image = tk.BooleanVar(value=True)
        self.batch_size = tk.IntVar(value=30)
        self.batch_pause_min = tk.IntVar(value=180)
        self.batch_pause_max = tk.IntVar(value=240)
        
        # User Data Dir for session
        self.user_data_dir = os.path.join(os.getcwd(), "chrome_profile")

        self._setup_styles()
        self._create_widgets()
        self._load_defaults()
        self.root.after(50, self._process_ui_queue)

    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TButton", padding=6, font=("Segoe UI", 10, "bold"))
        style.configure("Action.TButton", background="#25D366", foreground="white")
        style.map("Action.TButton", background=[('active', '#128C7E')])
        style.configure("Stop.TButton", background="#DC3545", foreground="white")
        style.map("Stop.TButton", background=[('active', '#C82333')])
        style.configure("TLabel", background="#f4f4f9", font=("Segoe UI", 10))
        style.configure("Header.TLabel", background="#128C7E", foreground="white", font=("Segoe UI", 16, "bold"))

    def _create_widgets(self):
        # Header
        header_frame = tk.Frame(self.root, bg="#128C7E")
        header_frame.pack(fill="x")
        ttk.Label(header_frame, text="برنامج إرسال واتساب المطور", style="Header.TLabel").pack(pady=15)

        main_container = ttk.Frame(self.root, padding="15")
        main_container.pack(fill="both", expand=True)

        # 1. File Selection
        files_frame = ttk.LabelFrame(main_container, text=" الملفات الأساسية ", padding="10")
        files_frame.pack(fill="x", pady=5)

        # Contacts
        ttk.Label(files_frame, text="ملف الأرقام (CSV):").grid(row=0, column=2, sticky="e")
        ttk.Entry(files_frame, textvariable=self.contacts_file_path, width=40).grid(row=0, column=1, padx=5)
        ttk.Button(files_frame, text="اختر", width=8, command=self.browse_contacts).grid(row=0, column=0)
        
        # Image
        ttk.Label(files_frame, text="الصورة (اختياري):").grid(row=1, column=2, sticky="e", pady=10)
        ttk.Entry(files_frame, textvariable=self.image_file_path, width=40).grid(row=1, column=1, padx=5)
        ttk.Button(files_frame, text="اختر", width=8, command=self.browse_image).grid(row=1, column=0)

        # 2. Message Content
        msg_frame = ttk.LabelFrame(main_container, text=" نص الرسالة ", padding="10")
        msg_frame.pack(fill="x", pady=5)
        
        ttk.Label(msg_frame, text="اكتب رسالتك هنا (استخدم {name} لاسم العميل) - يمكن تركها فارغة إذا كانت صورة فقط:").pack(anchor="e")
        self.message_text = scrolledtext.ScrolledText(msg_frame, height=6, font=("Segoe UI", 10))
        self.message_text.pack(fill="x", pady=5)
        ttk.Checkbutton(msg_frame, text="إرسال نص مع الصورة", variable=self.send_text_with_image).pack(anchor="e")

        # 3. Settings
        settings_frame = ttk.LabelFrame(main_container, text=" إعدادات الوقت الأساسية ", padding="10")
        settings_frame.pack(fill="x", pady=5)
        
        # Grid for settings
        settings_grid = ttk.Frame(settings_frame)
        settings_grid.pack(fill="x")
        
        ttk.Label(settings_grid, text="انتظار (ثانية):").grid(row=0, column=3, sticky="e")
        self.delay_min = tk.IntVar(value=30)
        self.delay_max = tk.IntVar(value=120)
        ttk.Spinbox(settings_grid, from_=10, to=600, textvariable=self.delay_min, width=5).grid(row=0, column=2, padx=5)
        ttk.Label(settings_grid, text="إلى").grid(row=0, column=1)
        ttk.Spinbox(settings_grid, from_=10, to=600, textvariable=self.delay_max, width=5).grid(row=0, column=0, padx=5)

        # Periodic pause
        batch_frame = ttk.LabelFrame(main_container, text=" استراحة دورية ", padding="10")
        batch_frame.pack(fill="x", pady=5)
        batch_grid = ttk.Frame(batch_frame)
        batch_grid.pack(fill="x")
        ttk.Label(batch_grid, text="بعد كل (رسالة):").grid(row=0, column=5, sticky="e")
        ttk.Spinbox(batch_grid, from_=5, to=200, textvariable=self.batch_size, width=5).grid(row=0, column=4, padx=5)
        ttk.Label(batch_grid, text="استراحة (ثانية):").grid(row=0, column=3, sticky="e")
        ttk.Spinbox(batch_grid, from_=30, to=900, textvariable=self.batch_pause_min, width=5).grid(row=0, column=2, padx=5)
        ttk.Label(batch_grid, text="إلى").grid(row=0, column=1)
        ttk.Spinbox(batch_grid, from_=30, to=1200, textvariable=self.batch_pause_max, width=5).grid(row=0, column=0, padx=5)

        # 4. Controls
        controls_frame = ttk.Frame(main_container, padding="5")
        controls_frame.pack(fill="x", pady=10)
        
        self.btn_login = ttk.Button(controls_frame, text="1. فتح واتساب ومسح QR (مرة واحدة)", style="Action.TButton", command=self.login_action)
        self.btn_login.pack(fill="x", pady=2)
        
        btn_sub_frame = ttk.Frame(controls_frame)
        btn_sub_frame.pack(fill="x", pady=5)
        
        self.btn_start = ttk.Button(btn_sub_frame, text="2. بدء الإرسال ▶", style="Action.TButton", command=self.start_thread)
        self.btn_start.pack(side="right", expand=True, fill="x", padx=2)
        
        self.btn_stop = ttk.Button(btn_sub_frame, text="إيقاف ⏹", style="Stop.TButton", command=self.stop_action, state="disabled")
        self.btn_stop.pack(side="left", expand=True, fill="x", padx=2)

        # 5. Progress
        progress_frame = ttk.Frame(main_container)
        progress_frame.pack(fill="x", pady=5)
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill="x", pady=2)
        
        self.status_var = tk.StringVar(value="جاهز...")
        ttk.Label(progress_frame, textvariable=self.status_var, font=("Segoe UI", 9)).pack(side="left")
        
        self.counters_var = tk.StringVar(value="✅ 0 | ❌ 0 | 🚫 0")
        ttk.Label(progress_frame, textvariable=self.counters_var, font=("Segoe UI", 10, "bold")).pack(side="right")

        # Diagnostics
        diag_frame = ttk.Frame(main_container)
        diag_frame.pack(fill="x", pady=2)
        ttk.Button(diag_frame, text="أكواد الأخطاء", command=self.show_error_codes).pack(side="left")

        # 6. Logs
        log_frame = ttk.LabelFrame(main_container, text=" سجل العمليات ", padding="5")
        log_frame.pack(fill="both", expand=True, pady=5)
        self.log_text = scrolledtext.ScrolledText(log_frame, height=10, state="disabled", font=("Consolas", 9))
        self.log_text.pack(fill="both", expand=True)

    def _process_ui_queue(self):
        while True:
            try:
                fn = self.ui_queue.get_nowait()
            except queue.Empty:
                break
            try:
                fn()
            finally:
                self.ui_queue.task_done()
        self.root.after(50, self._process_ui_queue)

    def _run_on_ui(self, fn):
        self.ui_queue.put(fn)

    def _load_defaults(self):
        def_contacts = os.path.join(os.getcwd(), "contacts.csv")
        if os.path.exists(def_contacts): self.contacts_file_path.set(def_contacts)
        def_img = os.path.join(os.getcwd(), "offer.jpg")
        if os.path.exists(def_img): self.image_file_path.set(def_img)

    def log(self, message):
        def _do_log():
            self.log_text.config(state="normal")
            self.log_text.insert(tk.END, f"[{time.strftime('%H:%M:%S')}] {message}\n")
            self.log_text.see(tk.END)
            self.log_text.config(state="disabled")
        self._run_on_ui(_do_log)

    def _show_dialog(self, kind, title, message):
        def _do():
            if kind == "info":
                messagebox.showinfo(title, message)
            elif kind == "warning":
                messagebox.showwarning(title, message)
            else:
                messagebox.showerror(title, message)
        self._run_on_ui(_do)

    def report_error(self, code, message=None, detail=None, dialog=True, level="error"):
        base_message = message or ERROR_CATALOG.get(code, "حدث خطأ غير معروف.")
        log_message = f"[{code}] {base_message}"
        if detail:
            log_message += f" | {detail}"
        self.log(log_message)
        if dialog:
            dialog_message = f"{base_message}\n\nالكود: {code}"
            self._show_dialog(level, "تنبيه" if level == "warning" else "خطأ", dialog_message)

    def show_error_codes(self):
        lines = [f"{code} - {desc}" for code, desc in ERROR_CATALOG.items()]
        self._show_dialog("info", "أكواد الأخطاء", "\n".join(lines))

    def browse_contacts(self):
        path = filedialog.askopenfilename(filetypes=[("CSV", "*.csv")])
        if path: self.contacts_file_path.set(path)

    def browse_image(self):
        path = filedialog.askopenfilename(filetypes=[("Images", "*.jpg;*.jpeg;*.png")])
        if path: self.image_file_path.set(path)

    def _prepare_message_and_image(self):
        msg_template = self.message_text.get("1.0", tk.END).strip()
        img_path_raw = (self.image_file_path.get() or "").strip()
        img_path = img_path_raw if img_path_raw and os.path.exists(img_path_raw) else None

        if img_path_raw and not img_path:
            self.report_error("ERR-09", "ملف الصورة غير موجود أو غير صالح.", dialog=True)
            return None, None

        if img_path and not self.send_text_with_image.get():
            msg_template = ""

        if not msg_template and not img_path:
            self.report_error("ERR-04", "يرجى كتابة نص الرسالة أو اختيار صورة.", dialog=True, level="warning")
            return None, None

        return msg_template, img_path

    def login_action(self):
        """Initializes the bot and opens the browser for login."""
        if self.bot and self.bot.driver:
            self.bot.bring_to_front()
            self.log("المتصفح مفتوح بالفعل.")
            return
            
        def run_login():
            try:
                self.log("جاري فتح المتصفح...")
                self.bot = WhatsAppBot(self.user_data_dir)
                self.bot.open_whatsapp()
                self.bot.bring_to_front()
                self.log("يرجى فتح واتساب على الهاتف ومسح QR لتسجيل الدخول...")
                if self.bot.wait_for_login(timeout=60):
                    self.log("تم تسجيل الدخول بنجاح!")
                    self._show_dialog("info", "تم", "تم تسجيل الدخول. يمكنك الآن الضغط على 'بدء الإرسال'.")
                else:
                    self.report_error("ERR-02", "لم يتم تسجيل الدخول خلال الوقت المحدد.", dialog=True, level="warning")
            except Exception as e:
                self.report_error("ERR-01", "تعذر تشغيل المتصفح.", detail=str(e), dialog=True)
                
        threading.Thread(target=run_login, daemon=True).start()

    def start_thread(self):
        msg_template, img_path = self._prepare_message_and_image()
        if msg_template is None and img_path is None:
            return

        if not self.contacts_file_path.get() or not os.path.exists(self.contacts_file_path.get()):
            self.report_error("ERR-03", "يرجى اختيار ملف أرقام صحيح.", dialog=True)
            return
        
        if not self.bot or not self.bot.driver:
            if messagebox.askyesno("تنبيه", "المتصفح غير مفتوح. هل تريد فتحه الآن؟"):
                self.login_action()
            return
        if not self.bot.is_logged_in():
            self.bot.bring_to_front()
            self.report_error("ERR-21", "لم يتم تسجيل الدخول بعد. يرجى مسح QR من الهاتف.", dialog=True, level="warning")
            return

        self.bot.bring_to_front()
        self.is_running = True
        self.stop_event.clear()
        self.btn_start.config(state="disabled")
        self.btn_stop.config(state="normal")
        
        threading.Thread(target=self.run_automation, args=(msg_template, img_path), daemon=True).start()

    def stop_action(self):
        if messagebox.askyesno("تأكيد", "هل تريد إيقاف العملية؟"):
            self.stop_event.set()
            self.log("🛑 طلب إيقاف...")

    def _map_bot_error(self, res):
        if not res:
            return "ERR-99", "خطأ غير معروف.", None
        if res.startswith("ERR_IMAGE_FLOW:"):
            detail = res.split(":", 1)[1].strip()
            return "ERR-08", "فشل إرسال الصورة.", detail
        if res.startswith("ERR_GENERAL:"):
            detail = res.split(":", 1)[1].strip()
            if "timeout" in detail.lower() or "timeoutexception" in detail.lower():
                return "ERR-10", "انتهت مهلة تحميل المحادثة.", detail
            return "ERR-99", "خطأ غير متوقع أثناء المعالجة.", detail
        mapping = {
            "ERR_NOT_READY": ("ERR-01", "المتصفح غير جاهز.", None),
            "ERR_EMPTY_MESSAGE": ("ERR-04", "لا يوجد نص للإرسال.", None),
            "ERR_CHAT_INPUT_NOT_FOUND": ("ERR-07", "صندوق كتابة الرسالة غير موجود.", None),
            "ERR_ATTACH_BTN_NOT_FOUND": ("ERR-06", "زر الإرفاق غير موجود.", None),
            "ERR_FILE_INPUT_NOT_FOUND": ("ERR-08", "حقل رفع الصورة غير موجود.", None),
            "ERR_CAPTION_BOX_NOT_FOUND": ("ERR-08", "صندوق كتابة الكابشن غير موجود.", None),
            "ERR_FINAL_SEND_BTN_NOT_FOUND": ("ERR-07", "زر الإرسال النهائي لم يظهر.", None),
            "ERR_SEND_BTN_TIMEOUT": ("ERR-07", "زر الإرسال لم يظهر في الوقت المحدد.", None),
            "ERR_TIMEOUT": ("ERR-10", "انتهت مهلة تحميل المحادثة.", None),
        }
        return mapping.get(res, ("ERR-99", f"خطأ غير معروف ({res})", None))

    def run_automation(self, msg_template, img_path):
        try:
            contacts = read_contacts(self.contacts_file_path.get())
            if not contacts:
                self.report_error("ERR-03", "لا يوجد أرقام صالحة في الملف.", dialog=True)
                return
            
            self.log(f"🚀 بدء إرسال {len(contacts)} رسالة...")
            
            self.sent = 0
            self.failed = 0
            self.invalid = 0
            total = len(contacts)
            self._run_on_ui(lambda: self.progress_bar.config(maximum=total))

            # Normalize timing ranges
            delay_min = int(self.delay_min.get())
            delay_max = int(self.delay_max.get())
            if delay_min > delay_max:
                delay_min, delay_max = delay_max, delay_min

            batch_size = int(self.batch_size.get()) if self.batch_size.get() else 0
            pause_min = int(self.batch_pause_min.get())
            pause_max = int(self.batch_pause_max.get())
            if pause_min > pause_max:
                pause_min, pause_max = pause_max, pause_min
            
            for i, c in enumerate(contacts):
                if self.stop_event.is_set(): break
                
                processed = i + 1
                self._run_on_ui(lambda processed=processed: self.progress_var.set(processed))
                self._run_on_ui(lambda c=c, processed=processed, total=total: self.status_var.set(f"إرسال إلى: {c['name']} ({processed}/{total})"))
                
                res = self.bot.send_message(c['phone'], c['name'], msg_template, img_path, self.stop_event)
                
                if res == "SUCCESS":
                    self.sent += 1
                    self.log(f"✅ تم الإرسال لـ {c['name']}")
                elif res == "INVALID":
                    self.invalid += 1
                    self.log(f"🚫 [ERR-20] الرقم {c['phone']} ليس عليه واتساب أو غير صحيح.")
                elif res == "STOPPED":
                    break
                else:
                    self.failed += 1
                    code, message, detail = self._map_bot_error(res)
                    self.log(f"❌ [{code}] {message} - {c['name']} ({c['phone']})")
                    if detail:
                        self.log(f"   تفاصيل: {detail}")

                counter_text = f"✅ {self.sent} | ❌ {self.failed} | 🚫 {self.invalid}"
                self._run_on_ui(lambda text=counter_text: self.counters_var.set(text))
                remaining = total - processed
                self._run_on_ui(lambda remaining=remaining, processed=processed, total=total: self.status_var.set(f"تمت معالجة {processed}/{total} | المتبقي {remaining}"))
                
                # Delay
                if processed < total:
                    wait = random.randint(delay_min, delay_max)
                    self.log(f"⏳ انتظار {wait} ثانية...")
                    for _ in range(wait):
                        if self.stop_event.is_set(): break
                        time.sleep(1)

                    if batch_size > 0 and processed % batch_size == 0:
                        batch_wait = random.randint(pause_min, pause_max)
                        self.log(f"🕒 استراحة دورية {batch_wait} ثانية بعد {processed} رسالة...")
                        for _ in range(batch_wait):
                            if self.stop_event.is_set(): break
                            time.sleep(1)

            if self.stop_event.is_set():
                self.log("🛑 تم إيقاف العملية.")
                self._show_dialog("info", "تم الإيقاف", "تم إيقاف العملية بناءً على طلبك.")
            else:
                self.log("🏁 انتهت العملية.")
                self._show_dialog("info", "انتهى", "تم الانتهاء من القائمة.")
            
        except Exception as e:
            self.report_error("ERR-99", "حدث خطأ عام أثناء الإرسال.", detail=str(e), dialog=True)
        finally:
            self.is_running = False
            self._run_on_ui(lambda: self.btn_start.config(state="normal"))
            self._run_on_ui(lambda: self.btn_stop.config(state="disabled"))
