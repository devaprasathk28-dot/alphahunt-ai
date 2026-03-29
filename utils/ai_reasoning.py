from openai import OpenAI

# This assumes you have the OPENAI_API_KEY environment variable set.
client = OpenAI()

def generate_explanation(stock, signal_data, news_summary=""):
    prompt = f"""
    Analyze stock {stock}.

    Signal: {signal_data['signal']}
    RSI: {signal_data['rsi']}

    News: {news_summary}

    Explain in simple terms:
    - Why this signal occurred
    - Whether it's a good opportunity
    - Risk level
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content