import os
import requests
from textblob import TextBlob

# It's recommended to load the API key from environment variables for security.
NEWS_API_KEY = os.getenv("NEWS_API_KEY", "9d0be412d5df4ef0b10e1ab55e141eb7")
NEWS_API_URL = "https://newsapi.org/v2/everything"

def get_news(query: str, page_size: int = 5) -> list[str]:
    """
    Fetches top news headlines for a given query using NewsAPI.
    """
    if not NEWS_API_KEY or NEWS_API_KEY == "YOUR_NEWS_API_KEY_HERE":
        print("Warning: NEWS_API_KEY is not configured.")
        return ["News service is not configured. Please set your NEWS_API_KEY."]

    params = {
        "q": query,
        "apiKey": NEWS_API_KEY,
        "pageSize": page_size,
        "sortBy": "publishedAt",
        "language": "en"
    }
    try:
        response = requests.get(NEWS_API_URL, params=params)
        response.raise_for_status()
        articles = response.json().get("articles", [])
        return [article['title'] for article in articles]
    except requests.exceptions.RequestException as e:
        print(f"Error fetching news for {query}: {e}")
        return []

def get_sentiment(headlines: list[str]) -> str:
    """
    Analyzes the sentiment of a list of headlines using TextBlob's polarity.
    """
    if not headlines:
        return "Neutral"

    polarity = sum(TextBlob(headline).sentiment.polarity for headline in headlines)  # type: ignore[reportAttributeAccessIssue]
    avg_polarity = polarity / len(headlines) if headlines else 0

    if avg_polarity > 0.1:
        return "Positive"
    elif avg_polarity < -0.1:
        return "Negative"
    else:
        return "Neutral"