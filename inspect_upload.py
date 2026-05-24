import os, sys, time
from selenium import webdriver
from selenium.webdriver.common.by import By

PHONE = "201030406057"
PROFILE_DIR = os.path.join(os.getcwd(), "data", "profiles", "Default")

def main():
    print(f"[UPLOAD-DIAG] Profile: {PROFILE_DIR}")
    options = webdriver.ChromeOptions()
    options.add_argument(f"user-data-dir={PROFILE_DIR}")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--app=https://web.whatsapp.com")
    options.add_argument("--window-size=1200,900")
    
    driver = webdriver.Chrome(options=options)
    print("[UPLOAD-DIAG] Opened Chrome. Waiting 15s for WhatsApp...")
    time.sleep(15)
    
    url = f"https://web.whatsapp.com/send?phone={PHONE}"
    print(f"[UPLOAD-DIAG] Navigating to: {url}")
    driver.get(url)
    
    print("[UPLOAD-DIAG] Waiting 15s for chat to load...")
    time.sleep(15)
    
    # Click the attach button (+) using JS
    attach_btn = None
    btn_xpaths = [
        '//*[@id="main"]//button[@data-testid="plus-rounded" or .//span[@data-icon="plus-rounded"]]',
        '//*[@id="main"]//button[.//span[@data-icon="plus-rounded"]]',
        '//*[@id="main"]//div[@role="button" and .//span[@data-icon="plus-rounded"]]',
    ]
    for xpath in btn_xpaths:
        try:
            els = driver.find_elements(By.XPATH, xpath)
            for el in els:
                if el.is_displayed():
                    attach_btn = el
                    break
            if attach_btn:
                break
        except Exception:
            pass
            
    if not attach_btn:
        print("[UPLOAD-DIAG] Could not find attach button. Exiting.")
        driver.quit()
        return

    # Snapshot existing inputs BEFORE clicking any option
    print("\n--- Inputs BEFORE clicking option ---")
    before_inputs = driver.find_elements(By.XPATH, '//input[@type="file"]')
    for idx, inp in enumerate(before_inputs):
        print(f"[{idx}] accept='{inp.get_attribute('accept')}' id='{inp.get_attribute('id')}' name='{inp.get_attribute('name')}' displayed={inp.is_displayed()}")

    # Click the attach button
    driver.execute_script("arguments[0].click();", attach_btn)
    time.sleep(2)

    # Click "الصور ومقاطع الفيديو" button in attach menu
    labels = ["الصور ومقاطع الفيديو", "الصور والفيديو", "صور وفيديو", "معرض", "gallery", "Photos & videos", "Photos and videos", "Photos & Videos"]
    row_clicked = False
    for label in labels:
        fragments = [
            f"//button[.//*[contains(normalize-space(.),'{label}')] or contains(normalize-space(.),'{label}')]",
            f"//*[@role='menuitem'][.//*[contains(normalize-space(.),'{label}')] or contains(normalize-space(.),'{label}')]",
            f"//li[.//*[contains(normalize-space(.),'{label}')]]",
        ]
        for xpath in fragments:
            try:
                els = driver.find_elements(By.XPATH, xpath)
                for el in els:
                    if el.is_displayed():
                        print(f"[UPLOAD-DIAG] Found and clicking option '{label}' via: {xpath}")
                        driver.execute_script("arguments[0].click();", el)
                        row_clicked = True
                        break
                if row_clicked:
                    break
            except Exception:
                pass
        if row_clicked:
            break

    if not row_clicked:
        print("[UPLOAD-DIAG] Could not find or click the 'Photos & videos' option!")
    else:
        print("[UPLOAD-DIAG] Clicked 'Photos & videos' option. Waiting 4 seconds for DOM changes...")
        time.sleep(4)

    # Snapshot existing inputs AFTER clicking option
    print("\n--- Inputs AFTER clicking option ---")
    after_inputs = driver.find_elements(By.XPATH, '//input[@type="file"]')
    for idx, inp in enumerate(after_inputs):
        accept_attr = inp.get_attribute('accept') or "none"
        name_attr = inp.get_attribute('name') or "none"
        id_attr = inp.get_attribute('id') or "none"
        print(f"[{idx}] accept='{accept_attr}' id='{id_attr}' name='{name_attr}' displayed={inp.is_displayed()}")

    print("\nDone! Closing browser in 3 seconds.")
    time.sleep(3)
    driver.quit()

if __name__ == "__main__":
    main()
