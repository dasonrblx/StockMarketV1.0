import time
import streamlit as st

from config.settings import STOCKS, REFRESH_RATE, TIME_RANGES
from auth.login import login
from data.fetcher import get_stock_data, get_history
from data.processor import add_technical_indicators, normalise_for_comparison
from charts.graphs import (
    make_comparison_chart,
    make_candlestick_chart,
    make_volume_chart,
    make_rsi_chart,
    make_heatmap,
)

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Stock Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&display=swap');

html, body, [class*="css"] { font-family: 'JetBrains Mono', monospace; }

.metric-card {
    background: linear-gradient(135deg, #0d1117 0%, #161b22 100%);
    border: 1px solid #21262d;
    border-radius: 10px;
    padding: 16px 20px;
    margin-bottom: 10px;
}
.metric-card .ticker  { font-size: 0.75rem; color: #8b949e; letter-spacing: 2px; }
.metric-card .price   { font-size: 1.6rem; font-weight: 700; color: #f0f6fc; }
.metric-card .change  { font-size: 0.9rem; font-weight: 600; }
.metric-card .meta    { font-size: 0.7rem; color: #8b949e; margin-top: 6px; }
.positive { color: #00ff88; }
.negative { color: #ff3b30; }

[data-testid="stSidebar"] { background: #0d1117; border-right: 1px solid #21262d; }
</style>
""", unsafe_allow_html=True)

# ── Auth ──────────────────────────────────────────────────────────────────────
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    login()
    st.stop()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"### 👋 {st.session_state.get('username', 'Trader')}")
    st.divider()

    selected_stocks = st.multiselect(
        "📌 Watchlist", STOCKS, default=STOCKS[:3]
    )

    time_label = st.selectbox("🕐 Time Range", list(TIME_RANGES.keys()), index=0)
    time_cfg   = TIME_RANGES[time_label]

    show_indicators = st.toggle("📐 Technical Indicators", value=True)
    normalise       = st.toggle("⚖️ Normalise for Comparison", value=False)

    st.divider()
    auto_refresh = st.toggle("🔄 Auto Refresh", value=False)
    if auto_refresh:
        st.caption(f"Refreshing every {REFRESH_RATE}s")

    st.divider()
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.logged_in = False
        st.rerun()

if not selected_stocks:
    st.warning("Select at least one stock from the sidebar.")
    st.stop()

# ── Header ────────────────────────────────────────────────────────────────────
st.title("📊 Live Stock Dashboard")
last_updated = st.empty()

# ── Fetch snapshot data ───────────────────────────────────────────────────────
df_snapshot = get_stock_data(tuple(selected_stocks))

# ── Ticker cards ──────────────────────────────────────────────────────────────
if not df_snapshot.empty:
    cols = st.columns(len(df_snapshot))
    for col, (_, row) in zip(cols, df_snapshot.iterrows()):
        sign       = "+" if row["Change"] >= 0 else ""
        cls        = "positive" if row["Change"] >= 0 else "negative"
        arrow      = "▲" if row["Change"] >= 0 else "▼"
        vol_fmt    = f"{row['Volume']:,}" if row['Volume'] < 1_000_000 else f"{row['Volume']/1_000_000:.1f}M"
        with col:
            st.markdown(f"""
            <div class="metric-card">
                <div class="ticker">{row['Ticker']}</div>
                <div class="price">${row['Price']:,.2f}</div>
                <div class="change {cls}">{arrow} {sign}{row['Change']:.2f} ({sign}{row['Change %']:.2f}%)</div>
                <div class="meta">H: ${row['High']:,.2f} &nbsp;|&nbsp; L: ${row['Low']:,.2f} &nbsp;|&nbsp; Vol: {vol_fmt}</div>
            </div>
            """, unsafe_allow_html=True)

st.divider()

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_compare, tab_detail, tab_heatmap, tab_table = st.tabs([
    "📈 Comparison", "🕯️ Detail / Candlestick", "🌡️ Heat Map", "📋 Data Table"
])

# ── Fetch history for all selected stocks ─────────────────────────────────────
histories = {}
for t in selected_stocks:
    raw = get_history(t, time_cfg["period"], time_cfg["interval"])
    if not raw.empty:
        histories[t] = add_technical_indicators(raw) if show_indicators else raw

# ── Tab 1 — Comparison ────────────────────────────────────────────────────────
with tab_compare:
    if histories:
        fig = make_comparison_chart(histories, normalised=normalise)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No history data available for selected stocks.")

# ── Tab 2 — Detail / Candlestick ─────────────────────────────────────────────
with tab_detail:
    detail_ticker = st.selectbox(
        "Select Ticker", selected_stocks, key="detail_ticker"
    )
    df_detail = histories.get(detail_ticker, None)

    if df_detail is not None and not df_detail.empty:
        st.plotly_chart(
            make_candlestick_chart(df_detail, detail_ticker, indicators=show_indicators),
            use_container_width=True
        )

        c1, c2 = st.columns(2)
        with c1:
            st.plotly_chart(make_volume_chart(df_detail, detail_ticker), use_container_width=True)
        with c2:
            if show_indicators and "RSI" in df_detail.columns:
                st.plotly_chart(make_rsi_chart(df_detail, detail_ticker), use_container_width=True)
            else:
                st.info("Enable Technical Indicators to see RSI.")
    else:
        st.warning(f"No data for {detail_ticker}.")

# ── Tab 3 — Heat Map ──────────────────────────────────────────────────────────
with tab_heatmap:
    if not df_snapshot.empty:
        st.plotly_chart(make_heatmap(df_snapshot), use_container_width=True)
    else:
        st.warning("No snapshot data for heatmap.")

# ── Tab 4 — Data Table ────────────────────────────────────────────────────────
with tab_table:
    if not df_snapshot.empty:
        display = df_snapshot.copy()
        display["Change %"] = display["Change %"].map(lambda x: f"{x:+.2f}%")
        display["Change"]   = display["Change"].map(lambda x: f"{x:+.2f}")
        display["Volume"]   = display["Volume"].map(lambda x: f"{x:,}")
        st.dataframe(display.set_index("Ticker"), use_container_width=True)

        csv = df_snapshot.to_csv(index=False)
        st.download_button("⬇️ Download CSV", csv, "stocks.csv", "text/csv")
    else:
        st.warning("No data to display.")

# ── Timestamp + Auto-refresh ──────────────────────────────────────────────────
last_updated.caption(f"Last updated: {time.strftime('%H:%M:%S')}")

if auto_refresh:
    time.sleep(REFRESH_RATE)
    st.cache_data.clear()
    st.rerun()