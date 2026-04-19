import yfinance as yf
import pandas as pd
import streamlit as st
from config.settings import REFRESH_RATE


@st.cache_data(ttl=REFRESH_RATE)
def get_stock_data(tickers: list[str]) -> pd.DataFrame:
    """Fetch current price snapshot for the ticker cards."""
    rows = []
    for t in tickers:
        try:
            stock = yf.Ticker(t)
            hist  = stock.history(period="2d", interval="1m")

            if hist.empty:
                continue

            price      = float(hist["Close"].iloc[-1])
            open_price = float(hist["Open"].iloc[0])
            prev_close = float(hist["Close"].iloc[0])
            high       = float(hist["High"].max())
            low        = float(hist["Low"].min())
            volume     = int(hist["Volume"].sum())

            change     = price - open_price
            change_pct = (change / open_price * 100) if open_price else 0.0

            rows.append({
                "Ticker":     t,
                "Price":      round(price, 2),
                "Open":       round(open_price, 2),
                "Prev Close": round(prev_close, 2),
                "High":       round(high, 2),
                "Low":        round(low, 2),
                "Change":     round(change, 2),
                "Change %":   round(change_pct, 2),
                "Volume":     volume,
            })
        except Exception:
            continue

    return pd.DataFrame(rows)


@st.cache_data(ttl=REFRESH_RATE)
def get_history(ticker: str, period: str, interval: str) -> pd.DataFrame:
    """Fetch OHLCV history for charting."""
    try:
        df = yf.download(ticker, period=period, interval=interval, progress=False)
        df.dropna(inplace=True)
        return df
    except Exception:
        return pd.DataFrame()