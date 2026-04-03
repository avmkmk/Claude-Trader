"""Test strategy with synthetic phase transition data"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import backtrader as bt
import pandas as pd
from strategies.ath_reclaim_daily_v1 import ATHReclaimStrategy

# Create synthetic data: ATH → Below EMA → Reclaim
# Need 200+ days for EMA 200 to stabilize
# Phase 1 (days 0-220): Gradual uptrend establishing ATH at 160
# Phase 2 (days 221-240): Drop below EMA 200, consolidate at 120
# Phase 3 (day 241): Reclaim ATH (close > 160)
# Phase 4 (days 242-244): Hold position above EMA
# Phase 5 (days 245-249): Exit when close < EMA

# Build price series
opens = []
highs = []
lows = []
closes = []

# Days 0-220: Uptrend from 100 to 160
for i in range(221):
    base = 100 + (i * 0.27)  # Linear rise to ~160
    opens.append(base - 2)
    highs.append(base + 3)
    lows.append(base - 3)
    closes.append(base)

# Days 221-235: Consolidation at 120 (below EMA ~130)
for i in range(15):
    opens.append(118)
    highs.append(125)
    lows.append(115)
    closes.append(120)

# Days 236-240: Gradual rise from 120 to 161 (smooth, no gaps)
for i in range(5):
    base = 120 + (i * 8.2)  # 120, 128.2, 136.4, 144.6, 152.8
    opens.append(base - 1)
    highs.append(base + 3)
    lows.append(base - 2)
    closes.append(base)

# Day 241: Reclaim ATH (close > previous ATH of 162.40)
# Previous close is 152.8, open exactly at previous close (no gap)
opens.append(152.8)
highs.append(165)
lows.append(152)
closes.append(163)  # Close above previous ATH 162.40

# Days 242-244: Continue uptrend well above EMA
for i in range(3):
    base = 165 + (i * 5)  # 165, 170, 175
    opens.append(base - 2)
    highs.append(base + 5)
    lows.append(base - 3)
    closes.append(base)

# Days 245-249: Drop sharply below EMA to trigger exit
for i in range(5):
    opens.append(120)
    highs.append(125)
    lows.append(118)
    closes.append(120)

data = {
    'datetime': pd.date_range('2020-01-01', periods=250),
    'open': opens,
    'high': highs,
    'low': lows,
    'close': closes,
    'volume': [10000] * 250
}
df = pd.DataFrame(data).set_index('datetime')

data_feed = bt.feeds.PandasData(dataname=df)
cerebro = bt.Cerebro()
cerebro.adddata(data_feed)
cerebro.addstrategy(ATHReclaimStrategy, verbose=True)  # Enable verbose to see phase transitions

print("Starting portfolio value:", cerebro.broker.getvalue())
cerebro.run()
print("Final portfolio value:", cerebro.broker.getvalue())
print("\nStrategy complete - check for phase transitions and trades")
