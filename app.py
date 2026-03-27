import streamlit as st
import pandas as pd
from datetime import datetime
import yfinance as yf
import finnhub

# ====================== CONFIG ======================
FINNHUB_API_KEY = "d734bs9r01qn7f07inigd734bs9r01qn7f07inj0"   # ← Your key here

st.set_page_config(page_title="🌅 Antonny's Morning Brief", page_icon="📈", layout="centered")

st.title("🌅 Good Morning, Antonny!")
st.subheader(f"{datetime.now().strftime('%B %d, %Y')} — Singapore Time")

WATCHLIST = {
    "NVDA": "NVDA", "MSFT": "MSFT", "GOOGL": "GOOGL", "AAPL": "AAPL",
    "AMZN": "AMZN", "META": "META", "TSLA": "TSLA",
    "ACN": "ACN", "SAP": "SAP",
    "BTC-USD": "BTC", "SOL-USD": "SOL",
    "GLD": "GLD",
    "FBMPM.L": "CPO (Palm Oil USD)"
}

finnhub_client = finnhub.Client(api_key=FINNHUB_API_KEY)

@st.cache_data(ttl=900, show_spinner="Fetching latest prices...")
def get_performance(ticker: str):
    try:
        if ticker == "FBMPM.L":
            # === CPO Price in USD ===
            asset = yf.Ticker("FBMPM.L")
            hist_price = asset.history(period="2d")
            myr_price = hist_price['Close'].iloc[-1] if not hist_price.empty else None

            # Get exchange rate
            exchange = yf.Ticker("MYR=X")
            ex_hist = exchange.history(period="1d")
            usd_myr = ex_hist['Close'].iloc[-1] if not ex_hist.empty else 4.45

            price = myr_price / usd_myr if myr_price else None

            # === Use a more reliable ticker for % changes (KLSE proxy or fallback) ===
            hist_asset = yf.Ticker("^KLSE")   # Kuala Lumpur Composite as proxy for history
            hist_1d = hist_asset.history(period="2d")
            hist_1w = hist_asset.history(period="7d")
            hist_1m = hist_asset.history(period="1mo")

        elif ticker in ["BTC-USD", "SOL-USD"]:
            asset = yf.Ticker(ticker)
            info = asset.fast_info if hasattr(asset, 'fast_info') else asset.info
            price = (info.get('lastPrice') or info.get('regularMarketPrice') or info.get('previousClose'))
            hist_1d = asset.history(period="2d")
            hist_1w = asset.history(period="7d")
            hist_1m = asset.history(period="1mo")
            hist_asset = asset

        else:
            quote = finnhub_client.quote(ticker)
            price = quote.get('c')
            hist_asset = yf.Ticker(ticker)
            hist_1d = hist_asset.history(period="2d")
            hist_1w = hist_asset.history(period="7d")
            hist_1m = hist_asset.history(period="1mo")

        if price is None and 'hist_asset' in locals():
            temp_hist = hist_asset.history(period="1d")
            if not temp_hist.empty:
                price = temp_hist['Close'].iloc[-1]

        def calc_pct(hist):
            if hist.empty or len(hist) < 2:
                return None
            return round(((hist['Close'].iloc[-1] - hist['Close'].iloc[0]) / hist['Close'].iloc[0]) * 100, 2)

        change_1d = calc_pct(hist_1d)
        change_1w = calc_pct(hist_1w)
        change_1m = calc_pct(hist_1m)

        return {
            "price": round(float(price), 2) if price is not None and price > 0 else "N/A",
            "change_1d": change_1d,
            "change_1w": change_1w,
            "change_1m": change_1m
        }
    except:
        return {"price": "N/A", "change_1d": None, "change_1w": None, "change_1m": None}

# ====================== TABLE ======================
st.subheader("📈 Your Watchlist Performance")

data_rows = []
positive_count = 0
total_with_data = 0

for ticker, display_name in WATCHLIST.items():
    perf = get_performance(ticker)
    
    d1 = f"{perf['change_1d']:+.1f}%" if perf['change_1d'] is not None else "N/A"
    w1 = f"{perf['change_1w']:+.1f}%" if perf['change_1w'] is not None else "N/A"
    m1 = f"{perf['change_1m']:+.1f}%" if perf['change_1m'] is not None else "N/A"

    emoji = "🟢" if (perf.get('change_1d') or 0) >= 0 else "🔴" if perf.get('change_1d') is not None else "⚪"

    data_rows.append({
        "Asset": f"{emoji} {display_name if ticker == 'FBMPM.L' else ticker}",
        "Price": f"${perf['price']}" if perf['price'] != "N/A" else "N/A",
        "1D %": d1,
        "1W %": w1,
        "1M %": m1
    })

    if perf['change_1d'] is not None:
        total_with_data += 1
        if perf['change_1d'] >= 0:
            positive_count += 1

df = pd.DataFrame(data_rows)

def color_percent(val):
    if val == "N/A":
        return ''
    try:
        num = float(val.strip('%'))
        if num >= 0:
            return 'background-color: #d4edda; color: #155724;'
        else:
            return 'background-color: #f8d7da; color: #721c24;'
    except:
        return ''

styled_df = df.style.applymap(color_percent, subset=['1D %', '1W %', '1M %'])

st.dataframe(styled_df, use_container_width=True, hide_index=True)

# ====================== VIBE ======================
st.divider()
if total_with_data > 0:
    bullish_ratio = positive_count / total_with_data
    if bullish_ratio >= 0.7:
        vibe = "🚀 **Strong Bullish**"
    elif bullish_ratio >= 0.55:
        vibe = "📈 **Mildly Bullish**"
    elif bullish_ratio >= 0.4:
        vibe = "⚖️ **Mixed**"
    else:
        vibe = "📉 **Cautious / Bearish**"
    st.subheader("🌡️ Overall Market Vibe")
    st.markdown(vibe)

if st.button("🔄 Refresh All Data"):
    st.cache_data.clear()
    st.rerun()

st.caption("CPO price converted to USD • % changes use proxy for CPO (due to limited history on FBMPM.L) • Refresh if needed")