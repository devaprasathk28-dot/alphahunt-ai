def score_stock(signal, sentiment):
    score = 50
    if signal == "BUY":
        score += 20
    if sentiment == "Positive":
        score += 20
    return score

