import os, sys, time
from selenium import webdriver
from selenium.webdriver.common.by import By

PHONE = "201030406057"
PROFILE_DIR = os.path.join(os.getcwd(), "data", "profiles", "Default")

def main():
    print(f"[MENU-DIAG] Profile: {PROFILE_DIR}")
    options = webdriver.ChromeOptions()
    options.add_argument(f"user-data-dir={PROFILE_DIR}")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--app=https://web.whatsapp.com")
    options.add_argument("--window-size=1200,900")
    
    driver = webdriver.Chrome(options=options)
    print("[MENU-DIAG] Opened Chrome. Waiting 15s for WhatsApp...")
    time.sleep(15)
    
    url = f"https://web.whatsapp.com/send?phone={PHONE}"
    print(f"[MENU-DIAG] Navigating to: {url}")
    driver.get(url)
    
    print("[MENU-DIAG] Waiting 15s for chat to load...")
    time.sleep(15)
    
    # Try finding the attach button (+)
    attach_btn = None
    btn_xpaths = [
        '//*[@id="main"]//button[@data-testid="plus-rounded" or .//span[@data-icon="plus-rounded"]]',
        '//*[@id="main"]//button[.//span[@data-icon="plus-rounded"]]',
        '//*[@id="main"]//div[@role="button" and .//span[@data-icon="plus-rounded"]]',
        '//*[@id="main"]//span[@data-icon="plus-rounded"]',
        '//*[@id="main"]//span[@data-icon="plus"]',
    ]
    for xpath in btn_xpaths:
        try:
            els = driver.find_elements(By.XPATH, xpath)
            for el in els:
                if el.is_displayed():
                    attach_btn = el
                    print(f"[MENU-DIAG] Found attach button via: {xpath}")
                    break
            if attach_btn:
                break
        except Exception:
            pass
            
    if not attach_btn:
        print("[MENU-DIAG] Could not find attach button. Dumping visible icons in #main:")
        try:
            spans = driver.find_elements(By.XPATH, '//*[@id="main"]//span[@data-icon]')
            for s in spans:
                print(f"  -> Icon: {s.get_attribute('data-icon')} displayed={s.is_displayed()}")
        except Exception as e:
            print(f"[MENU-DIAG] Error: {e}")
        driver.quit()
        return

    # Click the button
    try:
        driver.execute_script("arguments[0].click();", attach_btn)
        print("[MENU-DIAG] Clicked attach button. Waiting 3 seconds for dropdown menu...")
        time.sleep(3)
    except Exception as e:
        print(f"[MENU-DIAG] Click failed: {e}")
        driver.quit()
        return

    # Dump all elements inside the popup menu
    print("\n" + "=" * 50)
    print("ATTACH MENU POPUP ELEMENT DUMP")
    print("=" * 50)
    try:
        # Find all <li> or items with tabindex/roles that are visible
        items = driver.find_elements(By.XPATH, '//li | //*[@role="button"] | //*[@role="menuitem"] | //div[@tabindex="0"]')
        print(f"Total potential menu items found: {len(items)}")
        for idx, item in enumerate(items):
            try:
                if not item.is_displayed():
                    continue
                text = item.text.strip().replace("\n", " | ")
                tag = item.tag_name
                role = item.get_attribute("role") or "none"
                tab = item.get_attribute("tabindex") or "none"
                
                # Check for nested file input
                inputs = item.find_elements(By.XPATH, './/input[@type="file"]')
                has_file_input = len(inputs) > 0
                accept_attr = inputs[0].get_attribute("accept") if has_file_input else "none"
                
                # Check for nested icons
                icons = [s.get_attribute("data-icon") for s in item.find_elements(By.XPATH, './/span[@data-icon]')]
                
                print(f"[{idx}] Tag: <{tag}> role='{role}' tab='{tab}' text='{text}' icons={icons} hasFileInput={has_file_input} accept='{accept_attr}'")
            except Exception as item_err:
                pass
    except Exception as e:
        print(f"[MENU-DIAG] Error listing elements: {e}")

    # General search for all input[type=file] on the page
    print("\n" + "=" * 50)
    print("ALL INPUT[TYPE=FILE] ELEMENTS ON PAGE")
    print("=" * 50)
    try:
        inputs = driver.find_elements(By.XPATH, '//input[@type="file"]')
        for idx, inp in enumerate(inputs):
            accept = inp.get_attribute("accept") or "none"
            name = inp.get_attribute("name") or "none"
            inp_id = inp.get_attribute("id") or "none"
            parent = inp.find_element(By.XPATH, "..").tag_name
            print(f"[{idx}] name='{name}' id='{inp_id}' accept='{accept}' parent=<{parent}> displayed={inp.is_displayed()}")
    except Exception as e:
        print(f"[MENU-DIAG] Error checking file inputs: {e}")

    print("\nDone! Closing browser in 3 seconds.")
    time.sleep(3)
    driver.quit()

if __name__ == "__main__":
    main()
