import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from config.settings import color_map

# ── Constants ─────────────────────────────────────────────────────────────────
UP_COLOR   = "#26a641"
DOWN_COLOR = "#f85149"
UP_WICK    = "#3fb950"
DOWN_WICK  = "#ff7b72"

# ── Base layout applied to every chart ───────────────────────────────────────
BASE = dict(
    template="plotly_dark",
    paper_bgcolor="rgba(13,17,23,0.95)",
    plot_bgcolor="rgba(13,17,23,0.0)",
    font=dict(family="JetBrains Mono, monospace", size=12, color="#c9d1d9"),
    hoverlabel=dict(bgcolor="#161b22", bordercolor="#30363d",
                    font=dict(family="JetBrains Mono, monospace", size=12)),
    legend=dict(bgcolor="rgba(22,27,34,0.85)", bordercolor="#30363d",
                borderwidth=1, font=dict(size=11)),
    margin=dict(l=50, r=30, t=55, b=45),
)

XAXIS = dict(gridcolor="#21262d", linecolor="#30363d",
             showspikes=True, spikecolor="#444c56",
             spikedash="dot", spikethickness=1)

YAXIS = dict(gridcolor="#21262d", linecolor="#30363d",
             showspikes=True, spikecolor="#444c56",
             spikedash="dot", spikethickness=1)


# ═════════════════════════════════════════════════════════════════════════════
# HELPERS
# ═════════════════════════════════════════════════════════════════════════════

def _col(df: pd.DataFrame, name: str) -> pd.Series:
    """
    Safely pull a column from a yfinance DataFrame.
    yfinance can return multi-level columns like ("Close", "AAPL") —
    this flattens that and always returns a plain 1-D float Series.
    Returns an empty Series on failure.
    """
    try:
        s = df[name]
        # Multi-level column? grab first sub-column
        if isinstance(s, pd.DataFrame):
            s = s.iloc[:, 0]
        s = s.squeeze()
        return s.astype(float)
    except Exception:
        return pd.Series(dtype=float)


def _index(df: pd.DataFrame) -> pd.Index:
    """
    Return a timezone-free index Plotly can render.
    Plotly crashes on tz-aware DatetimeIndex — strip it here.
    """
    try:
        idx = df.index
        if isinstance(idx, pd.MultiIndex):
            idx = idx.get_level_values(0)
        if hasattr(idx, "tz") and idx.tz is not None:
            idx = idx.tz_localize(None)
        return idx
    except Exception:
        return pd.RangeIndex(len(df))


def _clip(s: pd.Series, factor: float = 5.0) -> pd.Series:
    """
    Clip extreme outliers using IQR so one bad tick doesn't blow the axis.
    e.g. a corrupted $0 price or $999999 spike gets clamped to a sane range.
    """
    if s.empty:
        return s
    q1, q3 = s.quantile(0.25), s.quantile(0.75)
    iqr = q3 - q1
    if iqr == 0:
        return s
    return s.clip(q1 - factor * iqr, q3 + factor * iqr)


def _yrange(s: pd.Series, pad: float = 0.05):
    """Return a padded [min, max] for a y-axis, or None if series is empty."""
    s = s.dropna()
    if s.empty:
        return None
    lo, hi = s.min(), s.max()
    span = hi - lo or abs(hi) * 0.1 or 1
    return [lo - span * pad, hi + span * pad]


# ═════════════════════════════════════════════════════════════════════════════
# CHART 1 — COMPARISON LINE CHART
# ═════════════════════════════════════════════════════════════════════════════

def make_comparison_chart(histories: dict, normalised: bool = False) -> go.Figure:
    """
    Overlaid line chart for all selected tickers.
    normalised=True rebases every line to 100 at t=0 so you can compare
    percentage moves regardless of absolute price differences.
    """
    fig   = go.Figure()
    all_y = []

    for ticker, df in histories.items():
        if df.empty or "Close" not in df.columns:
            continue
        try:
            close = _clip(_col(df, "Close"))
            if close.empty or close.iloc[0] == 0:
                continue

            y      = (close / close.iloc[0] * 100) if normalised else close
            colour = color_map.get(ticker, "#8b949e")
            x      = _index(df)
            all_y.append(y)

            fig.add_trace(go.Scatter(
                x=x, y=y,
                mode="lines",
                name=ticker,
                line=dict(color=colour, width=2),
                fill="tozeroy",
                fillcolor=colour + "1a",          # ~10% opacity fill
                hovertemplate=(
                    f"<b>{ticker}</b><br>%{{x|%Y-%m-%d %H:%M}}<br>"
                    + ("Rebased: %{y:.2f}" if normalised else "Price: $%{y:,.2f}")
                    + "<extra></extra>"
                ),
            ))
        except Exception:
            continue

    # Compute a safe y-range across all traces
    y_range = _yrange(pd.concat(all_y)) if all_y else None

    fig.update_layout(
        **BASE,
        title=dict(text="Multi-Stock Comparison", font=dict(size=16)),
        hovermode="x unified",
        xaxis=dict(
            **XAXIS,
            type="date",
            rangeslider=dict(visible=True, bgcolor="#0d1117", thickness=0.05),
            rangeselector=dict(
                bgcolor="#161b22", activecolor="#388bfd", bordercolor="#30363d",
                font=dict(color="#c9d1d9", size=11),
                buttons=[
                    dict(count=1,  label="1D",  step="day",   stepmode="backward"),
                    dict(count=5,  label="5D",  step="day",   stepmode="backward"),
                    dict(count=1,  label="1M",  step="month", stepmode="backward"),
                    dict(count=3,  label="3M",  step="month", stepmode="backward"),
                    dict(count=6,  label="6M",  step="month", stepmode="backward"),
                    dict(count=1,  label="1Y",  step="year",  stepmode="backward"),
                    dict(step="all", label="All"),
                ],
            ),
        ),
        yaxis=dict(**YAXIS,
                   title="Rebased (base=100)" if normalised else "Price (USD)",
                   range=y_range),
        legend=dict(**BASE["legend"], orientation="h",
                    yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig


# ═════════════════════════════════════════════════════════════════════════════
# CHART 2 — CANDLESTICK  (price + volume subplot + optional indicators)
# ═════════════════════════════════════════════════════════════════════════════

def make_candlestick_chart(df: pd.DataFrame, ticker: str,
                           indicators: bool = True) -> go.Figure:
    """
    Single-ticker candlestick with:
    - correct green/red body AND wick colours
    - volume bars synced below (green up-day, red down-day)
    - optional SMA-20, SMA-50, Bollinger Band overlay
    - outlier-safe axes
    """
    if df.empty:
        return go.Figure()

    # Pull OHLCV — bail out cleanly if data is broken
    op = _clip(_col(df, "Open"))
    hi = _clip(_col(df, "High"))
    lo = _clip(_col(df, "Low"))
    cl = _clip(_col(df, "Close"))
    if any(s.empty for s in [op, hi, lo, cl]):
        return go.Figure()

    x     = _index(df)
    is_up = (cl >= op).values          # boolean array, one per candle

    # Volume is optional — futures & some tickers return 0
    vol_raw   = _col(df, "Volume") if "Volume" in df.columns else pd.Series(dtype=float)
    has_vol   = not vol_raw.empty and vol_raw.sum() > 0

    # Build subplot grid: price on top, volume below if available
    rows        = 2 if has_vol else 1
    row_heights = [0.72, 0.28] if has_vol else [1.0]

    fig = make_subplots(rows=rows, cols=1, shared_xaxes=True,
                        row_heights=row_heights, vertical_spacing=0.02)

    # ── Candlestick ──────────────────────────────────────────────────────────
    fig.add_trace(go.Candlestick(
        x=x, open=op, high=hi, low=lo, close=cl,
        name=ticker,
        increasing=dict(line=dict(color=UP_WICK,   width=1), fillcolor=UP_COLOR),
        decreasing=dict(line=dict(color=DOWN_WICK, width=1), fillcolor=DOWN_COLOR),
        whiskerwidth=0.3,
        hoverinfo="x+y",               # keep it simple — avoids per-row format errors
    ), row=1, col=1)

    # ── Indicator overlays ───────────────────────────────────────────────────
    if indicators:
        for col_name, label, colour, dash, lw in [
            ("SMA20",    "SMA 20",   "#388bfd", "solid", 1.5),
            ("SMA50",    "SMA 50",   "#f0e68c", "dot",   1.5),
            ("BB_upper", "BB Upper", "#58a6ff", "dash",  1.0),
            ("BB_lower", "BB Lower", "#58a6ff", "dash",  1.0),
        ]:
            if col_name not in df.columns:
                continue
            s = _col(df, col_name)
            if s.empty:
                continue
            fig.add_trace(go.Scatter(
                x=x, y=s, mode="lines", name=label,
                line=dict(color=colour, width=lw, dash=dash),
                hoverinfo="skip", showlegend=True,
            ), row=1, col=1)

        # Shaded band between BB upper/lower
        if "BB_upper" in df.columns and "BB_lower" in df.columns:
            u = _col(df, "BB_upper")
            l = _col(df, "BB_lower")
            if not u.empty and not l.empty:
                x_fwd = list(x)
                x_rev = list(x)[::-1]
                fig.add_trace(go.Scatter(
                    x=x_fwd + x_rev,
                    y=list(u) + list(l)[::-1],
                    fill="toself",
                    fillcolor="rgba(88,166,255,0.06)",
                    line=dict(color="rgba(0,0,0,0)"),
                    hoverinfo="skip", showlegend=False, name="BB Band",
                ), row=1, col=1)

    # ── Volume bars ──────────────────────────────────────────────────────────
    if has_vol:
        vol = _clip(vol_raw, factor=6.0)
        fig.add_trace(go.Bar(
            x=x, y=vol,
            marker_color=[UP_COLOR if u else DOWN_COLOR for u in is_up],
            marker_line_width=0,
            name="Volume", showlegend=False,
            hovertemplate="%{x|%Y-%m-%d}<br>Vol: %{y:,.0f}<extra></extra>",
        ), row=2, col=1)
        fig.update_yaxes(title_text="Volume", row=2, col=1,
                         gridcolor="#21262d", linecolor="#30363d")

    # ── Layout ───────────────────────────────────────────────────────────────
    fig.update_layout(
        **BASE,
        title=dict(text=f"{ticker} — Candlestick", font=dict(size=16)),
        hovermode="x unified",
        xaxis_rangeslider_visible=False,
        legend=dict(**BASE["legend"], orientation="h",
                    yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    fig.update_yaxes(title_text="Price (USD)", range=_yrange(cl),
                     row=1, col=1, **YAXIS)
    for i in range(1, rows + 1):
        fig.update_xaxes(row=i, col=1, **XAXIS)

    return fig


# ═════════════════════════════════════════════════════════════════════════════
# CHART 3 — RSI
# ═════════════════════════════════════════════════════════════════════════════

def make_rsi_chart(df: pd.DataFrame, ticker: str) -> go.Figure:
    """RSI(14) with overbought/oversold zones shaded."""
    if "RSI" not in df.columns:
        return go.Figure()

    rsi    = _col(df, "RSI")
    x      = _index(df)
    colour = color_map.get(ticker, "#8b949e")

    fig = go.Figure()
    # Shaded zones
    fig.add_hrect(y0=70, y1=100, fillcolor="rgba(248,81,73,0.08)",  line_width=0)
    fig.add_hrect(y0=0,  y1=30,  fillcolor="rgba(38,166,65,0.08)",  line_width=0)
    # Reference lines
    fig.add_hline(y=70, line_dash="dash", line_color=DOWN_COLOR, line_width=1, opacity=0.6)
    fig.add_hline(y=50, line_dash="dot",  line_color="#444c56",  line_width=1, opacity=0.4)
    fig.add_hline(y=30, line_dash="dash", line_color=UP_COLOR,   line_width=1, opacity=0.6)
    # RSI line
    fig.add_trace(go.Scatter(
        x=x, y=rsi, mode="lines", name="RSI",
        line=dict(color=colour, width=2),
        fill="tozeroy", fillcolor=colour + "15",
        hovertemplate="%{x|%Y-%m-%d %H:%M}<br>RSI: %{y:.1f}<extra></extra>",
    ))
    fig.update_layout(
        **BASE,
        title=dict(text=f"{ticker} — RSI (14)", font=dict(size=15)),
        hovermode="x unified",
        xaxis=dict(**XAXIS),
        yaxis=dict(**YAXIS, title="RSI", range=[0, 100]),
    )
    return fig


# ═════════════════════════════════════════════════════════════════════════════
# CHART 4 — DAILY CHANGE HEATMAP (bar chart)
# ═════════════════════════════════════════════════════════════════════════════

def make_heatmap(df_snapshot: pd.DataFrame) -> go.Figure:
    """Sorted bar chart showing daily % change for all watchlist stocks."""
    if df_snapshot.empty:
        return go.Figure()

    df      = df_snapshot.sort_values("Change %", ascending=False)
    tickers = df["Ticker"].tolist()
    changes = df["Change %"].tolist()
    colors  = [UP_COLOR if c >= 0 else DOWN_COLOR for c in changes]
    max_abs = max((abs(c) for c in changes), default=5)

    fig = go.Figure(go.Bar(
        x=tickers, y=changes,
        marker_color=colors, marker_line_width=0,
        text=[f"{c:+.2f}%" for c in changes],
        textposition="outside", textfont=dict(size=10),
        hovertemplate="<b>%{x}</b><br>%{y:+.2f}%<extra></extra>",
    ))
    fig.add_hline(y=0, line_color="#444c56", line_width=1)
    fig.update_layout(
        **BASE,
        title=dict(text="Daily % Change", font=dict(size=16)),
        hovermode="closest",
        xaxis=dict(**XAXIS, title="Ticker"),
        yaxis=dict(**YAXIS, title="Change (%)",
                   range=[-(max_abs * 1.4), max_abs * 1.4],
                   zeroline=True, zerolinecolor="#444c56"),
    )
    return fig