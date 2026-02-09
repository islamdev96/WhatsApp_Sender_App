import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
import threading
import time
import random
import csv
import urllib.parse
import os
import sys
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

class WhatsAppSenderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("WhatsApp Sender Pro - مصنع النجمة")
        self.root.geometry("600x750")
        self.root.configure(bg="#f0f0f0")

        # Variables
        self.contacts_file_path = tk.StringVar()
        self.image_file_path = tk.StringVar()
        self.is_running = False
        self.driver = None
        self.stop_event = threading.Event()

        # Styles
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TButton", padding=6, relief="flat", background="#25D366", foreground="white", font=("Segoe UI", 10, "bold"))
        style.map("TButton", background=[('active', '#128C7E')])
        style.configure("Stop.TButton", background="#DC3545", foreground="white")
        style.map("Stop.TButton", background=[('active', '#C82333')])
        style.configure("TLabel", background="#f0f0f0", font=("Segoe UI", 10))
        style.configure("TFrame", background="#f0f0f0")
        style.configure("TLabelframe", background="#f0f0f0")
        style.configure("TLabelframe.Label", background="#f0f0f0", font=("Segoe UI", 11, "bold"))

        self._create_widgets()
        
        # Set defaults
        default_contacts = os.path.join(os.getcwd(), "contacts.csv")
        if os.path.exists(default_contacts):
            self.contacts_file_path.set(default_contacts)
            
        default_image = os.path.join(os.getcwd(), "offer.jpg")
        if os.path.exists(default_image):
            self.image_file_path.set(default_image)

    def _create_widgets(self):
        # Header
        header_frame = tk.Frame(self.root, bg="#128C7E", height=60)
        header_frame.pack(fill="x")
        lbl_header = tk.Label(header_frame, text="برنامج إرسال واتساب الآلي", bg="#128C7E", fg="white", font=("Segoe UI", 16, "bold"))
        lbl_header.pack(pady=10)

        main_container = ttk.Frame(self.root, padding="15")
        main_container.pack(fill="both", expand=True)

        # 1. File Selection
        files_frame = ttk.LabelFrame(main_container, text=" الملفات ", padding="10")
        files_frame.pack(fill="x", pady=5)

        # Contacts File
        ttk.Label(files_frame, text="ملف الأرقام (CSV):").grid(row=0, column=2, sticky="e")
        ttk.Entry(files_frame, textvariable=self.contacts_file_path, width=35).grid(row=0, column=1, padx=5)
        
        btn_browse_contacts = ttk.Button(files_frame, text="اختر ملف", width=10, command=self.browse_contacts)
        btn_browse_contacts.grid(row=0, column=0, padx=2)
        
        # Help/Template Button
        btn_help = ttk.Button(files_frame, text="؟", width=3, command=self.show_file_help)
        btn_help.grid(row=0, column=3, padx=2)

        # Image File
        ttk.Label(files_frame, text="الصورة (اختياري):").grid(row=1, column=2, sticky="e", pady=5)
        ttk.Entry(files_frame, textvariable=self.image_file_path, width=40).grid(row=1, column=1, padx=5, pady=5)
        ttk.Button(files_frame, text="اختر صورة", command=self.browse_image).grid(row=1, column=0)

        # 2. Settings
        settings_frame = ttk.LabelFrame(main_container, text=" إعدادات الوقت ", padding="10")
        settings_frame.pack(fill="x", pady=10)

        # Delay between messages
        ttk.Label(settings_frame, text="انتظار بين الرسائل (ثانية):").grid(row=0, column=3, sticky="e")
        self.delay_min = tk.IntVar(value=30)
        self.delay_max = tk.IntVar(value=120)
        
        delay_min_spin = ttk.Spinbox(settings_frame, from_=5, to=300, textvariable=self.delay_min, width=5)
        delay_max_spin = ttk.Spinbox(settings_frame, from_=5, to=600, textvariable=self.delay_max, width=5)
        
        delay_min_spin.grid(row=0, column=2, padx=5)
        ttk.Label(settings_frame, text="إلى").grid(row=0, column=1)
        delay_max_spin.grid(row=0, column=0, padx=5)


        # Batch Pause
        ttk.Label(settings_frame, text="استراحة طويلة كل:").grid(row=1, column=3, sticky="e", pady=10)
        self.batch_size = tk.IntVar(value=30)
        ttk.Spinbox(settings_frame, from_=5, to=1000, textvariable=self.batch_size, width=5).grid(row=1, column=2, sticky="e", padx=5)
        ttk.Label(settings_frame, text="رسالة").grid(row=1, column=1, sticky="w")

        ttk.Label(settings_frame, text="مدة الاستراحة (دقيقة):").grid(row=2, column=3, sticky="e")
        self.batch_pause_time = tk.IntVar(value=3)
        ttk.Spinbox(settings_frame, from_=1, to=60, textvariable=self.batch_pause_time, width=5).grid(row=2, column=2, sticky="e", padx=5)
        
        # 3. Control Buttons
        btn_frame = ttk.Frame(main_container)
        btn_frame.pack(fill="x", pady=10)

        # Login / Check Button
        self.btn_login = ttk.Button(btn_frame, text="تسجيل الدخول / تجهيز واتساب (خطوة أولى)", command=self.login_only)
        self.btn_login.pack(side="top", pady=(0, 10), fill="x")

        self.btn_start = ttk.Button(btn_frame, text="بدء الإرسال ▶", command=self.start_thread)
        self.btn_start.pack(side="right", padx=5, fill="x", expand=True)

        self.btn_stop = ttk.Button(btn_frame, text="إيقاف ⏹", style="Stop.TButton", command=self.stop_process, state="disabled")
        self.btn_stop.pack(side="left", padx=5, fill="x", expand=True)

        # 4. Progress & Status
        status_frame = ttk.Frame(main_container)
        status_frame.pack(fill="x", pady=5)
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(status_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill="x", side="top", pady=2)
        
        self.status_lbl_var = tk.StringVar(value="جاهز للبدء...")
        ttk.Label(status_frame, textvariable=self.status_lbl_var, font=("Segoe UI", 9)).pack(side="left")
        
        self.counters_var = tk.StringVar(value="✅ تم: 0 | ❌ فشل: 0 | 🚫 خطأ: 0")
        ttk.Label(status_frame, textvariable=self.counters_var, font=("Segoe UI", 9, "bold")).pack(side="right")

        # 5. Log Area
        log_frame = ttk.LabelFrame(main_container, text=" سجل العمليات التفصيلي ", padding="5")
        log_frame.pack(fill="both", expand=True, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=12, state="disabled", font=("Consolas", 9))
        self.log_text.pack(fill="both", expand=True)

        # Footer
        footer_lbl = tk.Label(self.root, text="Designed for Al Najma Factory", bg="#f0f0f0", fg="#888", font=("Segoe UI", 8))
        footer_lbl.pack(side="bottom", pady=5)

    def log(self, message):
        self.log_text.config(state="normal")
        self.log_text.insert(tk.END, f"[{time.strftime('%H:%M:%S')}] {message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state="disabled")

    def show_error(self, code, message, technical_detail=None):
        """Shows a detailed error message with a code for debugging."""
        full_msg = f"رمز الخطأ: {code}\n\nالمشكلة: {message}"
        if technical_detail:
            full_msg += f"\n\nتفاصيل تقنية (للمطور):\n{technical_detail}"
        
        self.log(f"❌ {code}: {message}")
        # Use root.after to safely show messagebox from thread
        self.root.after(0, lambda: messagebox.showerror(f"خطأ {code}", full_msg))

    def browse_contacts(self):
        filename = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
        if filename:
            self.contacts_file_path.set(filename)

    def browse_image(self):
        filename = filedialog.askopenfilename(filetypes=[("Images", "*.jpg;*.jpeg;*.png")])
        if filename:
            self.image_file_path.set(filename)

    def login_only(self):
        """Opens WhatsApp Web just for login/scan purposes."""
        try:
            self.log("جاري فتح واتساب لتسجيل الدخول...")
            user_data_dir = os.path.join(os.getcwd(), "chrome_profile")
            if not os.path.exists(user_data_dir):
                os.makedirs(user_data_dir)
                
            options = webdriver.ChromeOptions()
            options.add_argument(f"user-data-dir={user_data_dir}")
            
            # Temporary driver for login
            self.temp_driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
            self.temp_driver.get("https://web.whatsapp.com")
            
            messagebox.showinfo("تعليمات", "1. قم بمسح الباركود الآن باستخدام هاتفك.\n2. انتظر حتى تظهر قائمة المحادثات.\n3. بعد التأكد من الدخول، اضغط OK هنا ليتم حفظ البيانات.")
            
            # Explicitly quit to save session cookies
            self.temp_driver.quit()
            self.log("تم حفظ تسجيل الدخول بنجاح.")
            messagebox.showinfo("تم", "تم حفظ الجلسة. يمكنك الآن الضغط على 'بدء الإرسال'.")
            
        except Exception as e:
            self.show_error("ERR-01", "فشل في فتح المتصفح للتسجيل.", str(e))

    def show_file_help(self):
        """Shows help dialog about file format and offers to create a template."""
        help_text = (
            "صيغة الملف المطلوبة:\n"
            "1. يجب أن يكون الملف بصيغة CSV (Excel Comma Separated).\n"
            "2. يجب أن يحتوي على عمودين أساسيين: Name و Phone.\n\n"
            "مثال:\n"
            "Name, Phone\n"
            "Client 1, 010xxxxxxx\n"
            "Client 2, 011xxxxxxx\n\n"
            "هل تريد إنشاء ملف تجريبي (template.csv) الآن؟"
        )
        if messagebox.askyesno("تعليمات الملف", help_text):
            self.create_template_file()

    def create_template_file(self):
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv")],
            initialfile="template_contacts.csv"
        )
        if filename:
            try:
                with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
                    writer = csv.writer(f)
                    writer.writerow(['Name', 'Phone'])
                    writer.writerow(['عميل تجريبي', '01000000000'])
                messagebox.showinfo("تم", "تم إنشاء ملف النموذج بنجاح.\nيمكنك فتحه بالإكسيل وتعبئة البيانات.")
                self.contacts_file_path.set(filename)
            except Exception as e:
                messagebox.showerror("خطأ", f"فشل إنشاء الملف: {e}")

    def start_thread(self):
        contacts_file = self.contacts_file_path.get()
        if not contacts_file or not os.path.exists(contacts_file):
            messagebox.showerror("خطأ", "يرجى اختيار ملف أرقام صحيح!")
            return
        
        self.is_running = True
        self.stop_event.clear()
        self.btn_start.config(state="disabled")
        self.btn_stop.config(state="normal")
        
        # Start Thread
        t = threading.Thread(target=self.run_automation)
        t.daemon = True
        t.start()

    def stop_process(self):
        if messagebox.askyesno("تأكيد", "هل تريد إيقاف العملية؟"):
            self.stop_event.set()
            self.log("🛑 جاري الإيقاف... يرجى الانتظار.")

    def _update_counters(self):
        self.counters_var.set(f"✅ تم: {self.sent_count} | ❌ فشل: {self.failed_count} | 🚫 خطأ: {self.invalid_count}")

    def run_automation(self):
        try:
            self.log("جاري تجهيز المتصفح...")
            
            # Setup Chrome
            options = webdriver.ChromeOptions()
            user_data_dir = os.path.join(os.getcwd(), "chrome_profile")
            if not os.path.exists(user_data_dir):
                os.makedirs(user_data_dir)
            options.add_argument(f"user-data-dir={user_data_dir}")
            
            # Prevent automation detection features
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
            try:
                self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
            except Exception as e:
                self.show_error("ERR-02", "لا يمكن فتح المتصفح للأتمتة.", f"تأكد من إغلاق جميع نوافذ Chrome المفتوحة.\n{e}")
                return
            
            self.log("فتح واتساب ويب...")
            self.driver.get("https://web.whatsapp.com")
            
            # Wait for login - robust check
            try:
                # Check for either chat list or 'start chat' text
                WebDriverWait(self.driver, 60).until(
                    lambda d: d.find_elements(By.XPATH, '//div[@contenteditable="true"][@data-tab="3"]') or 
                              d.find_elements(By.XPATH, '//canvas[@aria-label="Scan this QR code"]')
                )
                
                # If QR code is present, wait longer for user
                if self.driver.find_elements(By.XPATH, '//canvas[@aria-label="Scan this QR code"]'):
                     self.log("يرجى مسح الباركود لتسجيل الدخول...")
                     WebDriverWait(self.driver, 120).until(
                        EC.presence_of_element_located((By.XPATH, '//div[@contenteditable="true"][@data-tab="3"]'))
                     )
                
                self.log("تم التأكد من تسجيل الدخول.")
            except:
                self.log("تنبيه: لم يتم تأكيد الدخول بشكل آلي، سنحاول الاستمرار...")

            # Read Contacts
            contacts = []
            try:
                with open(self.contacts_file_path.get(), 'r', encoding='utf-8-sig') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        normalized_row = {k.strip().lower(): v for k, v in row.items()}
                        phone = normalized_row.get('phone') or normalized_row.get('mobile') or normalized_row.get('number')
                        name = normalized_row.get('name') or normalized_row.get('given name') or 'Customer'
                        
                        if phone:
                            phone = phone.strip().replace(' ', '')
                            if phone.startswith('01'): phone = '2' + phone
                            elif phone.startswith('1') and len(phone) == 10: phone = '20' + phone
                            contacts.append({'phone': phone, 'name': name})
            except Exception as e:
                self.show_error("ERR-03", "فشل قراءة ملف الأرقام.", str(e))
                return

            self.log(f"تم تحميل {len(contacts)} رقم.")
            image_path = self.image_file_path.get()
            if image_path and not os.path.exists(image_path):
                image_path = None

            count = 0
            self.sent_count = 0
            self.failed_count = 0
            self.invalid_count = 0
            total = len(contacts)
            self.progress_bar["maximum"] = total
            
            for i, contact in enumerate(contacts):
                if self.stop_event.is_set():
                    self.log("⏹ تم إيقاف العملية يدوياً.")
                    break

                phone = contact['phone']
                name = contact['name']
                
                # Update Status
                self.progress_var.set(i + 1)
                self.status_lbl_var.set(f"جاري معالجة: {name} ({phone})...")
                self.root.update_idletasks()

                # Personalized Message
                message = f"مرحباً {name}،\nنتمنى أن تكون بخير. نتواصل معك من مصنع النجمة للبليتات البلاستيك بخصوص العروض الجديدة.\nيسعدنا تواصلك معنا!"
                encoded_msg = urllib.parse.quote(message)
                
                link = f"https://web.whatsapp.com/send?phone={phone}&text={encoded_msg}"
                self.driver.get(link)
                
                try:
                    # Robust Wait for Chat Load - INCREASED TIMEOUT
                    try:
                        # Wait for ANY of these indicators: Send Button, Invalid Number Popup, or Chat Input
                        # Increased to 90 seconds for slow connections
                        WebDriverWait(self.driver, 90).until(
                            lambda d: d.find_elements(By.XPATH, '//span[@data-icon="send"]') or 
                                      d.find_elements(By.XPATH, '//div[contains(text(), "invalid")]') or
                                      d.find_elements(By.XPATH, '//div[contains(text(), "غير صحيح")]') or
                                      d.find_elements(By.XPATH, '//div[contains(text(), "url check")]') 
                        )
                    except:
                        self.log(f"❌ [{i+1}] انتهت مهلة التحميل لـ {name}. (الإنترنت بطيء؟)")
                        self.failed_count += 1
                        self._update_counters()
                        continue

                    # Check for Invalid Number
                    invalid_popup = self.driver.find_elements(By.XPATH, '//div[contains(text(), "invalid")]') or \
                                    self.driver.find_elements(By.XPATH, '//div[contains(text(), "غير صحيح")]')
                    if invalid_popup:
                        self.log(f"🚫 [{i+1}] الرقم {phone} ليس عليه واتساب.")
                        self.invalid_count += 1
                        self._update_counters()
                        continue
                    
                    # Random delay
                    time.sleep(random.uniform(3, 6))
                    
                    sent_success = False
                    if image_path:
                        # Attach Image
                        try:
                            # Try multiple selectors for attach button
                            attach_btns = self.driver.find_elements(By.XPATH, '//div[@title="Attach"]') or \
                                          self.driver.find_elements(By.XPATH, '//div[@title="إرفاق"]') or \
                                          self.driver.find_elements(By.XPATH, '//span[@data-icon="plus"]')
                            
                            if attach_btns:
                                attach_btns[0].click()
                                time.sleep(1.5)
                                
                                image_input = self.driver.find_element(By.XPATH, '//input[@accept="image/*,video/mp4,video/3gpp,video/quicktime"]')
                                image_input.send_keys(image_path)
                                
                                # Wait for preview and send
                                time.sleep(3)
                                image_send_btn = WebDriverWait(self.driver, 30).until(
                                    EC.element_to_be_clickable((By.XPATH, '//span[@data-icon="send"]'))
                                )
                                time.sleep(random.uniform(1, 3))
                                image_send_btn.click()
                                self.log(f"✅ [{i+1}/{total}] تم إرسال الصورة لـ {name}")
                                sent_success = True
                                time.sleep(3)
                            else:
                                self.log("⚠️ لم يتم العثور على زر الإرفاق.")
                        except Exception as e:
                            self.log(f"❌ فشل إرفاق الصورة: {e}")

                    else:
                        # Text Only
                        try:
                            text_send_btn = self.driver.find_element(By.XPATH, '//span[@data-icon="send"]')
                            text_send_btn.click()
                            self.log(f"✅ [{i+1}/{total}] تم إرسال النص لـ {name}")
                            sent_success = True
                        except:
                            pass

                    if sent_success:
                        self.sent_count += 1
                        count += 1
                    else:
                        self.failed_count += 1
                    
                    self._update_counters()
                    
                    # Batch Pause Logic
                    if count > 0 and count % self.batch_size.get() == 0:
                        pause_mins = self.batch_pause_time.get()
                        self.log(f"--- استراحة طويلة لمدة {pause_mins} دقيقة ---")
                        for _ in range(pause_mins * 60):
                            if self.stop_event.is_set(): break
                            time.sleep(1)
                    else:
                        delay = random.randint(self.delay_min.get(), self.delay_max.get())
                        self.log(f"انتظار {delay} ثانية...")
                        for _ in range(delay):
                             if self.stop_event.is_set(): break
                             time.sleep(1)

                except Exception as e:
                    self.log(f"⚠️ خطأ غير متوقع مع {name}. (ERR-05)")
                    self.failed_count += 1
                    self._update_counters()
                    time.sleep(5)

            self.log("--- انتهت العملية ---")
            messagebox.showinfo("انتهى", "تم الانتهاء من جميع الأرقام.")

        except Exception as e:
            self.show_error("ERR-99", "حدث خطأ عام غير متوقع.", str(e))
        
        finally:
            self.is_running = False
            self.root.after(0, lambda: self.btn_start.config(state="normal"))
            self.root.after(0, lambda: self.btn_stop.config(state="disabled"))
            if self.driver:
                try:
                    self.driver.quit()
                except:
                    pass

if __name__ == "__main__":
    root = tk.Tk()
    app = WhatsAppSenderApp(root)
    root.mainloop()
