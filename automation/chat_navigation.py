"""WhatsApp Sender Pro — Chat opening, search, number validation."""
import time

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, NoSuchElementException, StaleElementReferenceException,
    WebDriverException, ElementClickInterceptedException,
    ElementNotInteractableException, JavascriptException,
)

from utils.logger import logger


class ChatNavigationMixin:
    """Mixin: Chat opening, search, number validation."""

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
            except Exception as exc:
                logger.debug("Could not clear search box before typing phone: %s", exc)
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
            try:
                self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
            except Exception as exc:
                logger.debug("Could not close search overlay with Escape: %s", exc)
            if stop_event:
                stop_event.wait(0.4)
            else:
                time.sleep(0.4)
            if stop_event:
                stop_event.wait(0.5)
            else:
                time.sleep(0.5)
            return self._is_active_chat_ready()
        except Exception as exc:
            logger.debug("Opening chat via search failed for %s: %s", phone, exc)
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

        force_url = getattr(self, "_force_url_next", False)
        if force_url:
            self._force_url_next = False

        can_search = False
        if can_search and self._open_chat_via_search(phone, stop_event=stop_event):
            self._last_opened_phone = phone
            self._emit("STEP", "فتح المحادثة عبر البحث", phone)
            state = self._wait_for_chat_or_invalid(timeout=45, stop_event=stop_event)
            self._emit("INFO", f"حالة المحادثة: {state}", phone)
            return state

        # Get reference to the current HTML element to detect when the page actually unloads
        old_html = None
        try:
            old_html = self.driver.find_element(By.TAG_NAME, "html")
        except Exception as exc:
            logger.debug("Could not capture current html element before navigation: %s", exc)

        # Force a full reload by appending a unique timestamp to avoid URL-navigation cache/routing locks in WhatsApp Web
        url = f"https://web.whatsapp.com/send?phone={phone}&t={int(time.time())}"
        self._emit("STEP", "فتح المحادثة عبر الرابط", phone)
        self.driver.get(url)
        
        # Force a complete refresh to discard all client-side cache, bfcache, and SPA router state
        try:
            self.driver.refresh()
        except Exception as exc:
            logger.debug("Could not refresh WhatsApp page after navigation: %s", exc)

        # Wait for the old HTML element to become stale (indicating that the browser has fully unloaded the old page)
        if old_html:
            try:
                from selenium.webdriver.support.ui import WebDriverWait
                from selenium.webdriver.support import expected_conditions as EC
                WebDriverWait(self.driver, 10).until(EC.staleness_of(old_html))
                self._emit("INFO", "تم تأكيد إلغاء تحميل الصفحة السابقة وتفريغ الذاكرة بنجاح.")
            except Exception as exc:
                logger.debug("Old page did not become stale in time: %s", exc)
                time.sleep(3.0)
        else:
            time.sleep(3.0)

        self._last_opened_phone = phone

        # Wait for the main app layout (search box) to become visible, indicating that the SPA has fully booted and stabilized
        self._emit("INFO", "انتظار اكتمال تحميل تطبيق واتساب واستقرار الواجهة...")
        start_wait = time.time()
        booted = False
        while time.time() - start_wait < 45:
            if stop_event and stop_event.is_set():
                return "STOPPED"
            try:
                search_box = self._find_any(self.SEARCH_BOX_LOCATORS)
                if search_box and search_box.is_displayed():
                    booted = True
                    break
            except Exception as exc:
                logger.debug("Could not inspect WhatsApp boot search box: %s", exc)
            time.sleep(0.5)
        
        if booted:
            self._emit("INFO", "اكتمل تحميل تطبيق واتساب واستقرار الواجهة بنجاح.")
        else:
            self._emit("WARN", "تنبيه: انتهت مهلة استقرار الواجهة، مواصلة الانتظار...")
        
        # Additional small buffer (1.5s) for React routing transition to take effect
        time.sleep(1.5)

        state = self._wait_for_chat_or_invalid(timeout=45, stop_event=stop_event)
        self._emit("INFO", f"حالة المحادثة: {state}", phone)
        return state

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
                self._dismiss_invalid_number_modal(stop_event=stop_event)
                return "INVALID"
            if ready_state == "READY":
                return "VALID"
            if ready_state == "STOPPED":
                return "STOPPED"
            return "ERR_TIMEOUT"
        except Exception as e:
            return f"ERR_GENERAL: {str(e)[:250]}"

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
            except Exception as exc:
                logger.debug("Number validity wait timed out or failed: %s", exc)

            time.sleep(1) # Give it a moment to render
            
            # If we find the invalid text anywhere in the page source, it's invalid
            if self._page_indicates_invalid_number():
                self._dismiss_invalid_number_modal()
                return False
                
            # Otherwise, assume valid (chat input is probably visible)
            return True
        except Exception as exc:
            logger.debug("Could not check number validity for %s: %s", phone, exc)
            return False

    def _page_indicates_invalid_number(self):
        if self._find_any(self.INVALID_NUMBER_LOCATORS):
            return True
        try:
            src = (self.driver.page_source or "").lower()
            return any(m.lower() in src for m in self._INVALID_PAGE_MARKERS)
        except Exception as exc:
            logger.debug("Could not inspect page source for invalid-number markers: %s", exc)
            return False

    def _invalid_number_modal_visible(self):
        return self._page_indicates_invalid_number()

    def _dismiss_invalid_number_modal(self, stop_event=None):
        """Click OK (موافق) on the 'number not on WhatsApp' dialog so automation can continue."""
        if not self.driver:
            return False
        if not self._page_indicates_invalid_number():
            return False

        dismissed = False
        ok_btn = self._find_best_clickable(self.INVALID_NUMBER_OK_LOCATORS)
        if ok_btn:
            dismissed = self._click_element(ok_btn)

        if not dismissed:
            try:
                dismissed = bool(
                    self.driver.execute_script(
                        """
                        var labels = ['موافق', 'OK', 'Ok', 'حسناً', 'حسنا'];
                        var nodes = document.querySelectorAll(
                            '[role="button"], button, div[tabindex="0"]'
                        );
                        for (var i = 0; i < nodes.length; i++) {
                            var el = nodes[i];
                            var t = (el.innerText || el.textContent || '').trim();
                            if (labels.indexOf(t) >= 0) {
                                el.click();
                                return true;
                            }
                        }
                        var modal = document.querySelector('[data-animate-modal-popup="true"]')
                            || document.querySelector('[role="dialog"]');
                        if (modal) {
                            var btn = modal.querySelector('[role="button"], button');
                            if (btn) { btn.click(); return true; }
                        }
                        return false;
                        """
                    )
                )
            except Exception as exc:
                logger.debug("Could not dismiss invalid-number modal with JavaScript: %s", exc)

        if not dismissed:
            try:
                self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
                dismissed = True
            except Exception as exc:
                logger.debug("Could not dismiss invalid-number modal with Escape: %s", exc)

        if stop_event:
            stop_event.wait(0.5)
        else:
            time.sleep(0.5)
        return dismissed

    def _handle_invalid_if_present(self, stop_event=None):
        """If invalid-number modal is open: dismiss it and report invalid."""
        if not self._page_indicates_invalid_number():
            return False
        self._emit("WARN", "رقم غير مسجل على واتساب — إغلاق النافذة والتخطي")
        self._dismiss_invalid_number_modal(stop_event=stop_event)
        self._last_opened_phone = None
        self._force_url_next = True
        return True

    def _ensure_chat_open_for_send(self, phone, stop_event=None):
        """Ensure compose footer and (+) are ready; reload URL only if needed."""
        if self._is_active_chat_ready():
            if self._wait_for_footer_compose_ready(
                timeout=5, stop_event=stop_event, require_attach=True
            ):
                return True
            self._reset_compose_overlays()
            self.bring_to_front()
            if self._wait_for_footer_compose_ready(
                timeout=5, stop_event=stop_event, require_attach=True
            ):
                return True
        if not phone or (stop_event and stop_event.is_set()):
            return False
        self._force_url_next = True
        state = self.open_chat(phone, stop_event=stop_event)
        if state == "INVALID":
            return False
        if state != "READY":
            return False
        return self._wait_for_footer_compose_ready(
            timeout=5, stop_event=stop_event, require_attach=True
        )

    def _wait_for_chat_or_invalid(self, timeout=60, poll=0.5, stop_event=None):
        return self.navigator.wait_for_chat_or_invalid(timeout, poll, stop_event)

