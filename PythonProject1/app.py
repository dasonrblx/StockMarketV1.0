import time
import streamlit as st

from config.settings import STOCKS, SECTORS, REFRESH_RATE, TIME_RANGES
from auth.login import login
from data.fetcher import get_stock_data, get_history
from data.processor import add_technical_indicators
from charts.graphs import (
    make_comparison_chart,
    make_candlestick_chart,
    make_rsi_chart,
    make_heatmap,
)

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

/* Hide Streamlit chrome completely */
#MainMenu { visibility: hidden; }
footer    { visibility: hidden; }
header    { visibility: hidden; }

/* Hide Streamlit's own collapse controls — we use our own */
[data-testid="stSidebarCollapseButton"] { display: none !important; }
[data-testid="collapsedControl"]        { display: none !important; }

.block-container { padding: 2rem 2.5rem !important; }

/* ── Sidebar shell ── */
[data-testid="stSidebar"] {
    background: #0b0f14 !important;
    border-right: 1px solid #1a2030 !important;
    transition: transform 0.25s ease !important;
}
[data-testid="stSidebar"] > div:first-child { padding: 0 !important; }

/* ── Custom arrow toggle tab ── */
#sb-toggle {
    position: fixed;
    top: 50%;
    transform: translateY(-50%);
    z-index: 99999;
    width: 18px;
    height: 52px;
    background: #0b0f14;
    border: 1px solid #1a2030;
    border-left: none;
    border-radius: 0 8px 8px 0;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: left 0.25s ease, background 0.15s, border-color 0.15s;
}
#sb-toggle:hover {
    background: #111827;
    border-color: #2d3f57;
}
#sb-toggle svg {
    transition: transform 0.25s ease;
    flex-shrink: 0;
}
/* Arrow flips to point right when sidebar is closed */
#sb-toggle.collapsed svg {
    transform: rotate(180deg);
}

/* ── User badge ── */
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

/* ── Sidebar section labels ── */
.sb-label {
    font-size: 0.62rem; font-weight: 600; letter-spacing: 0.12em;
    text-transform: uppercase; color: #2d3748; padding: 14px 20px 6px;
}
.sb-div { border: none; border-top: 1px solid #1a2030; margin: 10px 0; }

/* ── Sidebar widgets ── */
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

/* ── Sign-out button ── */
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

/* ── Ticker cards ── */
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

/* ── Tabs ── */
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

/* ── Misc overrides ── */
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

# ── Sidebar toggle — arrow tab pinned to the sidebar's right edge ─────────────
st.markdown("""
<div id="sb-toggle" title="Toggle sidebar">
    <svg width="8" height="14" viewBox="0 0 8 14" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M6.5 1L1.5 7L6.5 13" stroke="#4a5568" stroke-width="1.8"
              stroke-linecap="round" stroke-linejoin="round"/>
    </svg>
</div>

<script>
(function () {
    function init() {
        const doc    = window.parent.document;
        const toggle = document.getElementById('sb-toggle');
        if (!toggle) return;

        const sidebar = doc.querySelector('[data-testid="stSidebar"]');
        if (!sidebar) { setTimeout(init, 100); return; }

        let collapsed = false;

        function getWidth() {
            return sidebar.getBoundingClientRect().width || 244;
        }

        function applyState(animate) {
            const w = getWidth();
            sidebar.style.transition = animate ? 'transform 0.25s ease' : 'none';
            toggle.style.transition  = animate
                ? 'left 0.25s ease, background 0.15s, border-color 0.15s'
                : 'background 0.15s, border-color 0.15s';

            if (collapsed) {
                sidebar.style.transform  = 'translateX(-' + w + 'px)';
                sidebar.style.marginRight = '-' + w + 'px';
                toggle.style.left = '0px';
                toggle.classList.add('collapsed');
            } else {
                sidebar.style.transform  = 'translateX(0)';
                sidebar.style.marginRight = '0';
                toggle.style.left = (w - 1) + 'px';
                toggle.classList.remove('collapsed');
            }
        }

        toggle.addEventListener('click', function () {
            collapsed = !collapsed;
            applyState(true);
        });

        // Set initial position without animation
        applyState(false);

        // Keep toggle aligned on resize
        window.addEventListener('resize', function () {
            if (!collapsed) applyState(false);
        });
    }

    if (window.parent && window.parent.document) {
        setTimeout(init, 350);
    }
})();
</script>
""", unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════════════════════
# AUTH
# ═════════════════════════════════════════════════════════════════════════════
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    login()
    st.stop()

username = st.session_state.get("username", "Trader")


# ═════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ═════════════════════════════════════════════════════════════════════════════
with st.sidebar:

    st.markdown(f"""
    <div class="sb-user">
        <div class="sb-avatar">{username[0].upper()}</div>
        <div>
            <div class="sb-name">{username}</div>
            <div class="sb-role">Trader</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="sb-label">Sector</div>', unsafe_allow_html=True)
    sector = st.selectbox("sector", ["All Sectors"] + list(SECTORS.keys()),
                          label_visibility="collapsed")
    pool = STOCKS if sector == "All Sectors" else SECTORS[sector]

    st.markdown('<div class="sb-label">Watchlist</div>', unsafe_allow_html=True)
    selected_stocks = st.multiselect("watchlist", pool, default=pool[:3],
                                     label_visibility="collapsed")

    st.markdown('<div class="sb-label">Time Range</div>', unsafe_allow_html=True)
    time_label = st.selectbox("timerange", list(TIME_RANGES.keys()),
                               label_visibility="collapsed")
    time_cfg = TIME_RANGES[time_label]

    st.markdown('<hr class="sb-div">', unsafe_allow_html=True)

    st.markdown('<div class="sb-label">Chart Options</div>', unsafe_allow_html=True)
    show_indicators = st.toggle("Technical Indicators", value=True)
    normalise       = st.toggle("Normalise Comparison",  value=False)

    st.markdown('<hr class="sb-div">', unsafe_allow_html=True)

    st.markdown('<div class="sb-label">Live Data</div>', unsafe_allow_html=True)
    auto_refresh = st.toggle("Auto Refresh", value=False)
    if auto_refresh:
        st.markdown(
            f'<div style="padding:2px 20px;font-size:0.68rem;color:#2d3748;'
            f'font-family:JetBrains Mono,monospace;">every {REFRESH_RATE}s</div>',
            unsafe_allow_html=True,
        )

    st.markdown('<hr class="sb-div">', unsafe_allow_html=True)

    if st.button("Sign out"):
        st.session_state.logged_in = False
        st.rerun()


# ═════════════════════════════════════════════════════════════════════════════
# GUARD
# ═════════════════════════════════════════════════════════════════════════════
if not selected_stocks:
    st.warning("Select at least one stock from the sidebar.")
    st.stop()


# ═════════════════════════════════════════════════════════════════════════════
# HEADER
# ═════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="dash-title">📈 Market Dashboard</div>', unsafe_allow_html=True)
timestamp_slot = st.empty()


# ═════════════════════════════════════════════════════════════════════════════
# DATA — fetch once, reuse everywhere
# ═════════════════════════════════════════════════════════════════════════════
df_snapshot = get_stock_data(tuple(selected_stocks))

histories: dict = {}
for ticker in selected_stocks:
    raw = get_history(ticker, time_cfg["period"], time_cfg["interval"])
    if raw is not None and not raw.empty:
        histories[ticker] = (
            add_technical_indicators(raw) if show_indicators else raw
        )


# ═════════════════════════════════════════════════════════════════════════════
# TICKER CARDS  (up to 6 per row)
# ═════════════════════════════════════════════════════════════════════════════
def _fmt_volume(v: float) -> str:
    if v >= 1_000_000_000: return f"{v/1_000_000_000:.2f}B"
    if v >= 1_000_000:     return f"{v/1_000_000:.1f}M"
    if v >= 1_000:         return f"{v/1_000:.0f}K"
    return f"{v:,.0f}"

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

st.markdown("<div style='margin-top:10px'></div>", unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════════════════════
# TABS
# ═════════════════════════════════════════════════════════════════════════════
CHART_CFG = {"displayModeBar": True,
             "modeBarButtonsToRemove": ["select2d", "lasso2d"],
             "toImageButtonOptions": {"format": "png"}}

tab_compare, tab_candle, tab_heatmap, tab_table = st.tabs([
    "  Comparison  ", "  Candlestick  ", "  Heat Map  ", "  Data Table  "
])

# ── Comparison ────────────────────────────────────────────────────────────────
with tab_compare:
    if histories:
        st.plotly_chart(
            make_comparison_chart(histories, normalised=normalise),
            use_container_width=True, config=CHART_CFG,
        )
    else:
        st.warning("No history data — try a different time range or stock.")

# ── Candlestick ───────────────────────────────────────────────────────────────
with tab_candle:
    if not histories:
        st.warning("No data available.")
    else:
        pick = st.selectbox("Ticker", list(histories.keys()),
                            key="candle_pick", label_visibility="collapsed")
        df_pick = histories.get(pick)

        if df_pick is not None and not df_pick.empty:
            st.plotly_chart(
                make_candlestick_chart(df_pick, pick, indicators=show_indicators),
                use_container_width=True, config=CHART_CFG,
            )
            if show_indicators and "RSI" in df_pick.columns:
                st.plotly_chart(
                    make_rsi_chart(df_pick, pick),
                    use_container_width=True,
                    config={"displayModeBar": False},
                )
        else:
            st.warning(f"No data for {pick}.")

# ── Heat Map ──────────────────────────────────────────────────────────────────
with tab_heatmap:
    if not df_snapshot.empty:
        st.plotly_chart(
            make_heatmap(df_snapshot),
            use_container_width=True,
            config={"displayModeBar": False},
        )
    else:
        st.warning("No snapshot data available.")

# ── Data Table ────────────────────────────────────────────────────────────────
with tab_table:
    if not df_snapshot.empty:
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
    else:
        st.warning("No data to display.")


# ═════════════════════════════════════════════════════════════════════════════
# TIMESTAMP  +  AUTO-REFRESH
# ═════════════════════════════════════════════════════════════════════════════
timestamp_slot.caption(
    f"Updated {time.strftime('%H:%M:%S')}  ·  {time_label}  ·  {len(selected_stocks)} stocks"
)

if auto_refresh:
    time.sleep(REFRESH_RATE)
    st.cache_data.clear()
    st.rerun()
