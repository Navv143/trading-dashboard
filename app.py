import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import pytz
from datetime import datetime, timedelta
import requests
from twelvedata import TDClient
from streamlit_autorefresh import st_autorefresh

# --- CONFIGURATION ---
st.set_page_config(page_title="Ultimate Monster Dashboard", layout="wide")
IST = pytz.timezone('Asia/Kolkata')
API_KEY = "8e3458e906524535a87fe7a3274135be"

# 1. FULL F&O TICKER LIST
FO_STOCKS = [
    "ADANIENT.NS", "ADANIPORTS.NS", "BHEL.NS", "NMDC.NS", "BANKBARODA.NS", "PNB.NS", 
    "SBIN.NS", "RELIANCE.NS", "HDFCBANK.NS", "ICICIBANK.NS", "AXISBANK.NS", "TCS.NS", 
    "INFY.NS", "TATAMOTORS.NS", "BHARTIARTL.NS", "COALINDIA.NS", "PFC.NS", "RECLTD.NS",
    "CANBK.NS", "VEDL.NS", "JINDALSTEL.NS", "TATASTEEL.NS", "SAIL.NS", "BATAINDIA.NS",
    "DLF.NS", "HAL.NS", "BEL.NS", "ITC.NS", "HINDALCO.NS", "BPCL.NS", "IOC.NS"
] # Add more to this list as needed

# --- AUTO REFRESH (60 SECONDS) ---
st_autorefresh(interval=60 * 1000, key="monster_refresh")

def get_ist_now():
    return datetime.now(IST)

# --- TWELVE DATA ENGINE (GOLD & CRYPTO) ---
def fetch_global_td(symbol):
    try:
        td = TDClient(apikey=API_KEY)
        ts = td.time_series(symbol=symbol, interval="15min", outputsize=50)
        df = ts.as_pandas()
        return df
    except:
        return pd.DataFrame()

# --- APP LAYOUT ---
st.title("🛡️ Ultimate Master Auto-Pilot Dashboard")
st.write(f"Refreshed at: {get_ist_now().strftime('%H:%M:%S')} IST")

# --- GLOBAL MARKETS (GOLD & CRYPTO) ---
st.header("🌍 Global AMD & Silver Bullet")
col1, col2, col3 = st.columns(3)

with col1: # GOLD
    df_gold = fetch_global_td("XAU/USD")
    if not df_gold.empty:
        curr_g = df_gold['close'].iloc[0]
        # Midnight Open (approx 5:30 AM IST)
        m_open_g = df_gold.iloc[-1]['open'] 
        man_l = df_gold['low'].min() < m_open_g
        man_h = df_gold['high'].max() > m_open_g
        
        status = "Watching"
        now = get_ist_now()
        if now.hour == 19 or (now.hour == 20 and now.minute <= 30):
            if man_l and curr_g > m_open_g: status = "🔥 GOLD NEWS SWEEP BUY"
            elif man_h and curr_g < m_open_g: status = "🩸 GOLD NEWS SWEEP SELL"
        
        st.metric("GOLD (XAU/USD)", f"${curr_g}", status)
        st.caption(f"AMD Target: Opposite Session Side")

with col2: # BTC
    df_btc = fetch_global_td("BTC/USD")
    if not df_btc.empty:
        curr_b = df_btc['close'].iloc[0]
        m_open_b = df_btc.iloc[-1]['open']
        status = "Scanning"
        now = get_ist_now()
        # 8:30 PM Silver Bullet & 9:00 PM Trend
        if now.hour >= 20:
            if curr_b > m_open_b: status = "🚀 SILVER BULLET BUY"
            else: status = "💀 TREND CRASH"
        
        st.metric("BITCOIN", f"${round(curr_b, 2)}", status)

with col3: # ETH
    df_eth = fetch_global_td("ETH/USD")
    if not df_eth.empty:
        curr_e = df_eth['close'].iloc[0]
        st.metric("ETHEREUM", f"${round(curr_e, 2)}", "Tracking")

st.divider()

# --- INDIAN MARKET (MONSTER F&O SCANNER) ---
st.header("🇮🇳 Indian Market: 9:45 Sweep & 10:30 Monster")

@st.cache_data(ttl=60)
def fetch_indian_data():
    tickers = [t for t in FO_STOCKS] + ["^NSEI", "^NSEBANK"]
    data = yf.download(tickers, period="2d", interval="15m", progress=False)
    return data

try:
    ind_data = fetch_indian_data()
    closes = ind_data['Close']
    opens = ind_data['Open']
    highs = ind_data['High']
    lows = ind_data['Low']
    vols = ind_data['Volume']
    
    # Nifty Relative Strength
    nifty_perf = ((closes['^NSEI'].iloc[-1] - opens['^NSEI'].iloc[0]) / opens['^NSEI'].iloc[0]) * 100
    
    results = []
    for t in FO_STOCKS:
        try:
            p_close = closes[t].iloc[-1]
            p_open = opens[t].iloc[0]
            orb_h = highs[t].iloc[0:2].max() # 9:15-9:45
            orb_l = lows[t].iloc[0:2].min()
            
            p_vols = vols[t].iloc[-1]
            avg_vols = vols[t].mean()
            
            # RS Calculation
            stock_perf = ((p_close - p_open) / p_open) * 100
            rs = stock_perf - nifty_perf
            
            signal = "Watch"
            # 9:45 Sweep Logic
            if p_close > orb_h and lows[t].iloc[-1] < orb_l: signal = "🎯 BN SWEEP"
            # 10:30 Monster Logic
            elif p_close > orb_h and p_vols > avg_vols * 2.5 and rs > 1.2: signal = "🚀 MONSTER BUY"
            elif p_close < orb_l and p_vols > avg_vols * 2.5 and rs < -1.2: signal = "💀 CRASHING"
            
            if signal != "Watch":
                results.append({"Symbol": t, "Price": round(p_close, 2), "RS": f"{round(rs,2)}%", "Signal": signal})
        except:
            continue

    if results:
        st.table(pd.DataFrame(results))
    else:
        st.info("No active Monster signals. Waiting for 9:45 AM or 10:30 AM volume spikes.")

except Exception as e:
    st.write("Initializing Market Data...")
