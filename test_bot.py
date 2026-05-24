import os
import sys
import time

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from automation.whatsapp_bot import WhatsAppBot

def log_event(level, message, detail=None):
    detail_str = f" | Detail: {detail}" if detail else ""
    print(f"[{level}] {message}{detail_str}")

def main():
    profile_dir = os.path.join(os.getcwd(), "data", "profiles", "Default")
    print(f"[TEST] Profile Directory: {profile_dir}")
    
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

    # Try sending a text message
    phone = "201030406057"
    print(f"\n[TEST] Sending a text message to: {phone}")
    result = bot.send_message(
        phone=phone,
        name="Islam",
        message_template="السلام عليكم يا إسلام، هذه رسالة تجريبية من الذكاء الاصطناعي لتأكيد استقرار البوت! 🚀🔥",
    )
    print(f"[TEST] Text message result: {result}")
    
    time.sleep(5)
    print("[TEST] Test completed. Closing browser.")
    bot.driver.quit()

if __name__ == "__main__":
    main()
