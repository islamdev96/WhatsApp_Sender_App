    # ─── Numbers Filter Tab ──────────────────────────────────────────────────
    def _build_tab_filter(self):
        frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.tab_frames["filter"] = frame

        # Title
        title_lbl = ctk.CTkLabel(frame, text="فلترة الأرقام (Numbers Filter) 🔍", font=("Segoe UI", 24, "bold"), text_color=COLORS["primary"])
        title_lbl.pack(anchor="w", padx=20, pady=(20, 10))
        
        inst_lbl = ctk.CTkLabel(frame, text="أدخل الأرقام للتحقق من وجود حسابات واتساب نشطة لها قبل إرسال حملتك.", font=("Segoe UI", 12), text_color=COLORS["text_muted"])
        inst_lbl.pack(anchor="w", padx=20, pady=(0, 20))

        # Main Layout
        content = ctk.CTkFrame(frame, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=20, pady=0)
        
        # Left side: Input
        left = ctk.CTkFrame(content, fg_color=COLORS["card_bg"], corner_radius=10, width=300)
        left.pack(side="left", fill="y", padx=(0, 10))
        left.pack_propagate(False)
        
        lbl_in = ctk.CTkLabel(left, text="أدخل الأرقام (رقم في كل سطر):", font=("Segoe UI", 14, "bold"))
        lbl_in.pack(anchor="w", padx=15, pady=15)
        
        self.filter_input_txt = ctk.CTkTextbox(left, font=("Consolas", 12))
        self.filter_input_txt.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
        # Right-click menu for filter_input_txt
        import tkinter as tk
        ctx_menu = tk.Menu(self, tearoff=0, font=("Segoe UI", 11))
        ctx_menu.add_command(label="قص (Cut)", command=lambda: self.filter_input_txt._textbox.event_generate("<<Cut>>"))
        ctx_menu.add_command(label="نسخ (Copy)", command=lambda: self.filter_input_txt._textbox.event_generate("<<Copy>>"))
        ctx_menu.add_command(label="لصق (Paste)", command=lambda: self.filter_input_txt._textbox.event_generate("<<Paste>>"))
        ctx_menu.add_separator()
        ctx_menu.add_command(label="تحديد الكل (Select All)", command=lambda: self.filter_input_txt._textbox.tag_add("sel", "1.0", "end"))
        def _show_ctx(event):
            try: ctx_menu.tk_popup(event.x_root, event.y_root)
            finally: ctx_menu.grab_release()
        self.filter_input_txt.bind("<Button-3>", _show_ctx)

        btn_start_filter = ctk.CTkButton(
            left, text="بدء الفحص 🔍", font=("Segoe UI", 14, "bold"), height=40,
            fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"], text_color="#000",
            command=self._start_number_filter
        )
        btn_start_filter.pack(fill="x", padx=15, pady=(0, 15))

        # Right side: Results
        right = ctk.CTkFrame(content, fg_color=COLORS["card_bg"], corner_radius=10)
        right.pack(side="right", fill="both", expand=True)
        
        lbl_out = ctk.CTkLabel(right, text="نتائج الفحص:", font=("Segoe UI", 14, "bold"))
        lbl_out.pack(anchor="w", padx=15, pady=15)

        self.filter_tree = ttk.Treeview(right, columns=("phone", "status"), show="headings")
        self.filter_tree.heading("phone", text="الرقم")
        self.filter_tree.heading("status", text="الحالة")
        self.filter_tree.column("phone", width=200, anchor="center")
        self.filter_tree.column("status", width=150, anchor="center")
        
        scroll = ctk.CTkScrollbar(right, command=self.filter_tree.yview)
        self.filter_tree.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y", pady=(0, 15))
        self.filter_tree.pack(fill="both", expand=True, padx=(15, 0), pady=(0, 15))
        
        # Tags for colors
        self.filter_tree.tag_configure("valid", foreground="#16A34A")
        self.filter_tree.tag_configure("invalid", foreground="#DC2626")
        self.filter_tree.tag_configure("checking", foreground="#EAB308")
        
        # Stats & Export
        bottom_right = ctk.CTkFrame(right, fg_color="transparent")
        bottom_right.pack(fill="x", padx=15, pady=(0, 15))
        
        self.filter_stats_lbl = ctk.CTkLabel(bottom_right, text="الإجمالي: 0 | صالح: 0 | غير صالح: 0", font=("Segoe UI", 12, "bold"))
        self.filter_stats_lbl.pack(side="left")
        
        btn_export = ctk.CTkButton(
            bottom_right, text="تصدير الصالح (Excel) 💾", font=("Segoe UI", 12, "bold"),
            fg_color="#3B82F6", hover_color="#2563EB", text_color="#FFF",
            command=self._export_filtered_numbers
        )
        btn_export.pack(side="right")
        
    def _start_number_filter(self):
        if not self.bot or not self.bot.driver:
            messagebox.showerror("خطأ", "يجب فتح المتصفح (Open WhatsApp) أولاً.")
            return
        if not self.bot.is_logged_in():
            messagebox.showerror("خطأ", "يجب تسجيل الدخول في واتساب أولاً.")
            return

        raw_text = self.filter_input_txt.get("1.0", "end").strip()
        if not raw_text:
            return
        
        numbers = [n.strip() for n in raw_text.split("\n") if n.strip()]
        if not numbers:
            return
            
        # Clear tree
        for item in self.filter_tree.get_children():
            self.filter_tree.delete(item)
            
        self.filter_stats = {"total": len(numbers), "valid": 0, "invalid": 0}
        self.filter_stats_lbl.configure(text=f"الإجمالي: {self.filter_stats['total']} | صالح: 0 | غير صالح: 0")
        
        # Insert all as checking
        self.filter_tree_items = {}
        for num in numbers:
            item_id = self.filter_tree.insert("", "end", values=(num, "⏳ في الانتظار"), tags=("checking",))
            self.filter_tree_items[num] = item_id
            
        self.log(f"🔍 بدء فحص {len(numbers)} رقم...")
        threading.Thread(target=self._run_filter_thread, args=(numbers,), daemon=True).start()
        
    def _run_filter_thread(self, numbers):
        for num in numbers:
            if not self.bot or not self.bot.driver:
                break
            
            # Format number simply
            formatted = num.replace("+", "").replace(" ", "").replace("-", "")
            
            self._run_on_ui(lambda n=num: self.filter_tree.item(self.filter_tree_items[n], values=(n, "🔄 جاري الفحص...")))
            
            # Use WhatsApp's wa.me link check
            is_valid = self.bot.check_number_validity(formatted)
            
            if is_valid:
                self.filter_stats["valid"] += 1
                self._run_on_ui(lambda n=num: self.filter_tree.item(self.filter_tree_items[n], values=(n, "✅ متوفر"), tags=("valid",)))
            else:
                self.filter_stats["invalid"] += 1
                self._run_on_ui(lambda n=num: self.filter_tree.item(self.filter_tree_items[n], values=(n, "❌ غير متوفر"), tags=("invalid",)))
                
            self._run_on_ui(lambda: self.filter_stats_lbl.configure(text=f"الإجمالي: {self.filter_stats['total']} | صالح: {self.filter_stats['valid']} | غير صالح: {self.filter_stats['invalid']}"))
            time.sleep(1) # delay to prevent rate limit
            
        self.log("✅ انتهت عملية الفحص.")
        
    def _export_filtered_numbers(self):
        valid_numbers = []
        for item in self.filter_tree.get_children():
            vals = self.filter_tree.item(item, "values")
            if "متوفر" in vals[1] or "✅" in vals[1]:
                valid_numbers.append(vals[0])
                
        if not valid_numbers:
            messagebox.showwarning("تنبيه", "لا توجد أرقام صالحة لتصديرها.")
            return
            
        file_path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")])
        if not file_path:
            return
            
        try:
            import pandas as pd
            df = pd.DataFrame({"Number": valid_numbers})
            df.to_excel(file_path, index=False)
            messagebox.showinfo("نجاح", f"تم تصدير {len(valid_numbers)} رقم بنجاح!")
        except Exception as e:
            messagebox.showerror("خطأ", f"حدث خطأ أثناء التصدير:\n{e}")

    # ─── Received Messages Tab (Mini CRM) ────────────────────────────────────
    def _build_tab_received(self):
        frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.tab_frames["received"] = frame

        # Title
        title_lbl = ctk.CTkLabel(frame, text="صندوق الوارد (Received Messages) 📥", font=("Segoe UI", 24, "bold"), text_color=COLORS["primary"])
        title_lbl.pack(anchor="w", padx=20, pady=(20, 10))
        
        inst_lbl = ctk.CTkLabel(frame, text="مراقبة حية للرسائل الواردة أثناء تشغيل البرنامج.", font=("Segoe UI", 12), text_color=COLORS["text_muted"])
        inst_lbl.pack(anchor="w", padx=20, pady=(0, 20))

        content = ctk.CTkFrame(frame, fg_color=COLORS["card_bg"], corner_radius=10)
        content.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        self.received_tree = ttk.Treeview(content, columns=("date", "sender", "message"), show="headings")
        self.received_tree.heading("date", text="الوقت والتاريخ")
        self.received_tree.heading("sender", text="المرسل")
        self.received_tree.heading("message", text="نص الرسالة")
        
        self.received_tree.column("date", width=150, anchor="center")
        self.received_tree.column("sender", width=150, anchor="center")
        self.received_tree.column("message", width=500, anchor="w")
        
        scroll = ctk.CTkScrollbar(content, command=self.received_tree.yview)
        self.received_tree.configure(yscrollcommand=scroll.set)
        
        scroll.pack(side="right", fill="y", pady=15)
        self.received_tree.pack(fill="both", expand=True, padx=(15, 0), pady=15)
        
        # We will share the chatbot thread to update this list
        # Whenever chatbot reads a message, it can append it here!
