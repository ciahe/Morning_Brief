import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="🌅 Antonny's Morning Brief", page_icon="📈", layout="wide")

st.title("🌅 Good Morning, Antonny!")
st.subheader(f"{datetime.now().strftime('%B %d, %Y')} — Singapore Time")

WATCHLIST = {
    "NVDA": "NVDA", "MSFT": "MSFT", "GOOGL": "GOOGL", "AAPL": "AAPL",
    "AMZN": "AMZN", "META": "META", "TSLA": "TSLA",
    "ACN": "ACN", "SAP": "SAP",
    "BTC-USD": "BTC", "SOL-USD": "SOL",
    "GLD": "GLD", "FBMPM.L": "CPO (Palm Oil)"
}

@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_performance(ticker):
    try:
        asset = yf.Ticker(ticker)
        info = asset.info
        price = info.get('regularMarketPrice') or info.get('previousClose') or info.get('currentPrice')

        hist_1d = asset.history(period="1d")
        hist_1w = asset.history(period="5d")
        hist_1m = asset.history(period="1mo")

        def calc_pct(hist):
            if hist.empty or len(hist) < 2:
                return None
            return round(((hist['Close'].iloc[-1] - hist['Close'].iloc[0]) / hist['Close'].iloc[0]) * 100, 2)

        return {
            "price": round(price, 2) if price else "N/A",
            "change_1d": calc_pct(hist_1d),
            "change_1w": calc_pct(hist_1w),
            "change_1m": calc_pct(hist_1m)
        }
    except:
        return {"price": "N/A", "change_1d": None, "change_1w": None, "change_1m": None}

# Fetch data
data_rows = []
for ticker, short_name in WATCHLIST.items():
    perf = get_performance(ticker)
    d1 = f"{perf['change_1d']:+.1f}%" if perf['change_1d'] is not None else "N/A"
    w1 = f"{perf['change_1w']:+.1f}%" if perf['change_1w'] is not None else "N/A"
    m1 = f"{perf['change_1m']:+.1f}%" if perf['change_1m'] is not None else "N/A"
    
    color = "🟢" if (perf.get('change_1d') or 0) >= 0 else "🔴"
    data_rows.append({
        "Asset": f"{color} {ticker}",
        "Price": f"${perf['price']}",
        "1D %": d1,
        "1W %": w1,
        "1M %": m1
    })

df = pd.DataFrame(data_rows)
st.dataframe(df, use_container_width=True, hide_index=True)

st.divider()

st.subheader("📰 Top Recent News")
news_found = False
for ticker in list(WATCHLIST.keys())[:7]:
    try:
        asset = yf.Ticker(ticker)
        news = asset.news[:2]
        for item in news:
            if 'title' in item:
                st.markdown(f"• **{item.get('title')}**  \n[{item.get('publisher', 'Source')}]({item.get('link', '#')})")
                news_found = True
    except:
        continue

if not news_found:
    st.info("News refreshing... Try refreshing the page.")

if st.button("🔄 Refresh Data"):
    st.rerun()

st.caption("Data via Yahoo Finance • FBMPM.L for Palm Oil Index • Refresh for latest")