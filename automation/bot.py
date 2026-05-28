"""
WhatsApp Sender Pro — Main Bot Class.
Combines all mixin modules into a single WhatsAppBot interface.
"""
import time
import os
import json


from utils.logger import logger
from utils.event_log import print_event
from automation.whatsapp_navigator import WhatsAppNavigator
from automation.browser_setup import BrowserSetupMixin
from automation.chat_navigation import ChatNavigationMixin
from automation.messaging import MessagingMixin
from automation.media_handler import MediaHandlerMixin
from automation.chatbot import ChatbotMixin


class WhatsAppBot(
    BrowserSetupMixin,
    ChatNavigationMixin,
    MessagingMixin,
    MediaHandlerMixin,
    ChatbotMixin,
):
    def __init__(self, user_data_dir, proxy_config=None, on_event=None):
        self.user_data_dir = user_data_dir
        self.proxy_config = proxy_config
        self.on_event = on_event
        self.driver = None
        self.background_mode = False
        self._just_launched = False
        self._last_opened_phone = None
        self._force_url_next = False

        # Initialize modular WhatsApp DOM navigator
        self.navigator = WhatsAppNavigator(self)

        # Common locators delegated to self.navigator for single-point maintenance
        self.LOGGED_IN_LOCATORS = self.navigator.LOGGED_IN_LOCATORS
        self.SEARCH_BOX_LOCATORS = self.navigator.SEARCH_BOX_LOCATORS
        self.CHAT_INPUT_LOCATORS = self.navigator.CHAT_INPUT_LOCATORS
        self.ATTACH_BUTTON_LOCATORS = self.navigator.ATTACH_BUTTON_LOCATORS
        self._ATTACH_BUTTON_RELATIVE_XPATHS = self.navigator._ATTACH_BUTTON_RELATIVE_XPATHS

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
        self.FOOTER_SEND_BUTTON_LOCATORS = [
            (By.XPATH, '//*[@id="main"]//footer//span[@data-icon="send"]'),
            (By.XPATH, '//*[@id="main"]//footer//span[@data-icon="send-light"]'),
            (By.XPATH, '//*[@id="main"]//footer//span[contains(@data-icon,"send")]'),
            (By.XPATH, '//*[@id="main"]//footer//button[@data-testid="compose-btn-send"]'),
            (By.XPATH, '//*[@id="main"]//footer//button[@aria-label="Send"]'),
            (By.XPATH, '//*[@id="main"]//footer//button[@aria-label="إرسال"]'),
            (By.XPATH, '//*[@id="main"]//footer//div[@role="button" and @aria-label="Send"]'),
            (By.XPATH, '//*[@id="main"]//footer//div[@role="button" and @aria-label="إرسال"]'),
            (By.XPATH, '//*[@id="main"]//footer//div[@role="button" and contains(@aria-label,"Send")]'),
            (By.XPATH, '//*[@id="main"]//footer//div[@role="button" and contains(@aria-label,"إرسال")]'),
            (By.XPATH, '//*[@id="main"]//footer//button[contains(@aria-label,"Send")]'),
            (By.XPATH, '//*[@id="main"]//footer//button[contains(@aria-label,"إرسال")]'),
        ]
        self.SEND_BUTTON_LOCATORS = list(self.FOOTER_SEND_BUTTON_LOCATORS)
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
            (By.XPATH, '//div[@data-testid="sticker-panel"]'),
            (By.XPATH, '//*[@data-testid="sticker-maker"]'),
        ]
        self.MEDIA_PREVIEW_LOCATORS = [
            (By.XPATH, '//div[@data-testid="media-viewer"]'),
        ]
        self.INVALID_NUMBER_LOCATORS = [
            (By.XPATH, '//*[contains(text(),"phone number shared via url is invalid")]'),
            (By.XPATH, '//*[contains(text(),"Phone number shared via url is invalid")]'),
            (By.XPATH, '//*[contains(text(),"Invalid phone number")]'),
            (By.XPATH, '//*[contains(text(),"is not on WhatsApp")]'),
            (By.XPATH, '//*[contains(text(),"not on WhatsApp")]'),
            (By.XPATH, '//*[contains(text(),"غير موجود على واتساب")]'),
            (By.XPATH, '//*[contains(text(),"غير موجود على WhatsApp")]'),
            (By.XPATH, '//*[contains(text(),"غير صحيح")]'),
            (By.XPATH, '//*[contains(text(),"رقم الهاتف الذي تمت مشاركته")]'),
            (By.XPATH, '//*[contains(text(),"ليس لديه واتساب")]'),
            (By.XPATH, '//*[contains(text(),"ليس لديه WhatsApp")]'),
            (By.XPATH, '//*[contains(text(),"doesn\'t have WhatsApp")]'),
        ]
        self.INVALID_NUMBER_OK_LOCATORS = [
            (By.XPATH, '//div[@data-animate-modal-popup="true"]//div[@role="button"]'),
            (By.XPATH, '//div[@data-animate-modal-popup="true"]//button'),
            (By.XPATH, '//div[@role="dialog"]//div[@role="button"]'),
            (By.XPATH, '//div[@role="dialog"]//button'),
            (By.XPATH, '//div[@role="button"]//span[normalize-space()="موافق"]/ancestor::div[@role="button"]'),
            (By.XPATH, '//div[@role="button"]//span[normalize-space()="OK"]/ancestor::div[@role="button"]'),
            (By.XPATH, '//button[.//span[normalize-space()="موافق"]]'),
            (By.XPATH, '//button[.//span[normalize-space()="OK"]]'),
            (By.XPATH, '//*[@role="button" and @aria-label="OK"]'),
            (By.XPATH, '//*[@role="button" and @aria-label="موافق"]'),
        ]
        self._INVALID_PAGE_MARKERS = (
            "غير موجود على واتساب",
            "غير موجود على whatsapp",
            "not on whatsapp",
            "is not on whatsapp",
            "phone number shared via url is invalid",
            "رقم الهاتف الذي تمت مشاركته",
            "ليس لديه واتساب",
            "doesn't have whatsapp",
        )

        self._load_selectors_from_file()
        self._emit("INFO", "تم تهيئة بوت واتساب")

    def _emit(self, level, message, detail=None):
        """Diagnostic line → GUI callback (if set) else terminal stderr."""
        if self.on_event:
            try:
                self.on_event(level, message, detail)
            except TypeError as exc:
                logger.warning("on_event callback failed: %s", exc)
            except Exception as exc:
                log_exception("Unexpected error in on_event callback", exc)
            return
        try:
            from utils.event_log import print_event
            print_event(level, message, detail)
        except ImportError:
            logger.debug("event_log module not available, logging to logger")
            logger.log(
                {"INFO": 20, "WARNING": 30, "ERROR": 40, "DEBUG": 10}.get(level, 20),
                message
            )
        except Exception as exc:
            log_exception(f"Error in _emit: {level} - {message}", exc)

    def _load_selectors_from_file(self):
        """Load DOM selectors from the JSON config file."""
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
        except FileNotFoundError:
            logger.debug("Selectors file not found: %s, using default selectors", selectors_path)
        except json.JSONDecodeError as exc:
            logger.error("Selectors file %s is invalid JSON: %s", selectors_path, exc)
        except Exception as exc:
            log_exception(f"Error loading selectors from {selectors_path}", exc)

    def _find_any(self, locators):
        """Try multiple CSS/XPath locators and return the first visible match."""
        if not self.driver:
            return None
        for by, value in locators:
            try:
                elements = self.driver.find_elements(by, value)
            except Exception as exc:
                logger.debug("Failed to find elements with %s=%r: %s", by, value, exc)
                continue
            if elements:
                return elements[0]
        return None

    def _wait_for_any(self, locators, timeout=30, poll=0.5, stop_event=None):
        """Wait until at least one of the given locators is present in the DOM."""
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
            except Exception as exc:
                logger.debug("Failed to find elements with %s=%r: %s", by, value, exc)
                continue
            for el in elements:
                try:
                    if el.is_displayed() and el.get_attribute("aria-disabled") != "true":
                        return el
                except Exception as exc:
                    logger.debug("Error checking element visibility: %s", exc)
                    continue
        return None

    @staticmethod

    def close(self):
        """Safely close the browser, ensuring session data is saved."""
        if self.driver:
            try:
                # Give Chrome a moment to flush any pending writes
                time.sleep(0.5)
                self.driver.quit()
            except Exception as exc:
                logger.debug("Could not close browser cleanly: %s", exc)
            finally:
                self.driver = None
                try:
                    from utils.helpers import cleanup_proxy_extension
                    cleanup_proxy_extension(self.user_data_dir)
                except Exception as cleanup_exc:
                    logger.debug("Proxy extension cleanup skipped: %s", cleanup_exc)
    # â”€â”€â”€ Chatbot Methods â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

