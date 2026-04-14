"""
Find the actual table structure near the sort buttons
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

print("Waiting 10 seconds...")
time.sleep(10)

# Find sort button and trace back to table
try:
    sort_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Sort table by Symbol')]")
    print("Found 'Sort by Symbol' button!")

    # Get parent elements to find the table structure
    parent = sort_button
    for i in range(5):
        parent = parent.find_element(By.XPATH, "..")
        tag = parent.tag_name
        classes = parent.get_attribute('class') or ''
        print(f"  Parent {i+1}: <{tag}> class='{classes[:80]}'")

    # Now look for tbody or rows near this button
    print("\nLooking for table/tbody near sort buttons...")

    # Try to find the container with all results
    containers = driver.find_elements(By.CSS_SELECTOR, "tbody, [role='rowgroup'], [class*='table']")
    print(f"\nFound {len(containers)} potential containers")

    for i, container in enumerate(containers[:5], 1):
        print(f"\nContainer {i}:")
        print(f"  Tag: {container.tag_name}")
        print(f"  Class: {(container.get_attribute('class') or '')[:80]}")

        # Look for child elements that might be rows
        children = container.find_elements(By.XPATH, "./*")
        print(f"  Children: {len(children)}")

        if len(children) > 1:
            first_child = children[0]
            print(f"  First child tag: {first_child.tag_name}")
            print(f"  First child class: {(first_child.get_attribute('class') or '')[:80]}")
            print(f"  First child text: {first_child.text[:80]}")

    # NEW APPROACH: Look for divs that contain stock symbols
    print("\n" + "="*60)
    print("Searching for elements containing known stocks...")
    print("="*60)

    known_stocks = ["SALSTEEL", "INOXINDIA", "MTARTECH", "STLTECH"]
    for stock in known_stocks:
        try:
            elements = driver.find_elements(By.XPATH, f"//*[contains(text(), '{stock}')]")
            if elements:
                print(f"\n'{stock}' found in {len(elements)} elements:")
                for el in elements[:2]:  # Show first 2
                    print(f"  Tag: {el.tag_name}, Class: {(el.get_attribute('class') or '')[:60]}")
                    print(f"  Text: {el.text[:80]}")
                break
        except:
            pass

except Exception as e:
    print(f"Error: {e}")

driver.quit()
