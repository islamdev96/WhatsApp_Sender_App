"""WhatsApp Sender Pro — File inputs, attachment menus, media preview handling."""
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


class MediaHandlerMixin:
    """Mixin: File inputs, attachment menus, media preview handling."""

    def _file_input_signature(el):
        try:
            return (
                el.get_attribute("name") or "",
                el.get_attribute("id") or "",
                el.get_attribute("accept") or "",
            )
        except Exception as exc:
            logger.debug("Error getting file input signature: %s", exc)
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
        except Exception as exc:
            logger.debug("Error finding file inputs: %s", exc)
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
        except Exception as exc:
            logger.debug("Error classifying file input: %s", exc)
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
        except Exception as exc:
            logger.debug("Error finding file inputs: %s", exc)
            return None

        for el in inputs:
            sig = self._file_input_signature(el)
            if not sig or sig in exclude_signatures:
                continue
            if self._classify_file_input(el) == kind:
                return el
        return None

    def _find_file_input_in_attach_menu(self, kind):
        """Locate file input nested under the matching attach-menu row using labels or icons."""
        if kind == "document":
            labels = ["document", "مستند", "documents"]
            icons = ["attach-document"]
        else:
            labels = [
                "photos & videos",
                "photos and videos",
                "photos & videos",
                "الصور ومقاطع الفيديو",
                "الصور والفيديو",
                "صور وفيديو",
                "gallery",
                "معرض",
            ]
            icons = ["attach-image", "attach-gallery", "media", "gallery"]

        # 1. Try finding by text labels first (most robust)
        try:
            script = """
            var labels = arguments[0];
            function norm(s) {
                return (s || '').replace(/\\s+/g, ' ').trim().toLowerCase();
            }
            var want = labels.map(norm);
            var candidates = document.querySelectorAll('li, div[role="button"], div[tabindex="0"]');
            for (var i = 0; i < candidates.length; i++) {
                var el = candidates[i];
                var text = norm(el.innerText || el.textContent);
                if (!text) continue;
                for (var j = 0; j < want.length; j++) {
                    if (text === want[j] || text.indexOf(want[j]) >= 0 || want[j].indexOf(text) >= 0) {
                        var inp = el.querySelector('input[type="file"]');
                        if (inp) return inp;
                    }
                }
            }
            return null;
            """
            el = self.driver.execute_script(script, labels)
            if el:
                return el
        except Exception as exc:
            logger.debug("Error executing label search script: %s", exc)

        # 2. Fallback to icons/xpaths if text search fails
        for icon in icons:
            xpaths = [
                f'//li[.//span[@data-icon="{icon}"]]//input[@type="file"]',
                f'//*[.//span[@data-icon="{icon}"]]//input[@type="file"]',
                f'//footer//li[.//span[@data-icon="{icon}"]]//input[@type="file"]',
            ]
            for xpath in xpaths:
                try:
                    for el in self.driver.find_elements(By.XPATH, xpath):
                        if self._classify_file_input(el) == kind:
                            return el
                except Exception as exc:
                    logger.debug("Error finding file input with xpath: %s", exc)
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
        var roots = [document.body];
        var footer = document.querySelector('#main footer') || document.querySelector('footer');
        if (footer) roots.unshift(footer);
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
        except Exception as exc:
            logger.debug("Could not activate attach menu option %s: %s", data_icon, exc)
            return False

    def _js_activate_attach_menu_option_by_text(self, labels):
        """Finds row by text, blocks its nested file input click/mousedown, and dispatch click events on the row."""
        if not self.driver:
            return False
        script = """
        var labels = arguments[0];
        function isVisible(el) {
            if (!el) return false;
            var st = window.getComputedStyle(el);
            return st.display !== 'none' && st.visibility !== 'hidden' && el.offsetParent !== null;
        }
        function norm(s) {
            return (s || '').replace(/\\s+/g, ' ').trim().toLowerCase();
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
        var want = labels.map(norm);
        var candidates = document.querySelectorAll(
            'li, div[role="button"], div[tabindex="0"], span[dir="auto"], button, [role="menuitem"]'
        );
        for (var i = 0; i < candidates.length; i++) {
            var el = candidates[i];
            if (!isVisible(el)) continue;
            var t = norm(el.innerText || el.textContent);
            if (!t) continue;
            for (var j = 0; j < want.length; j++) {
                if (t === want[j] || t.indexOf(want[j]) >= 0 || want[j].indexOf(t) >= 0) {
                    var row = el.closest('li')
                        || el.closest('[role="button"]')
                        || el.closest('button')
                        || el.closest('[role="menuitem"]')
                        || el.closest('div[tabindex]')
                        || el;
                    if (!isVisible(row)) continue;
                    
                    var inp = row.querySelector('input[type="file"]');
                    if (inp) {
                        blockInputPicker(inp);
                    }
                    
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
        }
        return false;
        """
        try:
            return bool(self.driver.execute_script(script, labels))
        except Exception as exc:
            logger.debug("Could not activate attach menu option by text: %s", exc)
            return False

    def _find_file_input_for_kind(self, kind, exclude_signatures=None):
        """Scan all file inputs on page (attach menu is often outside footer)."""
        exclude_signatures = exclude_signatures or set()
        try:
            inputs = self.driver.find_elements(By.CSS_SELECTOR, 'input[type="file"]')
        except Exception as exc:
            logger.debug("Could not enumerate file inputs: %s", exc)
            return None
        for el in inputs:
            sig = self._file_input_signature(el)
            if sig and sig in exclude_signatures:
                continue
            if self._classify_file_input(el) == kind:
                return el
        return None

    def _activate_attach_menu_option(self, input_kind, stop_event=None):
        """Open Photos/Videos or Document row in the (+) menu."""
        if input_kind == "document":
            icons = ["attach-document"]
            labels = ["Document", "مستند", "Documents"]
        else:
            icons = ["attach-image", "attach-gallery", "media", "gallery"]
            labels = [
                "Photos & videos",
                "Photos and videos",
                "Photos & Videos",
                "الصور ومقاطع الفيديو",
                "الصور والفيديو",
                "صور وفيديو",
            ]

        for icon in icons:
            if self._js_activate_attach_menu_option(icon):
                if stop_event:
                    stop_event.wait(0.4)
                else:
                    time.sleep(0.4)
                return True

        if self._js_activate_attach_menu_option_by_text(labels):
            if stop_event:
                stop_event.wait(0.4)
            else:
                time.sleep(0.4)
            return True

        return False

    def _click_attach_menu_row_by_text(self, labels):
        """Selenium click on visible attach-menu row (Arabic/English)."""
        if not self.driver:
            return False
        for label in labels:
            fragments = [
                f"//li[.//*[contains(normalize-space(.),'{label}')]]",
                f"//*[@role='button'][.//*[contains(normalize-space(.),'{label}')]]",
                f"//div[contains(@class,'x1n2onr6')][.//*[contains(normalize-space(.),'{label}')]]",
                f"//button[.//*[contains(normalize-space(.),'{label}')] or contains(normalize-space(.),'{label}')]",
                f"//*[@role='menuitem'][.//*[contains(normalize-space(.),'{label}')] or contains(normalize-space(.),'{label}')]",
            ]
            for xpath in fragments:
                try:
                    for el in self.driver.find_elements(By.XPATH, xpath):
                        if el.is_displayed():
                            # Prioritize direct JS click on the menu option to ensure React triggers the input injection
                            try:
                                self.driver.execute_script("arguments[0].click();", el)
                                return True
                            except Exception as exc:
                                logger.debug("Could not JS-click attach menu row %r: %s", label, exc)
                                if self._click_element(el):
                                    return True
                except Exception as exc:
                    logger.debug("Could not inspect attach menu row %r: %s", label, exc)
                    continue
        return False

    def _find_visible_menu_file_input(self, kind):
        """File input inside the open (+) menu popup."""
        if not self.driver:
            return None
        script = """
        var kind = arguments[0];
        function classify(accept) {
            accept = (accept || '').toLowerCase();
            if (!accept) return null;
            if (accept.indexOf('sticker') >= 0) return 'sticker';
            if (accept.indexOf('video/mp4') >= 0 || accept.indexOf('video/3gpp') >= 0
                || accept.indexOf('video/quicktime') >= 0 || accept.indexOf('video/*') >= 0)
                return 'media';
            if (accept === '*' || accept === '*/*') return 'document';
            if (accept.indexOf('image') < 0 && accept.indexOf('video') < 0) return 'document';
            return null;
        }
        function visible(el) {
            if (!el) return false;
            var st = window.getComputedStyle(el);
            if (st.display === 'none' || st.visibility === 'hidden') return false;
            var r = el.getBoundingClientRect();
            return r.width > 0 || r.height > 0;
        }
        var inputs = document.querySelectorAll('input[type="file"]');
        for (var i = 0; i < inputs.length; i++) {
            var inp = inputs[i];
            if (classify(inp.getAttribute('accept')) !== kind) continue;
            var host = inp.closest('li') || inp.closest('[role="listbox"]')
                || inp.closest('[data-animate-dropdown-item]') || inp.parentElement;
            if (host && visible(host)) return inp;
            if (visible(inp)) return inp;
        }
        return null;
        """
        try:
            return self.driver.execute_script(script, kind)
        except Exception as exc:
            logger.debug("Could not find visible menu file input for %s: %s", kind, exc)
            return None

    def _expose_attach_file_input(self, input_kind, existing_signatures, stop_event=None):
        """After attach (+) is open: find the correct file input and prepare for send_keys."""
        labels = (
            ["Document", "مستند", "Documents"]
            if input_kind == "document"
            else [
                "الصور ومقاطع الفيديو",
                "الصور والفيديو",
                "صور وفيديو",
                "معرض",
                "gallery",
                "Photos & videos",
                "Photos and videos",
                "Photos & Videos",
            ]
        )

        input_el = self._find_visible_menu_file_input(input_kind)
        if input_el:
            return input_el

        input_el = self._find_file_input_in_attach_menu(input_kind)
        if input_el:
            return input_el

        input_el = self._find_file_input_for_kind(input_kind, existing_signatures)
        if input_el:
            return input_el

        # Attempt 1: Resilient Selenium Click on menu row
        self._click_attach_menu_row_by_text(labels)
        
        # Check if click injected the file input in the DOM immediately
        input_el = self._wait_for_new_file_input(
            input_kind,
            existing_signatures,
            timeout=3.0,
            stop_event=stop_event,
        )
        if input_el:
            return input_el

        input_el = self._find_visible_menu_file_input(input_kind)
        if input_el:
            return input_el

        input_el = self._wait_for_file_input_in_attach_menu(
            input_kind, timeout=1.0, stop_event=stop_event
        )
        if input_el:
            return input_el

        # Attempt 2: JS Click fallback
        self._js_activate_attach_menu_option_by_text(labels)
        
        # Check if JS click injected the file input in the DOM immediately
        input_el = self._wait_for_new_file_input(
            input_kind,
            existing_signatures,
            timeout=4.0,
            stop_event=stop_event,
        )
        if input_el:
            return input_el

        input_el = self._find_visible_menu_file_input(input_kind)
        if input_el:
            return input_el

        # Last resort fallback: check any file input on the page matching kind
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
        except Exception as exc:
            logger.debug("Could not dismiss sticker panel: %s", exc)

    def _reset_compose_overlays(self):
        """Close sticker panel, media preview, and attach menu before a new upload."""
        for _ in range(3):
            if (
                not self._sticker_panel_visible()
                and not self._media_preview_visible()
            ):
                break
            try:
                self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
            except Exception as exc:
                logger.debug("Could not reset compose overlay with Escape: %s", exc)
            time.sleep(0.35)

    def recover_compose_state(self, stop_event=None):
        """Dismiss overlays and wait until footer chat input is usable (for retries)."""
        if stop_event and stop_event.is_set():
            return False
        self._reset_compose_overlays()
        self._dismiss_attach_menu()
        try:
            self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
        except Exception as exc:
            logger.debug("Could not recover compose state with Escape: %s", exc)
        if stop_event:
            stop_event.wait(0.4)
        else:
            time.sleep(0.4)
        return self._wait_for_footer_compose_ready(timeout=15, stop_event=stop_event)

    def _get_main_compose_footer(self):
        return self.navigator._get_main_compose_footer()

    def _find_compose_footer(self):
        return self.navigator._find_compose_footer()

    def _find_in_compose_footer(self, relative_xpaths):
        footer = self._get_main_compose_footer()
        if not footer:
            return None
        for xpath in relative_xpaths:
            try:
                for el in footer.find_elements(By.XPATH, xpath):
                    if el.is_displayed() and el.get_attribute("aria-disabled") != "true":
                        return el
            except Exception as exc:
                logger.debug("Could not inspect compose footer element for %s: %s", xpath, exc)
                continue
        return None

    def _is_active_chat_ready(self):
        return self.navigator.is_active_chat_ready()

    def _find_attach_button_js(self):
        return self.navigator._find_attach_button_js()

    def _find_attach_button(self):
        return self.navigator.find_attach_button()

    def _wait_for_footer_compose_ready(self, timeout=20, stop_event=None, require_attach=False):
        return self.navigator.wait_for_footer_compose_ready(timeout, stop_event, require_attach)

    def _find_footer_send_button(self, stop_event=None):
        send_btn = self._find_best_clickable(self.FOOTER_SEND_BUTTON_LOCATORS)
        if send_btn:
            return send_btn
        return self._wait_for_any(
            self.FOOTER_SEND_BUTTON_LOCATORS, timeout=8, stop_event=stop_event
        )

    def _focus_footer_chat_input(self, chat_input):
        try:
            self.driver.execute_script(
                "arguments[0].scrollIntoView({block:'center'}); arguments[0].focus();",
                chat_input,
            )
        except Exception as exc:
            logger.debug("Could not focus footer chat input: %s", exc)

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
        except Exception as exc:
            logger.debug("Could not expose file input before send_keys: %s", exc)
        try:
            input_el.send_keys(abs_path)
            return True
        except Exception as exc:
            logger.debug("Could not send file path to input %s: %s", abs_path, exc)
            return False

    def _dismiss_attach_menu(self):
        try:
            self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
            time.sleep(0.3)
        except Exception as exc:
            logger.debug("Could not dismiss attach menu: %s", exc)

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

    def _send_attachment_via_attach_menu(self, path, input_kind, stop_event=None, phone=None):
        """Single-path attach: reset overlays -> (+) -> JS menu row -> send_keys only."""
        if stop_event and stop_event.is_set():
            return "STOPPED"
        if self._handle_invalid_if_present(stop_event=stop_event):
            return "INVALID"

        max_attempts = 3
        last_err = "ERR_ATTACH_BTN_NOT_FOUND"

        for attempt in range(max_attempts):
            if stop_event and stop_event.is_set():
                return "STOPPED"

            if not self._is_active_chat_ready() and phone:
                self._ensure_chat_open_for_send(phone, stop_event=stop_event)

            self._reset_compose_overlays()
            if not self._is_active_chat_ready():
                last_err = "ERR_ATTACH_BTN_NOT_FOUND"
                if attempt < max_attempts - 1:
                    self.recover_compose_state(stop_event=stop_event)
                    self.bring_to_front()
                    if stop_event:
                        stop_event.wait(0.6)
                    else:
                        time.sleep(0.6)
                    continue
                return last_err

            if not self._wait_for_footer_compose_ready(
                timeout=20, stop_event=stop_event, require_attach=True
            ):
                self._emit("ERROR", "زر الإرفاق (+) غير جاهز")
                last_err = "ERR_ATTACH_BTN_NOT_FOUND"
                if attempt < max_attempts - 1:
                    self.recover_compose_state(stop_event=stop_event)
                    self.bring_to_front()
                    if stop_event:
                        stop_event.wait(0.8)
                    else:
                        time.sleep(0.8)
                    continue
                return last_err

            try:
                result = self._send_attachment_via_attach_menu_once(
                    path, input_kind, stop_event=stop_event
                )
                if result == "SUCCESS":
                    return "SUCCESS"
                if result in ("STOPPED", "ERR_STICKER_PANEL_OPENED"):
                    return result
                last_err = result
            except Exception as e:
                last_err = f"ERR_ATTACH: {str(e)[:250]}"

            if attempt < max_attempts - 1:
                self._dismiss_attach_menu()
                self._reset_compose_overlays()
                if stop_event:
                    stop_event.wait(0.8)
                else:
                    time.sleep(0.8)

        return last_err

    def _send_attachment_via_attach_menu_once(self, path, input_kind, stop_event=None):
        try:
            existing_signatures = self._snapshot_file_input_signatures()
            self._emit("STEP", "بدء إرفاق ملف", os.path.basename(path))

            attach_btn = self._find_attach_button()
            if not attach_btn:
                self._emit("ERROR", "زر الإرفاق (+) غير موجود")
                return "ERR_ATTACH_BTN_NOT_FOUND"

            # Use JavaScript click to ensure React synthetic event handlers trigger and the menu opens
            try:
                self.driver.execute_script("arguments[0].click();", attach_btn)
            except Exception as exc:
                logger.debug("Could not JS-click attach button; using fallback click: %s", exc)
                self._click_element(attach_btn)
                
            self._emit("STEP", "تم فتح قائمة الإرفاق (+)")
            if stop_event:
                stop_event.wait(1.2)
            else:
                time.sleep(1.2)

            input_el = self._expose_attach_file_input(
                input_kind,
                existing_signatures,
                stop_event=stop_event,
            )

            if not input_el or self._classify_file_input(input_el) != input_kind:
                self._emit("ERROR", "لم يُعثر على حقل رفع الملف في القائمة")
                self._dismiss_attach_menu()
                return "ERR_FILE_INPUT_NOT_FOUND"

            self._emit("INFO", "تم العثور على حقل الملف", input_kind)

            if self._sticker_panel_visible():
                self._dismiss_attach_menu()
                self._reset_compose_overlays()
                return "ERR_STICKER_PANEL_OPENED"

            if not self._send_keys_to_file_input(input_el, path):
                self._emit("ERROR", "فشل حقن مسار الملف (send_keys)")
                self._dismiss_attach_menu()
                return "ERR_FILE_INPUT_NOT_FOUND"

            self._emit("STEP", "تم حقن مسار الملف — انتظار المعاينة")

            if stop_event:
                stop_event.wait(1.0)
            else:
                time.sleep(1.0)

            if input_kind == "media" and self._sticker_panel_visible():
                self._dismiss_attach_menu()
                self._reset_compose_overlays()
                return "ERR_STICKER_PANEL_OPENED"

            if input_kind == "media":
                preview = self._wait_for_any(
                    self.MEDIA_PREVIEW_LOCATORS, timeout=20, stop_event=stop_event
                )
                if not preview:
                    self._emit("ERROR", "معاينة الصورة لم تظهر بعد الرفع")
                    self._dismiss_attach_menu()
                    return "ERR_FILE_INPUT_NOT_FOUND"
                self._emit("INFO", "ظهرت معاينة الوسائط")
                try:
                    self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
                except Exception as exc:
                    logger.debug("Could not send Escape after media preview appeared: %s", exc)
                if stop_event:
                    stop_event.wait(0.3)
                else:
                    time.sleep(0.3)

            self._emit("INFO", "اكتمل رفع الملف في الواجهة")
            return "SUCCESS"
        except Exception as e:
            self._dismiss_attach_menu()
            self._emit("ERROR", "استثناء أثناء الإرفاق", str(e)[:200])
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
        self._reset_compose_overlays()
        self._wait_for_preview_close(timeout=12, stop_event=stop_event)
        if stop_event and stop_event.is_set():
            return "STOPPED"
        if not self._wait_for_footer_compose_ready(timeout=20, stop_event=stop_event):
            return "ERR_CHAT_INPUT_NOT_FOUND"
        if stop_event:
            stop_event.wait(0.8)
        else:
            time.sleep(0.8)
        return "SUCCESS"

    def _send_attachment(self, path, media_type, caption=None, stop_event=None, phone=None):
        """Upload file via attach menu; send preview/doc; never touch footer chat during media step."""
        if stop_event and stop_event.is_set():
            return "STOPPED"
        if not self._is_active_chat_ready() and phone:
            self._ensure_chat_open_for_send(phone, stop_event=stop_event)

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
                path, input_kind, stop_event=stop_event, phone=phone
            )
        else:
            upload_result = self._try_direct_file_injection(
                path, input_kind, stop_event=stop_event
            )
            if upload_result is False:
                upload_result = self._send_attachment_via_attach_menu(
                    path, input_kind, stop_event=stop_event, phone=phone
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
                # Dismiss any blocking modal that may overlay the preview area (e.g. discard/ignore prompts)
                try:
                    self._dismiss_modal_if_present(stop_event=stop_event)
                except Exception as exc:
                    logger.debug("Could not dismiss blocking modal before media send: %s", exc)

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
                    # Final-resort JS click: try to find & click send inside preview via JS (avoids Selenium click issues)
                    try:
                        js_click = '''
                        var preview = document.querySelector('[data-testid="media-viewer"]') || document.querySelector('[role="dialog"]');
                        function visible(el){ if(!el) return false; var s=window.getComputedStyle(el); return s.display!=='none' && s.visibility!=='hidden' && el.offsetParent!==null; }
                        if(preview){
                            var spans = preview.querySelectorAll('span[data-icon]');
                            for(var i=0;i<spans.length;i++){ var d=spans[i].getAttribute('data-icon')||''; if(d.indexOf('send')>=0 && visible(spans[i])){ var btn=spans[i].closest('button')||spans[i].closest('[role="button"]')||spans[i]; try{ btn.click(); }catch(e){} return {clicked:true, why:'span-send'}; } }
                            var btns = preview.querySelectorAll('button, [role="button"]');
                            for(var j=0;j<btns.length;j++){ var b=btns[j]; var txt=(b.getAttribute('aria-label')||b.textContent||'').toLowerCase(); if((txt.indexOf('send')>=0 || txt.indexOf('إرسال')>=0) && visible(b)){ try{ b.click(); }catch(e){} return {clicked:true, why:'aria-text'}; } }
                            // Try dispatching Enter on preview
                            try{ var ev = new KeyboardEvent('keydown', {key:'Enter', code:'Enter', bubbles:true}); preview.dispatchEvent(ev); }catch(e){}
                            return {clicked:false, why:'none'};
                        }
                        return {clicked:false, why:'no-preview'};
                        '''
                        res = self.driver.execute_script(js_click)
                        if res and isinstance(res, dict) and res.get('clicked'):
                            self._emit('INFO', f"[JS-SEND] clicked preview send via {res.get('why')}")
                            send_btn = True
                    except Exception as exc:
                        logger.debug("Preview send JavaScript fallback failed: %s", exc)

                if not send_btn:
                    # Diagnostic: dump preview/dialog DOM to logs to help identify blocking overlays
                    try:
                        diag = self.driver.execute_script("""
                        var preview = document.querySelector('[data-testid="media-viewer"]') || document.querySelector('[role="dialog"]');
                        if(!preview) return {error:'NO_PREVIEW'};
                        var buttons = [];
                        preview.querySelectorAll('button, [role="button"]').forEach(function(b){
                            var txt = (b.textContent||'').trim().slice(0,80);
                            var aria = b.getAttribute('aria-label')||'';
                            var icons = Array.from(b.querySelectorAll('span[data-icon]')).map(s=>s.getAttribute('data-icon'));
                            var vis = window.getComputedStyle(b).display!=='none' && b.offsetParent!==null;
                            buttons.push({tag:b.tagName, text:txt, aria:aria, icons:icons, visible:vis});
                        });
                        var dialogs = [];
                        document.querySelectorAll('div[role="dialog"], div[class*="modal"]').forEach(function(d){
                            if(window.getComputedStyle(d).display==='none') return;
                            dialogs.push({text:d.textContent.trim().slice(0,200)});
                        });
                        return {buttons:buttons, dialogs:dialogs};
                        """
                        )
                        self._emit("ERROR", f"[DIAG-PREVIEW] {diag}")
                    except Exception as e:
                        self._emit("ERROR", f"[DIAG-PREVIEW] dump failed: {e}")
                    self._emit("ERROR", "زر إرسال المعاينة غير موجود")
                    return "ERR_SEND_BTN_NOT_FOUND"

            if stop_event and stop_event.is_set():
                return "STOPPED"

            self._emit("STEP", "الضغط على إرسال المعاينة")
            if not self._click_element(send_btn):
                self.driver.execute_script("arguments[0].click();", send_btn)

            file_size = os.path.getsize(path) if os.path.exists(path) else 0
            wait_time = max(4, min(30, file_size // (1024 * 1024)) + 3)
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

        # Try waiting for the configured locators first
        waited = self._wait_for_any(
            self.MEDIA_PREVIEW_SEND_BUTTON_LOCATORS, timeout=10, stop_event=stop_event
        )
        if waited:
            return waited

        # JS fallback: search inside the preview/dialog or globally for any visible send-like control
        if not self.driver:
            return None
        try:
            script = """
            function visible(el){ if(!el) return false; var st=window.getComputedStyle(el); return st.display!=='none' && st.visibility!=='hidden' && el.offsetParent!==null; }
            var preview = document.querySelector('[data-testid="media-viewer"]') || document.querySelector('[role="dialog"]');
            var containers = [];
            if (preview) {
                containers.push(preview);
            } else {
                containers.push(document);
            }
            var selectors = [
                'span[data-icon*="send"]',
                'span[data-icon*="send-light"]',
                'button[aria-label*="Send"]',
                'button[aria-label*="إرسال"]',
                '[role="button"][aria-label*="Send"]',
                '[role="button"][aria-label*="إرسال"]'
            ];
            for (var ci = 0; ci < containers.length; ci++) {
                var container = containers[ci];
                for (var si = 0; si < selectors.length; si++) {
                    var els = container.querySelectorAll(selectors[si]);
                    for (var ei = 0; ei < els.length; ei++) {
                        if (visible(els[ei])) {
                            var el = els[ei];
                            if (el.tagName.toLowerCase() === 'span') {
                                var clickable = el.closest('button') || el.closest('[role="button"]') || el;
                                if (clickable) return clickable;
                            }
                            return el;
                        }
                    }
                }
            }
            return null;
            """
            return self.driver.execute_script(script)
        except Exception as exc:
            logger.debug("Could not locate media preview send button: %s", exc)
            return None

