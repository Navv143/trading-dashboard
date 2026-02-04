import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import pytz
from datetime import datetime
import os
from streamlit_autorefresh import st_autorefresh

# --- CONFIGURATION ---
st.set_page_config(page_title="God-Mode Multi-Strategy Scanner", layout="wide", page_icon="🏦")
IST = pytz.timezone('Asia/Kolkata')
LOG_FILE = "master_signal_log.csv"

# AUTO REFRESH (Every 60 Seconds)
st_autorefresh(interval=60 * 1000, key="godmode_refresh")

# --- TICKER LIST (All 180+ F&O Stocks) ---
ALL_FO = [
    "AARTIIND.NS", "ABB.NS", "ABBOTINDIA.NS", "ABCAPITAL.NS", "ABFRL.NS", "ACC.NS", "ADANIENT.NS", "ADANIPORTS.NS", "ALKEM.NS", "AMBUJACEM.NS", "APOLLOHOSP.NS", "APOLLOTYRE.NS", "ASHOKLEY.NS", "ASIANPAINT.NS", "ASTRAL.NS", "ATUL.NS", "AUBANK.NS", "AUROPHARMA.NS", "AXISBANK.NS", "BAJAJ-AUTO.NS", "BAJFINANCE.NS", "BAJAJFINSV.NS", "BALKRISIND.NS", "BALRAMCHIN.NS", "BANDHANBNK.NS", "BANKBARODA.NS", "BATAINDIA.NS", "BEL.NS", "BERGEPAINT.NS", "BHARATFORG.NS", "BHARTIARTL.NS", "BHEL.NS", "BIOCON.NS", "BPCL.NS", "BRITANNIA.NS", "BSOFT.NS", "CANBK.NS", "CANFINHOME.NS", "CHAMBLFERT.NS", "CHOLAFIN.NS", "CIPLA.NS", "COALINDIA.NS", "COFORGE.NS", "COLPAL.NS", "CONCOR.NS", "COROMANDEL.NS", "CROMPTON.NS", "CUB.NS", "CUMMINSIND.NS", "DABUR.NS", "DALBHARAT.NS", "DEEPAKNTR.NS", "DELHIVERY.NS", "DIVISLAB.NS", "DIXON.NS", "DLF.NS", "DRREDDY.NS", "EICHERMOT.NS", "ESCORTS.NS", "EXIDEIND.NS", "FEDERALBNK.NS", "GAIL.NS", "GLENMARK.NS", "GMRINFRA.NS", "GNFC.NS", "GODREJCP.NS", "GODREJPROP.NS", "GRANULES.NS", "GRASIM.NS", "GUJGASLTD.NS", "HAL.NS", "HAVELLS.NS", "HCLTECH.NS", "HDFCBANK.NS", "HDFCLIFE.NS", "HEROMOTOCO.NS", "HINDALCO.NS", "HINDCOPPER.NS", "HINDPETRO.NS", "HINDUNILVR.NS", "ICICIBANK.NS", "ICICIGI.NS", "ICICIPRULI.NS", "IDFC.NS", "IDFCFIRSTB.NS", "IEX.NS", "IGL.NS", "INDHOTEL.NS", "INDIACEM.NS", "INDIAMART.NS", "INDIGO.NS", "INDUSINDBK.NS", "INDUSTOWER.NS", "INFY.NS", "IOC.NS", "IRCTC.NS", "ITC.NS", "JINDALSTEL.NS", "JKCEMENT.NS", "JSWSTEEL.NS", "JUBLFOOD.NS", "KOTAKBANK.NS", "L&TFH.NS", "LALPATHLAB.NS", "LAURUSLABS.NS", "LICHSGFIN.NS", "LT.NS", "LTIM.NS", "LTTS.NS", "LUPIN.NS", "M&M.NS", "M&MFIN.NS", "MANAPPURAM.NS", "MARICO.NS", "MARUTI.NS", "MCX.NS", "METROPOLIS.NS", "MFSL.NS", "MGL.NS", "MOTHERSON.NS", "MPHASIS.NS", "MRF.NS", "MUTHOOTFIN.NS", "NATIONALUM.NS", "NAVINFLUOR.NS", "NESTLEIND.NS", "NMDC.NS", "NTPC.NS", "OBEROIRLTY.NS", "OFSS.NS", "ONGC.NS", "PAGEIND.NS", "PEL.NS", "PERSISTENT.NS", "PETRONET.NS", "PFC.NS", "PIDILITIND.NS", "PIIND.NS", "PNB.NS", "POLYCAB.NS", "POWERGRID.NS", "PVRINOX.NS", "RAMCOCEM.NS", "RBLBANK.NS", "RECLTD.NS", "RELIANCE.NS", "SAIL.NS", "SBICARD.NS", "SBILIFE.NS", "SBIN.NS", "SHREECEM.NS", "SHRIRAMFIN.NS", "SIEMENS.NS", "SRF.NS", "SUNPHARMA.NS", "SUNTV.NS", "SYNGENE.NS", "TATACOMM.NS", "TATACONSUM.NS", "TATAMOTORS.NS", "TATAPOWER.NS", "TATASTEEL.NS", "TCS.NS", "TECHM.NS", "TITAN.NS", "TORNTPHARM.NS", "TRENT.NS", "TVSMOTOR.NS", "UBL.NS", "ULTRACEMCO.NS", "UPL.NS", "VEDL.NS", "VOLTAS.NS", "WIPRO.NS", "ZEEL.NS", "ZYDUSLIFE.NS"
]

def get_ist_now():
    return datetime.now(IST)

# --- DATA DOWNLOADER ---
@st.cache_data(ttl=60)
def fetch_master_data():
    all_tickers = ALL_FO + ["^NSEI", "^NSEBANK", "BTC-USD", "ETH-USD", "GC=F"]
    data = yf.download(all_tickers, period="2d", interval="15m", progress=False)
    return data

# --- SIGNAL LOGGING ---
def log_master_signal(asset, strategy, signal):
    if not os.path.isfile(LOG_FILE):
        pd.DataFrame(columns=["Time", "Asset", "Strategy", "Signal"]).to_csv(LOG_FILE, index=False)
    
    if any(emoji in signal for emoji in ["🚀", "🎯", "🔥", "💀"]):
        df = pd.read_csv(LOG_FILE)
        now_str = get_ist_now().strftime("%H:%M:%S")
        # Log only if new
        if not ((df['Asset'] == asset) & (df['Strategy'] == strategy)).tail(1).any():
            new_row = {"Time": now_str, "Asset": asset, "Strategy": strategy, "Signal": signal}
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            df.to_csv(LOG_FILE, index=False)

# --- UI START ---
st.title("🛡️ Institutional God-Mode Auto-Pilot")
now = get_ist_now()
st.caption(f"Server Time: {now.strftime('%H:%M:%S')} IST | All 180+ F&O Stocks Monitored")

# --- LIVE PRICE BAR ---
try:
    master_data = fetch_master_data()
    closes = master_data['Close']
    opens = master_data['Open']
    highs = master_data['High']
    lows = master_data['Low']
    vols = master_data['Volume']

    # --- TOP DASHBOARD (INDICES) ---
    st.subheader("📊 Live Index Tracker")
    idx_cols = st.columns(5)
    indices = {"Nifty": "^NSEI", "Bank Nifty": "^NSEBANK", "Gold": "GC=F", "BTC": "BTC-USD", "ETH": "ETH-USD"}
    for i, (name, tick) in enumerate(indices.items()):
        curr = closes[tick].iloc[-1]
        prev = closes[tick].iloc[0]
        chg = ((curr - prev)/prev)*100
        idx_cols[i].metric(name, f"{curr:.2f}", f"{chg:.2f}%")

    st.divider()

    # --- THE 6-STRATEGY SCANNER ENGINE ---
    all_signals = []
    nifty_perf = ((closes['^NSEI'].iloc[-1] - opens['^NSEI'].iloc[0])/opens['^NSEI'].iloc[0])*100

    for t in ALL_FO:
        try:
            name = t.replace(".NS","")
            cp = closes[t].iloc[-1]
            op = opens[t].iloc[0] # 9:15 AM IST
            v_last = vols[t].iloc[-1]
            v_avg = vols[t].mean()
            
            # ORB Range
            orb_h = highs[t].iloc[0:2].max()
            orb_l = lows[t].iloc[0:2].min()
            
            # Performance
            perf = ((cp - op)/op)*100
            rs = perf - nifty_perf
            
            signal = "Scanning"
            strategy = "Momentum"

            # 1. 9:45 AM Sweep Logic
            if now.hour == 9 and now.minute >= 45:
                if cp > orb_h and lows[t].iloc[-1] < orb_l:
                    signal, strategy = "🎯 SWEEP BUY", "ORB-Sweep"
            
            # 2. 10:30 AM Monster (Loosened for more signals)
            if cp > orb_h and v_last > v_avg * 1.5 and rs > 0.8:
                signal, strategy = "🚀 MONSTER BUY", "Monster"
            elif cp < orb_l and v_last > v_avg * 1.5 and rs < -0.8:
                signal, strategy = "💀 CRASHING", "Monster"

            # Log and Add
            if signal != "Scanning":
                log_master_signal(name, strategy, signal)
                all_signals.append({"Asset": name, "Strategy": strategy, "Signal": signal, "RS": f"{rs:.2f}%", "Price": cp})
        except: continue

    # --- DISPLAY SIGNALS ---
    st.subheader("🔥 Real-Time Multi-Strategy Signals")
    if all_signals:
        st.table(pd.DataFrame(all_signals).sort_values(by="RS", ascending=False))
    else:
        st.info("Searching 180+ stocks for specific footprints... (Signals typically peak at 9:45, 10:30, 13:15, 19:00 IST)")

    # --- GLOBAL AMD & SILVER BULLET ---
    st.divider()
    st.subheader("🌍 Global AMD & Silver Bullet (BTC/Gold)")
    global_res = []
    for t in ["BTC-USD", "GC=F"]:
        cp = closes[t].iloc[-1]
        m_open = opens[t].iloc[0] # 5:30 AM IST
        h_range = highs[t].max()
        l_range = lows[t].min()
        
        status = "Waiting"
        # AMD Logic: Was there manipulation?
        if t == "GC=F" and now.hour >= 19:
            if l_range < m_open and cp > m_open: status = "🔥 AMD BULLISH"
            elif h_range > m_open and cp < m_open: status = "🩸 AMD BEARISH"
        
        if "BTC" in t and now.hour >= 20:
            status = "🚀 SILVER BULLET" if cp > m_open else "💀 TREND DOWN"
            
        global_res.append({"Asset": t, "Price": cp, "5:30 AM Open": m_open, "Signal": status})
    st.table(pd.DataFrame(global_res))

except Exception as e:
    st.error(f"Waiting for market data streams... {e}")

# --- SIDEBAR LOGS ---
st.sidebar.header("📜 Signal Journal")
if os.path.isfile(LOG_FILE):
    st.sidebar.dataframe(pd.read_csv(LOG_FILE).tail(30).sort_index(ascending=False), use_container_width=True)
    if st.sidebar.button("Wipe Journal"):
        os.remove(LOG_FILE)
        st.rerun()
