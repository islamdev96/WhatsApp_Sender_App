"""WhatsApp Sender Pro — Google Maps Scraper Tab builder module.

Provides a dedicated tab for scraping business phone numbers from Google Maps search results.
"""
import customtkinter as ctk
from tkinter import ttk, filedialog, messagebox
import threading
import os
import csv
import datetime
import urllib.parse
from selenium import webdriver
from selenium.webdriver.chrome.service import Service

from gui.theme import COLORS
from utils.logger import logger
from automation.gmaps_scraper import GMapsScraper


def build_gmaps_tab(self, frame: ctk.CTkFrame) -> None:
    """Build the Google Maps Scraper tab."""
    self.tab_frames["gmaps"] = frame

    is_ar = self.current_lang.get() == "ar"
    anchor_val = "e" if is_ar else "w"
    side_lbl = "right" if is_ar else "left"
    side_opp = "left" if is_ar else "right"

    # ── Header ──
    header_frame = ctk.CTkFrame(frame, fg_color="transparent")
    header_frame.pack(fill="x", padx=20, pady=(15, 5))

    ctk.CTkLabel(
        header_frame, text=self.tr("gmaps_header"),
        font=ctk.CTkFont(size=20, weight="bold")
    ).pack(side=side_lbl, padx=5)

    ctk.CTkLabel(
        header_frame, text=self.tr("gmaps_desc"),
        font=ctk.CTkFont(size=12), text_color=COLORS["text_muted"]
    ).pack(side=side_lbl, padx=15)

    # ── Controls Row ──
    controls_frame = ctk.CTkFrame(frame, corner_radius=12)
    controls_frame.pack(fill="x", padx=20, pady=(10, 5))

    ctrl_inner = ctk.CTkFrame(controls_frame, fg_color="transparent")
    ctrl_inner.pack(fill="x", padx=15, pady=12)

    # Query Input
    ctk.CTkLabel(
        ctrl_inner, text=self.tr("gmaps_search_placeholder") + ":",
        font=ctk.CTkFont(size=12, weight="bold")
    ).pack(side=side_lbl, padx=5)

    self.gmaps_query_entry = ctk.CTkEntry(
        ctrl_inner, height=36, corner_radius=8,
        placeholder_text=self.tr("gmaps_search_placeholder"),
        font=ctk.CTkFont(size=12), width=300
    )
    self.gmaps_query_entry.pack(side=side_lbl, padx=5)

    # Limit Input
    ctk.CTkLabel(
        ctrl_inner, text=self.tr("gmaps_limit") + ":",
        font=ctk.CTkFont(size=12, weight="bold")
    ).pack(side=side_lbl, padx=5)

    self.gmaps_limit_entry = ctk.CTkEntry(
        ctrl_inner, height=36, corner_radius=8,
        font=ctk.CTkFont(size=12), width=80
    )
    self.gmaps_limit_entry.pack(side=side_lbl, padx=5)
    self.gmaps_limit_entry.insert(0, "50")

    # ── Table ──
    table_frame = ctk.CTkFrame(frame, corner_radius=12)
    table_frame.pack(fill="both", expand=True, padx=20, pady=5)

    columns = ("name", "phone")
    self.gmaps_tree = ttk.Treeview(
        table_frame, columns=columns, show="headings",
        selectmode="extended", height=15
    )
    self.gmaps_tree.heading("name", text=self.tr("gmaps_col_name"))
    self.gmaps_tree.heading("phone", text=self.tr("gmaps_col_phone"))

    self.gmaps_tree.column("name", width=350, anchor=anchor_val)
    self.gmaps_tree.column("phone", width=250, anchor="center")

    scrollbar = ctk.CTkScrollbar(table_frame, command=self.gmaps_tree.yview)
    self.gmaps_tree.configure(yscrollcommand=scrollbar.set)

    self.gmaps_tree.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=10)
    scrollbar.pack(side="right", fill="y", padx=(0, 10), pady=10)

    # ── Progress & Status Footer ──
    progress_frame = ctk.CTkFrame(frame, corner_radius=12)
    progress_frame.pack(fill="x", padx=20, pady=5)

    prog_inner = ctk.CTkFrame(progress_frame, fg_color="transparent")
    prog_inner.pack(fill="x", padx=15, pady=10)

    self.gmaps_status_lbl = ctk.CTkLabel(
        prog_inner, text=self.tr("gmaps_found_count").format(count=0),
        font=ctk.CTkFont(size=12, weight="bold")
    )
    self.gmaps_status_lbl.pack(side=side_lbl, padx=8)

    # ── Actions ──
    action_frame = ctk.CTkFrame(frame, fg_color="transparent")
    action_frame.pack(fill="x", padx=20, pady=(5, 15))

    self.gmaps_start_btn = ctk.CTkButton(
        action_frame, text=self.tr("gmaps_btn_start"),
        font=ctk.CTkFont(size=14, weight="bold"),
        width=160, height=42, corner_radius=10,
        fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"],
        text_color="#FFFFFF",
        command=lambda: _start_scraping()
    )
    self.gmaps_start_btn.pack(side=side_lbl, padx=5)

    self.gmaps_stop_btn = ctk.CTkButton(
        action_frame, text=self.tr("gmaps_btn_stop"),
        font=ctk.CTkFont(size=14, weight="bold"),
        width=120, height=42, corner_radius=10,
        fg_color=COLORS["danger"], hover_color=COLORS["danger_hover"],
        text_color="#FFFFFF",
        state="disabled",
        command=lambda: _stop_scraping()
    )
    self.gmaps_stop_btn.pack(side=side_lbl, padx=5)

    # Import button
    ctk.CTkButton(
        action_frame, text=self.tr("gmaps_btn_import"),
        font=ctk.CTkFont(size=12, weight="bold"),
        width=180, height=42, corner_radius=10,
        fg_color="#00A884", hover_color="#008F6F",
        text_color="#FFFFFF",
        command=lambda: _import_to_campaign()
    ).pack(side=side_opp, padx=5)

    # Export button
    ctk.CTkButton(
        action_frame, text=self.tr("gmaps_btn_export"),
        font=ctk.CTkFont(size=12),
        width=130, height=42, corner_radius=10,
        fg_color=COLORS["secondary"], hover_color=COLORS["secondary_hover"],
        text_color=COLORS["secondary_text"],
        command=lambda: _export_scraped()
    ).pack(side=side_opp, padx=5)

    # State variables
    self._gmaps_stop_event = threading.Event()
    self._gmaps_running = False
    self._gmaps_driver = None

    def _start_scraping():
        query = self.gmaps_query_entry.get().strip()
        if not query:
            messagebox.showwarning(self.tr("msg_alert"), self.tr("gmaps_search_placeholder"))
            return

        try:
            limit = int(self.gmaps_limit_entry.get().strip())
        except ValueError:
            limit = 50

        # Clear existing
        for item in self.gmaps_tree.get_children():
            self.gmaps_tree.delete(item)

        self._gmaps_stop_event.clear()
        self._gmaps_running = True
        self.gmaps_start_btn.configure(state="disabled")
        self.gmaps_stop_btn.configure(state="normal")
        self.gmaps_status_lbl.configure(text=self.tr("gmaps_status_scraping"))

        def _thread_run():
            # Set up Chrome Options for Maps Scraping
            options = webdriver.ChromeOptions()
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--window-size=1000,750")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)

            driver = None
            try:
                try:
                    driver = webdriver.Chrome(options=options)
                except Exception:
                    # Fallback to webdriver manager
                    from webdriver_manager.chrome import ChromeDriverManager
                    service = Service(ChromeDriverManager().install())
                    driver = webdriver.Chrome(service=service, options=options)

                self._gmaps_driver = driver
                scraper = GMapsScraper(driver)

                def update_callback(status, data):
                    if status == "FOUND":
                        name = data.get("name", "Unknown")
                        phone = data.get("phone", "")
                        count = data.get("count", 0)
                        self._run_on_ui(lambda: (
                            self.gmaps_tree.insert("", "end", values=(name, phone)),
                            self.gmaps_status_lbl.configure(
                                text=self.tr("gmaps_found_count").format(count=count)
                            )
                        ))
                    elif status == "ERROR":
                        self._run_on_ui(lambda: messagebox.showerror(self.tr("msg_error"), str(data)))

                results = scraper.scrape(
                    query=query,
                    stop_event=self._gmaps_stop_event,
                    max_results=limit,
                    update_callback=update_callback
                )

                self._run_on_ui(lambda: (
                    self.gmaps_status_lbl.configure(
                        text=self.tr("gmaps_status_complete") + " " + self.tr("gmaps_found_count").format(count=len(results))
                    )
                ))

            except Exception as e:
                logger.debug("Google Maps scraper crash: %s", e)
                self._run_on_ui(lambda: messagebox.showerror(self.tr("msg_error"), str(e)))
            finally:
                if driver:
                    try:
                        driver.quit()
                    except Exception:
                        pass
                self._gmaps_driver = None
                self._gmaps_running = False
                self._run_on_ui(lambda: (
                    self.gmaps_start_btn.configure(state="normal"),
                    self.gmaps_stop_btn.configure(state="disabled")
                ))

        t = threading.Thread(target=_thread_run, daemon=True)
        t.start()

    def _stop_scraping():
        self._gmaps_stop_event.set()
        if self._gmaps_driver:
            try:
                self._gmaps_driver.quit()
            except Exception:
                pass
        self.gmaps_stop_btn.configure(state="disabled")
        self.gmaps_status_lbl.configure(text=self.tr("gmaps_status_stopped"))

    def _import_to_campaign():
        items = self.gmaps_tree.get_children()
        if not items:
            messagebox.showwarning(self.tr("msg_alert"), "لا توجد أرقام صالحة للاستيراد.")
            return

        count = 0
        if hasattr(self, "progress_tree") and self.progress_tree:
            existing = [self.progress_tree.item(i, "values")[1] for i in self.progress_tree.get_children() if len(self.progress_tree.item(i, "values")) > 1]
            for item in items:
                name, phone = self.gmaps_tree.item(item, "values")
                if phone:
                    if phone not in existing:
                        self.progress_tree.insert(
                            "", "end", values=(name, phone, "", "⏳ معلق"),
                            tags=("pending",)
                        )
                        existing.append(phone)
                        count += 1

            self._update_contacts_count_from_tree()
            messagebox.showinfo(self.tr("msg_done"), f"تم استيراد {count} جهة اتصال بنجاح!")
            self.log(f"📥 Imported {count} scraped business contacts to current campaign list.")
        else:
            messagebox.showerror("خطأ", "تعذر تحديد قائمة الإرسال الرئيسية.")

    def _export_scraped():
        items = self.gmaps_tree.get_children()
        if not items:
            return

        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv")],
            initialfile=f"gmaps_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )
        if not filepath:
            return

        try:
            with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow([self.tr("gmaps_col_name"), self.tr("gmaps_col_phone")])
                for item in items:
                    writer.writerow(self.gmaps_tree.item(item, "values"))
            self.log(f"📤 Exported Google Maps scraper results.")
        except Exception as exc:
            messagebox.showerror(self.tr("msg_error"), str(exc))
