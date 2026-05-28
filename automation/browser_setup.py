"""WhatsApp Sender Pro — Browser driver setup, login, and window management."""
import time
import os

from selenium.common.exceptions import (
    TimeoutException, NoSuchElementException, StaleElementReferenceException,
    WebDriverException, ElementClickInterceptedException,
    ElementNotInteractableException, JavascriptException,
)

from utils.logger import logger
from selenium import webdriver
from selenium.webdriver.chrome.service import Service


class BrowserSetupMixin:
    """Mixin: Browser driver setup, login, and window management."""

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
        if self.proxy_config and self.proxy_config.get("fingerprint_enabled"):
            user_agent = self.proxy_config.get("user_agent") or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36"
            options.add_argument(f"user-agent={user_agent}")
            resolution = self.proxy_config.get("resolution") or "1000,750"
            options.add_argument(f"--window-size={resolution}")
        else:
            if not start_minimized:
                options.add_argument("--window-size=1000,750")
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
        except Exception as exc:
            logger.debug("Native Chrome driver initialization failed; trying webdriver-manager: %s", exc)
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
            except Exception as exc:
                logger.debug("Could not inspect current browser URL: %s", exc)
                try:
                    self.driver.get("https://web.whatsapp.com")
                except Exception as nav_exc:
                    logger.debug("Could not navigate to WhatsApp Web: %s", nav_exc)

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
            except Exception as exc:
                logger.debug("Could not bring browser window to front: %s", exc)

    def minimize(self):
        """Minimizes the browser window."""
        if self.driver:
            try:
                self.driver.minimize_window()
            except Exception as exc:
                logger.debug("Could not minimize browser window: %s", exc)

    def is_logged_in(self):
        if not self.driver:
            return False
        if self._find_any(self.LOGGED_IN_LOCATORS) is not None:
            return True
        return self._find_any(self.SEARCH_BOX_LOCATORS) is not None or self._find_any(self.CHAT_INPUT_LOCATORS) is not None

