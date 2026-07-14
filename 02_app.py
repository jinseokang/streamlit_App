import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

st.set_page_config(
    page_title="Global Top10 Market Cap Dashboard",
    layout="wide"
)

st.title("🌍 Global Top 10 Market Cap Stocks")
st.markdown("최근 1년 주가 변화")

# Top10 (2025~2026 기준 대표 기업)
stocks = {
    "Apple":"AAPL",
    "Microsoft":"MSFT",
    "NVIDIA":"NVDA",
    "Amazon":"AMZN",
    "Alphabet":"GOOGL",
    "Meta":"META",
    "Saudi Aramco":"2222.SR",
    "Broadcom":"AVGO",
    "TSMC":"TSM",
    "Tesla":"TSLA"
}

today = datetime.today()
start = today - timedelta(days=365)

@st.cache_data(ttl=3600)
def load_data():
    df = yf.download(
        list(stocks.values()),
        start=start,
        end=today,
        auto_adjust=True,
        progress=False
    )["Close"]
    return df

data = load_data()

# Normalize
normalized = data / data.iloc[0] * 100

fig = go.Figure()

for company, ticker in stocks.items():

    fig.add_trace(
        go.Scatter(
            x=normalized.index,
            y=normalized[ticker],
            mode="lines",
            name=company,
            hovertemplate=
            "<b>%{fullData.name}</b><br>"
            "Date: %{x|%Y-%m-%d}<br>"
            "Index: %{y:.2f}<extra></extra>"
        )
    )

fig.update_layout(
    title="Normalized Stock Performance (100 = 1 Year Ago)",
    xaxis_title="Date",
    yaxis_title="Relative Performance",
    hovermode="x unified",
    template="plotly_dark",
    height=700
)

st.plotly_chart(fig, use_container_width=True)

st.divider()

st.subheader("Current Performance")

returns = (
    normalized.iloc[-1]-100
).sort_values(ascending=False)

performance = pd.DataFrame({
    "Company":[k for k,v in stocks.items()],
    "Ticker":[v for k,v in stocks.items()]
})

performance["Return(%)"] = performance["Ticker"].map(returns)

performance = performance.sort_values(
    "Return(%)",
    ascending=False
)

st.dataframe(
    performance,
    use_container_width=True,
    hide_index=True
)
