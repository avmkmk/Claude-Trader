"""
Complete Chartink scraper with proper pagination
"""
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
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
    time.sleep(10)  # Wait for initial page load

    try:
        # Find the stock table
        table = driver.find_element(By.CSS_SELECTOR, "table[class*='cluster-table']")
        print(f"Found stock table!")

        page_num = 1
        max_pages = 20  # Safety limit

        while page_num <= max_pages:
            print(f"\nPage {page_num}:")

            # Extract stocks from current page
            rows = table.find_elements(By.TAG_NAME, "tr")
            print(f"  Found {len(rows)} rows")

            stocks_this_page = 0
            for row in rows[1:]:  # Skip header row
                cells = row.find_elements(By.TAG_NAME, "td")
                if len(cells) >= 3:
                    symbol = cells[2].text.strip()
                    if symbol and symbol.isupper() and symbol != 'SYMBOL':
                        all_results.append({"symbol": symbol, "source": source})
                        stocks_this_page += 1

            print(f"  Extracted {stocks_this_page} stocks")

            # Try to click Next button
            try:
                # Wait a bit for any JS to settle
                time.sleep(1)

                # Find Next button - try multiple approaches
                next_button = None

                # Approach 1: Button with text "Next"
                try:
                    next_button = driver.find_element(By.XPATH, "//button[text()='Next']")
                except:
                    pass

                # Approach 2: Link with text "Next"
                if not next_button:
                    try:
                        next_button = driver.find_element(By.XPATH, "//a[text()='Next']")
                    except:
                        pass

                # Approach 3: Any element with aria-label containing "next"
                if not next_button:
                    try:
                        next_button = driver.find_element(By.XPATH, "//*[contains(@aria-label, 'next') or contains(@aria-label, 'Next')]")
                    except:
                        pass

                # Approach 4: Button/link with > symbol
                if not next_button:
                    try:
                        next_button = driver.find_element(By.XPATH, "//button[contains(text(), '>') or contains(text(), '›') or contains(text(), '»')]")
                    except:
                        pass

                if next_button:
                    # Check if button is disabled
                    disabled_attr = next_button.get_attribute('disabled')
                    aria_disabled = next_button.get_attribute('aria-disabled')
                    classes = next_button.get_attribute('class') or ''

                    is_disabled = (
                        disabled_attr == 'true' or
                        disabled_attr == 'disabled' or
                        aria_disabled == 'true' or
                        'disabled' in classes.lower() or
                        'cursor-not-allowed' in classes.lower()
                    )

                    if is_disabled:
                        print(f"  Next button disabled - reached last page")
                        break

                    # Click next
                    print(f"  Clicking Next...")
                    next_button.click()
                    time.sleep(3)  # Wait for next page to load

                    # Re-find table after navigation
                    table = driver.find_element(By.CSS_SELECTOR, "table[class*='cluster-table']")
                    page_num += 1
                else:
                    print(f"  No Next button found - single page only")
                    break

            except Exception as e:
                print(f"  Navigation ended: {str(e)[:100]}")
                break

        if page_num > max_pages:
            print(f"\n⚠️  Hit safety limit ({max_pages} pages)")

    except Exception as e:
        print(f"❌ Error scraping {source}: {e}")

driver.quit()

print(f"\n\n{'='*60}")
print(f"FINAL RESULTS - BOTH SCREENERS")
print(f"{'='*60}\n")

if all_results:
    # Group by source
    for source_name in ["within-2-52week", "stage-2-trend"]:
        source_stocks = [r for r in all_results if r["source"] == source_name]
        if source_stocks:
            print(f"\n{source_name.upper()}: {len(source_stocks)} stocks")
            print("-" * 60)
            for i, stock in enumerate(source_stocks, 1):
                print(f"  {i:2d}. {stock['symbol']}")

    print(f"\n{'='*60}")
    print(f"✅ SUCCESS! Scraped {len(all_results)} total stocks")
    print(f"{'='*60}")
else:
    print("❌ FAILED - No stocks extracted")
