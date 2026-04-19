import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from config.settings import color_map

DARK = "plotly_dark"
LAYOUT_BASE = dict(
    template=DARK,
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="monospace", color="#e0e0e0"),
    legend=dict(bgcolor="rgba(0,0,0,0.3)", bordercolor="#333", borderwidth=1),
    margin=dict(l=40, r=20, t=50, b=40),
)


def make_comparison_chart(histories: dict[str, pd.DataFrame], normalised: bool = False) -> go.Figure:
    """Line chart comparing multiple tickers — raw price or % rebased."""
    fig = go.Figure()

    for ticker, df in histories.items():
        if df.empty or "Close" not in df.columns:
            continue
        close = df["Close"].squeeze()
        y = (close / close.iloc[0] * 100) if normalised else close
        fig.add_trace(go.Scatter(
            x=df.index, y=y,
            mode="lines",
            name=ticker,
            line=dict(color=color_map.get(ticker, "#aaaaaa"), width=2),
            hovertemplate=f"<b>{ticker}</b><br>%{{x|%b %d %H:%M}}<br>{'Rebased' if normalised else 'Price'}: %{{y:.2f}}<extra></extra>",
        ))

    y_title = "Rebased Value (base=100)" if normalised else "Price (USD)"
    fig.update_layout(
        **LAYOUT_BASE,
        title="Multi-Stock Comparison",
        xaxis_title="Time",
        yaxis_title=y_title,
    )
    return fig


def make_candlestick_chart(df: pd.DataFrame, ticker: str, indicators: bool = True) -> go.Figure:
    """Candlestick chart with optional SMA + Bollinger Bands overlaid."""
    fig = go.Figure()

    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df["Open"].squeeze(),
        high=df["High"].squeeze(),
        close=df["Close"].squeeze(),
        low=df["Low"].squeeze(),
        name=ticker,
        increasing_line_color="#00ff88",
        decreasing_line_color="#ff3b30",
    ))

    if indicators:
        for col, label, color, dash in [
            ("SMA20", "SMA 20", "#4da3ff", "solid"),
            ("SMA50", "SMA 50", "#ffcc00", "dot"),
            ("BB_upper", "BB Upper", "#888888", "dash"),
            ("BB_lower", "BB Lower", "#888888", "dash"),
        ]:
            if col in df.columns:
                fig.add_trace(go.Scatter(
                    x=df.index, y=df[col].squeeze(),
                    mode="lines", name=label,
                    line=dict(color=color, width=1, dash=dash),
                    hoverinfo="skip",
                ))

    fig.update_layout(
        **LAYOUT_BASE,
        title=f"{ticker} — Candlestick",
        xaxis_title="Time",
        yaxis_title="Price (USD)",
        xaxis_rangeslider_visible=False,
    )
    return fig


def make_volume_chart(df: pd.DataFrame, ticker: str) -> go.Figure:
    """Bar chart of volume coloured green/red by price direction."""
    if df.empty or "Volume" not in df.columns:
        return go.Figure()

    close = df["Close"].squeeze()
    colors = ["#00ff88" if c >= o else "#ff3b30"
              for c, o in zip(close, df["Open"].squeeze())]

    fig = go.Figure(go.Bar(
        x=df.index,
        y=df["Volume"].squeeze(),
        marker_color=colors,
        name="Volume",
        hovertemplate="%{x|%b %d}<br>Volume: %{y:,.0f}<extra></extra>",
    ))
    fig.update_layout(
        **LAYOUT_BASE,
        title=f"{ticker} — Volume",
        xaxis_title="Time",
        yaxis_title="Volume",
    )
    return fig


def make_rsi_chart(df: pd.DataFrame, ticker: str) -> go.Figure:
    """RSI line chart with overbought/oversold bands."""
    if "RSI" not in df.columns:
        return go.Figure()

    fig = go.Figure()
    fig.add_hline(y=70, line_dash="dash", line_color="#ff3b30", opacity=0.6)
    fig.add_hline(y=30, line_dash="dash", line_color="#00ff88", opacity=0.6)
    fig.add_trace(go.Scatter(
        x=df.index, y=df["RSI"].squeeze(),
        mode="lines", name="RSI",
        line=dict(color=color_map.get(ticker, "#aaaaaa"), width=2),
    ))
    fig.update_layout(
        **LAYOUT_BASE,
        title=f"{ticker} — RSI (14)",
        xaxis_title="Time",
        yaxis_title="RSI",
        yaxis=dict(range=[0, 100]),
    )
    return fig


def make_heatmap(df_snapshot: pd.DataFrame) -> go.Figure:
    """Colour-coded heatmap of % change across all selected tickers."""
    if df_snapshot.empty:
        return go.Figure()

    tickers = df_snapshot["Ticker"].tolist()
    changes = df_snapshot["Change %"].tolist()
    colors  = ["#00ff88" if c >= 0 else "#ff3b30" for c in changes]

    fig = go.Figure(go.Bar(
        x=tickers, y=changes,
        marker_color=colors,
        text=[f"{c:+.2f}%" for c in changes],
        textposition="outside",
        hovertemplate="%{x}<br>Change: %{y:+.2f}%<extra></extra>",
    ))
    fig.update_layout(
        **LAYOUT_BASE,
        title="Daily % Change — All Stocks",
        xaxis_title="Ticker",
        yaxis_title="Change (%)",
        yaxis=dict(zeroline=True, zerolinecolor="#444"),
    )
    return fig