import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import pytz
from datetime import datetime, time
import os
from twelvedata import TDClient
from streamlit_autorefresh import st_autorefresh

# --- CONFIGURATION ---
st.set_page_config(page_title="Master Auto-Pilot Dashboard", layout="wide", page_icon="⚡")
IST = pytz.timezone('Asia/Kolkata')
API_KEY = "8e3458e906524535a87fe7a3274135be"
LOG_FILE = "signal_log.csv"

# --- AUTO REFRESH ---
st_autorefresh(interval=60 * 1000, key="master_refresh")

def get_ist_now():
    return datetime.now(IST)

# --- LIVE PRICE ENGINE ---
@st.cache_data(ttl=55)
def get_live_indices():
    indices = {
        "Nifty 50": "^NSEI",
        "Bank Nifty": "^NSEBANK",
        "Bitcoin": "BTC-USD",
        "Ethereum": "ETH-USD",
        "Gold": "GC=F",
        "S&P 500": "^GSPC",
        "Nasdaq": "^IXIC"
    }
    data = yf.download(list(indices.values()), period="1d", interval="1m", progress=False)['Close']
    res = {}
    for name, ticker in indices.items():
        try:
            val = data[ticker].dropna().iloc[-1]
            prev = data[ticker].dropna().iloc[0]
            change = ((val - prev) / prev) * 100
            res[name] = {"price": val, "change": change}
        except: res[name] = {"price": 0, "change": 0}
    return res

# --- SIGNAL LOGGER ---
def log_signal(asset, strategy, signal):
    if not os.path.isfile(LOG_FILE):
        pd.DataFrame(columns=["Time", "Asset", "Strategy", "Signal"]).to_csv(LOG_FILE, index=False)
    
    if "🚀" in signal or "🎯" in signal or "🔥" in signal:
        df = pd.read_csv(LOG_FILE)
        now_str = get_ist_now().strftime("%H:%M:%S")
        new_row = {"Time": now_str, "Asset": asset, "Strategy": strategy, "Signal": signal}
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        df.to_csv(LOG_FILE, index=False)

# --- HEADER: LIVE INDEX TICKER ---
idx = get_live_indices()
cols = st.columns(len(idx))
for i, (name, d) in enumerate(idx.items()):
    cols[i].metric(name, f"{d['price']:.2f}", f"{d['change']:.2f}%")

st.divider()

# --- MAIN ENGINE ---
def run_logic():
    now = get_ist_now()
    h, m = now.hour, now.minute
    
    # 1. INDIAN MARKET (9:45 Sweep & 10:30 Monster)
    st.subheader("🇮🇳 Indian Market Sniper")
    ind_tickers = ["^NSEBANK", "^NSEI", "RELIANCE.NS", "BHEL.NS", "ADANIENT.NS", "SBIN.NS", "NMDC.NS"]
    df_ind = yf.download(ind_tickers, period="2d", interval="5m", progress=False)
    
    ind_res = []
    for t in ind_tickers:
        try:
            closes = df_ind['Close'][t].dropna()
            opens = df_ind['Open'][t].dropna()
            highs = df_ind['High'][t].dropna()
            lows = df_ind['Low'][t].dropna()
            
            m_open = opens.iloc[0] # 9:15 Open
            curr = closes.iloc[-1]
            orb_h = highs.between_time('09:15', '09:45').max()
            orb_l = lows.between_time('09:15', '09:45').min()
            
            status = "Scanning"
            if t == "^NSEBANK" and h == 9 and m >= 45:
                if curr > orb_h and lows.iloc[-1] < orb_l: status = "🎯 BN SWEEP BUY"
            elif h >= 10 and m >= 30 and curr > orb_h:
                status = "🚀 MONSTER BUY"
            
            log_signal(t, "Momentum/Sweep", status)
            ind_res.append({"Asset": t, "Price": curr, "Status": status})
        except: continue
    st.table(pd.DataFrame(ind_res))

    # 2. GLOBAL MARKET (AMD + Silver Bullet)
    st.subheader("🌍 Global AMD & Crypto")
    global_res = []
    # Use TwelveData for Gold & Crypto (High Accuracy)
    td = TDClient(apikey=API_KEY)
    for sym, name in [("XAU/USD", "GOLD"), ("BTC/USD", "BTC"), ("ETH/USD", "ETH")]:
        try:
            ts = td.time_series(symbol=sym, interval="15min", outputsize=50).as_pandas()
            m_open = ts['open'].iloc[-1] # Midnight Open
            curr = ts['close'].iloc[0]
            
            status = "Waiting"
            # AMD Logic: Manipulation below midnight open
            manipulated = ts['low'].min() < m_open
            
            if name == "GOLD" and h >= 19:
                if manipulated and curr > m_open: status = "🔥 AMD NEWS BUY"
            if name == "BTC" and (h == 20 and m >= 30 or h == 21):
                status = "🚀 SILVER BULLET" if curr > m_open else "Scanning"
                
            log_signal(name, "AMD/Bullet", status)
            global_res.append({"Asset": name, "Price": curr, "Midnight Open": m_open, "Status": status})
        except: continue
    st.table(pd.DataFrame(global_res))

run_logic()

# --- SIDEBAR: LOGS ---
st.sidebar.header("📜 Signal Logs")
if os.path.isfile(LOG_FILE):
    st.sidebar.dataframe(pd.read_csv(LOG_FILE).tail(15))
    if st.sidebar.button("Clear Logs"):
        os.remove(LOG_FILE)
        st.rerun()
