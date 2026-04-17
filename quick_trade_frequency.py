"""
Quick estimate of trade frequency based on signal threshold
Samples recent market data to estimate how often signals exceed threshold
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import yfinance as yf
from datetime import datetime, timedelta
from src.components.signal_generator import generate_trading_signal
import json

# Load best parameters
with open('hyperopt_optuna_inverted_results.json', 'r') as f:
    results = json.load(f)

best_params = results['best_params']
signal_threshold = best_params['signal_threshold']
lookback_periods = best_params['lookback_periods']

print("=" * 80)
print("QUICK TRADE FREQUENCY ESTIMATE")
print("=" * 80)
print()
print(f"Signal Threshold: {signal_threshold:.3f}")
print(f"Lookback Periods: {lookback_periods}")
print()

# Fetch 30 days of recent data (enough for estimation)
symbols = ["BTC-USD", "ETH-USD", "SOL-USD", "AVAX-USD", "BNB-USD"]
end_date = datetime.now()
start_date = end_date - timedelta(days=30)

print(f"Sampling period: Last 30 days")
print(f"Assets: {len(symbols)}")
print()

signal_counts = {}
total_checks = 0
signals_above_threshold = 0

for symbol in symbols:
    print(f"Analyzing {symbol}...")
    ticker = yf.Ticker(symbol)
    df = ticker.history(start=start_date.strftime("%Y-%m-%d"), 
                       end=end_date.strftime("%Y-%m-%d"), 
                       interval="1h")
    
    if len(df) < lookback_periods:
        print(f"  Insufficient data")
        continue
    
    above_threshold_count = 0
    checks = 0
    
    # Sample every 6 hours to speed up
    for i in range(lookback_periods, len(df), 6):
        prices = df['Close'].iloc[:i].tail(lookback_periods).tolist()
        
        try:
            signal_data = generate_trading_signal(prices)
            # Invert signal as in strategy
            signal_strength = abs(-signal_data['signal'])
            
            checks += 1
            if signal_strength >= signal_threshold:
                above_threshold_count += 1
        except Exception as e:
            continue
    
    signal_counts[symbol] = {
        'checks': checks,
        'above_threshold': above_threshold_count,
        'percentage': (above_threshold_count / checks * 100) if checks > 0 else 0
    }
    
    total_checks += checks
    signals_above_threshold += above_threshold_count
    
    print(f"  Checked {checks} time points")
    print(f"  Signals ≥ threshold: {above_threshold_count} ({above_threshold_count/checks*100:.1f}%)")
    print()

# Calculate estimates
overall_percentage = (signals_above_threshold / total_checks * 100) if total_checks > 0 else 0

print("=" * 80)
print("TRADE FREQUENCY ESTIMATES")
print("=" * 80)
print()

print(f"📊 Signal Analysis:")
print(f"  Total checks: {total_checks}")
print(f"  Signals ≥ {signal_threshold:.3f}: {signals_above_threshold} ({overall_percentage:.1f}%)")
print()

# Estimate trades per day
# In live trading, we check every 5 minutes = 288 checks/day
# But with 8 assets and signal threshold, actual frequency will be lower

checks_per_day = 24  # 24 hourly checks per day per asset
assets = 5

# Best case: if every signal above threshold becomes a trade
max_potential_trades_per_day = checks_per_day * assets * (overall_percentage / 100)

# Realistic: not every signal results in trade (LLM confidence, existing positions)
# Apply a conservative 50% conversion rate
realistic_trades_per_day = max_potential_trades_per_day * 0.5

print(f"📈 Trade Frequency Estimates:")
print(f"  Potential signals per day: {max_potential_trades_per_day:.1f}")
print(f"  Realistic trades per day: {realistic_trades_per_day:.1f}")
print(f"  Trades per week: {realistic_trades_per_day * 7:.1f}")
print(f"  Trades per month: {realistic_trades_per_day * 30:.0f}")
print()

# Calculate based on actual backtest performance
backtest_return = results['best_return']
backtest_days = 180  # 6 months

# If we assume average trade P&L of 5-10% (with 10x leverage), and achieved 256% over 180 days
# We can estimate trade count
avg_trade_pnl_pct = 8  # Average 8% per trade estimate
estimated_total_trades = backtest_return / avg_trade_pnl_pct
estimated_trades_per_day = estimated_total_trades / backtest_days

print(f"📊 Backtest-based Estimate:")
print(f"  Total return: +{backtest_return:.2f}%")
print(f"  Backtest period: {backtest_days} days")
print(f"  Estimated avg trade P&L: {avg_trade_pnl_pct}%")
print(f"  Estimated total trades: {estimated_total_trades:.0f}")
print(f"  Trades per day: {estimated_trades_per_day:.2f}")
print(f"  Trades per week: {estimated_trades_per_day * 7:.1f}")
print(f"  Trades per month: {estimated_trades_per_day * 30:.0f}")
print()

print("=" * 80)
print("SUMMARY")
print("=" * 80)
print()
print(f"📌 Expected Trade Frequency: {realistic_trades_per_day:.1f} - {estimated_trades_per_day:.2f} trades/day")
print()
print(f"This represents:")
print(f"  • {realistic_trades_per_day * 7:.0f}-{estimated_trades_per_day * 7:.0f} trades per week")
print(f"  • {realistic_trades_per_day * 30:.0f}-{estimated_trades_per_day * 30:.0f} trades per month")
print()
print(f"With signal threshold of {signal_threshold:.3f}, the strategy is SELECTIVE")
print(f"and waits for high-quality setups rather than frequent trading.")
print()
print("=" * 80)
