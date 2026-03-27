import streamlit as st
import pandas as pd
from datetime import datetime
import finnhub
import time

# ====================== CONFIG ======================
FINNHUB_API_KEY = "d734bs9r01qn7f07inigd734bs9r01qn7f07inj0"   # ← Make sure this is correct and activated

st.set_page_config(page_title="🌅 Antonny's Morning Brief", page_icon="📈", layout="centered")

st.title("🌅 Good Morning, Antonny!")
st.subheader(f"{datetime.now().strftime('%B %d, %Y')} — Singapore Time")

WATCHLIST = ["NVDA", "MSFT", "GOOGL", "AAPL", "AMZN", "META", "TSLA", "ACN", "SAP", "BTC-USD", "SOL-USD", "GLD"]

finnhub_client = finnhub.Client(api_key=FINNHUB_API_KEY)

@st.cache_data(ttl=300, show_spinner="Loading market data...")
def get_performance(ticker):
    try:
        # === 1. Current Price & 1D % using Quote ===
        quote = finnhub_client.quote(ticker)
        
        current = quote.get('c')
        prev_close = quote.get('pc')

        if current is None:
            return {"ticker": ticker, "price": "N/A", "change_1d": None, "change_1w": None, "change_1m": None, "error": "No price data"}

        change_1d = round(((current - prev_close) / prev_close * 100), 2) if prev_close and prev_close != 0 else 0.0

        # === 2. Simple 1W and 1M (using recent quote only for now) ===
        # We'll improve this later if needed. For now we show 1D properly.

        return {
            "ticker": ticker,
            "price": round(current, 2),
            "change_1d": change_1d,
            "change_1w": None,
            "change_1m": None,
            "error": None
        }
    except Exception as e:
        error_str = str(e)
        if "429" in error_str or "limit" in error_str.lower():
            return {"ticker": ticker, "price": "N/A", "change_1d": None, "change_1w": None, "change_1m": None, "error": "Rate limit — wait 1 min"}
        else:
            return {"ticker": ticker, "price": "N/A", "change_1d": None, "change_1w": None, "change_1m": None, "error": f"Error: {error_str[:60]}"}

# ====================== TABLE ======================
st.subheader("📈 Watchlist Performance")

data_rows = []
for ticker in WATCHLIST:
    perf = get_performance(ticker)
    
    d1 = f"{perf['change_1d']:+.1f}%" if perf['change_1d'] is not None else "N/A"
    
    emoji = "🟢" if (perf.get('change_1d') or 0) >= 0 else "🔴" if perf.get('change_1d') is not None else "⚪"

    row = {
        "Asset": f"{emoji} {ticker}",
        "Price": f"${perf['price']}" if perf['price'] != "N/A" else "N/A",
        "1D %": d1,
        "1W %": "N/A",
        "1M %": "N/A"
    }
    data_rows.append(row)

df = pd.DataFrame(data_rows)
st.dataframe(df, use_container_width=True, hide_index=True)

# Show any errors at the bottom for debugging
errors = [perf for perf in [get_performance(t) for t in WATCHLIST] if perf.get('error')]
if errors:
    with st.expander("Debug Info (click to expand)"):
        for e in errors:
            st.write(f"{e['ticker']}: {e['error']}")

if st.button("🔄 Refresh All Data"):
    st.cache_data.clear()
    st.rerun()

st.caption("Using Finnhub • Refresh a few times if you see rate limit messages • Make sure your API key is correct and activated")