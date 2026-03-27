"""
Batch scrape historical data for multiple Nifty 50 symbols
Usage: python scripts/batch_data_scraper.py
"""

from apis.nubra_api import NubraAPIHandler
from backtesting.data_scraper import EquityDataScraper

# Nifty 50 stocks: high liquidity, sector diversity
SYMBOLS = [
    'RELIANCE',    # Energy (50+ lakh vol)
    'INFY',        # IT (30+ lakh vol)
    'HDFCBANK',    # Banking (40+ lakh vol)
    'TCS',         # IT (25+ lakh vol)
    'ICICIBANK',   # Banking (35+ lakh vol)
    'BHARTIARTL',  # Telecom (30+ lakh vol)
    'ITC',         # FMCG (40+ lakh vol)
    'TATASTEEL',   # Metals (25+ lakh vol)
    'SBIN',        # Banking (50+ lakh vol)
    'WIPRO',       # IT (20+ lakh vol)
]

def main():
    # Initialize
    nubra = NubraAPIHandler()
    success = nubra.initialize_sdk()

    if not success:
        print("ERROR: Failed to initialize Nubra SDK")
        print("Please ensure .env file contains valid credentials:")
        print("  NUBRA_CLIENT_ID=your_client_id")
        print("  NUBRA_MPIN=your_mpin")
        return

    scraper = EquityDataScraper(nubra)

    print(f"Starting batch scrape for {len(SYMBOLS)} symbols...")
    print(f"Period: 365 days")
    print(f"Rate limit: 2 seconds between requests (60 req/min)")

    # Batch scrape with 365-day period
    scraper.scrape_batch(
        symbols=SYMBOLS,
        delay_seconds=2,
        period_days=365
    )

    print("\nBatch scraping complete!")
    print(f"Data saved to data/ directory")

if __name__ == '__main__':
    main()
