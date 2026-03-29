from fastapi import APIRouter
import pandas as pd

# Upgrade: Use the existing, more powerful backend services instead of the new simple ones.
from backend.data_fetch import get_stock_data, get_unknown_stock_response
from backend.signal_engine import generate_signal
from backend.scanner import rank_opportunities
from backend.ai_engine import generate_ai_explanation

router = APIRouter()

@router.get("/global-opportunities")
def get_opportunities():
    """
    Scans a predefined list of global and Indian stocks, generates signals,
    ranks them using the existing backend logic, and returns the top opportunities.
    This endpoint powers the "Global Market Intelligence" tab in the UI.
    """
    # A mix of global and Indian stocks for demonstration
    tickers = ["AAPL", "TSLA", "GOOGL", "MSFT", "RELIANCE.NS", "TCS.NS", "INFY.NS", "NVDA"]

    results = []
    for ticker in tickers:
        # Use the existing, more powerful data fetcher which includes indicator calculation
        data_df = get_stock_data(ticker, period="3mo")

        if isinstance(data_df, pd.DataFrame) and not data_df.empty:
            # Use the existing, more powerful signal engine
            signal = generate_signal(data_df)
            signal['stock'] = ticker # Ensure stock ticker is in the result
        else:
            # Handle cases where stock data couldn't be fetched
            signal = get_unknown_stock_response(data_df if isinstance(data_df, dict) else ticker)
        
        signal['ai_explanation'] = generate_ai_explanation(signal)
        results.append(signal)

    # Use the existing, more powerful ranking logic
    ranked = rank_opportunities(results)

    return ranked[:10]