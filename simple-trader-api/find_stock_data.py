"""
More aggressive search for stock data on Chartink
"""
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import os
import re

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

print("Waiting 10 seconds for full page load...")
time.sleep(10)

# Get all text content
page_text = driver.find_element(By.TAG_NAME, "body").text

print(f"{'='*60}")
print("SEARCHING FOR STOCK SYMBOLS")
print(f"{'='*60}\n")

# Look for NSE/BSE stock pattern (usually ALLCAPS)
stock_pattern = r'\b[A-Z][A-Z0-9]{2,14}\b'
potential_stocks = re.findall(stock_pattern, page_text)

# Filter for likely stock names (remove common words)
common_words = {'THE', 'AND', 'FOR', 'ARE', 'THIS', 'FROM', 'WITH', 'YOUR', 'HAVE',
                'BEEN', 'THAT', 'WILL', 'MORE', 'ALL', 'CAN', 'GET', 'VIEW', 'HOME',
                'ABOUT', 'SEARCH', 'LOGIN', 'LOGOUT', 'SIGN', 'JOIN', 'FREE', 'HELP',
                'CONTACT', 'PRIVACY', 'TERMS', 'STOCK', 'STOCKS', 'NSE', 'BSE', 'INDIA'}

likely_stocks = [s for s in potential_stocks if s not in common_words and len(s) >= 3]

# Remove duplicates while preserving order
seen = set()
unique_stocks = []
for stock in likely_stocks:
    if stock not in seen:
        seen.add(stock)
        unique_stocks.append(stock)

if unique_stocks:
    print(f"Found {len(unique_stocks)} potential stock symbols:\n")
    for i, stock in enumerate(unique_stocks[:20], 1):  # Show first 20
        print(f"  {i:2d}. {stock}")
    if len(unique_stocks) > 20:
        print(f"\n  ... and {len(unique_stocks) - 20} more")
else:
    print("NO STOCK SYMBOLS FOUND\n")
    print("Page might require:")
    print("  - Login/authentication")
    print("  - Button click to load results")
    print("  - Different wait strategy")

# Check if there's a "login" or "sign in" requirement
if "login" in page_text.lower() or "sign in" in page_text.lower():
    print("\n⚠️  Page mentions 'login' or 'sign in'")

# Save page content for inspection
with open("page_text_content.txt", "w", encoding="utf-8") as f:
    f.write(page_text)

print(f"\n{'='*60}")
print("Page text saved to: page_text_content.txt")
print(f"{'='*60}")

driver.quit()
