"""
Detailed inspection of pagination structure
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
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=1920,1080")
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")

service = Service(driver_path)
driver = webdriver.Chrome(service=service, options=chrome_options)

# Test with stage-2-trend which has 102 stocks (multiple pages)
url = "https://chartink.com/screener/stage-2-trend-template"
print(f"Loading: {url}\n")
driver.get(url)

print("Waiting 10 seconds...")
time.sleep(10)

print("="*60)
print("PAGINATION STRUCTURE ANALYSIS")
print("="*60)

# Find all elements with "next" in text or attributes
elements = driver.find_elements(By.XPATH, "//*[contains(translate(., 'NEXT', 'next'), 'next')]")
print(f"\nFound {len(elements)} elements containing 'next':")

for i, el in enumerate(elements[:10], 1):
    print(f"\nElement {i}:")
    print(f"  Tag: {el.tag_name}")
    print(f"  Text: '{el.text[:50]}'")
    print(f"  Classes: {(el.get_attribute('class') or 'none')[:80]}")
    print(f"  Disabled attr: {el.get_attribute('disabled')}")
    print(f"  Aria-disabled: {el.get_attribute('aria-disabled')}")
    print(f"  Is displayed: {el.is_displayed()}")
    print(f"  Is enabled: {el.is_enabled()}")

# Look for page info text like "Page 1 of 6" or "1-20 of 102"
page_text = driver.find_element(By.TAG_NAME, "body").text
print(f"\n{'='*60}")
print("SEARCHING FOR PAGE COUNT INFO")
print(f"{'='*60}\n")

# Look for numbers that might indicate total pages/results
import re
patterns = [
    r'Page \d+ of \d+',
    r'\d+-\d+ of \d+',
    r'Showing \d+ to \d+ of \d+',
    r'(\d+) results',
    r'(\d+) stocks',
]

for pattern in patterns:
    matches = re.findall(pattern, page_text, re.IGNORECASE)
    if matches:
        print(f"Pattern '{pattern}' found: {matches}")

# Get the raw HTML of the pagination area
try:
    nav = driver.find_element(By.TAG_NAME, "nav")
    print(f"\n{'='*60}")
    print("NAV ELEMENT HTML")
    print(f"{'='*60}")
    print(nav.get_attribute('outerHTML')[:500])
except:
    print("\nNo nav element found")

driver.quit()
