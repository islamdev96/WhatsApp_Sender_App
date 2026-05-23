import time
import re
import urllib.parse
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

class GMapsScraper:
    def __init__(self, driver):
        self.driver = driver

    def scrape(self, query, stop_event, max_results=100, update_callback=None):
        results = []
        try:
            encoded_query = urllib.parse.quote_plus(query)
            url = f"https://www.google.com/maps/search/{encoded_query}"
            self.driver.get(url)
            
            # Wait for results to load
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div[role='feed']"))
            )
        except TimeoutException:
            if update_callback:
                update_callback("ERROR", "انتهت مهلة تحميل خرائط جوجل.")
            return results
        except WebDriverException as e:
            if update_callback:
                update_callback("ERROR", f"خطأ في المتصفح: {str(e)}")
            return results

        feed = self.driver.find_element(By.CSS_SELECTOR, "div[role='feed']")
        
        last_count = 0
        scroll_attempts = 0
        
        while len(results) < max_results and not stop_event.is_set():
            # Find all item links in the feed
            items = feed.find_elements(By.CSS_SELECTOR, "a[href*='/maps/place/']")
            
            # If no new items loaded after a few scrolls, we might be at the end
            if len(items) == last_count:
                scroll_attempts += 1
                if scroll_attempts >= 5:  # Give it 5 tries to load more
                    break
            else:
                scroll_attempts = 0
                last_count = len(items)

            # Process new items
            for i in range(len(results), len(items)):
                if stop_event.is_set() or len(results) >= max_results:
                    break
                    
                item = items[i]
                try:
                    # Scroll item into view
                    self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", item)
                    time.sleep(0.5)
                    
                    # Sometimes the phone number is inside the aria-label of the item or its children.
                    # Or we need to click it. Clicking takes too long. Let's try to extract from text first.
                    parent_div = item.find_element(By.XPATH, "./..")
                    text_content = parent_div.text
                    
                    # Extract title (usually first line)
                    lines = text_content.split('\n')
                    title = lines[0] if lines else "Unknown"
                    
                    # Look for phone number using regex
                    # Maps usually formats them as +XXX XX XXX XXXX or similar
                    phone_match = re.search(r'(\+?\d{1,4}[\s-]?\d{1,4}[\s-]?\d{3,4}[\s-]?\d{3,4})', text_content)
                    
                    phone = ""
                    if phone_match:
                        phone = phone_match.group(1)
                    
                    # If phone not found in text, it's harder without clicking. 
                    # Often the phone is visible in the list view if it's a search result.
                    
                    if phone:
                        # Clean phone
                        clean_phone = re.sub(r'[^\d+]', '', phone)
                        # Ensure it looks like a valid phone (at least 7 digits)
                        if len(clean_phone.replace("+", "")) >= 7:
                            results.append({
                                "name": title,
                                "phone": clean_phone
                            })
                            if update_callback:
                                update_callback("FOUND", {"name": title, "phone": clean_phone, "count": len(results)})
                except Exception as e:
                    pass

            # Scroll down the feed container to load more
            if not stop_event.is_set():
                try:
                    self.driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", feed)
                    time.sleep(2)
                except Exception:
                    pass

        return results
