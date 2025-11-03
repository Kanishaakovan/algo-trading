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

Analyze tick-by-tick market data using the First Minute Breakout trading strategy. Visualize and backtest intraday breakout strategies based on the first minute's high (H1) and low (L1) levels.

## 🎯 Key Features

- **First Minute Breakout**: Uses H1/L1 from first minute as key trading levels
- **Automatic Signals**: BUY on breakout above H1, SELL on breakdown below L1
- **Risk Management**: Configurable target % and stop-loss %
- **Interactive Charts**: Plotly visualizations with trade markers and entry/exit points
- **Multi-Instrument**: Analyze multiple instruments from SQLite database
- **Export Options**: Download analysis as JSON or CSV

## 🚀 Quick Start

1. **Upload Database**: Include `market_data.db` with tick data (schema below)
2. **Select Instrument**: Choose from available instruments
3. **Set Date**: Pick analysis date
4. **Configure**: Set target % (default: 1.0%) and stop loss % (default: 0.2%)
5. **Analyze**: Click "🔍 Analyze Ticks" to run

### Database Schema
```sql
CREATE TABLE ticks (
    timestamp DATETIME NOT NULL,
    instrument TEXT NOT NULL,
    ltp REAL NOT NULL,
    high REAL,
    low REAL
);
```

## 📋 How It Works

**Strategy Logic:**
1. Extract H1 (high) and L1 (low) from first minute (9:15 AM or first available)
2. Enter BUY when price breaks above H1
3. Enter SELL when price breaks below L1
4. Exit on target hit or stop loss hit
5. One position at a time, no pyramiding

**Metrics:** Total trades, win rate, P&L, average P&L per trade

## 🔧 Chart Elements

- **Blue Line**: Tick-by-tick LTP
- **Blue/Orange Dashed Lines**: H1/L1 breakout levels
- **Green/Red Triangles**: BUY/SELL entry points
- **X Markers**: Exit points (green=profit, red=loss)

## ⚠️ Disclaimer

Educational purposes only. Past performance doesn't guarantee future results. Always practice proper risk management.

---

Built with Streamlit, Pandas, and Plotly | MIT License
