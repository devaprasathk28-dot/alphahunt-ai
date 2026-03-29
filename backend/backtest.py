from backend.data_fetch import get_stock_data
import pandas as pd

def backtest_strategy(df):
    df = df.copy()

    # Indicators
    df["MA20"] = df["Close"].rolling(20).mean()
    df["MA50"] = df["Close"].rolling(50).mean()

    signals_list = []
    buy_signals = 0
    sell_signals = 0
    buy_wins = 0
    sell_wins = 0
    hold_count = 0
    returns = []
    import numpy as np

    for i in range(50, len(df) - 5):  # leave future candles
        price = df["Close"].iloc[i]
        ma20 = df["MA20"].iloc[i]
        ma50 = df["MA50"].iloc[i]

        future_price = df["Close"].iloc[i + 5]

        # 🔥 BUY CONDITION
        if price > ma20 and ma20 > ma50:
            buy_signals += 1
            ret_pct = (future_price - price) / price * 100
            is_win = ret_pct > 0  # BUY win if price rises
            if is_win:
                buy_wins += 1
            signals_list.append({
                'timestamp': df.index[i],
                'signal': 'BUY',
                'entry_price': price,
                'future_price': future_price,
                'return_pct': ret_pct,
                'win': is_win
            })
            returns.append(ret_pct if is_win else 0)

        # 🔥 SELL CONDITION
        elif price < ma20 and ma20 < ma50:
            sell_signals += 1
            ret_pct = (future_price - price) / price * 100
            is_win = ret_pct < 0  # SELL win if price drops
            if is_win:
                sell_wins += 1
            signals_list.append({
                'timestamp': df.index[i],
                'signal': 'SELL',
                'entry_price': price,
                'future_price': future_price,
                'return_pct': ret_pct,
                'win': is_win
            })
            returns.append(ret_pct if is_win else 0)
        else:
            hold_count += 1
            signals_list.append({
                'timestamp': df.index[i],
                'signal': 'HOLD',
                'entry_price': price,
                'future_price': future_price,
                'return_pct': 0,
                'win': True  # HOLD always "wins"
            })

    # Compute perf stats
    signals_df = pd.DataFrame(signals_list)
    
    if len(returns) > 1:
        returns = np.array(returns)
        total_return = (np.prod(1 + returns/100) - 1) * 100
        mean_ret = np.mean(returns)
        std_ret = np.std(returns)
        sharpe = mean_ret / std_ret * np.sqrt(252 * 24) if std_ret > 0 else 0  # Hourly
        equity_curve = [10000]
        for r in returns:
            equity_curve.append(equity_curve[-1] * (1 + r/100))
        max_dd = min(0, ((np.array(equity_curve) / np.maximum.accumulate(np.array(equity_curve))) - 1).min() * 100)
    else:
        total_return = sharpe = max_dd = 0
        equity_curve = [10000]
    
    perf_stats = {
        'total_return_pct': round(total_return, 2),
        'sharpe_ratio': round(sharpe, 2),
        'max_drawdown_pct': round(max_dd, 2),
        'equity_curve': equity_curve
    }
    
    return {
        **perf_stats,
        "BUY": buy_wins, "SELL": sell_wins,
        "BUY_TOTAL": buy_signals, "SELL_TOTAL": sell_signals, "HOLD_TOTAL": hold_count,
        "signals_df": signals_df.to_dict('records'),
        "returns": returns
    }

def backtest_stock(symbol='RELIANCE.NS', period='3mo', lookforward_days=5, win_threshold_pct=1.0):
    """
    Fixed backtest using simple MA strategy - generates signals guaranteed
    """
    try:
        df = get_stock_data(symbol, period=period)
        if isinstance(df, dict):  # Error case
            print(f'Error fetching data for {symbol}')
            return backtest_strategy(pd.DataFrame())  # Return zeros
        
        if len(df) < 60:
            print(f'Insufficient data for {symbol}: {len(df)} rows')
            return backtest_strategy(df.tail(60))  # Use what we have
        
        print(f'Backtesting {symbol} with {len(df)} hourly candles')
        result = backtest_strategy(df)
        
        # Log results
        print(f'{symbol}: BUY {result["BUY"]}/{result["BUY_TOTAL"]} | SELL {result["SELL"]}/{result["SELL_TOTAL"]}')
        
        # Backward compatibility
        return {
            'buy_accuracy': round(result["BUY"] / max(result["BUY_TOTAL"], 1) * 100, 1),
            'sell_accuracy': round(result["SELL"] / max(result["SELL_TOTAL"], 1) * 100, 1),
            'hold_accuracy': 100.0,
            'total_buy': result["BUY_TOTAL"],
            'total_sell': result["SELL_TOTAL"],
            'total_hold': result.get("HOLD_TOTAL", 0),
            'signal_counts': {
                'BUY': result["BUY_TOTAL"], 
                'SELL': result["SELL_TOTAL"], 
                'HOLD': result.get("HOLD_TOTAL", 0)
            },
            **result
        }
    except Exception as e:
        print(f'Backtest error {symbol}: {e}')
        return {'buy_accuracy': 0, 'sell_accuracy': 0, 'total_buy': 0, 'total_sell': 0}

def run_full_backtest():
    stocks = ['RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS']
    results = []
    for symbol in stocks:
        result = backtest_stock(symbol)
        results.append({**result, 'symbol': symbol})
    return results

if __name__ == '__main__':
    run_full_backtest()

