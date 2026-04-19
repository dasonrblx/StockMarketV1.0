import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from config.settings import color_map

# ── Shared layout base ────────────────────────────────────────────────────────
_LAYOUT = dict(
    template="plotly_dark",
    paper_bgcolor="rgba(13,17,23,0.95)",
    plot_bgcolor="rgba(13,17,23,0.0)",
    font=dict(family="JetBrains Mono, monospace", size=12, color="#c9d1d9"),
    legend=dict(
        bgcolor="rgba(22,27,34,0.85)",
        bordercolor="#30363d",
        borderwidth=1,
        font=dict(size=11),
    ),
    hoverlabel=dict(
        bgcolor="#161b22",
        bordercolor="#30363d",
        font=dict(family="JetBrains Mono, monospace", size=12),
    ),
    margin=dict(l=50, r=30, t=55, b=45),
    xaxis=dict(
        gridcolor="#21262d",
        linecolor="#30363d",
        showspikes=True,
        spikecolor="#444c56",
        spikedash="dot",
        spikethickness=1,
    ),
    yaxis=dict(
        gridcolor="#21262d",
        linecolor="#30363d",
        showspikes=True,
        spikecolor="#444c56",
        spikedash="dot",
        spikethickness=1,
    ),
)

# ── Colours ───────────────────────────────────────────────────────────────────
UP_COLOR   = "#26a641"   # green  — bullish candle body + volume bar
DOWN_COLOR = "#f85149"   # red    — bearish candle body + volume bar
UP_WICK    = "#3fb950"   # lighter green for wicks
DOWN_WICK  = "#ff7b72"   # lighter red for wicks


# ── Helpers ───────────────────────────────────────────────────────────────────

def _safe_squeeze(series: pd.Series) -> pd.Series:
    """Ensure we always get a 1-D Series even from multi-level columns."""
    s = series.squeeze()
    if isinstance(s, pd.DataFrame):
        s = s.iloc[:, 0]
    return s


def _remove_outliers(series: pd.Series, iqr_factor: float = 5.0) -> pd.Series:
    """
    Cap extreme outlier values using IQR fencing so one bad tick doesn't
    blow up the y-axis. Values outside factor×IQR are clipped, not dropped.
    """
    q1, q3 = series.quantile(0.25), series.quantile(0.75)
    iqr = q3 - q1
    if iqr == 0:
        return series
    lo, hi = q1 - iqr_factor * iqr, q3 + iqr_factor * iqr
    return series.clip(lo, hi)


def _axis_range_with_padding(series: pd.Series, pad: float = 0.05):
    """Return [min, max] with padding so traces don't hug the edges."""
    clean = series.dropna()
    if clean.empty:
        return None
    lo, hi = clean.min(), clean.max()
    span = hi - lo or abs(hi) * 0.1 or 1
    return [lo - span * pad, hi + span * pad]


# ── 1. Comparison chart ───────────────────────────────────────────────────────

def make_comparison_chart(
    histories: dict[str, pd.DataFrame],
    normalised: bool = False,
) -> go.Figure:
    """
    Rich multi-ticker comparison with:
    - filled area under each line for depth
    - crosshair spikes on both axes
    - range-selector buttons + slider
    - hover unified mode so all tickers show at once
    - outlier-safe y-axis
    """
    fig = go.Figure()

    all_y: list[pd.Series] = []

    for ticker, df in histories.items():
        if df.empty or "Close" not in df.columns:
            continue

        close = _safe_squeeze(df["Close"])
        close = _remove_outliers(close)

        y = (close / close.iloc[0] * 100) if normalised else close
        all_y.append(y)

        colour = color_map.get(ticker, "#8b949e")
        # Transparent fill — same hue, 15 % opacity
        fill_colour = colour + "26"  # hex alpha 26 ≈ 15 %

        fig.add_trace(go.Scatter(
            x=df.index,
            y=y,
            mode="lines",
            name=ticker,
            line=dict(color=colour, width=2),
            fill="tozeroy",
            fillcolor=fill_colour,
            hovertemplate=(
                f"<b>{ticker}</b><br>"
                "%{x|%Y-%m-%d %H:%M}<br>"
                + ("Rebased: %{y:.2f}" if normalised else "Price: $%{y:,.2f}")
                + "<extra></extra>"
            ),
        ))

    # Safe y-axis range
    if all_y:
        combined = pd.concat(all_y).dropna()
        y_range = _axis_range_with_padding(combined)
    else:
        y_range = None

    y_title = "Rebased (base = 100)" if normalised else "Price (USD)"

    fig.update_layout(
        **_LAYOUT,
        title=dict(text="Multi-Stock Comparison", font=dict(size=16)),
        xaxis_title="Time",
        yaxis_title=y_title,
        yaxis=dict(**_LAYOUT["yaxis"], range=y_range),
        hovermode="x unified",
        # Range selector buttons
        xaxis=dict(
            **_LAYOUT["xaxis"],
            rangeselector=dict(
                buttons=[
                    dict(count=1,  label="1D",  step="day",   stepmode="backward"),
                    dict(count=5,  label="5D",  step="day",   stepmode="backward"),
                    dict(count=1,  label="1M",  step="month", stepmode="backward"),
                    dict(count=3,  label="3M",  step="month", stepmode="backward"),
                    dict(count=6,  label="6M",  step="month", stepmode="backward"),
                    dict(count=1,  label="1Y",  step="year",  stepmode="backward"),
                    dict(step="all", label="All"),
                ],
                bgcolor="#161b22",
                activecolor="#388bfd",
                bordercolor="#30363d",
                font=dict(color="#c9d1d9", size=11),
            ),
            rangeslider=dict(visible=True, bgcolor="#0d1117", thickness=0.06),
            type="date",
        ),
        legend=dict(
            **_LAYOUT["legend"],
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
        ),
    )

    return fig


# ── 2. Candlestick chart ──────────────────────────────────────────────────────

def make_candlestick_chart(
    df: pd.DataFrame,
    ticker: str,
    indicators: bool = True,
) -> go.Figure:
    """
    Candlestick with:
    - explicit up/down colours (green body + green wick / red body + red wick)
    - outlier-clipped price axis so a bad tick doesn't break the view
    - optional SMA-20, SMA-50, Bollinger Bands
    - volume subplot synced to x-axis
    - crosshair spikes
    """
    if df.empty:
        return go.Figure()

    # Pull columns safely
    try:
        op = _safe_squeeze(df["Open"]).astype(float)
        hi = _safe_squeeze(df["High"]).astype(float)
        lo = _safe_squeeze(df["Low"]).astype(float)
        cl = _safe_squeeze(df["Close"]).astype(float)
    except Exception:
        return go.Figure()

    # Clip price outliers
    op = _remove_outliers(op)
    hi = _remove_outliers(hi)
    lo = _remove_outliers(lo)
    cl = _remove_outliers(cl)

    # Per-candle colour arrays — this is what fixes "random" colours
    is_up      = cl >= op
    body_color = [UP_COLOR   if u else DOWN_COLOR for u in is_up]
    wick_color = [UP_WICK    if u else DOWN_WICK   for u in is_up]

    has_volume = "Volume" in df.columns and _safe_squeeze(df["Volume"]).sum() > 0

    # Build subplots — price on top, volume below (if available)
    row_heights = [0.72, 0.28] if has_volume else [1.0]
    rows = 2 if has_volume else 1

    fig = make_subplots(
        rows=rows, cols=1,
        shared_xaxes=True,
        row_heights=row_heights,
        vertical_spacing=0.02,
    )

    # ── Candlestick trace ──
    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=op, high=hi, low=lo, close=cl,
            name=ticker,
            increasing=dict(
                line=dict(color=UP_WICK,   width=1),
                fillcolor=UP_COLOR,
            ),
            decreasing=dict(
                line=dict(color=DOWN_WICK, width=1),
                fillcolor=DOWN_COLOR,
            ),
            whiskerwidth=0.3,
            hovertext=[
                f"<b>{ticker}</b><br>"
                f"O: ${o:,.2f}  H: ${h:,.2f}<br>"
                f"L: ${l:,.2f}  C: ${c:,.2f}<br>"
                f"{'▲' if u else '▼'} {'+' if u else ''}{((c-o)/o*100):.2f}%"
                for o, h, l, c, u in zip(op, hi, lo, cl, is_up)
            ],
            hoverinfo="text",
        ),
        row=1, col=1,
    )

    # ── Indicator overlays ──
    if indicators:
        overlay_cfg = [
            ("SMA20",    "SMA 20",   "#388bfd", "solid", 1.5),
            ("SMA50",    "SMA 50",   "#f0e68c", "dot",   1.5),
            ("BB_upper", "BB Upper", "#58a6ff", "dash",  1),
            ("BB_lower", "BB Lower", "#58a6ff", "dash",  1),
        ]
        for col_name, label, colour, dash, width in overlay_cfg:
            if col_name not in df.columns:
                continue
            s = _safe_squeeze(df[col_name]).astype(float)
            fig.add_trace(
                go.Scatter(
                    x=df.index, y=s,
                    mode="lines", name=label,
                    line=dict(color=colour, width=width, dash=dash),
                    hoverinfo="skip",
                    showlegend=True,
                ),
                row=1, col=1,
            )

        # BB fill between bands
        if "BB_upper" in df.columns and "BB_lower" in df.columns:
            fig.add_trace(
                go.Scatter(
                    x=pd.concat([pd.Series(df.index), pd.Series(df.index[::-1])]),
                    y=pd.concat([
                        _safe_squeeze(df["BB_upper"]).astype(float),
                        _safe_squeeze(df["BB_lower"]).astype(float).iloc[::-1],
                    ]),
                    fill="toself",
                    fillcolor="rgba(88,166,255,0.07)",
                    line=dict(color="rgba(0,0,0,0)"),
                    hoverinfo="skip",
                    showlegend=False,
                    name="BB Band",
                ),
                row=1, col=1,
            )

    # ── Volume subplot ──
    if has_volume:
        vol = _safe_squeeze(df["Volume"]).astype(float)
        vol = _remove_outliers(vol, iqr_factor=6.0)
        vol_colors = [UP_COLOR if u else DOWN_COLOR for u in is_up]

        fig.add_trace(
            go.Bar(
                x=df.index,
                y=vol,
                name="Volume",
                marker_color=vol_colors,
                marker_line_width=0,
                hovertemplate="%{x|%Y-%m-%d}<br>Volume: %{y:,.0f}<extra></extra>",
                showlegend=False,
            ),
            row=2, col=1,
        )

        fig.update_yaxes(
            title_text="Volume",
            row=2, col=1,
            gridcolor="#21262d",
            linecolor="#30363d",
        )

    # ── Y-axis safe range for price ──
    price_range = _axis_range_with_padding(cl)

    fig.update_layout(
        **_LAYOUT,
        title=dict(text=f"{ticker} — Candlestick", font=dict(size=16)),
        yaxis=dict(
            **_LAYOUT["yaxis"],
            title="Price (USD)",
            range=price_range,
        ),
        xaxis_rangeslider_visible=False,
        hovermode="x unified",
        legend=dict(
            **_LAYOUT["legend"],
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
        ),
    )

    # Sync x-axis spikes across subplots
    for i in range(1, rows + 1):
        fig.update_xaxes(
            showspikes=True,
            spikecolor="#444c56",
            spikedash="dot",
            spikethickness=1,
            row=i, col=1,
        )

    return fig


# ── 3. Standalone volume chart (used outside candlestick tab) ─────────────────

def make_volume_chart(df: pd.DataFrame, ticker: str) -> go.Figure:
    """Standalone volume bar chart with correct green/red per candle direction."""
    if df.empty or "Volume" not in df.columns:
        return go.Figure()

    try:
        cl  = _safe_squeeze(df["Close"]).astype(float)
        op  = _safe_squeeze(df["Open"]).astype(float)
        vol = _safe_squeeze(df["Volume"]).astype(float)
    except Exception:
        return go.Figure()

    vol   = _remove_outliers(vol, iqr_factor=6.0)
    is_up = cl >= op
    colors = [UP_COLOR if u else DOWN_COLOR for u in is_up]

    fig = go.Figure(go.Bar(
        x=df.index,
        y=vol,
        marker_color=colors,
        marker_line_width=0,
        name="Volume",
        hovertemplate="%{x|%Y-%m-%d %H:%M}<br>Volume: %{y:,.0f}<extra></extra>",
    ))

    fig.update_layout(
        **_LAYOUT,
        title=dict(text=f"{ticker} — Volume", font=dict(size=15)),
        xaxis_title="Time",
        yaxis_title="Volume",
        yaxis=dict(**_LAYOUT["yaxis"], range=_axis_range_with_padding(vol, pad=0.1)),
        hovermode="x unified",
    )
    return fig


# ── 4. RSI chart ──────────────────────────────────────────────────────────────

def make_rsi_chart(df: pd.DataFrame, ticker: str) -> go.Figure:
    """RSI with coloured gradient fill — green below 30, red above 70."""
    if "RSI" not in df.columns:
        return go.Figure()

    rsi = _safe_squeeze(df["RSI"]).astype(float)
    colour = color_map.get(ticker, "#8b949e")

    fig = go.Figure()

    # Overbought / oversold zones
    fig.add_hrect(y0=70, y1=100, fillcolor="rgba(248,81,73,0.08)",  line_width=0)
    fig.add_hrect(y0=0,  y1=30,  fillcolor="rgba(38,166,65,0.08)",  line_width=0)
    fig.add_hline(y=70, line_dash="dash", line_color=DOWN_COLOR, line_width=1, opacity=0.7)
    fig.add_hline(y=50, line_dash="dot",  line_color="#444c56",  line_width=1, opacity=0.5)
    fig.add_hline(y=30, line_dash="dash", line_color=UP_COLOR,   line_width=1, opacity=0.7)

    fig.add_trace(go.Scatter(
        x=df.index, y=rsi,
        mode="lines",
        name="RSI",
        line=dict(color=colour, width=2),
        fill="tozeroy",
        fillcolor=colour + "18",
        hovertemplate="%{x|%Y-%m-%d %H:%M}<br>RSI: %{y:.1f}<extra></extra>",
    ))

    fig.update_layout(
        **_LAYOUT,
        title=dict(text=f"{ticker} — RSI (14)", font=dict(size=15)),
        xaxis_title="Time",
        yaxis_title="RSI",
        yaxis=dict(**_LAYOUT["yaxis"], range=[0, 100]),
        hovermode="x unified",
    )
    return fig


# ── 5. Heatmap / daily change bar chart ──────────────────────────────────────

def make_heatmap(df_snapshot: pd.DataFrame) -> go.Figure:
    """Sorted bar chart of daily % change — green positive, red negative."""
    if df_snapshot.empty:
        return go.Figure()

    df = df_snapshot.copy().sort_values("Change %", ascending=False)
    tickers = df["Ticker"].tolist()
    changes = df["Change %"].tolist()
    colors  = [UP_COLOR if c >= 0 else DOWN_COLOR for c in changes]

    fig = go.Figure(go.Bar(
        x=tickers,
        y=changes,
        marker_color=colors,
        marker_line_width=0,
        text=[f"{c:+.2f}%" for c in changes],
        textposition="outside",
        textfont=dict(size=10),
        hovertemplate="<b>%{x}</b><br>Change: %{y:+.2f}%<extra></extra>",
    ))

    # Zero line
    fig.add_hline(y=0, line_color="#444c56", line_width=1)

    # Dynamic y-range so text labels aren't clipped
    max_abs = max(abs(c) for c in changes) if changes else 5
    fig.update_layout(
        **_LAYOUT,
        title=dict(text="Daily % Change", font=dict(size=16)),
        xaxis_title="Ticker",
        yaxis_title="Change (%)",
        yaxis=dict(
            **_LAYOUT["yaxis"],
            range=[-(max_abs * 1.35), max_abs * 1.35],
            zeroline=True,
            zerolinecolor="#444c56",
        ),
        hovermode="closest",
    )
    return fig