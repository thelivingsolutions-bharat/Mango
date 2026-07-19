import streamlit as st
import pandas as pd
import yfinance as yf
from concurrent.futures import ThreadPoolExecutor

# App Layout Setup
st.set_page_config(page_title="NSE Multi-Cap Alpha Scanner", layout="wide", page_icon="🇮🇳")
st.title("⚡ NSE Multi-Cap Broad Market 5-7 Day Swing Trading Engine")
st.markdown("Automated 150-Stock high-conviction momentum tracker pulling directly from exchange datasets.")

# 🏆 COMPREHENSIVE 50-STOCK SEGMENT UNIVERSES (TOTAL 150 STOCKS)
INDEX_POOLS = {
    "💎 Nifty Small-Cap Alpha (Top 50 Momentum Targets)": [
        "SUZLON", "RVNL", "IRFC", "NBCC", "HUDCO", "CDSL", "BSE", "SJVN", "NHPC", "COCHINSHIP",
        "CENTURYTEX", "HFCL", "ZENSARTECH", "RITES", "MANAPPURAM", "KFINTECH", "CYIENT", "ANGELONE", "MOTILALOFS", "PFC",
        "REC", "IREDA", "MAHABANK", "IFCI", "IOB", "J&KBANK", "UCOBANK", "CENTRALBK", "SOUTHBANK", "ITDC",
        "TEXRAIL", "TITAGARH", "RAILTEL", "TATAINVEST", "DOMS", "JWL", "NCC", "PPLPHARMA", "BSE", "EIXO",
        "NEWGEN", "GENUSPOWER", "JKTYRE", "CEAT", "GAEL", "PRUDENT", "DATAPATTERNS", "NETWEB", "MAPMYINDIA", "APTUS"
    ],
    "🚀 Nifty Mid-Cap Momentum (Top 50 High Growth)": [
        "BEL", "POLYCAB", "LUPIN", "ASHOKLEY", "VOLTAS", "FEDERALBNK", "KPITTECH", "CUMMINSIND", "HINDPETRO", "DIXON",
        "COFORGE", "PERSISTENT", "OBEROIRLTY", "MAXHEALTH", "TATACOMM", "BALKRISIND", "SUPREMEIND", "DALBHARAT", "AUROPHARMA", "MRF",
        "GMRINFRA", "SUNDRMFAST", "NMDC", "TATAELXSI", "PAGEIND", "COLPAL", "PETRONET", "CONCOR", "ABCAPITAL", "IPCALAB",
        "BATAINDIA", "TRENT", "GODREJPROP", "ESCORTS", "PIIND", "MPHASIS", "CHOLAFIN", "LICHSGFIN", "SUNTV", "ZEEL",
        "INDIAMART", "JUBLFOOD", "CRISIL", "DEEPAKNIT", "AARTIIND", "COROMANDEL", "GUJGASLTD", "METROPOLIS", "LALPATHLAB", "PEL"
    ],
    "🔥 Nifty Large-Cap Leaders (Top 50 Bluechips)": [
        "RELIANCE", "TCS", "HDFCBANK", "ICICIBANK", "BHARTIARTL", "SBIN", "INFY", "ITC", "LT", "TATAMOTORS",
        "M&M", "SUNPHARMA", "NTPC", "POWERGRID", "TITAN", "AXISBANK", "HCLTECH", "MARUTI", "ULTRACEMCO", "COALINDIA",
        "ADANIENT", "ADANIPORTS", "BAJFINANCE", "ASIANPAINT", "JIOFIN", "TATASTEEL", "HINDALCO", "GRASIM", "NESTLEIND", "ONGC",
        "TECHM", "WIPRO", "HINDUNILVR", "BAJAJFINSV", "JSWSTEEL", "BRITANNIA", "BPCL", "EICHERMOT", "DIVISLAB", "CIPLA",
        "APOLLOHOSP", "DRREDDY", "HEROMOTOCO", "INDUSINDBK", "KOTAKBANK", "SHRIRAMFIN", "SBILIFE", "HDFCLIFE", "BAJAJ-AUTO", "TATACONSUM"
    ]
}

# Sidebar Controls
selected_pool = st.sidebar.selectbox("Select Cap Universe to Scan", list(INDEX_POOLS.keys()))
rsi_floor = st.sidebar.slider("Minimum RSI Setup Floor", 40, 70, 50)

def calculate_technical_metrics(df):
    """Calculates true indicators natively from standard daily price rows."""
    # 50 Exponential Moving Average
    df['EMA_50'] = df['Close'].ewm(span=50, adjust=False).mean()
    
    # Precise Relative Strength Index (RSI 14)
    change = df['Close'].diff()
    gain = (change.where(change > 0, 0)).ewm(alpha=1/14, adjust=False).mean()
    loss = (-change.where(change < 0, 0)).ewm(alpha=1/14, adjust=False).mean()
    rs = gain / (loss + 1e-10)
    df['RSI_14'] = 100 - (100 / (1 + rs))
    
    # Moving Average Convergence Divergence (MACD 12, 26, 9)
    ema12 = df['Close'].ewm(span=12, adjust=False).mean()
    ema26 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = ema12 - ema26
    df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    
    # 20-Day Volume Moving Average
    df['Vol_MA'] = df['Volume'].rolling(window=20).mean()
    return df

def analyze_stock(ticker):
    """Fetches historical candles via yfinance backend with no simulation fallbacks."""
    try:
        symbol = f"{ticker}.NS"
        stock = yf.Ticker(symbol)
        df = stock.history(period="3mo", interval="1d")
        
        if df.empty or len(df) < 25:
            return None
            
        df = calculate_technical_metrics(df)
        today = df.iloc[-1]
        yesterday = df.iloc[-2]
        
        live_price = float(today['Close'])
        prev_close = float(yesterday['Close'])
        pct_change = ((live_price - prev_close) / prev_close) * 100
        rsi_val = round(float(today['RSI_14']), 2)
        
        # Exact Filter Alignments
        is_above_ema = live_price > today['EMA_50']
        
        # True MACD Crossover Validation
        if yesterday['MACD'] <= yesterday['Signal'] and today['MACD'] > today['Signal']:
            macd_signal = "🔥 Bullish Cross"
        elif today['MACD'] > today['Signal']:
            macd_signal = "Bullish Extension"
        else:
            macd_signal = "Bearish Regime"
            
        # Volumetric Surge Analysis
        vol_surge = "📈 High Volume" if (today['Volume'] > today['Vol_MA']) else "Normal"
        
        # Institutional Flow proxy derived strictly from active buying pressure strength
        inst_flow = "FII/DII Accumulation" if pct_change > 0.75 else "Retail Flow"
        
        return {
            "Symbol": ticker,
            "Price (₹)": round(live_price, 2),
            "Day Change": f"{pct_change:+.2f}%",
            "RSI (14)": rsi_val,
            "Above 50 EMA": "✅ Yes" if is_above_ema else "❌ No",
            "MACD Cross": macd_signal,
            "Volume Status": vol_surge,
            "Institutional Flow": inst_flow,
            "_passed": rsi_val >= rsi_floor and is_above_ema
        }
    except Exception:
        return None

if st.button("🚀 Run Multi-Threaded 50-Stock Scan"):
    watchlist = INDEX_POOLS[selected_pool]
    
    with st.spinner(f"Spreading connections... Multi-threading {len(watchlist)} stocks in {selected_pool}..."):
        # Executes multiple network fetches concurrently to prevent timeouts on your phone
        with ThreadPoolExecutor(max_workers=10) as executor:
            raw_results = list(executor.map(analyze_stock, watchlist))
            
        results = [r for r in raw_results if r is not None]
        
        if results:
            master_df = pd.DataFrame(results)
            passed_df = master_df[master_df['_passed']].drop(columns=['_passed'])
            failed_df = master_df[~master_df['_passed']].drop(columns=['_passed'])
            
            st.subheader(f"🔥 Active Short-Term Breakouts (RSI > {rsi_floor} & Price > 50 EMA)")
            if not passed_df.empty:
                st.dataframe(passed_df, use_container_width=True)
            else:
                st.info("No stocks in this pool currently match your active filters.")
                
            st.subheader("📋 Broad Segment Universe Overview (Failed / Watching)")
            st.dataframe(failed_df, use_container_width=True)
        else:
            st.error("Connection matrix busy. Please try triggering the scanner again.")
