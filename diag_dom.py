"""
Diagnostic script: Opens WhatsApp Web, navigates to a chat,
and dumps the full DOM structure of #main to help identify
the correct locators for the attach button.
"""
import os, sys, time, json

from selenium import webdriver
from selenium.webdriver.common.by import By

PHONE = "201030406057"
PROFILE_DIR = os.path.join(os.getcwd(), "data", "profiles", "Default")

def main():
    print(f"[DIAG] Profile dir: {PROFILE_DIR}")
    print(f"[DIAG] Phone: {PHONE}")

    options = webdriver.ChromeOptions()
    options.add_argument(f"user-data-dir={PROFILE_DIR}")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--app=https://web.whatsapp.com")
    options.add_argument("--disable-notifications")
    options.add_argument("--no-first-run")
    options.add_argument("--no-default-browser-check")
    options.add_argument("--disable-sync")
    options.add_argument("--disable-extensions")
    options.add_argument("--window-size=1000,750")
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    options.add_argument(f"user-agent={user_agent}")
    options.add_argument("--remote-allow-origins=*")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    driver = webdriver.Chrome(options=options)
    print("[DIAG] Chrome opened. Waiting for WhatsApp Web to load...")

    # Wait for login (check for side panel or chat input)
    for i in range(60):
        try:
            els = driver.find_elements(By.XPATH, '//div[@id="side"]')
            if els and els[0].is_displayed():
                print(f"[DIAG] WhatsApp Web loaded (logged in) after {i}s")
                break
        except:
            pass
        time.sleep(1)
    else:
        print("[DIAG] WARNING: WhatsApp Web did not load in 60s. Continuing anyway...")

    time.sleep(2)

    # Navigate to chat
    url = f"https://web.whatsapp.com/send?phone={PHONE}"
    print(f"[DIAG] Navigating to: {url}")
    driver.get(url)

    # Wait for chat to be ready
    print("[DIAG] Waiting for chat to load (either #main or any contenteditable)...")
    for i in range(40):
        try:
            mains = driver.find_elements(By.ID, "main")
            editables = driver.find_elements(By.XPATH, '//div[@contenteditable="true"]')
            if mains or editables:
                print(f"[DIAG] Found mains={len(mains)} or editables={len(editables)} after {i}s")
                break
        except Exception as e:
            pass
        time.sleep(1)
    
    # Extra wait for DOM to settle
    time.sleep(3)

    # ===== DUMP EVERYTHING =====
    print("\n" + "=" * 80)
    print("FULL DOM DIAGNOSTIC DUMP")
    print("=" * 80)

    # 1. Check if #main exists
    try:
        mains = driver.find_elements(By.ID, "main")
        print(f"\n[1] #main elements found: {len(mains)}")
        for m in mains:
            print(f"    displayed: {m.is_displayed()}, tag: {m.tag_name}")
    except Exception as e:
        print(f"[1] ERROR checking #main: {e}")

    # 2. Check footer
    try:
        footers = driver.find_elements(By.XPATH, '//*[@id="main"]//footer')
        print(f"\n[2] #main footer elements: {len(footers)}")
        for f in footers:
            print(f"    displayed: {f.is_displayed()}, innerHTML length: {len(f.get_attribute('innerHTML') or '')}")
    except Exception as e:
        print(f"[2] ERROR: {e}")

    # 3. All data-icon spans in #main
    try:
        icons = driver.find_elements(By.XPATH, '//*[@id="main"]//span[@data-icon]')
        print(f"\n[3] All span[data-icon] in #main: {len(icons)}")
        for el in icons:
            icon = el.get_attribute("data-icon")
            vis = el.is_displayed()
            parent_tag = ""
            try:
                parent = el.find_element(By.XPATH, "..")
                parent_tag = parent.tag_name
                parent_role = parent.get_attribute("role") or ""
                parent_aria = parent.get_attribute("aria-label") or ""
            except:
                parent_role = ""
                parent_aria = ""
            print(f"    icon='{icon}' visible={vis} parent={parent_tag} role='{parent_role}' aria='{parent_aria}'")
    except Exception as e:
        print(f"[3] ERROR: {e}")

    # 4. All buttons in #main
    try:
        btns = driver.find_elements(By.XPATH, '//*[@id="main"]//*[self::button or @role="button"]')
        print(f"\n[4] All buttons/[role=button] in #main: {len(btns)}")
        for b in btns:
            tag = b.tag_name
            aria = b.get_attribute("aria-label") or ""
            title = b.get_attribute("title") or ""
            vis = b.is_displayed()
            # Check for child data-icon
            child_icons = []
            try:
                for ci in b.find_elements(By.XPATH, './/span[@data-icon]'):
                    child_icons.append(ci.get_attribute("data-icon"))
            except:
                pass
            print(f"    <{tag}> aria='{aria}' title='{title}' visible={vis} child-icons={child_icons}")
    except Exception as e:
        print(f"[4] ERROR: {e}")

    # 5. All contenteditable divs (chat inputs and global ones)
    try:
        inputs = driver.find_elements(By.XPATH, '//div[@contenteditable="true"]')
        print(f"\n[5] contenteditable divs (GLOBAL): {len(inputs)}")
        for inp in inputs:
            role = inp.get_attribute("role") or ""
            tab = inp.get_attribute("data-tab") or ""
            vis = inp.is_displayed()
            cls = inp.get_attribute("class") or ""
            print(f"    tag=DIV class='{cls[:50]}' data-tab='{tab}' role='{role}' visible={vis}")
    except Exception as e:
        print(f"[5] ERROR: {e}")

    # 6. All divs with tabindex in footer area
    try:
        tabs = driver.find_elements(By.XPATH, '//*[@id="main"]//div[@tabindex]')
        print(f"\n[6] All div[tabindex] in #main: {len(tabs)}")
        for t in tabs:
            tabidx = t.get_attribute("tabindex")
            aria = t.get_attribute("aria-label") or ""
            title = t.get_attribute("title") or ""
            vis = t.is_displayed()
            child_icons = []
            try:
                for ci in t.find_elements(By.XPATH, './/span[@data-icon]'):
                    child_icons.append(ci.get_attribute("data-icon"))
            except:
                pass
            if child_icons or aria or title:
                print(f"    tabindex={tabidx} aria='{aria}' title='{title}' visible={vis} child-icons={child_icons}")
    except Exception as e:
        print(f"[6] ERROR: {e}")

    # 7. Full JS diagnostic
    try:
        js_result = driver.execute_script("""
        var result = {};
        var main = document.querySelector('#main');
        if (!main) return {error: 'NO #main'};
        
        // Check footer
        var footer = main.querySelector('footer');
        result.hasFooter = !!footer;
        result.footerDisplay = footer ? window.getComputedStyle(footer).display : 'N/A';
        
        // Get compose area - might not be in footer anymore
        var composeArea = main.querySelector('footer') || main.querySelector('[class*="compose"]') || main;
        
        // All clickable things near bottom
        var allSpans = main.querySelectorAll('span[data-icon]');
        result.allIcons = [];
        for (var i = 0; i < allSpans.length; i++) {
            var s = allSpans[i];
            var st = window.getComputedStyle(s);
            result.allIcons.push({
                icon: s.getAttribute('data-icon'),
                visible: st.display !== 'none' && st.visibility !== 'hidden',
                parentTag: s.parentElement ? s.parentElement.tagName : 'none',
                parentRole: s.parentElement ? (s.parentElement.getAttribute('role') || '') : '',
                rect: s.getBoundingClientRect()
            });
        }
        
        // Check if any element has "plus" or "attach" in any attribute
        var allEls = main.querySelectorAll('*');
        result.attachRelated = [];
        for (var j = 0; j < allEls.length; j++) {
            var el = allEls[j];
            var attrs = el.attributes;
            for (var k = 0; k < attrs.length; k++) {
                var val = (attrs[k].value || '').toLowerCase();
                if (val.indexOf('attach') >= 0 || val.indexOf('plus') >= 0 || val.indexOf('clip') >= 0 || val.indexOf('إرفاق') >= 0) {
                    result.attachRelated.push({
                        tag: el.tagName,
                        attr: attrs[k].name,
                        value: attrs[k].value,
                        visible: window.getComputedStyle(el).display !== 'none'
                    });
                }
            }
        }
        
        return result;
        """)
        print(f"\n[7] JS Diagnostic:")
        print(f"    hasFooter: {js_result.get('hasFooter')}")
        print(f"    footerDisplay: {js_result.get('footerDisplay')}")
        print(f"\n    All icons ({len(js_result.get('allIcons', []))}):")
        for ic in js_result.get('allIcons', []):
            print(f"      icon='{ic['icon']}' visible={ic['visible']} parent={ic['parentTag']} role='{ic['parentRole']}'")
        print(f"\n    Attach-related elements ({len(js_result.get('attachRelated', []))}):")
        for ar in js_result.get('attachRelated', []):
            print(f"      <{ar['tag']}> {ar['attr']}='{ar['value']}' visible={ar['visible']}")
    except Exception as e:
        print(f"[7] JS ERROR: {e}")

    print("\n" + "=" * 80)
    print("[DIAG] Done! Closing browser in 5 seconds...")
    time.sleep(5)
    driver.quit()

if __name__ == "__main__":
    main()
