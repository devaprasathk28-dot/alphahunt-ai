from backend.data_fetch import get_stock_data, get_unknown_stock_response
from backend.signal_engine import generate_signal
from backend.ai_engine import generate_ai_explanation
from backend.news_service import get_news, get_sentiment
# Sample stock list (you can expand later)
from backend.stock_search import find_stock

STOCKS = [
    "reliance",
    "tcs",
    "infosys",
    "hdfc bank",
    "icici bank"
]

def scan_market(stocks_to_scan=None):
    results = []

    # If no stocks are provided, fall back to the default list for backward compatibility.
    if stocks_to_scan is None:
        stocks_to_scan = STOCKS

    for stock_query in stocks_to_scan:
        try:
            ticker = find_stock(stock_query)
            if not ticker:
                print(f"Scanner: Could not find ticker for '{stock_query}'. Skipping.")
                signal = get_unknown_stock_response(stock_query)
                signal['ai_explanation'] = generate_ai_explanation(signal)
                results.append(signal)
                continue

            data = get_stock_data(ticker)

            if isinstance(data, dict) and data.get('status') == 'error':
                signal = get_unknown_stock_response(data)
            else:
                signal = generate_signal(data)
                headlines = get_news(ticker)
                sentiment = get_sentiment(headlines)
                signal['news_sentiment'] = sentiment

            # Ensure stock key is the normalized version
            signal['stock'] = ticker

            # 🔥 AI explanation
            signal['ai_explanation'] = generate_ai_explanation(signal)

            results.append(signal)

        except Exception as e:
            print(f"Error processing {stock_query}: {e}")

    return results
def rank_opportunities(results):
    for r in results:
        # Handle non-technical signals gracefully.
        # If a signal is an error or for an unknown stock, it won't have technical
        # indicator keys like 'rsi', 'price', or 'ma'. We should skip ranking for these.
        if r.get('signal') in ["ERROR", "UNKNOWN"]:
            r['score'] = r.get('score', 0)
            r['confidence'] = r.get('confidence', "Low")
            r['event_signal'] = "Neutral"
            continue

        score = 0

        # 🔥 1. Signal base
        if r['signal'] == "BUY":
            score += 3
        elif r['signal'] == "SELL":
            score += 0
        else:
            score += 1

        # 🔥 2. RSI strength
        rsi = r.get('rsi', 50)
        if rsi < 25:
            score += 3
        elif rsi < 35:
            score += 2
        elif rsi < 45:
            score += 1

        # 🔥 3. Trend (price vs MA)
        price = r.get('price', 0)
        ma = r.get('ma', 0)
        if price > ma:
            score += 1
        else:
            score -= 1  # weak trend

        # 🔥 4. Breakout bonus (if exists in reason)
        if "Breakout" in r['reason']:
            score += 2

        # 🔥 Volume spike bonus
        if r.get('volume_spike'):
            score += 2

# 🔥 5. News sentiment
        sentiment = r.get('news_sentiment', "")
        if "Positive" in sentiment:
            score += 2
        elif "Negative" in sentiment:
            score -= 2

        # 🔥 Event-based signal
        sentiment = r.get('news_sentiment', "")
        if "Positive" in sentiment and r.get('volume_spike'):
            r['event_signal'] = "Strong BUY (News + Volume)"
        elif "Negative" in sentiment:
            r['event_signal'] = "SELL Warning (Negative News)"
        else:
            r['event_signal'] = "Neutral"

        # Boost score for strongest signal
        if r['event_signal'] == "Strong BUY (News + Volume)":
            score += 3

        # 🔥 Normalize score (0–10)
        score = max(0, min(score, 10))

        # 🔥 Confidence label
        if score >= 8:
            confidence = "High"
        elif score >= 5:
            confidence = "Medium"
        else:
            confidence = "Low"

        # ✅ Save results
        r['score'] = score
        r['confidence'] = confidence

    return sorted(results, key=lambda x: x['score'], reverse=True)
