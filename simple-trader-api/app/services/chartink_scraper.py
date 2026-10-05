"""
Chartink Scraper Service

Scrapes stocks from Chartink screeners using Selenium.
Handles JavaScript-rendered tables and pagination.
"""

import logging
import time
import os
from typing import List, Dict
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException, TimeoutException
from webdriver_manager.chrome import ChromeDriverManager

logger = logging.getLogger(__name__)


class ChartinkScraper:
    """Scraper for Chartink stock screeners"""

    SCREENER_URLS = {
        "within-2-52week": "https://chartink.com/screener/within-2-of-52-week-highs-chartitude",
        "stage-2-trend": "https://chartink.com/screener/stage-2-trend-template"
    }

    MAX_PAGES = 20  # Safety limit
    PAGE_LOAD_TIME = 15  # Initial page load wait (seconds)
    PAGE_CHANGE_WAIT = 15  # Max wait for pagination (seconds)

    def __init__(self):
        """Initialize scraper with headless Chrome"""
        self.driver = None

    def _setup_driver(self):
        """Setup headless Chrome driver"""
        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless=new")  # Use new headless mode
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")  # Avoid detection
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")

            # Fix Windows webdriver-manager bug that returns wrong file path
            driver_path = ChromeDriverManager().install()
            logger.info(f"ChromeDriverManager returned: {driver_path}")

            # On Windows, ensure we have the actual chromedriver.exe
            if os.name == 'nt':
                # If path doesn't end with .exe or points to wrong file
                if not driver_path.endswith('.exe') or 'THIRD_PARTY' in driver_path:
                    driver_dir = os.path.dirname(driver_path)
                    chromedriver_exe = os.path.join(driver_dir, 'chromedriver.exe')

                    if os.path.exists(chromedriver_exe):
                        driver_path = chromedriver_exe
                        logger.info(f"Fixed ChromeDriver path: {driver_path}")
                    else:
                        # Search in parent directory
                        parent_files = os.listdir(driver_dir)
                        logger.error(f"chromedriver.exe not found. Directory contents: {parent_files}")
                        raise FileNotFoundError(
                            f"chromedriver.exe not found in {driver_dir}. "
                            f"Found files: {parent_files}"
                        )

                # Verify the file is executable (not THIRD_PARTY_NOTICES)
                if not os.access(driver_path, os.X_OK):
                    logger.warning(f"Driver path not executable: {driver_path}")
                    # Try to find chromedriver.exe in the same directory
                    driver_dir = os.path.dirname(driver_path)
                    chromedriver_exe = os.path.join(driver_dir, 'chromedriver.exe')
                    if os.path.exists(chromedriver_exe):
                        driver_path = chromedriver_exe
                        logger.info(f"Using executable: {driver_path}")

            service = Service(driver_path)
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            logger.info("Chrome driver initialized successfully")
        except Exception as e:
            logger.error(f"Failed to setup Chrome driver: {e}")
            raise

    def _teardown_driver(self):
        """Close and cleanup driver"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("Chrome driver closed")
            except Exception as e:
                logger.warning(f"Error closing driver: {e}")
            finally:
                self.driver = None

    def _enabled_next_buttons(self, attempts: int = 5):
        """Enabled, visible 'Next' buttons. The table re-renders right after a page change, so elements can go stale
        mid-scan; retry instead of treating that as the end of pagination (which silently truncated the results)."""
        for attempt in range(attempts):
            try:
                found = []
                for btn in self.driver.find_elements(By.TAG_NAME, "button"):
                    if 'next' not in btn.text.strip().lower():
                        continue
                    is_disabled = (
                        btn.get_attribute('disabled') == 'true' or
                        btn.get_attribute('disabled') == 'disabled' or
                        btn.get_attribute('aria-disabled') == 'true'
                    )
                    if not is_disabled and btn.is_displayed():
                        found.append(btn)
                return found
            except StaleElementReferenceException:
                if attempt == attempts - 1:
                    raise
                time.sleep(1)
        return []

    def scrape_screener(self, url: str, source_name: str) -> List[Dict]:
        """
        Scrape a single Chartink screener with pagination support.

        Args:
            url: Chartink screener URL
            source_name: Source identifier (e.g., 'within-2-52week')

        Returns:
            List of dicts with symbol and source
        """
        results = []
        seen_symbols = set()  # Track symbols to avoid page duplicates

        try:
            logger.info(f"Starting scrape of {source_name}: {url}")
            self.driver.get(url)

            # Wait for JavaScript to fully render the page
            logger.info(f"Waiting {self.PAGE_LOAD_TIME}s for page to load...")
            time.sleep(self.PAGE_LOAD_TIME)

            self.last_scrape_incomplete = False  # set True if paging ends for any reason other than the last page
            page_num = 1
            while page_num <= self.MAX_PAGES:
                logger.info(f"Scraping page {page_num} of {source_name}")

                # Find table with cluster-table class (new Chartink structure)
                try:
                    table = self.driver.find_element(By.CSS_SELECTOR, "table[class*='cluster-table']")
                except NoSuchElementException:
                    logger.error(f"Table not found for {source_name}")
                    break

                # Parse current page
                rows = table.find_elements(By.TAG_NAME, "tr")
                page_symbols = []
                stocks_this_page = 0

                # Skip header row (index 0)
                for row in rows[1:]:
                    try:
                        cells = row.find_elements(By.TAG_NAME, "td")
                        if len(cells) >= 3:
                            # Symbol is in 3rd column (index 2)
                            symbol = cells[2].text.strip()

                            if symbol and symbol.isupper() and symbol != 'SYMBOL':
                                page_symbols.append(symbol)

                                # Only add if not seen before (avoid duplicates)
                                if symbol not in seen_symbols:
                                    results.append({
                                        "symbol": symbol,
                                        "source": source_name
                                    })
                                    seen_symbols.add(symbol)
                                    stocks_this_page += 1
                    except Exception as e:
                        logger.warning(f"Error parsing row: {e}")
                        continue

                logger.info(f"Extracted {stocks_this_page} new stocks from page {page_num}")

                # If no new stocks found, we've reached the end
                if stocks_this_page == 0 and page_num > 1:
                    logger.info(f"No new stocks on page {page_num} - reached end")
                    break

                # Store first symbol to detect page change
                current_first_symbol = page_symbols[0] if page_symbols else None

                # Try to find and click Next button
                try:
                    next_buttons = self._enabled_next_buttons()

                    if not next_buttons:
                        logger.info(f"No enabled Next button found - last page")
                        break

                    # Click first enabled Next button with JavaScript
                    next_button = next_buttons[0]
                    logger.info(f"Clicking Next button...")
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_button)
                    time.sleep(0.5)
                    self.driver.execute_script("arguments[0].click();", next_button)

                    # Wait for page to change
                    logger.info(f"Waiting for page to update...")
                    page_changed = False

                    for i in range(self.PAGE_CHANGE_WAIT):
                        time.sleep(1)
                        try:
                            table = self.driver.find_element(By.CSS_SELECTOR, "table[class*='cluster-table']")
                            rows = table.find_elements(By.TAG_NAME, "tr")
                            if len(rows) > 1:
                                cells = rows[1].find_elements(By.TAG_NAME, "td")
                                if len(cells) >= 3:
                                    new_first_symbol = cells[2].text.strip()
                                    if new_first_symbol and new_first_symbol != current_first_symbol:
                                        logger.info(f"Page changed: {current_first_symbol} -> {new_first_symbol}")
                                        page_changed = True
                                        break
                        except:
                            pass

                    if not page_changed:
                        logger.warning(f"Page did not change - stopping (results may be incomplete)")
                        self.last_scrape_incomplete = True
                        break

                    page_num += 1

                except Exception as e:
                    logger.warning(f"Pagination ended abnormally: {str(e)[:100]} (results may be incomplete)")
                    self.last_scrape_incomplete = True
                    break

            if page_num > self.MAX_PAGES:
                logger.warning(f"Hit max page limit ({self.MAX_PAGES}) for {source_name}")
                self.last_scrape_incomplete = True

            logger.info(f"Completed scraping {source_name}: {len(results)} stocks found")
            return results

        except Exception as e:
            logger.error(f"Error scraping {source_name}: {e}")
            return []

    def _deduplicate_stocks(self, stocks: List[Dict]) -> List[Dict]:
        """
        Remove duplicate stocks that appear in multiple screeners.
        Keeps first occurrence and tracks sources.

        Args:
            stocks: List of stock dicts with 'symbol' and 'source'

        Returns:
            List of unique stocks
        """
        seen_symbols = set()
        unique_stocks = []

        for stock in stocks:
            symbol = stock["symbol"]
            if symbol not in seen_symbols:
                seen_symbols.add(symbol)
                unique_stocks.append(stock)

        # Log deduplication stats
        if len(stocks) != len(unique_stocks):
            duplicates = len(stocks) - len(unique_stocks)
            logger.info(f"Removed {duplicates} duplicate stocks. Unique: {len(unique_stocks)}")

        return unique_stocks

    def scrape_both_screeners(self) -> Dict[str, any]:
        """
        Scrape both Chartink screener URLs and deduplicate results.

        Returns:
            Dict with:
            - 'stocks': list of unique stocks (duplicates removed)
            - 'total_scraped': total stocks before deduplication
            - 'unique_count': stocks after deduplication
            - 'errors': list of error messages
        """
        all_results = []
        errors = []

        try:
            self._setup_driver()

            for source_name, url in self.SCREENER_URLS.items():
                try:
                    results = self.scrape_screener(url, source_name)
                    all_results.extend(results)

                    # Polite delay between screeners
                    if source_name != list(self.SCREENER_URLS.keys())[-1]:
                        logger.info("Waiting 3 seconds before next screener...")
                        time.sleep(3)

                except Exception as e:
                    error_msg = f"Failed to scrape {source_name}: {str(e)}"
                    logger.error(error_msg)
                    errors.append(error_msg)

            # Deduplicate across screeners
            total_scraped = len(all_results)
            unique_stocks = self._deduplicate_stocks(all_results)

            return {
                "stocks": unique_stocks,
                "total_scraped": total_scraped,
                "unique_count": len(unique_stocks),
                "errors": errors
            }

        finally:
            self._teardown_driver()

    def scrape_single_screener(self, source_name: str) -> Dict[str, any]:
        """
        Scrape a single screener by name.

        Args:
            source_name: One of 'within-2-52week' or 'stage-2-trend'

        Returns:
            Dict with 'stocks' and 'errors'
        """
        if source_name not in self.SCREENER_URLS:
            return {
                "stocks": [],
                "errors": [f"Invalid source: {source_name}"]
            }

        try:
            self._setup_driver()
            url = self.SCREENER_URLS[source_name]
            results = self.scrape_screener(url, source_name)

            return {
                "stocks": results,
                "errors": []
            }
        except Exception as e:
            return {
                "stocks": [],
                "errors": [str(e)]
            }
        finally:
            self._teardown_driver()
