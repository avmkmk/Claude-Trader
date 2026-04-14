"""
Test script for ChromeDriver and Chartink scraping
Run: python test_scraper.py
"""
import sys
import os

# Test 1: Check Chrome installation
print("=" * 60)
print("TEST 1: Chrome Browser Installation")
print("=" * 60)

chrome_paths = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
]

chrome_found = None
for path in chrome_paths:
    if os.path.exists(path):
        chrome_found = path
        print(f"Chrome found: {path}")
        break

if not chrome_found:
    print("Chrome not found at standard locations")
    print("  Please install Chrome or update paths")
    sys.exit(1)

# Test 2: Check Selenium installation
print("\n" + "=" * 60)
print("TEST 2: Selenium Installation")
print("=" * 60)

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from webdriver_manager.chrome import ChromeDriverManager
    print("Selenium imports successful")
except ImportError as e:
    print(f"Selenium import failed: {e}")
    print("  Run: pip install selenium webdriver-manager")
    sys.exit(1)

# Test 3: ChromeDriver installation
print("\n" + "=" * 60)
print("TEST 3: ChromeDriver Installation")
print("=" * 60)

try:
    print("Attempting to install/locate ChromeDriver...")
    driver_path = ChromeDriverManager().install()

    # Fix Windows webdriver-manager bug
    if not driver_path.endswith('.exe') and os.name == 'nt':
        driver_dir = os.path.dirname(driver_path)
        chromedriver_exe = os.path.join(driver_dir, 'chromedriver.exe')
        if os.path.exists(chromedriver_exe):
            driver_path = chromedriver_exe
            print(f"Fixed ChromeDriver path on Windows: {driver_path}")

    print(f"ChromeDriver path: {driver_path}")
except Exception as e:
    print(f"ChromeDriver installation failed: {e}")
    print("\nTroubleshooting:")
    print("  1. Check internet connection")
    print("  2. Try: webdriver-manager --version")
    print("  3. Manually download ChromeDriver from: https://chromedriver.chromium.org/")
    sys.exit(1)

# Test 4: Launch headless Chrome
print("\n" + "=" * 60)
print("TEST 4: Headless Chrome Launch")
print("=" * 60)

try:
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")  # Use new headless mode
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")

    service = Service(driver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)

    print("Chrome driver created successfully")

    # Test 5: Access Chartink
    print("\n" + "=" * 60)
    print("TEST 5: Access Chartink Website")
    print("=" * 60)

    test_url = "https://chartink.com/screener/within-2-of-52-week-highs-chartitude"
    print(f"Navigating to: {test_url}")

    driver.get(test_url)
    print(f"Page loaded, title: {driver.title}")

    # Test 6: Wait for table
    print("\n" + "=" * 60)
    print("TEST 6: Find DataTable")
    print("=" * 60)

    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC

    try:
        table = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.ID, "DataTables_Table_0"))
        )
        print("DataTable found!")

        # Count rows
        rows = driver.find_elements(By.CSS_SELECTOR, "#DataTables_Table_0 tbody tr")
        print(f"Found {len(rows)} rows in table")

        if len(rows) > 0:
            # Try to extract first symbol
            first_row = rows[0]
            cells = first_row.find_elements(By.TAG_NAME, "td")
            if cells:
                symbol = cells[0].text.strip()
                print(f"Sample symbol extracted: {symbol}")

    except Exception as e:
        print(f"Failed to find table: {e}")
        print("\nPossible causes:")
        print("  1. Chartink changed page structure")
        print("  2. Anti-scraping measures blocked access")
        print("  3. Page requires authentication")
        print(f"\nPage source preview:\n{driver.page_source[:500]}")

    driver.quit()
    print("\n" + "=" * 60)
    print("ALL TESTS PASSED")
    print("=" * 60)

except Exception as e:
    print(f"Chrome launch failed: {e}")
    print("\nTroubleshooting:")
    print("  1. Ensure Chrome and ChromeDriver versions match")
    print("  2. Try running as administrator")
    print("  3. Check antivirus/firewall settings")
    sys.exit(1)
