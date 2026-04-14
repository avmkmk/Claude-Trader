"""
Extract all potential stocks without strict filtering
"""
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import os
import re

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

print("Scraping both Chartink screeners:\n")

urls = {
    "within-2-52week": "https://chartink.com/screener/within-2-of-52-week-highs-chartitude",
    "stage-2-trend": "https://chartink.com/screener/stage-2-trend-template"
}

all_results = []

for source, url in urls.items():
    print(f"{'='*60}")
    print(f"Scraping: {source}")
    print(f"{'='*60}\n")

    driver.get(url)
    print("Waiting 10 seconds for page load...")
    time.sleep(10)

    # Get body text
    body_text = driver.find_element(By.TAG_NAME, "body").text

    # Extract all uppercase words (potential stocks)
    pattern = r'\b[A-Z][A-Z0-9]{2,14}\b'
    candidates = re.findall(pattern, body_text)

    # Filter out obvious non-stocks
    exclude = {'THE', 'AND', 'FOR', 'ARE', 'THIS', 'FROM', 'WITH', 'YOUR', 'HAVE',
               'BEEN', 'THAT', 'WILL', 'MORE', 'ALL', 'CAN', 'GET', 'VIEW', 'HOME',
               'ABOUT', 'SEARCH', 'LOGIN', 'LOGOUT', 'SIGN', 'JOIN', 'FREE', 'HELP',
               'CONTACT', 'PRIVACY', 'TERMS', 'STOCK', 'STOCKS', 'NSE', 'BSE', 'INDIA',
               'WITHIN', 'WEEK', 'HIGHS', 'MAGIC', 'FILTERS', 'CSV', 'COPY', 'LIVE',
               'CHARTITUDE', 'STAGE', 'TREND', 'TEMPLATE'}

    stocks = []
    for candidate in candidates:
        if candidate not in exclude and candidate not in stocks:
            stocks.append(candidate)

    print(f"Found {len(stocks)} potential stocks from {source}:\n")

    if stocks:
        for i, stock in enumerate(stocks[:20], 1):
            print(f"  {i:2d}. {stock}")
            all_results.append({"symbol": stock, "source": source})

        if len(stocks) > 20:
            print(f"\n  ... and {len(stocks) - 20} more\n")
            # Add remaining to results
            for stock in stocks[20:]:
                all_results.append({"symbol": stock, "source": source})
    else:
        print("  NO STOCKS FOUND\n")

driver.quit()

print(f"\n{'='*60}")
print(f"FINAL RESULTS - BOTH SCREENERS")
print(f"{'='*60}")
print(f"Total stocks extracted: {len(all_results)}\n")

if all_results:
    # Show all results grouped by source
    for source in ["within-2-52week", "stage-2-trend"]:
        source_stocks = [r for r in all_results if r["source"] == source]
        if source_stocks:
            print(f"\n{source}: {len(source_stocks)} stocks")
            for i, stock in enumerate(source_stocks[:15], 1):
                print(f"  {i:2d}. {stock['symbol']}")
            if len(source_stocks) > 15:
                print(f"  ... and {len(source_stocks) - 15} more")
else:
    print("SCRAPING FAILED - NO STOCKS EXTRACTED")
