"""
Check if Chartink requires clicking a button to show results
"""
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import os

# Setup Chrome
driver_path = ChromeDriverManager().install()
if not driver_path.endswith('.exe') and os.name == 'nt':
    driver_dir = os.path.dirname(driver_path)
    driver_path = os.path.join(driver_dir, 'chromedriver.exe')

chrome_options = Options()
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=1920,1080")
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")

service = Service(driver_path)
driver = webdriver.Chrome(service=service, options=chrome_options)

url = "https://chartink.com/screener/within-2-of-52-week-highs-chartitude"
print(f"Loading: {url}\n")
driver.get(url)

print("Waiting 5 seconds...")
time.sleep(5)

# Look for buttons
buttons = driver.find_elements(By.TAG_NAME, "button")
print(f"Found {len(buttons)} buttons\n")

for i, button in enumerate(buttons[:10], 1):  # Check first 10
    text = button.text.strip()
    onclick = button.get_attribute('onclick') or ''
    classes = button.get_attribute('class') or ''

    if text or 'run' in onclick.lower() or 'search' in onclick.lower():
        print(f"Button {i}:")
        print(f"  Text: '{text}'")
        print(f"  Classes: {classes[:80]}")
        if onclick:
            print(f"  onclick: {onclick[:80]}")
        print()

# Check for specific text like "Run", "Search", "Show Results"
page_text = driver.find_element(By.TAG_NAME, "body").text
if "run" in page_text.lower() or "search" in page_text.lower():
    print("Page contains 'run' or 'search' text")

# Try clicking a button if it looks like a Run button
try:
    # Common button texts for running screeners
    for button_text in ["Run", "Search", "Show Results", "Scan", "Get Results"]:
        try:
            button = driver.find_element(By.XPATH, f"//button[contains(text(), '{button_text}')]")
            print(f"\nFound '{button_text}' button! Clicking...")
            button.click()
            time.sleep(5)  # Wait for results

            # Check if results appeared
            page_text_after = driver.find_element(By.TAG_NAME, "body").text
            if "SALSTEEL" in page_text_after or "INOXINDIA" in page_text_after:
                print(f"SUCCESS! Results appeared after clicking '{button_text}'")
            break
        except:
            continue
except Exception as e:
    print(f"No clickable button found: {e}")

driver.quit()
