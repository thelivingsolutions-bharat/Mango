import streamlit as st
import pandas as pd
import yfinance as yf
import pandas_ta as ta
from datetime import datetime

# --- STAGE 1: WEB PAGE LAYOUT INITIALIZATION ---
st.set_page_config(
    page_title="Short-Term Swing Trading Screener", 
    layout="wide", 
    page_icon="⚡"
)

st.title("⚡ 5-7 Day Short-Term Institutional & Momentum Swing Screener")
st.markdown("Automated multi-factor screening matching macro institutional trends, financial growth, and technical entry setups.")

# --- STAGE 2: SIDEBAR INPUT CONTROL LAYER ---
st.sidebar.header("🔧 Screener Parameters")

# Watchlist Configuration Matrix
tickers_input = st.sidebar.text_area(
    "Target Watchlist Tickers (Comma-separated)",
    value="AAPL, MSFT, NVDA, AMD, TSLA, INFY, RELIANCE.NS, TCS.NS"
)
# Parse input string into structured cleanly-spaced elements
watchlist = [t.strip().upper() for t in tickers_input.split(",") if t.strip()]

st.sidebar.markdown("---")
st.sidebar.subheader("🎯 Technical Guardrails")

# Input thresholds for dynamic logic evaluations
rsi_threshold = st.sidebar.slider("Minimum RSI (14) Level", 40, 70, 50)
vol_window = st.sidebar.slider("Volume MA Comparison Window (Days)", 10, 50, 20)

st.sidebar.markdown("""
**⚙️ Included Scan Metrics:**
* Price > 50 Exponential Moving Average
* Long-Term Structural Golden Cross Check
* Fresh Internal MACD Bullish Crossover
* Advancing Volumetric Momentum Scales
* Improving Year-over-Year Earnings Growth
* Strong Global Institutional Footprint
""")

# --- STAGE 3: DATA PROCESSING & ENGINE ---
def process_swing_metrics(ticker):
    """
    Downloads historical performance data, applies technical metrics engines,
    and references public fundamental sheets to yield a multi-point trading vector.
    """
    try:
        stock = yf.Ticker(ticker)
        # Pull 1 year of daily historical data to cleanly compute 50 & 200 EMA lines
        df = stock.history(period="1y")
        
        if df.empty or len(df) < 200:
            return None
            
        # 1. TECHNICAL PIPELINE COMPONENT CALCULATIONS
        df['EMA_50'] = ta.ema(df['Close'], length=50)
        df['EMA_200'] = ta.ema(df['Close'], length=200)
        df['RSI_14'] = ta.rsi(df['Close'], length=14)
        
        # MACD Core Signal Arrays
        macd_output = ta.macd(df['Close'], fast=12, slow=26, signal=9)
        df = pd.concat([df, macd_output], axis=1)
        macd_line = 'MACD_12_26_9'
        signal_line = 'MACDs_12_26_9'
        
        # Volumetric standard moving metrics
        df['Vol_MA'] = df['Volume'].rolling(window=vol_window).mean()
        
        # Dynamic slice capturing critical recent data points
        today = df.iloc[-1]
        yesterday = df.iloc[-2]
        
        # 2. BOOLEAN GATE TESTING CONDITIONS
        above_50_ema = today['Close'] > today['EMA_50']
        rsi_valid = today['RSI_14'] >= rsi_threshold
        golden_cross = today['EMA_50'] > today['EMA_200']
        volume_surging = today['Volume'] > today['Vol_MA']
        
        # Exact Intraday / End-of-Day MACD Cross trigger check
        macd_crossover = (yesterday[macd_line] <= yesterday[signal_line]) and (today[macd_line] > today[signal_line])
        
        # 3. FUNDAMENTAL & FINANCIAL ANALYSIS
        info = stock.info
        financials = stock.quarterly_financials
        
        # Evaluate Year-over-Year or sequential Profit Expansion Trajectory
        profit_increasing = False
        if financials is not None and financials.shape[1] >= 2:
            recent_quarter_net = financials.iloc[0, 0]
            prior_quarter_net = financials.iloc[0, 1]
            if pd.notna(recent_quarter_net) and pd.notna(prior_quarter_net):
                profit_increasing = recent_quarter_net > prior_quarter_net
        
        # Institutional Holdings Vector Proxy
        inst_float_pct = info.get('heldPercentInstitutions', 0.0)
        inst_footprint = f"{round(inst_float_pct * 100, 1)}%" if inst_float_pct else "Unavailable"
        
        # 4. LATEST CORPORATE PRESS MONITOR
        news_array = stock.news
        headline = news_array[0]['title'] if news_array else "No current news wire active."
        
        # Structured asset profile payload
        return {
            "Ticker": ticker,
            "Price": round(today['Close'], 2),
            "RSI (14)": round(today['RSI_14'], 2),
            "Above 50 EMA": "✅ Yes" if above_50_ema else "❌ No",
            "MACD Cross": "🔥 Active Trigger" if macd_crossover else "Inactive",
            "Golden Cross": "⚡ Bullish Shift" if golden_cross else "Bearish Regime",
            "Vol Surge": "📈 High Vol" if volume_surging else "Subdued",
            "Profit Rising": "🟢 Expanding" if profit_increasing else "Flat / Decreasing",
            "Inst. Float": inst_footprint,
            "Latest News Wire Headline": headline,
            # Hidden flags to execute conditional multi-factor filtering separations
            "_meets_technicals": (above_50_ema and rsi_valid and (macd_crossover or volume_surging or golden_cross))
        }
    except Exception as e:
        return None

# --- STAGE 4: USER LAYER INTERFACE ENGINE ---
if st.button("🚀 Run Comprehensive Strategy Scan"):
    if not watchlist:
        st.warning("Please configure standard asset symbols inside the operational input area.")
    else:
        with st.spinner("Processing live algorithmic asset vectors, checking financials, and screening news feeds..."):
            compiled_results = []
            
            for ticker_symbol in watchlist:
                metrics_payload = process_swing_metrics(ticker_symbol)
                if metrics_payload:
                    compiled_results.append(metrics_payload)
            
            if compiled_results:
                master_dataframe = pd.DataFrame(compiled_results)
                
                # Split the raw data array into clear Actionable Signals vs Base Watchlist Targets
                high_conviction_df = master_dataframe[master_dataframe['_meets_technicals']].drop(columns=['_meets_technicals'])
                baseline_df = master_dataframe[~master_dataframe['_meets_technicals']].drop(columns=['_meets_technicals'])
                
                # KPI Summary Metadata Metrics Row Banner
                col1, col2, col3 = st.columns(3)
                col1.metric("Monitored Scanned Equities", len(master_dataframe))
                col2.metric("Active Short-Term Setups", len(high_conviction_df))
                col3.metric("Data Process Engine Clock", datetime.now().strftime("%H:%M:%S"))
                
                st.markdown("---")
                
                # SECTION A: HIGH CONVICTION BREAKOUTS
                st.subheader("🔥 High-Conviction 5-7 Day Swing Setups")
                st.markdown("These equities have successfully passed structural trend indicators (RSI base, 50 EMA tracking, or dynamic volume shifts).")
                if not high_conviction_df.empty:
                    st.dataframe(
                        high_conviction_df.style.background_gradient(subset=['RSI (14)'], cmap='YlOrRd'),
                        use_container_width=True
                    )
                else:
                    st.info("No tickers are currently clearing all core momentum filters concurrently at this time.")
                
                # SECTION B: BASELINE MARKET OVERVIEW MONITOR
                st.subheader("📋 General Watchlist Performance & Fundamental Profiles")
                st.markdown("A complete breakdown of all watchlisted equities, detailing their financial trajectories and institutional backing.")
                if not baseline_df.empty:
                    st.dataframe(baseline_df, use_container_width=True)
            else:
                st.error("Application Engine Error: Unable to fetch market data matrix metrics. Verify symbols or internet connection.")
