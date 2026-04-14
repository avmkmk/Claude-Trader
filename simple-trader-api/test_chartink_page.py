"""
Enhanced Chartink page inspector
Saves page HTML for analysis
"""
import sys
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time

print("Setting up Chrome...")
driver_path = ChromeDriverManager().install()

# Fix Windows bug
if not driver_path.endswith('.exe') and os.name == 'nt':
    driver_dir = os.path.dirname(driver_path)
    chromedriver_exe = os.path.join(driver_dir, 'chromedriver.exe')
    if os.path.exists(chromedriver_exe):
        driver_path = chromedriver_exe

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
print(f"\nNavigating to: {url}")
driver.get(url)

print(f"Page title: {driver.title}")
print("\nWaiting 5 seconds for JavaScript to load...")
time.sleep(5)

# Try to find table with different selectors
print("\nSearching for table...")

# Try multiple possible selectors
selectors = [
    ("ID", "DataTables_Table_0"),
    ("CSS", "table.dataTable"),
    ("CSS", "table"),
    ("CSS", ".table"),
    ("XPATH", "//table")
]

table_found = None
for selector_type, selector in selectors:
    try:
        if selector_type == "ID":
            elements = driver.find_elements(By.ID, selector)
        elif selector_type == "CSS":
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
        elif selector_type == "XPATH":
            elements = driver.find_elements(By.XPATH, selector)

        if elements:
            print(f"  Found {len(elements)} element(s) with {selector_type}: {selector}")
            table_found = elements[0]
            if selector_type != "XPATH":  # Don't break on xpath, check others first
                break
    except Exception as e:
        pass

if table_found:
    print(f"\n  Table found! Tag: {table_found.tag_name}, ID: {table_found.get_attribute('id')}")

    # Try to get rows
    try:
        rows = table_found.find_elements(By.TAG_NAME, "tr")
        print(f"  Rows in table: {len(rows)}")

        if len(rows) > 0:
            # Get first row data
            first_row = rows[1] if len(rows) > 1 else rows[0]  # Skip header
            cells = first_row.find_elements(By.TAG_NAME, "td")
            if cells:
                print(f"  First row has {len(cells)} cells")
                print(f"  First cell text: {cells[0].text}")
    except Exception as e:
        print(f"  Error getting rows: {e}")
else:
    print("  NO TABLE FOUND!")

# Save page source
output_file = "chartink_page_source.html"
with open(output_file, "w", encoding="utf-8") as f:
    f.write(driver.page_source)

print(f"\nPage source saved to: {output_file}")
print(f"Page source length: {len(driver.page_source)} characters")

# Print first 2000 characters
print("\nFirst 2000 characters of page:")
print("=" * 60)
print(driver.page_source[:2000])
print("=" * 60)

driver.quit()
print("\nDone!")
