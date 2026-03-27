import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import finnhub
import time

# ====================== CONFIG ======================
FINNHUB_API_KEY = "YOUR_FINNHUB_API_KEY_HERE"   # ← Replace with your key

st.set_page_config(
    page_title="🌅 Antonny's Morning Brief",
    page_icon="📈",
    layout="centered"
)

st.title("🌅 Good Morning, Antonny!")
st.subheader(f"{datetime.now().strftime('%B %d, %Y')} — Singapore Time")

WATCHLIST = {
    "NVDA": "NVDA", "MSFT": "MSFT", "GOOGL": "GOOGL", "AAPL": "AAPL",
    "AMZN": "AMZN", "META": "META", "TSLA": "TSLA",
    "ACN": "ACN", "SAP": "SAP",
    "BTC-USD": "BTC", "SOL-USD": "SOL",
    "GLD": "GLD"
}

finnhub_client = finnhub.Client(api_key=FINNHUB_API_KEY)

@st.cache_data(ttl=600, show_spinner="Fetching market data...")
def get_performance(ticker: str):
    try:
        # 1. Current price + 1D %
        quote = finnhub_client.quote(ticker)
        current = quote.get('c')
        prev_close = quote.get('pc')

        if current is None:
            return {"price": "N/A", "change_1d": None, "change_1w": None, "change_1m": None}

        # Safe 1D calculation (avoid division by zero)
        change_1d = round(((current - prev_close) / prev_close * 100), 2) if prev_close and prev_close != 0 else None

        # 2. 1W and 1M using daily candles
        now = int(time.time())
        one_week_ago = int((datetime.now() - timedelta(days=8)).timestamp())   # extra buffer
        one_month_ago = int((datetime.now() - timedelta(days=35)).timestamp())

        def get_change(from_ts, to_ts):
            try:
                candles = finnhub_client.stock_candles(ticker, "D", from_ts, to_ts)
                if candles and candles.get('c') and len(candles['c']) >= 2:
                    old_price = candles['c'][0]
                    new_price = candles['c'][-1]
                    return round(((new_price - old_price) / old_price * 100), 2)
                return None
            except:
                return None

        change_1w = get_change(one_week_ago, now)
        change_1m = get_change(one_month_ago, now)

        return {
            "price": round(current, 2),
            "change_1d": change_1d,
            "change_1w": change_1w,
            "change_1m": change_1m
        }
    except Exception as e:
        st.warning(f"⚠️ Issue loading {ticker} — try Refresh")
        return {"price": "N/A", "change_1d": None, "change_1w": None, "change_1m": None}

# ====================== BUILD TABLE ======================
st.subheader("📈 Your Watchlist Performance")

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

# ====================== CONTROLS ======================
col1, col2 = st.columns([1, 4])
with col1:
    if st.button("🔄 Refresh All Data"):
        st.cache_data.clear()
        st.rerun()

st.caption("Data from Finnhub • Prices update in real-time • 1W/1M based on daily candles • Refresh for latest data")
