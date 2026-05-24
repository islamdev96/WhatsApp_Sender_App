import os, time
from selenium import webdriver
from selenium.webdriver.common.by import By

PROFILE_DIR = os.path.join(os.getcwd(), "data", "profiles", "Default")
PHONE = "201030406057"
IMAGE_PATH = os.path.join(os.getcwd(), "test_image.png")

if not os.path.isfile(IMAGE_PATH):
    print(f"Creating dummy image at {IMAGE_PATH}")
    with open(IMAGE_PATH, "wb") as f:
        f.write(
            b"\x89PNG\r\n\x1a\n" +
            b"\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde" +
            b"\x00\x00\x00\nIDATx\x9cc```\x00\x00\x00\x02\x00\x01\xe2!\xbc\x33" +
            b"\x00\x00\x00\x00IEND\xaeB`\x82"
        )

options = webdriver.ChromeOptions()
options.add_argument(f"user-data-dir={PROFILE_DIR}")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--app=https://web.whatsapp.com")
options.add_argument("--window-size=1200,900")
options.add_argument("--remote-allow-origins=*")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option("useAutomationExtension", False)

print(f"Using profile: {PROFILE_DIR}")
print(f"Opening chat for phone: {PHONE}")

driver = webdriver.Chrome(options=options)
try:
    driver.get(f"https://web.whatsapp.com/send?phone={PHONE}")
    for i in range(60):
        try:
            main = driver.find_element(By.ID, "main")
            if main.is_displayed():
                print(f"Chat loaded after {i}s")
                break
        except Exception:
            pass
        time.sleep(1)
    else:
        print("Chat not loaded after 60s")

    time.sleep(2)
    # try attach button
    attach_xpaths = [
        '//*[@id="main"]//button[@data-testid="clip"]',
        '//*[@id="main"]//button[@data-testid="plus-rounded"]',
        '//*[@id="main"]//button[.//span[@data-icon="clip"]]',
        '//*[@id="main"]//div[@role="button" and .//span[@data-icon="clip"]]',
        '//*[@id="main"]//button[.//span[contains(@data-icon, "clip")]]',
    ]
    attach = None
    for xp in attach_xpaths:
        els = driver.find_elements(By.XPATH, xp)
        for el in els:
            if el.is_displayed():
                attach = el
                break
        if attach:
            break
    print(f"Attach button found: {attach is not None}")
    if attach:
        driver.execute_script("arguments[0].click();", attach)
    else:
        print("No attach button found")
        raise SystemExit(1)

    time.sleep(2)
    # click photos/videos option
    labels = ["الصور ومقاطع الفيديو", "الصور والفيديو", "صور وفيديو", "معرض", "gallery", "Photos & videos", "Photos and videos", "Photos & Videos"]
    clicked = False
    for label in labels:
        xpath = f"//button[.//*[contains(normalize-space(.),'{label}')] or contains(normalize-space(.),'{label}') or .='{label}']"
        els = driver.find_elements(By.XPATH, xpath)
        for el in els:
            if el.is_displayed():
                print(f"Clicking option label: {label}")
                driver.execute_script("arguments[0].click();", el)
                clicked = True
                break
        if clicked:
            break
    if not clicked:
        print("Could not click photos/videos option")
        raise SystemExit(1)
    time.sleep(3)

    inp = None
    for i in range(20):
        inputs = driver.find_elements(By.XPATH, '//input[@type="file"]')
        for el in inputs:
            if el.is_displayed():
                inp = el
                break
        if inp:
            break
        time.sleep(1)
    print(f"File input found: {inp is not None}")
    if not inp:
        raise SystemExit(1)
    inp.send_keys(IMAGE_PATH)
    print("Sent file path to input")

    for i in range(30):
        preview = driver.execute_script("return document.querySelector('[data-testid=\\\"media-viewer\\\"]') || document.querySelector('[role=\\\"dialog\\\"]');")
        if preview:
            print(f"Preview found after {i}s")
            break
        time.sleep(1)
    else:
        print("Preview not found")
        raise SystemExit(1)

    print("Collecting candidate buttons...")
    info = driver.execute_script('''
        var result = {previewExists:false, previewTag:null, buttons:[], spans:[], globalSendCandidates:[]};
        var preview = document.querySelector('[data-testid="media-viewer"]') || document.querySelector('[role="dialog"]');
        if(preview){ result.previewExists=true; result.previewTag=preview.tagName; }
        var buttons = preview ? preview.querySelectorAll('button, [role="button"]') : [];
        for(var i=0;i<buttons.length;i++){
            var b=buttons[i];
            var txt=(b.getAttribute('aria-label')||b.textContent||'').trim();
            var icons=[];
            b.querySelectorAll('span[data-icon]').forEach(function(s){ icons.push(s.getAttribute('data-icon')); });
            var vis = window.getComputedStyle(b).display!=='none' && window.getComputedStyle(b).visibility!=='hidden' && b.offsetParent!==null;
            result.buttons.push({tag:b.tagName, aria:b.getAttribute('aria-label')||'', text:txt, icons:icons, visible:vis, outer:b.outerHTML.slice(0,200)});
        }
        var spans = preview ? preview.querySelectorAll('span[data-icon]') : [];
        for(var i=0;i<spans.length;i++){
            var s=spans[i];
            var vis = window.getComputedStyle(s).display!=='none' && window.getComputedStyle(s).visibility!=='hidden' && s.offsetParent!==null;
            result.spans.push({icon:s.getAttribute('data-icon'), visible:vis, outer:s.outerHTML.slice(0,200)});
        }
        var all = document.querySelectorAll('[data-icon*="send"], [aria-label*="Send"], [aria-label*="إرسال"], button, [role="button"]');
        for(var i=0;i<all.length;i++){
            var a=all[i];
            var txt=(a.getAttribute('aria-label')||a.textContent||'').trim();
            var icon = a.getAttribute('data-icon')||'';
            var vis = window.getComputedStyle(a).display!=='none' && window.getComputedStyle(a).visibility!=='hidden' && a.offsetParent!==null;
            if(txt.toLowerCase().includes('send')||txt.includes('إرسال')||icon.includes('send')){
                result.globalSendCandidates.push({tag:a.tagName, aria:a.getAttribute('aria-label')||'', text:txt, icon:icon, visible:vis, outer:a.outerHTML.slice(0,200)});
            }
        }
        return result;
    ''')
    print("Preview exists:", info['previewExists'])
    print("Preview tag:", info['previewTag'])
    print("Buttons:")
    for b in info['buttons']:
        print(f"  {b}")
    print("Spans:")
    for s in info['spans']:
        print(f"  {s}")
    print("Global send candidates:")
    for c in info['globalSendCandidates']:
        print(f"  {c}")
    time.sleep(5)
finally:
    print("Closing browser")
    driver.quit()
