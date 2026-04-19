import random
import colorsys

REFRESH_RATE = 30

# ═════════════════════════════════════════════════════════════════════════════
# SECTOR DEFINITIONS  (single source of truth — everything derives from this)
# ═════════════════════════════════════════════════════════════════════════════
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


# ═════════════════════════════════════════════════════════════════════════════
# TICKER → FULL NAME  (used for display labels throughout the app)
# ═════════════════════════════════════════════════════════════════════════════
TICKER_NAMES: dict[str, str] = {
    # ── Technology ──
    "AAPL":    "Apple",
    "MSFT":    "Microsoft",
    "NVDA":    "NVIDIA",
    "GOOGL":   "Alphabet",
    "META":    "Meta",
    "AMZN":    "Amazon",
    "TSLA":    "Tesla",
    "AMD":     "AMD",
    "INTC":    "Intel",
    "QCOM":    "Qualcomm",
    "AVGO":    "Broadcom",
    "TXN":     "Texas Instruments",
    "MU":      "Micron",
    "AMAT":    "Applied Materials",
    "KLAC":    "KLA Corp",
    "LRCX":    "Lam Research",
    "SNPS":    "Synopsys",
    "CDNS":    "Cadence",
    "MRVL":    "Marvell",
    "NXPI":    "NXP Semi",
    "CRM":     "Salesforce",
    "ORCL":    "Oracle",
    "SAP":     "SAP",
    "NOW":     "ServiceNow",
    "ADBE":    "Adobe",
    "INTU":    "Intuit",
    "PANW":    "Palo Alto",
    "CRWD":    "CrowdStrike",
    "ZS":      "Zscaler",
    "FTNT":    "Fortinet",
    "SHOP":    "Shopify",
    "UBER":    "Uber",
    "LYFT":    "Lyft",
    "ABNB":    "Airbnb",
    "DASH":    "DoorDash",
    "RBLX":    "Roblox",
    "SNAP":    "Snap",
    "PINS":    "Pinterest",
    "SPOT":    "Spotify",
    "NFLX":    "Netflix",
    # ── Finance ──
    "JPM":     "JPMorgan Chase",
    "BAC":     "Bank of America",
    "WFC":     "Wells Fargo",
    "GS":      "Goldman Sachs",
    "MS":      "Morgan Stanley",
    "C":       "Citigroup",
    "BLK":     "BlackRock",
    "SCHW":    "Charles Schwab",
    "AXP":     "American Express",
    "V":       "Visa",
    "MA":      "Mastercard",
    "PYPL":    "PayPal",
    "COF":     "Capital One",
    "USB":     "US Bancorp",
    "PNC":     "PNC Financial",
    "TFC":     "Truist Financial",
    "BK":      "BNY Mellon",
    "STT":     "State Street",
    "MTB":     "M&T Bank",
    "CFG":     "Citizens Financial",
    # ── Healthcare ──
    "JNJ":     "Johnson & Johnson",
    "UNH":     "UnitedHealth",
    "PFE":     "Pfizer",
    "ABBV":    "AbbVie",
    "MRK":     "Merck",
    "LLY":     "Eli Lilly",
    "TMO":     "Thermo Fisher",
    "ABT":     "Abbott Labs",
    "DHR":     "Danaher",
    "BMY":     "Bristol-Myers",
    "AMGN":    "Amgen",
    "GILD":    "Gilead Sciences",
    "REGN":    "Regeneron",
    "VRTX":    "Vertex Pharma",
    "BIIB":    "Biogen",
    "ISRG":    "Intuitive Surgical",
    "SYK":     "Stryker",
    "BSX":     "Boston Scientific",
    "MDT":     "Medtronic",
    "ZBH":     "Zimmer Biomet",
    # ── Energy ──
    "XOM":     "ExxonMobil",
    "CVX":     "Chevron",
    "COP":     "ConocoPhillips",
    "SLB":     "SLB",
    "EOG":     "EOG Resources",
    "PXD":     "Pioneer Natural",
    "MPC":     "Marathon Petroleum",
    "VLO":     "Valero Energy",
    "PSX":     "Phillips 66",
    "OXY":     "Occidental",
    # ── Consumer ──
    "WMT":     "Walmart",
    "HD":      "Home Depot",
    "MCD":     "McDonald's",
    "SBUX":    "Starbucks",
    "NKE":     "Nike",
    "TGT":     "Target",
    "COST":    "Costco",
    "LOW":     "Lowe's",
    "TJX":     "TJX Companies",
    "BKNG":    "Booking Holdings",
    "PG":      "Procter & Gamble",
    "KO":      "Coca-Cola",
    "PEP":     "PepsiCo",
    "PM":      "Philip Morris",
    "MO":      "Altria",
    "CL":      "Colgate-Palmolive",
    "GIS":     "General Mills",
    "K":       "Kellanova",
    "CPB":     "Campbell Soup",
    "HSY":     "Hershey",
    "UL":      "Unilever",
    # ── Industrials ──
    "BA":      "Boeing",
    "CAT":     "Caterpillar",
    "GE":      "GE Aerospace",
    "HON":     "Honeywell",
    "LMT":     "Lockheed Martin",
    "RTX":     "RTX Corp",
    "UPS":     "UPS",
    "FDX":     "FedEx",
    "DE":      "John Deere",
    "MMM":     "3M",
    # ── Futures ──
    "NQ=F":    "Nasdaq Futures",
    "ES=F":    "S&P 500 Futures",
    "YM=F":    "Dow Futures",
    "CL=F":    "Crude Oil Futures",
    "GC=F":    "Gold Futures",
    "SI=F":    "Silver Futures",
    # ── Crypto ──
    "BTC-USD": "Bitcoin",
    "ETH-USD": "Ethereum",
    # ── ETFs ──
    "SPY":     "S&P 500 ETF",
    "QQQ":     "Nasdaq 100 ETF",
    "DIA":     "Dow Jones ETF",
    "IWM":     "Russell 2000 ETF",
    "VXX":     "VIX ETF",
    "GLD":     "Gold ETF",
    "SLV":     "Silver ETF",
    "USO":     "Oil ETF",
}


# ═════════════════════════════════════════════════════════════════════════════
# COLOR MAP  — generated once per process, visually distinct across all tickers
# ═════════════════════════════════════════════════════════════════════════════
def _generate_color_map(tickers: list[str], seed: int = 42) -> dict[str, str]:
    """
    Distribute tickers evenly around the hue wheel with controlled saturation
    and lightness so every color is vivid and distinct on a dark background.
    A fixed seed keeps colors stable across reruns.
    """
    rng   = random.Random(seed)
    count = len(tickers)

    indices = list(range(count))
    rng.shuffle(indices)

    color_map: dict[str, str] = {}
    for rank, ticker in enumerate(tickers):
        hue        = indices[rank] / count
        saturation = rng.uniform(0.65, 0.95)
        lightness  = rng.uniform(0.50, 0.72)

        r, g, b = colorsys.hls_to_rgb(hue, lightness, saturation)
        color_map[ticker] = "#{:02x}{:02x}{:02x}".format(
            int(r * 255), int(g * 255), int(b * 255)
        )

    return color_map


color_map: dict[str, str] = _generate_color_map(STOCKS)


# ═════════════════════════════════════════════════════════════════════════════
# TIME RANGES  (yfinance-valid period / interval combos only)
# ═════════════════════════════════════════════════════════════════════════════
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
