"""
Complete Chartink scraper with pagination
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

urls = {
    "within-2-52week": "https://chartink.com/screener/within-2-of-52-week-highs-chartitude",
    "stage-2-trend": "https://chartink.com/screener/stage-2-trend-template"
}

all_results = []

for source, url in urls.items():
    print(f"\n{'='*60}")
    print(f"Scraping: {source}")
    print(f"URL: {url}")
    print(f"{'='*60}\n")

    driver.get(url)
    time.sleep(10)  # Wait for page load

    # Find the stock table
    try:
        # The table with class containing 'cluster-table'
        table = driver.find_element(By.CSS_SELECTOR, "table.cluster-table--resizabl, table[class*='cluster-table']")
        print(f"Found stock table!")

        page_num = 1
        max_pages = 10  # Safety limit

        while page_num <= max_pages:
            print(f"\nPage {page_num}:")

            # Extract stocks from current page
            rows = table.find_elements(By.TAG_NAME, "tr")
            print(f"  Found {len(rows)} rows")

            stocks_this_page = 0
            for row in rows[1:]:  # Skip header row
                cells = row.find_elements(By.TAG_NAME, "td")
                if len(cells) >= 3:
                    # Cell 2 has stock name, Cell 3 has symbol
                    symbol = cells[2].text.strip()
                    if symbol and symbol != 'Symbol':  # Skip if it's header
                        all_results.append({"symbol": symbol, "source": source})
                        stocks_this_page += 1

            print(f"  Extracted {stocks_this_page} stocks")

            # Look for Next button
            try:
                next_buttons = driver.find_elements(By.XPATH, "//button[contains(text(), 'Next') or contains(@aria-label, 'Next')]")
                if not next_buttons:
                    next_buttons = driver.find_elements(By.XPATH, "//a[contains(text(), 'Next')]")

                if next_buttons:
                    next_button = next_buttons[0]

                    # Check if button is disabled
                    is_disabled = next_button.get_attribute('disabled') or 'disabled' in (next_button.get_attribute('class') or '')

                    if is_disabled:
                        print(f"  Reached last page")
                        break

                    # Click next
                    next_button.click()
                    time.sleep(3)  # Wait for next page to load
                    page_num += 1

                    # Re-find table after page change
                    table = driver.find_element(By.CSS_SELECTOR, "table.cluster-table--resizabl, table[class*='cluster-table']")
                else:
                    print(f"  No Next button found - only 1 page")
                    break

            except Exception as e:
                print(f"  Navigation ended: {e}")
                break

        if page_num > max_pages:
            print(f"\nHit safety limit ({max_pages} pages)")

    except Exception as e:
        print(f"Error scraping {source}: {e}")

driver.quit()

print(f"\n\n{'='*60}")
print(f"FINAL RESULTS - BOTH SCREENERS")
print(f"{'='*60}\n")
print(f"Total stocks extracted: {len(all_results)}\n")

if all_results:
    # Group by source
    for source_name in ["within-2-52week", "stage-2-trend"]:
        source_stocks = [r for r in all_results if r["source"] == source_name]
        if source_stocks:
            print(f"\n{source_name.upper()}: {len(source_stocks)} stocks")
            print("-" * 60)
            for i, stock in enumerate(source_stocks[:20], 1):
                print(f"  {i:2d}. {stock['symbol']}")
            if len(source_stocks) > 20:
                print(f"  ... and {len(source_stocks) - 20} more\n")

    print(f"\n{'='*60}")
    print(f"SUCCESS! Scraped {len(all_results)} total stocks")
    print(f"{'='*60}")
else:
    print("FAILED - No stocks extracted")
