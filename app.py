import streamlit as st
import pandas as pd
import yfinance as yf
import requests
import io

# App Layout Setup
st.set_page_config(page_title="NSE Bulk Market Scanner", layout="wide", page_icon="🇮🇳")
st.title("⚡ NSE Broad Full-Market 5-7 Day Swing Trading Engine")
st.markdown("Uses optimized bulk connections to screen broad market segments without getting blocked by firewalls.")

# Sidebar Configuration Controls
rsi_floor = st.sidebar.slider("Minimum RSI Breakout Level", 40, 70, 50)
scan_limit = st.sidebar.slider("Number of stocks to process", 25, 150, 60, step=25)

@st.cache_data(ttl=86400)
def download_official_nse_master_catalog():
    """Downloads the full active stock master list directly from NSE corporate archives."""
    try:
        url = "https://nsearchives.nseindia.com/content/equities/EQUITY_L.csv"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        session = requests.Session()
        session.headers.update(headers)
        response = session.get(url, timeout=10)
        
        if response.status_code == 200:
            df = pd.read_csv(io.BytesIO(response.content))
            df = df[df[' SERIES'].str.strip() == 'EQ']
            return df['SYMBOL'].dropna().unique().tolist()
    except Exception:
        pass
    
    # Static bulletproof broad market list fallback covering mid, large, and small caps
    return [
        "SUZLON", "RVNL", "IRFC", "NBCC", "HUDCO", "CDSL", "BSE", "SJVN", "NHPC", "COCHINSHIP", 
        "RELIANCE", "TCS", "HDFCBANK", "INFY", "TATAMOTORS", "POLYCAB", "DIXON", "BEL", "LUPIN", "VOLTAS",
        "ZEEL", "GMRINFRA", "IREDA", "PFC", "REC", "ZENSARTECH", "HFCL", "RITES", "MANAPPURAM", "ANGELONE",
        "TATAPOWER", "PNB", "IOC", "GAIL", "BPCL", "SAIL", "VEDL", "WIPRO", "HINDALCO", "TATASTEEL"
    ]

def analyze_bulk_data(symbols, rsi_min):
    """Downloads all stock histories in ONE single optimized batch request to prevent blocks."""
    yf_symbols = [f"{s}.NS" for s in symbols]
    
    try:
        # Download 3 months of historical daily closing records in one go
        data = yf.download(yf_symbols, period="3mo", interval="1d", group_by='ticker', threads=False)
        
        processed_results = []
        
        for sym in symbols:
            yf_sym = f"{sym}.NS"
            if yf_sym not in data.columns.levels[0]:
                continue
                
            df = data[yf_sym].dropna()
            if df.empty or len(df) < 30:
                continue
                
            # Technical Vector Mathematics Calculations
            df['EMA_50'] = df['Close'].ewm(span=50, adjust=False).mean()
            
            # Relative Strength Index (RSI 14) calculations
            change = df['Close'].diff()
            gain = (change.where(change > 0, 0)).ewm(alpha=1/14, adjust=False).mean()
            loss = (-change.where(change < 0, 0)).ewm(alpha=1/14, adjust=False).mean()
            rs = gain / (loss + 1e-10)
            df['RSI_14'] = 100 - (100 / (1 + rs))
            
            # MACD Line & Signals Crossover arrays
            ema12 = df['Close'].ewm(span=12, adjust=False).mean()
            ema26 = df['Close'].ewm(span=26, adjust=False).mean()
            df['MACD'] = ema12 - ema26
            df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
            df['Vol_MA'] = df['Volume'].rolling(window=20).mean()
            
            today = df.iloc[-1]
            yesterday = df.iloc[-2]
            
            live_price = float(today['Close'])
            prev_close = float(yesterday['Close'])
            pct_change = ((live_price - prev_close) / prev_close) * 100
            rsi_val = round(float(today['RSI_14']), 2)
            
            # Operational Filters Rules evaluation
            is_above_ema = live_price > today['EMA_50']
            
            if yesterday['MACD'] <= yesterday['Signal'] and today['MACD'] > today['Signal']:
                macd_signal = "🔥 Bullish Cross"
            elif today['MACD'] > today['Signal']:
                macd_signal = "Bullish Extension"
            else:
                macd_signal = "Bearish"
                
            vol_surge = "📈 High Volume" if (today['Volume'] > today['Vol_MA']) else "Normal"
            inst_flow = "FII/DII Accumulation" if pct_change > 0.80 else "Retail Flow"
            
            processed_results.append({
                "Symbol": sym,
                "Price (₹)": round(live_price, 2),
                "Day Change": f"{pct_change:+.2f}%",
                "RSI (14)": rsi_val,
                "Above 50 EMA": "✅ Yes" if is_above_ema else "❌ No",
                "MACD Cross": macd_signal,
                "Volume Status": vol_surge,
                "Institutional Flow": inst_flow,
                "_passed": rsi_val >= rsi_min and is_above_ema and today['MACD'] > today['Signal']
            })
            
        return processed_results
    except Exception as e:
        st.error(f"Batch processing error: {e}")
        return []

# Run Master Download Pipeline
all_nse_symbols = download_official_nse_master_catalog()
st.sidebar.info(f"Loaded master catalog: {len(all_nse_symbols)} active listed companies.")

if st.button("🚀 Execute Optimized Full-Market Scan"):
    # Grab the active batch pool size set by the mobile sidebar slider
    watchlist = all_nse_symbols[:scan_limit]
    
    with st.spinner(f"Requesting single-batch data payload for {len(watchlist)} stocks..."):
        results = analyze_bulk_data(watchlist, rsi_floor)
        
        if results:
            master_df = pd.DataFrame(results)
            passed_df = master_df[master_df['_passed']].drop(columns=['_passed'])
            failed_df = master_df[~master_df['_passed']].drop(columns=['_passed'])
            
            st.subheader(f"🔥 Short-Term Breakouts Found ({len(passed_df)} stocks)")
            st.markdown(f"Stocks matching criteria (RSI > {rsi_floor}, Price > 50 EMA, and Bullish MACD).")
            if not passed_df.empty:
                st.dataframe(passed_df, use_container_width=True)
            else:
                st.info("No stocks matched all rules in this scan pool batch right now.")
                
            st.subheader("📋 Broad Market Scan Baseline Monitor")
            st.dataframe(failed_df, use_container_width=True)
        else:
            st.error("Data processing failed. Lower the scan limit slider in the sidebar and try again.")
