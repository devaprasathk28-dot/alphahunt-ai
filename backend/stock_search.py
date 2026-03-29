from difflib import get_close_matches
import yfinance as yf

stock_db = {
    "reliance": "RELIANCE.NS",
    "tcs": "TCS.NS",
    "infosys": "INFY.NS",
    "hdfc bank": "HDFCBANK.NS",
    "icici bank": "ICICIBANK.NS",
    "canara bank": "CANBK.NS",
    "andhra bank": "CANBK.NS",
    "bharti airtel": "BHARTIARTL.NS",
    "bajaj finance": "BAJFINANCE.NS",
    "larsen toubro": "LT.NS",
    "hindustan unilever": "HINDUNILVR.NS",
    "asian paints": "ASIANPAINT.NS",
    "maruti suzuki": "MARUTI.NS",
    "ultratech cement": "ULTRACEMCO.NS",
    " ITC": "ITC.NS",
    "kotak bank": "KOTAKBANK.NS",
    "axis bank": "AXISBANK.NS",
    "state bank": "SBIN.NS",
    "ntpc": "NTPC.NS",
    "power grid": "POWERGRID.NS",
    "apple": "AAPL",
    "tesla": "TSLA",
    "microsoft": "MSFT",
    "nvidia": "NVDA",
    "amazon": "AMZN"
}

def search_stock_api(query):
    """
    Uses yfinance to search for a stock ticker by checking its info.
    This is a common workaround as yfinance does not have a dedicated search endpoint.
    """
    try:
        search_results = yf.Ticker(query)
        info = search_results.info
        # Ensure a valid symbol was found and it's an equity, not a currency or other asset type.
        if info and info.get('symbol') and info.get('quoteType') == 'EQUITY':
            return info['symbol']
    except Exception:
        # This can happen for many reasons, e.g., network issues or an invalid query.
        return None
    return None

def find_stock(query):
    """
    Finds the best possible stock ticker for a given query.
    1. Checks a local database for an exact match.
    2. Checks the local database for a fuzzy match.
    3. Uses the yfinance API as a fallback search.
    4. Returns None if no valid ticker is found.
    """
    if not query:
        return None
    
    query_lower = query.lower().strip()

    # 1. Exact match in our DB
    if query_lower in stock_db:
        return stock_db[query_lower]

    # 2. Fuzzy match in our DB
    matches = get_close_matches(query_lower, stock_db.keys(), n=1, cutoff=0.6)  # Increased cutoff for better accuracy
    if matches:
        return stock_db[matches[0]]

    # 3. Fallback to yfinance API search
    api_result = search_stock_api(query)
    if api_result:
        return api_result

    # 4. If nothing is found, return None
    return None

def get_suggestions(query, n=3):
    if not query:
        return []
    return get_close_matches(query.lower().strip(), stock_db.keys(), n=n, cutoff=0.6)