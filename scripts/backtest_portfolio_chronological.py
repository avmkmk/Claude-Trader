"""
Portfolio-Level Chronological Backtest with CapitalManager

This implements a REALISTIC backtest that:
1. Starts with Rs 70,000
2. Adds Rs 70,000 monthly
3. Takes trades chronologically (date-by-date across all stocks)
4. Skips trades when capital is insufficient
5. Simulates actual capital constraints

This is different from per-stock backtests which give each stock
its own capital pool independently.
"""
import sys
import os
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
from collections import defaultdict

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backtesting.capital_manager import CapitalManager


def load_all_stock_data(symbols, data_dir, start_date, end_date):
    """
    Load historical data for all symbols and merge into single chronological dataset

    Returns:
        DataFrame with columns: date, symbol, open, high, low, close, ema200
    """
    print(f"Loading data for {len(symbols)} symbols...")

    all_data = []

    for i, symbol in enumerate(symbols, 1):
        # Try both uppercase and lowercase
        data_path = data_dir / f'{symbol}.csv'
        data_path_lower = data_dir / f'{symbol.lower()}.csv'

        if data_path.exists():
            path_to_use = data_path
        elif data_path_lower.exists():
            path_to_use = data_path_lower
        else:
            continue

        try:
            df = pd.read_csv(path_to_use)
            df['Date'] = pd.to_datetime(df['Date'])
            df = df[(df['Date'] >= start_date) & (df['Date'] <= end_date)]

            if len(df) < 200:  # Need 200 days for EMA 200
                continue

            # Calculate EMA 200
            df['ema200'] = df['Close'].ewm(span=200, adjust=False).mean()

            # Add symbol column
            df['symbol'] = symbol

            # Select needed columns
            df = df[['Date', 'symbol', 'Open', 'High', 'Low', 'Close', 'ema200']].copy()
            df.columns = ['date', 'symbol', 'open', 'high', 'low', 'close', 'ema200']

            all_data.append(df)

            if i % 50 == 0:
                print(f"  Loaded {i}/{len(symbols)}...")

        except Exception as e:
            continue

    if not all_data:
        return None

    # Concatenate all data and sort by date
    combined = pd.concat(all_data, ignore_index=True)
    combined = combined.sort_values('date').reset_index(drop=True)

    print(f"[OK] Loaded {len(all_data)} stocks, {len(combined)} total bars")
    print(f"Date range: {combined['date'].min()} to {combined['date'].max()}")

    return combined


def detect_ath_reclaim_signals(df):
    """
    Detect ATH reclaim signals across all stocks

    Returns:
        DataFrame with signals: date, symbol, signal_type, price, etc.
    """
    print("\nDetecting ATH reclaim signals...")

    signals = []

    # Group by symbol to track per-stock state
    for symbol, group in df.groupby('symbol'):
        group = group.sort_values('date').reset_index(drop=True)

        # Track ATH and phases per stock
        ath = 0
        current_phase = None
        prev_close = None
        below_ema_date = None

        for idx, row in group.iterrows():
            current_date = row['date']
            current_high = row['high']
            current_close = row['close']
            current_open = row['open']
            ema_value = row['ema200']

            # Skip if EMA not ready
            if pd.isna(ema_value) or idx < 200:
                prev_close = current_close
                continue

            # CRITICAL: Check for entry BEFORE updating ATH
            # Phase 3: ATH Reclaim - ENTRY SIGNAL
            if current_phase == 2 and current_close > ath:
                # Check for gap up (skip if gap)
                if prev_close is not None:
                    gap_up = current_open > (prev_close * 1.001)

                    if not gap_up:
                        # Valid entry signal!
                        signals.append({
                            'date': current_date,
                            'symbol': symbol,
                            'signal_type': 'ENTRY',
                            'price': current_close,
                            'ema200': ema_value,
                            'ath': ath,
                            'days_since_phase2': (current_date - below_ema_date).days if below_ema_date else None
                        })
                        current_phase = 3

            # Phase 1: Update ATH (AFTER entry check)
            if current_high > ath:
                ath = current_high
                # Only set to Phase 1 if we're in Phase 1 or None
                # Don't reset Phase 2 or Phase 3
                if current_phase is None or current_phase == 1:
                    current_phase = 1

            # Phase 2: Below EMA 200
            if current_phase == 1 and current_close < ema_value:
                current_phase = 2
                below_ema_date = current_date

            prev_close = current_close

    signals_df = pd.DataFrame(signals)

    if len(signals_df) > 0:
        print(f"[OK] Found {len(signals_df)} entry signals across {signals_df['symbol'].nunique()} stocks")
        print(f"Signal date range: {signals_df['date'].min()} to {signals_df['date'].max()}")
    else:
        print("[WARNING] No signals found!")

    return signals_df


def run_portfolio_backtest(symbols_file, start_date_str, end_date_str,
                          starting_cash=70000, monthly_injection=70000,
                          position_pct=0.10, data_dir=None):
    """
    Run chronological portfolio backtest with CapitalManager

    This simulates real trading: start with 70K, add 70K monthly,
    take trades as signals appear chronologically
    """
    # Parse dates
    start_date = pd.to_datetime(start_date_str)
    end_date = pd.to_datetime(end_date_str)

    print("="*80)
    print("PORTFOLIO-LEVEL CHRONOLOGICAL BACKTEST")
    print("="*80)
    print(f"\nPeriod: {start_date_str} to {end_date_str}")
    print(f"Starting Capital: Rs {starting_cash:,}")
    print(f"Monthly Injection: Rs {monthly_injection:,}")
    print(f"Position Size: {position_pct*100:.0f}% of portfolio")
    print()

    # Load symbols
    symbols_df = pd.read_csv(symbols_file)
    symbols = symbols_df['Symbol'].tolist()

    # Data directory
    if data_dir is None:
        psp_root = project_root.parent.parent.parent
        data_dir = psp_root / 'historical_Indian_equity_data' / 'daily' / 'eod2'
    else:
        data_dir = Path(data_dir)

    # Load all stock data
    df = load_all_stock_data(symbols, data_dir, start_date, end_date)

    if df is None or len(df) == 0:
        print("[ERROR] No data loaded!")
        return None

    # Detect signals
    signals_df = detect_ath_reclaim_signals(df)

    if len(signals_df) == 0:
        print("[ERROR] No signals detected!")
        return None

    # Initialize CapitalManager
    capital_mgr = CapitalManager(
        start_date=start_date.date(),
        starting_cash=starting_cash,
        monthly_injection=monthly_injection
    )

    # Track trades and positions
    open_positions = {}  # symbol -> {entry_date, entry_price, shares, ath, ema200_at_entry}
    closed_trades = []

    # Process day by day
    print("\n" + "="*80)
    print("RUNNING CHRONOLOGICAL SIMULATION")
    print("="*80)
    print()

    all_dates = sorted(df['date'].unique())

    for current_date in all_dates:
        # Update capital manager with current date
        capital_mgr.update_date(current_date.date())

        # Get today's data for all stocks
        today_data = df[df['date'] == current_date].set_index('symbol')

        # Check for entry signals on this date
        today_signals = signals_df[signals_df['date'] == current_date]

        for _, signal in today_signals.iterrows():
            symbol = signal['symbol']
            entry_price = signal['price']

            # Skip if already in position
            if symbol in open_positions:
                continue

            # Calculate position size
            shares = capital_mgr.calculate_position_size(entry_price)

            if shares >= 1:
                # Enter trade
                capital_mgr.enter_trade(shares, entry_price)

                open_positions[symbol] = {
                    'entry_date': current_date,
                    'entry_price': entry_price,
                    'shares': shares,
                    'ath': signal['ath'],
                    'ema200_at_entry': signal['ema200']
                }

                print(f"{current_date.date()} | BUY {symbol:12s} | {shares:4d} shares @ Rs {entry_price:8.2f} | "
                      f"Cost: Rs {shares*entry_price:10,.0f} | Cash: Rs {capital_mgr.available_cash:10,.0f}")

        # Check for exit signals (close < EMA 200)
        for symbol in list(open_positions.keys()):
            if symbol not in today_data.index:
                continue

            position = open_positions[symbol]
            stock_data = today_data.loc[symbol]

            current_close = stock_data['close']
            current_ema = stock_data['ema200']

            # Exit if close < EMA 200
            if current_close < current_ema:
                # Close position
                shares = position['shares']
                entry_price = position['entry_price']
                exit_price = current_close

                capital_mgr.exit_trade(shares, entry_price, exit_price)

                # Calculate trade metrics
                pnl = shares * (exit_price - entry_price)
                pnl_pct = ((exit_price - entry_price) / entry_price) * 100
                hold_days = (current_date - position['entry_date']).days

                closed_trades.append({
                    'symbol': symbol,
                    'entry_date': position['entry_date'],
                    'exit_date': current_date,
                    'hold_days': hold_days,
                    'entry_price': entry_price,
                    'exit_price': exit_price,
                    'shares': shares,
                    'pnl': pnl,
                    'pnl_pct': pnl_pct,
                    'win': pnl > 0
                })

                print(f"{current_date.date()} | SELL {symbol:12s} | {shares:4d} shares @ Rs {exit_price:8.2f} | "
                      f"P&L: Rs {pnl:10,.0f} ({pnl_pct:+6.2f}%) | Hold: {hold_days:3d}d | Cash: Rs {capital_mgr.available_cash:10,.0f}")

                # Remove from open positions
                del open_positions[symbol]

    # Close any remaining positions at end date
    final_data = df[df['date'] == all_dates[-1]].set_index('symbol')

    for symbol, position in open_positions.items():
        if symbol not in final_data.index:
            continue

        shares = position['shares']
        entry_price = position['entry_price']
        exit_price = final_data.loc[symbol]['close']

        capital_mgr.exit_trade(shares, entry_price, exit_price)

        pnl = shares * (exit_price - entry_price)
        pnl_pct = ((exit_price - entry_price) / entry_price) * 100
        hold_days = (all_dates[-1] - position['entry_date']).days

        closed_trades.append({
            'symbol': symbol,
            'entry_date': position['entry_date'],
            'exit_date': all_dates[-1],
            'hold_days': hold_days,
            'entry_price': entry_price,
            'exit_price': exit_price,
            'shares': shares,
            'pnl': pnl,
            'pnl_pct': pnl_pct,
            'win': pnl > 0
        })

        print(f"{all_dates[-1].date()} | CLOSE {symbol:12s} | {shares:4d} shares @ Rs {exit_price:8.2f} | "
              f"P&L: Rs {pnl:10,.0f} ({pnl_pct:+6.2f}%) | Hold: {hold_days:3d}d (EOD)")

    # Calculate final results
    final_value = capital_mgr.portfolio_value
    total_return = ((final_value - capital_mgr.total_injected) / capital_mgr.total_injected) * 100

    trades_df = pd.DataFrame(closed_trades)

    return {
        'starting_cash': starting_cash,
        'total_injected': capital_mgr.total_injected,
        'final_value': final_value,
        'net_pnl': final_value - capital_mgr.total_injected,
        'total_return_pct': total_return,
        'total_trades': len(trades_df),
        'won_trades': len(trades_df[trades_df['win']]),
        'lost_trades': len(trades_df[~trades_df['win']]),
        'win_rate': len(trades_df[trades_df['win']]) / len(trades_df) * 100 if len(trades_df) > 0 else 0,
        'avg_hold_days': trades_df['hold_days'].mean() if len(trades_df) > 0 else 0,
        'trades': trades_df
    }


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        description='Run portfolio-level chronological backtest with CapitalManager'
    )
    parser.add_argument('--symbols-file', type=str, required=True,
                       help='CSV file with symbols')
    parser.add_argument('--start-date', type=str, required=True,
                       help='Start date YYYY-MM-DD')
    parser.add_argument('--end-date', type=str, required=True,
                       help='End date YYYY-MM-DD')
    parser.add_argument('--starting-cash', type=float, default=70000,
                       help='Starting capital (default: 70000)')
    parser.add_argument('--monthly-injection', type=float, default=70000,
                       help='Monthly capital injection (default: 70000)')
    parser.add_argument('--data-dir', type=str, default=None,
                       help='Data directory path (optional, uses default if not specified)')
    parser.add_argument('--output', type=str, default='results/portfolio_backtest.csv',
                       help='Output CSV file for trades')

    args = parser.parse_args()

    result = run_portfolio_backtest(
        symbols_file=args.symbols_file,
        start_date_str=args.start_date,
        end_date_str=args.end_date,
        starting_cash=args.starting_cash,
        monthly_injection=args.monthly_injection,
        data_dir=args.data_dir
    )

    if result:
        # Print summary
        print("\n" + "="*80)
        print("PORTFOLIO BACKTEST SUMMARY")
        print("="*80)
        print(f"\nCapital Management:")
        print(f"  Starting Cash:      Rs {result['starting_cash']:,}")
        print(f"  Total Injected:     Rs {result['total_injected']:,}")
        print(f"  Final Value:        Rs {result['final_value']:,.2f}")
        print(f"  Net P&L:            Rs {result['net_pnl']:,.2f}")
        print(f"  Total Return:       {result['total_return_pct']:.2f}%")

        print(f"\nTrading Activity:")
        print(f"  Total Trades:       {result['total_trades']}")
        print(f"  Won Trades:         {result['won_trades']}")
        print(f"  Lost Trades:        {result['lost_trades']}")
        print(f"  Win Rate:           {result['win_rate']:.1f}%")
        print(f"  Avg Hold Period:    {result['avg_hold_days']:.0f} days")

        # Save trades
        if len(result['trades']) > 0:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            result['trades'].to_csv(output_path, index=False)
            print(f"\n[OK] Saved {len(result['trades'])} trades to: {output_path}")

        print("="*80)
