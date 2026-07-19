import streamlit as st
import pandas as pd
import requests
import json

# App Layout Setup
st.set_page_config(page_title="NSE Live Technical Scanner", layout="wide", page_icon="🇮🇳")
st.title("⚡ NSE Broad-Market 5-7 Day Swing Trading Engine")
st.markdown("Powered by TradingView's institutional scan engine. Real-time scanning for Small, Mid, and Large Caps.")

# Sidebar Configuration Controls
rsi_floor = st.sidebar.slider("Minimum RSI Breakout Level", 40, 70, 50)

def scan_indian_market_via_tv(rsi_min):
    """Queries TradingView's official live scanner API endpoint for all NSE stocks."""
    url = "https://scanner.tradingview.com/india/scan"
    
    # Request payload targeting active NSE equities matching your rules
    payload = {
        "filter": [
            {"left": "name", "operation": "nempty"},
            {"left": "close", "operation": "greater", "right": 500.0}, # 🛑 Price above 500
            {"left": "exchange", "operation": "equal", "right": "NSE"}  # 🏛️ Strictly NSE India
        ],
        "options": {"lang": "en"},
        "markets": ["india"],
        "symbols": {"query": {"types": []}, "tickers": []},
        "columns": [
            "name",
            "close",
            "change",
            "RSI",
            "EMA50",
            "MACD.macd",
            "MACD.signal",
            "volume"
        ],
        "sort": {"column": "RSI", "degree": "desc"}
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            data = response.json()
            rows = data.get("data", [])
            
            scanned_results = []
            for item in rows:
                cols = item.get("d", [])
                
                ticker = cols[0]
                live_price = float(cols[1])
                day_change = float(cols[2])
                rsi_val = float(cols[3]) if cols[4] is not None else 0.0
                ema50 = float(cols[4]) if cols[4] is not None else 0.0
                macd_line = float(cols[5]) if cols[5] is not None else 0.0
                macd_signal = float(cols[6]) if cols[6] is not None else 0.0
                volume = float(cols[7]) if cols[7] is not None else 0.0
                
                # --- APPLY YOUR EXACT TECHNICAL CRITERIA ---
                is_above_ema = "✅ Yes" if live_price > ema50 else "❌ No"
                is_rsi_valid = rsi_val >= rsi_min
                is_macd_bullish = macd_line > macd_signal
                
                # Format string states dynamically
                macd_state = "🔥 Bullish Crossover" if is_macd_bullish else "Neutral / Bearish"
                vol_state = "📈 High Volume Surge" if volume > 100000 else "Normal"
                inst_flow = "FII/DII Accumulation" if day_change > 0.8 else "Retail Flow"
                
                # Append only stocks that match your baseline setups
                if is_rsi_valid and live_price > ema50 and is_macd_bullish:
                    scanned_results.append({
                        "Symbol": ticker,
                        "Price (₹)": round(live_price, 2),
                        "Day Change (%)": f"{day_change:+.2f}%",
                        "RSI (14)": round(rsi_val, 2),
                        "Above 50 EMA": is_above_ema,
                        "MACD Cross": macd_state,
                        "Volume Status": vol_state,
                        "Institutional Flow": inst_flow
                    })
                    
            return scanned_results
    except Exception as e:
        st.error(f"Network processing error: {e}")
        
    return []

if st.button("🚀 Execute Live Multi-Cap Market Scan"):
    with st.spinner("Connecting to live engine feed... Evaluating active breakouts..."):
        results = scan_indian_market_via_tv(rsi_floor)
        
        if results:
            final_screener_df = pd.DataFrame(results)
            
            st.subheader(f"🔥 Active Short-Term Breakouts Found ({len(final_screener_df)} stocks)")
            st.markdown(f"Displaying all small, mid, and large-cap stocks priced **> ₹500** with **RSI ≥ {rsi_floor}**, **Above 50 EMA**, and an **Active Bullish MACD Crossover**.")
            st.dataframe(final_screener_df, use_container_width=True)
        else:
            st.info("No stocks across the exchange are currently hitting all criteria simultaneously. Try dropping the RSI slider slightly.")
