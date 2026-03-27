import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import finnhub
import os

# ====================== CONFIG ======================
FINNHUB_API_KEY = "d734bs9r01qn7f07inigd734bs9r01qn7f07inj0"   # ← Replace with your actual key

st.set_page_config(
    page_title="🌅 Antonny's Morning Brief",
    page_icon="📈",
    layout="centered"
)

st.title("🌅 Good Morning, Antonny!")
st.subheader(f"{datetime.now().strftime('%B %d, %Y')} — Singapore Time")

# Your full watchlist
WATCHLIST = {
    "NVDA": "NVDA", "MSFT": "MSFT", "GOOGL": "GOOGL", "AAPL": "AAPL",
    "AMZN": "AMZN", "META": "META", "TSLA": "TSLA",
    "ACN": "ACN", "SAP": "SAP",
    "BTC-USD": "BTC", "SOL-USD": "SOL",
    "GLD": "GLD"
}

# Initialize Finnhub client
finnhub_client = finnhub.Client(api_key=FINNHUB_API_KEY)

@st.cache_data(ttl=600, show_spinner="Fetching latest market data...")  # Cache for 10 minutes
def get_performance(ticker):
    try:
        # Get real-time quote
        quote = finnhub_client.quote(ticker)
        
        current_price = quote.get('c')      # current price
        prev_close = quote.get('pc')        # previous close
        
        if current_price is None or prev_close is None:
            return {"price": "N/A", "change_1d": None, "change_1w": None, "change_1m": None}
        
        change_1d = round(((current_price - prev_close) / prev_close) * 100, 2)
        
        # For 1W and 1M we still use yfinance-style fallback or skip for now (Finnhub quote is mainly 1D)
        # Simple placeholder - you can enhance later with candles if needed
        change_1w = None
        change_1m = None
        
        return {
            "price": round(current_price, 2),
            "change_1d": change_1d,
            "change_1w": change_1w,
            "change_1m": change_1m
        }
    except Exception as e:
        st.warning(f"⚠️ Failed to load price for {ticker}: {str(e)[:80]}")
        return {"price": "N/A", "change_1d": None, "change_1w": None, "change_1m": None}

@st.cache_data(ttl=900)
def get_recent_news(ticker):
    try:
        # Get news from last 7 days
        to_date = datetime.now().strftime('%Y-%m-%d')
        from_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        
        news = finnhub_client.company_news(ticker, _from=from_date, to=to_date)
        return news[:3]  # Top 3 recent news per ticker
    except:
        return []

# ====================== PERFORMANCE TABLE ======================
st.subheader("📈 Your Watchlist Performance")

data_rows = []
for ticker in WATCHLIST:
    perf = get_performance(ticker)
    d1 = f"{perf['change_1d']:+.1f}%" if perf['change_1d'] is not None else "N/A"
    
    emoji = "🟢" if (perf.get('change_1d') or 0) >= 0 else "🔴"
    
    data_rows.append({
        "Asset": f"{emoji} {ticker}",
        "Price": f"${perf['price']}" if perf['price'] != "N/A" else "N/A",
        "1D %": d1,
        "1W %": "N/A (coming soon)",
        "1M %": "N/A (coming soon)"
    })

df = pd.DataFrame(data_rows)
st.dataframe(df, use_container_width=True, hide_index=True)

# ====================== NEWS SECTION ======================
st.divider()
st.subheader("📰 Top Recent News")

news_found = False
for ticker in list(WATCHLIST.keys())[:8]:   # Limit to avoid too many calls
    news_list = get_recent_news(ticker)
    if news_list:
        for item in news_list:
            if item.get('headline'):
                st.markdown(f"• **{item['headline']}**")
                if item.get('url'):
                    st.markdown(f"[Read full article →]({item['url']})")
                if item.get('source'):
                    st.caption(f"_{item['source']}_ • {ticker}")
                news_found = True

if not news_found:
    st.info("No recent news loaded yet. Click Refresh below or try again in a few minutes.")

# ====================== CONTROLS ======================
if st.button("🔄 Refresh All Data"):
    st.cache_data.clear()
    st.rerun()

st.caption("""
Data powered by Finnhub (free tier) • 
1W and 1M % coming in next update (requires candles endpoint) • 
Refresh button clears cache for fresh data
""")