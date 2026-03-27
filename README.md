# SimpleTrader

A Python-based algorithmic trading bot for Indian equity markets (NSE/BSE) with support for Nubra and Upstox broker APIs.

## Features

- **Multi-Broker Support**: Nubra and Upstox API integration
- **Backtesting Framework**: Complete backtesting system powered by Backtrader
- **Strategy Templates**: Pre-built templates for momentum, mean reversion, and breakout strategies
- **Interactive Dashboard**: Streamlit-based UI for authentication, data management, and backtesting
- **Indian Market Compliance**: Built-in risk management and circuit breaker awareness

## Quick Start

### Prerequisites

- Python 3.8+
- Nubra or Upstox trading account
- Git Bash (for Windows users)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/SimpleTrader.git
cd SimpleTrader
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/Scripts/activate  # Git Bash on Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables:
Create a `.env` file with your broker credentials:
```env
NUBRA_CLIENT_ID="your_client_id"
NUBRA_MPIN="your_mpin"
UPSTOX_ACCESS_TOKEN="your_token"
```

5. Launch the dashboard:
```bash
streamlit run dashboard/streamlit_app.py
```
Access at http://localhost:8501

## Project Structure

```
SimpleTrader/
├── main.py                    # Entry point
├── apis/                      # Broker API handlers
├── strategies/                # Strategy implementations
│   └── templates/            # Strategy templates
├── backtesting/              # Backtesting engine
├── dashboard/                # Streamlit UI
├── docs/                     # Documentation
│   ├── quick_start/          # Getting started guides
│   ├── strategy_development/ # Strategy workflow
│   ├── indian_markets/       # Market-specific guides
│   └── backtesting/          # Backtesting guides
└── data/                     # Historical market data
```

## Documentation

- **[Development Workflow](docs/quick_start/development_workflow.md)** - Quick reference guide
- **[Strategy Development](docs/strategy_development/README.md)** - Complete 6-phase workflow
- **[Indian Markets Guide](docs/indian_markets/README.md)** - Market rules and patterns
- **[Backtesting System](docs/backtesting/README.md)** - Architecture and usage

## Strategy Development Workflow

1. **Research & Selection** - Identify strategy type and market conditions
2. **Parameter Design** - Define indicators and entry/exit rules
3. **Implementation** - Code strategy using templates
4. **Backtesting** - Test on historical data
5. **Optimization** - Tune parameters for performance
6. **Validation** - Verify on out-of-sample data

See [Strategy Development Guide](docs/strategy_development/README.md) for details.

## Risk Management

Built-in safeguards for Indian markets:
- Max 3% risk per trade
- Max 10% risk per position
- -5% daily loss triggers stop
- Circuit breaker awareness (±5/10/20%)
- Liquidity filters (min 5 lakh daily volume)

See [Risk Management Guide](docs/indian_markets/risk_management.md) for complete rules.

## Key Dependencies

- **backtrader** - Strategy backtesting framework
- **streamlit** - Web dashboard
- **nubra-sdk** - Nubra broker API
- **upstox-python-sdk** - Upstox broker API
- **pandas** - Data manipulation

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-strategy`)
3. Commit changes (`git commit -m 'Add amazing strategy'`)
4. Push to branch (`git push origin feature/amazing-strategy`)
5. Open a Pull Request

## License

This project is for educational and personal use only. Trading involves risk of loss. Use at your own discretion.

## Disclaimer

This software is provided for educational purposes only. Trading in financial markets carries risk. The authors are not responsible for any financial losses incurred using this software. Always test strategies thoroughly before live trading.

## Support

For issues, questions, or contributions, please open an issue on GitHub.
