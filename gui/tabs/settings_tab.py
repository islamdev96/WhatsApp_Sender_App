"""WhatsApp Sender Pro — Settings Tab builder module."""
import customtkinter as ctk
from gui.theme import COLORS


def build_settings_tab(self, frame: ctk.CTkFrame) -> None:
    """Build the settings components inside the Proxy & Safety tab of the popup dialog."""
    self.tab_frames["settings"] = frame

    is_ar = self.current_lang.get() == "ar"
    anchor_val = "e" if is_ar else "w"
    side_lbl = "right" if is_ar else "left"
    side_opposite = "left" if is_ar else "right"
    
    scroll = ctk.CTkScrollableFrame(frame, corner_radius=12)
    scroll.pack(fill="both", expand=True, padx=10, pady=10)

    # Hidden frame to keep required widgets in memory but not render them visually
    hidden_frame = ctk.CTkFrame(frame)
    # Note: hidden_frame is NOT packed, keeping everything inside it invisible

    self.delay_min_entry = ctk.CTkEntry(hidden_frame)
    self.delay_min_entry.insert(0, str(self.config.get("delay_min", 8)))

    self.delay_max_entry = ctk.CTkEntry(hidden_frame)
    self.delay_max_entry.insert(0, str(self.config.get("delay_max", 25)))

    self.batch_size_entry = ctk.CTkEntry(hidden_frame)
    self.batch_size_entry.insert(0, str(self.config.get("batch_size", 30)))

    self.batch_min_entry = ctk.CTkEntry(hidden_frame)
    self.batch_min_entry.insert(0, str(self.config.get("batch_pause_min", 180)))

    self.batch_max_entry = ctk.CTkEntry(hidden_frame)
    self.batch_max_entry.insert(0, str(self.config.get("batch_pause_max", 240)))

    # Reliability Settings
    reliability_card = ctk.CTkFrame(scroll, corner_radius=10)
    reliability_card.pack(fill="x", padx=10, pady=8)
    ctk.CTkLabel(reliability_card, text=self.tr("settings_reliability_title"),
                 font=ctk.CTkFont(size=14, weight="bold")).pack(anchor=anchor_val, padx=15, pady=(10, 5))

    r1 = ctk.CTkFrame(reliability_card, fg_color="transparent")
    r1.pack(fill="x", padx=15, pady=(0, 5))
    ctk.CTkLabel(r1, text=self.tr("settings_retry_count"), font=ctk.CTkFont(size=12)).pack(side=side_lbl, padx=(5, 0))
    self.retry_count_entry = ctk.CTkEntry(r1, width=70, height=34, corner_radius=8, justify="center")
    self.retry_count_entry.pack(side=side_lbl, padx=5)
    self.retry_count_entry.insert(0, str(self.config.get("max_retries", 2)))

    r2 = ctk.CTkFrame(reliability_card, fg_color="transparent")
    r2.pack(fill="x", padx=15, pady=(0, 5))
    ctk.CTkLabel(r2, text=self.tr("settings_retry_delay_from"), font=ctk.CTkFont(size=12)).pack(side=side_lbl, padx=(5, 0))
    self.retry_min_entry = ctk.CTkEntry(r2, width=70, height=34, corner_radius=8, justify="center")
    self.retry_min_entry.pack(side=side_lbl, padx=5)
    self.retry_min_entry.insert(0, str(self.config.get("retry_delay_min", 3)))

    ctk.CTkLabel(r2, text=self.tr("settings_to"), font=ctk.CTkFont(size=12)).pack(side=side_lbl, padx=(5, 0))
    self.retry_max_entry = ctk.CTkEntry(r2, width=70, height=34, corner_radius=8, justify="center")
    self.retry_max_entry.pack(side=side_lbl, padx=5)
    self.retry_max_entry.insert(0, str(self.config.get("retry_delay_max", 6)))

    r3 = ctk.CTkFrame(reliability_card, fg_color="transparent")
    r3.pack(fill="x", padx=15, pady=(0, 12))
    ctk.CTkLabel(r3, text=self.tr("settings_max_fail"), font=ctk.CTkFont(size=12)).pack(side=side_lbl, padx=(5, 0))
    self.max_fail_entry = ctk.CTkEntry(r3, width=70, height=34, corner_radius=8, justify="center")
    self.max_fail_entry.pack(side=side_lbl, padx=5)
    self.max_fail_entry.insert(0, str(self.config.get("max_consecutive_failures", 5)))

    # Rotation Settings (Multi-Account Rotation)
    rotation_card = ctk.CTkFrame(scroll, corner_radius=10)
    rotation_card.pack(fill="x", padx=10, pady=8)
    ctk.CTkLabel(rotation_card, text=self.tr("settings_rotation_title"),
                 font=ctk.CTkFont(size=14, weight="bold")).pack(anchor=anchor_val, padx=15, pady=(10, 5))

    rot_row1 = ctk.CTkFrame(rotation_card, fg_color="transparent")
    rot_row1.pack(fill="x", padx=15, pady=(0, 5))
    self.rotation_enabled_var = ctk.BooleanVar(value=self.config.get("rotation_enabled", False))
    ctk.CTkCheckBox(rot_row1, text=self.tr("settings_rotation_enabled"), 
                    variable=self.rotation_enabled_var, font=ctk.CTkFont(size=12)).pack(side=side_lbl, padx=5)

    rot_row2 = ctk.CTkFrame(rotation_card, fg_color="transparent")
    rot_row2.pack(fill="x", padx=15, pady=(0, 12))
    ctk.CTkLabel(rot_row2, text=self.tr("settings_rotation_interval"), font=ctk.CTkFont(size=12)).pack(side=side_lbl, padx=(5, 0))
    self.rotation_interval_entry = ctk.CTkEntry(rot_row2, width=70, height=34, corner_radius=8, justify="center")
    self.rotation_interval_entry.pack(side=side_lbl, padx=5)
    self.rotation_interval_entry.insert(0, str(self.config.get("rotation_interval", 50)))

    # General Settings
    general_card = ctk.CTkFrame(scroll, corner_radius=10)
    general_card.pack(fill="x", padx=10, pady=8)
    ctk.CTkLabel(general_card, text=self.tr("settings_general_title"),
                 font=ctk.CTkFont(size=14, weight="bold")).pack(anchor=anchor_val, padx=15, pady=(10, 5))

    g1 = ctk.CTkFrame(general_card, fg_color="transparent")
    g1.pack(fill="x", padx=15, pady=(0, 12))
    ctk.CTkLabel(g1, text=self.tr("settings_default_country_code"), font=ctk.CTkFont(size=12)).pack(side=side_lbl, padx=(5, 0))
    self.country_code_entry = ctk.CTkEntry(g1, width=70, height=34, corner_radius=8, justify="center")
    self.country_code_entry.pack(side=side_lbl, padx=5)
    self.country_code_entry.insert(0, str(self.config.get("default_country_code", "20")))

    # Proxy & VPN Settings Card
    proxy_card = ctk.CTkFrame(scroll, corner_radius=10)
    proxy_card.pack(fill="x", padx=10, pady=8)
    ctk.CTkLabel(proxy_card, text=self.tr("settings_proxy_title"),
                 font=ctk.CTkFont(size=14, weight="bold")).pack(anchor=anchor_val, padx=15, pady=(10, 5))

    # Checkbox and Type row
    chk_row = ctk.CTkFrame(proxy_card, fg_color="transparent")
    chk_row.pack(fill="x", padx=15, pady=(0, 5))
    
    self.proxy_enabled_var = ctk.BooleanVar(value=False)
    ctk.CTkCheckBox(chk_row, text=self.tr("settings_proxy_enabled"), variable=self.proxy_enabled_var,
                    font=ctk.CTkFont(size=12)).pack(side=side_lbl, padx=5)
                    
    self.proxy_type_var = ctk.StringVar(value="HTTP")
    ctk.CTkLabel(chk_row, text=self.tr("settings_proxy_type"), font=ctk.CTkFont(size=12)).pack(side=side_opposite, padx=(5, 0))
    self.proxy_type_menu = ctk.CTkOptionMenu(
        chk_row,
        values=["HTTP", "SOCKS5"],
        variable=self.proxy_type_var,
        width=90,
        height=28,
        fg_color=COLORS["card_bg"],
        button_color=COLORS["primary"],
        button_hover_color=COLORS["primary_hover"],
        text_color=COLORS["text_main"],
        dropdown_fg_color=COLORS["card_bg"],
        dropdown_text_color=COLORS["text_main"],
    )
    self.proxy_type_menu.pack(side=side_opposite, padx=5)

    # Host and Port row
    addr_row = ctk.CTkFrame(proxy_card, fg_color="transparent")
    addr_row.pack(fill="x", padx=15, pady=5)
    
    ctk.CTkLabel(addr_row, text=self.tr("settings_proxy_host"), font=ctk.CTkFont(size=12)).pack(side=side_lbl, padx=(5, 0))
    self.proxy_host_entry = ctk.CTkEntry(addr_row, width=200, height=34, corner_radius=8,
                                         placeholder_text="e.g. 192.168.1.1 or proxy.com")
    self.proxy_host_entry.pack(side=side_lbl, padx=5)
    
    ctk.CTkLabel(addr_row, text=self.tr("settings_proxy_port"), font=ctk.CTkFont(size=12)).pack(side=side_lbl, padx=(5, 0))
    self.proxy_port_entry = ctk.CTkEntry(addr_row, width=80, height=34, corner_radius=8,
                                        justify="center", placeholder_text="8080")
    self.proxy_port_entry.pack(side=side_lbl, padx=5)

    # Auth credentials row
    auth_row = ctk.CTkFrame(proxy_card, fg_color="transparent")
    auth_row.pack(fill="x", padx=15, pady=5)
    
    ctk.CTkLabel(auth_row, text=self.tr("settings_proxy_username"), font=ctk.CTkFont(size=12)).pack(side=side_lbl, padx=(5, 0))
    self.proxy_username_entry = ctk.CTkEntry(auth_row, width=120, height=34, corner_radius=8,
                                             placeholder_text="Username")
    self.proxy_username_entry.pack(side=side_lbl, padx=5)
    
    ctk.CTkLabel(auth_row, text=self.tr("settings_proxy_password"), font=ctk.CTkFont(size=12)).pack(side=side_lbl, padx=(5, 0))
    self.proxy_password_entry = ctk.CTkEntry(auth_row, width=120, height=34, corner_radius=8,
                                             show="*", placeholder_text="Password")
    self.proxy_password_entry.pack(side=side_lbl, padx=5)

    # Action/Test connection row
    action_row = ctk.CTkFrame(proxy_card, fg_color="transparent")
    action_row.pack(fill="x", padx=15, pady=(5, 10))
    
    self.test_proxy_btn = ctk.CTkButton(
        action_row,
        text=self.tr("settings_test_proxy"),
        width=120,
        height=32,
        fg_color=COLORS["accent"],
        hover_color=COLORS["accent_hover"],
        font=ctk.CTkFont(size=12, weight="bold"),
        command=self._test_proxy_connection
    )
    self.test_proxy_btn.pack(side=side_lbl, padx=5)
    
    self.proxy_status_label = ctk.CTkLabel(
        action_row,
        text=self.tr("settings_proxy_status"),
        font=ctk.CTkFont(size=12),
        text_color=COLORS["text_muted"]
    )
    self.proxy_status_label.pack(side=side_opposite, padx=5)

    # Fingerprint section separator
    sep = ctk.CTkFrame(proxy_card, height=2, fg_color=COLORS["border"])
    sep.pack(fill="x", padx=15, pady=8)
    
    ctk.CTkLabel(proxy_card, text=self.tr("settings_fingerprint_title"),
                 font=ctk.CTkFont(size=13, weight="bold")).pack(anchor=anchor_val, padx=15, pady=(2, 5))

    # Fingerprint toggle row
    fp_toggle_row = ctk.CTkFrame(proxy_card, fg_color="transparent")
    fp_toggle_row.pack(fill="x", padx=15, pady=2)
    
    self.fp_enabled_var = ctk.BooleanVar(value=True)
    ctk.CTkCheckBox(fp_toggle_row, text=self.tr("settings_fingerprint_enabled"), 
                    variable=self.fp_enabled_var, font=ctk.CTkFont(size=12)).pack(side=side_lbl, padx=5)

    # Fingerprint values display row
    fp_row = ctk.CTkFrame(proxy_card, fg_color="transparent")
    fp_row.pack(fill="x", padx=15, pady=5)
    
    # User-Agent read-only entry
    ctk.CTkLabel(fp_row, text=self.tr("settings_fingerprint_ua"), font=ctk.CTkFont(size=11)).pack(side=side_lbl, padx=(5, 0))
    self.fp_ua_entry = ctk.CTkEntry(fp_row, width=280, height=28, corner_radius=6, font=ctk.CTkFont(size=10))
    self.fp_ua_entry.pack(side=side_lbl, padx=5)
    
    # Resolution entry
    ctk.CTkLabel(fp_row, text=self.tr("settings_fingerprint_res"), font=ctk.CTkFont(size=11)).pack(side=side_lbl, padx=(5, 0))
    self.fp_res_entry = ctk.CTkEntry(fp_row, width=80, height=28, corner_radius=6, justify="center", font=ctk.CTkFont(size=11))
    self.fp_res_entry.pack(side=side_lbl, padx=5)
    
    # Generate new fingerprint button
    self.fp_gen_btn = ctk.CTkButton(
        fp_row,
        text=self.tr("settings_fingerprint_gen"),
        width=90,
        height=28,
        fg_color=COLORS["secondary"],
        hover_color=COLORS["secondary_hover"],
        text_color=COLORS["secondary_text"],
        font=ctk.CTkFont(size=11, weight="bold"),
        command=self._generate_new_profile_fingerprint
    )
    self.fp_gen_btn.pack(side=side_opposite, padx=5)
