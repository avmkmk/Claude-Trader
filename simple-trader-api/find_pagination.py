"""
Find pagination elements to locate the data table
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

url = "https://chartink.com/screener/within-2-of-52-week-highs-chartitude"
print(f"Loading: {url}\n")
driver.get(url)

print("Waiting 10 seconds for page load...")
time.sleep(10)

print("="*60)
print("SEARCHING FOR PAGINATION")
print("="*60)

# Look for pagination-related text/elements
page_text = driver.find_element(By.TAG_NAME, "body").text

# Common pagination patterns
pagination_keywords = ["page", "of", "showing", "entries", "results", "stocks", "next", "previous"]

for keyword in pagination_keywords:
    if keyword in page_text.lower():
        # Find elements containing this keyword
        elements = driver.find_elements(By.XPATH, f"//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{keyword}')]")
        if elements:
            print(f"\nFound '{keyword}' in {len(elements)} elements:")
            for el in elements[:3]:
                text = el.text.strip()
                if text and len(text) < 200:  # Not too long
                    print(f"  - {text[:100]}")

# Look for page numbers or navigation
print("\n" + "="*60)
print("LOOKING FOR PAGE NUMBERS/NAVIGATION")
print("="*60)

# Find links that might be page numbers
links = driver.find_elements(By.TAG_NAME, "a")
page_links = []
for link in links:
    text = link.text.strip()
    href = link.get_attribute('href') or ''

    # Check if it looks like a page number or next/prev button
    if text.isdigit() or text.lower() in ['next', 'prev', 'previous', '>', '<', '»', '«']:
        page_links.append((text, href))

if page_links:
    print(f"\nFound {len(page_links)} pagination links:")
    for text, href in page_links[:10]:
        print(f"  - Text: '{text}', Href: {href[:60]}")

# Look for nav elements
navs = driver.find_elements(By.TAG_NAME, "nav")
print(f"\nFound {len(navs)} <nav> elements")

# Try to find the table now that we know pagination exists
print("\n" + "="*60)
print("LOOKING FOR THE MAIN DATA TABLE")
print("="*60)

# Get all tables
tables = driver.find_elements(By.TAG_NAME, "table")
print(f"\nFound {len(tables)} tables")

for i, table in enumerate(tables, 1):
    rows = table.find_elements(By.TAG_NAME, "tr")
    print(f"\nTable {i}:")
    print(f"  Rows: {len(rows)}")
    print(f"  ID: {table.get_attribute('id') or 'none'}")
    print(f"  Class: {(table.get_attribute('class') or 'none')[:60]}")

    if rows and len(rows) > 1:
        # Check first data row
        for row in rows[1:3]:  # Check rows 2 and 3
            cells = row.find_elements(By.TAG_NAME, "td")
            if cells:
                print(f"  Row {rows.index(row)+1} has {len(cells)} cells:")
                for j, cell in enumerate(cells[:5], 1):  # First 5 cells
                    text = cell.text.strip()
                    if text:
                        print(f"    Cell {j}: {text[:40]}")

driver.quit()
