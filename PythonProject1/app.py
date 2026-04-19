import time
import streamlit as st

from config.settings import STOCKS, SECTORS, REFRESH_RATE, TIME_RANGES
from auth.login import login
from data.fetcher import get_stock_data, get_history
from data.processor import add_technical_indicators
from charts.graphs import (
    make_comparison_chart,
    make_candlestick_chart,
    make_volume_chart,
    make_rsi_chart,
    make_heatmap,
)

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="StockMarket",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');

/* ── Global reset ── */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    background-color: #080c10;
}

/* ── Hide default streamlit chrome ── */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 2rem 2.5rem 2rem 2.5rem !important; }

/* ══════════════════════════════════════
   SIDEBAR
══════════════════════════════════════ */
[data-testid="stSidebar"] {
    background: #0b0f14 !important;
    border-right: 1px solid #1a2030 !important;
    padding: 0 !important;
}
[data-testid="stSidebar"] > div:first-child {
    padding: 0 !important;
}

/* User badge at top */
.sb-user {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 22px 20px 18px;
    border-bottom: 1px solid #1a2030;
    margin-bottom: 6px;
}
.sb-avatar {
    width: 36px; height: 36px;
    border-radius: 50%;
    background: linear-gradient(135deg, #3b82f6, #8b5cf6);
    display: flex; align-items: center; justify-content: center;
    font-size: 15px; font-weight: 700; color: #fff;
    flex-shrink: 0;
}
.sb-name  { font-size: 0.85rem; font-weight: 600; color: #e2e8f0; }
.sb-role  { font-size: 0.68rem; color: #4a5568; letter-spacing: 0.05em; text-transform: uppercase; }

/* Section label */
.sb-label {
    font-size: 0.62rem;
    font-weight: 600;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #2d3748;
    padding: 14px 20px 6px;
}

/* Toggle row */
.sb-toggle-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 4px 20px;
    margin: 2px 0;
}
.sb-toggle-label {
    font-size: 0.78rem;
    color: #94a3b8;
    font-weight: 500;
}

/* Sidebar divider */
.sb-div {
    border: none;
    border-top: 1px solid #1a2030;
    margin: 10px 0;
}

/* Logout button */
[data-testid="stSidebar"] [data-testid="stButton"] button {
    background: transparent !important;
    border: 1px solid #1e2d3d !important;
    color: #4a5568 !important;
    border-radius: 8px !important;
    font-size: 0.75rem !important;
    font-weight: 500 !important;
    padding: 8px 16px !important;
    width: calc(100% - 40px) !important;
    margin: 8px 20px !important;
    transition: all 0.2s !important;
    letter-spacing: 0.04em;
}
[data-testid="stSidebar"] [data-testid="stButton"] button:hover {
    border-color: #f85149 !important;
    color: #f85149 !important;
    background: rgba(248,81,73,0.06) !important;
}

/* Sidebar selectbox + multiselect */
[data-testid="stSidebar"] [data-testid="stSelectbox"],
[data-testid="stSidebar"] [data-testid="stMultiSelect"] {
    padding: 0 20px;
}
[data-testid="stSidebar"] .stSelectbox > div > div,
[data-testid="stSidebar"] .stMultiSelect > div > div {
    background: #0f1620 !important;
    border: 1px solid #1a2030 !important;
    border-radius: 8px !important;
    color: #c9d1d9 !important;
    font-size: 0.8rem !important;
}

/* Sidebar toggle styling */
[data-testid="stSidebar"] [data-testid="stToggle"] {
    padding: 2px 20px;
}
[data-testid="stSidebar"] [data-testid="stToggle"] label {
    font-size: 0.78rem !important;
    color: #64748b !important;
    font-weight: 500 !important;
}
[data-testid="stSidebar"] [data-testid="stToggle"] p {
    font-size: 0.78rem !important;
    color: #64748b !important;
}

/* ══════════════════════════════════════
   MAIN HEADER
══════════════════════════════════════ */
.dash-header {
    display: flex;
    align-items: baseline;
    gap: 12px;
    margin-bottom: 4px;
}
.dash-title {
    font-size: 1.6rem;
    font-weight: 700;
    color: #f1f5f9;
    letter-spacing: -0.02em;
}
.dash-subtitle {
    font-size: 0.75rem;
    color: #2d3748;
    font-family: 'JetBrains Mono', monospace;
}

/* ══════════════════════════════════════
   TICKER CARDS
══════════════════════════════════════ */
.ticker-card {
    background: #0d1520;
    border: 1px solid #1a2030;
    border-radius: 14px;
    padding: 18px 20px 14px;
    position: relative;
    overflow: hidden;
    transition: border-color 0.2s, transform 0.15s;
}
.ticker-card:hover {
    border-color: #2d3f57;
    transform: translateY(-1px);
}
.ticker-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
}
.ticker-card.up::before   { background: linear-gradient(90deg, #26a641, #3fb950); }
.ticker-card.down::before { background: linear-gradient(90deg, #f85149, #ff7b72); }

.tc-symbol {
    font-size: 0.65rem;
    font-weight: 700;
    letter-spacing: 0.14em;
    color: #4a5568;
    text-transform: uppercase;
    margin-bottom: 6px;
}
.tc-price {
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.55rem;
    font-weight: 600;
    color: #f1f5f9;
    line-height: 1.1;
    margin-bottom: 5px;
}
.tc-change {
    font-size: 0.82rem;
    font-weight: 600;
    margin-bottom: 8px;
}
.tc-change.up   { color: #3fb950; }
.tc-change.down { color: #f85149; }
.tc-meta {
    font-size: 0.67rem;
    color: #2d3748;
    font-family: 'JetBrains Mono', monospace;
    border-top: 1px solid #1a2030;
    padding-top: 8px;
    margin-top: 4px;
}
.tc-meta span { color: #4a5568; }

/* ══════════════════════════════════════
   TABS
══════════════════════════════════════ */
[data-testid="stTabs"] [data-baseweb="tab-list"] {
    background: transparent !important;
    border-bottom: 1px solid #1a2030 !important;
    gap: 0 !important;
    padding: 0 !important;
}
[data-testid="stTabs"] [data-baseweb="tab"] {
    background: transparent !important;
    border: none !important;
    border-bottom: 2px solid transparent !important;
    color: #4a5568 !important;
    font-size: 0.8rem !important;
    font-weight: 500 !important;
    padding: 10px 20px !important;
    border-radius: 0 !important;
    transition: all 0.2s !important;
    letter-spacing: 0.03em;
}
[data-testid="stTabs"] [data-baseweb="tab"]:hover {
    color: #94a3b8 !important;
    border-bottom-color: #2d3748 !important;
}
[data-testid="stTabs"] [aria-selected="true"] {
    color: #58a6ff !important;
    border-bottom-color: #58a6ff !important;
}
[data-testid="stTabs"] [data-baseweb="tab-panel"] {
    padding-top: 20px !important;
}

/* ══════════════════════════════════════
   MISC STREAMLIT OVERRIDES
══════════════════════════════════════ */
[data-testid="stMarkdownContainer"] hr {
    border-color: #1a2030 !important;
    margin: 10px 0 !important;
}
.stAlert { border-radius: 10px !important; font-size: 0.8rem !important; }
[data-testid="stDataFrame"] { border-radius: 10px !important; overflow: hidden; }

/* Download button */
[data-testid="stDownloadButton"] button {
    background: #0f1620 !important;
    border: 1px solid #1a2030 !important;
    color: #58a6ff !important;
    border-radius: 8px !important;
    font-size: 0.78rem !important;
    font-weight: 500 !important;
}
[data-testid="stDownloadButton"] button:hover {
    border-color: #58a6ff !important;
    background: rgba(88,166,255,0.06) !important;
}

/* Caption / timestamp */
[data-testid="stCaptionContainer"] p {
    color: #2d3748 !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.68rem !important;
}
</style>
""", unsafe_allow_html=True)

# ── Auth ──────────────────────────────────────────────────────────────────────
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    login()
    st.stop()

username = st.session_state.get("username", "Trader")
initial  = username[0].upper()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:

    # User badge
    st.markdown(f"""
    <div class="sb-user">
        <div class="sb-avatar">{initial}</div>
        <div>
            <div class="sb-name">{username}</div>
            <div class="sb-role">Trader</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Sector filter
    st.markdown('<div class="sb-label">Sector</div>', unsafe_allow_html=True)
    sector = st.selectbox(
        "sector", ["All Sectors"] + list(SECTORS.keys()),
        label_visibility="collapsed"
    )
    pool = STOCKS if sector == "All Sectors" else SECTORS[sector]

    # Watchlist
    st.markdown('<div class="sb-label">Watchlist</div>', unsafe_allow_html=True)
    selected_stocks = st.multiselect(
        "watchlist", pool, default=pool[:3],
        label_visibility="collapsed"
    )

    # Time range
    st.markdown('<div class="sb-label">Time Range</div>', unsafe_allow_html=True)
    time_label = st.selectbox(
        "timerange", list(TIME_RANGES.keys()),
        label_visibility="collapsed"
    )
    time_cfg = TIME_RANGES[time_label]

    st.markdown('<hr class="sb-div">', unsafe_allow_html=True)

    # Toggles
    st.markdown('<div class="sb-label">Chart Options</div>', unsafe_allow_html=True)
    show_indicators = st.toggle("Technical Indicators", value=True)
    normalise       = st.toggle("Normalise Comparison",  value=False)

    st.markdown('<hr class="sb-div">', unsafe_allow_html=True)

    # Auto refresh
    st.markdown('<div class="sb-label">Live Data</div>', unsafe_allow_html=True)
    auto_refresh = st.toggle("Auto Refresh", value=False)
    if auto_refresh:
        st.markdown(
            f'<div style="padding:2px 20px;font-size:0.68rem;color:#2d3748;'
            f'font-family:JetBrains Mono,monospace;">every {REFRESH_RATE}s</div>',
            unsafe_allow_html=True
        )

    st.markdown('<hr class="sb-div">', unsafe_allow_html=True)

    if st.button("Sign out"):
        st.session_state.logged_in = False
        st.rerun()

# ── Guard ─────────────────────────────────────────────────────────────────────
if not selected_stocks:
    st.warning("Select at least one stock from the sidebar.")
    st.stop()

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="dash-header">
    <div class="dash-title">📈 Market Dashboard</div>
</div>
""", unsafe_allow_html=True)

last_updated = st.empty()

# ── Fetch snapshot ────────────────────────────────────────────────────────────
df_snapshot = get_stock_data(tuple(selected_stocks))

# ── Ticker cards ──────────────────────────────────────────────────────────────
if not df_snapshot.empty:
    max_cols = 6
    chunks   = [df_snapshot.iloc[i:i+max_cols] for i in range(0, len(df_snapshot), max_cols)]

    for chunk in chunks:
        cols = st.columns(len(chunk))
        for col, (_, row) in zip(cols, chunk.iterrows()):
            is_up    = row["Change"] >= 0
            sign     = "+" if is_up else ""
            arrow    = "▲" if is_up else "▼"
            card_cls = "up" if is_up else "down"
            chg_cls  = "up" if is_up else "down"

            vol = row["Volume"]
            if vol >= 1_000_000_000:
                vol_fmt = f"{vol/1_000_000_000:.2f}B"
            elif vol >= 1_000_000:
                vol_fmt = f"{vol/1_000_000:.1f}M"
            elif vol >= 1_000:
                vol_fmt = f"{vol/1_000:.0f}K"
            else:
                vol_fmt = f"{vol:,}"

            with col:
                st.markdown(f"""
                <div class="ticker-card {card_cls}">
                    <div class="tc-symbol">{row['Ticker']}</div>
                    <div class="tc-price">${row['Price']:,.2f}</div>
                    <div class="tc-change {chg_cls}">{arrow} {sign}{row['Change']:.2f} &nbsp;<span style="opacity:.7">({sign}{row['Change %']:.2f}%)</span></div>
                    <div class="tc-meta">
                        <span>H</span> ${row['High']:,.2f} &nbsp;
                        <span>L</span> ${row['Low']:,.2f} &nbsp;
                        <span>V</span> {vol_fmt}
                    </div>
                </div>
                """, unsafe_allow_html=True)

    st.markdown("<div style='margin-top:8px'></div>", unsafe_allow_html=True)

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_compare, tab_candle, tab_heatmap, tab_table = st.tabs([
    "  Comparison  ", "  Candlestick  ", "  Heat Map  ", "  Data Table  "
])

# ── Fetch history ─────────────────────────────────────────────────────────────
histories = {}
for t in selected_stocks:
    raw = get_history(t, time_cfg["period"], time_cfg["interval"])
    if not raw.empty:
        histories[t] = add_technical_indicators(raw) if show_indicators else raw

# ── Tab 1 — Comparison ────────────────────────────────────────────────────────
with tab_compare:
    if histories:
        fig = make_comparison_chart(histories, normalised=normalise)
        st.plotly_chart(fig, use_container_width=True, config={
            "displayModeBar": True,
            "modeBarButtonsToRemove": ["select2d", "lasso2d"],
            "toImageButtonOptions": {"format": "png", "filename": "comparison"},
        })
    else:
        st.warning("No history data available.")

# ── Tab 2 — Candlestick ───────────────────────────────────────────────────────
with tab_candle:
    if selected_stocks:
        detail_ticker = st.selectbox(
            "Ticker", selected_stocks, key="detail_ticker",
            label_visibility="collapsed"
        )
        df_detail = histories.get(detail_ticker)

        if df_detail is not None and not df_detail.empty:
            st.plotly_chart(
                make_candlestick_chart(df_detail, detail_ticker, indicators=show_indicators),
                use_container_width=True,
                config={"displayModeBar": True, "modeBarButtonsToRemove": ["select2d", "lasso2d"]},
            )
            if show_indicators and "RSI" in df_detail.columns:
                st.plotly_chart(
                    make_rsi_chart(df_detail, detail_ticker),
                    use_container_width=True,
                    config={"displayModeBar": False},
                )
        else:
            st.warning(f"No data for {detail_ticker}.")

# ── Tab 3 — Heat Map ──────────────────────────────────────────────────────────
with tab_heatmap:
    if not df_snapshot.empty:
        st.plotly_chart(
            make_heatmap(df_snapshot),
            use_container_width=True,
            config={"displayModeBar": False},
        )
    else:
        st.warning("No snapshot data.")

# ── Tab 4 — Data Table ────────────────────────────────────────────────────────
with tab_table:
    if not df_snapshot.empty:
        display = df_snapshot.copy()
        display["Change %"] = display["Change %"].map(lambda x: f"{x:+.2f}%")
        display["Change"]   = display["Change"].map(lambda x: f"{x:+.2f}")
        display["Volume"]   = display["Volume"].map(lambda x: f"{x:,}")
        st.dataframe(
            display.set_index("Ticker"),
            use_container_width=True,
            height=min(400, 40 + 35 * len(display)),
        )
        csv = df_snapshot.to_csv(index=False)
        st.download_button("⬇ Export CSV", csv, "stocks.csv", "text/csv")
    else:
        st.warning("No data to display.")

# ── Timestamp ─────────────────────────────────────────────────────────────────
last_updated.caption(f"Last updated {time.strftime('%H:%M:%S')}  ·  {time_label}  ·  {len(selected_stocks)} stocks")

# ── Auto-refresh ──────────────────────────────────────────────────────────────
if auto_refresh:
    time.sleep(REFRESH_RATE)
    st.cache_data.clear()
    st.rerun()