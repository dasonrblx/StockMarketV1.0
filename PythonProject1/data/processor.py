import pandas as pd


def add_technical_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Add SMA-20, SMA-50, and Bollinger Bands to an OHLCV DataFrame."""
    if df.empty or "Close" not in df.columns:
        return df

    close = df["Close"].squeeze()

    df = df.copy()
    df["SMA20"] = close.rolling(window=20).mean()
    df["SMA50"] = close.rolling(window=50).mean()

    rolling_std      = close.rolling(window=20).std()
    df["BB_upper"]   = df["SMA20"] + 2 * rolling_std
    df["BB_lower"]   = df["SMA20"] - 2 * rolling_std

    # RSI (14-period)
    delta  = close.diff()
    gain   = delta.clip(lower=0).rolling(14).mean()
    loss   = (-delta.clip(upper=0)).rolling(14).mean()
    rs     = gain / loss.replace(0, float("nan"))
    df["RSI"] = 100 - (100 / (1 + rs))

    return df


def normalise_for_comparison(histories: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Rebase each ticker's Close to 100 at the first data point for % comparison."""
    frames = []
    for ticker, df in histories.items():
        if df.empty or "Close" not in df.columns:
            continue
        close = df["Close"].squeeze()
        rebased = (close / close.iloc[0]) * 100
        rebased.name = ticker
        frames.append(rebased)

    if not frames:
        return pd.DataFrame()

    return pd.concat(frames, axis=1).dropna(how="all")