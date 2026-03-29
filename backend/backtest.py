from backend.data_fetch import get_stock_data
from backend.signal_engine import generate_signal
import pandas as pd
import numpy as np

def backtest_stock(symbol='RELIANCE.NS', period='1y', lookforward_days=5, win_threshold_pct=1.0):
    """
    Enhanced backtest with configurable params, drawdown, avg returns.
    """
    try:
        df = get_stock_data(symbol, period=period)
        if isinstance(df, dict):  # Error case
            print(f'$ {symbol}: data fetch failed')
            return {'buy_accuracy': 0, 'sell_accuracy': 0, 'total_buy': 0, 'total_sell': 0, 'signal_counts': {'BUY': 0, 'SELL': 0, 'HOLD': 0}}
    except Exception as e:
        print(f'$ {symbol}: error {e}')
        return {'buy_accuracy': 0, 'sell_accuracy': 0, 'total_buy': 0, 'total_sell': 0, 'signal_counts': {'BUY': 0, 'SELL': 0, 'HOLD': 0}}

    if len(df) < 100:
        print(f'{symbol}: insufficient data ({len(df)} candles)')
        return {'buy_accuracy': 0, 'sell_accuracy': 0, 'total_buy': 0, 'total_sell': 0, 'signal_counts': {'BUY': 0, 'SELL': 0, 'HOLD': 0}}

    print(f'Backtesting {symbol} ({period}, fwd={lookforward_days}d, thresh={win_threshold_pct}%) : {len(df)} candles')
    
    wins_buy = 0
    total_buy = 0
    buy_returns = []
    wins_sell = 0
    total_sell = 0
    sell_returns = []
    signal_counts = {'BUY': 0, 'SELL': 0, 'HOLD': 0}
    
    for i in range(20, len(df) - lookforward_days):  # Start at 20 for new signal min data
        sub_df = df.iloc[:i].copy()
        
        signal = generate_signal(sub_df)
        if 'signal' not in signal or signal['signal'] is None:
            continue
        signal_counts[signal['signal']] += 1
        
        current_price = df.iloc[i]['Close']
        
        if signal['signal'] == 'BUY' and len(sub_df) >= 20:
            total_buy += 1
            future_price = df.iloc[i + lookforward_days]['Close']
            profit_pct = (future_price - current_price) / current_price * 100
            buy_returns.append(profit_pct)
            if profit_pct > win_threshold_pct:
                wins_buy += 1
            if total_buy % 10 == 0 or total_buy <= 5:  # Log every 10 + first 5
                print(f'{symbol} BUY #{total_buy}@{i}: {current_price:.2f}->{future_price:.2f} ({profit_pct:+.1f}%) {"WIN" if profit_pct > win_threshold_pct else "LOSS"} | conf:{signal.get("confidence", "N/A")}')
            
        elif signal['signal'] == 'SELL' and len(sub_df) >= 20:
            total_sell += 1
            future_price = df.iloc[i + lookforward_days]['Close']
            profit_pct = (current_price - future_price) / current_price * 100  # Positive if price drops
            sell_returns.append(profit_pct)
            if profit_pct > win_threshold_pct:
                wins_sell += 1
            if total_sell % 10 == 0 or total_sell <= 5:
                print(f'{symbol} SELL #{total_sell}@{i}: {current_price:.2f}->{future_price:.2f} ({profit_pct:+.1f}%) {"WIN" if profit_pct > win_threshold_pct else "LOSS"}')
    
    # Calculate metrics
    buy_accuracy = round((wins_buy / total_buy * 100), 1) if total_buy > 0 else 0
    sell_accuracy = round((wins_sell / total_sell * 100), 1) if total_sell > 0 else 0
    
    avg_buy_return = round(np.mean(buy_returns), 2) if buy_returns else 0
    avg_sell_return = round(np.mean(sell_returns), 2) if sell_returns else 0
    
    # Simple max drawdown proxy (per-signal basis)
    buy_dd = round(np.min(buy_returns), 2) if buy_returns else 0
    sell_dd = round(np.min(sell_returns), 2) if sell_returns else 0
    
    print(f'{symbol} Signals: {signal_counts}')
    print(f'{symbol} BUY: {buy_accuracy}% ({wins_buy}/{total_buy}), avg {avg_buy_return}%, worst {buy_dd}%')
    print(f'{symbol} SELL: {sell_accuracy}% ({wins_sell}/{total_sell}), avg {avg_sell_return}%, worst {sell_dd}%')
    
    return {
        'buy_accuracy': buy_accuracy,
        'sell_accuracy': sell_accuracy,
        'total_buy': total_buy,
        'total_sell': total_sell,
        'avg_buy_return': avg_buy_return,
        'avg_sell_return': avg_sell_return,
        'buy_max_dd': buy_dd,
        'sell_max_dd': sell_dd,
        'signal_counts': signal_counts
    }

def run_full_backtest():
    stocks = ['RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'INFY.NS', 'ICICIBANK.NS']
    results = []
    
    for symbol in stocks:
        result = backtest_stock(symbol, period='1y', lookforward_days=5, win_threshold_pct=1.0)
        results.append({**result, 'symbol': symbol})
    
    active_results = [r for r in results if r['total_buy'] + r['total_sell'] > 10]
    if active_results:
        avg_buy = np.mean([r['buy_accuracy'] for r in active_results])
        avg_sell = np.mean([r['sell_accuracy'] for r in active_results if r['total_sell'] > 0])
        print(f'\n🚀 AVG BUY ACC: {avg_buy:.1f}% | AVG SELL ACC: {avg_sell:.1f}% across {len(active_results)} stocks')
    
    return results

if __name__ == '__main__':
    run_full_backtest()

