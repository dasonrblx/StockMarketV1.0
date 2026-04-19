import time
import streamlit as st

# ── DEBUG HELPER ─────────────────────────────────────────────────────────────
import traceback

def dbg(label: str, value=None, level: str = "info"):
    """Emit a coloured debug line in the Streamlit UI."""
    colors = {"info": "#58a6ff", "ok": "#3fb950", "warn": "#d29922", "err": "#f85149"}
    icon   = {"info": "ℹ️", "ok": "✅", "warn": "⚠️", "err": "❌"}
    color  = colors.get(level, "#ccc")
    ic     = icon.get(level, "•")
    msg    = f"{ic} **[DEBUG] {label}**"
    if value is not None:
        msg += f"  →  `{value}`"
    st.markdown(
        f'<div style="font-size:0.72rem;color:{color};'
        f'font-family:JetBrains Mono,monospace;padding:2px 0">{msg}</div>',
        unsafe_allow_html=True,
    )

# ─────────────────────────────────────────────────────────────────────────────

try:
    from config.settings import STOCKS, SECTORS, REFRESH_RATE, TIME_RANGES
    # Verify the imports look sane
    assert isinstance(STOCKS, list),       "STOCKS is not a list"
    assert isinstance(SECTORS, dict),      "SECTORS is not a dict"
    assert isinstance(TIME_RANGES, dict),  "TIME_RANGES is not a dict"
    assert isinstance(REFRESH_RATE, int),  "REFRESH_RATE is not an int"
except Exception as e:
    st.error(f"❌ **config.settings import failed:** `{e}`")
    st.code(traceback.format_exc())
    st.stop()

try:
    from auth.login import login
except Exception as e:
    st.error(f"❌ **auth.login import failed:** `{e}`")
    st.code(traceback.format_exc())
    st.stop()

try:
    from data.fetcher import get_stock_data, get_history
except Exception as e:
    st.error(f"❌ **data.fetcher import failed:** `{e}`")
    st.code(traceback.format_exc())
    st.stop()

try:
    from data.processor import add_technical_indicators
except Exception as e:
    st.error(f"❌ **data.processor import failed:** `{e}`")
    st.code(traceback.format_exc())
    st.stop()

try:
    from charts.graphs import (
        make_comparison_chart,
        make_candlestick_chart,
        make_rsi_chart,
        make_heatmap,
    )
except Exception as e:
    st.error(f"❌ **charts.graphs import failed:** `{e}`")
    st.code(traceback.format_exc())
    st.stop()

# ═════════════════════════════════════════════════════════════════════════════
# PAGE CONFIG
# ═════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="StockMarket",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ═════════════════════════════════════════════════════════════════════════════
# CSS
# ═════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #080c10; }

#MainMenu { visibility: hidden; }
footer    { visibility: hidden; }
header    { visibility: hidden; }

[data-testid="stSidebarCollapseButton"] { display: none !important; }
[data-testid="collapsedControl"]        { display: none !important; }

.block-container { padding: 2rem 2.5rem !important; }

[data-testid="stSidebar"] {
    background: #0b0f14 !important;
    border-right: 1px solid #1a2030 !important;
}
[data-testid="stSidebar"] > div:first-child { padding: 0 !important; }

.sb-user {
    display: flex; align-items: center; gap: 10px;
    padding: 22px 20px 18px; border-bottom: 1px solid #1a2030; margin-bottom: 6px;
}
.sb-avatar {
    width: 36px; height: 36px; border-radius: 50%;
    background: linear-gradient(135deg, #3b82f6, #8b5cf6);
    display: flex; align-items: center; justify-content: center;
    font-size: 15px; font-weight: 700; color: #fff; flex-shrink: 0;
}
.sb-name { font-size: 0.85rem; font-weight: 600; color: #e2e8f0; }
.sb-role { font-size: 0.68rem; color: #4a5568; letter-spacing: 0.05em; text-transform: uppercase; }

.sb-label {
    font-size: 0.62rem; font-weight: 600; letter-spacing: 0.12em;
    text-transform: uppercase; color: #2d3748; padding: 14px 20px 6px;
}
.sb-div { border: none; border-top: 1px solid #1a2030; margin: 10px 0; }

[data-testid="stSidebar"] [data-testid="stSelectbox"],
[data-testid="stSidebar"] [data-testid="stMultiSelect"] { padding: 0 20px; }

[data-testid="stSidebar"] .stSelectbox > div > div,
[data-testid="stSidebar"] .stMultiSelect > div > div {
    background: #0f1620 !important; border: 1px solid #1a2030 !important;
    border-radius: 8px !important; color: #c9d1d9 !important; font-size: 0.8rem !important;
}
[data-testid="stSidebar"] [data-testid="stToggle"] { padding: 2px 20px; }
[data-testid="stSidebar"] [data-testid="stToggle"] label,
[data-testid="stSidebar"] [data-testid="stToggle"] p {
    font-size: 0.78rem !important; color: #64748b !important; font-weight: 500 !important;
}

[data-testid="stSidebar"] [data-testid="stButton"] button {
    background: transparent !important; border: 1px solid #1e2d3d !important;
    color: #4a5568 !important; border-radius: 8px !important;
    font-size: 0.75rem !important; font-weight: 500 !important;
    width: calc(100% - 40px) !important; margin: 8px 20px !important;
    transition: all 0.2s !important;
}
[data-testid="stSidebar"] [data-testid="stButton"] button:hover {
    border-color: #f85149 !important; color: #f85149 !important;
    background: rgba(248,81,73,0.06) !important;
}

.ticker-card {
    background: #0d1520; border: 1px solid #1a2030; border-radius: 14px;
    padding: 18px 20px 14px; position: relative; overflow: hidden;
    transition: border-color 0.2s, transform 0.15s;
}
.ticker-card:hover { border-color: #2d3f57; transform: translateY(-1px); }
.ticker-card::before {
    content: ''; position: absolute; top: 0; left: 0; right: 0; height: 2px;
}
.ticker-card.up::before   { background: linear-gradient(90deg, #26a641, #3fb950); }
.ticker-card.down::before { background: linear-gradient(90deg, #f85149, #ff7b72); }

.tc-symbol {
    font-size: 0.65rem; font-weight: 700; letter-spacing: 0.14em;
    color: #4a5568; text-transform: uppercase; margin-bottom: 6px;
}
.tc-price {
    font-family: 'JetBrains Mono', monospace; font-size: 1.55rem;
    font-weight: 600; color: #f1f5f9; line-height: 1.1; margin-bottom: 5px;
}
.tc-change { font-size: 0.82rem; font-weight: 600; margin-bottom: 8px; }
.tc-change.up   { color: #3fb950; }
.tc-change.down { color: #f85149; }
.tc-meta {
    font-size: 0.67rem; color: #2d3748;
    font-family: 'JetBrains Mono', monospace;
    border-top: 1px solid #1a2030; padding-top: 8px; margin-top: 4px;
}
.tc-meta span { color: #4a5568; }

[data-testid="stTabs"] [data-baseweb="tab-list"] {
    background: transparent !important; border-bottom: 1px solid #1a2030 !important;
    gap: 0 !important; padding: 0 !important;
}
[data-testid="stTabs"] [data-baseweb="tab"] {
    background: transparent !important; border: none !important;
    border-bottom: 2px solid transparent !important; color: #4a5568 !important;
    font-size: 0.8rem !important; font-weight: 500 !important;
    padding: 10px 20px !important; border-radius: 0 !important;
    transition: all 0.2s !important; letter-spacing: 0.03em;
}
[data-testid="stTabs"] [data-baseweb="tab"]:hover {
    color: #94a3b8 !important; border-bottom-color: #2d3748 !important;
}
[data-testid="stTabs"] [aria-selected="true"] {
    color: #58a6ff !important; border-bottom-color: #58a6ff !important;
}
[data-testid="stTabs"] [data-baseweb="tab-panel"] { padding-top: 20px !important; }

.stAlert { border-radius: 10px !important; font-size: 0.8rem !important; }
[data-testid="stDataFrame"] { border-radius: 10px !important; overflow: hidden; }
[data-testid="stMarkdownContainer"] hr { border-color: #1a2030 !important; margin: 10px 0 !important; }
[data-testid="stDownloadButton"] button {
    background: #0f1620 !important; border: 1px solid #1a2030 !important;
    color: #58a6ff !important; border-radius: 8px !important;
    font-size: 0.78rem !important; font-weight: 500 !important;
}
[data-testid="stDownloadButton"] button:hover {
    border-color: #58a6ff !important; background: rgba(88,166,255,0.06) !important;
}
[data-testid="stCaptionContainer"] p {
    color: #2d3748 !important; font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.68rem !important;
}
</style>
""", unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════════════════════
# AUTH
# ═════════════════════════════════════════════════════════════════════════════
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

dbg("session_state.logged_in", st.session_state.logged_in)

if not st.session_state.logged_in:
    dbg("Auth gate reached — calling login()", level="warn")
    try:
        login()
    except Exception as e:
        st.error(f"❌ **login() raised an exception:** `{e}`")
        st.code(traceback.format_exc())
    st.stop()

username = st.session_state.get("username", "Trader")
dbg("username resolved", username, level="ok")


# ═════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ═════════════════════════════════════════════════════════════════════════════
with st.sidebar:

    # ── 1. Avatar/user badge ──────────────────────────────────────────────────
    dbg("Rendering user badge", username)
    try:
        st.markdown(f"""
        <div class="sb-user">
            <div class="sb-avatar">{username[0].upper()}</div>
            <div>
                <div class="sb-name">{username}</div>
                <div class="sb-role">Trader</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        dbg("User badge rendered", level="ok")
    except Exception as e:
        dbg(f"User badge FAILED: {e}", level="err")

    # ── 2. Sector selectbox ───────────────────────────────────────────────────
    dbg("SECTORS keys", list(SECTORS.keys()))
    st.markdown('<div class="sb-label">Sector</div>', unsafe_allow_html=True)
    try:
        sector = st.selectbox(
            "sector",
            ["All Sectors"] + list(SECTORS.keys()),
            label_visibility="collapsed",
        )
        dbg("sector selected", sector, level="ok")
    except Exception as e:
        dbg(f"Sector selectbox FAILED: {e}", level="err")
        st.code(traceback.format_exc())
        sector = "All Sectors"

    pool = STOCKS if sector == "All Sectors" else SECTORS[sector]
    dbg("pool size", len(pool))

    # ── 3. Watchlist multiselect ──────────────────────────────────────────────
    st.markdown('<div class="sb-label">Watchlist</div>', unsafe_allow_html=True)
    dbg("pool[:3] default", pool[:3])
    try:
        selected_stocks = st.multiselect(
            "watchlist",
            pool,
            default=pool[:3],
            label_visibility="collapsed",
        )
        dbg("selected_stocks", selected_stocks, level="ok")
    except Exception as e:
        dbg(f"Watchlist multiselect FAILED: {e}", level="err")
        st.code(traceback.format_exc())
        selected_stocks = pool[:3]

    # ── 4. Time range ─────────────────────────────────────────────────────────
    st.markdown('<div class="sb-label">Time Range</div>', unsafe_allow_html=True)
    dbg("TIME_RANGES keys", list(TIME_RANGES.keys()))
    try:
        time_label = st.selectbox(
            "timerange",
            list(TIME_RANGES.keys()),
            label_visibility="collapsed",
        )
        time_cfg = TIME_RANGES[time_label]
        dbg("time_label", time_label, level="ok")
        dbg("time_cfg", time_cfg)
    except Exception as e:
        dbg(f"Time range selectbox FAILED: {e}", level="err")
        st.code(traceback.format_exc())
        time_label = list(TIME_RANGES.keys())[0]
        time_cfg   = TIME_RANGES[time_label]

    st.markdown('<hr class="sb-div">', unsafe_allow_html=True)

    # ── 5. Chart options ──────────────────────────────────────────────────────
    st.markdown('<div class="sb-label">Chart Options</div>', unsafe_allow_html=True)
    try:
        show_indicators = st.toggle("Technical Indicators", value=True)
        normalise       = st.toggle("Normalise Comparison",  value=False)
        dbg("show_indicators", show_indicators, level="ok")
        dbg("normalise",       normalise,       level="ok")
    except Exception as e:
        dbg(f"Chart option toggles FAILED: {e}", level="err")
        st.code(traceback.format_exc())
        show_indicators = True
        normalise       = False

    st.markdown('<hr class="sb-div">', unsafe_allow_html=True)

    # ── 6. Live data / auto-refresh ───────────────────────────────────────────
    st.markdown('<div class="sb-label">Live Data</div>', unsafe_allow_html=True)
    try:
        auto_refresh = st.toggle("Auto Refresh", value=False)
        dbg("auto_refresh", auto_refresh, level="ok")
    except Exception as e:
        dbg(f"Auto refresh toggle FAILED: {e}", level="err")
        auto_refresh = False

    if auto_refresh:
        st.markdown(
            f'<div style="padding:2px 20px;font-size:0.68rem;color:#2d3748;'
            f'font-family:JetBrains Mono,monospace;">every {REFRESH_RATE}s</div>',
            unsafe_allow_html=True,
        )

    st.markdown('<hr class="sb-div">', unsafe_allow_html=True)

    # ── 7. Sign-out ───────────────────────────────────────────────────────────
    try:
        if st.button("Sign out"):
            dbg("Sign out clicked — clearing session", level="warn")
            st.session_state.logged_in = False
            st.rerun()
    except Exception as e:
        dbg(f"Sign-out button FAILED: {e}", level="err")

dbg("Sidebar block exited cleanly", level="ok")


# ═════════════════════════════════════════════════════════════════════════════
# GUARD
# ═════════════════════════════════════════════════════════════════════════════
if not selected_stocks:
    st.warning("Select at least one stock from the sidebar.")
    dbg("No stocks selected — stopped", level="warn")
    st.stop()

dbg(f"Proceeding with {len(selected_stocks)} stocks", selected_stocks)


# ═════════════════════════════════════════════════════════════════════════════
# HEADER
# ═════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="dash-title">📈 Market Dashboard</div>', unsafe_allow_html=True)
timestamp_slot = st.empty()


# ═════════════════════════════════════════════════════════════════════════════
# DATA FETCH
# ═════════════════════════════════════════════════════════════════════════════
dbg("Calling get_stock_data()", selected_stocks)
try:
    df_snapshot = get_stock_data(tuple(selected_stocks))
    dbg("get_stock_data() returned", f"shape={df_snapshot.shape}", level="ok")
    dbg("df_snapshot columns", list(df_snapshot.columns))
    if df_snapshot.empty:
        dbg("df_snapshot is EMPTY", level="warn")
except Exception as e:
    dbg(f"get_stock_data() FAILED: {e}", level="err")
    st.code(traceback.format_exc())
    st.stop()

histories: dict = {}
for ticker in selected_stocks:
    dbg(f"Fetching history for {ticker}", f"period={time_cfg['period']} interval={time_cfg['interval']}")
    try:
        raw = get_history(ticker, time_cfg["period"], time_cfg["interval"])
        if raw is None:
            dbg(f"{ticker}: get_history() returned None", level="warn")
            continue
        if raw.empty:
            dbg(f"{ticker}: history DataFrame is empty", level="warn")
            continue
        dbg(f"{ticker}: raw history shape", raw.shape, level="ok")
        if show_indicators:
            try:
                processed = add_technical_indicators(raw)
                dbg(f"{ticker}: indicators added, cols={list(processed.columns)}", level="ok")
                histories[ticker] = processed
            except Exception as e:
                dbg(f"{ticker}: add_technical_indicators() FAILED: {e}", level="err")
                st.code(traceback.format_exc())
                histories[ticker] = raw          # fall back to raw
        else:
            histories[ticker] = raw
    except Exception as e:
        dbg(f"{ticker}: get_history() FAILED: {e}", level="err")
        st.code(traceback.format_exc())

dbg("histories populated", list(histories.keys()), level="ok")


# ═════════════════════════════════════════════════════════════════════════════
# TICKER CARDS
# ═════════════════════════════════════════════════════════════════════════════
def _fmt_volume(v: float) -> str:
    if v >= 1_000_000_000: return f"{v/1_000_000_000:.2f}B"
    if v >= 1_000_000:     return f"{v/1_000_000:.1f}M"
    if v >= 1_000:         return f"{v/1_000:.0f}K"
    return f"{v:,.0f}"

dbg("Rendering ticker cards", f"{len(df_snapshot)} rows")

# Verify required columns exist before rendering cards
REQUIRED_COLS = {"Ticker", "Price", "Change", "Change %", "High", "Low", "Volume"}
missing = REQUIRED_COLS - set(df_snapshot.columns)
if missing:
    dbg(f"df_snapshot missing columns: {missing}", level="err")
    st.error(f"Snapshot DataFrame is missing columns: `{missing}`")
else:
    if not df_snapshot.empty:
        for chunk_start in range(0, len(df_snapshot), 6):
            chunk = df_snapshot.iloc[chunk_start : chunk_start + 6]
            cols  = st.columns(len(chunk))
            for col, (_, row) in zip(cols, chunk.iterrows()):
                up   = row["Change"] >= 0
                sign = "+" if up else ""
                with col:
                    st.markdown(f"""
                    <div class="ticker-card {'up' if up else 'down'}">
                        <div class="tc-symbol">{row['Ticker']}</div>
                        <div class="tc-price">${row['Price']:,.2f}</div>
                        <div class="tc-change {'up' if up else 'down'}">
                            {'▲' if up else '▼'} {sign}{row['Change']:.2f}
                            <span style="opacity:.7">({sign}{row['Change %']:.2f}%)</span>
                        </div>
                        <div class="tc-meta">
                            <span>H</span> ${row['High']:,.2f} &nbsp;
                            <span>L</span> ${row['Low']:,.2f} &nbsp;
                            <span>V</span> {_fmt_volume(row['Volume'])}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
        dbg("Ticker cards rendered", level="ok")

st.markdown("<div style='margin-top:10px'></div>", unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════════════════════
# TABS
# ═════════════════════════════════════════════════════════════════════════════
CHART_CFG = {
    "displayModeBar": True,
    "modeBarButtonsToRemove": ["select2d", "lasso2d"],
    "toImageButtonOptions": {"format": "png"},
}

tab_compare, tab_candle, tab_heatmap, tab_table = st.tabs([
    "  Comparison  ", "  Candlestick  ", "  Heat Map  ", "  Data Table  "
])

# ── Comparison ────────────────────────────────────────────────────────────────
with tab_compare:
    dbg("Rendering Comparison tab", f"histories={list(histories.keys())}")
    if histories:
        try:
            fig = make_comparison_chart(histories, normalised=normalise)
            st.plotly_chart(fig, use_container_width=True, config=CHART_CFG)
            dbg("Comparison chart rendered", level="ok")
        except Exception as e:
            dbg(f"make_comparison_chart() FAILED: {e}", level="err")
            st.code(traceback.format_exc())
    else:
        st.warning("No history data — try a different time range or stock.")

# ── Candlestick ───────────────────────────────────────────────────────────────
with tab_candle:
    dbg("Rendering Candlestick tab")
    if not histories:
        st.warning("No data available.")
    else:
        pick = st.selectbox("Ticker", list(histories.keys()),
                            key="candle_pick", label_visibility="collapsed")
        dbg("candle pick", pick)
        df_pick = histories.get(pick)

        if df_pick is not None and not df_pick.empty:
            try:
                fig = make_candlestick_chart(df_pick, pick, indicators=show_indicators)
                st.plotly_chart(fig, use_container_width=True, config=CHART_CFG)
                dbg(f"Candlestick chart for {pick} rendered", level="ok")
            except Exception as e:
                dbg(f"make_candlestick_chart() FAILED: {e}", level="err")
                st.code(traceback.format_exc())

            if show_indicators and "RSI" in df_pick.columns:
                try:
                    st.plotly_chart(
                        make_rsi_chart(df_pick, pick),
                        use_container_width=True,
                        config={"displayModeBar": False},
                    )
                    dbg("RSI chart rendered", level="ok")
                except Exception as e:
                    dbg(f"make_rsi_chart() FAILED: {e}", level="err")
                    st.code(traceback.format_exc())
            elif show_indicators:
                dbg(f"RSI column not found in df_pick for {pick}", level="warn")
        else:
            st.warning(f"No data for {pick}.")

# ── Heat Map ──────────────────────────────────────────────────────────────────
with tab_heatmap:
    dbg("Rendering Heat Map tab")
    if not df_snapshot.empty:
        try:
            fig = make_heatmap(df_snapshot)
            st.plotly_chart(fig, use_container_width=True,
                            config={"displayModeBar": False})
            dbg("Heatmap rendered", level="ok")
        except Exception as e:
            dbg(f"make_heatmap() FAILED: {e}", level="err")
            st.code(traceback.format_exc())
    else:
        st.warning("No snapshot data available.")

# ── Data Table ────────────────────────────────────────────────────────────────
with tab_table:
    dbg("Rendering Data Table tab")
    if not df_snapshot.empty:
        try:
            display = df_snapshot.copy()
            display["Change %"] = display["Change %"].map(lambda x: f"{x:+.2f}%")
            display["Change"]   = display["Change"].map(lambda x: f"{x:+.2f}")
            display["Volume"]   = display["Volume"].map(lambda x: f"{x:,}")
            st.dataframe(
                display.set_index("Ticker"),
                use_container_width=True,
                height=min(420, 45 + 38 * len(display)),
            )
            st.download_button(
                "⬇ Export CSV",
                df_snapshot.to_csv(index=False),
                file_name="stocks.csv",
                mime="text/csv",
            )
            dbg("Data table rendered", level="ok")
        except Exception as e:
            dbg(f"Data table FAILED: {e}", level="err")
            st.code(traceback.format_exc())
    else:
        st.warning("No data to display.")


# ═════════════════════════════════════════════════════════════════════════════
# TIMESTAMP  +  AUTO-REFRESH
# ═════════════════════════════════════════════════════════════════════════════
timestamp_slot.caption(
    f"Updated {time.strftime('%H:%M:%S')}  ·  {time_label}  ·  {len(selected_stocks)} stocks"
)

if auto_refresh:
    dbg(f"Auto-refresh sleeping {REFRESH_RATE}s then rerunning", level="warn")
    time.sleep(REFRESH_RATE)
    st.cache_data.clear()
    st.rerun()

dbg("Full render cycle complete", level="ok")
