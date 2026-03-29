from typing import Any
from groq import Groq
import os



client = Groq(api_key=os.getenv("GROQ_API_KEY"))  # Load from .env



def generate_ai_explanation(signal_data: dict[str, Any]) -> str:
    try:
        prompt = f"""
You are an expert financial analyst AI. Analyze this stock signal.

Stock: {signal_data.get('stock', 'Unknown')}
Signal: {signal_data['signal']}
RSI: {signal_data.get('rsi', 'N/A')}
Price: {signal_data.get('price', 'N/A')}
MA: {signal_data.get('ma', 'N/A')}
Reason: {signal_data['reason'][:200]}...

Provide detailed analysis and recommendation (200-300 words)."""
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            temperature=0.7
        )
        return response.choices[0].message.content or "Analysis unavailable"
    except:
        return f"Signal {signal_data['signal']}: {signal_data['reason'][:150]}... (Live AI unavailable - demo mode)"

def chat_with_ai(messages, temperature=0.7, max_tokens=500, context_data=""):
    try:
        prompt = f"Stock context: {context_data[:300]}\nUser query: {messages[-1]['content']}"
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature
        )
        return response.choices[0].message.content or "No response"
    except:
        return "AI chat demo: Great question about stocks! Check technical levels, news sentiment, and RSI for decisions. (Live Groq unavailable)"

def analyze_sentiment(headlines):
    positive_words = ['gain', 'rise', 'bullish', 'buy', 'profit']
    negative_words = ['loss', 'fall', 'bearish', 'sell', 'decline']
    pos_count = sum(any(word in h.lower() for word in positive_words) for h in headlines)
    neg_count = sum(any(word in h.lower() for word in negative_words) for h in headlines)
    if pos_count > neg_count:
        return "Positive"
    elif neg_count > pos_count:
        return "Negative"
    return "Neutral"
