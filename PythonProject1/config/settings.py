STOCKS = ["NVDA", "AAPL", "TSLA", "MSFT", "AMZN", "NQ=F"]
REFRESH_RATE = 30

color_map = {
    "NVDA": "#00ff88",
    "AAPL": "#ff3b30",
    "TSLA": "#ffcc00",
    "MSFT": "#4da3ff",
    "AMZN": "#ff9900",
    "NQ=F": "#cc88ff"
}

TIME_RANGES = {
    "1 Day":   {"period": "1d",  "interval": "5m"},
    "5 Days":  {"period": "5d",  "interval": "15m"},
    "1 Month": {"period": "1mo", "interval": "1h"},
    "3 Months":{"period": "3mo", "interval": "1d"},
    "6 Months":{"period": "6mo", "interval": "1d"},
    "1 Year":  {"period": "1y",  "interval": "1wk"},
}