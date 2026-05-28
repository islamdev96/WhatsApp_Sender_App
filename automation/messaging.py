"""WhatsApp Sender Pro — Text and message sending, clipboard, typing."""
import time
import os
import re
import json
import random
import subprocess
import platform

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, NoSuchElementException, StaleElementReferenceException,
    WebDriverException, ElementClickInterceptedException,
    ElementNotInteractableException, JavascriptException,
)

from utils.logger import logger
from automation.whatsapp_navigator import WhatsAppNavigator


class MessagingMixin:
    """Mixin: Text and message sending, clipboard, typing."""

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
                if self._handle_invalid_if_present(stop_event=stop_event):
                    ready_state = "INVALID"
                elif self._is_active_chat_ready():
                    ready_state = "READY"
                else:
                    ready_state = "TIMEOUT"
            else:
                ready_state = self.open_chat(phone, stop_event=stop_event)

            if ready_state == "STOPPED":
                return "STOPPED"
            if ready_state == "INVALID":
                self._emit("WARN", "تخطي — لا واتساب", phone)
                return "INVALID"
            if ready_state == "TIMEOUT":
                if self._handle_invalid_if_present(stop_event=stop_event):
                    return "INVALID"
                self._emit("ERROR", "انتهت مهلة فتح المحادثة", phone)
                return "ERR_TIMEOUT"

            if attachments and ready_state == "READY":
                if not self._wait_for_footer_compose_ready(
                    timeout=20, stop_event=stop_event, require_attach=True
                ):
                    if not self._ensure_chat_open_for_send(phone, stop_event=stop_event):
                        if self._handle_invalid_if_present(stop_event=stop_event):
                            return "INVALID"
                        self._emit("ERROR", "زر الإرفاق (+) غير جاهز بعد فتح المحادثة")
                        return "ERR_ATTACH_BTN_NOT_FOUND"
                    if not self._wait_for_footer_compose_ready(
                        timeout=20, stop_event=stop_event, require_attach=True
                    ):
                        self._emit("ERROR", "زر الإرفاق (+) غير جاهز بعد فتح المحادثة")
                        return "ERR_ATTACH_BTN_NOT_FOUND"

            # TEST MODE: minimal jitter
            jitter = random.uniform(0.3, 0.8)
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
                phone=phone,
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
        phone=None,
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

                if not self._is_active_chat_ready():
                    self._ensure_chat_open_for_send(phone, stop_event=stop_event)

                res = self._send_attachment(
                    path, type_, caption, stop_event=stop_event, phone=phone
                )
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
                except Exception as exc:
                    logger.debug("Could not calculate attachment safety delay: %s", exc)
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

    def _send_text(self, message, stop_event=None):
        if stop_event and stop_event.is_set():
            return "STOPPED"

        for attempt in range(2):
            if stop_event and stop_event.is_set():
                return "STOPPED"
            result = self._send_text_once(message, stop_event=stop_event)
            if result == "SUCCESS":
                return "SUCCESS"
            if result == "INVALID":
                return "INVALID"
            if result != "ERR_TEXT_SEND_RETRY":
                return result
            self.recover_compose_state(stop_event=stop_event)

        return f"ERR_TEXT_SEND: click intercepted after retry"

    def _send_text_once(self, message, stop_event=None):
        if self._handle_invalid_if_present(stop_event=stop_event):
            return "INVALID"
        self._reset_compose_overlays()
        if self._media_preview_visible():
            self._wait_for_preview_close(timeout=12, stop_event=stop_event)
            if stop_event and stop_event.is_set():
                return "STOPPED"
        try:
            if not self._wait_for_footer_compose_ready(timeout=25, stop_event=stop_event):
                self._emit("ERROR", "صندوق الكتابة غير جاهز")
                return "ERR_CHAT_INPUT_NOT_FOUND"

            self._emit("STEP", "إرسال النص", f"{len(message)} حرف")

            chat_input = self._find_footer_chat_input() or self._find_any(
                self.CHAT_INPUT_LOCATORS
            )
            if not chat_input:
                return "ERR_CHAT_INPUT_NOT_FOUND"

            if stop_event and stop_event.is_set():
                return "STOPPED"

            self._focus_footer_chat_input(chat_input)
            if not self._click_element(chat_input):
                try:
                    self.driver.execute_script("arguments[0].click();", chat_input)
                except Exception as e:
                    if "intercepted" in str(e).lower():
                        return "ERR_TEXT_SEND_RETRY"
                    raise

            if stop_event:
                stop_event.wait(0.4)
            else:
                time.sleep(0.4)

            if stop_event and stop_event.is_set():
                return "STOPPED"

            self._enter_text(chat_input, message, stop_event=stop_event)

            if stop_event:
                stop_event.wait(0.4)
            else:
                time.sleep(0.4)

            if stop_event and stop_event.is_set():
                return "STOPPED"

            sent = False
            try:
                chat_input.send_keys(Keys.ENTER)
                sent = True
            except ElementClickInterceptedException:
                return "ERR_TEXT_SEND_RETRY"
            except Exception as exc:
                logger.debug("Enter key send failed, trying send button fallback: %s", exc)

            if not sent:
                send_btn = self._find_footer_send_button(stop_event=stop_event)
                if send_btn:
                    if not self._click_element(send_btn):
                        try:
                            self.driver.execute_script(
                                "arguments[0].click();", send_btn
                            )
                        except Exception as e:
                            if "intercepted" in str(e).lower():
                                return "ERR_TEXT_SEND_RETRY"
                            raise
                else:
                    try:
                        chat_input.send_keys(Keys.ENTER)
                    except ElementClickInterceptedException:
                        return "ERR_TEXT_SEND_RETRY"

            if stop_event:
                stop_event.wait(1.0)
            else:
                time.sleep(1.0)
            if random.random() < 0.25:
                self._random_scroll(stop_event=stop_event)
            self._emit("INFO", "تم إرسال النص")
            return "SUCCESS"
        except ElementClickInterceptedException:
            self._emit("WARN", "النقر محجوب — إعادة محاولة")
            return "ERR_TEXT_SEND_RETRY"
        except Exception as e:
            err = str(e)
            if "intercepted" in err.lower():
                self._emit("WARN", "النقر محجوب — إعادة محاولة")
                return "ERR_TEXT_SEND_RETRY"
            self._emit("ERROR", "فشل إرسال النص", err[:200])
            return f"ERR_TEXT_SEND: {err[:250]}"

    def _enter_text(self, element, text, stop_event=None):
        """Types or pastes text to ensure non-BMP characters like emojis send successfully."""
        if not text:
            return
            
        try:
            element.click()
        except Exception as exc:
            logger.debug("Could not focus text element with native click: %s", exc)
            try:
                self.driver.execute_script("arguments[0].click();", element)
            except Exception as js_exc:
                logger.debug("Could not focus text element with JavaScript click: %s", js_exc)
                
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
                except Exception as exc:
                    logger.debug("Could not paste text from clipboard: %s", exc)
                    
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
        except Exception as exc:
            logger.debug("Could not set clipboard text: %s", exc)
            return False
        finally:
            CloseClipboard()
        return True

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
        except Exception as exc:
            logger.debug("Could not read contenteditable text: %s", exc)
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
        except Exception as exc:
            logger.debug("Native element click failed: %s", exc)
        try:
            from selenium.webdriver.common.action_chains import ActionChains
            ActionChains(self.driver).move_to_element(element).click().perform()
            return True
        except Exception as exc:
            logger.debug("ActionChains element click failed: %s", exc)
        try:
            self.driver.execute_script("arguments[0].click();", element)
            return True
        except Exception as exc:
            logger.debug("JavaScript element click failed: %s", exc)
        return False

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
        except Exception as exc:
            logger.debug("Random chat scroll failed: %s", exc)

    def _dismiss_modal_if_present(self, stop_event=None):
        """Dismiss common dialog/modals that can block the media preview (e.g. discard/ignore prompts)."""
        if stop_event and stop_event.is_set():
            return False
        if not self.driver:
            return False
        try:
            dialogs = self.driver.find_elements(By.XPATH, "//div[@role='dialog'] | //div[contains(@class,'modal')]")
            for d in dialogs:
                try:
                    if not d.is_displayed():
                        continue
                    # Prefer buttons with text 'إلغاء' / 'Cancel' / 'لا' to dismiss the dialog without discarding
                    cand_buttons = d.find_elements(By.XPATH, ".//button | .//*[@role='button']")
                    for b in cand_buttons:
                        try:
                            txt = (b.text or "").strip()
                            aria = (b.get_attribute('aria-label') or "").strip()
                            if any(k in txt for k in ('إلغاء', 'Cancel', 'لا', 'تجاهل')) or any(k in aria for k in ('إلغاء', 'Cancel', 'لا', 'تجاهل')):
                                self._emit("INFO", f"[MODAL] Dismissing dialog via button text='{txt}' aria='{aria}'")
                                self._click_element(b)
                                return True
                        except Exception as exc:
                            logger.debug("Could not inspect modal button: %s", exc)
                            continue
                    # Fallback: click any visible close control inside the dialog
                    try:
                        close = d.find_element(By.XPATH, ".//span[@data-icon='x'] | .//button[contains(@aria-label,'Close')] | .//button[contains(., '×')]")
                        if close.is_displayed():
                            self._click_element(close)
                            return True
                    except Exception as exc:
                        logger.debug("Could not click modal close control: %s", exc)
                except Exception as exc:
                    logger.debug("Could not inspect modal dialog: %s", exc)
                    continue
        except Exception as exc:
            logger.debug("Could not enumerate modal dialogs: %s", exc)
            return False
        return False

    def _send_caption_fallback_text(self, caption, stop_event=None):
        if stop_event and stop_event.is_set():
            return "STOPPED"
        leftover = self._footer_chat_input_text()
        text_to_send = leftover if leftover else caption
        if not text_to_send:
            return "SUCCESS"
        return self._send_text(text_to_send, stop_event=stop_event)

