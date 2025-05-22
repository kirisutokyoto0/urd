import os
import time
import json
from datetime import datetime
from PIL import ImageGrab
import pytesseract
import pygetwindow as gw

# Point pytesseract to your Tesseract executable
pytesseract.pytesseract.tesseract_cmd = os.path.join(os.getcwd(), "Tesseract-OCR", "tesseract.exe")

def load_blacklist(json_path):
    with open(json_path, 'r') as file:
        data = json.load(file)
    apps = data.get("apps", [])
    websites = data.get("websites", [])
    return apps + websites

# Load blacklist once at start
FORBIDDEN_SITES = load_blacklist("blacklist.json")

MAX_SUSPICIOUS = 30
suspicious_count = 0

def contains_forbidden(text):
    text_lower = text.lower()
    return any(keyword.lower() in text_lower for keyword in FORBIDDEN_SITES)

def capture_and_check():
    global suspicious_count

    active_window = gw.getActiveWindow()
    bbox = (active_window.left, active_window.top, active_window.right, active_window.bottom) if active_window else None

    screenshot = ImageGrab.grab(bbox)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"screenshots/screen_{timestamp}.png"
    screenshot.save(filename)

    extracted_text = pytesseract.image_to_string(screenshot)

    if contains_forbidden(extracted_text):
        suspicious_count += 1
        print(f"⚠️ Forbidden content detected! Screenshot saved at {timestamp} (Count: {suspicious_count})")
        if suspicious_count >= MAX_SUSPICIOUS:
            print("🚩 Cheating flagged! Maximum suspicious screenshots reached.")
            return False  # stop monitoring
    else:
        os.remove(filename)
        print(f"Clean screenshot at {timestamp} deleted.")
    return True  # continue monitoring

if __name__ == "__main__":
    os.makedirs("screenshots", exist_ok=True)
    print("Starting exam monitoring...")

    try:
        while True:
            if not capture_and_check():
                break
            time.sleep(3)  # Adjust this interval as you see fit
    except KeyboardInterrupt:
        print("Exam monitoring stopped.")
