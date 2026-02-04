import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import pytz
from datetime import datetime, time
import os

# --- CONFIGURATION ---
st.set_page_config(page_title="Monster F&O Scanner", layout="wide")
IST = pytz.timezone('Asia/Kolkata')

# 1. FULL F&O TICKER LIST (Approx 180 stocks)
FO_STOCKS = [
    "AARTIIND.NS", "ABB.NS", "ABBOTINDIA.NS", "ABCAPITAL.NS", "ABFRL.NS", "ACC.NS", "ADANIENT.NS", "ADANIPORTS.NS",
    "ALKEM.NS", "AMBUJACEM.NS", "APOLLOHOSP.NS", "APOLLOTYRE.NS", "ASHOKLEY.NS", "ASIANPAINT.NS", "ASTRAL.NS",
    "ATUL.NS", "AUBANK.NS", "AUROPHARMA.MA", "AXISBANK.NS", "BAJAJ-AUTO.NS", "BAJFINANCE.NS", "BAJAJFINSV.NS",
    "BALKRISIND.NS", "BALRAMCHIN.NS", "BANDHANBNK.NS", "BANKBARODA.NS", "BATAINDIA.NS", "BEL.NS", "BERGEPAINT.NS",
    "BHARATFORG.NS", "BHARTIARTL.NS", "BHEL.NS", "BIOCON.NS", "BSOFT.NS", "BPCL.NS", "BRITANNIA.NS", "CANBK.NS",
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

# --- APP START ---
def get_ist_now():
    return datetime.now(IST)

st.title("🚀 Monster F&O Sniper (AMD + Momentum)")
st_time = st.empty()

# --- AUTO REFRESH ---
from streamlit_autorefresh import st_autorefresh
st_autorefresh(interval=60 * 1000, key="fnotracker")

# --- DATA ENGINE ---
@st.cache_data(ttl=60)
def fetch_all_data():
    all_tickers = FO_STOCKS + ["^NSEI", "^NSEBANK", "BTC-USD", "GC=F"]
    data = yf.download(all_tickers, period="2d", interval="15m", progress=False)
    return data['Close'], data['Open'], data['High'], data['Low'], data['Volume']

try:
    closes, opens, highs, lows, volumes = fetch_all_data()
    now = get_ist_now()
    st_time.write(f"Last Scan: {now.strftime('%H:%M:%S')} IST")

    results = []

    # Calculate Nifty Performance for Relative Strength
    nifty_open = opens['^NSEI'].iloc[0]
    nifty_curr = closes['^NSEI'].iloc[-1]
    nifty_perf = ((nifty_curr - nifty_open) / nifty_open) * 100

    for ticker in FO_STOCKS:
        try:
            curr_p = closes[ticker].iloc[-1]
            m_open = opens[ticker].iloc[0] # 9:15 AM Open
            vol_last = volumes[ticker].iloc[-1]
            vol_avg = volumes[ticker].mean()
            
            # Monster Logic Triggers
            perf = ((curr_p - m_open) / m_open) * 100
            rel_strength = perf - nifty_perf
            
            # ORB 30 Filter (9:15 - 9:45)
            orb_h = highs[ticker].iloc[0:2].max()
            
            status = "Scanning"
            if curr_p > orb_h and vol_last > vol_avg * 2.5 and rel_strength > 1.0:
                status = "🔥 MONSTER BUY"
            elif curr_p < m_open and vol_last > vol_avg * 2.5 and rel_strength < -1.0:
                status = "🩸 CRASHING"
            
            if status != "Scanning":
                results.append({
                    "Symbol": ticker.replace(".NS", ""),
                    "Price": round(curr_p, 2),
                    "Rel Strength": f"{round(rel_strength, 2)}%",
                    "Signal": status,
                    "Time": now.strftime("%H:%M")
                })
        except:
            continue

    # Display Monster Results
    st.header("🎯 Active Monster Signals")
    if results:
        df_res = pd.DataFrame(results)
        st.dataframe(df_res.sort_values(by="Rel Strength", ascending=False), use_container_width=True)
    else:
        st.write("No Monster moves detected yet. Waiting for Volume + Range Break.")

    # Global Assets (BTC & GOLD)
    st.divider()
    st.header("🌍 Global AMD Signals")
    col1, col2 = st.columns(2)
    
    with col1: # BTC
        btc_p = closes['BTC-USD'].iloc[-1]
        btc_o = opens['BTC-USD'].iloc[0]
        st.metric("BTC-USD", round(btc_p, 2), f"{round(((btc_p-btc_o)/btc_o)*100, 2)}%")
        if now.hour >= 20: st.success("Silver Bullet Window Active")

    with col2: # GOLD
        gold_p = closes['GC=F'].iloc[-1]
        gold_o = opens['GC=F'].iloc[0]
        st.metric("GOLD (XAU)", round(gold_p, 2), f"{round(((gold_p-gold_o)/gold_o)*100, 2)}%")

except Exception as e:
    st.error(f"Waiting for Market Data... {e}")
