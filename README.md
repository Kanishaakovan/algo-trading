---
title: Tick Data Analysis - First Minute Breakout
emoji: 📊
colorFrom: blue
colorTo: green
sdk: streamlit
sdk_version: "1.31.1"
app_file: app.py
pinned: false
license: mit
---

# 📊 Tick Data Analysis - First Minute Breakout Strategy

A powerful Streamlit dashboard for analyzing tick-by-tick market data using the First Minute Breakout trading strategy. This tool helps traders visualize and backtest intraday breakout strategies based on the first minute's high and low levels.

## 🎯 Features

### 📈 Strategy Implementation
- **First Minute Breakout**: Uses the first minute's high (H1) and low (L1) as key trading levels
- **Automatic Signal Generation**: Detects breakouts above H1 (BUY) and breakdowns below L1 (SELL)
- **Risk Management**: Configurable target percentage and stop-loss percentage
- **Trade Tracking**: Monitors entry, exit, P&L, and win rate for each trade

### 📊 Visualization
- **Interactive Tick Charts**: Real-time price movements with Plotly
- **Trade Markers**: Clear visual indicators for entry and exit points
- **H1/L1 Reference Lines**: Visual breakout/breakdown trigger levels
- **Performance Metrics**: Win rate, total P&L, and average P&L per trade

### 💾 Data Management
- **SQLite Database Support**: Reads from `market_data.db` with tick data
- **Multi-Instrument Support**: Analyze multiple instruments from the database
- **Date Selection**: Choose specific dates for historical analysis
- **Export Options**: Download analysis as JSON or CSV

## 🚀 Getting Started

### Prerequisites
Upload a SQLite database file named `market_data.db` with the following schema:

```sql
CREATE TABLE ticks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME NOT NULL,
    instrument TEXT NOT NULL,
    ltp REAL NOT NULL,
    close_price REAL,
    high REAL,
    low REAL
);
```

### Configuration

1. **Select Instrument**: Choose from available instruments in the database
2. **Set Analysis Date**: Pick the date you want to analyze
3. **Configure Strategy**:
   - **Target %**: Profit target as a percentage (default: 1.0%)
   - **Stop Loss %**: Maximum loss tolerance (default: 0.2%)
4. Click **🔍 Analyze Ticks** to run the analysis

## 📋 How It Works

### Strategy Logic

1. **First Minute Identification**: 
   - Tries to find 9:15 AM data (market open)
   - Falls back to first available minute if 9:15 AM data not found
   - Extracts H1 (high) and L1 (low) from that period

2. **Trade Entry**:
   - **BUY Signal**: Price breaks above H1
   - **SELL Signal**: Price breaks below L1

3. **Trade Exit**:
   - **Target Hit**: Price reaches target percentage gain
   - **Stop Loss Hit**: Price reaches stop loss percentage loss

4. **Position Management**:
   - Only one position at a time (no pyramiding)
   - New signals ignored while in position
   - Automatic exit on target or stop loss

### Output Metrics

- **Total Trades**: Number of trades executed
- **Winning/Losing Trades**: Trade breakdown by outcome
- **Win Rate**: Percentage of profitable trades
- **Total P&L**: Cumulative profit/loss
- **Average P&L**: Average profit/loss per trade

## 📊 Dashboard Sections

### 1. Tick Data Summary
- Total tick count
- First and last tick timestamps
- Day's high and low prices

### 2. First Minute Breakout Levels
- **H1 (High)**: Breakout trigger for BUY signals
- **L1 (Low)**: Breakdown trigger for SELL signals
- **Range**: Price range of first minute (H1 - L1)

### 3. Trade Analysis
- Performance metrics (trades, win rate, P&L)
- Interactive chart with all trades marked
- Detailed trade table with entry/exit information

### 4. Export Options
- **JSON Export**: Complete analysis with metadata
- **CSV Export**: Trade details in spreadsheet format

## 🔧 Technical Details

### Data Requirements
- Tick-by-tick data stored in SQLite database
- Each tick should include: timestamp, instrument, LTP, high, low
- Data should be organized by date and instrument

### Chart Features
- **Blue Line**: Last Traded Price (LTP) tick-by-tick
- **Green Dots**: Tick high values
- **Red Dots**: Tick low values
- **Blue Dashed Line**: H1 breakout level
- **Orange Dashed Line**: L1 breakdown level
- **Green Triangles**: BUY entry points
- **Red Triangles**: SELL entry points
- **X Markers**: Exit points (green = profit, red = loss)

## 📝 Example Use Cases

1. **Strategy Backtesting**: Test first minute breakout strategy on historical tick data
2. **Parameter Optimization**: Experiment with different target and stop loss percentages
3. **Multi-Day Analysis**: Compare strategy performance across different trading days
4. **Instrument Comparison**: Analyze which instruments work best with this strategy
5. **Trade Review**: Review individual trades with exact entry/exit timestamps

## 🎓 Trading Strategy Explanation

The **First Minute Breakout Strategy** is based on the premise that the first minute's price range often sets the tone for intraday movements:

- **High (H1)**: Represents initial resistance; breakout suggests bullish momentum
- **Low (L1)**: Represents initial support; breakdown suggests bearish momentum
- **Range**: Wider ranges may indicate higher volatility and larger potential moves

This strategy works best in:
- Trending markets with clear directional bias
- High volatility stocks/instruments
- Instruments with sufficient liquidity

## ⚠️ Disclaimer

This tool is for educational and analysis purposes only. Past performance does not guarantee future results. Always conduct thorough research and risk management before live trading.

## 📄 License

MIT License - Feel free to use and modify for your trading analysis needs.

## 🙋‍♂️ Support

For issues or questions, please refer to the dashboard's interactive help sections or consult the strategy documentation.

---

Built with ❤️ using Streamlit, Pandas, and Plotly
