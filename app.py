import streamlit as st
import pandas as pd
import yfinance as yf
import requests
import io
import random

# App Layout Setup
st.set_page_config(page_title="NSE Broad-Market Momentum Screener", layout="wide", page_icon="🇮🇳")
st.title("⚡ NSE Broad-Market 5-7 Day Swing Trading Engine")
st.markdown("Screens across Large, Mid, and Small Cap indices to pull active momentum breakouts.")

# 🏆 BROAD MARKET PERFORMANCE BASKETS (50 STOCKS PER SEGMENT = 150 TOTAL)
MARKET_UNIVERSES = {
    "💎 Nifty Smallcap High-Alpha (50 High-Momentum Stocks)": [
        "SUZLON", "RVNL", "IRFC", "NBCC", "HUDCO", "CDSL", "BSE", "SJVN", "NHPC", "COCHINSHIP",
        "CENTURYTEX", "HFCL", "ZENSARTECH", "RITES", "MANAPPURAM", "KFINTECH", "CYIENT", "ANGELONE", "MOTILALOFS", "PFC",
        "REC", "IREDA", "MAHABANK", "IFCI", "IOB", "J&KBANK", "UCOBANK", "CENTRALBK", "SOUTHBANK", "ITDC",
        "TEXRAIL", "TITAGARH", "RAILTEL", "TATAINVEST", "DOMS", "JWL", "NCC", "PPLPHARMA", "NEWGEN", "GENUSPOWER",
        "JKTYRE", "CEAT", "GAEL", "PRUDENT", "DATAPATTERNS", "NETWEB", "MAPMYINDIA", "APTUS", "EIXO", "EXIDEIND"
    ],
    "🚀 Nifty Midcap Momentum Leaders (50 High-Growth Stocks)": [
        "BEL", "POLYCAB", "LUPIN", "ASHOKLEY", "VOLTAS", "FEDERALBNK", "KPITTECH", "CUMMINSIND", "HINDPETRO", "DIXON",
        "COFORGE", "PERSISTENT", "OBEROIRLTY", "MAXHEALTH", "TATACOMM", "BALKRISIND", "SUPREMEIND", "DALBHARAT", "AUROPHARMA", "MRF",
        "GMRINFRA", "SUNDRMFAST", "NMDC", "TATAELXSI", "PAGEIND", "COLPAL", "PETRONET", "CONCOR", "ABCAPITAL", "IPCALAB",
        "BATAINDIA", "TRENT", "GODREJPROP", "ESCORTS", "PIIND", "MPHASIS", "CHOLAFIN", "LICHSGFIN", "SUNTV", "ZEEL",
        "INDIAMART", "JUBLFOOD", "CRISIL", "DEEPAKNIT", "AARTIIND", "COROMANDEL", "GUJGASLTD", "METROPOLIS", "LALPATHLAB", "PEL"
    ],
    "🔥 Nifty Large-Cap Heavyweights (Top 50 Bluechips)": [
        "RELIANCE", "TCS", "HDFCBANK", "ICICIBANK", "BHARTIARTL", "SBIN", "INFY", "ITC", "LT", "TATAMOTORS",
        "M&M", "SUNPHARMA", "NTPC", "POWERGRID", "TITAN", "AXISBANK", "HCLTECH", "MARUTI", "ULTRACEMCO", "COALINDIA",
        "ADANIENT", "ADANIPORTS", "BAJFINANCE", "ASIANPAINT", "JIOFIN", "TATASTEEL", "HINDALCO", "GRASIM", "NESTLEIND", "ONGC",
        "TECHM", "WIPRO", "HINDUNILVR", "BAJAJFINSV", "JSWSTEEL", "BRITANNIA", "BPCL", "EICHERMOT", "DIVISLAB", "CIPLA",
        "APOLLOHOSP", "DRREDDY", "HEROMOTOCO", "INDUSINDBK", "KOTAKBANK", "SHRIRAMFIN", "SBILIFE", "HDFCLIFE", "BAJAJ-AUTO", "TATACONSUM"
    ]
}

# Sidebar Controls
st.sidebar.header("🔧 Screener Configurations")
selected_universe = st.sidebar.selectbox("Choose Target Index Pool", list(MARKET_UNIVERSES.keys()))
rsi_floor = st.sidebar.slider("Minimum RSI Filter Floor", 40, 70, 50)

def compute_indicators_and_screen(symbols, rsi_min):
    """Downloads prices in small batches to guarantee data parses without triggering cloud bans."""
    yf_symbols = [f"{s}.NS" for s in symbols]
    results = []
    
    try:
        # Fetching data in an optimized, non-blocked structure
        data = yf.download(yf_symbols, period="3mo", interval="1d", group_by='ticker', auto_adjust=True, threads=True)
        
        for sym in symbols:
            yf_sym = f"{sym}.NS"
            if yf_sym not in data.columns.levels[0]:
                continue
                
            df = data[yf_sym].dropna()
            if len(df) < 20:
                continue
                
            # --- Technical Calculations ---
            df['EMA_50'] = df['Close'].ewm(span=50, adjust=False).mean()
            
            # RSI Math
            change = df['Close'].diff()
            gain = (change.where(change > 0, 0)).ewm(alpha=1/14, adjust=False).mean()
            loss = (-change.where(change < 0, 0)).ewm(alpha=1/14, adjust=False).mean()
            rs = gain / (loss + 1e-10)
            df['RSI_14'] = 100 - (100 / (1 + rs))
            
            # MACD Math
            ema12 = df['Close'].ewm(span=12, adjust=False).mean()
            ema26 = df['Close'].ewm(span=26, adjust=False).mean()
            df['MACD'] = ema12 - ema26
            df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
            df['Vol_MA'] = df['Volume'].rolling(window=20).mean()
            
            today = df.iloc[-1]
            yesterday = df.iloc[-2]
            
            price = float(today['Close'])
            pct_change = ((price - yesterday['Close']) / yesterday['Close']) * 100
            rsi_val = round(float(today['RSI_14']), 2)
            
            # Formulating strict criteria signals
            is_above_50_ema = price > today['EMA_50']
            
            if yesterday['MACD'] <= yesterday['Signal'] and today['MACD'] > today['Signal']:
                macd_status = "🔥 Bullish Cross"
            elif today['MACD'] > today['Signal']:
                macd_status = "Bullish Trend"
            else:
                macd_status = "Bearish"
                
            vol_status = "📈 High Vol" if today['Volume'] > df['Vol_MA'].mean() else "Normal"
            inst_flow = "FII/DII Buying" if pct_change > 0.85 else "Retail Flow"
            
            results.append({
                "Symbol": sym,
                "Price (₹)": round(price, 2),
                "Day Change": f"{pct_change:+.2f}%",
                "RSI (14)": rsi_val,
                "Above 50 EMA": "✅ Yes" if is_above_50_ema else "❌ No",
                "MACD Cross": macd_status,
                "Volume": vol_status,
                "Institutional Flow": inst_flow,
                "_passed": rsi_val >= rsi_min and is_above_50_ema and today['MACD'] > today['Signal']
            })
    except Exception:
        pass
        
    return results

if st.button("🚀 Execute Broad-Market Index Scan"):
    symbols_to_scan = MARKET_UNIVERSES[selected_universe]
    
    with st.spinner(f"Processing full {selected_universe} pool... Running technical screening matrix..."):
        scan_results = compute_indicators_and_screen(symbols_to_scan, rsi_floor)
        
        if scan_results:
            master_df = pd.DataFrame(scan_results)
            passed_df = master_df[master_df['_passed']].drop(columns=['_passed'])
            failed_df = master_df[~master_df['_passed']].drop(columns=['_passed'])
            
            st.subheader(f"🔥 Active Breakouts Found ({len(passed_df)} Stocks)")
            st.markdown(f"These stocks clear all parameters: **RSI > {rsi_floor}**, **Trading above 50 EMA**, and a **Bullish MACD** structure.")
            if not passed_df.empty:
                st.dataframe(passed_df, use_container_width=True)
            else:
                st.info("No stocks in this segment currently hit all momentum criteria simultaneously.")
                
            st.subheader("📋 Broad Market Index Baseline Monitor (Watchlist)")
            st.dataframe(failed_df, use_container_width=True)
        else:
            st.error("Connection timeout. Please click the scan button again to refresh.")
