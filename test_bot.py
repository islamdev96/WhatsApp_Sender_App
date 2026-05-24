import os
import sys
import time

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from automation.whatsapp_bot import WhatsAppBot

def log_event(level, message, detail=None):
    detail_str = f" | Detail: {detail}" if detail else ""
    print(f"[{level}] {message}{detail_str}")

def create_test_image(filename="test_image.png"):
    try:
        from PIL import Image, ImageDraw
        # Create a simple harmonious gradient or solid color image
        img = Image.new("RGB", (400, 400), color=(30, 144, 255)) # Sleek blue
        d = ImageDraw.Draw(img)
        d.text((20, 20), "Antigravity WhatsApp Bot Test Image", fill="white")
        img.save(filename)
        return os.path.abspath(filename)
    except Exception as e:
        print(f"[TEST] Failed to create test image via Pillow: {e}. Writing raw bytes fallback.")
        # Minimal solid 1x1 PNG fallback
        png_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\rIDATx\x9cc`\x00\x01\x00\x00\x0c\x00\x01\x1c\xed\xee\x13\x00\x00\x00\x00IEND\xaeB`\x82'
        with open(filename, "wb") as f:
            f.write(png_data)
        return os.path.abspath(filename)

def main():
    profile_dir = os.path.join(os.getcwd(), "data", "profiles", "Default")
    print(f"[TEST] Profile Directory: {profile_dir}")
    
    # Generate test image
    img_path = create_test_image()
    print(f"[TEST] Created test image at: {img_path}")
    
    # Initialize bot
    bot = WhatsAppBot(user_data_dir=profile_dir, on_event=log_event)
    
    print("[TEST] Opening WhatsApp...")
    bot.open_whatsapp()
    
    print("[TEST] Waiting for login status...")
    status = bot.wait_for_login(timeout=60)
    print(f"[TEST] Login status: {status}")
    
    if status != "SUCCESS":
        print("[TEST] Failed to log in or closed. Exiting.")
        bot.driver.quit()
        return

    phone = "201030406057"
    
    # =========================================================================
    # TEST CASE 1: Send Text ONLY
    # =========================================================================
    print(f"\n[TEST CASE 1] Sending a text message to: {phone}")
    res1 = bot.send_message(
        phone=phone,
        name="Islam",
        message_template="السلام عليكم يا إسلام، هذه رسالة تجريبية (نص فقط) من البوت! 🚀",
    )
    print(f"[TEST CASE 1] Result: {res1}")
    time.sleep(4)

    # =========================================================================
    # TEST CASE 2: Send Image ONLY
    # =========================================================================
    print(f"\n[TEST CASE 2] Sending an image (no caption) to: {phone}")
    res2 = bot.send_message(
        phone=phone,
        name="Islam",
        message_template="",
        attachments=[{"path": img_path, "type": "image"}]
    )
    print(f"[TEST CASE 2] Result: {res2}")
    time.sleep(4)

    # =========================================================================
    # TEST CASE 3: Send BOTH (Image + Caption)
    # =========================================================================
    print(f"\n[TEST CASE 3] Sending both (Image + Caption) to: {phone}")
    res3 = bot.send_message(
        phone=phone,
        name="Islam",
        message_template="هذه صورة ممتازة تم إرسالها مع نص توضيحي في نفس الوقت! 🎨🔥",
        attachments=[{"path": img_path, "type": "image"}],
        send_text_with_image=True
    )
    print(f"[TEST CASE 3] Result: {res3}")
    
    time.sleep(5)
    print("[TEST] All tests completed. Closing browser.")
    bot.driver.quit()

if __name__ == "__main__":
    main()
