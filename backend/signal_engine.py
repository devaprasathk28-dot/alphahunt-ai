import pandas as pd

# -----------------------------
# RSI CALCULATION (FIXED)
# -----------------------------
def calculate_rsi(df, window=14):
    if len(df) < window:
        return None

    delta = df["Close"].diff()

    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(window=window).mean()
    avg_loss = loss.rolling(window=window).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    return rsi


# -----------------------------
# SUPPORT & RESISTANCE (NEW)
# -----------------------------
def get_support_resistance(df):
    if len(df) < 20:
        return None, None

    support = df["Low"].rolling(window=20).min().iloc[-1]
    resistance = df["High"].rolling(window=20).max().iloc[-1]

    return support, resistance


# -----------------------------
# SIGNAL GENERATION (FINAL)
# -----------------------------
def generate_signal(df):

    if df is None or df.empty or len(df) < 20:
        return {
            "signal": "HOLD",
            "reason": "Not enough data",
            "confidence": "Low"
        }

    df = df.copy()

    # RSI
    df["RSI"] = calculate_rsi(df)

    latest = df.iloc[-1]

    rsi = latest["RSI"]
    price = latest["Close"]

    # Support / Resistance
    support, resistance = get_support_resistance(df)

    signal = "HOLD"
    reason = "Neutral condition"
    confidence = "Medium"

    # -----------------------------
    # STRONG BUY CONDITIONS
    # -----------------------------
    if rsi is not None:
        if rsi < 30:
            signal = "BUY"
            reason = "Oversold (RSI < 30)"
            confidence = "High"

        elif price > resistance:
            signal = "BUY"
            reason = "Breakout above resistance"
            confidence = "High"

    # -----------------------------
    # STRONG SELL CONDITIONS
    # -----------------------------
    if rsi is not None:
        if rsi > 70:
            signal = "SELL"
            reason = "Overbought (RSI > 70)"
            confidence = "High"

        elif price < support:
            signal = "SELL"
            reason = "Breakdown below support"
            confidence = "High"

    return {
        "signal": signal,
        "reason": reason,
        "confidence": confidence,
        "rsi": float(rsi) if rsi is not None else None,
        "support": float(support) if support else None,
        "resistance": float(resistance) if resistance else None
    }
