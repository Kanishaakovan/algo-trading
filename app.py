"""
Tick Data Analysis Dashboard for First Minute Breakout Strategy
Analyzes tick-by-tick data stored in market_data.db and calculates potential trades
"""

import sqlite3
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import json

# Page configuration
st.set_page_config(
    page_title="Tick Analysis - First Minute Breakout",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Constants
DEFAULT_INSTRUMENT = "NSE_EQ|INE669E01016"
DB_PATH = 'market_data.db'


def get_available_instruments(db_path: str = DB_PATH) -> List[str]:
    """Get list of instruments with tick data"""
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DISTINCT instrument, COUNT(*) as tick_count, 
                       DATE(MIN(timestamp)) as first_date,
                       DATE(MAX(timestamp)) as last_date
                FROM ticks 
                GROUP BY instrument 
                ORDER BY tick_count DESC
            """)
            results = cursor.fetchall()
            return results
    except Exception as e:
        st.error(f"Error fetching instruments: {e}")
        return []


def get_tick_data(instrument: str, date: str, db_path: str = DB_PATH) -> pd.DataFrame:
    """Get all tick data for a specific instrument and date"""
    try:
        with sqlite3.connect(db_path) as conn:
            query = """
            SELECT 
                timestamp,
                ltp,
                COALESCE(high, ltp) as high,
                COALESCE(low, ltp) as low,
                close_price
            FROM ticks
            WHERE instrument = ?
            AND DATE(timestamp) = ?
            ORDER BY timestamp
            """
            
            df = pd.read_sql_query(query, conn, params=(instrument, date))
            
            if not df.empty:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                
            return df
    except Exception as e:
        st.error(f"Error fetching tick data: {e}")
        return pd.DataFrame()


def get_first_minute_data(df: pd.DataFrame) -> Tuple[Optional[float], Optional[float], str]:
    """Extract first minute high and low (9:15 AM or first available minute)"""
    if df.empty:
        return None, None, "No data"
    
    # Try to find 9:15 AM data first
    first_minute = df[
        (df['timestamp'].dt.hour == 9) & 
        (df['timestamp'].dt.minute == 15)
    ]
    
    if not first_minute.empty:
        h1 = first_minute['high'].max()
        l1 = first_minute['low'].min()
        return h1, l1, "9:15 AM"
    
    # If 9:15 AM data not found, use the first available minute of data
    first_timestamp = df['timestamp'].min()
    first_minute_time = first_timestamp.replace(second=0, microsecond=0)
    next_minute_time = first_minute_time + timedelta(minutes=1)
    
    first_minute = df[
        (df['timestamp'] >= first_minute_time) & 
        (df['timestamp'] < next_minute_time)
    ]
    
    if first_minute.empty:
        # Fallback: use first 60 seconds of data
        first_minute = df.head(min(60, len(df)))
    
    h1 = first_minute['high'].max()
    l1 = first_minute['low'].min()
    first_min_str = first_minute_time.strftime('%H:%M')
    
    return h1, l1, f"{first_min_str} (First available minute)"


def calculate_trades(df: pd.DataFrame, h1: float, l1: float, 
                     target_pct: float = 0.01, stop_loss_pct: float = 0.002,
                     first_minute_end_time: pd.Timestamp = None) -> List[Dict]:
    """Calculate all trades based on first minute breakout strategy"""
    trades = []
    position = None
    entry_price = None
    entry_time = None
    trade_id = 0
    
    for idx, row in df.iterrows():
        timestamp = row['timestamp']
        high = row['high']
        low = row['low']
        ltp = row['ltp']
        
        # Skip first minute based on actual first minute end time
        if first_minute_end_time and timestamp < first_minute_end_time:
            continue
        
        # Check for exit if in position
        if position:
            if position == 'BUY':
                target = entry_price * (1 + target_pct)
                stop_loss = entry_price * (1 - stop_loss_pct)
                
                if ltp >= target:
                    trade_id += 1
                    trades.append({
                        'trade_id': trade_id,
                        'type': 'BUY',
                        'entry_time': entry_time,
                        'entry_price': entry_price,
                        'exit_time': timestamp,
                        'exit_price': ltp,
                        'exit_reason': 'TARGET',
                        'pnl': ltp - entry_price,
                        'pnl_pct': ((ltp - entry_price) / entry_price) * 100,
                        'duration': str(timestamp - entry_time)
                    })
                    position = None
                    entry_price = None
                    entry_time = None
                    
                elif ltp <= stop_loss:
                    trade_id += 1
                    trades.append({
                        'trade_id': trade_id,
                        'type': 'BUY',
                        'entry_time': entry_time,
                        'entry_price': entry_price,
                        'exit_time': timestamp,
                        'exit_price': ltp,
                        'exit_reason': 'STOPLOSS',
                        'pnl': ltp - entry_price,
                        'pnl_pct': ((ltp - entry_price) / entry_price) * 100,
                        'duration': str(timestamp - entry_time)
                    })
                    position = None
                    entry_price = None
                    entry_time = None
                    
            elif position == 'SELL':
                target = entry_price * (1 - target_pct)
                stop_loss = entry_price * (1 + stop_loss_pct)
                
                if ltp <= target:
                    trade_id += 1
                    trades.append({
                        'trade_id': trade_id,
                        'type': 'SELL',
                        'entry_time': entry_time,
                        'entry_price': entry_price,
                        'exit_time': timestamp,
                        'exit_price': ltp,
                        'exit_reason': 'TARGET',
                        'pnl': entry_price - ltp,
                        'pnl_pct': ((entry_price - ltp) / entry_price) * 100,
                        'duration': str(timestamp - entry_time)
                    })
                    position = None
                    entry_price = None
                    entry_time = None
                    
                elif ltp >= stop_loss:
                    trade_id += 1
                    trades.append({
                        'trade_id': trade_id,
                        'type': 'SELL',
                        'entry_time': entry_time,
                        'entry_price': entry_price,
                        'exit_time': timestamp,
                        'exit_price': ltp,
                        'exit_reason': 'STOPLOSS',
                        'pnl': entry_price - ltp,
                        'pnl_pct': ((entry_price - ltp) / entry_price) * 100,
                        'duration': str(timestamp - entry_time)
                    })
                    position = None
                    entry_price = None
                    entry_time = None
        
        # Check for entry if not in position
        if not position:
            # Breakout above H1
            if high > h1:
                position = 'BUY'
                entry_price = ltp
                entry_time = timestamp
                
            # Breakdown below L1
            elif low < l1:
                position = 'SELL'
                entry_price = ltp
                entry_time = timestamp
    
    return trades


def create_tick_chart(df: pd.DataFrame, h1: float, l1: float, trades: List[Dict]) -> go.Figure:
    """Create detailed tick chart with trades"""
    fig = go.Figure()
    
    # Add tick line
    fig.add_trace(go.Scatter(
        x=df['timestamp'],
        y=df['ltp'],
        mode='lines',
        line=dict(color='blue', width=1),
        name='LTP (Tick by Tick)',
        hovertemplate='Time: %{x}<br>Price: ₹%{y:.2f}<extra></extra>'
    ))
    
    # Add high/low bands
    fig.add_trace(go.Scatter(
        x=df['timestamp'],
        y=df['high'],
        mode='lines',
        line=dict(color='lightgreen', width=1, dash='dot'),
        name='High',
        opacity=0.5
    ))
    
    fig.add_trace(go.Scatter(
        x=df['timestamp'],
        y=df['low'],
        mode='lines',
        line=dict(color='lightcoral', width=1, dash='dot'),
        name='Low',
        opacity=0.5
    ))
    
    # Add H1 and L1 lines
    fig.add_hline(
        y=h1, 
        line_dash="dash", 
        line_color="blue", 
        line_width=3,
        annotation_text=f"H1 Breakout: ₹{h1:.2f}",
        annotation_position="right"
    )
    
    fig.add_hline(
        y=l1, 
        line_dash="dash", 
        line_color="orange", 
        line_width=3,
        annotation_text=f"L1 Breakdown: ₹{l1:.2f}",
        annotation_position="right"
    )
    
    # Add buy signals
    buy_entries = [t for t in trades if t['type'] == 'BUY']
    if buy_entries:
        fig.add_trace(go.Scatter(
            x=[t['entry_time'] for t in buy_entries],
            y=[t['entry_price'] for t in buy_entries],
            mode='markers+text',
            marker=dict(symbol='triangle-up', size=15, color='lime', 
                       line=dict(color='darkgreen', width=2)),
            name='BUY Entry',
            text=['BUY' for _ in buy_entries],
            textposition="top center",
            textfont=dict(size=10, color='darkgreen')
        ))
    
    # Add sell signals
    sell_entries = [t for t in trades if t['type'] == 'SELL']
    if sell_entries:
        fig.add_trace(go.Scatter(
            x=[t['entry_time'] for t in sell_entries],
            y=[t['entry_price'] for t in sell_entries],
            mode='markers+text',
            marker=dict(symbol='triangle-down', size=15, color='red',
                       line=dict(color='darkred', width=2)),
            name='SELL Entry',
            text=['SELL' for _ in sell_entries],
            textposition="bottom center",
            textfont=dict(size=10, color='darkred')
        ))
    
    # Add exit points
    for trade in trades:
        exit_color = 'green' if trade['pnl'] > 0 else 'red'
        fig.add_trace(go.Scatter(
            x=[trade['exit_time']],
            y=[trade['exit_price']],
            mode='markers',
            marker=dict(symbol='x', size=12, color=exit_color),
            name=f"Exit ({trade['exit_reason']})",
            showlegend=False,
            hovertemplate=f"Exit: ₹{trade['exit_price']:.2f}<br>" +
                         f"P&L: ₹{trade['pnl']:.2f} ({trade['pnl_pct']:.2f}%)<br>" +
                         f"Reason: {trade['exit_reason']}<extra></extra>"
        ))
    
    fig.update_layout(
        title='Tick-by-Tick Price Chart with First Minute Breakout Trades',
        xaxis_title='Time',
        yaxis_title='Price (₹)',
        height=700,
        hovermode='x unified',
        showlegend=True
    )
    
    return fig


def main():
    st.title("📊 Tick Data Analysis - First Minute Breakout Strategy")
    st.markdown("Analyze tick-by-tick data and calculate potential trades using first minute breakout strategy")
    
    # Sidebar controls
    st.sidebar.header("⚙️ Settings")
    
    # Get available instruments
    instruments_data = get_available_instruments()
    
    if not instruments_data:
        st.error("No instruments found in database!")
        st.info("Please upload a market_data.db file with tick data in the 'ticks' table.")
        return
    
    # Display instrument selection
    st.sidebar.subheader("Available Instruments")
    instrument_options = []
    for inst, count, first_date, last_date in instruments_data:
        label = f"{inst} ({count:,} ticks, {first_date} to {last_date})"
        instrument_options.append((inst, label))
    
    selected_idx = st.sidebar.selectbox(
        "Select Instrument",
        options=range(len(instrument_options)),
        format_func=lambda x: instrument_options[x][1],
        index=0
    )
    
    selected_instrument = instrument_options[selected_idx][0]
    
    # Date selection
    analysis_date = st.sidebar.date_input(
        "Analysis Date",
        value=datetime.today().date(),
        help="Select date to analyze tick data"
    )
    
    # Strategy parameters
    st.sidebar.markdown("---")
    st.sidebar.subheader("📈 Strategy Parameters")
    target_pct = st.sidebar.number_input(
        "Target %",
        min_value=0.1,
        max_value=10.0,
        value=1.0,
        step=0.1,
        help="Profit target as percentage"
    ) / 100
    
    stop_loss_pct = st.sidebar.number_input(
        "Stop Loss %",
        min_value=0.05,
        max_value=5.0,
        value=0.2,
        step=0.05,
        help="Stop loss as percentage"
    ) / 100
    
    # Analyze button
    if st.sidebar.button("🔍 Analyze Ticks", type="primary"):
        st.session_state.analyze_requested = True
    
    # Main analysis
    if st.session_state.get('analyze_requested', False):
        with st.spinner(f"Loading tick data for {selected_instrument} on {analysis_date}..."):
            df = get_tick_data(selected_instrument, analysis_date.strftime('%Y-%m-%d'))
        
        if df.empty:
            st.warning(f"No tick data found for {selected_instrument} on {analysis_date}")
            return
        
        # Display basic statistics
        st.header("📋 Tick Data Summary")
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric("Total Ticks", f"{len(df):,}")
        
        with col2:
            st.metric("First Tick", df['timestamp'].min().strftime('%H:%M:%S'))
        
        with col3:
            st.metric("Last Tick", df['timestamp'].max().strftime('%H:%M:%S'))
        
        with col4:
            st.metric("Day High", f"₹{df['high'].max():.2f}")
        
        with col5:
            st.metric("Day Low", f"₹{df['low'].min():.2f}")
        
        # Get first minute data
        h1, l1, first_minute_label = get_first_minute_data(df)
        
        if h1 is None or l1 is None:
            st.error("Could not extract first minute data from the available ticks!")
            return
        
        # Calculate first minute end time
        first_timestamp = df['timestamp'].min()
        first_minute_end = first_timestamp.replace(second=0, microsecond=0) + timedelta(minutes=1)
        
        # Show info about first minute
        if "9:15" not in first_minute_label:
            st.info(f"ℹ️ Note: Data doesn't start at market open (9:15 AM). Using {first_minute_label} as the reference period for H1/L1 calculation.")
        
        # Display first minute levels
        st.markdown("---")
        st.header("🎯 First Minute Breakout Levels")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(f"""
            <div style='background-color: #e3f2fd; padding: 20px; border-radius: 10px; 
                        border-left: 5px solid #2196F3; text-align: center;'>
                <h3 style='color: #1976D2; margin: 0;'>🔵 H1 (High)</h3>
                <h2 style='color: #1976D2; margin: 10px 0;'>₹{h1:.2f}</h2>
                <p style='margin: 0;'>Breakout trigger for BUY</p>
                <p style='margin: 5px 0; font-size: 0.85em;'>From: {first_minute_label}</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div style='background-color: #fff3e0; padding: 20px; border-radius: 10px; 
                        border-left: 5px solid #FF9800; text-align: center;'>
                <h3 style='color: #F57C00; margin: 0;'>🟠 L1 (Low)</h3>
                <h2 style='color: #F57C00; margin: 10px 0;'>₹{l1:.2f}</h2>
                <p style='margin: 0;'>Breakdown trigger for SELL</p>
                <p style='margin: 5px 0; font-size: 0.85em;'>From: {first_minute_label}</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            range_val = h1 - l1
            range_pct = (range_val / l1) * 100
            st.markdown(f"""
            <div style='background-color: #f3e5f5; padding: 20px; border-radius: 10px; 
                        border-left: 5px solid #9C27B0; text-align: center;'>
                <h3 style='color: #7B1FA2; margin: 0;'>📏 Range</h3>
                <h2 style='color: #7B1FA2; margin: 10px 0;'>₹{range_val:.2f}</h2>
                <p style='margin: 0;'>{range_pct:.2f}% of price</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Calculate trades
        st.markdown("---")
        st.header("💼 Trade Analysis")
        
        with st.spinner("Calculating potential trades..."):
            trades = calculate_trades(df, h1, l1, target_pct, stop_loss_pct, first_minute_end)
        
        if not trades:
            st.info("No trades would be placed based on the strategy parameters.")
        else:
            # Trade statistics
            total_trades = len(trades)
            winning_trades = len([t for t in trades if t['pnl'] > 0])
            losing_trades = len([t for t in trades if t['pnl'] <= 0])
            total_pnl = sum(t['pnl'] for t in trades)
            avg_pnl = total_pnl / total_trades
            win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0
            
            # Display trade metrics
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                st.metric("Total Trades", total_trades)
            
            with col2:
                st.metric("Winning Trades", winning_trades, delta=f"{win_rate:.1f}%")
            
            with col3:
                st.metric("Losing Trades", losing_trades)
            
            with col4:
                pnl_color = "🟢" if total_pnl > 0 else "🔴"
                st.metric("Total P&L", f"{pnl_color} ₹{total_pnl:.2f}")
            
            with col5:
                avg_color = "🟢" if avg_pnl > 0 else "🔴"
                st.metric("Avg P&L/Trade", f"{avg_color} ₹{avg_pnl:.2f}")
            
            # Display chart
            st.markdown("---")
            st.subheader("📈 Tick Chart with Trade Signals")
            fig = create_tick_chart(df, h1, l1, trades)
            st.plotly_chart(fig, use_container_width=True)
            
            # Trade details table
            st.markdown("---")
            st.subheader("📊 Trade Details")
            
            trades_df = pd.DataFrame(trades)
            
            # Format for display
            display_df = trades_df.copy()
            display_df['entry_time'] = pd.to_datetime(display_df['entry_time']).dt.strftime('%H:%M:%S')
            display_df['exit_time'] = pd.to_datetime(display_df['exit_time']).dt.strftime('%H:%M:%S')
            display_df['entry_price'] = display_df['entry_price'].apply(lambda x: f"₹{x:.2f}")
            display_df['exit_price'] = display_df['exit_price'].apply(lambda x: f"₹{x:.2f}")
            display_df['pnl'] = display_df['pnl'].apply(lambda x: f"₹{x:.2f}")
            display_df['pnl_pct'] = display_df['pnl_pct'].apply(lambda x: f"{x:.2f}%")
            
            # Rename columns
            display_df = display_df.rename(columns={
                'trade_id': 'Trade #',
                'type': 'Type',
                'entry_time': 'Entry Time',
                'entry_price': 'Entry Price',
                'exit_time': 'Exit Time',
                'exit_price': 'Exit Price',
                'exit_reason': 'Exit Reason',
                'pnl': 'P&L',
                'pnl_pct': 'P&L %',
                'duration': 'Duration'
            })
            
            st.dataframe(display_df, use_container_width=True, height=400)
            
            # Export trades
            st.markdown("---")
            st.subheader("💾 Export Analysis")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Export as JSON
                export_data = {
                    'instrument': selected_instrument,
                    'date': analysis_date.strftime('%Y-%m-%d'),
                    'first_minute': {
                        'high': h1,
                        'low': l1,
                        'range': h1 - l1
                    },
                    'strategy_params': {
                        'target_pct': target_pct * 100,
                        'stop_loss_pct': stop_loss_pct * 100
                    },
                    'summary': {
                        'total_trades': total_trades,
                        'winning_trades': winning_trades,
                        'losing_trades': losing_trades,
                        'win_rate': win_rate,
                        'total_pnl': total_pnl,
                        'avg_pnl': avg_pnl
                    },
                    'trades': trades
                }
                
                json_str = json.dumps(export_data, indent=2, default=str)
                st.download_button(
                    label="📥 Download as JSON",
                    data=json_str,
                    file_name=f"tick_analysis_{selected_instrument.replace('|', '_')}_{analysis_date.strftime('%Y%m%d')}.json",
                    mime="application/json"
                )
            
            with col2:
                # Export as CSV
                csv_data = trades_df.to_csv(index=False)
                st.download_button(
                    label="📥 Download Trades as CSV",
                    data=csv_data,
                    file_name=f"trades_{selected_instrument.replace('|', '_')}_{analysis_date.strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )


if __name__ == "__main__":
    main()
