"""
Extract stocks from Chartink using proper selectors
"""
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
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

print("Waiting for page to load...")
time.sleep(10)

# Try to find links or elements containing stock symbols
# Chartink usually links each stock
stocks_found = []

# Strategy 1: Find all links (stock symbols are usually clickable)
try:
    links = driver.find_elements(By.TAG_NAME, "a")
    print(f"Found {len(links)} links on page")

    for link in links:
        href = link.get_attribute('href') or ''
        text = link.text.strip()

        # Check if this looks like a stock link
        if '/stocks/' in href and text and len(text) >= 3 and text.isupper():
            stocks_found.append(text)
except Exception as e:
    print(f"Error finding links: {e}")

# Remove duplicates
stocks_found = list(dict.fromkeys(stocks_found))

print(f"\n{'='*60}")
print(f"STOCKS EXTRACTED: {len(stocks_found)}")
print(f"{'='*60}\n")

if stocks_found:
    for i, stock in enumerate(stocks_found, 1):
        print(f"  {i:2d}. {stock}")
else:
    print("  NO STOCKS FOUND!")
    print("\n  Possible reasons:")
    print("  - Page requires login")
    print("  - Results load via AJAX after initial page load")
    print("  - Need to click a 'Run' or 'Search' button")

driver.quit()
