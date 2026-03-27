import backtrader as bt
import pandas as pd


class BacktestRunner:
    """
    Orchestrates backtrader backtesting with data loading,
    strategy execution, and performance metrics
    """

    def __init__(self, initial_cash=5000000):
        """
        Initialize backtest runner

        Args:
            initial_cash: Starting portfolio value (default: 50 lakhs / 5 million for Indian equities)
        """
        self.cerebro = bt.Cerebro()
        self.cerebro.broker.setcash(initial_cash)
        self.cerebro.broker.setcommission(commission=0.001)  # 0.1% commission

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
