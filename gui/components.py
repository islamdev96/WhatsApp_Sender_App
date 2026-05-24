
import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog
import os

class AttachmentItem(ctk.CTkFrame):
    def __init__(self, master, path, type_="image", caption="", remove_callback=None, colors=None, **kwargs):
        self.colors = colors or {}
        if "fg_color" not in kwargs:
            kwargs["fg_color"] = self._c("bg_dark", "transparent")
        super().__init__(master, **kwargs)
        self.path = path
        self.type_ = type_
        self.remove_callback = remove_callback

        # Layout
        self.grid_columnconfigure(1, weight=1)

        # Icon/Type
        icon_text = "📷" if type_ == "image" else "🎥" if type_ == "video" else "📄"
        self.icon_label = ctk.CTkLabel(self, text=icon_text, width=30,
                                       text_color=self._c("accent", None))
        self.icon_label.grid(row=0, column=0, padx=5, pady=5)

        # Path (Truncated) & Caption Frame
        content_frame = ctk.CTkFrame(self, fg_color="transparent")
        content_frame.grid(row=0, column=1, sticky="ew", padx=5, pady=5)

        filename = os.path.basename(path)
        if len(filename) > 25:
            filename = filename[:22] + "..."
            
        self.path_label = ctk.CTkLabel(content_frame, text=filename, anchor="w",
                                       font=("Segoe UI", 12, "bold"),
                                       text_color=self._c("text_main", None))
        self.path_label.pack(fill="x")

        self.caption_entry = ctk.CTkEntry(
            content_frame,
            placeholder_text="أضف كابشن (اختياري)...",
            height=24,
            font=("Segoe UI", 11),
            fg_color=self._c("card_bg", None),
            text_color=self._c("text_main", None),
            border_color=self._c("border", None),
            placeholder_text_color=self._c("text_muted", None),
        )
        self.caption_entry.pack(fill="x", pady=(2, 0))
        if caption:
            self.caption_entry.insert(0, caption)

        # Remove Button
        self.remove_btn = ctk.CTkButton(self, text="❌", width=30, height=24,
                                        fg_color=self._c("danger", "#FF5555"),
                                        hover_color=self._c("danger_hover", "#CC0000"),
                                        command=self._on_remove)
        self.remove_btn.grid(row=0, column=2, padx=5, pady=5)

    def _c(self, key, fallback=None):
        return self.colors.get(key, fallback)

    def apply_theme(self, colors):
        self.colors = colors or {}
        self.configure(fg_color=self._c("bg_dark", "transparent"))
        self.icon_label.configure(text_color=self._c("accent", None))
        self.path_label.configure(text_color=self._c("text_main", None))
        self.caption_entry.configure(
            fg_color=self._c("card_bg", None),
            text_color=self._c("text_main", None),
            border_color=self._c("border", None),
            placeholder_text_color=self._c("text_muted", None),
        )
        self.remove_btn.configure(
            fg_color=self._c("danger", "#FF5555"),
            hover_color=self._c("danger_hover", "#CC0000"),
        )

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
    def __init__(self, master, colors=None, **kwargs):
        self.colors = colors or {}
        super().__init__(master, **kwargs)

        self.attachments = [] # List of AttachmentItem widgets

        # Header
        header = ctk.CTkFrame(self, fg_color="transparent", height=30)
        header.pack(fill="x", padx=5, pady=5)

        self.header_label = ctk.CTkLabel(header, text="المرفقات", font=("Segoe UI", 13, "bold"),
                                         text_color=self._c("text_main", None))
        self.header_label.pack(side="right", padx=5)

        # Add Buttons (Right aligned)
        self.btn_add_doc = ctk.CTkButton(
            header, text="+ ملف", width=60, height=24,
            fg_color=self._c("primary", None),
            hover_color=self._c("primary_hover", None),
            text_color=self._c("text_main", None),
            command=lambda: self.add_attachment("document"),
        )
        self.btn_add_doc.pack(side="left", padx=2)

        self.btn_add_vid = ctk.CTkButton(
            header, text="+ فيديو", width=60, height=24,
            fg_color=self._c("primary", None),
            hover_color=self._c("primary_hover", None),
            text_color=self._c("text_main", None),
            command=lambda: self.add_attachment("video"),
        )
        self.btn_add_vid.pack(side="left", padx=2)

        self.btn_add_img = ctk.CTkButton(
            header, text="+ صورة", width=60, height=24,
            fg_color=self._c("primary", None),
            hover_color=self._c("primary_hover", None),
            text_color=self._c("text_main", None),
            command=lambda: self.add_attachment("image"),
        )
        self.btn_add_img.pack(side="left", padx=2)

        self.btn_clear = ctk.CTkButton(
            header, text="مسح", width=50, height=24,
            fg_color=self._c("danger", None),
            hover_color=self._c("danger_hover", None),
            text_color=self._c("text_main", None),
            command=self.clear,
        )
        self.btn_clear.pack(side="left", padx=2)

        # List Area
        self.scroll_frame = ctk.CTkScrollableFrame(self, height=150, fg_color="transparent")
        self.scroll_frame.pack(fill="both", expand=True, padx=5, pady=5)

        self.apply_theme(self.colors)

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

    def _add_item(self, path, type_, caption=""):
        item = AttachmentItem(self.scroll_frame, path, type_, caption=caption, remove_callback=self._remove_item, colors=self.colors)
        item.pack(fill="x", pady=2)
        self.attachments.append(item)

    def _remove_item(self, item):
        if item in self.attachments:
            self.attachments.remove(item)
            item.destroy()

    def get_attachments(self):
        return [item.get_data() for item in self.attachments]

    def clear(self):
        for item in list(self.attachments):
            item.destroy()
        self.attachments = []

    def _c(self, key, fallback=None):
        return self.colors.get(key, fallback)

    def apply_theme(self, colors):
        self.colors = colors or {}
        self.header_label.configure(text_color=self._c("text_main", None))
        for btn in (self.btn_add_doc, self.btn_add_vid, self.btn_add_img):
            btn.configure(
                fg_color=self._c("primary", None),
                hover_color=self._c("primary_hover", None),
                text_color=self._c("text_main", None),
            )
        self.btn_clear.configure(
            fg_color=self._c("danger", None),
            hover_color=self._c("danger_hover", None),
            text_color=self._c("text_main", None),
        )
        for item in self.attachments:
            item.apply_theme(self.colors)

class RichTextFrame(ctk.CTkFrame):
    def __init__(self, master, colors=None, **kwargs):
        self.colors = colors or {}
        super().__init__(master, **kwargs)
        
        # Toolbar
        self.toolbar = ctk.CTkFrame(self, height=30, fg_color="transparent")
        self.toolbar.pack(fill="x", padx=5, pady=2)

        # Tools
        # Tools
        self.label = ctk.CTkLabel(self.toolbar, text="📝 Message", font=("Segoe UI", 13, "bold"),
                                  text_color=self._c("text_main", None))
        self.label.pack(side="right", padx=5)
        
        # Insert Variable
        self.var_option = ctk.CTkOptionMenu(
            self.toolbar,
            values=["{name}", "{phone}", "{var1}", "{var2}", "{var3}", "{var4}", "{var5}"],
            width=90,
            height=24,
            command=self._insert_var,
            fg_color=self._c("card_bg", None),
            button_color=self._c("primary", None),
            button_hover_color=self._c("primary_hover", None),
            text_color=self._c("text_main", None),
            dropdown_fg_color=self._c("card_bg", None),
            dropdown_text_color=self._c("text_main", None),
        )
        self.var_option.set("{var}")
        self.var_option.pack(side="left", padx=2)
        
        # Formatting buttons (Simulated for now, as CTkTextbox doesn't support rich tags easily yet)
        # We'll just insert markdown-like syntax or placeholders if user wants, 
        # but standard WhatsApp supports *bold*, _italic_, ~strike~.
        
        self.btn_bold = ctk.CTkButton(
            self.toolbar, text="B", width=30, height=24, font=("Segoe UI", 12, "bold"),
            fg_color=self._c("card_bg", None),
            hover_color=self._c("border", None),
            text_color=self._c("text_main", None),
            command=lambda: self._insert_wrap("*"),
        )
        self.btn_bold.pack(side="left", padx=2)
        
        self.btn_italic = ctk.CTkButton(
            self.toolbar, text="I", width=30, height=24, font=("Segoe UI", 12, "italic"),
            fg_color=self._c("card_bg", None),
            hover_color=self._c("border", None),
            text_color=self._c("text_main", None),
            command=lambda: self._insert_wrap("_"),
        )
        self.btn_italic.pack(side="left", padx=2)
        
        self.btn_strike = ctk.CTkButton(
            self.toolbar, text="S", width=30, height=24, font=("Segoe UI", 12, "overstrike"),
            fg_color=self._c("card_bg", None),
            hover_color=self._c("border", None),
            text_color=self._c("text_main", None),
            command=lambda: self._insert_wrap("~"),
        )
        self.btn_strike.pack(side="left", padx=2)

        # Text Area
        self.text_box = ctk.CTkTextbox(
            self,
            font=("Segoe UI", 14),
            wrap="word",
            fg_color=self._c("bg_dark", None),
            text_color=self._c("text_main", None),
            border_color=self._c("border", None),
        )
        self.text_box.pack(fill="both", expand=True, padx=5, pady=(5, 2))
        
        # Enable undo in the underlying tk.Text widget
        tb = self.text_box._textbox
        try:
            tb.configure(undo=True)
        except Exception:
            pass

        # Configure premium typography fonts and tag options
        try:
            self.font_bold = ctk.CTkFont(family="Segoe UI", size=14, weight="bold")
            self.font_italic = ctk.CTkFont(family="Segoe UI", size=14, slant="italic")
            self.font_bold_italic = ctk.CTkFont(family="Segoe UI", size=14, weight="bold", slant="italic")
            
            tb.tag_configure("bold", font=self.font_bold)
            tb.tag_configure("italic", font=self.font_italic)
            tb.tag_configure("bold_italic", font=self.font_bold_italic)
            tb.tag_configure("strike", overstrike=True)
            tb.tag_configure("variable", font=self.font_bold)
        except Exception:
            pass

        # Bind mouse click event for visual offset correction in right alignment
        tb.bind("<Button-1>", self._on_click)

        # Context Menu for Right-Click
        self.context_menu = tk.Menu(self, tearoff=0, font=("Segoe UI", 11))
        self.context_menu.add_command(label="تراجع (Undo)", command=self._undo)
        self.context_menu.add_command(label="إعادة (Redo)", command=self._redo)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="قص (Cut)", command=self._cut)
        self.context_menu.add_command(label="نسخ (Copy)", command=self._copy)
        self.context_menu.add_command(label="لصق (Paste)", command=self._paste)
        self.context_menu.add_command(label="حذف (Delete)", command=self._delete)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="تحديد الكل (Select All)", command=self._select_all)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="اتجاه القراءة من اليمين لليسار (RTL)", command=self._align_right)
        self.context_menu.add_command(label="اتجاه القراءة من اليسار لليمين (LTR)", command=self._align_left)

        self.text_box.bind("<Button-3>", self._show_context_menu)

        # Character counter
        self.char_counter = ctk.CTkLabel(
            self, text="0 حرف",
            font=("Segoe UI", 10),
            text_color=self._c("text_muted", "#888888"),
            anchor="e",
        )
        self.char_counter.pack(fill="x", padx=10, pady=(0, 4))
        self.text_box.bind("<KeyRelease>", self._update_char_count)

        self.apply_theme(self.colors)

    def _undo(self):
        try:
            self.text_box._textbox.edit_undo()
        except tk.TclError:
            pass

    def _redo(self):
        try:
            self.text_box._textbox.edit_redo()
        except tk.TclError:
            pass

    def _cut(self):
        self.text_box._textbox.event_generate("<<Cut>>")

    def _copy(self):
        self.text_box._textbox.event_generate("<<Copy>>")

    def _paste(self):
        self.text_box._textbox.event_generate("<<Paste>>")

    def _delete(self):
        try:
            self.text_box._textbox.delete("sel.first", "sel.last")
        except tk.TclError:
            pass

    def _select_all(self):
        self.text_box._textbox.tag_add("sel", "1.0", "end")

    def _show_context_menu(self, event):
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()

    def _insert_var(self, value):
        self.text_box.insert("insert", f" {value} ")
        self.var_option.set("متغير")
        self._update_char_count()

    def _insert_wrap(self, char):
        try:
            # Try to wrap selected text
            sel_start = self.text_box.index("sel.first")
            sel_end = self.text_box.index("sel.last")
            if sel_start and sel_end:
                text = self.text_box.get(sel_start, sel_end)
                self.text_box.delete(sel_start, sel_end)
                self.text_box.insert(sel_start, f"{char}{text}{char}")
                self._update_char_count()
                return
        except tk.TclError:
            pass
        
        # If no selection, just insert chars
        self.text_box.insert("insert", f"{char}{char}")
        self._update_char_count()

    def get_text(self):
        return self.text_box.get("1.0", "end").strip()
    
    def set_text(self, text):
        self.text_box.delete("1.0", "end")
        self.text_box.insert("1.0", text)
        self._update_char_count()

    def _on_click(self, event):
        """Corrects index mapping coordinate error when the text is right-justified."""
        if not getattr(self, "align_right_enabled", False):
            return
            
        tb = self.text_box._textbox
        try:
            line_start_idx = tb.index(f"@0,{event.y}")
            line_num = int(line_start_idx.split('.')[0])
        except Exception:
            return
            
        line_text = tb.get(f"{line_num}.0", f"{line_num}.end")
        num_chars = len(line_text)
        
        if num_chars == 0:
            tb.mark_set("insert", f"{line_num}.0")
            tb.focus_set()
            return "break"
            
        closest_idx = None
        min_dist = float('inf')
        matched = False
        
        # Look for exact character bounding box click match
        for col in range(num_chars + 1):
            idx = f"{line_num}.{col}"
            bbox = tb.bbox(idx)
            if bbox:
                x, y, w, h = bbox
                if x <= event.x <= x + w:
                    closest_idx = idx
                    matched = True
                    break
                    
        # Fallback to the closest character edge
        if not matched:
            for col in range(num_chars + 1):
                idx = f"{line_num}.{col}"
                bbox = tb.bbox(idx)
                if bbox:
                    x, y, w, h = bbox
                    dist_left = abs(event.x - x)
                    if dist_left < min_dist:
                        min_dist = dist_left
                        closest_idx = idx
                    dist_right = abs(event.x - (x + w))
                    if dist_right < min_dist:
                        min_dist = dist_right
                        closest_idx = f"{line_num}.{col + 1}"
                        
        if closest_idx:
            tb.mark_set("insert", closest_idx)
            tb.focus_set()
            return "break"

    def _align_right(self):
        self.align_right_enabled = True
        try:
            self.text_box._textbox.tag_configure("align_right", justify="right")
            self.text_box._textbox.tag_add("align_right", "1.0", "end")
        except Exception:
            pass

    def _align_left(self):
        self.align_right_enabled = False
        try:
            self.text_box._textbox.tag_remove("align_right", "1.0", "end")
        except Exception:
            pass

    def _update_visual_styling(self):
        """Highlights variables and formatting syntaxes dynamically in the textbox."""
        import re
        tb = self.text_box._textbox
        
        # Remove old tags
        for tag in ["bold", "italic", "bold_italic", "strike", "variable"]:
            try:
                tb.tag_remove(tag, "1.0", "end")
            except Exception:
                pass
                
        text = tb.get("1.0", "end")
        
        # 1. Variables {name}, {phone}, etc.
        for match in re.finditer(r"\{[^{}]+\}", text):
            tb.tag_add("variable", f"1.0 + {match.start()} chars", f"1.0 + {match.end()} chars")
            
        # 2. Bold *text*
        for match in re.finditer(r"\*([^*]+)\*", text):
            tb.tag_add("bold", f"1.0 + {match.start(1)} chars", f"1.0 + {match.end(1)} chars")
            
        # 3. Italic _text_
        for match in re.finditer(r"_([^_]+)_", text):
            tb.tag_add("italic", f"1.0 + {match.start(1)} chars", f"1.0 + {match.end(1)} chars")
            
        # 4. Strike ~text~
        for match in re.finditer(r"~([^~]+)~", text):
            tb.tag_add("strike", f"1.0 + {match.start(1)} chars", f"1.0 + {match.end(1)} chars")

    def _update_char_count(self, event=None):
        text = self.text_box.get("1.0", "end").strip()
        count = len(text)
        self.char_counter.configure(text=f"{count} حرف")
        self._update_visual_styling()
        if getattr(self, "align_right_enabled", False):
            try:
                self.text_box._textbox.tag_configure("align_right", justify="right")
                self.text_box._textbox.tag_add("align_right", "1.0", "end")
            except Exception:
                pass

    def _c(self, key, fallback=None):
        return self.colors.get(key, fallback)

    def apply_theme(self, colors):
        self.colors = colors or {}
        self.label.configure(text_color=self._c("text_main", None))
        self.var_option.configure(
            fg_color=self._c("card_bg", None),
            button_color=self._c("primary", None),
            button_hover_color=self._c("primary_hover", None),
            text_color=self._c("text_main", None),
            dropdown_fg_color=self._c("card_bg", None),
            dropdown_text_color=self._c("text_main", None),
        )
        for btn in (self.btn_bold, self.btn_italic, self.btn_strike):
            btn.configure(
                fg_color=self._c("card_bg", None),
                hover_color=self._c("border", None),
                text_color=self._c("text_main", None),
            )
        self.text_box.configure(
            fg_color=self._c("bg_dark", None),
            text_color=self._c("text_main", None),
            border_color=self._c("border", None),
        )
        self.char_counter.configure(text_color=self._c("text_muted", "#888888"))
        
        # Configure variable tag coloring dynamically based on active theme
        tb = self.text_box._textbox
        is_dark = self._c("appearance_mode", "dark") == "dark"
        var_bg = "#1b3f27" if is_dark else "#e2fbe8"
        var_fg = "#7effa3" if is_dark else "#155724"
        try:
            tb.tag_configure("variable", background=var_bg, foreground=var_fg)
        except Exception:
            pass
