"""WhatsApp Sender Pro — Auto-reply: unread chats, read messages, reply."""
import time

from selenium.webdriver.common.by import By
from selenium.common.exceptions import (
    TimeoutException, NoSuchElementException, StaleElementReferenceException,
    WebDriverException, ElementClickInterceptedException,
    ElementNotInteractableException, JavascriptException,
)

from utils.logger import logger


class ChatbotMixin:
    """Mixin: Auto-reply: unread chats, read messages, reply."""

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
                    except Exception as exc:
                        logger.debug("Could not inspect unread chat element: %s", exc)
                if valid_elements:
                    return valid_elements
            return []
        except Exception as exc:
            logger.debug("Could not find unread chats: %s", exc)
            return []

    def open_chat_element(self, chat_element):
        """Clicks a chat row in the side list to open that conversation."""
        try:
            self.driver.execute_script("arguments[0].click();", chat_element)
            time.sleep(1)
            return True
        except Exception as exc:
            logger.debug("Could not open chat element: %s", exc)
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
            except Exception as exc:
                logger.debug("Could not read active chat title with locator %s: %s", value, exc)
                continue
        return ""

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
        except Exception as exc:
            logger.debug("Could not read last incoming message: %s", exc)
            return ""

    def reply_to_current_chat(self, message):
        """Sends a message to the currently open chat."""
        # Just use the existing _send_text which looks for the chat input and sends
        return self._send_text(message)

