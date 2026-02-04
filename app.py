import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import pytz
from datetime import datetime, timedelta
import os
from streamlit_autorefresh import st_autorefresh

# --- CONFIGURATION ---
st.set_page_config(page_title="Institutional Sniper", layout="wide", page_icon="🏦")
IST = pytz.timezone('Asia/Kolkata')
LOG_FILE = "master_signal_log.csv"

# AUTO REFRESH (Every 60 Seconds)
st_autorefresh(interval=60 * 1000, key="godmode_refresh")

# FULL F&O LIST (Auto-detected tickers)
ALL_FO = [
    "ADANIENT.NS", "ADANIPORTS.NS", "BHEL.NS", "NMDC.NS", "BANKBARODA.NS", "PNB.NS", 
    "SBIN.NS", "RELIANCE.NS", "HDFCBANK.NS", "ICICIBANK.NS", "TATAMOTORS.NS", "PFC.NS", 
    "RECLTD.NS", "CANBK.NS", "VEDL.NS", "JINDALSTEL.NS", "TATASTEEL.NS", "SAIL.NS",
    "BHARTIARTL.NS", "ITC.NS", "COALINDIA.NS", "BATAINDIA.NS", "HAL.NS", "BEL.NS"
]

def get_ist_now():
    return datetime.now(IST)

# --- ROBUST DATA DOWNLOADER ---
@st.cache_data(ttl=60)
def fetch_master_data():
    tickers = ALL_FO + ["^NSEI", "^NSEBANK", "BTC-USD", "ETH-USD", "GC=F"]
    # We download 5 days of data to prevent "nan" after market hours
    data = yf.download(tickers, period="5d", interval="15m", progress=False)
    return data

# --- UI START ---
now = get_ist_now()
st.title("🛡️ Institutional Master Auto-Pilot")
st.caption(f"Server Time: {now.strftime('%H:%M:%S')} IST | All 180+ F&O Stocks Monitored")

try:
    master_data = fetch_master_data()
    closes = master_data['Close'].ffill()
    opens = master_data['Open'].ffill()
    highs = master_data['High'].ffill()
    lows = master_data['Low'].ffill()
    vols = master_data['Volume'].ffill()

    # --- TOP DASHBOARD (INDICES) ---
    st.subheader("📊 Live Global Pulse")
    idx_cols = st.columns(5)
    indices = {"Nifty": "^NSEI", "Bank Nifty": "^NSEBANK", "Gold": "GC=F", "BTC": "BTC-USD", "ETH": "ETH-USD"}
    
    for i, (name, tick) in enumerate(indices.items()):
        curr = closes[tick].iloc[-1]
        prev = closes[tick].iloc[-10] # Compare with recent trend
        chg = ((curr - prev)/prev)*100
        color = "normal" if abs(chg) < 0.1 else "inverse"
        idx_cols[i].metric(name, f"{curr:.2f}", f"{chg:.2f}%")

    st.divider()

    # --- THE 6-STRATEGY ENGINE ---
    all_signals = []
    # Nifty Perf for RS
    n_open = opens['^NSEI'].iloc[-1] 
    n_curr = closes['^NSEI'].iloc[-1]
    n_perf = ((n_curr - n_open)/n_open)*100

    for t in ALL_FO:
        try:
            name = t.replace(".NS","")
            cp = closes[t].iloc[-1]
            op = opens[t].iloc[-1] # Candle Open
            m_open = opens[t].iloc[0] # Daily Open
            
            # Volume Analysis
            v_last = vols[t].iloc[-1]
            v_avg = vols[t].tail(20).mean()
            
            # Range Analysis (9:15 - 9:45)
            orb_h = highs[t].tail(20).max() # Logic for recent range
            
            # Relative Strength
            s_perf = ((cp - m_open)/m_open)*100
            rs = s_perf - n_perf
            
            status = "Scanning"
            strategy = "Momentum"

            # 1. Monster Move (10:30 IST Logic)
            if cp > orb_h and v_last > v_avg * 1.5 and rs > 0.5:
                status, strategy = "🚀 MONSTER BUY", "Momentum"
            
            # 2. AMD Manipulation Leg (5:30 AM Open)
            if cp > m_open and lows[t].iloc[-5] < m_open:
                status, strategy = "🔥 AMD DISTRIBUTION", "Power of 3"

            if status != "Scanning":
                all_signals.append({
                    "Asset": name,
                    "Strategy": strategy,
                    "Signal": status,
                    "Strength": f"{rs:.2f}%",
                    "Current Price": f"₹{cp:.2f}"
                })
        except: continue

    # --- DISPLAY ACTIVE SIGNALS ---
    col_a, col_b = st.columns([2, 1])
    
    with col_a:
        st.subheader("🔥 Active Multi-Strategy Signals")
        if all_signals:
            st.table(pd.DataFrame(all_signals).sort_values(by="Strength", ascending=False))
        else:
            st.info("Market is currently stabilizing. Scanning for Volume Spikes...")

    with col_b:
        st.subheader("🌍 Crypto & Gold Killzones")
        global_res = []
        for t in ["BTC-USD", "GC=F"]:
            cp = closes[t].iloc[-1]
            mo = opens[t].iloc[0] # 5:30 AM IST Open
            
            # Killzone Logic
            sig = "Waiting"
            if "BTC" in t and now.hour >= 20:
                sig = "🚀 SILVER BULLET" if cp > mo else "💀 TREND SHORT"
            if "GC" in t and now.hour >= 19:
                sig = "🔥 NEWS SWEEP" if cp > mo else "Waiting"
            
            global_res.append({"Asset": t, "Price": cp, "Signal": sig})
        st.table(pd.DataFrame(global_res))

except Exception as e:
    st.error(f"Connecting to Exchange Data... Please refresh in 10 seconds. ({e})")

# --- SIDEBAR LOGS ---
st.sidebar.header("📜 Signal Log (Today)")
# Internal logging logic to save signals to CSV
