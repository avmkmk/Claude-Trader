"""
Nubra Broker API Handler

Provides integration with Nubra broker for:
- Historical data fetching (equities and F&O)
- Real-time WebSocket data
- Trading operations

Usage:
    handler = NubraAPIHandler()
    handler.initialize_sdk()
    df = handler.get_historical_data('RELIANCE', '2024-01-01', '2024-03-01', '1d')
"""

import datetime
import pandas as pd
from nubra_python_sdk.start_sdk import InitNubraSdk, NubraEnv
from nubra_python_sdk.marketdata.market_data import MarketData
from nubra_python_sdk.trading.trading_data import NubraTrader as Trading
from nubra_python_sdk.ticker.websocketdata import NubraDataSocket


class NubraAPIHandler:
    """
    Handler class for Nubra broker API operations.
    
    Provides methods for fetching historical data, connecting to WebSocket,
    and accessing trading functionality through the Nubra SDK.
    """
    def __init__(self, env=NubraEnv.PROD):
        """
        Initialize the Nubra API handler.
        
        Args:
            env: Nubra environment (default: PROD)
        """
        self.env = env
        self.sdk_instance = None
        self.market_data_api = None
        self.trading_api = None
        self.ws_client = None

    def initialize_sdk(self):
        """
        Initialize the Nubra SDK and API clients.
        
        Returns:
            bool: True if initialization successful, False otherwise
        """
        try:
            self.sdk_instance = InitNubraSdk(self.env, env_creds=True)
            self.market_data_api = MarketData(self.sdk_instance)
            self.trading_api = Trading(self.sdk_instance)
            return True
        except Exception as e:
            print(f"Error initializing Nubra SDK: {e}")
            return False

    def get_historical_data(self, instrument_key, from_date, to_date, interval):
        """Wrapper around MarketData.historical_data that returns a pandas DataFrame.

        interval: '1m', '5m', '15m', '30m', '1h', '4h', '1d' (also accepts legacy: 'minute','hour','days')
        from_date/to_date strings in 'YYYY-MM-DD' or 'YYYY-MM-DD HH:MM'
        """
        if not self.market_data_api:
            print("Nubra MarketData API not initialized.")
            return None

        try:
            from_datetime = datetime.datetime.strptime(from_date, '%Y-%m-%d %H:%M') if ' ' in from_date else datetime.datetime.strptime(from_date, '%Y-%m-%d')
            to_datetime = datetime.datetime.strptime(to_date, '%Y-%m-%d %H:%M') if ' ' in to_date else datetime.datetime.strptime(to_date, '%Y-%m-%d')

            # Support both new interval format and legacy format
            nubra_interval_map = {
                'minute': '1m',
                'hour': '1h',
                'days': '1d',
                # Direct format (new)
                '1m': '1m',
                '5m': '5m',
                '15m': '15m',
                '30m': '30m',
                '1h': '1h',
                '4h': '4h',
                '1d': '1d'
            }
            nubra_interval = nubra_interval_map.get(interval, '1d')

            symbol = str(instrument_key).split('-')[0].upper()
            request_payload = {
                "exchange": "NSE",
                "type": "STOCK",
                "values": [symbol],
                "fields": ["open", "high", "low", "close", "cumulative_volume"],
                "startDate": from_datetime.strftime('%Y-%m-%dT%H:%M:%SZ'),
                "endDate": to_datetime.strftime('%Y-%m-%dT%H:%M:%SZ'),
                "interval": nubra_interval,
                "intraDay": False,
                "realTime": False
            }

            api_response = self.market_data_api.historical_data(request_payload)
            if not api_response or not getattr(api_response, 'result', None):
                return None

            first_result = api_response.result[0]
            if not first_result.values:
                return None

            symbol_map = first_result.values[0]
            _, chart = next(iter(symbol_map.items()))

            series_map = {}
            for field in ['open', 'high', 'low', 'close', 'cumulative_volume']:
                pts = getattr(chart, field, [])
                d = {(p.timestamp or p.ts): (p.value or p.v) for p in (pts or []) if (p.timestamp or p.ts) is not None}
                if d:
                    s = pd.Series(d)
                    s.index = pd.to_datetime(s.index, unit='ns', utc=True).tz_convert('Asia/Kolkata')
                    series_map[field] = s

            if not series_map:
                return None

            df = pd.DataFrame(series_map)
            df = df.rename(columns={'cumulative_volume': 'volume'})
            df = df[['open', 'high', 'low', 'close', 'volume']]
            df = df.sort_index()
            return df

        except Exception as e:
            print(f"Error fetching Nubra historical data: {e}")
            return None

    def connect_websocket(self, on_message=None):
        if not self.sdk_instance:
            print("SDK not initialized")
            return False
        socket = NubraDataSocket(self.sdk_instance, on_market_data=on_message, on_index_data=on_message)
        socket.connect()
        self.ws_client = socket
        return True

    def get_3months_equity(self, symbol='GRAPHITE'):
        """Fetch last 90 days daily OHLCV for an equity symbol."""
        today = datetime.datetime.utcnow().date()
        start = today - datetime.timedelta(days=90)
        from_date = start.strftime('%Y-%m-%d')
        to_date = today.strftime('%Y-%m-%d')
        return self.get_historical_data(symbol, from_date, to_date, 'days')

    def get_1year_equity(self, symbol='GRAPHITE'):
        """Fetch last 365 days (1 year) daily OHLCV for an equity symbol."""
        today = datetime.datetime.utcnow().date()
        start = today - datetime.timedelta(days=365)
        from_date = start.strftime('%Y-%m-%d')
        to_date = today.strftime('%Y-%m-%d')
        return self.get_historical_data(symbol, from_date, to_date, 'days')

    # ─── F&O / Derivatives Support ───────────────────────────────────────────

    def get_fno_historical_data(
        self, symbol, from_date, to_date, interval='1d',
        instrument_type='OPT', fields=None
    ):
        """Fetch historical data for F&O instruments (options/futures).

        Args:
            symbol: Option/futures symbol string.
                Options: 'NIFTY2611326000CE', 'BANKNIFTY25D2348000PE'
                Futures: 'NIFTY26MARFUT', 'BANKNIFTY26MARFUT'
            from_date: Start date 'YYYY-MM-DD' or 'YYYY-MM-DD HH:MM'
            to_date: End date 'YYYY-MM-DD' or 'YYYY-MM-DD HH:MM'
            interval: '1m', '5m', '15m', '30m', '1h', '4h', '1d', '1w', '1mt'
            instrument_type: 'OPT' for options, 'FUT' for futures
            fields: List of fields to fetch. Defaults to OHLCV + Greeks + OI.

        Returns:
            pandas DataFrame with datetime index, or None if failed.

        Note:
            Intraday intervals (< 1d) are limited to ~3 months lookback.
            Daily+ intervals can go further back.
            Nubra rate limit: 60 requests/minute. This method makes 1 request.
        """
        if not self.market_data_api:
            print("Nubra MarketData API not initialized.")
            return None

        if fields is None:
            fields = [
                "open", "high", "low", "close", "cumulative_volume",
                "theta", "delta", "gamma", "vega", "iv_mid",
                "cumulative_oi"
            ]

        try:
            from_dt = self._parse_date(from_date)
            to_dt = self._parse_date(to_date)

            nubra_interval_map = {
                '1m': '1m', '5m': '5m', '15m': '15m', '30m': '30m',
                '1h': '1h', '4h': '4h', '1d': '1d', '1w': '1w', '1mt': '1mt',
                'minute': '1m', 'hour': '1h', 'days': '1d',
            }
            nubra_interval = nubra_interval_map.get(interval, '1d')

            request_payload = {
                "exchange": "NSE",
                "type": instrument_type,
                "values": [symbol],
                "fields": fields,
                "startDate": from_dt.strftime('%Y-%m-%dT%H:%M:%SZ'),
                "endDate": to_dt.strftime('%Y-%m-%dT%H:%M:%SZ'),
                "interval": nubra_interval,
                "intraDay": False,
                "realTime": False
            }

            api_response = self.market_data_api.historical_data(request_payload)
            if not api_response or not getattr(api_response, 'result', None):
                return None

            first_result = api_response.result[0]
            if not first_result.values:
                return None

            symbol_map = first_result.values[0]
            _, chart = next(iter(symbol_map.items()))

            series_map = {}
            for field in fields:
                pts = getattr(chart, field, None)
                if pts:
                    d = {}
                    for p in pts:
                        ts = getattr(p, 'timestamp', None) or getattr(p, 'ts', None)
                        val = getattr(p, 'value', None) or getattr(p, 'v', None)
                        if ts is not None:
                            d[ts] = val
                    if d:
                        s = pd.Series(d)
                        s.index = pd.to_datetime(s.index, unit='ns', utc=True).tz_convert('Asia/Kolkata')
                        series_map[field] = s

            if not series_map:
                return None

            df = pd.DataFrame(series_map)
            col_rename = {'cumulative_volume': 'volume', 'cumulative_oi': 'open_interest'}
            df = df.rename(columns=col_rename)
            df = df.sort_index()
            return df

        except Exception as e:
            print(f"Error fetching F&O historical data for {symbol}: {e}")
            return None

    def get_fno_historical_batch(
        self, symbols, from_date, to_date, interval='1d',
        instrument_type='OPT', fields=None, delay_seconds=1.5
    ):
        """Fetch historical data for multiple F&O symbols with rate limiting.

        Args:
            symbols: List of option/futures symbol strings
            from_date: Start date 'YYYY-MM-DD'
            to_date: End date 'YYYY-MM-DD'
            interval: Timeframe interval
            instrument_type: 'OPT' or 'FUT'
            fields: Fields to fetch (defaults to OHLCV + Greeks + OI)
            delay_seconds: Delay between requests (default: 1.5s for 60 req/min)

        Returns:
            dict: {symbol: DataFrame} for symbols with data
        """
        import time as _time

        results = {}
        total = len(symbols)

        for idx, symbol in enumerate(symbols, 1):
            if idx % 10 == 0 or idx == 1:
                print(f"[F&O Batch] [{idx}/{total}] Fetching {symbol}...")

            df = self.get_fno_historical_data(
                symbol=symbol,
                from_date=from_date,
                to_date=to_date,
                interval=interval,
                instrument_type=instrument_type,
                fields=fields,
            )

            if df is not None and not df.empty:
                results[symbol] = df
            else:
                print(f"  No data for {symbol}")

            if idx < total:
                _time.sleep(delay_seconds)

        print(f"[F&O Batch] Complete: {len(results)}/{total} symbols fetched")
        return results

    def get_fno_historical_batch_multi(
        self, symbols, from_date, to_date, interval='1d',
        instrument_type='OPT', fields=None, batch_size=10, delay_seconds=1.5
    ):
        """Fetch historical data for multiple F&O symbols in batches of N per request.

        Sends up to `batch_size` symbols in a single API call instead of
        one request per symbol. Much faster than get_fno_historical_batch.

        Args:
            symbols: List of option/futures symbol strings
            from_date: Start date 'YYYY-MM-DD'
            to_date: End date 'YYYY-MM-DD'
            interval: Timeframe interval ('5m', '15m', '1d', etc.)
            instrument_type: 'OPT' or 'FUT'
            fields: Fields to fetch (defaults to OHLCV + Greeks + OI)
            batch_size: Symbols per request (default: 20)
            delay_seconds: Delay between batch requests (default: 1.5s)

        Returns:
            dict: {symbol: DataFrame} for symbols with data
        """
        import time as _time

        if fields is None:
            fields = [
                "open", "high", "low", "close", "cumulative_volume",
                "theta", "delta", "gamma", "vega", "iv_mid",
                "cumulative_oi"
            ]

        from_dt = self._parse_date(from_date)
        to_dt = self._parse_date(to_date)

        nubra_interval_map = {
            '1m': '1m', '5m': '5m', '15m': '15m', '30m': '30m',
            '1h': '1h', '4h': '4h', '1d': '1d', '1w': '1w', '1mt': '1mt',
        }
        nubra_interval = nubra_interval_map.get(interval, '1d')

        results = {}
        total = len(symbols)
        batches = [symbols[i:i + batch_size] for i in range(0, total, batch_size)]

        for batch_idx, batch_symbols in enumerate(batches, 1):
            print(f"  Batch [{batch_idx}/{len(batches)}] ({len(batch_symbols)} symbols)...")

            try:
                request_payload = {
                    "exchange": "NSE",
                    "type": instrument_type,
                    "values": batch_symbols,
                    "fields": fields,
                    "startDate": from_dt.strftime('%Y-%m-%dT%H:%M:%SZ'),
                    "endDate": to_dt.strftime('%Y-%m-%dT%H:%M:%SZ'),
                    "interval": nubra_interval,
                    "intraDay": False,
                    "realTime": False
                }

                api_response = self.market_data_api.historical_data(request_payload)

                if not api_response or not getattr(api_response, 'result', None):
                    print(f"    No response for batch {batch_idx}")
                    continue

                for result_item in api_response.result:
                    if not result_item.values:
                        continue
                    for symbol_map in result_item.values:
                        for sym_name, chart in symbol_map.items():
                            series_map = {}
                            for field in fields:
                                pts = getattr(chart, field, None)
                                if pts:
                                    d = {}
                                    for p in pts:
                                        ts = getattr(p, 'timestamp', None) or getattr(p, 'ts', None)
                                        val = getattr(p, 'value', None) or getattr(p, 'v', None)
                                        if ts is not None:
                                            d[ts] = val
                                    if d:
                                        s = pd.Series(d)
                                        s.index = pd.to_datetime(s.index, unit='ns', utc=True).tz_convert('Asia/Kolkata')
                                        series_map[field] = s

                            if series_map:
                                df = pd.DataFrame(series_map)
                                col_rename = {'cumulative_volume': 'volume', 'cumulative_oi': 'open_interest'}
                                df = df.rename(columns=col_rename)
                                df = df.sort_index()
                                results[sym_name] = df

                print(f"    Got data for {sum(1 for s in batch_symbols if s in results)}/{len(batch_symbols)} symbols")

            except Exception as e:
                print(f"    Error in batch {batch_idx}: {e}")

            if batch_idx < len(batches):
                _time.sleep(delay_seconds)

        print(f"[Batch Multi] Complete: {len(results)}/{total} symbols fetched")
        return results

    def get_option_chain(self, underlying, expiry=None, exchange="NSE"):
        """Fetch the current option chain snapshot for an underlying.

        Args:
            underlying: Underlying symbol, e.g., 'NIFTY', 'BANKNIFTY'
            expiry: Optional expiry date filter (format depends on SDK)
            exchange: Exchange, default 'NSE'

        Returns:
            SDK response object with strike-level calls/puts, OI, Greeks, IV.
            Access via result.option_chain or similar SDK attribute.
        """
        if not self.market_data_api:
            print("Nubra MarketData API not initialized.")
            return None

        try:
            kwargs = {"exchange": exchange}
            if expiry:
                kwargs["expiry"] = expiry

            result = self.market_data_api.option_chain(underlying, **kwargs)
            return result

        except Exception as e:
            print(f"Error fetching option chain for {underlying}: {e}")
            return None

    def get_fno_instruments(self, underlying, derivative_type="OPT", exchange="NSE"):
        """Get instrument metadata for F&O contracts.

        Args:
            underlying: Asset symbol, e.g., 'NIFTY', 'BANKNIFTY'
            derivative_type: 'OPT' for options, 'FUT' for futures
            exchange: Exchange, default 'NSE'

        Returns:
            pandas DataFrame of matching instruments with ref_id, expiry,
            strike_price, option_type, lot_size, etc.
        """
        try:
            from nubra_python_sdk.refdata.instruments import InstrumentData
            instruments = InstrumentData(self.sdk_instance)

            kwargs = {
                "exchange": exchange,
                "asset": underlying,
                "derivative_type": derivative_type,
            }

            matches = instruments.get_instruments(**kwargs)

            if matches is None:
                return None

            # Convert to DataFrame if not already
            if hasattr(matches, 'to_pandas'):
                return matches.to_pandas()
            elif isinstance(matches, list):
                return pd.DataFrame([m.__dict__ if hasattr(m, '__dict__') else m for m in matches])
            else:
                return pd.DataFrame(matches)

        except Exception as e:
            print(f"Error fetching F&O instruments for {underlying}: {e}")
            return None

    def _parse_date(self, date_str):
        """Parse date string to datetime object."""
        if ' ' in date_str:
            return datetime.datetime.strptime(date_str, '%Y-%m-%d %H:%M')
        return datetime.datetime.strptime(date_str, '%Y-%m-%d')

    def initialize_sdk_with_credentials(self, phone=None, mpin=None, otp=None):
        """
        Initialize SDK with credentials from UI instead of .env file.

        Args:
            phone (str, optional): Phone number for full login
            mpin (str, required): MPIN for authentication
            otp (str, optional): OTP code for full login step 2

        Returns:
            tuple: (success: bool, error_message: str or None)

        Example:
            # Quick login
            success, error = handler.initialize_sdk_with_credentials(mpin="1234")

            # Full login
            success, error = handler.initialize_sdk_with_credentials(
                phone="9876543210",
                mpin="1234",
                otp="123456"
            )
        """
        import os

        try:
            # Set environment variables temporarily
            if phone:
                os.environ['PHONE_NO'] = phone
            if mpin:
                os.environ['MPIN'] = mpin
            if otp:
                os.environ['OTP'] = otp

            # Initialize SDK (reads from env vars via env_creds=True)
            self.sdk_instance = InitNubraSdk(self.env, env_creds=True)
            self.market_data_api = MarketData(self.sdk_instance)
            self.trading_api = Trading(self.sdk_instance)

            # Clear sensitive environment variables after initialization
            for key in ['MPIN', 'OTP']:
                if key in os.environ:
                    del os.environ[key]

            return (True, None)

        except Exception as e:
            error_msg = str(e)

            # Clear all credentials on failure
            for key in ['PHONE_NO', 'MPIN', 'OTP']:
                if key in os.environ:
                    del os.environ[key]

            return (False, error_msg)
