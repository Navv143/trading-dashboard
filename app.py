import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import pytz
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# --- CONFIGURATION ---
st.set_page_config(page_title="Institutional Sniper", layout="wide", page_icon="🏦")
IST = pytz.timezone('Asia/Kolkata')

# 1. FULL F&O TICKER LIST (180+ Tickers)
ALL_FO = [
    "AARTIIND.NS", "ABB.NS", "ABBOTINDIA.NS", "ABCAPITAL.NS", "ABFRL.NS", "ACC.NS", "ADANIENT.NS", "ADANIPORTS.NS",
    "ALKEM.NS", "AMBUJACEM.NS", "APOLLOHOSP.NS", "APOLLOTYRE.NS", "ASHOKLEY.NS", "ASIANPAINT.NS", "ASTRAL.NS",
    "ATUL.NS", "AUBANK.NS", "AUROPHARMA.NS", "AXISBANK.NS", "BAJAJ-AUTO.NS", "BAJFINANCE.NS", "BAJAJFINSV.NS",
    "BALKRISIND.NS", "BALRAMCHIN.NS", "BANDHANBNK.NS", "BANKBARODA.NS", "BATAINDIA.NS", "BEL.NS", "BERGEPAINT.NS",
    "BHARATFORG.NS", "BHARTIARTL.NS", "BHEL.NS", "BIOCON.NS", "BPCL.NS", "BRITANNIA.NS", "BSOFT.NS", "CANBK.NS",
    "CHAMBLFERT.NS", "CHOLAFIN.NS", "CIPLA.NS", "COALINDIA.NS", "COFORGE.NS", "COLPAL.NS", "CONCOR.NS", "COROMANDEL.NS",
    "CROMPTON.NS", "CUB.NS", "CUMMINSIND.NS", "DABUR.NS", "DALBHARAT.NS", "DEEPAKNTR.NS", "DELHIVERY.NS", "DIVISLAB.NS",
    "DIXON.NS", "DLF.NS", "DRREDDY.NS", "EICHERMOT.NS", "ESCORTS.NS", "EXIDEIND.NS", "FEDERALBNK.NS", "GAIL.NS",
    "GLENMARK.NS", "GMRINFRA.NS", "GNFC.NS", "GODREJCP.NS", "GODREJPROP.NS", "GRANULES.NS", "GRASIM.NS", "GUJGASLTD.NS",
    "HAL.NS", "HAVELLS.NS", "HCLTECH.NS", "HDFCBANK.NS", "HDFCLIFE.NS", "HEROMOTOCO.NS", "HINDALCO.NS", "HINDCOPPER.NS",
    "HINDPETRO.NS", "HINDUNILVR.NS", "ICICIBANK.NS", "ICICIGI.NS", "ICICIPRULI.NS", "IDFC.NS", "IDFCFIRSTB.NS", "IEX.NS",
    "IGL.NS", "INDHOTEL.NS", "INDIACEM.NS", "INDIAMART.NS", "INDIGO.NS", "INDUSINDBK.NS", "INDUSTOWER.NS", "INFY.NS",
    "IOC.NS", "IRCTC.NS", "ITC.NS", "JINDALSTEL.NS", "JKCEMENT.NS", "JSWSTEEL.NS", "JUBLFOOD.NS", "KOTAKBANK.NS",
    "L&TFH.NS", "LT.NS", "LTIM.NS", "LTTS.NS", "LUPIN.NS", "M&M.NS", "M&MFIN.NS", "MANAPPURAM.NS", "MARICO.NS",
    "MARUTI.NS", "MCX.NS", "METROPOLIS.NS", "MFSL.NS", "MGL.NS", "MOTHERSON.NS", "MPHASIS.NS", "MRF.NS", "MUTHOOTFIN.NS",
    "NATIONALUM.NS", "NAVINFLUOR.NS", "NESTLEIND.NS", "NMDC.NS", "NTPC.NS", "OBEROIRLTY.NS", "ONGC.NS", "PAGEIND.NS",
    "PEL.NS", "PERSISTENT.NS", "PETRONET.NS", "PFC.NS", "PIDILITIND.NS", "PIIND.NS", "PNB.NS", "POLYCAB.NS", "POWERGRID.NS",
    "PVRINOX.NS", "RECLTD.NS", "RELIANCE.NS", "SAIL.NS", "SBICARD.NS", "SBILIFE.NS", "SBIN.NS", "SHREECEM.NS", "SHRIRAMFIN.NS",
    "SIEMENS.NS", "SRF.NS", "SUNPHARMA.NS", "SUNTV.NS", "SYNGENE.NS", "TATACOMM.NS", "TATACONSUM.NS", "TATAMOTORS.NS",
    "TATAPOWER.NS", "TATASTEEL.NS", "TCS.NS", "TECHM.NS", "TITAN.NS", "TRENT.NS", "TVSMOTOR.NS", "ULTRACEMCO.NS",
    "UPL.NS", "VEDL.NS", "VOLTAS.NS", "WIPRO.NS", "ZEEL.NS", "ZYDUSLIFE.NS"
]

st_autorefresh(interval=60 * 1000, key="monster_refresh")

def get_ist_now():
    return datetime.now(IST)

# --- ROBUST DATA FETCHING ---
@st.cache_data(ttl=60)
def fetch_data(tickers):
    try:
        data = yf.download(tickers, period="5d", interval="15m", progress=False, group_by='ticker')
        return data
    except:
        return None

# --- UI START ---
now = get_ist_now()
st.title("🛡️ Institutional Master Auto-Pilot")
st.caption(f"Server Time: {now.strftime('%H:%M:%S')} IST | All 180+ F&O Stocks Monitored")

# --- 1. LIVE PULSE SECTION ---
st.subheader("📊 Live Index Tracker")
indices = {"Nifty 50": "^NSEI", "Bank Nifty": "^NSEBANK", "Gold": "GC=F", "Bitcoin": "BTC-USD"}
idx_cols = st.columns(len(indices))

idx_data = fetch_data(list(indices.values()))

for i, (name, ticker) in enumerate(indices.items()):
    try:
        df = idx_data[ticker].dropna()
        curr = df['Close'].iloc[-1]
        prev = df['Close'].iloc[-2]
        change = ((curr - prev)/prev)*100
        idx_cols[i].metric(name, f"{curr:.2f}", f"{change:.2f}%")
    except:
        idx_cols[i].metric(name, "Offline", "0.00%")

st.divider()

# --- 2. MASTER SCANNER SECTION ---
st.subheader("🔥 Active Multi-Strategy Signals")

fo_data = fetch_data(ALL_FO)

if fo_data is not None:
    results = []
    
    # Get Nifty Performance for Relative Strength
    try:
        nifty_df = idx_data["^NSEI"].dropna()
        n_open = nifty_df['Open'].iloc[-1]
        n_curr = nifty_df['Close'].iloc[-1]
        n_perf = ((n_curr - n_open)/n_open)*100
    except:
        n_perf = 0.0

    for ticker in ALL_FO:
        try:
            df = fo_data[ticker].dropna()
            if df.empty: continue
            
            cp = df['Close'].iloc[-1]
            op = df['Open'].iloc[0] # Daily Open (09:15)
            hi = df['High']
            lo = df['Low']
            vl = df['Volume']
            
            # --- STRATEGY 1: MONSTER MOVE (10:30 IST) ---
            orb_h = hi.iloc[0:2].max() # 9:15 to 9:45
            rs = (((cp - op)/op)*100) - n_perf
            v_spike = vl.iloc[-1] > vl.mean() * 1.5
            
            status = "Scanning"
            strategy = "Momentum"

            if cp > orb_h and v_spike and rs > 1.0:
                status, strategy = "🚀 MONSTER BUY", "Momentum"
            
            # --- STRATEGY 2: AMD MANIPULATION (POWER OF 3) ---
            midnight_open = op # 9:15 Open
            manipulated = lo.min() < midnight_open
            if manipulated and cp > midnight_open and rs > 0.5:
                status, strategy = "🔥 AMD BULLISH", "Power of 3"

            # --- STRATEGY 3: BANK NIFTY SWEEP ---
            if "BANKNIFTY" in ticker or "SBIN" in ticker:
                if cp > orb_h and lo.iloc[-1] < df['Low'].iloc[0:2].min():
                    status, strategy = "🎯 SWEEP BUY", "Liquidity"

            if status != "Scanning":
                results.append({
                    "Asset": ticker.replace(".NS",""),
                    "Price": round(cp, 2),
                    "Strategy": strategy,
                    "Signal": status,
                    "Strength": f"{round(rs, 2)}%"
                })
        except:
            continue

    if results:
        st.table(pd.DataFrame(results).sort_values(by="Price", ascending=False))
    else:
        st.info("No 'Monster' or 'Sweep' signals detected in the last 60 seconds. Scanning F&O Universe...")

else:
    st.error("Connecting to Exchange Data... Please refresh in 10 seconds.")

# --- 3. GLOBAL AMD & SILVER BULLET ---
st.sidebar.header("🌍 Global Killzones")
try:
    btc_df = idx_data["BTC-USD"].dropna()
    btc_p = btc_df['Close'].iloc[-1]
    btc_sig = "🚀 SILVER BULLET" if btc_p > btc_df['Open'].iloc[0] and now.hour >= 20 else "Waiting"
    st.sidebar.metric("Bitcoin", f"${btc_p:.2f}", btc_sig)
    
    gold_df = idx_data["GC=F"].dropna()
    gold_p = gold_df['Close'].iloc[-1]
    gold_sig = "🔥 NEWS SWEEP" if now.hour >= 19 else "Waiting"
    st.sidebar.metric("Gold", f"${gold_p:.2f}", gold_sig)
except:
    st.sidebar.write("Global Data Loading...")
