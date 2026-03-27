import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import time
import os

# Fix for yfinance on Streamlit Cloud
os.environ["YFINANCE_CACHE_DIR"] = "/tmp"

st.set_page_config(page_title="🌅 Antonny's Morning Brief", page_icon="📈", layout="centered")

st.title("🌅 Good Morning, Antonny!")
st.subheader(f"{datetime.now().strftime('%B %d, %Y')} — Singapore Time")

WATCHLIST = {
    "NVDA": "NVDA", "MSFT": "MSFT", "GOOGL": "GOOGL", "AAPL": "AAPL",
    "AMZN": "AMZN", "META": "META", "TSLA": "TSLA",
    "ACN": "ACN", "SAP": "SAP",
    "BTC-USD": "BTC", "SOL-USD": "SOL",
    "GLD": "GLD"
    # "FBMPM.L": "CPO"  # Temporarily removed – too unreliable
}

@st.cache_data(ttl=600, show_spinner=False)  # 10 minutes cache
def get_performance(ticker):
    try:
        asset = yf.Ticker(ticker)
        
        # Primary: Try info for current price
        info = asset.info
        price = (info.get('regularMarketPrice') or 
                 info.get('currentPrice') or 
                 info.get('previousClose') or 
                 info.get('regularMarketPreviousClose'))

        # Fallback: Try history for more accurate %
        hist_1d = asset.history(period="2d", timeout=10)
        hist_1w = asset.history(period="7d", timeout=10)
        hist_1m = asset.history(period="1mo", timeout=10)

        def calc_pct(hist):
            if hist.empty or len(hist['Close']) < 2:
                return None
            return round(((hist['Close'].iloc[-1] - hist['Close'].iloc[0]) / hist['Close'].iloc[0]) * 100, 2)

        change_1d = calc_pct(hist_1d)
        change_1w = calc_pct(hist_1w)
        change_1m = calc_pct(hist_1m)

        if price is None and not hist_1d.empty:
            price = hist_1d['Close'].iloc[-1]

        return {
            "price": round(float(price), 2) if price else "N/A",
            "change_1d": change_1d,
            "change_1w": change_1w,
            "change_1m": change_1m
        }
    except Exception as e:
        st.warning(f"⚠️ Failed to load {ticker}: {str(e)[:80]}...")
        return {"price": "N/A", "change_1d": None, "change_1w": None, "change_1m": None}

# Build table
data_rows = []
for ticker, short_name in WATCHLIST.items():
    perf = get_performance(ticker)
    d1 = f"{perf['change_1d']:+.1f}%" if perf['change_1d'] is not None else "N/A"
    w1 = f"{perf['change_1w']:+.1f}%" if perf['change_1w'] is not None else "N/A"
    m1 = f"{perf['change_1m']:+.1f}%" if perf['change_1m'] is not None else "N/A"
    
    emoji = "🟢" if (perf.get('change_1d') or 0) >= 0 else "🔴"
    data_rows.append({
        "Asset": f"{emoji} {ticker}",
        "Price": f"${perf['price']}" if perf['price'] != "N/A" else "N/A",
        "1D %": d1,
        "1W %": w1,
        "1M %": m1
    })

df = pd.DataFrame(data_rows)
st.dataframe(df, use_container_width=True, hide_index=True)

st.divider()

st.subheader("📰 Top Recent News")
news_found = False
for ticker in list(WATCHLIST.keys())[:6]:
    try:
        asset = yf.Ticker(ticker)
        news = asset.news[:3]
        for item in news:
            if item.get('title'):
                st.markdown(f"• **{item['title']}**  \n_{item.get('publisher', 'Source')}_")
                if item.get('link'):
                    st.markdown(f"[Read →]({item['link']})")
                news_found = True
    except:
        continue

if not news_found:
    st.info("News not loading right now. Try Refresh.")

col1, col2 = st.columns([1, 3])
with col1:
    if st.button("🔄 Refresh All Data"):
        st.cache_data.clear()
        st.rerun()

st.caption("Data sourced from Yahoo Finance via yfinance • Some days data fetching can be slow/unreliable on free cloud hosting")