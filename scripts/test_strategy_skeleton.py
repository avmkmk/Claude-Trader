"""Quick test that strategy skeleton works"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import backtrader as bt
from strategies.ath_reclaim_daily_v1 import ATHReclaimStrategy

cerebro = bt.Cerebro()
cerebro.addstrategy(ATHReclaimStrategy)
print("SUCCESS: Strategy skeleton created successfully")
