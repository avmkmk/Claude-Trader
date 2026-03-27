import os # For interacting with the operating system, like environment variables
from dotenv import load_dotenv # For loading environment variables from a .env file
import pandas as pd # For data manipulation and analysis, especially with DataFrames
import datetime # For working with dates and times
import time # For time-related functions, like pauses
import backtrader as bt # For backtesting trading strategies (currently commented out)
from dotenv import load_dotenv
from apis.nubra_api import NubraAPIHandler
from apis.upstox_api import get_historical_data_upstox

# Upstox helpers moved to apis/upstox_api.py

def place_mock_order_upstox(order_api, instrument_key, signal):
    """
    Place a mock order for Upstox broker.
    """
    print(f"Mock order placed on Upstox: {signal} for {instrument_key}")


def place_mock_order_nubra(order_api, instrument_key, signal):
    """
    Place a mock order for Nubra broker.
    """
    print(f"Mock order placed on Nubra: {signal} for {instrument_key}")


def live_signal_generation(history_api, order_api, instrument_key, interval_unit='minute', interval_value=1, fast_length=10, slow_length=30, check_interval_seconds=60, broker="Upstox"):
    """
    Continuously fetches latest data, calculates SMA crossovers, and generates signals.
    """
    print(f"Starting live signal generation for {instrument_key} using {broker}...")
    last_signal = None # To track the last generated signal

    # If Nubra broker is selected, attempt to connect to WebSocket for real-time data
    if broker == "Nubra":
        # Check if history_api is an instance of NubraAPIHandler and has the method
        if isinstance(history_api, NubraAPIHandler) and hasattr(history_api, 'connect_websocket') and callable(history_api.connect_websocket):
            connection_successful = history_api.connect_websocket()
            if not connection_successful:
                print("WebSocket connection failed. Falling back to polling historical data.")
                # Potentially switch to polling if WebSocket fails
        else:
            print("Warning: history_api is not a NubraAPIHandler instance or connect_websocket method is missing. Falling back to polling historical data.")

    while True:
        try:
            now = datetime.datetime.now()
            to_date_str = now.strftime('%Y-%m-%d %H:%M') if interval_unit == 'minute' else now.strftime('%Y-%m-%d')
            
            if interval_unit == 'minute':
                from_date_obj = now - datetime.timedelta(minutes=(slow_length * interval_value * 2))
                from_date_str = from_date_obj.strftime('%Y-%m-%d %H:%M')
            elif interval_unit == 'hour':
                from_date_obj = now - datetime.timedelta(hours=(slow_length * interval_value * 2))
                from_date_str = from_date_obj.strftime('%Y-%m-%d %H:%M')
            else: # days
                from_date_obj = now - datetime.timedelta(days=(slow_length * interval_value * 2))
                from_date_str = from_date_obj.strftime('%Y-%m-%d')

            latest_data_df = None
            if broker == "Upstox":
                latest_data_df = get_historical_data_upstox(history_api, instrument_key, from_date_str, to_date_str, interval_unit, interval_value)
            elif broker == "Nubra":
                # Use the method from the NubraAPIHandler instance
                latest_data_df = history_api.get_historical_data(instrument_key, from_date_str, to_date_str, interval_unit)
            
            if latest_data_df is None or latest_data_df.empty:
                print(f"{datetime.datetime.now()}: No data fetched for signal generation from {broker}. Retrying in {check_interval_seconds} seconds.")
                time.sleep(check_interval_seconds)
                continue
            
            if len(latest_data_df) < slow_length:
                print(f"{datetime.datetime.now()}: Not enough data for SMA calculation ({len(latest_data_df)}/{slow_length} needed) from {broker}. Retrying in {check_interval_seconds} seconds.")
                time.sleep(check_interval_seconds)
                continue
            
            data_for_sma = latest_data_df.iloc[- (slow_length + 5):]
            data_for_sma['fast_sma'] = data_for_sma['close'].rolling(window=fast_length).mean()
            data_for_sma['slow_sma'] = data_for_sma['close'].rolling(window=slow_length).mean()

            latest_fast_sma = data_for_sma['fast_sma'].iloc[-1]
            latest_slow_sma = data_for_sma['slow_sma'].iloc[-1]
            
            previous_fast_sma = data_for_sma['fast_sma'].iloc[-2]
            previous_slow_sma = data_for_sma['slow_sma'].iloc[-2]

            current_close = data_for_sma['close'].iloc[-1]
            
            signal = None
            if previous_fast_sma <= previous_slow_sma and latest_fast_sma > latest_slow_sma:
                signal = "BUY"
            elif previous_fast_sma >= previous_slow_sma and latest_fast_sma < latest_slow_sma:
                signal = "SELL"
            
            if signal and signal != last_signal:
                print(f"{datetime.datetime.now()}: ----- {signal} Signal Generated! Current Close: {current_close:.2f} using {broker} -----")
                last_signal = signal
                if broker == "Upstox":
                    place_mock_order_upstox(order_api, instrument_key, signal)
                elif broker == "Nubra":
                    place_mock_order_nubra(order_api, instrument_key, signal)
            else:
                print(f"{datetime.datetime.now()}: No new signal. Close: {current_close:.2f}, Fast SMA: {latest_fast_sma:.2f}, Slow SMA: {latest_slow_sma:.2f} ({broker})")

        except Exception as e:
            print(f"{datetime.datetime.now()}: Error in live signal generation loop for {broker}: {e}")
        
        time.sleep(check_interval_seconds)


def main():
    """
    Main function to connect to chosen API, fetch data, and run live signal generation.
    """
    load_dotenv()

    # For now use Nubra only and fetch 3 months daily data for GRAPHITE
    load_dotenv()
    nubra = NubraAPIHandler()
    if not nubra.initialize_sdk():
        print("Failed to initialize Nubra SDK. Exiting.")
        return

    print("Fetching 3 months daily historical data for GRAPHITE from Nubra...")
    df = nubra.get_3months_equity('GRAPHITE')
    if df is None or df.empty:
        print("No historical data returned for GRAPHITE.")
        return

    print("Sample:")
    print(df.tail())

    # Save to CSV for backtesting use
    out_path = os.path.join(os.getcwd(), 'GRAPHITE_3months.csv')
    df.to_csv(out_path)
    print(f"Saved 3-month historical to {out_path}")

if __name__ == "__main__":
    main()
