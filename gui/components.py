
import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog
import os

class AttachmentItem(ctk.CTkFrame):
    def __init__(self, master, path, type_="image", caption="", remove_callback=None, **kwargs):
        super().__init__(master, **kwargs)
        self.path = path
        self.type_ = type_
        self.remove_callback = remove_callback

        # Layout
        self.grid_columnconfigure(1, weight=1)

        # Icon/Type
        icon_text = "📷" if type_ == "image" else "🎥" if type_ == "video" else "📄"
        self.icon_label = ctk.CTkLabel(self, text=icon_text, width=30)
        self.icon_label.grid(row=0, column=0, padx=5, pady=5)

        # Path (Truncated) & Caption Frame
        content_frame = ctk.CTkFrame(self, fg_color="transparent")
        content_frame.grid(row=0, column=1, sticky="ew", padx=5, pady=5)

        filename = os.path.basename(path)
        if len(filename) > 25:
            filename = filename[:22] + "..."
            
        self.path_label = ctk.CTkLabel(content_frame, text=filename, anchor="w", font=("Segoe UI", 12, "bold"))
        self.path_label.pack(fill="x")

        self.caption_entry = ctk.CTkEntry(content_frame, placeholder_text="أضف كابشن (اختياري)...", height=24, font=("Segoe UI", 11))
        self.caption_entry.pack(fill="x", pady=(2, 0))
        if caption:
            self.caption_entry.insert(0, caption)

        # Remove Button
        self.remove_btn = ctk.CTkButton(self, text="❌", width=30, height=24, fg_color="#FF5555", hover_color="#CC0000",
                                        command=self._on_remove)
        self.remove_btn.grid(row=0, column=2, padx=5, pady=5)

    def _on_remove(self):
        if self.remove_callback:
            self.remove_callback(self)

    def get_data(self):
        return {
            "path": self.path,
            "type": self.type_,
            "caption": self.caption_entry.get().strip()
        }

class AttachmentManager(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        self.attachments = [] # List of AttachmentItem widgets

        # Header
        header = ctk.CTkFrame(self, fg_color="transparent", height=30)
        header.pack(fill="x", padx=5, pady=5)
        
        ctk.CTkLabel(header, text="المرفقات", font=("Segoe UI", 13, "bold")).pack(side="right", padx=5)

        # Add Buttons (Right aligned)
        self.btn_add_doc = ctk.CTkButton(header, text="+ ملف", width=60, height=24, command=lambda: self.add_attachment("document"))
        self.btn_add_doc.pack(side="left", padx=2)
        
        self.btn_add_vid = ctk.CTkButton(header, text="+ فيديو", width=60, height=24, command=lambda: self.add_attachment("video"))
        self.btn_add_vid.pack(side="left", padx=2)
        
        self.btn_add_img = ctk.CTkButton(header, text="+ صورة", width=60, height=24, command=lambda: self.add_attachment("image"))
        self.btn_add_img.pack(side="left", padx=2)

        # List Area
        self.scroll_frame = ctk.CTkScrollableFrame(self, height=150, fg_color="transparent")
        self.scroll_frame.pack(fill="both", expand=True, padx=5, pady=5)

    def add_attachment(self, type_):
        filetypes = []
        if type_ == "image":
            filetypes = [("Images", "*.jpg *.jpeg *.png *.gif *.bmp *.webp")]
        elif type_ == "video":
            filetypes = [("Videos", "*.mp4 *.avi *.mov *.mkv *.3gp")]
        else:
            filetypes = [("All Files", "*.*")]

        paths = filedialog.askopenfilenames(filetypes=filetypes)
        if paths:
            for path in paths:
                self._add_item(path, type_)

    def _add_item(self, path, type_):
        item = AttachmentItem(self.scroll_frame, path, type_, remove_callback=self._remove_item)
        item.pack(fill="x", pady=2)
        self.attachments.append(item)

    def _remove_item(self, item):
        if item in self.attachments:
            self.attachments.remove(item)
            item.destroy()

    def get_attachments(self):
        return [item.get_data() for item in self.attachments]

class RichTextFrame(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        # Toolbar
        self.toolbar = ctk.CTkFrame(self, height=30, fg_color="transparent")
        self.toolbar.pack(fill="x", padx=5, pady=2)

        # Tools
        ctk.CTkLabel(self.toolbar, text="الرسالة", font=("Segoe UI", 13, "bold")).pack(side="right", padx=5)
        
        # Insert Variable
        self.var_option = ctk.CTkOptionMenu(self.toolbar, values=["{name}", "{phone}", "{var1}", "{var2}", "{var3}", "{var4}", "{var5}"], width=90, height=24,
                                            command=self._insert_var)
        self.var_option.set("متغير")
        self.var_option.pack(side="left", padx=2)
        
        # Formatting buttons (Simulated for now, as CTkTextbox doesn't support rich tags easily yet)
        # We'll just insert markdown-like syntax or placeholders if user wants, 
        # but standard WhatsApp supports *bold*, _italic_, ~strike~.
        
        self.btn_bold = ctk.CTkButton(self.toolbar, text="B", width=30, height=24, font=("Segoe UI", 12, "bold"),
                                      command=lambda: self._insert_wrap("*"))
        self.btn_bold.pack(side="left", padx=2)
        
        self.btn_italic = ctk.CTkButton(self.toolbar, text="I", width=30, height=24, font=("Segoe UI", 12, "italic"),
                                        command=lambda: self._insert_wrap("_"))
        self.btn_italic.pack(side="left", padx=2)
        
        self.btn_strike = ctk.CTkButton(self.toolbar, text="S", width=30, height=24, font=("Segoe UI", 12, "overstrike"),
                                        command=lambda: self._insert_wrap("~"))
        self.btn_strike.pack(side="left", padx=2)

        # Text Area
        self.text_box = ctk.CTkTextbox(self, font=("Segoe UI", 14), wrap="word")
        self.text_box.pack(fill="both", expand=True, padx=5, pady=5)

    def _insert_var(self, value):
        self.text_box.insert("insert", f" {value} ")
        self.var_option.set("متغير")

    def _insert_wrap(self, char):
        try:
            # Try to wrap selected text
            sel_start = self.text_box.index("sel.first")
            sel_end = self.text_box.index("sel.last")
            if sel_start and sel_end:
                text = self.text_box.get(sel_start, sel_end)
                self.text_box.delete(sel_start, sel_end)
                self.text_box.insert(sel_start, f"{char}{text}{char}")
                return
        except tk.TclError:
            pass
        
        # If no selection, just insert chars
        self.text_box.insert("insert", f"{char}{char}")
        # Move cursor back one char? (Not easy in CTkTextbox without index math)

    def get_text(self):
        return self.text_box.get("1.0", "end").strip()
    
    def set_text(self, text):
        self.text_box.delete("1.0", "end")
        self.text_box.insert("1.0", text)
