import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
import threading
import time
import random
import os
from automation.whatsapp_bot import WhatsAppBot
from utils.helpers import read_contacts, create_contacts_template

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
        
        # User Data Dir for session
        self.user_data_dir = os.path.join(os.getcwd(), "chrome_profile")

        self._setup_styles()
        self._create_widgets()
        self._load_defaults()

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
        
        ttk.Label(msg_frame, text="اكتب رسالتك هنا (استخدم {name} لاسم العميل):").pack(anchor="e")
        self.message_text = scrolledtext.ScrolledText(msg_frame, height=6, font=("Segoe UI", 10))
        self.message_text.pack(fill="x", pady=5)
        self.message_text.insert(tk.END, "مرحباً {name}،\nنتمنى أن تكون بخير. نتواصل معك من مصنع النجمة للبليتات بخصوص العروض الجديدة.")

        # 3. Settings
        settings_frame = ttk.LabelFrame(main_container, text=" إعدادات الوقت ", padding="10")
        settings_frame.pack(fill="x", pady=5)
        
        # Grid for settings
        settings_grid = ttk.Frame(settings_frame)
        settings_grid.pack(fill="x")
        
        ttk.Label(settings_grid, text="انتظار (ثانية):").grid(row=0, column=3, sticky="e")
        self.delay_min = tk.IntVar(value=30)
        self.delay_max = tk.IntVar(value=60)
        ttk.Spinbox(settings_grid, from_=5, to=300, textvariable=self.delay_min, width=5).grid(row=0, column=2, padx=5)
        ttk.Label(settings_grid, text="إلى").grid(row=0, column=1)
        ttk.Spinbox(settings_grid, from_=5, to=600, textvariable=self.delay_max, width=5).grid(row=0, column=0, padx=5)

        # 4. Controls
        controls_frame = ttk.Frame(main_container, padding="5")
        controls_frame.pack(fill="x", pady=10)
        
        self.btn_login = ttk.Button(controls_frame, text="1. فتح وتسجيل دخول واتساب (نافذة واحدة)", style="Action.TButton", command=self.login_action)
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

        # 6. Logs
        log_frame = ttk.LabelFrame(main_container, text=" سجل العمليات ", padding="5")
        log_frame.pack(fill="both", expand=True, pady=5)
        self.log_text = scrolledtext.ScrolledText(log_frame, height=10, state="disabled", font=("Consolas", 9))
        self.log_text.pack(fill="both", expand=True)

    def _load_defaults(self):
        def_contacts = os.path.join(os.getcwd(), "contacts.csv")
        if os.path.exists(def_contacts): self.contacts_file_path.set(def_contacts)
        def_img = os.path.join(os.getcwd(), "offer.jpg")
        if os.path.exists(def_img): self.image_file_path.set(def_img)

    def log(self, message):
        self.log_text.config(state="normal")
        self.log_text.insert(tk.END, f"[{time.strftime('%H:%M:%S')}] {message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state="disabled")

    def browse_contacts(self):
        path = filedialog.askopenfilename(filetypes=[("CSV", "*.csv")])
        if path: self.contacts_file_path.set(path)

    def browse_image(self):
        path = filedialog.askopenfilename(filetypes=[("Images", "*.jpg;*.jpeg;*.png")])
        if path: self.image_file_path.set(path)

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
                self.log("يرجى فحص الواتساب وتسجيل الدخول...")
                if self.bot.wait_for_login(timeout=60):
                    self.log("تم تسجيل الدخول بنجاح!")
                    messagebox.showinfo("تم", "تم تسجيل الدخول. يمكنك الآن الضغط على 'بدء الإرسال'.")
                else:
                    self.log("تنبيه: لم يتم اكتشاف تسجيل الدخول، تأكد من المتصفح.")
            except Exception as e:
                self.log(f"خطأ: {e}")
                
        threading.Thread(target=run_login, daemon=True).start()

    def start_thread(self):
        msg_template = self.message_text.get("1.0", tk.END).strip()
        if not msg_template:
            messagebox.showwarning("تنبيه", "يرجى كتابة نص الرسالة أولاً!")
            return

        if not self.contacts_file_path.get() or not os.path.exists(self.contacts_file_path.get()):
            messagebox.showerror("خطأ", "يرجى اختيار ملف أرقام صحيح.")
            return
        
        if not self.bot or not self.bot.driver:
            if messagebox.askyesno("تنبيه", "المتصفح غير مفتوح. هل تريد فتحه الآن؟"):
                self.login_action()
            return

        self.bot.bring_to_front()
        self.is_running = True
        self.stop_event.clear()
        self.btn_start.config(state="disabled")
        self.btn_stop.config(state="normal")
        
        threading.Thread(target=self.run_automation, daemon=True).start()

    def stop_action(self):
        if messagebox.askyesno("تأكيد", "هل تريد إيقاف العملية؟"):
            self.stop_event.set()
            self.log("🛑 طلب إيقاف...")

    def run_automation(self):
        try:
            contacts = read_contacts(self.contacts_file_path.get())
            if not contacts:
                self.log("❌ لا يوجد أرقام صالحة في الملف.")
                return
            
            self.log(f"🚀 بدء إرسال {len(contacts)} رسالة...")
            msg_template = self.message_text.get("1.0", tk.END).strip()
            img_path = self.image_file_path.get() if os.path.exists(self.image_file_path.get()) else None
            
            self.sent = 0
            self.failed = 0
            self.invalid = 0
            total = len(contacts)
            self.progress_bar["maximum"] = total
            
            for i, c in enumerate(contacts):
                if self.stop_event.is_set(): break
                
                self.progress_var.set(i + 1)
                self.status_var.set(f"إرسال إلى: {c['name']}")
                self.root.update_idletasks()
                
                res = self.bot.send_message(c['phone'], c['name'], msg_template, img_path, self.stop_event)
                
                if res == "SUCCESS":
                    self.sent += 1
                    self.log(f"✅ تم الإرسال لـ {c['name']}")
                elif res == "INVALID":
                    self.invalid += 1
                    self.log(f"🚫 الرقم {c['phone']} غير صحيح.")
                elif res == "STOPPED":
                    break
                else:
                    self.failed += 1
                    # Show the specific error code from the bot
                    self.log(f"❌ فشل: {c['name']} ({res})")

                self.counters_var.set(f"✅ {self.sent} | ❌ {self.failed} | 🚫 {self.invalid}")
                
                # Delay
                if i < total - 1:
                    wait = random.randint(self.delay_min.get(), self.delay_max.get())
                    self.log(f"⏳ انتظار {wait} ثانية...")
                    for _ in range(wait):
                        if self.stop_event.is_set(): break
                        time.sleep(1)

            self.log("🏁 انتهت العملية.")
            messagebox.showinfo("انتهى", "تم الانتهاء من القائمة.")
            
        except Exception as e:
            self.log(f"خطأ عام: {e}")
        finally:
            self.is_running = False
            self.root.after(0, lambda: self.btn_start.config(state="normal"))
            self.root.after(0, lambda: self.btn_stop.config(state="disabled"))
