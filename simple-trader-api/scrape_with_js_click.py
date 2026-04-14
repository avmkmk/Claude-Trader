"""
Chartink scraper with JavaScript click and AJAX detection
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
    print(f"{'='*60}\n")

    driver.get(url)
    time.sleep(10)

    try:
        page_num = 1
        max_pages = 20
        seen_symbols = set()

        while page_num <= max_pages:
            print(f"Page {page_num}:")

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
            print(f"  Total unique so far: {len([s for s in all_results if s['source'] == source])}")

            if stocks_this_page == 0 and page_num > 1:
                print(f"  No new stocks - reached end")
                break

            # Try to find and click Next button using JavaScript
            try:
                # Try multiple selectors for Next button
                next_button = None
                selectors = [
                    "//button[contains(text(), 'Next')]",
                    "//a[contains(text(), 'Next')]",
                    "//button[contains(., '>') and not(contains(., '<<'))]",
                    "//*[contains(@aria-label, 'next')]"
                ]

                for selector in selectors:
                    try:
                        elements = driver.find_elements(By.XPATH, selector)
                        if elements:
                            for elem in elements:
                                if elem.is_displayed() and elem.is_enabled():
                                    next_button = elem
                                    break
                            if next_button:
                                break
                    except:
                        pass

                if not next_button:
                    print(f"  No Next button found")
                    break

                # Check if disabled
                disabled = next_button.get_attribute('disabled')
                aria_disabled = next_button.get_attribute('aria-disabled')
                classes = next_button.get_attribute('class') or ''

                if disabled == 'true' or aria_disabled == 'true' or 'disabled' in classes.lower():
                    print(f"  Next button is disabled - last page")
                    break

                # Get current first symbol to detect page change
                current_first_symbol = page_symbols[0] if page_symbols else None

                # Use JavaScript click instead of Selenium click
                print(f"  Clicking Next with JavaScript...")
                driver.execute_script("arguments[0].click();", next_button)

                # Wait for page change - check if first symbol changes
                max_wait = 10
                page_changed = False
                for i in range(max_wait):
                    time.sleep(0.5)
                    try:
                        table = driver.find_element(By.CSS_SELECTOR, "table[class*='cluster-table']")
                        rows = table.find_elements(By.TAG_NAME, "tr")
                        if len(rows) > 1:
                            cells = rows[1].find_elements(By.TAG_NAME, "td")
                            if len(cells) >= 3:
                                new_first_symbol = cells[2].text.strip()
                                if new_first_symbol and new_first_symbol != current_first_symbol:
                                    page_changed = True
                                    print(f"  Page changed detected (old: {current_first_symbol}, new: {new_first_symbol})")
                                    break
                    except:
                        pass

                if not page_changed:
                    print(f"  Page did not change after {max_wait/2}s - stopping")
                    break

                page_num += 1
                time.sleep(2)  # Extra wait for stability

            except Exception as e:
                print(f"  Pagination error: {str(e)[:80]}")
                break

    except Exception as e:
        print(f"Error: {e}")

driver.quit()

print(f"\n\n{'='*60}")
print(f"FINAL RESULTS")
print(f"{'='*60}\n")

for source_name in ["within-2-52week", "stage-2-trend"]:
    source_stocks = [r for r in all_results if r["source"] == source_name]
    if source_stocks:
        print(f"\n{source_name.upper()}: {len(source_stocks)} stocks")
        print("-" * 60)
        for i, stock in enumerate(source_stocks, 1):
            print(f"  {i:2d}. {stock['symbol']}")

print(f"\n{'='*60}")
print(f"Total: {len(all_results)} stocks from both screeners")
print(f"{'='*60}")
