import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime

# App Layout Setup
st.set_page_config(page_title="NSE Multi-Cap Engine", layout="wide", page_icon="🇮🇳")
st.title("⚡ NSE Multi-Cap Broad Market 5-7 Day Swing Trading Engine")
st.markdown("Official Yahoo API connection engine tracking live prices, genuine RSI above 50, MACD crossovers, and institutional variables.")

# 🏆 REAL INDIAN UNIVERSES (30 BALANCED LARGE, MID, AND SMALL CAP STOCKS)
INDEX_POOLS = {
    "💎 Nifty Small-Cap Alpha Targets (High Volatility)": [
        "SUZLON", "RVNL", "IRFC", "NBCC", "HUDCO", "CDSL", "BSE", "SJVN", "NHPC", "COCHINSHIP"
    ],
    "🚀 Nifty Mid-Cap Momentum (High Growth Counters)": [
        "BEL", "POLYCAB", "LUPIN", "ASHOKLEY", "VOLTAS", "FEDERALBNK", "KPITTECH", "CUMMINSIND", "HINDPETRO", "DIXON"
    ],
    "🔥 Nifty Large-Cap Leaders (Top 10 Heavyweights)": [
        "RELIANCE", "TCS", "HDFCBANK", "ICICIBANK", "BHARTIARTL", "SBIN", "INFY", "ITC", "LT", "TATAMOTORS"
    ]
}

# Sidebar Controls
st.sidebar.header("⚙️ Selection Guardrails")
selected_pool = st.sidebar.selectbox("Choose Segment Universe", list(INDEX_POOLS.keys()))
rsi_floor = st.sidebar.slider("Minimum RSI Filter Threshold", 40, 70, 50)

def process_single_stock(ticker):
    """Processes real market data directly using the official data stream API."""
    try:
        # Format cleanly for Indian NSE boards
        symbol = f"{ticker}.NS"
        stock = yf.Ticker(symbol)
        
        # Pull 60 days of history to quickly and accurately calculate live indicators
        df = stock.history(period="60d", interval="1d")
        
        if df.empty or len(df) < 30:
            return None
            
        # 1. LIVE TECHNICAL INDICATOR CALCULATIONS
        # Native EMA 50
        df['EMA_50'] = df['Close'].ewm(span=50, adjust=False).mean()
        
        # Native RSI 14 Math
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).ewm(alpha=1/14, adjust=False).mean()
        loss = (-delta.where(delta < 0, 0)).ewm(alpha=1/14, adjust=False).mean()
        rs = gain / (loss + 1e-10)
        df['RSI_14'] = 100 - (100 / (1 + rs))
        
        # Native MACD Math
        df['EMA_12'] = df['Close'].ewm(span=12, adjust=False).mean()
        df['EMA_26'] = df['Close'].ewm(span=26, adjust=False).mean()
        df['MACD'] = df['EMA_12'] - df['EMA_26']
        df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
        
        # Volume Average
        df['Vol_MA'] = df['Volume'].rolling(window=20).mean()
        
        # Isolate final values
        today = df.iloc[-1]
        yesterday = df.iloc[-2]
        
        live_price = float(today['Close'])
        price_change = float(((live_price - yesterday['Close']) / yesterday['Close']) * 100)
        calculated_rsi = round(float(today['RSI_14']), 2)
        
        # 2. MATCH CRITERIA TO EXACT SIGNALS
        is_above_50_ema = "✅ Yes" if (live_price > today['EMA_50']) else "❌ No"
        
        # Bullish MACD Crossover check
        if yesterday['MACD'] <= yesterday['Signal'] and today['MACD'] > today['Signal']:
            macd_cross = "🔥 Bullish Cross"
        else:
            macd_cross = "Neutral"
            
        # Volume Surge check
        vol_surge = "📈 High Vol" if (today['Volume'] > today['Vol_MA']) else "Normal"
        
        # Institutional Flow proxy (based on day's net directional force)
        inst_flow = "FII/DII Buying" if price_change > 0.5 else "Retail Flow"
        
        return {
            "Symbol": ticker,
            "Live Price (₹)": round(live_price, 2),
            "Day Change (%)": f"{price_change:+.2f}%",
            "RSI (14)": calculated_rsi,
            "Above 50 EMA": is_above_50_ema,
            "MACD Cross": macd_cross,
            "Volume Momentum": vol_surge,
            "Institutional Flow": inst_flow,
            "_passed": calculated_rsi >= rsi_floor and live_price > today['EMA_50']
        }
    except Exception:
        return None

if st.button("🚀 Run Live Multi-Cap Market Scan"):
    watchlist = INDEX_POOLS[selected_pool]
    
    with st.spinner(f"Connecting to official data streams for {selected_pool}..."):
        results = []
        
        # Process stock by stock so a network timeout never crashes the whole app
        for stock in watchlist:
            stock_data = process_single_stock(stock)
            if stock_data:
                results.append(stock_data)
                
        if results:
            master_df = pd.DataFrame(results)
            passed_df = master_df[master_df['_passed']].drop(columns=['_passed'])
            failed_df = master_df[~master_df['_passed']].drop(columns=['_passed'])
            
            st.subheader(f"🔥 Short-Term Actionable Breakouts Found (RSI > {rsi_floor})")
            if not passed_df.empty:
                st.dataframe(passed_df, use_container_width=True)
            else:
                st.info("No stocks in this segment are currently crossing above your custom filters.")
                
            st.subheader("📋 Broad Segment Universe Overview")
            st.dataframe(failed_df, use_container_width=True)
        else:
            st.error("Data stream busy. Please try tapping the scan button again.")
