from backend.scanner import scan_market, rank_opportunities

results = scan_market()
ranked = rank_opportunities(results)

print("\n=== TOP OPPORTUNITIES ===\n")

for r in ranked:
    print(f"{r['stock']} | {r['signal']} | Score: {r['score']} | Confidence: {r['confidence']}")
    print(f"Reason: {r['reason']}")
    print(f"AI: {r['ai_explanation']}")
    print(f"Sentiment: {r['news_sentiment']}")
    print("-" * 40)