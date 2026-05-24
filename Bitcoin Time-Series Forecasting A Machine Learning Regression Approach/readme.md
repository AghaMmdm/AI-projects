# Algorithmic Trading Bot: Bitcoin Time-Series Forecasting

A production-grade Quantitative Trading pipeline that leverages Machine Learning (XGBoost) and Technical Analysis to predict Bitcoin (BTC) price movements and execute profitable simulated trades. 

## 📌 Project Overview
Unlike traditional classification models that predict simple "up/down" movements, this project models the exact **percentage returns** of Bitcoin 4-hour candles. By applying a custom trading logic over the model's continuous predictions, the strategy successfully generated substantial alpha during a bearish market phase.

## 📊 Backtest Performance & Results
The model's predictions were fed into a custom-built backtesting engine simulating real-world conditions (including a 0.1% threshold to account for exchange fees and market noise).

**Out-of-Sample Performance:**
| Metric | Result |
| :--- | :--- |
| **Total Market Return (Buy & Hold)** | `-34.26%` |
| **Total Strategy Return (XGBoost)** | **`+64.60%`** |
| **Total Trades Executed** | `261` |
| **Win Rate** | `56.32%` |
| **Maximum Drawdown** | `-20.25%` |

*Conclusion:* The ML strategy effectively hedged against market downturns, outperforming a simple Buy & Hold strategy by over 93% while maintaining a highly controlled maximum drawdown.

## 🛠️ Key Pipeline Architecture

### 1. Temporal Feature Engineering
* **Resampling:** Aggregated highly noisy 1-minute historical tick data into robust 4-Hour (4H) OHLCV candles.
* **Stationarity:** Converted all absolute price values into percentage changes to prevent algorithmic confusion caused by non-stationary macro trends.
* **Technical Indicators:** Integrated the `pandas-ta` library to inject market memory and momentum into the model using features like:
  - Relative Strength Index (RSI_14)
  - MACD (12, 26, 9)
  - Average True Range (ATR_14) converted to volatility percentage.
  - Bollinger Bands.

### 2. Preventing Temporal Data Leakage
Standard randomized cross-validation is fatal in time-series forecasting. Data was strictly split using **Chronological Indexing** (80% Train, 20% Test) to ensure the model never trains on future data.

### 3. Hyperparameter Optimization
Utilized **Optuna** to dynamically search the XGBoost hyperparameter space, aggressively minimizing the **Mean Absolute Error (MAE)** to achieve sub-1% error on 4H candle return predictions.

### 4. Custom Trading Engine
Built a vectorized backtesting engine using `pandas` and `numpy` to calculate:
* Long/Short/Hold Signals based on a defined risk threshold.
* Cumulative Returns.
* Dynamic Maximum Drawdown.
* Trade-by-Trade Win Rates.

### Dataset Note

Due to GitHub storage limits, the raw 1-minute Bitcoin historical data is not included in this repository.
Download the dataset from Kaggle: [Bitcoin Historical Data](https://www.kaggle.com/datasets/swaptr/bitcoin-historical-data).
Place the CSV file in the /Data folder.
Run the main.ipynb notebook from top to bottom.