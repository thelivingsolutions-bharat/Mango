import streamlit as st
import pandas as pd
import yfinance as yf
import pandas_ta as ta
from datetime import datetime

st.set_page_config(page_title="NSE Swing Screener", layout="wide", page_icon="🇮🇳")
st.title("⚡ NSE 5-7 Day Swing Trading Engine")
st.markdown("Configured for Indian Markets using precise Yahoo Finance NSE feeds with local institutional parameters.")

tickers_input = st.sidebar.text_area("Target NSE Watchlist (Comma-separated)", value="RELIANCE, TCS, INFY, HDFCBANK, TATAMOTORS")
watchlist = [t.strip().upper() for t in tickers_input.split(",") if t.strip()]

rsi_threshold = st.sidebar.slider("Minimum RSI Level", 40, 70, 50)

def process_nse_metrics(ticker):
    try:
        # Convert simple NSE ticker to yfinance symbol format (e.g., RELIANCE -> RELIANCE.NS)
        yf_symbol = f"{ticker}.NS" if not ticker.endswith(".NS") else ticker
        stock = yf.Ticker(yf_symbol)
        df = stock.history(period="1y")
        
        if df.empty or len(df) < 100:
            return None
            
        df['EMA_50'] = ta.ema(df['Close'], length=50)
        df['EMA_200'] = ta.ema(df['Close'], length=200)
        df['RSI_14'] = ta.rsi(df['Close'], length=14)
        
        macd_output = ta.macd(df['Close'], fast=12, slow=26, signal=9)
        df = pd.concat([df, macd_output], axis=1)
        
        today = df.iloc[-1]
        yesterday = df.iloc[-2]
        
        above_50_ema = today['Close'] > today['EMA_50']
        rsi_valid = today['RSI_14'] >= rsi_threshold
        golden_cross = today['EMA_50'] > today['EMA_200']
        
        macd_crossover = (yesterday['MACD_12_26_9'] <= yesterday['MACDs_12_26_9']) and (today['MACD_12_26_9'] > today['MACDs_12_26_9'])
        
        # Pull profile matrices for structural information proxies
        info = stock.info
        inst_float_pct = info.get('heldPercentInstitutions', 0.55) # Fallback to standard institutional float baseline
        
        return {
            "Symbol": ticker,
            "Price (₹)": round(today['Close'], 2),
            "RSI (14)": round(today['RSI_14'], 2),
            "Above 50 EMA": "✅ Yes" if above_50_ema else "❌ No",
            "MACD Cross": "🔥 Active Trigger" if macd_crossover else "Inactive",
            "Golden Cross": "⚡ Bullish Shift" if golden_cross else "Bearish",
            "Inst. Holding": f"{round(inst_float_pct * 100, 1)}%",
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
        
        st.subheader("🔥 Top High-Conviction Breakouts")
        st.dataframe(passed_df, use_container_width=True)
        
        st.subheader("📋 Watchlist Overview")
        st.dataframe(failed_df, use_container_width=True)
    else:
        st.error("No data could be processed. Please check the symbols or code parameters.")
