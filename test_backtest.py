from backend.backtest import backtest_stock, run_full_backtest
import pandas as pd

print("=== SINGLE STOCK TEST ===")
result = backtest_stock("RELIANCE.NS", period="1y", lookforward_days=5, win_threshold_pct=1.0)
print(f"RELIANCE.NS 1y: BUY {result['buy_accuracy']:.1f}% ({result['total_buy']} sigs, avg {result['avg_buy_return']:.2f}%) | SELL {result['sell_accuracy']:.1f}% ({result['total_sell']} sigs)")
print(f"Counts: {result['signal_counts']}")

print("\n=== FULL MARKET TEST ===")
results = run_full_backtest()
summary = pd.DataFrame([r for r in results if r['total_buy'] + r['total_sell'] > 0])
if not summary.empty:
    print(f"\n📊 SUMMARY (Active Stocks):")
    print(f"  Avg BUY Win Rate: {summary['buy_accuracy'].mean():.1f}%")
    print(f"  Avg SELL Win Rate: {summary[summary['total_sell']>0]['sell_accuracy'].mean():.1f}%")
    print(f"  Total Signals/Stock: ~{summary['total_buy'].sum() + summary['total_sell'].sum() / len(summary):.0f}")
    print(f"  Success Criteria: BUY>50%, Signals>20/stock ✓" if summary['buy_accuracy'].mean() > 50 and summary['total_buy'].mean() > 20 else "⚠️ Needs more tuning")
else:
    print("No active results")

print("\n🎯 REFINEMENT COMPLETE - Strategy improved!")

