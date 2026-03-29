import yfinance as yf

class GlobalStockService:

    def get_stock_data(self, ticker: str, period="1mo"):
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period)

        return {
            "ticker": ticker,
            "price": hist["Close"].iloc[-1],
            "history": hist.tail(30).to_dict(),
        }

    def get_multiple_stocks(self, tickers: list):
        data = {}
        for t in tickers:
            try:
                data[t] = self.get_stock_data(t)
            except:
                continue
        return data