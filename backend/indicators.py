import pandas as pd
import numpy as np

def calculate_rsi(df, window=14):
    df = df.copy()
    delta = df['Close'].diff()

    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()

    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))

    df.loc[:, 'RSI'] = rsi
    return df

def detect_breakout(df, window=10):
    df = df.copy()
    df.loc[:, 'Resistance'] = df['Close'].rolling(window=window).max()
    df.loc[:, 'Support'] = df['Close'].rolling(window=window).min()

    latest = df.iloc[-1]

    breakout = False
    breakdown = False

    if latest['Close'] > latest['Resistance']:
        breakout = True

    if latest['Close'] < latest['Support']:
        breakdown = True

    pattern = "Breakout" if breakout else "None"

    return breakout, breakdown, pattern

def detect_trend_reversal(df):
    df = df.copy()
    df.loc[:, 'Short_MA'] = df['Close'].rolling(window=5).mean()
    df.loc[:, 'Long_MA'] = df['Close'].rolling(window=15).mean()

    latest = df.iloc[-1]

    bullish_reversal = False
    bearish_reversal = False

    # 🔥 Relaxed condition
    if latest['Short_MA'] > latest['Long_MA'] and latest['RSI'] < 50:
        bullish_reversal = True

    if latest['Short_MA'] < latest['Long_MA'] and latest['RSI'] > 50:
        bearish_reversal = True

    return bullish_reversal, bearish_reversal

def detect_volume_spike(df, window=10):
    df = df.copy()
    df.loc[:, 'Avg_Volume'] = df['Volume'].rolling(window=window).mean()

    latest = df.iloc[-1]

    spike = False

    if latest['Volume'] > 1.3 * latest['Avg_Volume']:  # Loosened from 1.5x
        spike = True

    return spike

def detect_divergence(df):
    price_trend = df['Close'].iloc[-1] > df['Close'].iloc[-5]
    rsi_trend = df['RSI'].iloc[-1] < df['RSI'].iloc[-5]

    if price_trend and rsi_trend:
        return "Bearish Divergence"

    if not price_trend and not rsi_trend:
        return "Bullish Divergence"

    return None

def calculate_support_resistance(df, window=20):
    df['Resistance'] = df['Close'].rolling(window=window).max()
    df['Support'] = df['Close'].rolling(window=window).min()
    return df

def calculate_moving_average(df, window=20):
    df['MA'] = df['Close'].rolling(window=window).mean()
    return df

# NEW: MACD
def calculate_macd(df, fast=12, slow=26, signal=9):
    df = df.copy()
    ema_fast = df['Close'].ewm(span=fast).mean()
    ema_slow = df['Close'].ewm(span=slow).mean()
    df['MACD'] = ema_fast - ema_slow
    df['MACD_signal'] = df['MACD'].ewm(span=signal).mean()
    df['MACD_hist'] = df['MACD'] - df['MACD_signal']
    return df

# NEW: Bollinger Bands
def bollinger_bands(df, window=20, num_std=2):
    df = df.copy()
    df['BB_mid'] = df['Close'].rolling(window=window).mean()
    bb_std = df['Close'].rolling(window=window).std()
    df['BB_upper'] = df['BB_mid'] + (bb_std * num_std)
    df['BB_lower'] = df['BB_mid'] - (bb_std * num_std)
    return df

# NEW: EMA 200
def ema_200(df):
    df = df.copy()
    df['EMA200'] = df['Close'].ewm(span=200).mean()
    return df

