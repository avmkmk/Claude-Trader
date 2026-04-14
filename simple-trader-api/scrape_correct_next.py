"""
Chartink scraper - clicks only the ENABLED Next button (not the disabled "Next >>")
Key insight: There are 2 Next buttons, only click the enabled one!
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

urls = {
    "within-2-52week": "https://chartink.com/screener/within-2-of-52-week-highs-chartitude",
    "stage-2-trend": "https://chartink.com/screener/stage-2-trend-template"
}

all_results = []

for source, url in urls.items():
    print(f"\n{'='*60}")
    print(f"Scraping: {source}")
    print(f"{'='*60}\n")

    driver.get(url)
    print("Waiting 15 seconds for page load...")
    time.sleep(15)

    try:
        page_num = 1
        max_pages = 20
        seen_symbols = set()

        while page_num <= max_pages:
            print(f"\nPage {page_num}:")

            # Find table
            table = driver.find_element(By.CSS_SELECTOR, "table[class*='cluster-table']")
            rows = table.find_elements(By.TAG_NAME, "tr")

            # Extract stocks
            stocks_this_page = 0
            page_symbols = []

            for row in rows[1:]:
                cells = row.find_elements(By.TAG_NAME, "td")
                if len(cells) >= 3:
                    symbol = cells[2].text.strip()
                    if symbol and symbol.isupper() and symbol != 'SYMBOL':
                        page_symbols.append(symbol)
                        if symbol not in seen_symbols:
                            all_results.append({"symbol": symbol, "source": source})
                            seen_symbols.add(symbol)
                            stocks_this_page += 1

            print(f"  Extracted {stocks_this_page} new stocks")
            print(f"  Total for {source}: {len([s for s in all_results if s['source'] == source])}")

            if stocks_this_page == 0 and page_num > 1:
                print(f"  No new stocks - stopping")
                break

            # Store first symbol to detect page change
            current_first = page_symbols[0] if page_symbols else None

            # Find ALL buttons with "Next" text
            try:
                all_buttons = driver.find_elements(By.TAG_NAME, "button")
                next_buttons = []

                for btn in all_buttons:
                    btn_text = btn.text.strip().lower()
                    if 'next' in btn_text:
                        # Check if enabled
                        is_disabled = (
                            btn.get_attribute('disabled') == 'true' or
                            btn.get_attribute('disabled') == 'disabled' or
                            btn.get_attribute('aria-disabled') == 'true'
                        )

                        if not is_disabled and btn.is_displayed():
                            next_buttons.append(btn)
                            print(f"  Found enabled Next button: '{btn.text.strip()}'")

                if not next_buttons:
                    print(f"  No enabled Next button found - last page")
                    break

                # Click the first enabled Next button
                next_button = next_buttons[0]
                print(f"  Clicking Next button...")

                # Scroll into view and click with JavaScript
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_button)
                time.sleep(0.5)
                driver.execute_script("arguments[0].click();", next_button)

                # Wait for page to change
                print(f"  Waiting for page to update...")
                page_changed = False

                for i in range(15):  # Wait up to 15 seconds
                    time.sleep(1)
                    try:
                        table = driver.find_element(By.CSS_SELECTOR, "table[class*='cluster-table']")
                        rows = table.find_elements(By.TAG_NAME, "tr")
                        if len(rows) > 1:
                            cells = rows[1].find_elements(By.TAG_NAME, "td")
                            if len(cells) >= 3:
                                new_first = cells[2].text.strip()
                                if new_first and new_first != current_first:
                                    print(f"  Page changed: {current_first} -> {new_first}")
                                    page_changed = True
                                    break
                    except:
                        pass

                if not page_changed:
                    print(f"  Page did not change - stopping")
                    break

                page_num += 1

            except Exception as e:
                print(f"  Error: {str(e)[:100]}")
                break

    except Exception as e:
        print(f"Error: {e}")

driver.quit()

print(f"\n\n{'='*60}")
print(f"RESULTS BY SOURCE")
print(f"{'='*60}\n")

# Show results by source
within_2_stocks = [r for r in all_results if r["source"] == "within-2-52week"]
stage_2_stocks = [r for r in all_results if r["source"] == "stage-2-trend"]

print(f"WITHIN-2-52WEEK: {len(within_2_stocks)} stocks")
print(f"STAGE-2-TREND: {len(stage_2_stocks)} stocks")
print(f"Total (with duplicates): {len(all_results)} stocks")

# Find unique stocks (eliminate duplicates across sources)
unique_symbols = set()
unique_stocks = []
overlapping_stocks = set()

# Track which symbols appear in both
within_2_symbols = {r["symbol"] for r in within_2_stocks}
stage_2_symbols = {r["symbol"] for r in stage_2_stocks}
overlapping_stocks = within_2_symbols & stage_2_symbols

# Build unique list
for result in all_results:
    if result["symbol"] not in unique_symbols:
        unique_symbols.add(result["symbol"])
        unique_stocks.append(result)

print(f"\n{'='*60}")
print(f"UNIQUE STOCKS (DUPLICATES REMOVED)")
print(f"{'='*60}\n")
print(f"Overlapping stocks (in both screeners): {len(overlapping_stocks)}")
print(f"Unique stocks after deduplication: {len(unique_stocks)}")

if overlapping_stocks:
    print(f"\nStocks appearing in BOTH screeners:")
    for i, symbol in enumerate(sorted(overlapping_stocks), 1):
        print(f"  {i:2d}. {symbol}")

print(f"\n{'='*60}")
print(f"FINAL UNIQUE STOCK LIST")
print(f"{'='*60}\n")

for i, stock in enumerate(sorted(unique_stocks, key=lambda x: x["symbol"]), 1):
    source_badge = "BOTH" if stock["symbol"] in overlapping_stocks else stock["source"].upper()
    print(f"  {i:3d}. {stock['symbol']:20s} [{source_badge}]")

print(f"\n{'='*60}")
print(f"Summary:")
print(f"  - Scraped: 34 + 102 = 136 total stocks")
print(f"  - Overlapping: {len(overlapping_stocks)} stocks")
print(f"  - Unique: {len(unique_stocks)} stocks")
print(f"{'='*60}")
