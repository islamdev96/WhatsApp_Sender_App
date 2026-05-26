import time
from selenium.webdriver.common.by import By
from utils.logger import logger

class WhatsAppNavigator:
    def __init__(self, bot):
        self.bot = bot
        
        # Locators moved from whatsapp_bot.py
        self.LOGGED_IN_LOCATORS = [
            (By.ID, "pane-side"),
            (By.XPATH, '//div[@id="pane-side"]'),
            (By.XPATH, '//div[@data-testid="chat-list"]'),
            (By.XPATH, '//header[@data-testid="chatlist-header"]'),
            (By.XPATH, '//div[@id="side"]'),
            (By.XPATH, '//div[@role="grid" and contains(@class, "chat-list")]'),
        ]
        self.SEARCH_BOX_LOCATORS = [
            (By.CSS_SELECTOR, 'div[data-testid="search-input-textbox"]'),
            (By.XPATH, '//div[@data-testid="search-input-textbox"]'),
            (By.XPATH, '//div[@contenteditable="true"][@data-tab="3"]'),
            (By.XPATH, '//div[@role="textbox" and @aria-label="Search input textbox"]'),
            (By.XPATH, '//div[@contenteditable="true" and @title="Search input textbox"]'),
            (By.XPATH, '//div[contains(@class, "lexical-rich-text-input")]//div[@contenteditable="true"]'),
        ]
        self.CHAT_INPUT_LOCATORS = [
            (By.XPATH, '//*[@id="main"]//footer//div[@contenteditable="true"][@role="textbox"]'),
            (By.XPATH, '//*[@id="main"]//footer//div[@contenteditable="true"][@data-tab="10"]'),
            (By.XPATH, '//*[@id="main"]//footer//div[@contenteditable="true" and contains(@class,"copyable-text")]'),
        ]
        self.ATTACH_BUTTON_LOCATORS = [
            (By.CSS_SELECTOR, '#main button[aria-label="Attach"]'),
            (By.CSS_SELECTOR, '#main button[aria-label="إرفاق"]'),
            (By.XPATH, '//*[@id="main"]//button[@data-testid="plus-rounded" or .//span[@data-icon="plus-rounded"]]'),
            (By.XPATH, '//*[@id="main"]//button[.//span[@data-icon="plus-rounded"]]'),
            (By.XPATH, '//*[@id="main"]//div[@role="button" and .//span[@data-icon="plus-rounded"]]'),
            (By.CSS_SELECTOR, '#main span[data-icon="plus-rounded"]'),
            (By.XPATH, '//*[@id="main"]//span[@data-icon="plus-rounded"]'),
            (By.CSS_SELECTOR, '#main span[data-icon="plus"]'),
            (By.XPATH, '//*[@id="main"]//span[@data-icon="plus"]'),
            (By.CSS_SELECTOR, '#main button[aria-label*="Attach"]'),
            (By.CSS_SELECTOR, '#main button[aria-label*="إرفاق"]'),
            (By.CSS_SELECTOR, '#main div[title*="Attach"]'),
            (By.CSS_SELECTOR, '#main div[title*="إرفاق"]'),
            (By.CSS_SELECTOR, '#main span[data-icon="attach-menu-plus"]'),
            (By.CSS_SELECTOR, '#main span[data-icon*="attach"]'),
            (By.CSS_SELECTOR, '#main span[data-icon*="clip"]'),
            (By.XPATH, '//*[@id="main"]//*[@aria-label="Attach"]'),
            (By.XPATH, '//*[@id="main"]//*[@aria-label="إرفاق"]'),
        ]
        self._ATTACH_BUTTON_RELATIVE_XPATHS = [
            './/button[.//span[@data-icon="plus-rounded"]]',
            './/button[@data-testid="plus-rounded"]',
            './/button[.//span[@data-icon="plus"]]',
            './/div[@role="button" and .//span[@data-icon="plus-rounded"]]',
            './/span[@data-icon="plus-rounded"]',
            './/span[@data-icon="plus"]',
            './/span[@data-icon="attach-menu-plus"]',
            './/span[contains(@data-icon,"attach")]',
            './/span[contains(@data-icon,"clip")]',
            './/*[@aria-label="Attach"]',
            './/*[@aria-label="إرفاق"]',
        ]

    @property
    def driver(self):
        return self.bot.driver

    def _emit(self, level, message, *args):
        self.bot._emit(level, message, *args)

    def _get_main_compose_footer(self):
        """Compose footer inside #main only (not side panel or stray footers)."""
        if not self.driver:
            return None
        try:
            for el in self.driver.find_elements(By.XPATH, '//*[@id="main"]//footer'):
                if el.is_displayed():
                    return el
        except Exception as exc:
            logger.debug("Could not locate main compose footer: %s", exc)
        return None

    def _find_compose_footer(self):
        """Footer of the open chat inside #main only."""
        footer = self._get_main_compose_footer()
        if footer:
            return footer
        if not self.driver:
            return None
        for xpath in ('//*[@id="main"]//div[contains(@class,"x1n2onr6")]//footer', '//*[@id="main"]//footer'):
            try:
                for el in self.driver.find_elements(By.XPATH, xpath):
                    if el.is_displayed():
                        return el
            except Exception as exc:
                logger.debug("Could not inspect compose footer candidate: %s", exc)
                continue
        return None

    def is_active_chat_ready(self):
        """True when a conversation compose bar is open (not the empty landing screen)."""
        if not self.driver:
            return False
            
        # DOM DIAGNOSTIC: Query state to solve the READY mystery
        try:
            dom_status = self.driver.execute_script("""
            var main = document.getElementById('main') || document.querySelector('#main');
            var footer = document.querySelector('footer');
            var mainFooter = main ? main.querySelector('footer') : null;
            var editables = document.querySelectorAll('[contenteditable="true"]');
            return {
                hasMain: !!main,
                mainTag: main ? main.tagName : 'N/A',
                hasFooter: !!footer,
                hasMainFooter: !!mainFooter,
                editablesCount: editables.length
            };
            """)
            if dom_status['hasMain'] or dom_status['editablesCount'] > 0:
                self._emit("INFO", f"[DIAG-DOM-READY] hasMain={dom_status['hasMain']} mainTag={dom_status['mainTag']} hasFooter={dom_status['hasFooter']} hasMainFooter={dom_status['hasMainFooter']} editables={dom_status['editablesCount']}")
        except Exception as exc:
            logger.debug("Could not collect active chat DOM diagnostics: %s", exc)

        footer = self._find_compose_footer()
        if not footer:
            return False
        try:
            inputs = footer.find_elements(
                By.XPATH,
                './/div[@contenteditable="true"][@role="textbox"]'
                ' | .//div[@contenteditable="true"][@data-tab="10"]'
                ' | .//div[@contenteditable="true" and contains(@class,"copyable-text")]',
            )
            for inp in inputs:
                if inp.is_displayed():
                    return True
        except Exception as exc:
            logger.debug("Could not inspect footer compose inputs: %s", exc)
        return False

    def _find_attach_button_js(self):
        """Find attach (+) control inside #main chat footer via JavaScript."""
        if not self.driver:
            return None
        script = """
        var container = document.querySelector('#main');
        if (!container) return null;
        function visible(el) {
            if (!el) return false;
            var st = window.getComputedStyle(el);
            return st.display !== 'none' && st.visibility !== 'hidden' && el.offsetParent !== null;
        }
        function pickClickable(span) {
            return span.closest('[role="button"]')
                || span.closest('button')
                || span.closest('div[tabindex="0"]')
                || span.parentElement
                || span;
        }
        var icons = ['plus-rounded', 'plus', 'attach-menu-plus', 'wds-ic-attach', 'clip', 'clip-light'];
        for (var i = 0; i < icons.length; i++) {
            var spans = container.querySelectorAll('span[data-icon="' + icons[i] + '"]');
            for (var j = 0; j < spans.length; j++) {
                if (visible(spans[j])) return pickClickable(spans[j]);
            }
        }
        var partial = container.querySelectorAll('span[data-icon*="attach"], span[data-icon*="clip"]');
        for (var k = 0; k < partial.length; k++) {
            if (visible(partial[k])) return pickClickable(partial[k]);
        }
        var labeled = container.querySelectorAll(
            '[aria-label="Attach"], [aria-label="إرفاق"], [title="Attach"], [title="إرفاق"]'
        );
        for (var m = 0; m < labeled.length; m++) {
            if (visible(labeled[m])) return labeled[m];
        }
        return null;
        """
        try:
            return self.driver.execute_script(script)
        except Exception as exc:
            logger.debug("Could not find attach button with JavaScript: %s", exc)
            return None

    def find_attach_button(self):
        # We need to find elements inside compose footer using relative paths
        footer = self._get_main_compose_footer()
        if footer:
            for xpath in self._ATTACH_BUTTON_RELATIVE_XPATHS:
                try:
                    for el in footer.find_elements(By.XPATH, xpath):
                        if el.is_displayed() and el.get_attribute("aria-disabled") != "true":
                            return el
                except Exception as exc:
                    logger.debug("Could not inspect attach button candidate: %s", exc)
                    continue

        attach_btn = self.bot._find_best_clickable(self.ATTACH_BUTTON_LOCATORS)
        if attach_btn:
            return attach_btn
            
        js_btn = self._find_attach_button_js()
        if js_btn:
            return js_btn

        # === DIAGNOSTIC: dump all icons in #main when attach button not found ===
        try:
            diag = self.driver.execute_script("""
            var result = {icons: [], buttons: [], ariaLabels: [], titles: []};
            var main = document.querySelector('#main');
            if (!main) { result.error = 'NO #main FOUND'; return result; }

            var spans = main.querySelectorAll('span[data-icon]');
            for (var i = 0; i < spans.length; i++) {
                var icon = spans[i].getAttribute('data-icon');
                var vis = window.getComputedStyle(spans[i]).display !== 'none';
                result.icons.push(icon + (vis ? ' [VISIBLE]' : ' [hidden]'));
            }

            var btns = main.querySelectorAll('button, [role="button"], div[tabindex="0"]');
            for (var j = 0; j < btns.length; j++) {
                var b = btns[j];
                var label = b.getAttribute('aria-label') || b.getAttribute('title') || b.textContent.trim().substring(0, 40) || '(no label)';
                var tag = b.tagName;
                var vis2 = window.getComputedStyle(b).display !== 'none';
                result.buttons.push(tag + ': ' + label + (vis2 ? ' [VISIBLE]' : ' [hidden]'));
            }

            var footer = main.querySelector('footer');
            result.hasFooter = !!footer;
            if (footer) {
                var fIcons = footer.querySelectorAll('span[data-icon]');
                result.footerIcons = [];
                for (var k = 0; k < fIcons.length; k++) {
                    result.footerIcons.push(fIcons[k].getAttribute('data-icon'));
                }
            }

            return result;
            """)
            self._emit("ERROR", f"[DIAG] Attach button NOT FOUND. DOM dump: {diag}")
        except Exception as diag_err:
            self._emit("ERROR", f"[DIAG] Failed to dump DOM: {diag_err}")

        return None

    def wait_for_chat_or_invalid(self, timeout=60, poll=0.5, stop_event=None):
        end_time = time.time() + timeout
        while time.time() < end_time:
            if stop_event and stop_event.is_set():
                return "STOPPED"
            if self.bot._page_indicates_invalid_number():
                self.bot._dismiss_invalid_number_modal(stop_event=stop_event)
                self.bot._last_opened_phone = None
                self.bot._force_url_next = True
                return "INVALID"
            if self.is_active_chat_ready():
                # Temporal stability check: wait 2 seconds and verify it remains ready!
                if stop_event:
                    stop_event.wait(2.0)
                else:
                    time.sleep(2.0)
                if self.is_active_chat_ready():
                    return "READY"
                else:
                    self._emit("INFO", "كشف جاهزية مؤقتة (محادثة سابقة)، مواصلة الانتظار...")
            if stop_event:
                stop_event.wait(poll)
            else:
                time.sleep(poll)
        if self.bot._handle_invalid_if_present(stop_event=stop_event):
            return "INVALID"
        return "TIMEOUT"

    def wait_for_footer_compose_ready(
        self, timeout=20, stop_event=None, require_attach=False
    ):
        """Wait until the open-chat compose footer is visible; optionally wait for (+)."""
        end_time = time.time() + timeout
        _diag_logged = False
        while time.time() < end_time:
            if stop_event and stop_event.is_set():
                return False

            footer = self._find_compose_footer()
            chat_ready = self.is_active_chat_ready()

            if chat_ready:
                if not require_attach:
                    return True
                btn = self.find_attach_button()
                if btn:
                    return True
                if not _diag_logged:
                    self._emit("WARN", f"[DIAG-WAIT] chat_ready=True but attach NOT found. footer={'YES' if footer else 'NO'}")
                    _diag_logged = True
            else:
                if not _diag_logged:
                    has_main = False
                    has_footer = False
                    has_textbox = False
                    try:
                        has_main = bool(self.driver.find_elements(By.ID, "main"))
                        has_footer = bool(footer)
                        if footer:
                            inputs = footer.find_elements(By.XPATH,
                                './/div[@contenteditable="true"][@role="textbox"]'
                                ' | .//div[@contenteditable="true"][@data-tab="10"]'
                                ' | .//div[@contenteditable="true" and contains(@class,"copyable-text")]')
                            has_textbox = any(inp.is_displayed() for inp in inputs)
                    except Exception as exc:
                        logger.debug("Could not collect wait diagnostics: %s", exc)
                    self._emit("WARN", f"[DIAG-WAIT] chat_ready=False! main={has_main} footer={has_footer} textbox={has_textbox}")
                    
                    # Run the exact JS query requested by the user to see all contenteditables on screen!
                    try:
                        editables_info = self.driver.execute_script("""
                        var result = [];
                        document.querySelectorAll('[contenteditable="true"]').forEach(e => {
                            result.push({
                                tag: e.tagName,
                                dataTab: e.getAttribute('data-tab') || 'N/A',
                                inFooter: !!e.closest('footer'),
                                className: e.className.slice(0, 40)
                            });
                        });
                        return result;
                        """)
                        self._emit("INFO", f"[DIAG-EDITABLES] Query result ({len(editables_info)} found):")
                        for info in editables_info:
                            self._emit("INFO", f"  -> Tag: {info['tag']}, data-tab: {info['dataTab']}, inFooter: {info['inFooter']}, class: {info['className']}")
                    except Exception as js_err:
                        self._emit("ERROR", f"[DIAG-EDITABLES] Failed JS: {js_err}")
                        
                    _diag_logged = True

                if require_attach:
                    btn = self._find_attach_button_js()
                    if btn:
                        self._emit("INFO", "[DIAG-WAIT] Found attach via JS fallback despite chat_ready=False!")
                        return True

            if stop_event:
                stop_event.wait(0.35)
            else:
                time.sleep(0.35)

        # Final attempt
        if self.is_active_chat_ready():
            if not require_attach:
                return True
            if self.find_attach_button():
                return True

        if require_attach:
            btn = self._find_attach_button_js()
            if btn:
                self._emit("INFO", "[DIAG-WAIT] Final JS fallback found attach button!")
                return True

        self._emit("ERROR", f"[DIAG-WAIT] TIMEOUT after {timeout}s. chat_ready={self.is_active_chat_ready()} require_attach={require_attach}")
        return False
