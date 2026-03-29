def rank_stocks(stock_results):
    ranked = []

    for stock, data in stock_results.items():
        score = 0

        if data["signal"]["signal"] == "BUY":
            score += 50

        rsi = data["signal"]["rsi"]
        score += max(0, 50 - abs(50 - rsi))

        ranked.append({
            "stock": stock,
            "score": score,
            "signal": data["signal"]["signal"]
        })

    ranked.sort(key=lambda x: x["score"], reverse=True)

    return ranked[:10]