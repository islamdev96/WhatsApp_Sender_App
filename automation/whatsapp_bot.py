import time
import random
import urllib.parse
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import os

class WhatsAppBot:
    def __init__(self, user_data_dir):
        self.user_data_dir = user_data_dir
        self.driver = None

    def setup_driver(self):
        """Initializes the Chrome driver with session persistence."""
        if not os.path.exists(self.user_data_dir):
            os.makedirs(self.user_data_dir)
            
        options = webdriver.ChromeOptions()
        options.add_argument(f"user-data-dir={self.user_data_dir}")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)
        return self.driver

    def open_whatsapp(self):
        """Opens WhatsApp Web and waits for login."""
        if not self.driver:
            self.setup_driver()
        self.driver.get("https://web.whatsapp.com")

    def wait_for_login(self, timeout=120):
        """Waits until the chat list is visible, indicating successful login."""
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.XPATH, '//div[@contenteditable="true"][@data-tab="3"]'))
            )
            return True
        except:
            return False

    def bring_to_front(self):
        """Brings the browser window to the front."""
        if self.driver:
            try:
                self.driver.execute_script("window.focus();")
                self.driver.maximize_window()
            except:
                pass

    def send_message(self, phone, name, message_template, image_path=None, stop_event=None):
        """Sends a message (and optionally an image) to a single phone number."""
        if stop_event and stop_event.is_set():
            return "STOPPED"

        # Personalize message
        message = message_template.replace("{name}", name)
        
        # 1. Open the chat
        if image_path:
            # We open without text because we'll fill the caption manually
            url = f"https://web.whatsapp.com/send?phone={phone}"
        else:
            encoded_msg = urllib.parse.quote(message)
            url = f"https://web.whatsapp.com/send?phone={phone}&text={encoded_msg}"
            
        try:
            self.driver.get(url)
            
            # 2. Wait for loading (Chat input or invalid number)
            # We look for ANY of these to know the page has reacted
            WebDriverWait(self.driver, 90).until(
                lambda d: d.find_elements(By.XPATH, '//div[@contenteditable="true"][@data-tab="10"]') or 
                          d.find_elements(By.XPATH, '//span[@data-icon="plus"]') or
                          d.find_elements(By.XPATH, '//div[contains(text(), "invalid")]') or
                          d.find_elements(By.XPATH, '//div[contains(text(), "غير صحيح")]')
            )
            
            # Check for invalid phone number
            if self.driver.find_elements(By.XPATH, '//div[contains(text(), "invalid")]') or \
               self.driver.find_elements(By.XPATH, '//div[contains(text(), "غير صحيح")]'):
                return "INVALID"

            time.sleep(random.uniform(5, 7))

            if image_path:
                # 3. Attach Image
                try:
                    # Find plus/attach button
                    plus_btns = self.driver.find_elements(By.XPATH, '//span[@data-icon="plus"]') or \
                                self.driver.find_elements(By.XPATH, '//div[@title="Attach"]') or \
                                self.driver.find_elements(By.XPATH, '//div[@title="إرفاق"]')
                    
                    if not plus_btns:
                        return "ERR_ATTACH_BTN_NOT_FOUND"

                    # Click the plus button to reveal menu
                    self.driver.execute_script("arguments[0].click();", plus_btns[0])
                    time.sleep(2)
                    
                    # Find the hidden input for images
                    # This input usually exists once the plus menu is clicked (or even before)
                    try:
                        image_input = self.driver.find_element(By.XPATH, '//input[@accept="image/*,video/mp4,video/3gpp,video/quicktime"]')
                        image_input.send_keys(image_path)
                    except:
                        return "ERR_FILE_INPUT_NOT_FOUND"
                    
                    # 4. Wait for Preview & Caption Box
                    # The caption box is where we put our message to send them together
                    caption_box = WebDriverWait(self.driver, 30).until(
                        EC.presence_of_element_located((By.XPATH, '//div[@contenteditable="true"][@data-tab="10"]'))
                    )
                    
                    time.sleep(1)
                    # Clear any existing text (though it should be empty)
                    caption_box.send_keys(message)
                    time.sleep(2)
                    
                    # 5. Final Send Click
                    send_btn = WebDriverWait(self.driver, 30).until(
                        EC.element_to_be_clickable((By.XPATH, '//span[contains(@data-icon, "send")]'))
                    )
                    send_btn.click()
                    
                    # Wait for upload to complete
                    time.sleep(5)
                    return "SUCCESS"
                except Exception as e:
                    return f"ERR_IMAGE_FLOW: {str(e)[:100]}"
            else:
                # 6. Text-only Send
                try:
                    send_btn = WebDriverWait(self.driver, 30).until(
                        EC.element_to_be_clickable((By.XPATH, '//span[@data-icon="send"]'))
                    )
                    send_btn.click()
                    time.sleep(3)
                    return "SUCCESS"
                except:
                    return "ERR_SEND_BTN_TIMEOUT"
                
        except Exception as e:
            return f"ERR_GENERAL: {str(e)[:100]}"

    def close(self):
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            self.driver = None
