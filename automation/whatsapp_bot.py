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
        self._last_opened_phone = None

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
            (By.XPATH, '//footer//div[@contenteditable="true"][@data-tab="10"]'),
            (By.XPATH, '//footer//div[@contenteditable="true" and contains(@class,"copyable-text")]'),
        ]
        self.CAPTION_BOX_LOCATORS = [
            (By.XPATH, '//div[@data-testid="media-viewer"]//div[@data-testid="media-caption-input-container"]//div[@contenteditable="true"]'),
            (By.XPATH, '//div[@data-testid="media-viewer"]//div[@contenteditable="true"][@role="textbox"]'),
            (By.XPATH, '//div[@role="dialog"]//div[@data-testid="media-caption-input-container"]//div[@contenteditable="true"]'),
            (By.XPATH, '//div[@role="dialog"][.//img or .//video]//div[@contenteditable="true"][@role="textbox"]'),
            (By.XPATH, '//div[@role="dialog"]//*[@data-testid="media-caption-input-container"]//div[@contenteditable="true"]'),
        ]
        self.MEDIA_PREVIEW_SEND_BUTTON_LOCATORS = [
            (By.XPATH, '//div[@data-testid="media-viewer"]//span[@data-icon="send"]'),
            (By.XPATH, '//div[@data-testid="media-viewer"]//span[@data-icon="send-light"]'),
            (By.XPATH, '//div[@data-testid="media-viewer"]//button[@aria-label="Send"]'),
            (By.XPATH, '//div[@data-testid="media-viewer"]//button[@aria-label="إرسال"]'),
            (By.XPATH, '//div[@data-testid="media-viewer"]//div[@role="button" and @aria-label="Send"]'),
            (By.XPATH, '//div[@data-testid="media-viewer"]//div[@role="button" and @aria-label="إرسال"]'),
            (By.XPATH, '//div[@role="dialog"]//span[@data-icon="send"]'),
            (By.XPATH, '//div[@role="dialog"]//span[@data-icon="send-light"]'),
            (By.XPATH, '//div[@role="dialog"]//button[@aria-label="Send"]'),
            (By.XPATH, '//div[@role="dialog"]//button[@aria-label="إرسال"]'),
            (By.XPATH, '//div[@role="dialog"]//div[@role="button" and @aria-label="Send"]'),
            (By.XPATH, '//div[@role="dialog"]//div[@role="button" and @aria-label="إرسال"]'),
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
            (By.CSS_SELECTOR, 'footer span[data-icon="attach-menu-plus"]'),
            (By.XPATH, '//footer//span[@data-icon="attach-menu-plus"]'),
            (By.CSS_SELECTOR, 'footer span[data-icon*="clip"]'),
            (By.XPATH, '//footer//span[@data-icon="clip"]'),
            (By.XPATH, '//footer//span[@data-icon="clip-light"]'),
            (By.XPATH, '//footer//*[@aria-label="Attach"]'),
            (By.XPATH, '//footer//*[@aria-label="إرفاق"]'),
            (By.XPATH, '//footer//div[@title="Attach"]'),
            (By.XPATH, '//footer//div[@title="إرفاق"]'),
            (By.CSS_SELECTOR, 'footer button[data-testid*="clip"]'),
        ]
        self.FILE_INPUT_LOCATORS = [
            (By.XPATH, '//input[@type="file" and @accept="*"]'),
            (By.XPATH, '//input[@type="file" and not(contains(@accept,"image")) and not(contains(@accept,"video"))]'),
        ]
        self.PHOTO_VIDEO_INPUT_LOCATORS = [
            (By.XPATH, '//input[@type="file" and contains(@accept,"video/mp4")]'),
            (By.XPATH, '//input[@type="file" and contains(@accept,"video/3gpp")]'),
            (By.XPATH, '//input[@type="file" and contains(@accept,"video/quicktime")]'),
        ]
        self.STICKER_PANEL_LOCATORS = [
            (By.XPATH, '//span[@data-icon="sticker"]'),
            (By.XPATH, '//span[@data-icon="sticker-add"]'),
            (By.XPATH, '//span[@data-icon="wds-ic-sticker"]'),
            (By.XPATH, '//div[@data-testid="sticker-panel"]'),
            (By.XPATH, '//*[@data-testid="sticker-maker"]'),
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
        """Returns the FIRST visible, enabled element matching any locator.
        Locators should be ordered most-specific-first so the best match wins."""
        if not self.driver:
            return None
        for by, value in locators:
            try:
                elements = self.driver.find_elements(by, value)
            except Exception:
                continue
            for el in elements:
                try:
                    if el.is_displayed() and el.get_attribute("aria-disabled") != "true":
                        return el
                except Exception:
                    continue
        return None

    @staticmethod
    def _file_input_signature(el):
        try:
            return (
                el.get_attribute("name") or "",
                el.get_attribute("id") or "",
                el.get_attribute("accept") or "",
            )
        except Exception:
            return None

    @staticmethod
    def _accept_is_sticker_only(accept):
        """Sticker maker accepts images only — never video/mp4/3gpp/quicktime."""
        accept = (accept or "").lower()
        if not accept:
            return False
        if "sticker" in accept:
            return True
        video_markers = ("video/mp4", "video/3gpp", "video/quicktime", "video/*")
        if any(marker in accept for marker in video_markers):
            return False
        if "image" in accept:
            return True
        return False

    @staticmethod
    def _accept_is_photo_video(accept):
        accept = (accept or "").lower()
        return any(
            marker in accept
            for marker in ("video/mp4", "video/3gpp", "video/quicktime", "video/*")
        )

    @staticmethod
    def _accept_is_document(accept):
        accept = (accept or "").lower().strip()
        if not accept:
            return False
        if WhatsAppBot._accept_is_sticker_only(accept):
            return False
        if WhatsAppBot._accept_is_photo_video(accept):
            return False
        return accept in ("*", "*/*") or ("image" not in accept and "video" not in accept)

    def _snapshot_file_input_signatures(self):
        try:
            inputs = self.driver.find_elements(By.XPATH, '//input[@type="file"]')
        except Exception:
            return set()
        signatures = set()
        for el in inputs:
            sig = self._file_input_signature(el)
            if sig:
                signatures.add(sig)
        return signatures

    def _classify_file_input(self, el):
        try:
            accept = el.get_attribute("accept") or ""
            name = (el.get_attribute("name") or "").lower()
            input_id = (el.get_attribute("id") or "").lower()
        except Exception:
            return None
        if "sticker" in name or "sticker" in input_id or "sticker" in accept.lower():
            return "sticker"
        if self._accept_is_sticker_only(accept):
            return "sticker"
        if self._accept_is_photo_video(accept):
            return "media"
        if self._accept_is_document(accept):
            return "document"
        return None

    def _find_file_input(self, kind, exclude_signatures=None):
        exclude_signatures = exclude_signatures or set()
        try:
            inputs = self.driver.find_elements(By.XPATH, '//input[@type="file"]')
        except Exception:
            return None

        for el in inputs:
            sig = self._file_input_signature(el)
            if not sig or sig in exclude_signatures:
                continue
            if self._classify_file_input(el) == kind:
                return el
        return None

    def _find_file_input_in_attach_menu(self, kind):
        """Locate file input nested under the matching attach-menu row."""
        icon = "attach-document" if kind == "document" else "attach-image"
        xpaths = [
            f'//footer//li[.//span[@data-icon="{icon}"]]//input[@type="file"]',
            f'//li[.//span[@data-icon="{icon}"]]//input[@type="file"]',
            f'//*[.//span[@data-icon="{icon}"]]//input[@type="file"]',
        ]
        for xpath in xpaths:
            try:
                for el in self.driver.find_elements(By.XPATH, xpath):
                    if self._classify_file_input(el) == kind:
                        return el
            except Exception:
                continue
        return None

    def _wait_for_file_input_in_attach_menu(self, kind, timeout=3, stop_event=None):
        end_time = time.time() + timeout
        while time.time() < end_time:
            if stop_event and stop_event.is_set():
                return None
            found = self._find_file_input_in_attach_menu(kind)
            if found:
                return found
            if stop_event:
                stop_event.wait(0.2)
            else:
                time.sleep(0.2)
        return None

    def _js_activate_attach_menu_option(self, data_icon):
        """Activate Photos/Document row via JS on the menu <li>, not Selenium click on <input>.

        Blocks bubbling clicks on the nested file input so the native OS picker does not open.
        """
        script = """
        var icon = arguments[0];
        function isVisible(el) {
            if (!el) return false;
            var st = window.getComputedStyle(el);
            return st.display !== 'none' && st.visibility !== 'hidden' && el.offsetParent !== null;
        }
        function blockInputPicker(inp) {
            if (!inp) return;
            var block = function(e) {
                e.preventDefault();
                e.stopImmediatePropagation();
                return false;
            };
            inp.addEventListener('click', block, true);
            inp.addEventListener('mousedown', block, true);
        }
        var roots = [];
        var footer = document.querySelector('footer');
        if (footer) roots.push(footer);
        roots.push(document.body);
        for (var r = 0; r < roots.length; r++) {
            var spans = roots[r].querySelectorAll('span[data-icon="' + icon + '"]');
            for (var i = 0; i < spans.length; i++) {
                var span = spans[i];
                if (!isVisible(span)) continue;
                var row = span.closest('li')
                    || span.closest('[role="button"]')
                    || span.closest('div[tabindex]')
                    || span.parentElement;
                if (!row || !isVisible(row)) continue;
                blockInputPicker(row.querySelector('input[type="file"]'));
                ['mousedown', 'mouseup', 'click'].forEach(function(type) {
                    row.dispatchEvent(new MouseEvent(type, {
                        bubbles: true,
                        cancelable: true,
                        view: window
                    }));
                });
                return true;
            }
        }
        return false;
        """
        try:
            return bool(self.driver.execute_script(script, data_icon))
        except Exception:
            return False

    def _expose_attach_file_input(self, input_kind, existing_signatures, stop_event=None):
        """After attach (+) is open: find or activate the correct hidden file input."""
        data_icon = "attach-document" if input_kind == "document" else "attach-image"

        input_el = self._wait_for_file_input_in_attach_menu(
            input_kind, timeout=1.2, stop_event=stop_event
        )
        if input_el:
            return input_el

        if self._js_activate_attach_menu_option(data_icon):
            if stop_event:
                stop_event.wait(0.5)
            else:
                time.sleep(0.5)

        input_el = self._wait_for_file_input_in_attach_menu(
            input_kind, timeout=2.5, stop_event=stop_event
        )
        if input_el:
            return input_el

        input_el = self._wait_for_new_file_input(
            input_kind,
            existing_signatures,
            timeout=5,
            stop_event=stop_event,
        )
        if input_el:
            return input_el

        return self._find_file_input(input_kind)

    def _wait_for_new_file_input(self, kind, existing_signatures, timeout=8, stop_event=None):
        end_time = time.time() + timeout
        while time.time() < end_time:
            if stop_event and stop_event.is_set():
                return None
            found = self._find_file_input(kind, exclude_signatures=existing_signatures)
            if found:
                return found
            if stop_event:
                stop_event.wait(0.25)
            else:
                time.sleep(0.25)
        return self._find_file_input(kind)

    def _media_preview_visible(self):
        return self._find_any(self.MEDIA_PREVIEW_LOCATORS) is not None

    def _sticker_panel_visible(self):
        return self._find_best_clickable(self.STICKER_PANEL_LOCATORS) is not None

    def _dismiss_sticker_panel(self):
        try:
            self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
            time.sleep(0.4)
        except Exception:
            pass

    def _reset_compose_overlays(self):
        """Close sticker panel, media preview, and attach menu before a new upload."""
        for _ in range(2):
            if (
                not self._sticker_panel_visible()
                and not self._media_preview_visible()
            ):
                break
            try:
                self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
            except Exception:
                pass
            time.sleep(0.35)

    def _find_photo_video_input(self):
        return self._find_file_input("media")

    def _send_keys_to_file_input(self, input_el, path):
        """Inject a local file path via send_keys only — never click the input (avoids OS file dialog)."""
        if not input_el:
            return False
        abs_path = os.path.abspath(path)
        if not os.path.isfile(abs_path):
            return False
        try:
            self.driver.execute_script(
                """
                var el = arguments[0];
                el.removeAttribute('hidden');
                el.style.display = 'block';
                el.style.visibility = 'visible';
                el.style.opacity = '0';
                el.style.position = 'fixed';
                el.style.left = '0';
                el.style.top = '0';
                el.style.width = '1px';
                el.style.height = '1px';
                el.style.pointerEvents = 'none';
                """,
                input_el,
            )
        except Exception:
            pass
        try:
            input_el.send_keys(abs_path)
            return True
        except Exception:
            return False

    def _dismiss_attach_menu(self):
        try:
            self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
            time.sleep(0.3)
        except Exception:
            pass

    def _try_direct_file_injection(self, path, input_kind, stop_event=None):
        """Documents only — media must use attach menu to avoid sticker file inputs."""
        if input_kind == "media":
            return False
        if stop_event and stop_event.is_set():
            return "STOPPED"

        if self._sticker_panel_visible():
            self._dismiss_sticker_panel()

        input_el = self._find_file_input(input_kind)
        if not input_el or self._classify_file_input(input_el) != input_kind:
            return False

        if not self._send_keys_to_file_input(input_el, path):
            return False

        if stop_event:
            stop_event.wait(0.6)
        else:
            time.sleep(0.6)

        if self._sticker_panel_visible():
            self._dismiss_sticker_panel()
            return False

        if input_kind == "media":
            preview = self._find_any(self.MEDIA_PREVIEW_LOCATORS)
            if not preview:
                preview = self._wait_for_any(
                    self.MEDIA_PREVIEW_LOCATORS, timeout=3, stop_event=stop_event
                )
            if stop_event and stop_event.is_set():
                return "STOPPED"
            if not preview:
                return False

        return True

    def _send_attachment_via_attach_menu(self, path, input_kind, stop_event=None):
        """Single-path attach: reset overlays -> (+) -> JS menu row -> send_keys only."""
        if stop_event and stop_event.is_set():
            return "STOPPED"

        self._reset_compose_overlays()

        try:
            existing_signatures = self._snapshot_file_input_signatures()

            attach_btn = self._find_best_clickable(self.ATTACH_BUTTON_LOCATORS)
            if not attach_btn:
                return "ERR_ATTACH_BTN_NOT_FOUND"

            self._click_element(attach_btn)
            if stop_event:
                stop_event.wait(0.8)
            else:
                time.sleep(0.8)

            input_el = self._expose_attach_file_input(
                input_kind,
                existing_signatures,
                stop_event=stop_event,
            )

            if not input_el or self._classify_file_input(input_el) != input_kind:
                self._dismiss_attach_menu()
                return "ERR_FILE_INPUT_NOT_FOUND"

            if self._sticker_panel_visible():
                self._dismiss_attach_menu()
                self._reset_compose_overlays()
                return "ERR_STICKER_PANEL_OPENED"

            if not self._send_keys_to_file_input(input_el, path):
                self._dismiss_attach_menu()
                return "ERR_FILE_INPUT_NOT_FOUND"

            if stop_event:
                stop_event.wait(0.6)
            else:
                time.sleep(0.6)

            if input_kind == "media" and self._sticker_panel_visible():
                self._dismiss_attach_menu()
                self._reset_compose_overlays()
                return "ERR_STICKER_PANEL_OPENED"

            if input_kind == "media":
                preview = self._find_any(self.MEDIA_PREVIEW_LOCATORS)
                if not preview:
                    preview = self._wait_for_any(
                        self.MEDIA_PREVIEW_LOCATORS, timeout=8, stop_event=stop_event
                    )
                if not preview:
                    self._dismiss_attach_menu()
                    return "ERR_FILE_INPUT_NOT_FOUND"

            return "SUCCESS"
        except Exception as e:
            self._dismiss_attach_menu()
            return f"ERR_ATTACH: {str(e)[:250]}"

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

    def _wait_for_chat_ready_after_attachments(self, stop_event=None):
        """Wait for media preview to close and footer chat input before a follow-up text."""
        if stop_event and stop_event.is_set():
            return "STOPPED"
        self._wait_for_preview_close(timeout=12, stop_event=stop_event)
        if stop_event and stop_event.is_set():
            return "STOPPED"
        chat_input = self._wait_for_any(
            self.CHAT_INPUT_LOCATORS, timeout=20, stop_event=stop_event
        )
        if not chat_input:
            return "ERR_CHAT_INPUT_NOT_FOUND"
        if stop_event:
            stop_event.wait(0.5)
        else:
            time.sleep(0.5)
        return "SUCCESS"

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

    def _open_chat_via_search(self, phone, stop_event=None):
        """Open a chat from the side search box without reloading the page."""
        if stop_event and stop_event.is_set():
            return False
        try:
            search_box = (
                self._find_best_clickable(self.SEARCH_BOX_LOCATORS)
                or self._find_any(self.SEARCH_BOX_LOCATORS)
            )
            if not search_box:
                return False
            self._click_element(search_box)
            if stop_event:
                stop_event.wait(0.3)
            else:
                time.sleep(0.3)
            try:
                search_box.send_keys(Keys.CONTROL, "a")
                search_box.send_keys(Keys.BACKSPACE)
            except Exception:
                pass
            query = phone.lstrip("+")
            search_box.send_keys(query)
            if stop_event:
                stop_event.wait(1.2)
            else:
                time.sleep(1.2)
            search_box.send_keys(Keys.ENTER)
            if stop_event:
                stop_event.wait(0.8)
            else:
                time.sleep(0.8)
            return self._find_any(self.CHAT_INPUT_LOCATORS) is not None
        except Exception:
            return False

    def open_chat(self, phone, stop_event=None):
        """Open chat: search when switching numbers in-session, else navigate by URL."""
        if stop_event and stop_event.is_set():
            return "STOPPED"
        if not self.driver:
            return "ERR_NOT_READY"

        phone = str(phone or "").strip()
        if not phone:
            return "TIMEOUT"

        can_search = (
            self._last_opened_phone
            and self.is_logged_in()
            and phone != self._last_opened_phone
        )
        if can_search and self._open_chat_via_search(phone, stop_event=stop_event):
            self._last_opened_phone = phone
            return self._wait_for_chat_or_invalid(timeout=45, stop_event=stop_event)

        url = f"https://web.whatsapp.com/send?phone={phone}"
        self.driver.get(url)
        self._last_opened_phone = phone
        return self._wait_for_chat_or_invalid(timeout=90, stop_event=stop_event)

    def send_message(
        self,
        phone,
        name,
        message_template,
        attachments=None,
        extra_messages=None,
        stop_event=None,
        send_text_with_image=False,
        skip_open_chat=False,
    ):
        """Sends a message and optionally multiple attachments (image, video, document)."""
        if stop_event and stop_event.is_set():
            return "STOPPED"
        if not self.driver:
            return "ERR_NOT_READY"

        message_template = message_template or ""
        message = message_template.replace("{name}", name).strip()

        if not attachments:
            attachments = []

        if not attachments and not message:
            return "ERR_EMPTY_MESSAGE"

        try:
            if skip_open_chat:
                if self._find_any(self.INVALID_NUMBER_LOCATORS):
                    ready_state = "INVALID"
                elif self._find_any(self.CHAT_INPUT_LOCATORS):
                    ready_state = "READY"
                else:
                    ready_state = "TIMEOUT"
            else:
                ready_state = self.open_chat(phone, stop_event=stop_event)

            if ready_state == "STOPPED":
                return "STOPPED"
            if ready_state == "INVALID":
                return "INVALID"
            if ready_state == "TIMEOUT":
                return "ERR_TIMEOUT"

            has_media = bool(attachments)
            if has_media:
                jitter = random.uniform(2.0, 4.5)
            else:
                jitter = random.choices(
                    [random.uniform(1.0, 2.0), random.uniform(2.0, 3.5), random.uniform(3.5, 5.0)],
                    weights=[60, 30, 10],
                    k=1,
                )[0]
            if stop_event:
                stop_event.wait(jitter)
            else:
                time.sleep(jitter)
            if stop_event and stop_event.is_set():
                return "STOPPED"

            return self._send_message_content(
                name,
                message,
                attachments,
                extra_messages,
                stop_event,
                send_text_with_image,
            )
        except Exception as e:
            return f"ERR_GENERAL: {str(e)[:250]}"

    def _send_message_content(
        self,
        name,
        message,
        attachments,
        extra_messages,
        stop_event,
        send_text_with_image,
    ):
        """Send attachments and/or text in an already-open chat."""
        if attachments:
            use_caption_mode = bool(send_text_with_image and message)

            for i, att in enumerate(attachments):
                if stop_event and stop_event.is_set():
                    return "STOPPED"

                path = att.get("path")
                type_ = att.get("type", "image")

                raw_caption = att.get("caption")
                caption = None
                if raw_caption:
                    caption = str(raw_caption).replace("{name}", name).strip()
                elif use_caption_mode and i == 0:
                    caption = message

                res = self._send_attachment(path, type_, caption, stop_event=stop_event)
                if res != "SUCCESS":
                    return res

                if (
                    use_caption_mode
                    and i == 0
                    and caption
                    and self._footer_chat_input_text()
                ):
                    text_res = self._send_caption_fallback_text(
                        caption, stop_event=stop_event
                    )
                    if text_res != "SUCCESS":
                        return text_res

                extra = 0.0
                try:
                    from utils.safety import extra_delay_after_attachment

                    extra = extra_delay_after_attachment(type_, path)
                except Exception:
                    extra = 5.0 if type_ in ("image", "video") else 2.0
                if stop_event:
                    stop_event.wait(2 + extra)
                else:
                    time.sleep(2 + extra)

            if message and not send_text_with_image:
                ready = self._wait_for_chat_ready_after_attachments(stop_event=stop_event)
                if ready == "STOPPED":
                    return "STOPPED"
                if ready != "SUCCESS":
                    return ready
                text_res = self._send_text(message, stop_event=stop_event)
                if text_res != "SUCCESS":
                    return text_res

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
            return f"ERR_GENERAL: {str(e)[:250]}"

    def _get_contenteditable_text(self, element):
        if not element:
            return ""
        try:
            text = (element.text or "").strip()
            if text:
                return text
            text = (element.get_attribute("innerText") or "").strip()
            if text:
                return text
            return (self.driver.execute_script(
                "return (arguments[0].innerText || arguments[0].textContent || '').trim();",
                element,
            ) or "").strip()
        except Exception:
            return ""

    def _find_footer_chat_input(self):
        return self._find_best_clickable(self.CHAT_INPUT_LOCATORS) or self._find_any(
            self.CHAT_INPUT_LOCATORS
        )

    def _footer_chat_input_text(self):
        chat_input = self._find_footer_chat_input()
        if not chat_input:
            return ""
        return self._get_contenteditable_text(chat_input)

    def _caption_text_matches(self, caption_box, expected):
        if not expected:
            return True
        actual = self._get_contenteditable_text(caption_box)
        if not actual:
            return False
        if actual == expected:
            return True
        # Long captions may truncate in DOM reads; prefix match is enough.
        shorter, longer = (actual, expected) if len(actual) <= len(expected) else (expected, actual)
        return longer.startswith(shorter) and len(shorter) >= min(40, len(longer) // 2)

    def _wait_for_media_caption_box(self, timeout=12, stop_event=None):
        if not self._wait_for_any(
            self.MEDIA_PREVIEW_LOCATORS, timeout=timeout, stop_event=stop_event
        ):
            return None
        return self._wait_for_any(
            self.CAPTION_BOX_LOCATORS, timeout=timeout, stop_event=stop_event
        )

    def _find_preview_send_button(self, stop_event=None):
        send_btn = self._find_best_clickable(self.MEDIA_PREVIEW_SEND_BUTTON_LOCATORS)
        if send_btn:
            return send_btn
        return self._wait_for_any(
            self.MEDIA_PREVIEW_SEND_BUTTON_LOCATORS, timeout=10, stop_event=stop_event
        )

    def _send_caption_fallback_text(self, caption, stop_event=None):
        if stop_event and stop_event.is_set():
            return "STOPPED"
        leftover = self._footer_chat_input_text()
        text_to_send = leftover if leftover else caption
        if not text_to_send:
            return "SUCCESS"
        return self._send_text(text_to_send, stop_event=stop_event)

    def _click_element(self, element):
        """Clicks an element using a highly resilient sequence of strategies:
        1. Native click (best for React/Vue synthetic events)
        2. ActionChains click (simulates real mouse movement and click)
        3. JavaScript click (fallback for obscured/intercepted elements)
        """
        if not element:
            return False
        try:
            element.click()
            return True
        except Exception:
            pass
        try:
            from selenium.webdriver.common.action_chains import ActionChains
            ActionChains(self.driver).move_to_element(element).click().perform()
            return True
        except Exception:
            pass
        try:
            self.driver.execute_script("arguments[0].click();", element)
            return True
        except Exception:
            pass
        return False

    def _send_attachment(self, path, media_type, caption=None, stop_event=None):
        """Upload file via attach menu; send preview/doc; never touch footer chat during media step."""
        if stop_event and stop_event.is_set():
            return "STOPPED"

        if not path:
            return "ERR_FILE_INPUT_NOT_FOUND"
        path = os.path.abspath(path)
        if not os.path.isfile(path):
            return "ERR_FILE_INPUT_NOT_FOUND"

        media_type = (media_type or "image").lower().strip()
        if media_type not in ("document", "image", "video"):
            media_type = "image"
        input_kind = "document" if media_type == "document" else "media"

        if input_kind == "media":
            upload_result = self._send_attachment_via_attach_menu(
                path, input_kind, stop_event=stop_event
            )
        else:
            upload_result = self._try_direct_file_injection(
                path, input_kind, stop_event=stop_event
            )
            if upload_result is False:
                upload_result = self._send_attachment_via_attach_menu(
                    path, input_kind, stop_event=stop_event
                )
            elif upload_result is True:
                upload_result = "SUCCESS"

        if upload_result == "STOPPED":
            return "STOPPED"
        if upload_result != "SUCCESS":
            return upload_result

        try:
            if media_type == "document":
                send_btn = (
                    self._find_best_clickable(self.SEND_BUTTON_LOCATORS)
                    or self._wait_for_any(
                        self.SEND_BUTTON_LOCATORS, timeout=15, stop_event=stop_event
                    )
                )
                if not send_btn:
                    return "ERR_DOC_SEND_BTN_NOT_FOUND"
            else:
                if not self._wait_for_any(
                    self.MEDIA_PREVIEW_LOCATORS, timeout=40, stop_event=stop_event
                ):
                    return "ERR_FILE_INPUT_NOT_FOUND"
                if stop_event and stop_event.is_set():
                    return "STOPPED"

                caption_applied = True
                if caption:
                    caption_box = self._wait_for_media_caption_box(
                        timeout=12, stop_event=stop_event
                    )
                    if not caption_box:
                        caption_applied = False
                    else:
                        if stop_event:
                            stop_event.wait(0.5)
                        else:
                            time.sleep(0.5)
                        if stop_event and stop_event.is_set():
                            return "STOPPED"
                        self._enter_text(caption_box, caption, stop_event=stop_event)
                        if stop_event:
                            stop_event.wait(0.8)
                        else:
                            time.sleep(0.8)
                        caption_applied = self._caption_text_matches(caption_box, caption)

                send_btn = self._find_preview_send_button(stop_event=stop_event)
                if not send_btn:
                    return "ERR_SEND_BTN_NOT_FOUND"

            if stop_event and stop_event.is_set():
                return "STOPPED"

            self.driver.execute_script("arguments[0].click();", send_btn)

            file_size = os.path.getsize(path) if os.path.exists(path) else 0
            wait_time = max(3, min(30, file_size // (1024 * 1024)))
            if stop_event:
                stop_event.wait(wait_time)
            else:
                time.sleep(wait_time)

            if media_type != "document":
                self._wait_for_preview_close(timeout=12, stop_event=stop_event)
                if caption and (not caption_applied or self._footer_chat_input_text()):
                    fallback = self._send_caption_fallback_text(
                        caption, stop_event=stop_event
                    )
                    if fallback != "SUCCESS":
                        return fallback

            return "SUCCESS"
        except Exception as e:
            return f"ERR_ATTACH: {str(e)[:250]}"

    def _set_clipboard_text(self, text):
        """Sets Unicode text to the Windows clipboard using ctypes."""
        import ctypes
        from ctypes import wintypes
        
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32
        
        OpenClipboard = user32.OpenClipboard
        OpenClipboard.argtypes = [wintypes.HWND]
        OpenClipboard.restype = wintypes.BOOL
        
        EmptyClipboard = user32.EmptyClipboard
        EmptyClipboard.argtypes = []
        EmptyClipboard.restype = wintypes.BOOL
        
        SetClipboardData = user32.SetClipboardData
        SetClipboardData.argtypes = [wintypes.UINT, wintypes.HANDLE]
        SetClipboardData.restype = wintypes.HANDLE
        
        CloseClipboard = user32.CloseClipboard
        CloseClipboard.argtypes = []
        CloseClipboard.restype = wintypes.BOOL
        
        GlobalAlloc = kernel32.GlobalAlloc
        GlobalAlloc.argtypes = [wintypes.UINT, ctypes.c_size_t]
        GlobalAlloc.restype = wintypes.HGLOBAL
        
        GlobalLock = kernel32.GlobalLock
        GlobalLock.argtypes = [wintypes.HGLOBAL]
        GlobalLock.restype = ctypes.c_void_p
        
        GlobalUnlock = kernel32.GlobalUnlock
        GlobalUnlock.argtypes = [wintypes.HGLOBAL]
        GlobalUnlock.restype = wintypes.BOOL
        
        GMEM_MOVEABLE = 0x0002
        CF_UNICODETEXT = 13
        
        if not OpenClipboard(None):
            return False
        try:
            EmptyClipboard()
            data = text.encode('utf-16-le') + b'\x00\x00'
            h_mem = GlobalAlloc(GMEM_MOVEABLE, len(data))
            if not h_mem:
                return False
            p_mem = GlobalLock(h_mem)
            if not p_mem:
                return False
            ctypes.memmove(p_mem, data, len(data))
            GlobalUnlock(h_mem)
            SetClipboardData(CF_UNICODETEXT, h_mem)
        except Exception:
            return False
        finally:
            CloseClipboard()
        return True

    def _enter_text(self, element, text, stop_event=None):
        """Types or pastes text to ensure non-BMP characters like emojis send successfully."""
        if not text:
            return
            
        try:
            element.click()
        except:
            try:
                self.driver.execute_script("arguments[0].click();", element)
            except:
                pass
                
        if stop_event:
            stop_event.wait(0.2)
        else:
            time.sleep(0.2)
            
        has_non_bmp = any(ord(char) > 0xffff for char in text)
        if has_non_bmp or len(text) >= 200:
            if self._set_clipboard_text(text):
                try:
                    element.send_keys(Keys.CONTROL, 'v')
                    if stop_event:
                        stop_event.wait(0.5)
                    else:
                        time.sleep(0.5)
                    return
                except Exception:
                    pass
                    
        # Fallback to direct send_keys or human type
        if len(text) < 200:
            self._human_type(element, text, stop_event=stop_event)
        else:
            element.send_keys(text)

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
        if self._media_preview_visible():
            self._wait_for_preview_close(timeout=12, stop_event=stop_event)
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
            self._enter_text(chat_input, message, stop_event=stop_event)
                
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
            if random.random() < 0.25:
                self._random_scroll(stop_event=stop_event)
            return "SUCCESS"
        except Exception as e:
            return f"ERR_TEXT_SEND: {str(e)[:250]}"

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
                (By.XPATH, '//span[contains(@aria-label, "رسالة غير مقروءة")]'),
                (By.XPATH, '//span[contains(@aria-label, "رسالة غير مقروءة")]/ancestor::div[@role="listitem"]'),
                (By.XPATH, '//span[contains(@aria-label, "unread message")]/ancestor::div[@role="listitem"]'),
                (By.XPATH, '//div[contains(@aria-label, "unread message")]'),
                (By.XPATH, '//div[contains(@aria-label, "رسالة غير مقروءة")]'),
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

    def open_chat_element(self, chat_element):
        """Clicks a chat row in the side list to open that conversation."""
        try:
            self.driver.execute_script("arguments[0].click();", chat_element)
            time.sleep(1)
            return True
        except Exception:
            return False

    def get_active_chat_name(self):
        """Best-effort read of the open conversation title from the chat header."""
        header_locators = [
            (By.XPATH, '//header//span[@data-testid="conversation-info-header-chat-title"]'),
            (By.XPATH, '//header//div[@role="button"]//span[@dir="auto"]'),
            (By.XPATH, '//header//span[contains(@class,"selectable-text")]'),
        ]
        for by, value in header_locators:
            try:
                for el in self.driver.find_elements(by, value):
                    text = (el.text or "").strip()
                    if text and len(text) < 120:
                        return text
            except Exception:
                continue
        return ""

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
