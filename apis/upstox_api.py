import pandas as pd
from upstox_client.rest import ApiException


def get_historical_data_upstox(history_api, instrument_key, from_date, to_date, interval_unit='days', interval_value=1):
    try:
        api_response = history_api.get_historical_candle_data1(
            instrument_key,
            interval_unit=interval_unit,
            interval_value=interval_value,
            to_date=to_date,
            from_date=from_date,
            api_version='3.0'
        )

        if api_response and api_response.data and api_response.data.candles:
            df = pd.DataFrame(api_response.data.candles,
                              columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'open_interest'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            return df
        return None
    except ApiException as e:
        print(f"Upstox API exception: {e}")
        return None
    except Exception as e:
        print(f"Unexpected Upstox error: {e}")
        return None


def place_mock_order_upstox(order_api, instrument_key, transaction_type):
    try:
        from upstox_client import PlaceOrderRequest
        body = PlaceOrderRequest(
            quantity=1,
            product='D',
            validity='DAY',
            price=0.0,
            tag='gemini_mock_order',
            instrument_token=instrument_key,
            order_type='MARKET',
            transaction_type=transaction_type,
            disclosed_quantity=0,
            trigger_price=0.0,
            is_amo=False
        )
        api_response = order_api.place_order(body, api_version='2.0')
        print(f"Placed mock Upstox order: {getattr(api_response.data, 'order_id', None)}")
    except Exception as e:
        print(f"Failed to place mock Upstox order: {e}")
