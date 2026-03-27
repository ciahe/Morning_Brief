import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import os

# Critical fix for Streamlit Cloud + yfinance cache/permission issues
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
}

@st.cache_data(ttl=900, show_spinner="Fetching market data...")  # 15 min cache
def get_performance(ticker):
    try:
        asset = yf.Ticker(ticker)
        
        # Try history first (more reliable on Cloud)
        hist_1d = asset.history(period="2d", timeout=15)
        hist_1w = asset.history(period="7d", timeout=15)
        hist_1m = asset.history(period="1mo", timeout=15)

        def calc_pct(hist):
            if hist is None or hist.empty or len(hist) < 2:
                return None
            try:
                return round(((hist['Close'].iloc[-1] - hist['Close'].iloc[0]) / hist['Close'].iloc[0]) * 100, 2)
            except:
                return None

        change_1d = calc_pct(hist_1d)
        change_1w = calc_pct(hist_1w)
        change_1m = calc_pct(hist_1m)

        # Get price from history (most reliable)
        price = None
        if not hist_1d.empty:
            price = hist_1d['Close'].iloc[-1]
        else:
            # Fallback to info only if history fails
            try:
                info = asset.info
                price = info.get('regularMarketPrice') or info.get('currentPrice') or info.get('previousClose')
            except:
                pass

        return {
            "price": round(float(price), 2) if price is not None else "N/A",
            "change_1d": change_1d,
            "change_1w": change_1w,
            "change_1m": change_1m
        }
    except Exception as e:
        error_msg = str(e)
        if "'NoneType' object has no attribute 'update'" in error_msg:
            st.warning(f"⚠️ Yahoo temporarily blocked {ticker} (common on Cloud). Retrying later helps.")
        else:
            st.warning(f"⚠️ Failed to load {ticker}: {error_msg[:100]}")
        return {"price": "N/A", "change_1d": None, "change_1w": None, "change_1m": None}

# Build table
data_rows = []
for ticker in WATCHLIST:
    perf = get_performance(ticker)
    d1 = f"{perf['change_1d']:+.1f}%" if perf['change_1d'] is not None else "N/A"
    w1 = f"{perf['change_1w']:+.1f}%" if perf['change_1w'] is not None else "N/A"
    m1 = f"{perf['change_1m']:+.1f}%" if perf['change_1m'] is not None else "N/A"
    
    emoji = "🟢" if (perf.get('change_1d') or 0) >= 0 else "🔴" if perf.get('change_1d') is not None else "⚪"
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
for ticker in list(WATCHLIST.keys())[:5]:
    try:
        asset = yf.Ticker(ticker)
        news = asset.news[:2]
        for item in news:
            if item and item.get('title'):
                st.markdown(f"• **{item['title']}**")
                if item.get('link'):
                    st.markdown(f"[Read article]({item['link']})")
                news_found = True
    except:
        continue

if not news_found:
    st.info("News section is having trouble loading right now.")

if st.button("🔄 Refresh All Data"):
    st.cache_data.clear()
    st.rerun()

st.caption("Note: yfinance can be unreliable on free Streamlit Cloud due to Yahoo restrictions. Refresh a few times or try later.")