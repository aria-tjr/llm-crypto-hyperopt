"""
Signal Analysis Script
Analyzes what signals were generated and why they're losing money
"""

import yfinance as yf
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from src.components.signal_generator import generate_trading_signal

def fetch_data(symbol, start_date, end_date):
    """Fetch historical price data"""
    ticker = yf.Ticker(symbol)
    df = ticker.history(start=start_date, end=end_date, interval="1h")
    return df

def analyze_signals_performance(symbols, start_date, end_date, lookback=100, signal_threshold=0.529):
    """Analyze signal performance for each asset"""
    
    print("=" * 100)
    print("SIGNAL ANALYSIS - Understanding Why Signals Lose Money")
    print("=" * 100)
    print(f"Period: {start_date.date()} to {end_date.date()}")
    print(f"Signal Threshold: {signal_threshold:.3f} (Best from optimization)")
    print(f"Lookback Periods: {lookback}")
    print()
    
    all_results = []
    
    for symbol in symbols:
        print(f"\n{'=' * 100}")
        print(f"📊 ANALYZING {symbol}")
        print('=' * 100)
        
        # Fetch data
        df = fetch_data(symbol, start_date, end_date)
        if len(df) < lookback + 1:
            print(f"⚠️  Not enough data for {symbol}")
            continue
        
        prices = df['Close'].values
        timestamps = df.index
        
        # Track signals and outcomes
        signals_data = {
            'BUY': {'count': 0, 'total_strength': 0, 'outcomes': []},
            'SELL': {'count': 0, 'total_strength': 0, 'outcomes': []},
            'HOLD': {'count': 0, 'total_strength': 0}
        }
        
        # Analyze each timepoint
        for i in range(lookback, len(prices) - 24):  # -24 to see 24h outcome
            current_price = prices[i]
            historical_prices = prices[i-lookback:i]
            
            # Generate signal
            signal_data = generate_trading_signal(historical_prices)
            signal = signal_data['signal']
            strength = abs(signal)
            action = signal_data['action']
            
            # Only count signals that meet threshold
            if strength >= signal_threshold:
                signals_data[action]['count'] += 1
                signals_data[action]['total_strength'] += strength
                
                # Calculate 24h outcome
                future_price = prices[i + 24]
                price_change_pct = ((future_price - current_price) / current_price) * 100
                
                signals_data[action]['outcomes'].append({
                    'timestamp': timestamps[i],
                    'price': current_price,
                    'future_price': future_price,
                    'change_pct': price_change_pct,
                    'strength': strength,
                    'reasons': signal_data['reasons']
                })
        
        # Calculate statistics
        print(f"\n📈 SIGNAL DISTRIBUTION:")
        print(f"  BUY signals:  {signals_data['BUY']['count']:4d} ({signals_data['BUY']['count']/max(1, sum(s['count'] for s in signals_data.values()))*100:.1f}%)")
        print(f"  SELL signals: {signals_data['SELL']['count']:4d} ({signals_data['SELL']['count']/max(1, sum(s['count'] for s in signals_data.values()))*100:.1f}%)")
        print(f"  HOLD signals: {signals_data['HOLD']['count']:4d} ({signals_data['HOLD']['count']/max(1, sum(s['count'] for s in signals_data.values()))*100:.1f}%)")
        
        # Initialize variables
        avg_buy_outcome = 0
        win_rate_buy = 0
        avg_sell_outcome = 0
        win_rate_sell = 0
        
        # Analyze BUY signal performance
        if signals_data['BUY']['outcomes']:
            buy_outcomes = [o['change_pct'] for o in signals_data['BUY']['outcomes']]
            avg_buy_outcome = np.mean(buy_outcomes)
            win_rate_buy = sum(1 for x in buy_outcomes if x > 0) / len(buy_outcomes) * 100
            
            print(f"\n🟢 BUY SIGNAL PERFORMANCE:")
            print(f"  Average 24h return: {avg_buy_outcome:+.2f}%")
            print(f"  Win rate: {win_rate_buy:.1f}%")
            print(f"  Best trade: {max(buy_outcomes):+.2f}%")
            print(f"  Worst trade: {min(buy_outcomes):+.2f}%")
            print(f"  Avg signal strength: {signals_data['BUY']['total_strength']/len(buy_outcomes):.3f}")
            
            # Show sample BUY signals
            print(f"\n  📋 Sample BUY signals:")
            for outcome in signals_data['BUY']['outcomes'][:3]:
                print(f"    {outcome['timestamp'].strftime('%Y-%m-%d %H:%M')} | "
                      f"Price: ${outcome['price']:.2f} | "
                      f"24h Change: {outcome['change_pct']:+.2f}% | "
                      f"Strength: {outcome['strength']:.3f}")
                print(f"       Reasons: {', '.join(outcome['reasons'][:2])}")
        
        # Analyze SELL signal performance
        if signals_data['SELL']['outcomes']:
            sell_outcomes = [o['change_pct'] for o in signals_data['SELL']['outcomes']]
            avg_sell_outcome = np.mean(sell_outcomes)
            # For SELL signals, negative price movement is good
            win_rate_sell = sum(1 for x in sell_outcomes if x < 0) / len(sell_outcomes) * 100
            
            print(f"\n🔴 SELL SIGNAL PERFORMANCE:")
            print(f"  Average 24h return: {avg_sell_outcome:+.2f}% (negative is good for shorts)")
            print(f"  Win rate: {win_rate_sell:.1f}% (price went down)")
            print(f"  Best trade: {min(sell_outcomes):+.2f}% (most negative)")
            print(f"  Worst trade: {max(sell_outcomes):+.2f}% (went up instead)")
            print(f"  Avg signal strength: {signals_data['SELL']['total_strength']/len(sell_outcomes):.3f}")
            
            # Show sample SELL signals
            print(f"\n  📋 Sample SELL signals:")
            for outcome in signals_data['SELL']['outcomes'][:3]:
                print(f"    {outcome['timestamp'].strftime('%Y-%m-%d %H:%M')} | "
                      f"Price: ${outcome['price']:.2f} | "
                      f"24h Change: {outcome['change_pct']:+.2f}% | "
                      f"Strength: {outcome['strength']:.3f}")
                print(f"       Reasons: {', '.join(outcome['reasons'][:2])}")
        
        # Market trend analysis
        start_price = prices[lookback]
        end_price = prices[-1]
        total_return = ((end_price - start_price) / start_price) * 100
        
        print(f"\n📊 MARKET TREND:")
        print(f"  Start price: ${start_price:.2f}")
        print(f"  End price:   ${end_price:.2f}")
        print(f"  Total return: {total_return:+.2f}%")
        
        # Calculate what would happen if we INVERTED signals
        if signals_data['BUY']['outcomes'] and signals_data['SELL']['outcomes']:
            # If we inverted: BUY becomes SELL (we profit from -change), SELL becomes BUY (we profit from +change)
            inverted_buy_return = -np.mean([o['change_pct'] for o in signals_data['BUY']['outcomes']])
            inverted_sell_return = np.mean([o['change_pct'] for o in signals_data['SELL']['outcomes']])
            
            print(f"\n🔄 INVERTED SIGNALS ANALYSIS:")
            print(f"  If we SOLD when signal said BUY: {inverted_buy_return:+.2f}% avg return")
            print(f"  If we BOUGHT when signal said SELL: {inverted_sell_return:+.2f}% avg return")
        
        # Store results
        all_results.append({
            'symbol': symbol,
            'buy_count': signals_data['BUY']['count'],
            'sell_count': signals_data['SELL']['count'],
            'buy_avg_return': avg_buy_outcome if signals_data['BUY']['outcomes'] else 0,
            'sell_avg_return': avg_sell_outcome if signals_data['SELL']['outcomes'] else 0,
            'buy_win_rate': win_rate_buy if signals_data['BUY']['outcomes'] else 0,
            'sell_win_rate': win_rate_sell if signals_data['SELL']['outcomes'] else 0,
            'market_return': total_return
        })
    
    # Summary across all assets
    print(f"\n\n{'=' * 100}")
    print("📊 OVERALL SUMMARY")
    print('=' * 100)
    
    df_results = pd.DataFrame(all_results)
    
    print(f"\nAverage BUY signal return: {df_results['buy_avg_return'].mean():+.2f}%")
    print(f"Average SELL signal return: {df_results['sell_avg_return'].mean():+.2f}%")
    print(f"Average BUY win rate: {df_results['buy_win_rate'].mean():.1f}%")
    print(f"Average SELL win rate: {df_results['sell_win_rate'].mean():.1f}%")
    print(f"Average market return: {df_results['market_return'].mean():+.2f}%")
    
    print(f"\n🔍 KEY INSIGHTS:")
    
    # Check if BUY signals are profitable
    if df_results['buy_avg_return'].mean() < 0:
        print(f"  ❌ BUY signals lose money on average ({df_results['buy_avg_return'].mean():+.2f}%)")
    else:
        print(f"  ✅ BUY signals make money on average ({df_results['buy_avg_return'].mean():+.2f}%)")
    
    # Check if SELL signals are profitable (negative movement is good)
    if df_results['sell_avg_return'].mean() > 0:
        print(f"  ❌ SELL signals fail - market went UP {df_results['sell_avg_return'].mean():+.2f}% after SELL signals")
    else:
        print(f"  ✅ SELL signals work - market went DOWN {df_results['sell_avg_return'].mean():+.2f}% after SELL signals")
    
    # Check signal inversion potential
    inverted_buy = -df_results['buy_avg_return'].mean()
    inverted_sell = df_results['sell_avg_return'].mean()
    
    print(f"\n💡 INVERSION ANALYSIS:")
    print(f"  If we SHORT when current signals say BUY: {inverted_buy:+.2f}% avg return")
    print(f"  If we LONG when current signals say SELL: {inverted_sell:+.2f}% avg return")
    
    if inverted_buy > 0 and inverted_sell > 0:
        print(f"  🔥 INVERTING SIGNALS WOULD BE PROFITABLE!")
    
    print(f"\n{'=' * 100}")

if __name__ == "__main__":
    # Use best parameters from optimization
    symbols = ["BTC-USD", "ETH-USD", "SOL-USD", "AVAX-USD", "BNB-USD"]
    end_date = datetime.now()
    start_date = end_date - timedelta(days=180)  # 6 months
    
    # Best parameters from optimization
    best_lookback = 100
    best_threshold = 0.529
    
    analyze_signals_performance(symbols, start_date, end_date, best_lookback, best_threshold)
