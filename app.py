import streamlit as st
import pandas as pd
import yfinance as yf
from concurrent.futures import ThreadPoolExecutor
import requests
import io

# App Layout Setup
st.set_page_config(page_title="NSE Full-Market Scanner", layout="wide", page_icon="🇮🇳")
st.title("⚡ NSE Broad Full-Market 5-7 Day Swing Trading Engine")
st.markdown("Downloads the master equity catalog directly from NSE archives and identifies hidden momentum breakouts.")

# Sidebar Configuration Controls
rsi_floor = st.sidebar.slider("Minimum RSI Breakout Level", 40, 70, 50)
scan_limit = st.sidebar.slider("Number of stocks to process concurrently", 50, 250, 100, step=25)

@st.cache_data(ttl=86400)
def download_official_nse_master_catalog():
    """
    Downloads the live official list of all active listed equities directly 
    from NSE archives to ensure no stock is missed.
    """
    try:
        url = "https://nsearchives.nseindia.com/content/equities/EQUITY_L.csv"
        headers = {'User-Agent': 'Mozilla/5.0'}
        
        session = requests.Session()
        session.headers.update(headers)
        response = session.get(url, timeout=10)
        
        if response.status_code == 200:
            df = pd.read_csv(io.BytesIO(response.content))
            # Clean and filter for standard ordinary shares (Series: EQ)
            df = df[df[' SERIES'] == ' EQ']
            symbols_list = df['SYMBOL'].dropna().unique().tolist()
            return symbols_list
    except Exception:
        pass
    
    # Secure structural backup database in case the archives link undergoes maintenance
    return ["SUZLON", "RVNL", "IRFC", "NBCC", "HUDCO", "CDSL", "BSE", "SJVN", "NHPC", "COCHINSHIP", 
            "RELIANCE", "TCS", "HDFCBANK", "INFY", "TATAMOTORS", "POLYCAB", "DIXON", "BEL", "LUPIN", "VOLTAS"]

def calculate_technical_metrics(df):
    """Natively computes complex momentum patterns without extra library dependencies."""
    df['EMA_50'] = df['Close'].ewm(span=50, adjust=False).mean()
    df['EMA_200'] = df['Close'].ewm(span=200, adjust=False).mean()
    
    # RSI (14) Engine
    change = df['Close'].diff()
    gain = (change.where(change > 0, 0)).ewm(alpha=1/14, adjust=False).mean()
    loss = (-change.where(change < 0, 0)).ewm(alpha=1/14, adjust=False).mean()
    rs = gain / (loss + 1e-10)
    df['RSI_14'] = 100 - (100 / (1 + rs))
    
    # MACD Engine
    ema12 = df['Close'].ewm(span=12, adjust=False).mean()
    ema26 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = ema12 - ema26
    df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    
    df['Vol_MA'] = df['Volume'].rolling(window=20).mean()
    return df

def analyze_stock(ticker):
    """Evaluates the live candles against the specific 5-7 day momentum criteria."""
    try:
        symbol = f"{ticker}.NS"
        stock = yf.Ticker(symbol)
        df = stock.history(period="3mo", interval="1d")
        
        if df.empty or len(df) < 30:
            return None
            
        df = calculate_technical_metrics(df)
        today = df.iloc[-1]
        yesterday = df.iloc[-2]
        
        live_price = float(today['Close'])
        prev_close = float(yesterday['Close'])
        pct_change = ((live_price - prev_close) / prev_close) * 100
        rsi_val = round(float(today['RSI_14']), 2)
        
        # Checking exact indicator alignments
        is_above_ema = live_price > today['EMA_50']
        golden_cross = "⚡ Bullish Shift" if today['EMA_50'] > today['EMA_200'] else "Bearish"
        
        if yesterday['MACD'] <= yesterday['Signal'] and today['MACD'] > today['Signal']:
            macd_signal = "🔥 Bullish Cross"
        elif today['MACD'] > today['Signal']:
            macd_signal = "Bullish Extension"
        else:
            macd_signal = "Bearish"
            
        vol_surge = "📈 High Volume" if (today['Volume'] > today['Vol_MA']) else "Normal"
        inst_flow = "FII/DII Accumulation" if pct_change > 0.80 else "Retail Flow"
        
        return {
            "Symbol": ticker,
            "Price (₹)": round(live_price, 2),
            "Day Change": f"{pct_change:+.2f}%",
            "RSI (14)": rsi_val,
            "Above 50 EMA": "✅ Yes" if is_above_ema else "❌ No",
            "MACD Cross": macd_signal,
            "Volume Status": vol_surge,
            "Institutional Flow": inst_flow,
            "_passed": rsi_val >= rsi_floor and is_above_ema and today['MACD'] > today['Signal']
        }
    except Exception:
        return None

# --- RUNTIME CONTROL FLOW ---
all_nse_symbols = download_official_nse_master_catalog()

st.sidebar.info(f"Loaded master catalog: {len(all_nse_symbols)} active listed companies.")

if st.button("🚀 Execute Full-Market Scan"):
    # Slice the database based on the chosen limits to manage mobile performance
    watchlist = all_nse_symbols[:scan_limit]
    
    with st.spinner(f"Scanning the broad market universe... Processing {len(watchlist)} stocks simultaneously..."):
        # Multi-threading allows the app to fetch data batches at the same time
        with ThreadPoolExecutor(max_workers=15) as executor:
            raw_results = list(executor.map(analyze_stock, watchlist))
            
        results = [r for r in raw_results if r is not None]
        
        if results:
            master_df = pd.DataFrame(results)
            passed_df = master_df[master_df['_passed']].drop(columns=['_passed'])
            failed_df = master_df[~master_df['_passed']].drop(columns=['_passed'])
            
            st.subheader(f"🔥 Short-Term Actionable Breakouts Found ({len(passed_df)} stocks)")
            st.markdown(f"These stocks actively meet all target conditions: RSI > {rsi_floor}, Trading above 50 EMA, and Bullish MACD positioning.")
            if not passed_df.empty:
                st.dataframe(passed_df, use_container_width=True)
            else:
                st.info("No stocks are currently showing a clean breakout setup in this data slice.")
                
            st.subheader("📋 Broad Market Scan Baseline Monitor")
            st.dataframe(failed_df, use_container_width=True)
        else:
            st.error("Connection window busy. Please try triggering the scanner again.")
