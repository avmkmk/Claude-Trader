"""
Detailed inspection of Next button to understand why it's not clicking
"""
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import os

driver_path = ChromeDriverManager().install()
if not driver_path.endswith('.exe') and os.name == 'nt':
    driver_dir = os.path.dirname(driver_path)
    driver_path = os.path.join(driver_dir, 'chromedriver.exe')

chrome_options = Options()
# NOT headless so we can see what's happening
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=1920,1080")
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")

service = Service(driver_path)
driver = webdriver.Chrome(service=service, options=chrome_options)

url = "https://chartink.com/screener/stage-2-trend-template"
print(f"Loading: {url}")
driver.get(url)

print("Waiting 15 seconds for page to fully load...")
time.sleep(15)

print("\n" + "="*60)
print("PAGINATION STRUCTURE INSPECTION")
print("="*60)

# Find all buttons
buttons = driver.find_elements(By.TAG_NAME, "button")
print(f"\nFound {len(buttons)} buttons total")

# Find buttons with text containing 'next', '>', or pagination-related
next_related = []
for i, btn in enumerate(buttons):
    text = btn.text.strip().lower()
    aria_label = (btn.get_attribute('aria-label') or '').lower()
    classes = btn.get_attribute('class') or ''

    if 'next' in text or 'next' in aria_label or '>' in btn.text or 'nav' in classes.lower() or 'pag' in classes.lower():
        next_related.append(btn)
        print(f"\nButton {i+1}:")
        print(f"  Text: '{btn.text[:50]}'")
        print(f"  Aria-label: '{btn.get_attribute('aria-label')}'")
        print(f"  Classes: {classes[:80]}")
        print(f"  Disabled: {btn.get_attribute('disabled')}")
        print(f"  Aria-disabled: {btn.get_attribute('aria-disabled')}")
        print(f"  Is displayed: {btn.is_displayed()}")
        print(f"  Is enabled: {btn.is_enabled()}")

# Find all links
links = driver.find_elements(By.TAG_NAME, "a")
next_links = []
for link in links:
    text = link.text.strip().lower()
    if 'next' in text or link.text.strip() == '>':
        next_links.append(link)
        print(f"\nLink:")
        print(f"  Text: '{link.text[:50]}'")
        print(f"  Href: {link.get_attribute('href')}")
        print(f"  Classes: {link.get_attribute('class')[:80]}")

# Try to find pagination container
print("\n" + "="*60)
print("LOOKING FOR PAGINATION CONTAINER")
print("="*60)

# Common pagination container patterns
pagination_selectors = [
    ("nav", By.TAG_NAME, "nav"),
    ("div with pagination", By.CSS_SELECTOR, "div[class*='pagination']"),
    ("div with nav", By.CSS_SELECTOR, "div[class*='nav']"),
    ("ul with pagination", By.CSS_SELECTOR, "ul[class*='pagination']"),
]

for name, by_type, selector in pagination_selectors:
    try:
        elements = driver.find_elements(by_type, selector)
        if elements:
            print(f"\nFound {len(elements)} x '{name}'")
            for elem in elements[:2]:
                print(f"  HTML snippet: {elem.get_attribute('outerHTML')[:200]}")
                print(f"  Text: {elem.text[:100]}")
    except:
        pass

# Check if there's a page info text
print("\n" + "="*60)
print("PAGE INFO TEXT")
print("="*60)

page_text = driver.find_element(By.TAG_NAME, "body").text
import re
patterns = [
    r'Page \d+ of \d+',
    r'\d+-\d+ of \d+',
    r'Showing \d+ to \d+ of \d+',
    r'\d+ results?',
    r'\d+ stocks?',
]

for pattern in patterns:
    matches = re.findall(pattern, page_text, re.IGNORECASE)
    if matches:
        print(f"Found: {matches}")

# Take screenshot
driver.save_screenshot("pagination_visible.png")
print("\n" + "="*60)
print("Screenshot saved: pagination_visible.png")
print("="*60)

input("\nPress Enter to try clicking the first Next button/link found...")

# Try to click
if next_related:
    print("\nAttempting JavaScript click on first button...")
    try:
        driver.execute_script("arguments[0].scrollIntoView(true);", next_related[0])
        time.sleep(1)
        driver.execute_script("arguments[0].click();", next_related[0])
        print("Clicked! Waiting 5 seconds...")
        time.sleep(5)

        # Take another screenshot
        driver.save_screenshot("after_click.png")
        print("Screenshot saved: after_click.png")

        # Check if page changed
        table = driver.find_element(By.CSS_SELECTOR, "table[class*='cluster-table']")
        rows = table.find_elements(By.TAG_NAME, "tr")
        if len(rows) > 1:
            cells = rows[1].find_elements(By.TAG_NAME, "td")
            if len(cells) >= 3:
                print(f"\nFirst symbol after click: {cells[2].text.strip()}")
    except Exception as e:
        print(f"Error clicking: {e}")

elif next_links:
    print("\nAttempting JavaScript click on first link...")
    try:
        driver.execute_script("arguments[0].scrollIntoView(true);", next_links[0])
        time.sleep(1)
        driver.execute_script("arguments[0].click();", next_links[0])
        print("Clicked! Waiting 5 seconds...")
        time.sleep(5)

        driver.save_screenshot("after_click.png")
        print("Screenshot saved: after_click.png")
    except Exception as e:
        print(f"Error clicking: {e}")

input("\nPress Enter to close browser...")
driver.quit()
