"""
Scraper that scrolls to pagination and waits for it to be visible
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
    print("Waiting 15 seconds for page load...")
    time.sleep(15)

    try:
        page_num = 1
        max_pages = 20
        seen_symbols = set()

        while page_num <= max_pages:
            print(f"\nPage {page_num}:")

            # Scroll to bottom to ensure pagination is visible
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)

            # Find table
            try:
                table = driver.find_element(By.CSS_SELECTOR, "table[class*='cluster-table']")
            except:
                print("  Could not find table")
                break

            rows = table.find_elements(By.TAG_NAME, "tr")
            print(f"  Found {len(rows)} rows")

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
                print(f"  No new stocks found - stopping")
                break

            # Store first symbol to detect page change
            current_first = page_symbols[0] if page_symbols else None

            # Try all possible Next button approaches
            clicked = False

            # Approach 1: Find by aria-label
            try:
                wait = WebDriverWait(driver, 5)
                next_btn = wait.until(EC.element_to_be_clickable(
                    (By.XPATH, "//*[@aria-label='Go to next page' or @aria-label='Next page' or contains(@aria-label, 'next')]")
                ))
                print(f"  Found Next button via aria-label")
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_btn)
                time.sleep(1)
                driver.execute_script("arguments[0].click();", next_btn)
                clicked = True
            except:
                pass

            # Approach 2: Button with text "Next"
            if not clicked:
                try:
                    buttons = driver.find_elements(By.TAG_NAME, "button")
                    for btn in buttons:
                        if btn.text.strip().lower() == 'next' and btn.is_displayed():
                            print(f"  Found Next button via text")
                            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                            time.sleep(1)
                            driver.execute_script("arguments[0].click();", btn)
                            clicked = True
                            break
                except:
                    pass

            # Approach 3: Button with >
            if not clicked:
                try:
                    buttons = driver.find_elements(By.TAG_NAME, "button")
                    for btn in buttons:
                        btn_text = btn.text.strip()
                        if btn_text in ['>', '›', '»'] and btn.is_displayed():
                            print(f"  Found Next button via '>' symbol")
                            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                            time.sleep(1)
                            driver.execute_script("arguments[0].click();", btn)
                            clicked = True
                            break
                except:
                    pass

            # Approach 4: Find inside nav element
            if not clicked:
                try:
                    navs = driver.find_elements(By.TAG_NAME, "nav")
                    for nav in navs:
                        buttons = nav.find_elements(By.TAG_NAME, "button")
                        if buttons and len(buttons) > 0:
                            # Last button in nav is often Next
                            last_btn = buttons[-1]
                            if last_btn.is_displayed() and not last_btn.get_attribute('disabled'):
                                print(f"  Found Next button as last button in nav")
                                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", last_btn)
                                time.sleep(1)
                                driver.execute_script("arguments[0].click();", last_btn)
                                clicked = True
                                break
                except:
                    pass

            if not clicked:
                print(f"  Could not find or click Next button")
                break

            # Wait for page to change
            print(f"  Waiting for page to update...")
            page_changed = False
            for i in range(10):
                time.sleep(1)
                try:
                    table = driver.find_element(By.CSS_SELECTOR, "table[class*='cluster-table']")
                    rows = table.find_elements(By.TAG_NAME, "tr")
                    if len(rows) > 1:
                        cells = rows[1].find_elements(By.TAG_NAME, "td")
                        if len(cells) >= 3:
                            new_first = cells[2].text.strip()
                            if new_first and new_first != current_first:
                                print(f"  ✓ Page changed: {current_first} → {new_first}")
                                page_changed = True
                                break
                except:
                    pass

            if not page_changed:
                print(f"  Page did not change after 10s - stopping")
                break

            page_num += 1

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

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
expected_total = "Expected: 34 (within-2-52week) + 102 (stage-2-trend) = 136 stocks"
actual_total = f"Actual: {len(all_results)} stocks"
print(expected_total)
print(actual_total)
if len(all_results) >= 130:
    print("✅ SUCCESS - Got all stocks!")
else:
    print(f"❌ INCOMPLETE - Missing {136 - len(all_results)} stocks")
print(f"{'='*60}")
