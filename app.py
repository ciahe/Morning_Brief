import streamlit as st
import pandas as pd
from datetime import datetime
import yfinance as yf
import finnhub

# ====================== CONFIG ======================
FINNHUB_API_KEY = "d734bs9r01qn7f07inigd734bs9r01qn7f07inj0"   # ← Keep your key (used for stocks)

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

finnhub_client = finnhub.Client(api_key=FINNHUB_API_KEY)

@st.cache_data(ttl=600, show_spinner="Fetching latest prices...")
def get_performance(ticker: str):
    try:
        # Use yfinance for crypto (BTC & SOL) - much more reliable
        if ticker in ["BTC-USD", "SOL-USD"]:
            asset = yf.Ticker(ticker)
            hist_1d = asset.history(period="2d")
            hist_1w = asset.history(period="7d")
            hist_1m = asset.history(period="1mo")
            
            # Get current price safely
            info = asset.fast_info if hasattr(asset, 'fast_info') else asset.info
            price = (info.get('lastPrice') or 
                     info.get('regularMarketPrice') or 
                     info.get('currentPrice') or 
                     (hist_1d['Close'].iloc[-1] if not hist_1d.empty else None))

        else:
            # Use Finnhub for traditional assets (better rate limits for stocks)
            quote = finnhub_client.quote(ticker)
            price = quote.get('c')
            
            # Fallback to yfinance for history (1W / 1M)
            asset = yf.Ticker(ticker)
            hist_1d = asset.history(period="2d")
            hist_1w = asset.history(period="7d")
            hist_1m = asset.history(period="1mo")

        if price is None and not hist_1d.empty:
            price = hist_1d['Close'].iloc[-1]

        def calc_pct(hist):
            if hist.empty or len(hist) < 2:
                return None
            return round(((hist['Close'].iloc[-1] - hist['Close'].iloc[0]) / hist['Close'].iloc[0]) * 100, 2)

        change_1d = calc_pct(hist_1d)
        change_1w = calc_pct(hist_1w)
        change_1m = calc_pct(hist_1m)

        return {
            "price": round(float(price), 2) if price is not None else "N/A",
            "change_1d": change_1d,
            "change_1w": change_1w,
            "change_1m": change_1m
        }
    except Exception as e:
        return {"price": "N/A", "change_1d": None, "change_1w": None, "change_1m": None}

# ====================== DISPLAY TABLE ======================
st.subheader("📈 Your Watchlist Performance")

data_rows = []
for ticker, display_name in WATCHLIST.items():
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

# ====================== REFRESH ======================
if st.button("🔄 Refresh All Data"):
    st.cache_data.clear()
    st.rerun()

st.caption("Hybrid data: Finnhub (stocks) + Yahoo Finance (crypto) • 1D/1W/1M changes included • Refresh for latest")