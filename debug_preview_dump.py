import os, time
from selenium import webdriver
from selenium.webdriver.common.by import By

PHONE = "201030406057"
PROFILE_DIR = os.path.join(os.getcwd(), "data", "profiles", "Default")
TEST_IMG = os.path.join(os.getcwd(), "test_image.png")

options = webdriver.ChromeOptions()
options.add_argument(f"user-data-dir={PROFILE_DIR}")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--app=https://web.whatsapp.com")
options.add_argument("--window-size=1200,900")
options.add_argument("--remote-allow-origins=*")

print(f"[DEBUG] Profile: {PROFILE_DIR}")
driver = webdriver.Chrome(options=options)
print("[DEBUG] Chrome opened. Waiting 8s for WhatsApp...")
time.sleep(8)
url = f"https://web.whatsapp.com/send?phone={PHONE}"
print(f"[DEBUG] Navigating to: {url}")
driver.get(url)
print("[DEBUG] Waiting 6s for chat to load...")
time.sleep(6)

# Click attach button via JS fallback
print("[DEBUG] Attempting to find attach button via JS")
attach = driver.execute_script("""
var container = document.querySelector('#main');
if (!container) return null;
function visible(el){var s = window.getComputedStyle(el); return s.display!='none' && s.visibility!='hidden' && el.offsetParent!==null}
var icons = ['plus-rounded','plus','attach-menu-plus','clip','clip-light'];
for(var i=0;i<icons.length;i++){var spans=container.querySelectorAll('span[data-icon="'+icons[i]+'"]'); for(var j=0;j<spans.length;j++){ if(visible(spans[j])){ var c = spans[j].closest('[role="button"]')||spans[j].closest('button')||spans[j].parentElement||spans[j]; return c; }}}
var partial = container.querySelectorAll('span[data-icon*="attach"], span[data-icon*="clip"]'); for(var k=0;k<partial.length;k++){ if(visible(partial[k])) return partial[k].closest('[role="button"]')||partial[k]; }
var labeled = container.querySelectorAll('[aria-label="Attach"],[aria-label="إرفاق"],[title*="Attach"],[title*="إرفاق"]'); for(var m=0;m<labeled.length;m++){ if(visible(labeled[m])) return labeled[m]; }
return null;
""")

if not attach:
    print('[DEBUG] Attach button not found via JS, aborting')
    driver.quit()
    raise SystemExit(1)

print('[DEBUG] Clicking attach')
driver.execute_script('arguments[0].click();', attach)
print('[DEBUG] Clicked attach, waiting 2s')
time.sleep(2)

# Try click photos/videos option
labels = ["الصور ومقاطع الفيديو","الصور والفيديو","صور وفيديو","معرض","gallery","Photos & videos","Photos and videos","Photos & Videos"]
clicked = False
for label in labels:
    fragments = [
        f"//button[.//*[contains(normalize-space(.),'{label}')] or contains(normalize-space(.),'{label}') ]",
        f"//*[@role='menuitem'][.//*[contains(normalize-space(.),'{label}')] or contains(normalize-space(.),'{label}') ]",
        f"//li[.//*[contains(normalize-space(.),'{label}')]]",
    ]
    for xp in fragments:
        try:
            els = driver.find_elements(By.XPATH, xp)
            for el in els:
                if el.is_displayed():
                    print(f"[DEBUG] Clicking menu option via: {xp}")
                    driver.execute_script('arguments[0].click();', el)
                    clicked = True
                    break
            if clicked: break
        except Exception:
            pass
    if clicked: break

if not clicked:
    print('[DEBUG] Could not click Photos & videos option; continuing to snapshot inputs')
else:
    print('[DEBUG] Clicked Photos option, waiting 3s')
    time.sleep(3)

# List input[type=file] elements
print('\n[DEBUG] Inputs on page:')
inputs = driver.find_elements(By.XPATH, '//input[@type="file"]')
for i, inp in enumerate(inputs):
    try:
        print(f"[{i}] id={inp.get_attribute('id')} name={inp.get_attribute('name')} accept={inp.get_attribute('accept')} displayed={inp.is_displayed()}")
    except Exception:
        pass

# If there's an input visible, inject file
visible_inputs = [inp for inp in inputs if inp.is_displayed()]
if visible_inputs:
    print('[DEBUG] Found visible file input, setting file path')
    try:
        visible_inputs[0].send_keys(TEST_IMG)
        print('[DEBUG] Sent file to input, waiting 2s for preview')
        time.sleep(2)
    except Exception as e:
        print(f'[DEBUG] Failed to send file: {e}')
else:
    print('[DEBUG] No visible file inputs found; attempting to find any input and set value via JS')
    if inputs:
        try:
            el = inputs[0]
            driver.execute_script("arguments[0].style.display='block';", el)
            el.send_keys(TEST_IMG)
            time.sleep(2)
        except Exception as e:
            print('[DEBUG] JS fallback failed:', e)

print('[DEBUG] Now dumping MEDIA PREVIEW and dialog elements')
js = driver.execute_script("""
var res = {previews:[],buttons:[],spans:[],texts:[]};
var preview = document.querySelector('[data-testid="media-viewer"]') || document.querySelector('[role="dialog"]');
if(preview){
    var btns = preview.querySelectorAll('button, [role="button"]');
    btns.forEach(b=>{res.buttons.push({tag:b.tagName, aria:b.getAttribute('aria-label')||'', text:b.textContent.trim().slice(0,60), icons:Array.from(b.querySelectorAll('span[data-icon]')).map(s=>s.getAttribute('data-icon'))});});
    var spans = preview.querySelectorAll('span[data-icon]');
    spans.forEach(s=>{res.spans.push({icon:s.getAttribute('data-icon'), parent:s.parentElement? s.parentElement.tagName:'', visible: window.getComputedStyle(s).display!='none'});});
    var texts=[]; preview.querySelectorAll('*').forEach(el=>{ if(el.textContent && el.textContent.trim().length>0) texts.push(el.tagName+':'+el.textContent.trim().slice(0,60)); });
    res.texts = texts.slice(0,40);
    return res;
}
return res;
""")

print('[DEBUG] JS dump result:')
print(js)

print('\nDone. Waiting 5s then closing.')
time.sleep(5)
driver.quit()
