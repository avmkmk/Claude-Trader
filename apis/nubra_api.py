import datetime
import pandas as pd
from nubra_python_sdk.start_sdk import InitNubraSdk, NubraEnv
from nubra_python_sdk.marketdata.market_data import MarketData
from nubra_python_sdk.trading.trading_data import NubraTrader as Trading
from nubra_python_sdk.ticker.websocketdata import NubraDataSocket


class NubraAPIHandler:
    def __init__(self, env=NubraEnv.PROD):
        self.env = env
        self.sdk_instance = None
        self.market_data_api = None
        self.trading_api = None
        self.ws_client = None

    def initialize_sdk(self):
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
