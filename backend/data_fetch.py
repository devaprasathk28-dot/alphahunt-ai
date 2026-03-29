import yfinance as yf
import pandas as pd
from backend.indicators import (
    calculate_rsi, 
    calculate_moving_average, 
    calculate_support_resistance,
    calculate_macd,
    bollinger_bands,
    ema_200
)
import streamlit as st

@st.cache_data(ttl=30)
def get_stock_data(symbol="RELIANCE.NS", period="3mo"):
    """
    Fetch stock data for a given ticker symbol.
    Returns df with indicators or an error dictionary if failed.
    """
    # The symbol is now expected to be pre-validated by the caller.
    if not symbol:
        return {'status': 'error', 'message': 'No symbol provided', 'symbol': ''}
    
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period)
        
        if df.empty:
            print(f"No data for {symbol} ({period}): empty dataframe")
            return {'status': 'error', 'message': 'No data available', 'symbol': symbol}
        
        # Add technical indicators - Enhanced for backtesting
        df = calculate_rsi(df)
        df = calculate_moving_average(df)
        df = calculate_support_resistance(df)
        df = calculate_macd(df)
        df = bollinger_bands(df)
        df = ema_200(df)
        
        return df
    
    except Exception as e:
        print(f"Error fetching data for {symbol} ({period}): {str(e)}")
        return {'status': 'error', 'message': str(e), 'symbol': symbol}

def get_unknown_stock_response(symbol_or_result):
    """
    Smart fallback for unknown stocks or data fetch errors.
    """
    if isinstance(symbol_or_result, dict) and 'status' in symbol_or_result:
        symbol = symbol_or_result['symbol']
        error_msg = symbol_or_result['message']
        return {
            "signal": "ERROR",
            "reason": f"Data fetch failed: {error_msg}",
            "suggestion": "Check ticker validity, market hours, or internet connection. Try NSE (.NS) or US tickers.",
            "stock": symbol,
            "confidence": "Low",
            "score": 0,
            "error": error_msg
        }
    else:
        symbol = symbol_or_result
        return {
            "signal": "UNKNOWN",
            "reason": "Stock not found or inactive",
            "suggestion": "Try using correct name or NSE/BSE ticker (e.g., RELIANCE.NS). For US: AAPL. Check mergers like Andhra Bank → Canara Bank (CANBK.NS).",
            "stock": symbol,
            "confidence": "Low",
            "score": 0
        }

if __name__ == "__main__":
    data = get_stock_data()
    if isinstance(data, pd.DataFrame):
        print(data[['Close', 'RSI', 'MA', 'MACD', 'BB_upper', 'BB_lower', 'EMA200']].tail())
    elif isinstance(data, dict) and 'error' in data:
        print(f"Test error: {data['message']}")
    else:
        print("No data")

