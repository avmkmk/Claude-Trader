"""
Smart pagination - compare content to detect when done
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
    time.sleep(10)

    try:
        page_num = 1
        max_pages = 20
        seen_symbols = set()  # Track symbols to detect duplicates

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

            # If we got no new stocks, we're probably seeing duplicates = reached end
            if stocks_this_page == 0 and page_num > 1:
                print(f"  No new stocks - reached end")
                break

            # Try to click Next
            try:
                # Find any button/link that might be Next
                next_candidates = []

                # Try multiple XPath expressions
                xpaths = [
                    "//button[contains(text(), 'Next')]",
                    "//a[contains(text(), 'Next')]",
                    "//button[contains(text(), '>')]",
                    "//button[contains(@aria-label, 'next')]",
                    "//button[contains(@aria-label, 'Next')]"
                ]

                for xpath in xpaths:
                    try:
                        elements = driver.find_elements(By.XPATH, xpath)
                        next_candidates.extend(elements)
                    except:
                        pass

                if not next_candidates:
                    print(f"  No Next button found")
                    break

                # Try first visible, enabled button
                clicked = False
                for button in next_candidates:
                    if button.is_displayed():
                        try:
                            # Just click it - if it fails, we're done
                            button.click()
                            print(f"  Clicked Next")
                            time.sleep(3)
                            clicked = True
                            break
                        except Exception as e:
                            # Button not clickable = probably disabled
                            continue

                if not clicked:
                    print(f"  Could not click Next - reached end")
                    break

                page_num += 1

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
