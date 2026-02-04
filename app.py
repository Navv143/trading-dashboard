import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import pytz
from datetime import datetime
import requests
from twelvedata import TDClient
from streamlit_autorefresh import st_autorefresh

# --- CONFIGURATION ---
st.set_page_config(page_title="Ultimate Monster Sniper", layout="wide")
IST = pytz.timezone('Asia/Kolkata')
API_KEY = "8e3458e906524535a87fe7a3274135be"

# REFINED F&O LIST (High Liquidity)
FO_STOCKS = [
    "ADANIENT.NS", "ADANIPORTS.NS", "BHEL.NS", "NMDC.NS", "BANKBARODA.NS", "PNB.NS", 
    "SBIN.NS", "RELIANCE.NS", "HDFCBANK.NS", "ICICIBANK.NS", "TATAMOTORS.NS", "PFC.NS", 
    "RECLTD.NS", "CANBK.NS", "VEDL.NS", "JINDALSTEL.NS", "TATASTEEL.NS", "SAIL.NS"
]

st_autorefresh(interval=60 * 1000, key="monster_refresh")

def get_ist_now():
    return datetime.now(IST)

# --- TWELVE DATA FALLBACK SYSTEM ---
def fetch_global_price(symbol, fallback_ticker):
    try:
        td = TDClient(apikey=API_KEY)
        ts = td.time_series(symbol=symbol, interval="15min", outputsize=1)
        df = ts.as_pandas()
        return df['close'].iloc[0], "TwelveData"
    except:
        try:
            data = yf.download(fallback_ticker, period="1d", interval="15min", progress=False)
            return data['Close'].iloc[-1], "YFinance"
        except:
            return 0, "Error"

# --- MAIN UI ---
now = get_ist_now()
st.title("🚀 Monster F&O Sniper (AMD + Momentum)")
st.write(f"Last Scan: {now.strftime('%H:%M:%S')} IST")

# MARKET STATUS CHECK
market_open = False
if now.weekday() < 5: # Mon-Fri
    if (now.hour == 9 and now.minute >= 15) or (now.hour > 9 and now.hour < 15) or (now.hour == 15 and now.minute <= 30):
        market_open = True

if not market_open:
    st.warning("🌙 Indian Market is CLOSED. Showing Final Results of the Day.")
else:
    st.success("🟢 Indian Market is OPEN.")

# --- GLOBAL SIGNALS ---
st.header("🌍 Global Market Status")
col1, col2 = st.columns(2)

with col1:
    btc_price, source_b = fetch_global_price("BTC/USD", "BTC-USD")
    st.metric("BITCOIN", f"${round(btc_price, 2)}", f"Source: {source_b}")

with col2:
    gold_price, source_g = fetch_global_price("XAU/USD", "GC=F")
    if gold_price > 0:
        st.metric("GOLD (XAU/USD)", f"${round(gold_price, 2)}", f"Source: {source_g}")
    else:
        st.metric("GOLD", "Loading...", "API Syncing")

st.divider()

# --- INDIAN MARKET SCANNER ---
st.header("🎯 Monster Potential (Today)")

@st.cache_data(ttl=60)
def fetch_indian_market():
    # Download in bulk for speed
    data = yf.download(FO_STOCKS + ["^NSEI"], period="1d", interval="15m", progress=False)
    return data

try:
    df_raw = fetch_indian_market()
    
    # Check if we got data
    if not df_raw.empty:
        # Handling YFinance Multi-Index
        close_df = df_raw['Close']
        open_df = df_raw['Open']
        high_df = df_raw['High']
        low_df = df_raw['Low']
        vol_df = df_raw['Volume']
        
        nifty_perf = ((close_df['^NSEI'].iloc[-1] - open_df['^NSEI'].iloc[0]) / open_df['^NSEI'].iloc[0]) * 100
        
        results = []
        for t in FO_STOCKS:
            try:
                curr_p = close_df[t].iloc[-1]
                m_open = open_df[t].iloc[0]
                orb_h = high_df[t].iloc[0:3].max() # First 45 mins
                vol_now = vol_df[t].iloc[-1]
                vol_avg = vol_df[t].mean()
                
                perf = ((curr_p - m_open) / m_open) * 100
                rs = perf - nifty_perf
                
                signal = "Normal"
                if curr_p > orb_h and rs > 1.0:
                    signal = "🚀 MONSTER BUY"
                elif curr_p < m_open and rs < -1.0:
                    signal = "💀 CRASHING"
                
                if signal != "Normal":
                    results.append({
                        "Stock": t.replace(".NS", ""),
                        "Price": round(curr_p, 2),
                        "Rel Strength": f"{round(rs, 2)}%",
                        "Signal": signal
                    })
            except:
                continue
        
        if results:
            st.table(pd.DataFrame(results))
        else:
            st.info("No stocks met the 'Monster' criteria (RS > 1.0% + Price > ORB High) for today.")
    else:
        st.error("Unable to fetch Indian market data. Please wait.")

except Exception as e:
    st.error(f"Error: {e}")
