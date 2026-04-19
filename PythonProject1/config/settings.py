import random
import colorsys

REFRESH_RATE = 30

SECTORS = {
    "Technology":  [
        "AAPL", "MSFT", "NVDA", "GOOGL", "META", "AMZN", "TSLA", "AMD",  "INTC", "QCOM",
        "AVGO", "TXN",  "MU",   "AMAT",  "KLAC", "LRCX", "SNPS", "CDNS", "MRVL", "NXPI",
        "CRM",  "ORCL", "SAP",  "NOW",   "ADBE", "INTU", "PANW", "CRWD", "ZS",   "FTNT",
        "SHOP", "UBER", "LYFT", "ABNB",  "DASH", "RBLX", "SNAP", "PINS", "SPOT", "NFLX",
    ],
    "Finance":     [
        "JPM", "BAC", "WFC", "GS",   "MS",  "C",   "BLK",  "SCHW", "AXP", "V",
        "MA",  "PYPL","COF", "USB",  "PNC", "TFC", "BK",   "STT",  "MTB", "CFG",
    ],
    "Healthcare":  [
        "JNJ",  "UNH",  "PFE",  "ABBV", "MRK",  "LLY",  "TMO",  "ABT",  "DHR",  "BMY",
        "AMGN", "GILD", "REGN", "VRTX", "BIIB", "ISRG", "SYK",  "BSX",  "MDT",  "ZBH",
    ],
    "Energy":      [
        "XOM", "CVX", "COP", "SLB", "EOG", "PXD", "MPC", "VLO", "PSX", "OXY",
    ],
    "Consumer":    [
        "WMT",  "HD",   "MCD",  "SBUX", "NKE", "TGT", "COST", "LOW", "TJX", "BKNG",
        "PG",   "KO",   "PEP",  "PM",   "MO",  "CL",  "GIS",  "K",   "CPB", "HSY", "UL",
        "UNILEVER.NG",
    ],
    "Industrials": [
        "BA", "CAT", "GE", "HON", "LMT", "RTX", "UPS", "FDX", "DE", "MMM",
    ],
    "Futures":     ["NQ=F", "ES=F", "YM=F", "CL=F", "GC=F", "SI=F"],
    "Crypto":      ["BTC-USD", "ETH-USD"],
    "ETFs":        ["SPY", "QQQ", "DIA", "IWM", "VXX", "GLD", "SLV", "USO"],
}

# Flat list derived from sectors — no duplication
STOCKS: list[str] = [ticker for sector in SECTORS.values() for ticker in sector]


def _generate_color_map(tickers: list[str], seed: int = 42) -> dict[str, str]:
    """
    Distribute tickers evenly around the hue wheel with controlled saturation
    and lightness so every color is vivid and distinct on a dark background.
    A fixed seed keeps colors stable across reruns.
    """
    rng   = random.Random(seed)
    count = len(tickers)

    # Shuffle indices so adjacent tickers in the list aren't adjacent in hue
    indices = list(range(count))
    rng.shuffle(indices)

    color_map: dict[str, str] = {}
    for rank, ticker in enumerate(tickers):
        hue        = indices[rank] / count          # evenly spaced, shuffled
        saturation = rng.uniform(0.65, 0.95)        # always vivid
        lightness  = rng.uniform(0.50, 0.72)        # bright enough on dark bg

        r, g, b = colorsys.hls_to_rgb(hue, lightness, saturation)
        color_map[ticker] = "#{:02x}{:02x}{:02x}".format(
            int(r * 255), int(g * 255), int(b * 255)
        )

    return color_map


color_map: dict[str, str] = _generate_color_map(STOCKS)

TIME_RANGES: dict[str, dict[str, str]] = {
    "1 Day":    {"period": "1d",  "interval": "5m"},
    "1 Week":   {"period": "5d",  "interval": "15m"},
    "2 Weeks":  {"period": "10d", "interval": "30m"},
    "1 Month":  {"period": "1mo", "interval": "1h"},
    "3 Months": {"period": "3mo", "interval": "1d"},
    "6 Months": {"period": "6mo", "interval": "1d"},
    "1 Year":   {"period": "1y",  "interval": "1d"},
    "2 Years":  {"period": "2y",  "interval": "1d"},
    "5 Years":  {"period": "5y",  "interval": "1wk"},
    "7 Years":  {"period": "7y",  "interval": "1wk"},
    "10 Years": {"period": "10y", "interval": "1mo"},
}
