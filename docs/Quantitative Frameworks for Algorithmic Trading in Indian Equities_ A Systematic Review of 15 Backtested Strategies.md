# **Quantitative Frameworks for Algorithmic Trading: Sector-Specific Strategies for Indian Equities**

The Indian equity market consists of diverse sectoral indices that exhibit distinct behavioral signatures. Your assumption that "one strategy might not fit all" is correct; for instance, a trend-following system that thrives on the directional momentum of Nifty IT may suffer from frequent whipsaws in the mean-reverting, range-bound environment of Nifty FMCG. Systematic trading success in India requires mapping the mathematical logic of a strategy to the microstructure and volatility regime of the specific sector.

The following 15 strategies are optimized for specific NSE sectoral indices, targeting a Sharpe ratio \> 1.0 and a minimum risk-to-reward ratio of ![][image1].

## **Sector 1: Nifty Bank (High Beta & Volatility)**

Nifty Bank has a beta of approximately 1.2 relative to Nifty 50, meaning it moves 20% more aggressively. It is characterized by frequent intraday oscillations and high options premiums.

### **Strategy 1: 9:20 AM Short Straddle (Theta-Volatility Play)**

* **Logic:** Capitalizes on the "volatility crush" and rapid theta decay after the initial opening range noise settles.1  
* **Entry:** Sell one At-the-Money (ATM) Call and one ATM Put at 9:20 AM.3  
* **Exit:** Individual leg stop-loss of 25–30% of the premium; mandatory square-off at 3:15 PM.1  
* **Metric:** Historically yields high win rates in range-bound sessions, common for Bank Nifty on non-policy days.1

### **Strategy 2: VWAP Mean Reversion (Intraday Oscillations)**

* **Logic:** Bank Nifty frequently oscillates around its Volume Weighted Average Price (VWAP) during the midday lull (11:00 AM to 2:00 PM).  
* **Entry:** Buy when the price dips 2 standard deviations below VWAP and shows a bullish rejection candle; Short when 2 standard deviations above.3  
* **Exit:** Target the VWAP mean line.5

### **Strategy 3: Cointegrated Banking Pairs (Statistical Arbitrage)**

* **Logic:** Large-cap banks like HDFC Bank and ICICI Bank are highly cointegrated due to similar fundamental drivers.7  
* **Signal:** Calculate the Z-score of the price spread. Entry when ![][image2].9  
* **Exit:** Close positions when the Z-score reverts to 0\.4

## **Sector 2: Nifty IT (Global Correlation & High Momentum)**

Nifty IT is heavily influenced by the US Nasdaq index and global sentiment, making it prone to gap openings and sustained trends.

### **Strategy 4: Nasdaq Lead-Lag Correlation**

* **Logic:** Strong correlation between Indian IT giants and overnight Nasdaq performance can be used to predict opening bias.  
* **Entry:** Go Long on liquid IT stocks (TCS, Infosys) at 9:15 AM if Nasdaq 100 closed ![][image3] higher; Short if it closed ![][image3] lower.  
* **Exit:** Exit at 10:30 AM or when a 1-period ATR trailing stop is hit.

### **Strategy 5: Mansfield Relative Strength (Momentum)**

* **Logic:** Identifies IT stocks entering a "Stage 2" markup phase by outperforming the Nifty 50 benchmark.11  
* **Entry:** Price ![][image4]\-week SMA AND Mansfield RS ![][image5] and rising.13  
* **Exit:** When Mansfield RS falls below 0 or price breaks the 30-week SMA.11

## **Sector 3: Nifty FMCG & Pharma (Defensive & Low Volatility)**

These sectors act as "defensive" plays, often remaining stable or rising during broader market corrections.

### **Strategy 6: Low-Volatility Gap Strategy (Overnight Edge)**

* **Logic:** Exploits the low ATR/price ratio of defensive stocks by capturing overnight moves.11  
* **Entry:** Enter long at 3:25 PM in stocks with the lowest relative volatility in the FMCG/Pharma universe.11  
* **Exit:** Exit at 9:15 AM the next day.11  
* **Metric:** Theoretical Sharpe ratio ![][image6] in backtests due to extremely low drawdown (![][image7]).11

### **Strategy 7: RSI Mean Reversion (Overbought/Oversold)**

* **Logic:** Defensive stocks rarely maintain extreme momentum, making them ideal for oscillators.  
* **Entry:** Buy when 14-period RSI ![][image8]; Sell when RSI ![][image9].  
* **Exit:** Target the RSI 50 midline.

## **Sector 4: Nifty Auto (Cyclical & Event-Driven)**

The Auto sector is highly sensitive to monthly sales data released at the start of each month.

### **Strategy 8: Monthly Sales Event Breakout**

* **Logic:** Significant deviations in sales data from analyst expectations trigger high-volume breakouts.  
* **Entry:** Long/Short on the breakout of the first 15-minute range on sales day, confirmed by ![][image10] average volume.  
* **Exit:** ![][image11] Risk-to-Reward target.14

### **Strategy 9: 200 EMA Trend Following (Structural Moves)**

* **Logic:** Auto stocks often exhibit long cyclical trends tied to interest rate environments.  
* **Entry:** Buy when 50 EMA crosses above 200 EMA (Golden Cross).  
* **Exit:** Inverse EMA crossover or 10% trailing stop-loss.16

## **Sector 5: Nifty Metal & Energy (Commodity-Linked)**

These sectors are driven by global commodity prices and often exhibit high directional strength once a trend is established.

### **Strategy 10: ADX Trend Strength Filter**

* **Logic:** Filters out non-trending noise in volatile commodity stocks.17  
* **Entry:** Long when \+DI ![][image12] \-DI AND ![][image13] (signaling a strong trend).19  
* **Exit:** When ADX begins to decline or \+DI crosses below \-DI.20

### **Strategy 11: Sector Rotation Ranking**

* **Logic:** Capital rotates between Metal and Energy based on global demand cycles.  
* **Ranking:** Rank stocks in both sectors by 12-month returns.5  
* **Execution:** Buy the top 3 ranked stocks; Rebalance monthly.5

## **Sector 6: Nifty Realty (Low Liquidity & Institutional Sentiment)**

Realty is often less liquid but prone to "Smart Money" accumulation phases.22

### **Strategy 12: Volume Spread Analysis (VSA)**

* **Logic:** Uses volume-to-price-range relationship to spot institutional activity.23  
* **Entry:** "No Supply" bar (narrow spread, low volume) near support zones indicates a potential reversal.25  
* **Exit:** "Upthrust" bar (high volume near resistance with a weak close) signals an exit.25

## **Cross-Sectoral & Macro Strategies**

These strategies utilize broad market data to enhance risk-adjusted returns across multiple indices.

### **Strategy 13: India VIX Volatility Regime Switching**

* **Logic:** Adapts the bot's logic based on the "Fear Index" level.26  
* **Mechanism:** If VIX ![][image14], use Option Selling (theta decay); If VIX ![][image15], use Breakout Trading (momentum).26  
* **Risk:** Dynamically widen stop-losses as VIX rises (![][image16]).28

### **Strategy 14: Index Rebalancing Arbitrage**

* **Logic:** Profits from the mandatory buying/selling of stocks by index funds during Nifty 50 or Sensex rebalancing.  
* **Entry:** Buy candidates for addition 10–15 days before the effective date.16  
* **Exit:** Sell on the "Market-on-Close" (MOC) orders of index funds on the rebalancing day.

### **Strategy 15: Triple Screen MTF (Multi-Timeframe) Momentum**

* **Logic:** Aligns lower-timeframe entries with higher-timeframe trends to improve win rates.1  
* **Entry:** Weekly trend is Up (Price ![][image12] 30-week SMA) AND Daily RSI is Oversold (![][image17]).31  
* **Exit:** Daily close hits a 2% target above entry or an 8% fixed stop-loss.30

## **Comparative Analysis for Backtesting**

| Sector | Recommended Strategy | Expected Edge | Risk Profile |
| :---- | :---- | :---- | :---- |
| Nifty Bank | 9:20 Straddle | Theta Decay 1 | High (Gamma Risk) 2 |
| Nifty IT | Nasdaq Lead-Lag | Information Gap | Moderate (Global Shock) |
| Nifty FMCG | Overnight Gap | Volatility Arbitrage 11 | Low (High Sharpe) 11 |
| Nifty Auto | Event Breakout | Volume Confirmation 16 | Moderate (Fake Breakout) 32 |
| Nifty Metal | ADX Trend Following | Directional Strength 21 | High (Whipsaws) 32 |
| Nifty Smallcap | Sector Rotation | Relative Strength | High (Concentration) |

### **Backtesting Guidelines for Your Bot**

1. **Slippage Calibration:** Indian large-caps require a 0.05–0.1% slippage buffer, while mid/small-caps need ![][image18] due to wider spreads.1  
2. **Corporate Actions:** Ensure your dataset is adjusted for bonus issues and stock splits to avoid false price signals.  
3. **Circuit Breakers:** Account for days where stocks hit upper/lower circuits, which can prevent trade execution in a backtest.19

#### **Works cited**

1. Backtest on Indian Markets : r/algotrading \- Reddit, accessed on March 27, 2026, [https://www.reddit.com/r/algotrading/comments/1q7pzyq/backtest\_on\_indian\_markets/](https://www.reddit.com/r/algotrading/comments/1q7pzyq/backtest_on_indian_markets/)  
2. Top 5 Algo Trading Strategies Every Retail Trader Should Know in 2025 \- RMoney, accessed on March 27, 2026, [https://rmoneyindia.com/blogs/algo-trading/top-5-algo-trading-strategies-for-retail-traders/](https://rmoneyindia.com/blogs/algo-trading/top-5-algo-trading-strategies-for-retail-traders/)  
3. 6 Popular Algo Trading Strategies for Retail Traders in India ..., accessed on March 27, 2026, [https://algotest.in/blog/6-popular-algo-trading-strategies-for-retail-traders-in-india/](https://algotest.in/blog/6-popular-algo-trading-strategies-for-retail-traders-in-india/)  
4. Mean-Reversion Trading with Statistical Arbitrage Pair Trading ..., accessed on March 27, 2026, [https://blog.quantinsti.com/epat-project-mean-reversion-statistical-arbitrage-pair-trading-strategy-indian-market-sectors/](https://blog.quantinsti.com/epat-project-mean-reversion-statistical-arbitrage-pair-trading-strategy-indian-market-sectors/)  
5. Momentum Portfolio Strategy: Rank Stocks & Rebalance Rules, accessed on March 27, 2026, [https://zerodha.com/varsity/chapter/momentum-portfolios/](https://zerodha.com/varsity/chapter/momentum-portfolios/)  
6. ChatGPT for Trading: Strategies, Prompts & Stock Market Insights \- QuantInsti, accessed on March 27, 2026, [https://www.quantinsti.com/articles/algorithmic-trading-chatgpt/](https://www.quantinsti.com/articles/algorithmic-trading-chatgpt/)  
7. Statistical Arbitrage with Pairs Trading and Backtesting \- My Framer Site \- FinSharpe, accessed on March 27, 2026, [https://finsharpe.com/blog/statistical-arbitrage-with-pairs-trading-and-backtesting](https://finsharpe.com/blog/statistical-arbitrage-with-pairs-trading-and-backtesting)  
8. Pair Trading Made Simple with a Clear Look at Statistical Arbitrage in India \- Tradejini, accessed on March 27, 2026, [https://www.tradejini.com/blogs/pair-trading-made-simple-with-a-clear-look-at-statistical-arbitrage-in-india](https://www.tradejini.com/blogs/pair-trading-made-simple-with-a-clear-look-at-statistical-arbitrage-in-india)  
9. Pair Trading Basics: Mean Reversion & Stock Relationships \- Zerodha, accessed on March 27, 2026, [https://zerodha.com/varsity/chapter/pair-trading-basics/](https://zerodha.com/varsity/chapter/pair-trading-basics/)  
10. Cointegrated Pairs Trading Strategy in Indian Equity Market (2015–2025) | EPAT Project, accessed on March 27, 2026, [https://blog.quantinsti.com/cointegrated-pairs-trading-indian-equity-market-epat-project/](https://blog.quantinsti.com/cointegrated-pairs-trading-indian-equity-market-epat-project/)  
11. Gap Trading Strategy: Based on the Markov Rule | EPAT Project, accessed on March 27, 2026, [https://blog.quantinsti.com/epat-project-gap-trading-strategy-based-on-the-markov-rule/](https://blog.quantinsti.com/epat-project-gap-trading-strategy-based-on-the-markov-rule/)  
12. Stage Analysis Trading: Master Stan Weinstein's 4-Stage Method, accessed on March 27, 2026, [https://arongroups.co/forex-articles/stage-analysis-trading/](https://arongroups.co/forex-articles/stage-analysis-trading/)  
13. Mansfield RS Indicator | Library of Technical & Fundamental Analysis \- Definedge Securities, accessed on March 27, 2026, [https://www.definedgesecurities.com/library/mansfield-rs-indicator/](https://www.definedgesecurities.com/library/mansfield-rs-indicator/)  
14. Master Intraday Options Trading: 5 Winning Strategies for Consistent Profits, accessed on March 27, 2026, [https://www.icfmindia.com/blog/master-intraday-options-trading-5-winning-strategies-for-consistent-profits](https://www.icfmindia.com/blog/master-intraday-options-trading-5-winning-strategies-for-consistent-profits)  
15. Breakout Trading Strategies for NSE Stocks: Entry, Exit, and Stop-Loss Rules, accessed on March 27, 2026, [https://www.gwcindia.in/blog/breakout-trading-strategies-for-nse-stocks-entry-exit-and-stop-loss-rules/](https://www.gwcindia.in/blog/breakout-trading-strategies-for-nse-stocks-entry-exit-and-stop-loss-rules/)  
16. Algorithmic Trading Strategies: Types, Examples & Benefits in India \- Dhan, accessed on March 27, 2026, [https://dhan.co/blog/trading-strategies/what-are-algorithmic-strategies/](https://dhan.co/blog/trading-strategies/what-are-algorithmic-strategies/)  
17. ADX Trading Strategy (Average Directional Movement Index Indicator) \- Statistics, Facts And Historical Backtests\! \- QuantifiedStrategies.com, accessed on March 27, 2026, [https://www.quantifiedstrategies.com/adx-trading-strategy/](https://www.quantifiedstrategies.com/adx-trading-strategy/)  
18. Backtest results for an ADX trading strategy (100% Annual Return?\!) : r/Daytrading \- Reddit, accessed on March 27, 2026, [https://www.reddit.com/r/Daytrading/comments/1irhtji/backtest\_results\_for\_an\_adx\_trading\_strategy\_100/](https://www.reddit.com/r/Daytrading/comments/1irhtji/backtest_results_for_an_adx_trading_strategy_100/)  
19. Backtesting Trading Strategies on NSE Data: What Retail Traders Actually Need to Know, accessed on March 27, 2026, [https://dev.to/trademineai/backtesting-trading-strategies-on-nse-data-what-retail-traders-actually-need-to-know-2n8k](https://dev.to/trademineai/backtesting-trading-strategies-on-nse-data-what-retail-traders-actually-need-to-know-2n8k)  
20. Other technical indicators: ADX, Supertrend, VWAP & more \- Zerodha, accessed on March 27, 2026, [https://zerodha.com/varsity/chapter/supplementary-notes-1/](https://zerodha.com/varsity/chapter/supplementary-notes-1/)  
21. ADX Indicator Trading Strategies \- AvaTrade, accessed on March 27, 2026, [https://www.avatrade.com/education/technical-analysis-indicators-strategies/adx-indicator-trading-strategies](https://www.avatrade.com/education/technical-analysis-indicators-strategies/adx-indicator-trading-strategies)  
22. Understanding Volume Spread Analysis | PDF | Market Trend | Algorithmic Trading \- Scribd, accessed on March 27, 2026, [https://www.scribd.com/document/143351486/Volume-Spread-Analysis-by-Kartik-Marar](https://www.scribd.com/document/143351486/Volume-Spread-Analysis-by-Kartik-Marar)  
23. New Indicators Added: Dorsey and Mansfield Relative Strength | TrendSpider Blog, accessed on March 27, 2026, [https://trendspider.com/blog/new-indicators-added-dorsey-and-mansfield-relative-strength/](https://trendspider.com/blog/new-indicators-added-dorsey-and-mansfield-relative-strength/)  
24. Volume Spread Analysis (VSA): What It Is & How It Works \- StockGro, accessed on March 27, 2026, [https://www.stockgro.club/blogs/trading/volume-spread-analysis/](https://www.stockgro.club/blogs/trading/volume-spread-analysis/)  
25. Back-Testing Super Trend in 15 Mins Time Frame among Top 5 Contributors of Nifty 50 Stocks \- INSPIRA, accessed on March 27, 2026, [https://www.inspirajournals.com/uploads/Issues/871152129.pdf](https://www.inspirajournals.com/uploads/Issues/871152129.pdf)  
26. India VIX & Stop Loss: Adjust Levels in Volatile Markets | 5paisa, accessed on March 27, 2026, [https://www.5paisa.com/blog/india-vix-and-stop-loss-how-to-adjust-your-levels](https://www.5paisa.com/blog/india-vix-and-stop-loss-how-to-adjust-your-levels)  
27. India VIX Today (Volatility Index) \- Ventura, accessed on March 27, 2026, [https://www.venturasecurities.com/invest/stocks/indices/india-vix](https://www.venturasecurities.com/invest/stocks/indices/india-vix)  
28. Using a Statistical Arbitrage Strategy for Algo Trading | Share India, accessed on March 27, 2026, [https://www.shareindia.com/knowledge-center/algo/statistical-arbitrage-trading-strategy](https://www.shareindia.com/knowledge-center/algo/statistical-arbitrage-trading-strategy)  
29. Backtest results for an ADX trading strategy : r/algotrading \- Reddit, accessed on March 27, 2026, [https://www.reddit.com/r/algotrading/comments/1irhrcw/backtest\_results\_for\_an\_adx\_trading\_strategy/](https://www.reddit.com/r/algotrading/comments/1irhrcw/backtest_results_for_an_adx_trading_strategy/)  
30. backtesting.py/doc/examples/Multiple Time Frames.ipynb at master · kernc/backtesting.py · GitHub, accessed on March 27, 2026, [https://github.com/kernc/backtesting.py/blob/master/doc/examples/Multiple%20Time%20Frames.ipynb](https://github.com/kernc/backtesting.py/blob/master/doc/examples/Multiple%20Time%20Frames.ipynb)  
31. Supertrend Indicator: How to Use It Effectively in Volatile Indian Markets \- Goodwill's Blog, accessed on March 27, 2026, [https://www.gwcindia.in/blog/supertrend-indicator-how-to-use-it-effectively-in-volatile-indian-markets/](https://www.gwcindia.in/blog/supertrend-indicator-how-to-use-it-effectively-in-volatile-indian-markets/)  
32. Common Algo Trading Strategies and Examples \- Stratzy, accessed on March 27, 2026, [https://stratzy.in/blog/common-algo-trading-strategies-and-examples/](https://stratzy.in/blog/common-algo-trading-strategies-and-examples/)

[image1]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAC8AAAAWCAYAAABQUsXJAAABWUlEQVR4Xu2Wr0sFQRSFj4hg0PRAMZnVIOIfIBhsgphtdjFpE4tVTK8bjQaLaYNdEGwGDWaTgog/zuXOuDPXt4PzeMqK88EH++bOXs7bnZ1doFD43wzRZTpvCwNE+l/awQQndJVOOY/oaTihoq9u8J0uhsUBMAbtfwXt/xiXk8j80Nm4XCP/8CfCh+SGP6dr0GyTphbRxvDHdqCJ3PByCw+hz8p36Tf8Cp0LC5bc8NfQ+TO2kCA3vDwrm+54BHr+Tl2uyQ3/G1d+G3F/Ofc5+P1Jbvh+yA1vqaA9xs1468Iv0T3ocvFU0B6y50fkhpemye2rB6nw8j4Ydsej9Ize0mk/gdxBe3xZqrnhZQ+W+RO2kKAp/AJ9gL5BfbB92vETHC8wa162I2lq3Q0n9eCAviG+rU3Y3l6PLIMLuh6MCTf0HvqZ8ES3UN+d1iMXRvb4Lt0wtUKh8Ff4ABaqXF2cVu3LAAAAAElFTkSuQmCC>

[image2]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAEcAAAAXCAYAAABZPlLoAAACLklEQVR4Xu2WTStFQRjHH6G8hUKSdBdKsbDwWhYWslViYyEbC+UDWClZ+gqiu7C3VZJuVrKx8QVYWCiUEEk8/54ztznPPe/Hvbeb86t/p/PMzJmZ/5l5ZogyMjLKRBuroIMJ6WON62AtE2bOEesuQAVWt1O32ubUs4Z00IdGVp2KNbF67ECYOT+sMx1kvknK0ImhGuZ0si5ZryTjuXUX+4Kxor6tbXLPJ9CcBhJjOlR8ieRj+ypeLXM2WRMU35wvkjZPrLy7WAgyZ4XVrGLPJB/UhoGo5qDeC+tQF6QkrjkLOqgJMmdMvedIBnCh4oao5oB21hbrlDVNpfs/CRU1x+acpPNhXWARxxwbJNI51gNrXZXFIa45H6wdVgtrg3VCakdEMQcN0DG2VBBJzTGMkqykPVaXKotCXHNWrXes3JI8GmYOcs4BiTEzVnyEpAObtOYYkIveWQO6IIQ45niB9p92IMgcLHc0wLGtc8IVq1fFasUczGWWNajibyTfKOJnDj6AhInKeOqyvPO0SWsOthX2Pe4b5dxWyJuPJPPG/A2RzfG65IFJkptxv4qDJOaskUzommSlpsHPHPOTc847cigujq3FGgLq3NgBL3PmSSoek0wYWiS5bCEO6VUD4pjzV0c52qFfTBzjwt83YzYUnDL76F4mWamGKZK8imcRL3OSEsUcGHFPybbNX4Mx4OqwS3LDLqHS5tQUmTkBZOYEgITmSkIpwMmmT4CMjH/EL9oof9ihBwWoAAAAAElFTkSuQmCC>

[image3]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAADkAAAAWCAYAAAB64jRmAAACT0lEQVR4Xu2WT6hNURSHl1D0hFJKKSm9/IukyOQNzCSU98qAuaGBIuYGRkoYSMlAyuDJiCeZKCKlRK8YkUjCBAPlz++z92Gd9e559+77el7qfPV1z1n73HvOOmvvta9ZS8tMsljOjcHAvBj4X5gl38jVcp/8YBOTXS5vywUhPm2ck+djsIGN8oFcL5fJFfKA3OmuYex0Pp4vb8p38qQckfvld/kpXzNt7JIf5XX5U16qDzeyWX6x9B38Jo/UrjC7IPe6c+414M5hzBqquEOujcEpwo1Kk3xtqSIYpyHwWyRWwbFPaFO2kdlyXL60zjcopZ8kX8VgYLc8no9Zn2fcGFWnil0h0e2W5vmhMFZKv0nygtfJJfXh3xB7mD9XyUdu7Ll1qWITo/KrpUZQSj9JsibpjrDFUgOhAXkWWirAkKVqIlWspi2FWiMX5fOeWGmpY12MA10oTXLQUrOq4OG551WbfPnwMqhiBdsHS+5tHiuCKUKyJ+JAA6VJdoLGwm/4jurhRfhuus3+Pt8ceSUf98RZSy2dqvZKaZKn5N0Qq5I8GuIVVMqvQ5qSv/agO54Ab2iD/Gxpo+2HbkkutXr7/2Hpeg8PzDplvUaOyVshxr3iPtpxzyTB+5YWfdxoS5gsSaYSY+9d7IXVH5B1eM2a1yTrkC7sYar6SvIP6A90pD2W9kk+pwJvnQSiNAMP0/+GOycRZs0dS38F+c49N15BEagif+sivNhqi9kqn/jBy/KxpWRnmsOWkuRldXoe4s9i0PE0y14/HMZaWlpa/g2/ALtIdEjiTkhJAAAAAElFTkSuQmCC>

[image4]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACUAAAAWCAYAAABHcFUAAAABtElEQVR4Xu2UPSiFURjH/5IiQhGJhSwMUpKsJspHmZTByKAMBmU3KJNYpJRSJiXZ76YYlJLBQkkZZEFRPv7/+5zjvve4t/u50P3Vr7fznPOe9znnfXqAEiX+BuX0hH7RCzqfPB2nlq7C1jzTluTp4jJFP2i1G7fSG3pEq1xMzxc64Mbinp5Gxhih3dFAAWzDTj/rxjU0Rh9pl4sNupjmPHuw95LQlV/RW1oRzOWCbmEUtp9oo3dIJOGTXHfzniVYUo1BPL7REH2gC8Fcvuh36mPjbqza0cGVRJRp2Dp/m2k5oK/IrwhVH/rINe2NxPtg9RQmNQZb3x/EU9IOK9ydcCID9bDDHMI+5gs/U1J6Zk0DLLmVcCILlmEfnEP63zcJW6Oks2KTvsNuLROVtCmI+Vs4hhXyJX4fzhd6RxD/oYz2wJqaGlwuaGMZrUO1B8V8CaiZKkEdwONbSUqUkLrxExJ1kAtvsM19o9R+G/STDrtYJ6z9NLuxiMHe/UGtYAK2UM9CqKP79IxuwX67DHvfGizRGboLu8WkS1A3PUei4RUD/TIlpXpSoqnQjWnNYjhRosS/5xuro1kv1kyFQAAAAABJRU5ErkJggg==>

[image5]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABwAAAAWCAYAAADTlvzyAAABLElEQVR4Xu2UsUtCURTGv4igKFoMojFxycFFIlzbGiRwbegfEBwc+gsagibBRQQhcG1rf1vQ4iTNLkFTiwkFld/xYJx3fNkVHd8PfjzeOcJ377v3CKSkJLNLb+gPHdKDeHu1bNF3emJqL/TJvOOM5m1hCUo0ojum1oXuNsY6faYDuuF6oUhIRBuufgUN3HP1SegpfaU11wtBzkoWLAGWC2jgkavPcE9HCD/0IvT8fGAZGnjs6okc0i/a8Y0E/guUZzAZaPC1bxj++qQVaKAsKIgm/YTudh5yKfqYXdT00mRd/Zc1WoAOrQzwIlTpA900tTYSxmKKhD3SN7rteiHkoOO1b2oR/TDvk3E4h/5QnstyS7/pJb2DXrjY4uWfoAcNXhWy0xat+0ZKykKMATldNUKcI1T2AAAAAElFTkSuQmCC>

[image6]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACoAAAAWCAYAAAC2ew6NAAABuklEQVR4Xu2VPyhFcRTHj1CEKINMshILoyJJGfxZbLIYmDCx6ZUMNgNWGQxKSlEv081CGYwWimIwWVDIn+955z7v3HPvu396TO6nPr33O+fe+zvv9zv394hSUv4nu3AYNruuwQPPFcG0wUP4BW9gtSf7B/BEWi4ginZ4AutVjO9dVmMaongPi8sxHCNZ1SaTK0YGLprYnauHcngJb2GlySVl2wYi6ILPcMDEHZJV9cHF9sMHOGdyScgXOkiypVHwynNBXLBmz41XmbiPffhC8kIk4QNOud95d3iyhULaB295UKH8gzleZ+KBtJJMvGUTIczDMjXmbX1VY0tUoYkWqpGk4BWbiIFD4StTbOt33HitiRdlA76RrG4UvXCJvC+kQ+Erwy/RJ+wxcYfkvgoT/4G3rRM+wVWTC4Ob/ojksG5RcT5JeELdDg1qzAd7Fk4X0jmuSX5AIHzzKXyENSYXhwxJm2jeydujIyRtNKNiE3Cd/L19psa5Y2mU5Bzlz1K5gvckf6V8asySzJGnw72mW8WYc5IW4xPjAk6St/Bc03JCP6wUuD/5DN0kWam48Px9JPeNe1MpKSm/wjckPFgsvV+ccQAAAABJRU5ErkJggg==>

[image7]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACYAAAAWCAYAAACsR+4DAAACH0lEQVR4Xu2VP0iWURTGH0mHIBUjiiAwcsqEkoYIXItcHEqwwcmG3AWHJqPBTUKCIAJxiIRa2hRFv3BzC3J0iUBwEQUdJKzn8dz7vue9vr3ftwhB3w8evu/cv+eee895gSb/Jm3UlbQxoSXoTDhHXUrablHToW+V+lLsPmGM2ksbIz3UEfWbWqB6i90NMUntO1sReEPdDPYj6he1TD2jhqkXsD3fhjEFtqgnzn4HG/zAtdXjAmzOgWu7DXO0Pdgas5Z3n3CNGkraMrSgn9BH7VKL1HnXXsUEdYyiY3eDLYeEfmtZL9AKi5R+S5FjUkRX8AG2qBavxxI1DhvvHYuOKCpCB97IeoFvqIiWGAiKKPTrsCuul01CjsmJ1DExGiReUa/Df2VqZbTK0GRFUBlVha7ZZ1mZY+IeNUt1BLsbFq1IJ/UQlrmV/G2DFF2fohVpdJ6SK2ahns0h7D2rXZE8hTxfoe6kHSVoAZUHXxQbcUzRiu9K1/iRuhHs+ygmR4Y8/u5sFcvSE5BBaof64RSTSP9n8qEZWkt7xHelpPhJXQ229tPbztCpdfqLvpF8pbqcfRnV7yCtYymbKGZhLCe+ztWyXjICK4RPYdX4Jexkn5Gfrh+2ccyqMqocU7Q011+9rnAbecQUBH0VMuIVpHruxmiyPlmPXVukhtNz513/dVi0ylAEYzmZo6byrrPnPayGlaGnoaz8BIuWErBJk/+XP1U/cplu7QmNAAAAAElFTkSuQmCC>

[image8]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACUAAAAWCAYAAABHcFUAAAABuUlEQVR4Xu2UPyiFURjGH0kRoYjEQkoWKUlWk8GfmJTByKAMBmU3CItYpJRSJiVZTDbFpmRgoGSTBUX58zzec+797nG5n9td6P7q1+285/3uec/5zvcCefL8DQrpEX2np3QydfqTcjoPy3mgdanTuWWEvtJSN66nV3SPlriYfh9plxuLW3ocGcemjQ6FwYB12O7H3biMHtI72upi3S6mOc8W7LlYaFfX9Bz2WjKh/D4kcxvoDZJF+CKX3bxnBlZUdRD/whS9pz2IV1A69Dq12IAb6+5okyoiyigsz59mCnrohe6EE79E90OLXND2SLwDdp/Covph+Z1BHBuwghrDiSyohG1wF7aYv/iZitLvJ0uwL6bKB3LMLGzBCXz/+oZhOSo6gU5Hp7QaDWZBMa0JYv4U9mEX+YzOpWQkL3pTEE+wQJ9oSzgRA/2xjDZDtQfFdD2EmqkK1AY8vpX8iDquOu0BLQjmfuIZ9ue+UerZFfpGe12sGdZiat1YHMKejY0+60s6iMytoYJu0xO6BrsSsiiaRBZhhY7RTdgp+o8hNipGn7kWioNemXJ1n1RoOnRiypkOJ/Lk+fd8AGkIWUNlesKYAAAAAElFTkSuQmCC>

[image9]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACUAAAAWCAYAAABHcFUAAAABjUlEQVR4Xu2UPyhGURjGH0kRMRAZSQplQVImMRhQshkMVmUwKKsMZFIWKVE2KYP9bl8xmKRsFjJZEMqf5/Xe+3Xue+/lur5Sur/69X3nPafuc8597wFyckJU0AZb/GsG6ROdpVMxBtTSVfpO72mzM1dylqAPivPSX1NFH2i/Pxau6YkzxijtdAu/YJeuQXfe6NRv6Ij/f4B6tKY4C+xDg4copxf0CtoXWTmi7c64jC7TOn8sQTy6ESzwWYSGivSjBBuit3TezGVlnJ47YzlB2biEcJmGhuow9QiH9BHZm1BOSU6/yan1QPvJhhqDhuoz9Vha6CvdsRMp6EL0NX0XSn5TUw8Nt2InEpDTkVOyO096fZPQUBI6FZv0BXpqaRmmb4j2iDSy9JjdXNDoraZeRHqhG3qpyQWXhQPoQ+L6cY4e00qnto2YKyFAAhXoHa02cz/BQ3KoNkQ/AI8+O+PPq2ACulB+S8EpNFTSxtahr3eG7kE/pNBauU3PoOFKRS/0Zv8KObEtumAncnL+PR8jAE9gxhsghgAAAABJRU5ErkJggg==>

[image10]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABcAAAAXCAYAAADgKtSgAAABIklEQVR4Xu2TPWsCQRRFn0QLmwSsIgg2abSJaGJISsFfkCalWFspCHZaCBZWKUM6f4RNmqRMZxUI2NlaJl1I7mWY8OY5+UALmz1wYOe+2bczs7siCfukDD/gJxzBw7C8PddwDauwLe4By2DGDnDFMzVuiXvAjcq2ho2opwbf4K3KPAc2UGRsQJrwVI3P4Tscq8zzCIc2BPcS7v5HOuJ2cmkLoAgXEq6S13N4pLIoKXGNH2zB8AL7cCp/z/3mAj7BY1swlOArfIYFU4vCLfOGnC1E4FFM4EDcbn+F58WXklVZ7GshbMZj4WLO4Cosh3AVdxI2ZoOuGnuY9+CJyurifsQo/re38nu38NgqNgRX4mob2KbevJ4E0hJv7GnYICHhf3wBwaczRUaBDVcAAAAASUVORK5CYII=>

[image11]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACEAAAAWCAYAAABOm/V6AAABGUlEQVR4XmNgGAWjAD9gBGInINZHl6ACUAbi+UD8H4i/ALEWqjQDwwEg/gvEGxkgioxRZCkHKkAcjMRnZYDYA7ITA/gy0MYRRUC8H4hlkMTeM0Ds4kQSAwNaOSKDAWJuMpLYUqgYhl2kOgIUr31AbIcugQaYgdgGSsPAYQaIXeJIYmBAqiOuMkDUv0WXIABAGQCk7zW6BAiQ6ghiQwIdmAPxVyD2RpcAAVIdQQ7YA8SP0AWRAa0dAcqaVxggWRYEQGkEJIYCSHUEyABQwuJAl8ACyhggoYAMQIlVEE2MZEfsYoCoB/kOHwAlxE9APB2IQ6B4FhCfAWIWmKKFDBDD0HE5TAEO0ArE/xgghuMDuMwH4VEwCkYBTgAAs1FBJ3bHZu4AAAAASUVORK5CYII=>

[image12]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAA4AAAAWCAYAAADwza0nAAAAgElEQVR4XmNgGAW0A55ArIUuSCxgBuLrQPwQiFnR5AgCkGYnIH4JxPlociSBdUD8DYgl0SWIAYpA/BeI56NLEAuEGSAGtKJL4ANTgfgXA8R2vIARiPWA+AsQd6LJ4QQgTceB+D0Qc6PJYQBQNPgzQOIRRBMNlgLxeQaIAaOAUgAAmNwQ7el6QG4AAAAASUVORK5CYII=>

[image13]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAFgAAAAXCAYAAACPm4iNAAADS0lEQVR4Xu2XS8hNURTHlzCQd+RRyluUkhQRExGlJAwMJJkwkwn5RkomBkgGkhIlEymZeKUbA6IoEXkMSCklI8rAY/2ss7+zzzqP2330DbR/9a979zr7nL3XXmvtvUUSiUSiZw6odvjGRP/4rbroGyPeqz7W6JFqXv5oiQVS7rMvs+3J/p/L9Fq1JrMNJfNVq1XDvUGZ5BuUqaqRvrGKYapTqj+qVtFUYo7Yc8e8QWwBsDV9dKPYM1dc+07VBrGxDDV3VZez34z9l5TncShri7UosjeyQnLnfHA2z2axSF/nDWJR91PMiXWMF/vOt6htq+pT9H+oeaGaG/0/LDbGuFziYOZN+3PVrsjWFtKbFKDzd2eLGSMW4VdVI4qmQSgxL1WTvSECZ/ItUmy5alvR3BZSeJPqnfS+Z4yWPCIDjJ05EHSMEXAw8++YWar12W8+8iM3lSAlvop9rArSm1QjC6Y7W8wZsW+dVL2R7ssCmXdbdVA1ztk6gZof7z3BwXGgdOVgUpqXB/xKek6L2euik/r8WfVANdbZYkapboqVk5XO1i1kIMFxTbpfsMBRsXkujdpw8FMxn7GZ3xcrbY20JN/JgfLQ5OAnYva68kB9xn5Bmic5TWyAPHukaOoJ0n2/6rFqrbN1AvsDG10MDo5PEovFnqPE1XJLimHfzsGUhyZ7iPCmTQ7YtW+IPfvK2foBdZn6vEWaTzRVsAnj3N2u3YPfGL8/Df2DjxJl252+iHUiEjxEJDbqUh3Y/crHUBrOi00CiAD60N5PunUwZ3A2Ng/1fUDK72LslYcCUrnKUS2xTlXFnLob0r+KmWJ2ztN1MAGiN8Dq06dfdTiUiIeqVc7WDpxHaZkRtd1TTZQ8M/FbDG1kdQGOOGwwVVHDTkqn+COBvWKrtcwblGfSHIm0nxBbhBgimSMix7bZztYJl8Q2uKaTSxOcQt5KMZvJgnCZ4jc3zXhfCReuwT0MI6t6XWyzWhIMYk6fkrXTiReGwRLNHM9wBAfyhZkNcfu6I5aOVZvKBLHrJ3bey3U5voYyhlZmOys2hqprah39OKbhl3Bz8yKogEBgniGAiPZwrfdl47+AiCWdO1mMfsCCHhcLrHABSSQSiUQikeiBv7unw9RAKfRSAAAAAElFTkSuQmCC>

[image14]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACUAAAAWCAYAAABHcFUAAAABVklEQVR4Xu2VMS8EURSFj4iExGoUohKVxCYaP0Ci0Ak6hU5vt1JutheJhkIjSo1EoVFN7Q9oFBRqDRJEODd32Dt39s3bsZqV+ZIv2bl3dubMe2/eABUVg8UEPfbFlDO6SqdTD+hF5ow/RG70Cb3BPT3Ntn+Qc6zz2XbvLNANXwwwThOEQ13RdehDTLlelDHoE9/QYdcrIhYqVI/SoI90GeUCCb2GWqF12+iGLLo3eu4bJYmF+qDb6e8R6Lra7bQ7nEADzfrGL4iFatIhc/xMX80x9qHJJ22xT2KhPAl0tGq2KKMjo3Roi31QFGqJtqDT9k0CDSXLpyt79IXO+UYJQqFG6SW9ozOmLm+4hLJTmkN24yfoflJ4YoBQKKGN/FJ5h1tTMTbpLV1DfGtYhC5av2PLSNipkes9QD83Mis7iF87h/zhGuFvWVlkPckedUS3XK+i4v/zBV6zRpyzir4dAAAAAElFTkSuQmCC>

[image15]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACUAAAAWCAYAAABHcFUAAAABsUlEQVR4Xu2UvytFYRjHv5IiQiiZRBaURUiZTBQplMFgsEkpBn+ADMogYZASZZNFNuluymIhFoNFSbKgKD++3/uc457zXtzDlaL7qU+n93nee+9z3ve5D5Ahw98gh57SF3pER8LpOIV0BrbnllaE0z/LFN0NrJvpDd2meV5Mzzva4m8iF/QgsEYnrQsG0uAMVkSWt9ZzgT7TDi/WSmO0wFuLDdiphcimJ/QcdvzfRdelLy8NxJq82BqskBidD+TFJGxPmROPF9ZOL+mYk4uKeqPLifXCfnAclteLq4ggg7A9tU48iS16j/SasJ5e0TnYVTbC+sktqhtWlE41JVX0ia66iYjoc/qxIm+dqig9I6MeUXHTbuIT+ugswj360fX5V6yiI7FIH2GnFhWNAl2b+lSowYthjXyM5JfzG73aib+hu2+ADTUNuK9SSQeQGAtiE9bMYpTu0NxEGit4ZyT46Iv2YbMm38lFoYTuwaZ4Px2mS/Satnl7amDjp9xbixh9CKzjR9wD26hnOqiJ9cauurLgDFKvaaAO0XXYHyJ0CJqmh0jc/2+hE1umE24iQ4Z/zyvu71aGK4mavAAAAABJRU5ErkJggg==>

[image16]: <data:image/png;base64,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>

[image17]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACUAAAAWCAYAAABHcFUAAAABgklEQVR4Xu2VTStFURSGX5kQmRApJVIyMZFkqgyRO1IG/oAyMPALDISJMpESZWpmYrTHKKWkZMLA1ARF+XjXXfZtn7W7H9tNSuepp3v3Wvucvc7ZHwfIyalKqw38Nb30xgZJG12jn/SJdmfTv8s7dOCQZvpMx4LYAz0N2jUzTGdtsAI90MFtUePUITuth4j7lUWe6o5e00aTq8Q0PaP7yA4mhTi6FcSEFWi/DhOPWKKPdAJpBQkX0MJsUbJ25CGliJB5aL8hEy8iF73RI5tIYBI6dYItagQ6pbaoKWi/URPHHrSgPptIoBM6bZ7UouS3yCZ0l7T7QB2cQ48Bjy2q3PQVoP2k6BLyduQtbYfBRFqg97gPlLYMJv8voQv5iq5+X+PxC73fxEus0xc6aBM/wCHe6ov0mDYFsV3E/SLkxJWT9oQ2mFwKDvFgA9AjpiuIOfoatKsyR2/pDGo/GvzCDZUF7tmgH3SBHkA3mUx/ElKMfAZ2bKIO5I3J/ZZtIifn3/MFoA1W/jcmozsAAAAASUVORK5CYII=>

[image18]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAEMAAAAWCAYAAACbiSE3AAADI0lEQVR4Xu2WS6iNURTH/0KRZ4gUuaaUiSgiEqK88ogiEwMyQAbEQLdkoAwMvDKRgQFJ5C3pZEKRRxED6iqUJCUU8lj/u/Z21rfOPvuec253wverf+fba+9vn2+vvdbaGygp+d8YLernjYa+ogHe+K+xSfQ1PE8X7ULtogeLnorGOHuPMEF0SfRb1CHqX+itD3frOfS9J6LNxe5OTosWQ3eeOii6YPqfiS6H516in6JPojWilaJjUGctCWN6lImi26IhxsbF7TXtFOy/adpTRR9FF1F0JueyouMttO027fuiUaZNJzw07RoWonbSVmkX7XS210E5XkIXz90k/D0k+iVaEAcJN0TLoNFhFxmhM+z/P4JGUISO6DIqekND7BU0XFthsuiLaK6zV6AfmYNpwTHDjW1KsJ00Nvucgv9/yrRPoOrgFWiiTtAhc0TvRFtdXyNwt/jxdIrlbLDnqjt3b5GzLYe+t93YojPmQ1PSc0b0NjzTsfPC8zjR4/DcEuegxcaGWQ6GZ8oZXADtg5w9Bxf6Hlog484SFsQN4ZkRzHl3VLs7YY05Do2ECNMjRgXnY2lIpVmW8dAPYLh1RVfOaNSphP/Hd2whJttQdA7T4ptpp2BUxDrBY5Zznxd9+DuiSRhydMo+32GolybMYdoHOns9uKMH0FjtqiAfdZzLnh4s5EzbSG49SQ6LvkOjJAcLJ6v/DGevQD+4j7On4JHK9GD9InTg0PA8S7QHRSdVkI861gl7enCsLcJXUXspK8AwnCT6LNrv+nIwV6+JNjo7j006KcKFjjTtCMN5NYppwF1cCy2+vEx1QMdFePpxgfadCOfypwfH2nuIP3oLcNI70DM/67E6rIPeD3xe3zXto9CPsqfBMNEt6K2TN0UWySPQvI6R1o7i0Ut+IF0z2qBXbo+PjCtw6cudWgq9Z/C3u9yDphUXxHxdj6JzGDnst8WRDuOHenFBI8y4F6I30Gs5T7otqKaU5QHS0ceNiEdvm2hatUthgeNHpyZtBc4zG7qzq4pd3Yb1gncMzs0oTDFWNNMbA4zA69Do6EA6vUpKSkpKmuEPyRimugW/nHcAAAAASUVORK5CYII=>