import time
import requests
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# ===== CONFIG =====
PHONE_NUMBER = ""  # recipient's phone number in international format
AUDIO_URL = "https://raw.githubusercon"
AUDIO_PATH = r"/Users/harshitjajoria/Developer/videos/automatic_calls/audio.mp3"
PROFILE_DIR = os.path.expanduser("~/.whatsapp_profile")

# Create profile directory if it doesn't exist
os.makedirs(PROFILE_DIR, exist_ok=True)

# ===== DOWNLOAD AUDIO IF NEEDED =====
def download_audio(url, file_path):
    """Download audio from GitHub URL"""
    if not os.path.exists(file_path):
        print(f"⏳ Downloading audio from {url}...")
        response = requests.get(url)
        with open(file_path, 'wb') as f:
            f.write(response.content)
        print(f"✅ Audio downloaded to {file_path}")
    else:
        print(f"✅ Audio file already exists: {file_path}")

download_audio(AUDIO_URL, AUDIO_PATH)

# ===== SETUP =====
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
options.add_argument(f"--user-data-dir={PROFILE_DIR}")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option("useAutomationExtension", False)

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=options
)

# Check if first time login (no session)
is_first_login = not os.path.exists(os.path.join(PROFILE_DIR, "Default", "Cache"))

if is_first_login:
    print("\n" + "="*60)
    print("⚠️  FIRST TIME LOGIN DETECTED")
    print("="*60)
    print("You need to scan the QR code with your phone to authenticate.")
    print("1. WhatsApp will open in the browser")
    print("2. Scan the QR code with your phone's WhatsApp")
    print("3. The script will continue automatically after login")
    print("="*60 + "\n")

wait = WebDriverWait(driver, 40 if not is_first_login else 120)

# ===== OPEN CHAT =====
try:
    driver.get(f"https://web.whatsapp.com/send?phone={PHONE_NUMBER}")

    print("⏳ Waiting for chat...")
    # Wait for footer to indicate full load
    wait.until(EC.presence_of_element_located((By.XPATH, '//footer')))
    print("✅ Footer loaded")
    
    # Extra wait for UI to fully render
    time.sleep(10)
    
    print("✅ Chat loaded")

    # ===== DEBUG: Save screenshot to see current state =====
    driver.save_screenshot("whatsapp_state.png")
    print("📸 Screenshot saved as whatsapp_state.png for debugging")

    # ===== UPLOAD FILE DIRECTLY TO MESSAGE INPUT =====
    # Try to find and interact with file input
    file_inputs = driver.find_elements(By.XPATH, '//input[@type="file"]')
    print(f"Found {len(file_inputs)} file input(s)")
    
    if file_inputs:
        file_input = file_inputs[0]
        print(f"Using file input...")
        file_input.send_keys(AUDIO_PATH)
        print(f"📎 File sent to input: {AUDIO_PATH}")
        time.sleep(3)
        
        print("📎 File selected, waiting for preview...")
        time.sleep(15)  # Significantly increased wait time for WhatsApp to process file
        
        # Save screenshot to see the current state
        driver.save_screenshot("before_send_button.png")
        print("📸 Screenshot saved as before_send_button.png")
        
        # 🔥 IMPORTANT: wait for preview/send screen - try multiple XPath options
        send_btn = None
        
        # Try first XPath
        try:
            send_btn = wait.until(
                EC.element_to_be_clickable((By.XPATH, '//span[@data-icon="wds-ic-send-filled"]'))
            )
            print("✅ Send button found (method 1 - new selector)")
        except TimeoutException:
            print("⚠️ Method 1 failed, trying method 2...")
            try:
                send_btn = wait.until(
                    EC.element_to_be_clickable((By.XPATH, '//span[@data-icon="send"]'))
                )
                print("✅ Send button found (method 2)")
            except TimeoutException:
                print("⚠️ Method 2 failed, trying method 3...")
                try:
                    send_btn = wait.until(
                        EC.element_to_be_clickable((By.XPATH, '//button[@aria-label="Send"]'))
                    )
                    print("✅ Send button found (method 3)")
                except TimeoutException:
                    print("⚠️ Method 3 failed, trying method 4...")
                    try:
                        send_btn = wait.until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[aria-label="Send"]'))
                        )
                        print("✅ Send button found (method 4)")
                    except TimeoutException:
                        print("⚠️ Method 4 failed, trying method 5...")
                        try:
                            send_btn = driver.find_element(By.CSS_SELECTOR, '[data-testid="send"]')
                            wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-testid="send"]')))
                            print("✅ Send button found (method 5)")
                        except:
                            print("❌ Could not find send button!")
                            driver.save_screenshot("send_button_error.png")
                            print("📸 Screenshot saved as send_button_error.png")
                            driver.quit()
                            exit(1)

        time.sleep(1)

        # ===== CLICK SEND =====
        if send_btn:
            try:
                send_btn.click()
                print("✅ Send button clicked!")
            except Exception as e:
                print(f"❌ Failed to click send button: {e}")
                # Try JavaScript click as fallback
                driver.execute_script("arguments[0].click();", send_btn)
                print("✅ Clicked using JavaScript!")

        time.sleep(5)
    else:
        print("No file input found, trying attach button method...")
        # ===== CLICK ATTACH =====
        attach_btn = None
        try:
            attach_btn = wait.until(
                EC.element_to_be_clickable((By.XPATH, '//div[@title="Attach"]'))
            )
            print("📎 Clicked attach button (method 1)")
            attach_btn.click()
        except TimeoutException:
            print("⚠️ Method 1 failed, trying method 2...")
            try:
                attach_btn = wait.until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-testid="attach"]'))
                )
                print("📎 Clicked attach button (method 2)")
                attach_btn.click()
            except TimeoutException:
                print("❌ Could not find attach button!")
                driver.save_screenshot("attach_button_error.png")
                print("📸 Screenshot saved as attach_button_error.png")
                driver.quit()
                exit(1)

        print("📎 File selected, waiting for preview...")
        time.sleep(5)  # Increased wait time for file to process
    
except TimeoutException as e:
    print(f"❌ Timeout: {e}")
    driver.save_screenshot("error_screenshot.png")
    print("📸 Screenshot saved as error_screenshot.png")
except Exception as e:
    print(f"❌ Error: {e}")
    driver.save_screenshot("error_screenshot.png")
    print("📸 Screenshot saved as error_screenshot.png")
finally:
    driver.quit()
