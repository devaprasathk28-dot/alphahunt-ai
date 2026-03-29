import pandas as pd

def calculate_rsi(data, window=14):
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))


def generate_signal(df):
    df["RSI"] = calculate_rsi(df["Close"])

    latest = df.iloc[-1]

    signal = "HOLD"

    if latest["RSI"] < 30:
        signal = "BUY"
    elif latest["RSI"] > 70:
        signal = "SELL"

    return {
        "signal": signal,
        "rsi": float(latest["RSI"])
    }