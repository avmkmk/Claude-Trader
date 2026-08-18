"""
TradingView CLI Integration Service

Wrapper for TradingView CLI commands to fetch fundamental data including market cap.
Uses the tradingview-mcp-server CLI (fiale-plus) to retrieve data from TradingView.

SETUP REQUIRED:
1. Install TradingView CLI:
   npm install -g tradingview-mcp-server

2. Test CLI:
   tradingview-cli --version

3. Usage:
   tradingview-cli lookup NSE:RELIANCE --format json
"""

import subprocess
import json
import logging
import os
import shutil
from typing import Optional, Dict, Literal, List
from pathlib import Path

logger = logging.getLogger(__name__)


class TradingViewCLI:
    """
    Wrapper for TradingView CLI to fetch fundamental data.

    Uses tradingview-cli commands (from tradingview-mcp-server package)
    to get market cap, ATH, 52-week high/low data for Indian equity stocks (NSE exchange).
    """

    # Market cap thresholds (in crores INR)
    LARGE_CAP_MIN = 20000  # >= 20,000 cr
    MID_CAP_MIN = 5000     # 5,000 - 20,000 cr
    # < 5,000 cr = small cap

    def __init__(self):
        """Initialize TradingView CLI wrapper"""
        self.cli_path = self._find_cli_executable()
        self.cli_available = self.cli_path is not None
        if not self.cli_available:
            logger.warning("TradingView CLI not installed. Run: npm install -g tradingview-mcp-server")
        else:
            logger.info(f"TradingView CLI found at: {self.cli_path}")

    def _find_cli_executable(self) -> Optional[str]:
        """
        Find the tradingview-cli executable.

        Checks common npm global install locations on Windows.

        Returns:
            Path to executable, or None if not found
        """
        # First try to find it in PATH
        cli_path = shutil.which("tradingview-cli")
        if cli_path:
            return cli_path

        # Check common Windows npm global install locations
        possible_paths = [
            os.path.join(os.environ.get("APPDATA", ""), "npm", "tradingview-cli.cmd"),
            os.path.join(os.environ.get("APPDATA", ""), "npm", "tradingview-cli"),
            "C:\\Program Files\\nodejs\\tradingview-cli.cmd",
            "C:\\Program Files\\nodejs\\tradingview-cli",
        ]

        for path in possible_paths:
            if os.path.exists(path):
                return path

        return None


    def get_fundamentals(self, symbol: str) -> Optional[Dict]:
        """
        Execute TradingView CLI to get fundamental data for a stock.

        Uses tradingview-cli lookup command to fetch market cap and price data.

        CLI Command Format:
        tradingview-cli lookup NSE:SYMBOL --format json

        Args:
            symbol: Stock symbol (e.g., 'RELIANCE')

        Returns:
            Dict with keys:
            - symbol: Full symbol (NSE:SYMBOL)
            - name: Stock name
            - close: Current close price
            - market_cap_basic: Market cap in lakhs
            - all_time_high: All-time high price
            - price_52_week_high: 52-week high
            - price_52_week_low: 52-week low
            Returns None if CLI not available or command fails

        Example Output:
        {
            "symbol": "NSE:RELIANCE",
            "name": "RELIANCE",
            "close": 1323.9,
            "market_cap_basic": 188198211605.625,
            "all_time_high": 1611.8,
            "price_52_week_high": 1611.8,
            "price_52_week_low": 1249.8
        }
        """
        if not self.cli_available:
            logger.warning(f"TradingView CLI not available, cannot fetch data for {symbol}")
            return None

        # Build CLI command using full path
        cmd = [
            self.cli_path, "lookup",
            f"NSE:{symbol}",
            "--format", "json"
        ]

        try:
            logger.info(f"Fetching fundamentals for {symbol} via TradingView CLI...")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30  # 30 second timeout
            )

            if result.returncode != 0:
                logger.error(f"TradingView CLI failed for {symbol}: {result.stderr}")
                return None

            # Parse JSON output
            try:
                data = json.loads(result.stdout)

                # Extract first symbol from results
                if data.get('symbols') and len(data['symbols']) > 0:
                    symbol_data = data['symbols'][0]
                    logger.info(f"Retrieved fundamentals for {symbol}: marketCap={symbol_data.get('market_cap_basic')}")
                    return symbol_data
                else:
                    logger.warning(f"No data found for {symbol}")
                    return None

            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse TradingView CLI output for {symbol}: {e}")
                logger.debug(f"CLI output was: {result.stdout}")
                return None

        except subprocess.TimeoutExpired:
            logger.error(f"TradingView CLI timeout for {symbol}")
            return None
        except FileNotFoundError:
            logger.error("TradingView CLI not found in PATH")
            self.cli_available = False
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching fundamentals for {symbol}: {e}")
            return None

    def get_market_cap_crores(self, symbol: str) -> Optional[float]:
        """
        Get market cap in crores INR.

        TradingView's market_cap_basic is in units where:
        market_cap_basic = market_cap_crores * 100,000

        Example: RELIANCE
        - market_cap_basic: 188,198,211,605.625
        - Actual market cap: ₹1,881,982 crores
        - Conversion: 188,198,211,605.625 / 100,000 = 1,881,982.12 crores ✓

        Args:
            symbol: Stock symbol

        Returns:
            Market cap in crores (1 crore = 10 million), or None if unavailable
        """
        fundamentals = self.get_fundamentals(symbol)
        if fundamentals and 'market_cap_basic' in fundamentals:
            market_cap_basic = fundamentals['market_cap_basic']
            # Convert to crores: market_cap_basic is in units of 0.00001 crores
            market_cap_cr = market_cap_basic / 100000
            return round(market_cap_cr, 2)
        return None

    def classify_cap_size(self, market_cap_cr: float) -> Literal['large', 'mid', 'small']:
        """
        Classify stock by market cap size.

        Args:
            market_cap_cr: Market cap in crores

        Returns:
            'large' if >= 20,000 cr
            'mid' if 5,000 - 20,000 cr
            'small' if < 5,000 cr
        """
        if market_cap_cr >= self.LARGE_CAP_MIN:
            return 'large'
        elif market_cap_cr >= self.MID_CAP_MIN:
            return 'mid'
        else:
            return 'small'

    def is_small_cap(self, symbol: str) -> bool:
        """
        Check if a stock is small cap (< 5,000 crores).

        Args:
            symbol: Stock symbol

        Returns:
            True if small cap, False if large/mid cap or data unavailable
        """
        market_cap_cr = self.get_market_cap_crores(symbol)
        if market_cap_cr is None:
            # Default to NOT filtering if data unavailable
            logger.warning(f"Could not determine market cap for {symbol}, not filtering")
            return False
        return market_cap_cr < self.MID_CAP_MIN

    def get_stock_info(self, symbol: str) -> Optional[Dict]:
        """
        Get complete stock information including market cap classification.

        Args:
            symbol: Stock symbol

        Returns:
            Dict with:
            - symbol: Stock symbol
            - market_cap_basic: Market cap in lakhs
            - market_cap_cr: Market cap in crores
            - cap_size: 'large', 'mid', or 'small'
            - is_small_cap: Boolean
            - all_time_high: All-time high price
            - price_52_week_high: 52-week high
            - price_52_week_low: 52-week low
            - sector: None (not available from this CLI)
            - industry: None (not available from this CLI)
            Returns None if data unavailable
        """
        fundamentals = self.get_fundamentals(symbol)
        if not fundamentals:
            return None

        market_cap_basic = fundamentals.get('market_cap_basic', 0)
        market_cap_cr = market_cap_basic / 100000 if market_cap_basic else 0

        return {
            'symbol': symbol,
            'market_cap_basic': market_cap_basic,
            'market_cap_cr': round(market_cap_cr, 2),
            'cap_size': self.classify_cap_size(market_cap_cr),
            'is_small_cap': market_cap_cr < self.MID_CAP_MIN,
            'all_time_high': fundamentals.get('all_time_high'),
            'price_52_week_high': fundamentals.get('price_52_week_high'),
            'price_52_week_low': fundamentals.get('price_52_week_low'),
            'current_price': fundamentals.get('close'),
            'sector': None,  # Not available from tradingview-cli lookup
            'industry': None  # Not available from tradingview-cli lookup
        }


# Singleton instance
tradingview_cli = TradingViewCLI()
