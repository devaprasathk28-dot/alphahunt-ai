GLOBAL_STOCKS = {
    "TCS": "TCS.NS",
    "RELIANCE": "RELIANCE.NS",
    "INFY": "INFY.NS",
    "AAPL": "AAPL",
    "TSLA": "TSLA",
    "GOOGL": "GOOGL",
    "MSFT": "MSFT"
}

def map_stock(user_input: str):
    return GLOBAL_STOCKS.get(user_input.upper(), user_input.upper())