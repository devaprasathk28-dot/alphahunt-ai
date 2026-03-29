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
# NEW FUNCTIONS FOR FIXES
# -----------------------------

def market_status(ticker):
    """Global market status - India/US"""
    from datetime import datetime
    now = datetime.utcnow()
    
    if ".NS" in ticker:
        # India NSE: 3:30-10:00 UTC (9:00-15:30 IST)
        return "OPEN" if 3 <= now.hour < 10 else "CLOSED"
    else:
        # US: 14:30-21:00 UTC (9:30-16:00 EST)
        return "OPEN" if 14 <= now.hour < 21 else "CLOSED"

def role_reversal(price, support, resistance):
    """Advanced role reversal detection"""
    if price > resistance:
        return "Resistance → Support"
    elif price < support:
        return "Support → Resistance"
    return "No role reversal"


# -----------------------------
# SUPPORT & RESISTANCE 
# -----------------------------
def support_resistance(df):
    """Alias for UI usage"""
    return get_support_resistance(df)

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
    if df is None or df.empty or len(df) < 50:
        return {
            "signal": "HOLD",
            "reason": "Not enough data",
            "confidence": "Low"
        }

    df = df.copy()

    # Calculate indicators
    df["RSI"] = calculate_rsi(df)
    df["MA20"] = df["Close"].rolling(20).mean()
    df["MA50"] = df["Close"].rolling(50).mean()
    support, resistance = get_support_resistance(df)

    latest = df.iloc[-1]
    price = latest["Close"]
    ma20 = latest["MA20"]
    ma50 = latest["MA50"]
    rsi = latest["RSI"]

    signal = "HOLD"
    reason = "Neutral conditions"
    confidence = "Medium"

    # Improved MA-based signals (fixes 0 signals issue)
    if price > ma20 and ma20 > ma50:
        signal = "BUY"
        reason = "Bullish trend (Price > MA20 > MA50)"
        confidence = "High"
    elif price < ma20 and ma20 < ma50:
        signal = "SELL"
        reason = "Bearish trend (Price < MA20 < MA50)"
        confidence = "High"
    elif rsi < 30:
        signal = "BUY"
        reason = "Oversold RSI"
        confidence = "Medium"
    elif rsi > 70:
        signal = "SELL"
        reason = "Overbought RSI"
        confidence = "Medium"

    return {
        "signal": signal,
        "reason": reason,
        "confidence": confidence,
        "rsi": float(rsi) if rsi is not None else None,
        "support": float(support) if support else None,
        "resistance": float(resistance) if resistance else None,
        "ma20": float(ma20),
        "ma50": float(ma50)
    }
