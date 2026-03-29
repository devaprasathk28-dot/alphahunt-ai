stock_map = {
    "reliance": "RELIANCE.NS",
    "tcs": "TCS.NS",
    "infosys": "INFY.NS",
    "hdfc bank": "HDFCBANK.NS",
    "icici bank": "ICICIBANK.NS",
    "andhra bank": "CANBK.NS",  # merged case
    "canara bank": "CANBK.NS",
    "apple": "AAPL",
    "tesla": "TSLA"
}

def normalize_stock(user_input):
    """
    Normalize stock input: map names to tickers, uppercase others.
    Supports NSE, US, global via yfinance.
    """
    if not user_input:
        return None
    
    user_input = user_input.lower().strip()
    
    if user_input in stock_map:
        return stock_map[user_input]
    
    # If ends with .NS or already ticker-like, uppercase
    return user_input.upper()
