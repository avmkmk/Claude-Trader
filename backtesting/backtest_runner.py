import backtrader as bt
import pandas as pd
import os
import glob


class BacktestRunner:
    """
    Orchestrates backtrader backtesting with data loading,
    strategy execution, and performance metrics
    """

    def __init__(self, initial_cash=5000000, data_dir=None):
        """
        Initialize backtest runner

        Args:
            initial_cash: Starting portfolio value (default: 50 lakhs / 5 million for Indian equities)
            data_dir: Path to data directory (default: project/data/)
        """
        self.cerebro = bt.Cerebro()
        self.cerebro.broker.setcash(initial_cash)
        self.cerebro.broker.setcommission(commission=0.001)  # 0.1% commission
        
        # Set data directory
        if data_dir is None:
            self.data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
        else:
            self.data_dir = data_dir

    def find_data_folder(self, symbol):
        """
        Find the most recent data folder for a symbol.
        
        Args:
            symbol: Trading symbol (e.g., 'RELIANCE')
            
        Returns:
            Path to the data folder, or None if not found
        """
        # Look for folders matching pattern SYMBOL_*
        pattern = os.path.join(self.data_dir, f"{symbol}_*")
        folders = glob.glob(pattern)
        
        if not folders:
            return None
        
        # Return most recently modified folder
        folders_with_mtime = [(f, os.path.getmtime(f)) for f in folders if os.path.isdir(f)]
        if not folders_with_mtime:
            return None
        
        folders_with_mtime.sort(key=lambda x: x[1], reverse=True)
        return folders_with_mtime[0][0]

    def find_timeframe_file(self, symbol, timeframe):
        """
        Find the CSV file for a specific symbol and timeframe.
        
        Args:
            symbol: Trading symbol (e.g., 'RELIANCE')
            timeframe: Timeframe ('5min', '15min', '60min', '4hour', 'daily', 'weekly')
            
        Returns:
            Path to CSV file, or None if not found
        """
        timeframe_filename = {
            '5min': '5min.csv',
            '15min': '15min.csv',
            '60min': '60min.csv',
            '4hour': '4hour.csv',
            'daily': 'daily.csv',
            'weekly': 'weekly.csv'
        }.get(timeframe)
        
        if not timeframe_filename:
            return None
        
        # Find data folder
        folder = self.find_data_folder(symbol)
        if not folder:
            return None
        
        # Build file path
        filepath = os.path.join(folder, timeframe_filename)
        
        if os.path.exists(filepath):
            return filepath
        
        return None

    def load_data(self, csv_path, symbol_name):
        """
        Load CSV data into backtrader format

        Args:
            csv_path: Path to CSV file with OHLCV data
            symbol_name: Name for the data feed

        CSV Format:
            - Index: datetime
            - Columns: open, high, low, close, volume
        """
        df = pd.read_csv(csv_path, index_col=0, parse_dates=True)

        # Convert to backtrader PandasData format
        data = bt.feeds.PandasData(
            dataname=df,
            datetime=None,  # Index is datetime
            open='open',
            high='high',
            low='low',
            close='close',
            volume='volume',
            openinterest=-1  # No open interest data
        )
        self.cerebro.adddata(data, name=symbol_name)

    def load_eod2_data(self, csv_path, symbol_name):
        """
        Load eod2 format daily data into backtrader.

        Args:
            csv_path: Path to eod2 CSV file
            symbol_name: Name for the data feed

        eod2 CSV Format:
            Date, Open, High, Low, Close, Volume, Series, TOTAL_TRADES, QTY_PER_TRADE, DLV_QTY
        """
        df = pd.read_csv(csv_path, parse_dates=['Date'])
        df = df.set_index('Date')

        # Map to backtrader expected columns (lowercase)
        df = df[['Open', 'High', 'Low', 'Close', 'Volume']]
        df.columns = [c.lower() for c in df.columns]

        # Drop rows with missing data
        df = df.dropna()

        # Convert to backtrader PandasData format
        data = bt.feeds.PandasData(
            dataname=df,
            datetime=None,
            open='open',
            high='high',
            low='low',
            close='close',
            volume='volume',
            openinterest=-1
        )
        self.cerebro.adddata(data, name=symbol_name)

    def load_eod2_data_filtered(self, csv_path, symbol_name, start_date=None, end_date=None):
        """
        Load eod2 data with optional date filtering.

        Args:
            csv_path: Path to eod2 CSV file
            symbol_name: Name for the data feed
            start_date: Start date string 'YYYY-MM-DD' (optional)
            end_date: End date string 'YYYY-MM-DD' (optional)
        """
        df = pd.read_csv(csv_path, parse_dates=['Date'])
        df = df.set_index('Date')

        # Apply date filtering
        if start_date:
            df = df[df.index >= start_date]
        if end_date:
            df = df[df.index <= end_date]

        # Map columns
        df = df[['Open', 'High', 'Low', 'Close', 'Volume']]
        df.columns = [c.lower() for c in df.columns]

        # Drop missing data
        df = df.dropna()

        # Convert to backtrader format
        data = bt.feeds.PandasData(
            dataname=df,
            datetime=None,
            open='open',
            high='high',
            low='low',
            close='close',
            volume='volume',
            openinterest=-1
        )
        self.cerebro.adddata(data, name=symbol_name)

    def add_strategy(self, strategy_class, **params):
        """
        Add strategy with parameters

        Args:
            strategy_class: Backtrader Strategy class
            **params: Strategy parameters (e.g., fast_period=10, slow_period=30)
        """
        self.cerebro.addstrategy(strategy_class, **params)

    def add_analyzers(self):
        """Add standard performance analyzers"""
        self.cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
        self.cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
        self.cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
        self.cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')

    def run(self):
        """
        Execute backtest

        Returns:
            First strategy instance with analyzer results
        """
        print(f'Starting Portfolio Value: Rs {self.cerebro.broker.getvalue():,.2f}')
        results = self.cerebro.run()
        print(f'Ending Portfolio Value:   Rs {self.cerebro.broker.getvalue():,.2f}')
        return results[0]  # Return first strategy instance

    def plot(self):
        """Display backtest chart"""
        try:
            self.cerebro.plot(style='candlestick')
        except Exception as e:
            print(f"Plot error: {e}")
            print("Note: Plotting may require additional matplotlib configuration")

    def get_metrics(self, strategy_result):
        """
        Extract performance metrics from analyzers

        Args:
            strategy_result: Strategy instance returned from run()

        Returns:
            Dictionary with performance metrics
        """
        metrics = {}

        # Sharpe Ratio
        try:
            sharpe = strategy_result.analyzers.sharpe.get_analysis()
            metrics['sharpe_ratio'] = sharpe.get('sharperatio', None)
        except:
            metrics['sharpe_ratio'] = None

        # Drawdown
        try:
            drawdown = strategy_result.analyzers.drawdown.get_analysis()
            metrics['drawdown'] = {
                'max_drawdown': drawdown.get('max', {}).get('drawdown', None),
                'max_drawdown_period': drawdown.get('max', {}).get('len', None),
            }
        except:
            metrics['drawdown'] = {}

        # Returns
        try:
            returns = strategy_result.analyzers.returns.get_analysis()
            metrics['returns'] = {
                'total_return': returns.get('rtot', None),
                'average_return': returns.get('ravg', None),
            }
        except:
            metrics['returns'] = {}

        # Trades
        try:
            trades = strategy_result.analyzers.trades.get_analysis()
            metrics['trades'] = {
                'total_trades': trades.get('total', {}).get('closed', 0),
                'won_trades': trades.get('won', {}).get('total', 0),
                'lost_trades': trades.get('lost', {}).get('total', 0),
                'win_streak': trades.get('streak', {}).get('won', {}).get('longest', 0),
                'lose_streak': trades.get('streak', {}).get('lost', {}).get('longest', 0),
                'pnl_net_total': trades.get('pnl', {}).get('net', {}).get('total', 0),
                'pnl_net_average': trades.get('pnl', {}).get('net', {}).get('average', 0),
            }
        except:
            metrics['trades'] = {}

        return metrics
