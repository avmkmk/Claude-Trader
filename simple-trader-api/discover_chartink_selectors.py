"""
Discover Chartink's current page structure after JavaScript renders
"""
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
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

# Wait for JavaScript to fully load - test incrementally
prev_wait = 0
for wait_time in [3, 5, 10, 15]:
    print(f"{'='*60}")
    print(f"After waiting {wait_time} seconds:")
    print(f"{'='*60}")
    time.sleep(wait_time - prev_wait)
    prev_wait = wait_time

    # Try multiple selector strategies
    selectors = [
        ("table", By.TAG_NAME, "table"),
        ("tbody", By.TAG_NAME, "tbody"),
        ("tr (all)", By.TAG_NAME, "tr"),
        ("div[class*='table']", By.CSS_SELECTOR, "div[class*='table']"),
        ("div[class*='grid']", By.CSS_SELECTOR, "div[class*='grid']"),
        ("div[class*='row']", By.CSS_SELECTOR, "div[class*='row']"),
        ("[data-table]", By.CSS_SELECTOR, "[data-table]"),
        ("[role='table']", By.CSS_SELECTOR, "[role='table']"),
        ("[role='grid']", By.CSS_SELECTOR, "[role='grid']"),
        ("div[class*='stock']", By.CSS_SELECTOR, "div[class*='stock']"),
    ]

    for name, by_type, selector in selectors:
        try:
            elements = driver.find_elements(by_type, selector)
            if elements:
                print(f"  Found {len(elements)} x '{name}'")

                # If we found tables or tbody, dive deeper
                if name in ["table", "tbody"] and len(elements) > 0:
                    elem = elements[0]
                    elem_id = elem.get_attribute('id')
                    elem_class = elem.get_attribute('class')
                    print(f"    First element - ID: '{elem_id}', Class: '{elem_class}'")

                    # Try to get rows
                    if name == "table":
                        rows = elem.find_elements(By.TAG_NAME, "tr")
                        print(f"    Contains {len(rows)} rows")
                        if len(rows) > 1:
                            data_row = rows[1]  # Skip header
                            cells = data_row.find_elements(By.TAG_NAME, "td")
                            if cells and len(cells) > 0:
                                print(f"    First row has {len(cells)} cells")
                                first_cell_text = cells[0].text[:50]
                                print(f"    First cell: '{first_cell_text}'")
        except Exception as e:
            pass

    # Look for stock symbols in page text
    try:
        page_text = driver.find_element(By.TAG_NAME, "body").text
        common_stocks = ["RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK"]
        found_stocks = [s for s in common_stocks if s in page_text]
        if found_stocks:
            print(f"  Stock symbols found: {', '.join(found_stocks)}")
    except:
        pass

    print()

# Take screenshot
driver.save_screenshot("chartink_rendered.png")
print(f"{'='*60}")
print("Screenshot saved: chartink_rendered.png")
print(f"{'='*60}\n")

driver.quit()
