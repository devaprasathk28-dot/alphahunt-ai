import requests

def get_news(stock_name):
    # Demo stub - replace API_KEY with real one
    return ["Sample news for " + stock_name, "Positive earnings report", "Market bullish"]

def analyze_sentiment(headlines):
    # Demo stub
    if any("positive" in h.lower() or "bullish" in h.lower() for h in headlines):
        return "Positive"
    elif any("negative" in h.lower() or "bearish" in h.lower() for h in headlines):
        return "Negative"
    return "Neutral"
