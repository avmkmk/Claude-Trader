"""
Test the updated production chartink_scraper.py
"""
import sys
sys.path.insert(0, '.')

from app.services.chartink_scraper import ChartinkScraper

print("Testing production Chartink scraper...")
print("="*60)

scraper = ChartinkScraper()
result = scraper.scrape_both_screeners()

stocks = result.get("stocks", [])
total_scraped = result.get("total_scraped", 0)
unique_count = result.get("unique_count", 0)
errors = result.get("errors", [])

print(f"\n{'='*60}")
print("SCRAPING RESULTS")
print(f"{'='*60}")
print(f"Total scraped: {total_scraped} stocks")
print(f"Duplicates removed: {total_scraped - unique_count}")
print(f"Unique stocks: {unique_count}")
print(f"Errors: {len(errors)}")

if errors:
    print(f"\nErrors encountered:")
    for error in errors:
        print(f"  - {error}")

if stocks:
    # Group by source
    within_2 = [s for s in stocks if s['source'] == 'within-2-52week']
    stage_2 = [s for s in stocks if s['source'] == 'stage-2-trend']

    print(f"\nBreakdown by source:")
    print(f"  - within-2-52week: {len(within_2)} stocks")
    print(f"  - stage-2-trend: {len(stage_2)} stocks")

    print(f"\nFirst 10 unique stocks:")
    for i, stock in enumerate(stocks[:10], 1):
        print(f"  {i:2d}. {stock['symbol']:20s} [{stock['source']}]")

    if len(stocks) > 10:
        print(f"  ... and {len(stocks) - 10} more")
else:
    print("\n❌ NO STOCKS FOUND")

print(f"\n{'='*60}")
if unique_count >= 100:
    print("✅ SUCCESS - Scraper is working!")
else:
    print("❌ FAILED - Insufficient stocks scraped")
print(f"{'='*60}")
