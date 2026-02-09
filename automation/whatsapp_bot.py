import time
import random
import urllib.parse
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
import os

class WhatsAppBot:
    def __init__(self, user_data_dir):
        self.user_data_dir = user_data_dir
        self.driver = None
        self.background_mode = False

        # Common locators (mix XPath + CSS for robustness)
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
            (By.XPATH, '//div[@role="button" and @aria-label="Send"]'),
            (By.XPATH, '//div[@role="button" and contains(@aria-label,"Send")]'),
            (By.XPATH, '//button[contains(@aria-label,"Send")]'),
            (By.XPATH, '//div[@role="dialog"]//span[contains(@data-icon,"send")]'),
            (By.XPATH, '//div[@role="dialog"]//button[contains(@aria-label,"Send")]'),
            (By.XPATH, '//div[@role="dialog"]//div[@role="button" and contains(@aria-label,"Send")]'),
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
            (By.XPATH, '//input[@accept="image/*,video/mp4,video/3gpp,video/quicktime"]'),
            (By.XPATH, '//input[@type="file" and contains(@accept,"image")]'),
            (By.XPATH, '//input[@type="file"]'),
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

    def _wait_for_any(self, locators, timeout=30, poll=0.5):
        end_time = time.time() + timeout
        while time.time() < end_time:
            el = self._find_any(locators)
            if el:
                return el
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

    def _wait_for_preview_close(self, timeout=5, poll=0.3):
        end_time = time.time() + timeout
        while time.time() < end_time:
            if not self._find_any(self.MEDIA_PREVIEW_LOCATORS):
                return True
            time.sleep(poll)
        return False

    def _wait_for_chat_or_invalid(self, timeout=60, poll=0.5):
        end_time = time.time() + timeout
        while time.time() < end_time:
            if self._find_any(self.INVALID_NUMBER_LOCATORS):
                return "INVALID"
            if self._find_any(self.CHAT_INPUT_LOCATORS):
                return "READY"
            time.sleep(poll)
        return "TIMEOUT"

    def is_logged_in(self):
        if not self.driver:
            return False
        return self._find_any(self.SEARCH_BOX_LOCATORS) is not None or self._find_any(self.CHAT_INPUT_LOCATORS) is not None

    def setup_driver(self, start_minimized=False):
        """Initializes the Chrome driver with session persistence."""
        if not os.path.exists(self.user_data_dir):
            os.makedirs(self.user_data_dir)
            
        options = webdriver.ChromeOptions()
        options.add_argument(f"user-data-dir={self.user_data_dir}")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        if start_minimized:
            options.add_argument("--start-minimized")
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)
        self.background_mode = start_minimized
        return self.driver

    def open_whatsapp(self):
        """Opens WhatsApp Web and waits for login."""
        if not self.driver:
            self.setup_driver()
        self.driver.get("https://web.whatsapp.com")

    def wait_for_login(self, timeout=120):
        """Waits until the chat list is visible, indicating successful login."""
        try:
            WebDriverWait(self.driver, timeout).until(lambda d: self.is_logged_in())
            return True
        except:
            return False

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

    def send_message(self, phone, name, message_template, image_path=None, stop_event=None):
        """Sends a message (and optionally an image) to a single phone number."""
        if stop_event and stop_event.is_set():
            return "STOPPED"
        if not self.driver:
            return "ERR_NOT_READY"

        # Personalize message
        message_template = message_template or ""
        message = message_template.replace("{name}", name).strip()
        
        if not image_path and not message:
            return "ERR_EMPTY_MESSAGE"

        # 1. Open the chat (always without prefilled text for reliability)
        url = f"https://web.whatsapp.com/send?phone={phone}"
            
        try:
            self.driver.get(url)
            
            # 2. Wait for loading (Chat input or invalid number)
            ready_state = self._wait_for_chat_or_invalid(timeout=90)
            
            # Check for invalid phone number
            if ready_state == "INVALID":
                return "INVALID"
            if ready_state == "TIMEOUT":
                return "ERR_TIMEOUT"

            time.sleep(random.uniform(5, 7))

            if image_path:
                # 3. Attach Image
                try:
                    attach_btn = self._find_any(self.ATTACH_BUTTON_LOCATORS)
                    if not attach_btn:
                        return "ERR_ATTACH_BTN_NOT_FOUND"

                    # Click the plus button to reveal menu
                    self.driver.execute_script("arguments[0].click();", attach_btn)
                    time.sleep(2)
                    
                    # Find the hidden input for images
                    image_input = self._wait_for_any(self.FILE_INPUT_LOCATORS, timeout=20)
                    if not image_input:
                        return "ERR_FILE_INPUT_NOT_FOUND"
                    image_input.send_keys(image_path)
                    
                    # 4. Wait for Preview & Caption Box
                    self._wait_for_any(self.MEDIA_PREVIEW_LOCATORS, timeout=40)
                    caption_box = None
                    if message:
                        caption_box = self._wait_for_any(self.CAPTION_BOX_LOCATORS, timeout=40)
                        if not caption_box:
                            return "ERR_CAPTION_BOX_NOT_FOUND"
                        time.sleep(1.5)
                        caption_box.send_keys(message)
                        time.sleep(2.5)
                    
                    # 5. Final Send Click
                    send_btn = self._find_best_clickable(self.SEND_BUTTON_LOCATORS)
                    if not send_btn:
                        send_btn = self._wait_for_any(self.SEND_BUTTON_LOCATORS, timeout=10)
                    if not send_btn:
                        return "ERR_FINAL_SEND_BTN_NOT_FOUND"
                        
                    self.driver.execute_script("arguments[0].click();", send_btn)
                    # If preview still open, try Enter fallback
                    if not self._wait_for_preview_close(timeout=5):
                        # JS fallback: click last visible send button
                        try:
                            self.driver.execute_script("""
                                const nodes = Array.from(document.querySelectorAll('[data-icon*="send"],button[aria-label*="Send"],div[role="button"][aria-label*="Send"]'));
                                for (let i = nodes.length - 1; i >= 0; i--) {
                                    const el = nodes[i];
                                    const style = window.getComputedStyle(el);
                                    if (el.offsetParent !== null && style.visibility !== 'hidden' && el.getAttribute('aria-disabled') !== 'true') {
                                        el.click();
                                        break;
                                    }
                                }
                            """)
                        except Exception:
                            pass
                        try:
                            if caption_box:
                                caption_box.send_keys(Keys.ENTER)
                            else:
                                self.driver.switch_to.active_element.send_keys(Keys.ENTER)
                        except Exception:
                            pass
                    
                    # Wait for upload to complete
                    time.sleep(6)
                    return "SUCCESS"
                except Exception as e:
                    return f"ERR_IMAGE_FLOW: {str(e)[:100]}"
            else:
                # 6. Text-only Send
                try:
                    chat_input = self._wait_for_any(self.CHAT_INPUT_LOCATORS, timeout=30)
                    if not chat_input:
                        return "ERR_CHAT_INPUT_NOT_FOUND"
                    chat_input.click()
                    chat_input.send_keys(message)
                    time.sleep(0.5)

                    send_btn = self._wait_for_any(self.SEND_BUTTON_LOCATORS, timeout=10)
                    if send_btn:
                        try:
                            self.driver.execute_script("arguments[0].click();", send_btn)
                        except Exception:
                            pass
                    # Fallback: press Enter to send
                    try:
                        chat_input.send_keys(Keys.ENTER)
                    except Exception:
                        pass
                    time.sleep(3)
                    return "SUCCESS"
                except Exception:
                    return "ERR_SEND_BTN_TIMEOUT"
                
        except TimeoutException:
            return "ERR_TIMEOUT"
        except Exception as e:
            return f"ERR_GENERAL: {str(e)[:100]}"

    def close(self):
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            self.driver = None
