import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime

# App Layout Setup
st.set_page_config(page_title="NSE Swing Screener", layout="wide", page_icon="🇮🇳")
st.title("⚡ NSE 5-7 Day Swing Trading Engine")
st.markdown("Calculates RSI, EMA, and MACD natively for the Indian Stock Market.")

# Inputs
tickers_input = st.sidebar.text_area("Target NSE Watchlist (Comma-separated)", value="RELIANCE, TCS, INFY, HDFCBANK, TATAMOTORS, SBIN, BHARTIARTL")
watchlist = [t.strip().upper() for t in tickers_input.split(",") if t.strip()]
rsi_threshold = st.sidebar.slider("Minimum RSI Level", 40, 70, 50)

def calculate_indicators(df):
    """Calculates all technical metrics using native math formulas to avoid install errors."""
    # 1. EMA Calculations
    df['EMA_50'] = df['Close'].ewm(span=50, adjust=False).mean()
    df['EMA_200'] = df['Close'].ewm(span=200, adjust=False).mean()
    
    # 2. Native RSI Calculation
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).ewm(alpha=1/14, adjust=False).mean()
    loss = (-delta.where(delta < 0, 0)).ewm(alpha=1/14, adjust=False).mean()
    rs = gain / (loss + 1e-10) # Avoid division by zero
    df['RSI_14'] = 100 - (100 / (1 + rs))
    
    # 3. Native MACD Calculation
    ema12 = df['Close'].ewm(span=12, adjust=False).mean()
    ema26 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = ema12 - ema26
    df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    
    # 4. Volume Moving Average
    df['Vol_MA'] = df['Volume'].rolling(window=20).mean()
    return df

def process_nse_metrics(ticker):
    try:
        yf_symbol = f"{ticker}.NS" if not ticker.endswith(".NS") else ticker
        stock = yf.Ticker(yf_symbol)
        df = stock.history(period="1y")
        
        if df.empty or len(df) < 200:
            return None
            
        df = calculate_indicators(df)
        
        today = df.iloc[-1]
        yesterday = df.iloc[-2]
        
        # Strategies & Rules Filters
        above_50_ema = today['Close'] > today['EMA_50']
        rsi_valid = today['RSI_14'] >= rsi_threshold
        golden_cross = today['EMA_50'] > today['EMA_200']
        volume_surging = today['Volume'] > today['Vol_MA']
        
        # Checking for a fresh crossover between MACD and Signal line
        macd_crossover = (yesterday['MACD'] <= yesterday['Signal']) and (today['MACD'] > today['Signal'])
        
        info = stock.info
        inst_float_pct = info.get('heldPercentInstitutions', 0.0)
        inst_footprint = f"{round(inst_float_pct * 100, 1)}%" if inst_float_pct else "N/A"
        
        return {
            "Symbol": ticker,
            "Price (₹)": round(today['Close'], 2),
            "RSI (14)": round(today['RSI_14'], 2),
            "Above 50 EMA": "✅ Yes" if above_50_ema else "❌ No",
            "MACD Cross": "🔥 Active Trigger" if macd_crossover else "Inactive",
            "Golden Cross": "⚡ Bullish Shift" if golden_cross else "Bearish",
            "Vol Surge": "📈 High Vol" if volume_surging else "Normal",
            "Inst. Holding": inst_footprint,
            "_passed": (above_50_ema and rsi_valid)
        }
    except Exception:
        return None

if st.button("🚀 Scan Indian Markets"):
    compiled = [process_nse_metrics(t) for t in watchlist if t]
    compiled = [c for c in compiled if c is not None]
    
    if compiled:
        master_df = pd.DataFrame(compiled)
        passed_df = master_df[master_df['_passed']].drop(columns=['_passed'])
        failed_df = master_df[~master_df['_passed']].drop(columns=['_passed'])
        
        st.subheader("🔥 Top High-Conviction Breakouts (5-7 Day Setup)")
        st.dataframe(passed_df, use_container_width=True)
        
        st.subheader("📋 Watchlist Baseline Overview")
        st.dataframe(failed_df, use_container_width=True)
    else:
        st.error("No data could be processed. Please check the symbols or configuration settings.")
