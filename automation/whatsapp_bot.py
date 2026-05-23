import time
import random
import json
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager

class WhatsAppBot:
    def __init__(self, user_data_dir, proxy_config=None):
        self.user_data_dir = user_data_dir
        self.proxy_config = proxy_config
        self.driver = None
        self.background_mode = False
        self._just_launched = False

        # Common locators (mix XPath + CSS for robustness)
        self.LOGGED_IN_LOCATORS = [
            (By.ID, "pane-side"),
            (By.XPATH, '//div[@id="pane-side"]'),
            (By.XPATH, '//div[@data-testid="chat-list"]'),
            (By.XPATH, '//header[@data-testid="chatlist-header"]'),
            (By.XPATH, '//div[@id="side"]'),
            (By.XPATH, '//div[@role="grid" and contains(@class, "chat-list")]'),
        ]
        self.SEARCH_BOX_LOCATORS = [
            (By.XPATH, '//div[@contenteditable="true"][@data-tab="3"]'),
            (By.XPATH, '//div[@role="textbox" and @aria-label="Search input textbox"]'),
            (By.XPATH, '//div[@contenteditable="true" and @title="Search input textbox"]'),
        ]
        self.CHAT_INPUT_LOCATORS = [
            (By.XPATH, '//footer//div[@contenteditable="true"][@role="textbox"]'),
            (By.XPATH, '//div[@contenteditable="true"][@data-tab="10"]'),
            (By.XPATH, '//div[@contenteditable="true" and contains(@class,"copyable-text")]'),
        ]
        self.CAPTION_BOX_LOCATORS = [
            (By.XPATH, '//div[@contenteditable="true"][@data-tab="10"]'),
            (By.XPATH, '//div[@contenteditable="true" and contains(@class,"copyable-text")]'),
            (By.XPATH, '//div[@contenteditable="true" and @data-testid="media-caption-input-container"]'),
        ]
        self.SEND_BUTTON_LOCATORS = [
            (By.XPATH, '//span[@data-icon="send"]'),
            (By.XPATH, '//span[@data-icon="send-light"]'),
            (By.XPATH, '//span[contains(@data-icon,"send")]'),
            (By.XPATH, '//button[@data-testid="compose-btn-send"]'),
            (By.XPATH, '//button[@aria-label="Send"]'),
            (By.XPATH, '//button[@aria-label="إرسال"]'),
            (By.XPATH, '//div[@role="button" and @aria-label="Send"]'),
            (By.XPATH, '//div[@role="button" and @aria-label="إرسال"]'),
            (By.XPATH, '//div[@role="button" and contains(@aria-label,"Send")]'),
            (By.XPATH, '//div[@role="button" and contains(@aria-label,"إرسال")]'),
            (By.XPATH, '//button[contains(@aria-label,"Send")]'),
            (By.XPATH, '//button[contains(@aria-label,"إرسال")]'),
            (By.XPATH, '//div[@role="dialog"]//span[contains(@data-icon,"send")]'),
            (By.XPATH, '//div[@role="dialog"]//button[contains(@aria-label,"Send")]'),
            (By.XPATH, '//div[@role="dialog"]//button[contains(@aria-label,"إرسال")]'),
            (By.XPATH, '//div[@role="dialog"]//div[@role="button" and contains(@aria-label,"Send")]'),
            (By.XPATH, '//div[@role="dialog"]//div[@role="button" and contains(@aria-label,"إرسال")]'),
            (By.XPATH, '//div[@aria-label="Send"]'),
            (By.XPATH, '//div[@aria-label="إرسال"]'),
        ]
        self.ATTACH_BUTTON_LOCATORS = [
            (By.XPATH, '//span[@data-icon="clip"]'),
            (By.XPATH, '//span[@data-icon="clip-light"]'),
            (By.XPATH, '//span[@data-icon="plus"]'),
            (By.XPATH, '//span[@data-icon="plus-large"]'),
            (By.XPATH, '//span[@data-icon="attach-menu-plus"]'),
            (By.XPATH, '//div[@title="Attach"]'),
            (By.XPATH, '//div[@title="إرفاق"]'),
            (By.XPATH, '//*[@aria-label="Attach"]'),
            (By.XPATH, '//*[@aria-label="إرفاق"]'),
            (By.CSS_SELECTOR, 'span[data-icon*="clip"]'),
            (By.CSS_SELECTOR, 'span[data-icon*="plus"]'),
            (By.CSS_SELECTOR, 'button[data-testid*="clip"]'),
        ]
        self.FILE_INPUT_LOCATORS = [
            (By.XPATH, '//input[@accept="*"]'),
            (By.XPATH, '//input[@type="file" and not(contains(@accept,"image"))]'),
            (By.XPATH, '//input[@type="file"]'),
        ]
        self.PHOTO_VIDEO_INPUT_LOCATORS = [
            (By.CSS_SELECTOR, 'input[type="file"][accept*="video/mp4"][accept*="image"]'),
            (By.XPATH, '//input[@type="file" and contains(@accept,"video/mp4") and contains(@accept,"image")]'),
            (By.XPATH, '//input[@type="file" and contains(@accept,"video/quicktime") and contains(@accept,"image")]'),
            (By.XPATH, '//input[@type="file" and contains(@accept,"image/*,video/mp4,video/3gpp,video/quicktime")]'),
        ]
        self.MEDIA_PREVIEW_LOCATORS = [
            (By.XPATH, '//div[@data-testid="media-viewer"]'),
            (By.XPATH, '//div[@role="dialog"]//img'),
            (By.XPATH, '//img[contains(@src,"blob:")]'),
        ]
        self.INVALID_NUMBER_LOCATORS = [
            (By.XPATH, '//*[contains(text(),"phone number shared via url is invalid")]'),
            (By.XPATH, '//*[contains(text(),"Phone number shared via url is invalid")]'),
            (By.XPATH, '//*[contains(text(),"Invalid phone number")]'),
            (By.XPATH, '//*[contains(text(),"غير صحيح")]'),
            (By.XPATH, '//*[contains(text(),"ليس لديه واتساب")]'),
            (By.XPATH, '//*[contains(text(),"ليس لديه WhatsApp")]'),
        ]

        self._load_selectors_from_file()

    def _load_selectors_from_file(self):
        selectors_path = os.path.join(os.path.dirname(__file__), "selectors.json")
        if not os.path.exists(selectors_path):
            return
        try:
            with open(selectors_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            mode = str(data.get("mode", "merge")).lower()
            mapping = {
                "xpath": By.XPATH,
                "css": By.CSS_SELECTOR,
                "css_selector": By.CSS_SELECTOR,
                "id": By.ID,
                "name": By.NAME,
                "class": By.CLASS_NAME,
                "class_name": By.CLASS_NAME,
            }

            def _parse_list(items):
                parsed = []
                for item in items or []:
                    by = mapping.get(str(item.get("by", "")).lower())
                    value = item.get("value")
                    if by and value:
                        parsed.append((by, value))
                return parsed

            for key, value in data.items():
                if not key.endswith("_LOCATORS"):
                    continue
                parsed = _parse_list(value)
                if not parsed:
                    continue
                if hasattr(self, key):
                    if mode == "replace":
                        setattr(self, key, parsed)
                    else:
                        current = getattr(self, key)
                        setattr(self, key, current + parsed)
        except Exception:
            # If selectors file is malformed, ignore and use defaults.
            return

    def _find_any(self, locators):
        if not self.driver:
            return None
        for by, value in locators:
            try:
                elements = self.driver.find_elements(by, value)
            except Exception:
                continue
            if elements:
                return elements[0]
        return None

    def _wait_for_any(self, locators, timeout=30, poll=0.5, stop_event=None):
        end_time = time.time() + timeout
        while time.time() < end_time:
            if stop_event and stop_event.is_set():
                return None
            el = self._find_any(locators)
            if el:
                return el
            if stop_event:
                stop_event.wait(poll)
            else:
                time.sleep(poll)
        return None

    def _find_best_clickable(self, locators):
        if not self.driver:
            return None
        candidates = []
        for by, value in locators:
            try:
                candidates.extend(self.driver.find_elements(by, value))
            except Exception:
                continue
        for el in reversed(candidates):
            try:
                if el.is_displayed() and el.get_attribute("aria-disabled") != "true":
                    return el
            except Exception:
                continue
        return None

    def _find_photo_video_input(self):
        """Find the WhatsApp Photos/Videos file input, avoiding sticker inputs."""
        if not self.driver:
            return None

        for by, value in self.PHOTO_VIDEO_INPUT_LOCATORS:
            try:
                elements = self.driver.find_elements(by, value)
            except Exception:
                continue
            if elements:
                return elements[0]

        try:
            inputs = self.driver.find_elements(By.XPATH, '//input[@type="file"]')
        except Exception:
            return None

        fallback = None
        # First try exact match for Photos/Videos
        try:
            exact = self.driver.find_elements(By.XPATH, '//input[@type="file" and contains(@accept, "video/mp4") and contains(@accept, "image")]')
            if exact:
                return exact[0]
            
            # WhatsApp sometimes uses image/png,image/jpeg... for photos if they changed it
            exact2 = self.driver.find_elements(By.XPATH, '//input[@type="file" and contains(@accept, "video/3gpp")]')
            if exact2:
                return exact2[0]
        except Exception:
            pass

        fallback = None
        # Then search all inputs
        for el in inputs:
            try:
                accept = (el.get_attribute("accept") or "").lower()
            except Exception:
                accept = ""
            
            # If it's a sticker input, it usually contains webp or has a very short accept string
            if "sticker" in accept or "webp" in accept:
                continue
            
            if "video/" in accept and "image" in accept:
                return el
                
            # If it accepts images but NOT ALL files (*)
            if "image" in accept and "*" not in accept and fallback is None:
                # Still risky, might be a sticker. Let's just take the first one that has "image/*"
                if "image/*" in accept:
                    fallback = el
            elif "image" in accept and fallback is None:
                fallback = el

        return fallback

    def _wait_for_preview_close(self, timeout=5, poll=0.3, stop_event=None):
        end_time = time.time() + timeout
        while time.time() < end_time:
            if stop_event and stop_event.is_set():
                return False
            if not self._find_any(self.MEDIA_PREVIEW_LOCATORS):
                return True
            if stop_event:
                stop_event.wait(poll)
            else:
                time.sleep(poll)
        return False

    def _wait_for_chat_or_invalid(self, timeout=60, poll=0.5, stop_event=None):
        end_time = time.time() + timeout
        while time.time() < end_time:
            if stop_event and stop_event.is_set():
                return "STOPPED"
            if self._find_any(self.INVALID_NUMBER_LOCATORS):
                return "INVALID"
            if self._find_any(self.CHAT_INPUT_LOCATORS):
                return "READY"
            if stop_event:
                stop_event.wait(poll)
            else:
                time.sleep(poll)
        return "TIMEOUT"

    def is_logged_in(self):
        if not self.driver:
            return False
        if self._find_any(self.LOGGED_IN_LOCATORS) is not None:
            return True
        return self._find_any(self.SEARCH_BOX_LOCATORS) is not None or self._find_any(self.CHAT_INPUT_LOCATORS) is not None

    def setup_driver(self, start_minimized=False):
        """Initializes the Chrome driver with session persistence."""
        if not os.path.exists(self.user_data_dir):
            os.makedirs(self.user_data_dir)
            
        options = webdriver.ChromeOptions()
        options.add_argument(f"user-data-dir={self.user_data_dir}")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        
        # Open in Chrome App Mode for a clean, minimal popup window (no address bar or tabs)
        options.add_argument("--app=https://web.whatsapp.com")
        options.add_argument("--disable-notifications")
        options.add_argument("--no-first-run")
        options.add_argument("--no-default-browser-check")
        options.add_argument("--disable-sync")

        # Apply proxy settings if enabled
        is_auth_proxy = False
        if self.proxy_config and self.proxy_config.get("enabled"):
            p_type = str(self.proxy_config.get("type", "http")).lower()
            p_host = str(self.proxy_config.get("host", "")).strip()
            p_port = str(self.proxy_config.get("port", "")).strip()
            p_user = str(self.proxy_config.get("username", "")).strip()
            p_pass = str(self.proxy_config.get("password", "")).strip()
            
            if p_host and p_port:
                if p_user and p_pass:
                    is_auth_proxy = True
                    # Authenticated proxy: generate extension and load it
                    from utils.helpers import create_proxy_extension
                    ext_dir = create_proxy_extension(self.user_data_dir, p_type, p_host, p_port, p_user, p_pass)
                    options.add_argument(f"--load-extension={ext_dir}")
                else:
                    # Unauthenticated proxy
                    options.add_argument(f"--proxy-server={p_type}://{p_host}:{p_port}")

        if not is_auth_proxy:
            options.add_argument("--disable-extensions")
            
        # Apply custom fingerprint or premium default app-window size if enabled
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        if self.proxy_config and self.proxy_config.get("fingerprint_enabled"):
            user_agent = self.proxy_config.get("user_agent", user_agent)
            resolution = self.proxy_config.get("resolution", "1000,750")
            options.add_argument(f"--window-size={resolution}")
        else:
            if not start_minimized:
                options.add_argument("--window-size=1000,750")
            
        options.add_argument(f"user-agent={user_agent}")
        options.add_argument("--remote-allow-origins=*")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        # Prevent Chrome from clearing session data
        options.add_experimental_option("prefs", {
            "profile.exit_type": "Normal",
            "profile.exited_cleanly": True,
        })
        if start_minimized:
            options.add_argument("--start-minimized")
        
        # Attempt lightning-fast native driver initialization first (uses C++ compiled Selenium Manager cache)
        # This completely avoids the slow 5-10s network overhead of webdriver-manager checks.
        try:
            self.driver = webdriver.Chrome(options=options)
            self.background_mode = start_minimized
            self._just_launched = True
            return self.driver
        except Exception:
            # Fallback to slower webdriver-manager if local environment lacks native support
            try:
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=options)
                self.background_mode = start_minimized
                self._just_launched = True
                return self.driver
            except Exception as e:
                err_msg = str(e).lower()
                if "user data directory is already in use" in err_msg or "in use" in err_msg or "user data dir" in err_msg:
                    raise Exception("ERR_PROFILE_LOCKED")
                raise e

    def open_whatsapp(self):
        """Opens WhatsApp Web and waits for login."""
        if not self.driver:
            self.setup_driver()
            # If we just launched, the --app flag already loaded web.whatsapp.com automatically! No double reload.
            self._just_launched = False
        else:
            if getattr(self, "_just_launched", False):
                self._just_launched = False
                return
            try:
                if "web.whatsapp.com" not in self.driver.current_url:
                    self.driver.get("https://web.whatsapp.com")
            except Exception:
                try:
                    self.driver.get("https://web.whatsapp.com")
                except:
                    pass

    def wait_for_login(self, timeout=900):
        """Waits until the chat list is visible, indicating successful login or browser is closed."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                # Check if driver or window is closed
                if not self.driver or not self.driver.window_handles:
                    return "CLOSED"
                
                # Check if logged in
                if self.is_logged_in():
                    return "SUCCESS"
            except Exception:
                # If a webdriver exception is thrown, it usually means the browser window was closed
                return "CLOSED"
            time.sleep(1)
        return "TIMEOUT"

    def bring_to_front(self):
        """Brings the browser window to the front."""
        if self.driver:
            try:
                if self.background_mode:
                    return  # Don't bring to front in background mode
                self.driver.execute_script("window.focus();")
                self.driver.maximize_window()
            except:
                pass

    def minimize(self):
        """Minimizes the browser window."""
        if self.driver:
            try:
                self.driver.minimize_window()
            except:
                pass

    def send_message(self, phone, name, message_template, attachments=None, extra_messages=None, stop_event=None, send_text_with_image=True):
        """Sends a message and optionally multiple attachments (image, video, document)."""
        if stop_event and stop_event.is_set():
            return "STOPPED"
        if not self.driver:
            return "ERR_NOT_READY"

        # Personalize message
        message_template = message_template or ""
        message = message_template.replace("{name}", name).strip()
        
        # Attachments can be None or list
        if not attachments:
            attachments = []
        
        if not attachments and not message:
            return "ERR_EMPTY_MESSAGE"

        # 1. Open the chat
        url = f"https://web.whatsapp.com/send?phone={phone}"
        
        try:
            self.driver.get(url)
            
            # 2. Wait for loading
            ready_state = self._wait_for_chat_or_invalid(timeout=90, stop_event=stop_event)
            if ready_state == "STOPPED":
                return "STOPPED"
            if ready_state == "INVALID":
                return "INVALID"
            if ready_state == "TIMEOUT":
                return "ERR_TIMEOUT"

            if stop_event:
                stop_event.wait(random.uniform(3, 5))
            else:
                time.sleep(random.uniform(3, 5))
            if stop_event and stop_event.is_set():
                return "STOPPED"

            # 3. Send Content
            # Strategy:
            # - If attachments exist:
            #   - Send 1st attachment WITH the message as caption.
            #   - Send subsequent attachments (no caption).
            # - If no attachments:
            #   - Send text message.
            
            if attachments:
                for i, att in enumerate(attachments):
                    if stop_event and stop_event.is_set():
                        return "STOPPED"
                        
                    path = att.get("path")
                    type_ = att.get("type", "image")
                    
                    # Determine caption: prefer per-attachment caption, else first attachment uses message
                    raw_caption = att.get("caption")
                    caption = None
                    if raw_caption:
                        caption = str(raw_caption).replace("{name}", name).strip()
                    elif i == 0 and message and send_text_with_image:
                        caption = message
                    
                    # Perform Attachment
                    res = self._send_attachment(path, type_, caption, stop_event=stop_event)
                    if res != "SUCCESS":
                        return res # Fail fast or continue? Fail fast is safer for now.
                    
                    if stop_event:
                        stop_event.wait(2)
                    else:
                        time.sleep(2)
                if message and not send_text_with_image:
                    text_res = self._send_text(message, stop_event=stop_event)
                    if text_res != "SUCCESS":
                        return text_res
                # Send extra messages (if any)
                if extra_messages:
                    for m in extra_messages:
                        if stop_event and stop_event.is_set():
                            return "STOPPED"
                        if not m:
                            continue
                        text_res = self._send_text(m, stop_event=stop_event)
                        if text_res != "SUCCESS":
                            return text_res
                        if stop_event:
                            stop_event.wait(0.4)
                        else:
                            time.sleep(0.4)
                return "SUCCESS"
            else:
                # Text Only
                res = self._send_text(message, stop_event=stop_event)
                if res != "SUCCESS":
                    return res
                if extra_messages:
                    for m in extra_messages:
                        if stop_event and stop_event.is_set():
                            return "STOPPED"
                        if not m:
                            continue
                        text_res = self._send_text(m, stop_event=stop_event)
                        if text_res != "SUCCESS":
                            return text_res
                        if stop_event:
                            stop_event.wait(0.4)
                        else:
                            time.sleep(0.4)
                return "SUCCESS"

        except Exception as e:
            return f"ERR_GENERAL: {str(e)[:100]}"

    def check_number(self, phone, stop_event=None):
        """Checks if a phone number has WhatsApp without sending a message."""
        if stop_event and stop_event.is_set():
            return "STOPPED"
        if not self.driver:
            return "ERR_NOT_READY"
        url = f"https://web.whatsapp.com/send?phone={phone}"
        try:
            self.driver.get(url)
            ready_state = self._wait_for_chat_or_invalid(timeout=45, stop_event=stop_event)
            if ready_state == "INVALID":
                return "INVALID"
            if ready_state == "READY":
                return "VALID"
            if ready_state == "STOPPED":
                return "STOPPED"
            return "ERR_TIMEOUT"
        except Exception as e:
            return f"ERR_GENERAL: {str(e)[:100]}"

    def _send_attachment(self, path, media_type, caption=None, stop_event=None):
        """Internal method to upload a single file."""
        if stop_event and stop_event.is_set():
            return "STOPPED"
        try:
            # 1. Click Attach Button
            attach_btn = self._find_best_clickable(self.ATTACH_BUTTON_LOCATORS) or self._find_any(self.ATTACH_BUTTON_LOCATORS)
            if not attach_btn:
                return "ERR_ATTACH_BTN_NOT_FOUND"
            if stop_event and stop_event.is_set():
                return "STOPPED"
            self.driver.execute_script("arguments[0].click();", attach_btn)
            if stop_event:
                stop_event.wait(1.0)
            else:
                time.sleep(1.0)
            
            # 2. Choose Input based on type
            # Photos/Videos usually input[accept*='image']
            # Documents usually input[accept='*'] or specific click
            
            input_el = None
            
            if media_type == 'document':
                # Try to find the Document button in the menu and click it to trigger input
                # Common selectors for "Document" button in the attach menu
                doc_btn_locators = [
                    (By.XPATH, '//span[@data-icon="attach-document"]'),
                    (By.XPATH, '//li//*[contains(text(),"Document")]'),
                    (By.XPATH, '//li//*[contains(text(),"مستند")]'),
                    (By.CSS_SELECTOR, 'span[data-icon="attach-document"]'),
                ]
                if stop_event and stop_event.is_set():
                    return "STOPPED"
                doc_btn = self._find_any(doc_btn_locators)
                if doc_btn:
                     self.driver.execute_script("arguments[0].click();", doc_btn)
                
                # Check for file input
                input_el = self._wait_for_any(self.FILE_INPUT_LOCATORS, timeout=5, stop_event=stop_event)
            else:
                # Image/Video - usually top button "Photos & Videos"
                # But typically the file input is present and works for images if we just send keys
                # We can try clicking the "Photos & Videos" button first for robustness
                media_btn_locators = [
                    (By.XPATH, '//span[@data-icon="attach-image"]'),
                    (By.XPATH, '//button[@aria-label="Photos & videos"]'),
                    (By.XPATH, '//div[@aria-label="Photos & videos"]'),
                    (By.XPATH, '//li//*[contains(text(),"Photos & videos")]'),
                    (By.XPATH, '//li//*[contains(text(),"Photos")]'),
                    (By.XPATH, '//li//*[contains(text(),"صور")]'),
                    (By.XPATH, '//li//*[contains(text(),"الصور")]'),
                    (By.XPATH, '//li//*[contains(text(),"صور")]'),
                ]
                if stop_event and stop_event.is_set():
                    return "STOPPED"
                media_btn = self._find_any(media_btn_locators)
                if media_btn:
                    self.driver.execute_script("arguments[0].click();", media_btn)
                    
                end_time = time.time() + 5
                while time.time() < end_time and not input_el:
                    if stop_event and stop_event.is_set():
                        return "STOPPED"
                    input_el = self._find_photo_video_input()
                    if stop_event:
                        stop_event.wait(0.2)
                    else:
                        time.sleep(0.2)

            if stop_event and stop_event.is_set():
                return "STOPPED"

            if not input_el:
                if media_type == 'document':
                    # Fallback: try finding any file input on page
                    input_el = self.driver.find_element(By.XPATH, '//input[@type="file"]')
                else:
                    input_el = self._find_photo_video_input()
            
            if not input_el:
                return "ERR_FILE_INPUT_NOT_FOUND"

            # 3. Send Keys
            input_el.send_keys(path)
            
            # 4. Wait for Preview (Media) or File Dialog (Doc)
            # Docs often have a different preview or simple "Send" icon
            # Media has the full editor.
            
            if media_type == 'document':
                 # Document preview is just a small box with send button
                 send_btn = self._find_best_clickable(self.SEND_BUTTON_LOCATORS) or self._wait_for_any(self.SEND_BUTTON_LOCATORS, timeout=15, stop_event=stop_event)
                 if not send_btn:
                     return "ERR_DOC_SEND_BTN_NOT_FOUND"
            else:
                # Media Preview
                self._wait_for_any(self.MEDIA_PREVIEW_LOCATORS, timeout=40, stop_event=stop_event)
                if stop_event and stop_event.is_set():
                    return "STOPPED"
                if caption:
                    caption_box = self._wait_for_any(self.CAPTION_BOX_LOCATORS, timeout=10, stop_event=stop_event)
                    if caption_box:
                        if stop_event:
                            stop_event.wait(0.5)
                        else:
                            time.sleep(0.5)
                        if stop_event and stop_event.is_set():
                            return "STOPPED"
                        caption_box.send_keys(caption)
                        if stop_event:
                            stop_event.wait(1.0)
                        else:
                            time.sleep(1.0)
                
                send_btn = self._find_best_clickable(self.SEND_BUTTON_LOCATORS) or self._wait_for_any(self.SEND_BUTTON_LOCATORS, timeout=15, stop_event=stop_event)
            
            if not send_btn:
                return "ERR_SEND_BTN_NOT_FOUND"
            
            if stop_event and stop_event.is_set():
                return "STOPPED"
                
            self.driver.execute_script("arguments[0].click();", send_btn)
            
            # Wait for upload/processing - dynamically based on file size
            file_size = os.path.getsize(path) if os.path.exists(path) else 0
            wait_time = max(3, min(30, file_size // (1024 * 1024)))  # 1s per MB, min 3s, max 30s
            if stop_event:
                stop_event.wait(wait_time)
            else:
                time.sleep(wait_time)
            
            # Close preview if stuck (rare for docs, common for media)
            if media_type != 'document':
                 self._wait_for_preview_close(timeout=10, stop_event=stop_event)
                 
            return "SUCCESS"
            
        except Exception as e:
            return f"ERR_ATTACH_{media_type.upper()}: {str(e)[:50]}"

    def _human_type(self, element, text, stop_event=None):
        """Types text like a human with random delays."""
        for char in text:
            if stop_event and stop_event.is_set():
                break
            element.send_keys(char)
            if stop_event:
                stop_event.wait(random.uniform(0.05, 0.2))
            else:
                time.sleep(random.uniform(0.05, 0.2))

    def _random_scroll(self, stop_event=None):
        """Simulates random scrolling in the chat list to mimic human activity."""
        try:
            # Find chat/side pane
            pane = self._find_any([
                (By.ID, "pane-side"),
                (By.XPATH, '//div[@id="pane-side"]'),
            ])
            if pane:
                self.driver.execute_script("arguments[0].scrollTop += arguments[1]", pane, random.randint(100, 300))
                if stop_event:
                    stop_event.wait(random.uniform(0.5, 1.5))
                else:
                    time.sleep(random.uniform(0.5, 1.5))
                self.driver.execute_script("arguments[0].scrollTop -= arguments[1]", pane, random.randint(50, 150))
        except:
            pass

    def _send_text(self, message, stop_event=None):
        if stop_event and stop_event.is_set():
            return "STOPPED"
        try:
            chat_input = self._wait_for_any(self.CHAT_INPUT_LOCATORS, timeout=30, stop_event=stop_event)
            if not chat_input:
                return "ERR_CHAT_INPUT_NOT_FOUND"
            
            if stop_event and stop_event.is_set():
                return "STOPPED"
            chat_input.click()
            if stop_event:
                stop_event.wait(0.5)
            else:
                time.sleep(0.5)
            
            if stop_event and stop_event.is_set():
                return "STOPPED"
            # Use human typing for shorter messages to avoid detection
            if len(message) < 200:
                self._human_type(chat_input, message, stop_event=stop_event)
            else:
                chat_input.send_keys(message) # Paste long messages
                
            if stop_event:
                stop_event.wait(0.5)
            else:
                time.sleep(0.5)

            if stop_event and stop_event.is_set():
                return "STOPPED"

            send_btn = self._find_best_clickable(self.SEND_BUTTON_LOCATORS) or self._wait_for_any(self.SEND_BUTTON_LOCATORS, timeout=10, stop_event=stop_event)
            if send_btn:
                try:
                    send_btn.click()
                except:
                    self.driver.execute_script("arguments[0].click();", send_btn)
            else:
                # Fallback Enter
                chat_input.send_keys(Keys.ENTER)
                
            if stop_event:
                stop_event.wait(1.0)
            else:
                time.sleep(1.0)
            self._random_scroll(stop_event=stop_event) # Scroll a bit after sending
            return "SUCCESS"
        except Exception as e:
            return f"ERR_TEXT_SEND: {str(e)[:50]}"

    def close(self):
        """Safely close the browser, ensuring session data is saved."""
        if self.driver:
            try:
                # Give Chrome a moment to flush any pending writes
                time.sleep(0.5)
                self.driver.quit()
            except Exception:
                pass
            finally:
                self.driver = None
    # â”€â”€â”€ Chatbot Methods â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    def get_unread_chats(self):
        """Returns a list of unread chat elements."""
        if not self.driver:
            return []
        
        try:
            # Common locators for unread badge in WhatsApp Web
            unread_locators = [
                (By.XPATH, '//span[contains(@aria-label, "unread message")]'),
                (By.XPATH, '//span[contains(@aria-label, "Ø±Ø³Ø§Ù„Ø© ØºÙŠØ± Ù…Ù‚Ø±ÙˆØ¡Ø©")]'),
                (By.XPATH, '//span[contains(@aria-label, "Ø±Ø³Ø§Ù„Ø© ØºÙŠØ± Ù…Ù‚Ø±ÙˆØ¡Ø©")]/ancestor::div[@role="listitem"]'),
                (By.XPATH, '//span[contains(@aria-label, "unread message")]/ancestor::div[@role="listitem"]'),
                (By.XPATH, '//div[contains(@aria-label, "unread message")]'),
                (By.XPATH, '//div[contains(@aria-label, "Ø±Ø³Ø§Ù„Ø© ØºÙŠØ± Ù…Ù‚Ø±ÙˆØ¡Ø©")]')
            ]
            
            for loc_type, loc_val in unread_locators:
                elements = self.driver.find_elements(loc_type, loc_val)
                # Filter valid clickables (list items usually)
                valid_elements = []
                for el in elements:
                    try:
                        # try to find the closest ancestor with role="listitem" or just return the element if it's clickable
                        if el.is_displayed():
                            valid_elements.append(el)
                    except:
                        pass
                if valid_elements:
                    return valid_elements
            return []
        except Exception:
            return []

    def open_chat(self, chat_element):
        """Clicks on a chat element to open it."""
        try:
            self.driver.execute_script("arguments[0].click();", chat_element)
            time.sleep(1) # wait for chat to load
            return True
        except Exception:
            return False

    def check_number_validity(self, phone):
        """Checks if a phone number has a WhatsApp account by navigating to wa.me link and checking for errors."""
        try:
            url = f"https://web.whatsapp.com/send?phone={phone}"
            self.driver.get(url)
            
            # Wait for either the chat to open or the invalid number popup
            try:
                # Look for the modal indicating the number is invalid
                WebDriverWait(self.driver, 10).until(
                    lambda d: d.find_element(By.XPATH, '//div[@data-animate-modal-popup="true"]') or 
                              d.find_element(By.XPATH, '//div[@title="Type a message"]') or
                              d.find_element(By.XPATH, '//div[@title="اكتب رسالة"]') or
                              "Phone number shared via url is invalid." in d.page_source or
                              "رقم الهاتف الذي تمت مشاركته عبر الرابط غير صحيح" in d.page_source
                )
            except:
                pass # Timeout, let's check page source directly

            time.sleep(1) # Give it a moment to render
            
            # If we find the invalid text anywhere in the page source, it's invalid
            if "invalid" in self.driver.page_source.lower() or "غير صحيح" in self.driver.page_source:
                # Click OK button to close modal if exists
                try:
                    btn = self.driver.find_element(By.XPATH, '//div[@data-animate-modal-popup="true"]//button')
                    btn.click()
                except:
                    pass
                return False
                
            # Otherwise, assume valid (chat input is probably visible)
            return True
        except Exception as e:
            return False

    def read_last_message(self):
        """Reads the last incoming message in the currently open chat."""
        if not self.driver:
            return ""
            
        try:
            # Locate incoming messages
            # 'message-in' is a common class for incoming messages
            in_msgs = self.driver.find_elements(By.XPATH, '//div[contains(@class, "message-in")]')
            if not in_msgs:
                return ""
            
            last_msg_container = in_msgs[-1]
            
            # Find the actual text span within the message container
            # Usually it's inside a span with class "selectable-text copyable-text"
            text_spans = last_msg_container.find_elements(By.XPATH, './/span[contains(@class, "selectable-text") and contains(@class, "copyable-text")]')
            
            if text_spans:
                # The text is usually the inner text of the last span or we can just combine them
                return " ".join([span.text for span in text_spans]).strip()
            else:
                return ""
        except Exception:
            return ""

    def reply_to_current_chat(self, message):
        """Sends a message to the currently open chat."""
        # Just use the existing _send_text which looks for the chat input and sends
        return self._send_text(message)
