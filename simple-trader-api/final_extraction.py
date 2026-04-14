"""
Final attempt - extract everything and parse stocks
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

print("Testing both screeners:\n")

urls = {
    "within-2-52week": "https://chartink.com/screener/within-2-of-52-week-highs-chartitude",
    "stage-2-trend": "https://chartink.com/screener/stage-2-trend-template"
}

all_stocks = []

for source, url in urls.items():
    print(f"{'='*60}")
    print(f"Source: {source}")
    print(f"URL: {url}")
    print(f"{'='*60}\n")

    driver.get(url)
    time.sleep(10)

    # Get ALL div elements and check their text
    all_divs = driver.find_elements(By.TAG_NAME, "div")

    # Known Indian stocks for validation
    indian_stocks = ["RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK", "SBIN", 
                     "BHARTIARTL", "ITC", "KOTAKBANK", "LT", "AXISBANK", "HDFC",
                     "WIPRO", "MARUTI", "SUNPHARMA", "TITAN", "ULTRACEMCO",
                     "ONGC", "NTPC", "POWERGRID"]

    stocks_this_source = []

    # Check each div for stock-like content
    for div in all_divs:
        text = div.text.strip()
        if text and 3 <= len(text) <= 15 and text.isupper() and text.isalpha():
            # Check if it's a known stock or follows pattern
            if text in indian_stocks or any(stock in text for stock in indian_stocks):
                if text not in stocks_this_source:
                    stocks_this_source.append(text)

    print(f"Stocks found from {source}: {len(stocks_this_source)}")
    if stocks_this_source:
        for i, stock in enumerate(stocks_this_source[:10], 1):
            print(f"  {i}. {stock}")
        if len(stocks_this_source) > 10:
            print(f"  ... and {len(stocks_this_source) - 10} more\n")

        all_stocks.extend([{"symbol": s, "source": source} for s in stocks_this_source])
    else:
        print("  NONE FOUND\n")

driver.quit()

print(f"\n{'='*60}")
print(f"FINAL RESULTS")
print(f"{'='*60}")
print(f"Total stocks from both screeners: {len(all_stocks)}\n")

if all_stocks:
    for i, stock in enumerate(all_stocks[:20], 1):
        print(f"  {i:2d}. {stock['symbol']:15s} (from {stock['source']})")
    if len(all_stocks) > 20:
        print(f"\n  ... and {len(all_stocks) - 20} more")
else:
    print("NO STOCKS EXTRACTED")
    print("\nChartink likely requires:")
    print("  1. Login/authentication")
    print("  2. Or uses anti-scraping measures")
    print("  3. Or loads data via API calls that Selenium can't intercept")
