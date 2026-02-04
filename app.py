import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import pytz
from datetime import datetime, time
import os

# --- CONFIGURATION ---
st.set_page_config(page_title="Auto-Pilot PWA", layout="wide", page_icon="📈")
IST = pytz.timezone('Asia/Kolkata')

# --- SIGNAL PERSISTENCE ---
# This file stores signals so they don't disappear on refresh
LOG_FILE = "signal_log.csv"

def log_signal(asset, strategy, status):
    now = datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S")
    if not os.path.isfile(LOG_FILE):
        df = pd.DataFrame(columns=["Time", "Asset", "Strategy", "Signal"])
        df.to_csv(LOG_FILE, index=False)
    
    # Read and check if this signal was already logged in the last 15 mins to avoid duplicates
    df = pd.read_csv(LOG_FILE)
    last_entry = df[(df['Asset'] == asset) & (df['Strategy'] == strategy)].tail(1)
    
    should_log = True
    if not last_entry.empty:
        last_time = datetime.strptime(last_entry['Time'].values[0], "%Y-%m-%d %H:%M:%S")
        diff = (datetime.now() - last_time).total_seconds() / 60
        if diff < 15: # Don't log the same signal for 15 minutes
            should_log = False
            
    if should_log and ("🚀" in status or "🎯" in status or "🔥" in status):
        new_row = {"Time": now, "Asset": asset, "Strategy": strategy, "Signal": status}
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        df.to_csv(LOG_FILE, index=False)

# --- APP LAYOUT ---
st.title("🛡️ Institutional Master Dashboard")
st.write(f"Refreshed at: {datetime.now(IST).strftime('%H:%M:%S')} IST")

# --- AUTO-REFRESH LOGIC (1 MINUTE) ---
from streamlit_autorefresh import st_autorefresh
st_autorefresh(interval=60 * 1000, key="datarefresh")

# --- STRATEGY ENGINE ---
def run_master_logic():
    tickers = {
        "^NSEBANK": "BANK NIFTY", 
        "^NSEI": "NIFTY", 
        "BTC-USD": "BTC", 
        "GC=F": "GOLD",
        "RELIANCE.NS": "RELIANCE",
        "BHEL.NS": "BHEL"
    }
    
    results = []
    now = datetime.now(IST)
    
    for t, name in tickers.items():
        try:
            df = yf.download(t, period="2d", interval="5m", progress=False)
            if df.empty: continue
            df.columns = df.columns.get_level_values(0)
            
            # 5:30 AM IST Midnight Open
            mid_open = df['Open'].iloc[0] 
            curr_p = df['Close'].iloc[-1]
            orb_h = df.between_time('09:15', '09:45')['High'].max()
            orb_l = df.between_time('09:15', '09:45')['Low'].min()
            
            status = "Scanning..."
            strat_name = "Momentum"

            # 1. GOLD / BANK NIFTY SWEEP LOGIC
            if name in ["GOLD", "BANK NIFTY"]:
                strat_name = "Sweep/AMD"
                if curr_p < mid_open and df['Low'].iloc[-1] < orb_l:
                    status = "🎯 BULLISH SWEEP/AMD"
                elif curr_p > mid_open and df['High'].iloc[-1] > orb_h:
                    status = "🎯 BEARISH SWEEP/AMD"

            # 2. BTC/ETH BULLET & TREND
            if name == "BTC":
                strat_name = "Silver Bullet"
                if (now.hour == 20 and now.minute >= 30) or now.hour == 21:
                    status = "🚀 TREND EXPANSION" if curr_p > mid_open else "💀 TREND CRASH"

            # 3. MONSTER STOCKS
            if ".NS" in t and name not in ["BANK NIFTY", "NIFTY"]:
                strat_name = "Monster Move"
                if curr_p > orb_h and df['Volume'].iloc[-1] > df['Volume'].mean() * 2:
                    status = "🔥 MONSTER BUY"

            log_signal(name, strat_name, status)
            results.append({"Time": now.strftime("%H:%M"), "Asset": name, "Price": curr_p, "Status": status})
        except:
            continue
            
    return pd.DataFrame(results)

# --- DISPLAY ---
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Live Market Status")
    df_live = run_master_logic()
    st.dataframe(df_live, use_container_width=True)

with col2:
    st.subheader("📜 Signal History (Last 10)")
    if os.path.isfile(LOG_FILE):
        history = pd.read_csv(LOG_FILE)
        st.dataframe(history.tail(10).sort_index(ascending=False), use_container_width=True)

if st.button("Clear History"):
    if os.path.isfile(LOG_FILE):
        os.remove(LOG_FILE)
        st.rerun()
