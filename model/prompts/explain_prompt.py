def get_prompt(stock, signal, sentiment):
    return f"""
Analyze stock {stock}.
Signal: {signal}
Sentiment: {sentiment}

Explain:
- Opportunity
- Risk
- Recommendation
    """

