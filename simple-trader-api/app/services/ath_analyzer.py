"""
ATH Analyzer Service

Analyzes stocks for ATH (All-Time High) reclaim patterns.
Determines phase and status labels based on EMA 200 and distance from ATH.
"""

import logging
import os
import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class ATHAnalyzer:
    """Analyzer for ATH reclaim strategy phase detection"""

    def __init__(self, data_path: Optional[str] = None):
        """
        Initialize ATH Analyzer.

        Args:
            data_path: Path to historical data directory. If None, uses default.
        """
        if data_path is None:
            # Default path from spec: SimpleTraderExternal/data/daily/eod2/
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
            self.data_path = os.path.join(base_dir, "..", "SimpleTraderExternal", "data", "daily", "eod2")
        else:
            self.data_path = data_path

        logger.info(f"ATHAnalyzer initialized with data path: {self.data_path}")

    def _load_data(self, symbol: str) -> Optional[pd.DataFrame]:
        """
        Load historical data for a symbol.

        Args:
            symbol: Stock symbol (e.g., 'RELIANCE')

        Returns:
            DataFrame with OHLCV data, or None if not found
        """
        try:
            csv_path = os.path.join(self.data_path, f"{symbol}.csv")

            if not os.path.exists(csv_path):
                logger.warning(f"Data file not found for {symbol}: {csv_path}")
                return None

            # Load CSV
            df = pd.read_csv(csv_path)

            # Ensure required columns exist
            required_cols = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
            if not all(col in df.columns for col in required_cols):
                logger.error(f"Missing required columns in {symbol} data")
                return None

            # Parse date and sort
            df['Date'] = pd.to_datetime(df['Date'])
            df = df.sort_values('Date').reset_index(drop=True)

            logger.info(f"Loaded {len(df)} rows for {symbol}")
            return df

        except Exception as e:
            logger.error(f"Error loading data for {symbol}: {e}")
            return None

    def _calculate_ema(self, df: pd.DataFrame, period: int = 200) -> pd.Series:
        """
        Calculate Exponential Moving Average.

        Args:
            df: DataFrame with 'Close' column
            period: EMA period (default 200)

        Returns:
            Series with EMA values
        """
        return df['Close'].ewm(span=period, adjust=False).mean()

    def _find_ath(self, df: pd.DataFrame) -> Tuple[float, str]:
        """
        Find all-time high and its date.

        Args:
            df: DataFrame with 'High' and 'Date' columns

        Returns:
            Tuple of (ath_value, ath_date)
        """
        max_idx = df['High'].idxmax()
        ath_value = df.loc[max_idx, 'High']
        ath_date = df.loc[max_idx, 'Date'].strftime('%Y-%m-%d')

        return ath_value, ath_date

    def _determine_phase_and_status(
        self,
        current_price: float,
        ema_200: float,
        ath_value: float
    ) -> Tuple[int, str]:
        """
        Determine phase based on ATH Reclaim Strategy.

        Phase Logic:
        - Phase 1: At ATH (within 2% of ATH or above)
        - Phase 2: Below EMA 200 (consolidation)
        - Phase 3: Above EMA 200, approaching ATH (entry setup)

        Args:
            current_price: Current close price
            ema_200: EMA 200 value
            ath_value: All-time high value

        Returns:
            Tuple of (phase: int, status_label: str)
        """
        # Calculate distance from ATH (percentage)
        distance_pct = ((current_price - ath_value) / ath_value) * 100

        # Phase 1: At or near ATH (within 2% of ATH)
        # This includes stocks making new ATHs (price > ath_value)
        if distance_pct >= -2.0:
            return (1, "Phase 1 (At ATH)")

        # Phase 2: Consolidation (below EMA 200)
        if current_price < ema_200:
            return (2, "Phase 2 (Consolidation)")

        # Phase 3: Entry Setup (above EMA 200, more than 2% below ATH)
        # This is the sweet spot - stock has finished consolidation and is recovering
        if current_price >= ema_200:
            return (3, "Phase 3 (Entry Setup)")

        # Fallback to Phase 2 (shouldn't normally reach here)
        return (2, "Phase 2 (Consolidation)")

    def analyze_symbol(self, symbol: str) -> Optional[Dict]:
        """
        Analyze single stock for ATH reclaim phase.

        Phase Logic:
        - Phase 1: At ATH (within 2% of ATH or making new highs)
        - Phase 2: Below EMA 200 (consolidation/pullback)
        - Phase 3: Above EMA 200, approaching ATH (entry setup - TARGET)

        Args:
            symbol: Stock symbol (e.g., 'RELIANCE')

        Returns:
            Dict with phase, status_label, ATH metrics, or None if analysis failed
        """
        try:
            logger.info(f"Analyzing {symbol}...")

            # Load data
            df = self._load_data(symbol)
            if df is None or len(df) < 200:
                logger.warning(f"Insufficient data for {symbol} (need at least 200 days)")
                return None

            # Calculate EMA 200
            df['EMA_200'] = self._calculate_ema(df, period=200)

            # Get latest values
            latest = df.iloc[-1]
            current_price = float(latest['Close'])
            ema_200 = float(latest['EMA_200'])

            # Find ATH
            ath_value, ath_date = self._find_ath(df)

            # Determine phase
            phase, status_label = self._determine_phase_and_status(
                current_price,
                ema_200,
                ath_value
            )

            # Calculate distance from ATH (percentage)
            distance_from_ath = ((current_price - ath_value) / ath_value) * 100

            result = {
                'symbol': symbol,
                'phase': phase,
                'status_label': status_label,
                'ath_value': float(ath_value),
                'ath_date': ath_date,
                'current_price': current_price,
                'ema_200': ema_200,
                'distance_from_ath': distance_from_ath,
                'last_analyzed': datetime.now().isoformat()
            }

            logger.info(
                f"{symbol} → {status_label} "
                f"(Distance: {distance_from_ath:.2f}%, EMA200: {ema_200:.2f})"
            )

            return result

        except Exception as e:
            logger.error(f"Error analyzing {symbol}: {e}")
            return None

    def analyze_multiple(self, symbols: list) -> Dict[str, Optional[Dict]]:
        """
        Analyze multiple symbols.

        Args:
            symbols: List of stock symbols

        Returns:
            Dict mapping symbol to analysis result (or None if failed)
        """
        results = {}

        for symbol in symbols:
            try:
                result = self.analyze_symbol(symbol)
                results[symbol] = result
            except Exception as e:
                logger.error(f"Failed to analyze {symbol}: {e}")
                results[symbol] = None

        return results
