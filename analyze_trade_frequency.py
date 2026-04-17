"""
Analyze trade frequency from hyperopt optimization
Runs backtest with best parameters and counts trades
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from src.components.signal_generator import generate_trading_signal
import json


def fetch_historical_data(symbol, start_date, end_date, interval="1h"):
    """Fetch historical price data"""
    ticker = yf.Ticker(symbol)
    df = ticker.history(start=start_date, end=end_date, interval=interval)
    return df


def run_detailed_backtest(params, start_date, end_date):
    """
    Run backtest with detailed trade logging
    
    Returns:
        dict: Detailed backtest results including trade count
    """
    # Load parameters
    initial_capital = 10000
    leverage = params['leverage']
    signal_threshold = params['signal_threshold']
    stop_loss_pct = params['stop_loss_pct']
    take_profit_pct = params['take_profit_pct']
    lookback_periods = params['lookback_periods']
    
    # Fetch data
    symbols = ["BTC-USD", "ETH-USD", "SOL-USD", "AVAX-USD", "BNB-USD"]
    allocations = {
        "BTC-USD": 0.25,
        "ETH-USD": 0.20,
        "SOL-USD": 0.15,
        "AVAX-USD": 0.15,
        "BNB-USD": 0.15
    }
    
    print(f"📊 Fetching data for {len(symbols)} symbols...")
    print(f"Period: {start_date} to {end_date}")
    print()
    
    historical_data = {}
    for symbol in symbols:
        print(f"  Fetching {symbol}...", end=" ")
        df = fetch_historical_data(symbol, start_date, end_date, interval="1h")
        if len(df) > 0:
            historical_data[symbol] = df
            print(f"✅ {len(df)} candles")
    
    print()
    print("Running backtest with best parameters...")
    print(f"  Leverage: {leverage}x")
    print(f"  Signal Threshold: {signal_threshold:.3f}")
    print(f"  Stop Loss: {stop_loss_pct*100:.1f}%")
    print(f"  Take Profit: {take_profit_pct*100:.1f}%")
    print(f"  Lookback: {lookback_periods} periods")
    print()
    
    capital = initial_capital
    positions = {}
    trades_log = []
    
    # Get timeline
    all_dates = set()
    for df in historical_data.values():
        all_dates.update(df.index)
    timeline = sorted(list(all_dates))
    
    # Main backtest loop
    for i, current_time in enumerate(timeline):
        if i < lookback_periods:
            continue
        
        for symbol in historical_data.keys():
            df = historical_data[symbol]
            
            if current_time not in df.index:
                continue
            
            current_price = df.loc[current_time, 'Close']
            prices = df.loc[:current_time, 'Close'].tail(lookback_periods).tolist()
            
            if len(prices) < lookback_periods:
                continue
            
            # Generate technical signals
            signal_data = generate_trading_signal(prices)
            
            # 🔥 INVERT SIGNALS
            signal = -signal_data['signal']
            signal_strength = abs(signal)
            
            allocation = allocations.get(symbol, 0)
            
            # Check existing position
            if symbol in positions:
                position = positions[symbol]
                entry_price = position['entry_price']
                entry_time = position['entry_time']
                pnl_pct = (current_price - entry_price) / entry_price
                
                # Check exit conditions
                should_exit = False
                exit_reason = None
                
                if signal < -signal_threshold:
                    should_exit = True
                    exit_reason = "signal_reversal"
                elif pnl_pct >= take_profit_pct:
                    should_exit = True
                    exit_reason = "take_profit"
                elif pnl_pct <= -stop_loss_pct:
                    should_exit = True
                    exit_reason = "stop_loss"
                
                if should_exit:
                    pnl = (current_price - entry_price) * position['quantity']
                    capital += pnl
                    
                    # Calculate holding duration
                    duration_hours = (current_time - entry_time).total_seconds() / 3600
                    
                    trades_log.append({
                        'symbol': symbol,
                        'entry_time': entry_time,
                        'exit_time': current_time,
                        'entry_price': entry_price,
                        'exit_price': current_price,
                        'quantity': position['quantity'],
                        'pnl': pnl,
                        'pnl_pct': pnl_pct * 100,
                        'exit_reason': exit_reason,
                        'duration_hours': duration_hours
                    })
                    
                    del positions[symbol]
            
            else:
                # No position - check for buy signal
                if signal > signal_threshold:
                    position_value = capital * allocation * leverage
                    quantity = position_value / current_price
                    
                    if position_value >= 100:
                        positions[symbol] = {
                            'entry_price': current_price,
                            'entry_time': current_time,
                            'quantity': quantity
                        }
    
    # Close remaining positions
    final_time = timeline[-1]
    for symbol, position in list(positions.items()):
        if final_time in historical_data[symbol].index:
            current_price = historical_data[symbol].loc[final_time, 'Close']
            pnl = (current_price - position['entry_price']) * position['quantity']
            pnl_pct = (current_price - position['entry_price']) / position['entry_price']
            capital += pnl
            
            duration_hours = (final_time - position['entry_time']).total_seconds() / 3600
            
            trades_log.append({
                'symbol': symbol,
                'entry_time': position['entry_time'],
                'exit_time': final_time,
                'entry_price': position['entry_price'],
                'exit_price': current_price,
                'quantity': position['quantity'],
                'pnl': pnl,
                'pnl_pct': pnl_pct * 100,
                'exit_reason': 'end_of_period',
                'duration_hours': duration_hours
            })
    
    # Calculate statistics
    total_return = (capital - initial_capital) / initial_capital * 100
    total_trades = len(trades_log)
    
    # Calculate date range in days
    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d")
    total_days = (end_dt - start_dt).days
    
    # Trading days calculation (assuming 24/7 crypto)
    trading_days = total_days
    
    # Calculate per-day and per-asset metrics
    trades_per_day = total_trades / trading_days
    trades_per_asset = {symbol: 0 for symbol in symbols}
    
    for trade in trades_log:
        trades_per_asset[trade['symbol']] += 1
    
    # Calculate win rate
    winning_trades = [t for t in trades_log if t['pnl'] > 0]
    losing_trades = [t for t in trades_log if t['pnl'] <= 0]
    win_rate = len(winning_trades) / total_trades * 100 if total_trades > 0 else 0
    
    # Calculate average metrics
    avg_pnl_pct = sum(t['pnl_pct'] for t in trades_log) / total_trades if total_trades > 0 else 0
    avg_win_pct = sum(t['pnl_pct'] for t in winning_trades) / len(winning_trades) if winning_trades else 0
    avg_loss_pct = sum(t['pnl_pct'] for t in losing_trades) / len(losing_trades) if losing_trades else 0
    avg_duration = sum(t['duration_hours'] for t in trades_log) / total_trades if total_trades > 0 else 0
    
    # Exit reason breakdown
    exit_reasons = {}
    for trade in trades_log:
        reason = trade['exit_reason']
        exit_reasons[reason] = exit_reasons.get(reason, 0) + 1
    
    results = {
        'total_return': total_return,
        'total_trades': total_trades,
        'total_days': trading_days,
        'trades_per_day': trades_per_day,
        'trades_per_asset': trades_per_asset,
        'win_rate': win_rate,
        'winning_trades': len(winning_trades),
        'losing_trades': len(losing_trades),
        'avg_pnl_pct': avg_pnl_pct,
        'avg_win_pct': avg_win_pct,
        'avg_loss_pct': avg_loss_pct,
        'avg_duration_hours': avg_duration,
        'exit_reasons': exit_reasons,
        'trades_log': trades_log
    }
    
    return results


def main():
    print("=" * 80)
    print("TRADE FREQUENCY ANALYSIS")
    print("=" * 80)
    print()
    
    # Load best parameters from optimization
    with open('hyperopt_optuna_inverted_results.json', 'r') as f:
        optimization_results = json.load(f)
    
    best_params = optimization_results['best_params']
    
    print("📋 Using optimized parameters:")
    print(f"  Leverage: {best_params['leverage']}x")
    print(f"  Signal Threshold: {best_params['signal_threshold']:.3f}")
    print(f"  Stop Loss: {best_params['stop_loss_pct']*100:.1f}%")
    print(f"  Take Profit: {best_params['take_profit_pct']*100:.1f}%")
    print(f"  Lookback: {best_params['lookback_periods']} periods")
    print()
    
    # Run backtest
    end_date = datetime.now()
    start_date = end_date - timedelta(days=180)  # 6 months
    
    results = run_detailed_backtest(
        best_params,
        start_date.strftime("%Y-%m-%d"),
        end_date.strftime("%Y-%m-%d")
    )
    
    # Display results
    print()
    print("=" * 80)
    print("RESULTS")
    print("=" * 80)
    print()
    
    print(f"📅 Backtest Period: {results['total_days']} days")
    print(f"💰 Total Return: {results['total_return']:+.2f}%")
    print()
    
    print("📊 TRADE FREQUENCY:")
    print(f"  Total Trades: {results['total_trades']}")
    print(f"  Trades per Day: {results['trades_per_day']:.2f}")
    print(f"  Trades per Week: {results['trades_per_day'] * 7:.1f}")
    print(f"  Trades per Month: {results['trades_per_day'] * 30:.1f}")
    print()
    
    print("📈 TRADES BY ASSET:")
    for symbol, count in sorted(results['trades_per_asset'].items(), key=lambda x: x[1], reverse=True):
        trades_per_day = count / results['total_days']
        print(f"  {symbol:10s}: {count:3d} trades ({trades_per_day:.2f} per day)")
    print()
    
    print("🎯 PERFORMANCE:")
    print(f"  Win Rate: {results['win_rate']:.1f}%")
    print(f"  Winning Trades: {results['winning_trades']}")
    print(f"  Losing Trades: {results['losing_trades']}")
    print(f"  Avg P&L per Trade: {results['avg_pnl_pct']:+.2f}%")
    print(f"  Avg Win: {results['avg_win_pct']:+.2f}%")
    print(f"  Avg Loss: {results['avg_loss_pct']:+.2f}%")
    print()
    
    print("⏱️  TRADE DURATION:")
    print(f"  Average Hold Time: {results['avg_duration_hours']:.1f} hours ({results['avg_duration_hours']/24:.1f} days)")
    print()
    
    print("🚪 EXIT REASONS:")
    for reason, count in sorted(results['exit_reasons'].items(), key=lambda x: x[1], reverse=True):
        pct = count / results['total_trades'] * 100
        print(f"  {reason:20s}: {count:3d} ({pct:.1f}%)")
    print()
    
    # Show sample trades
    print("=" * 80)
    print("SAMPLE TRADES (First 10)")
    print("=" * 80)
    print()
    print(f"{'Symbol':<10} {'Entry Date':<20} {'Exit Date':<20} {'P&L%':<10} {'Duration':<15} {'Exit Reason':<15}")
    print("-" * 100)
    
    for trade in results['trades_log'][:10]:
        entry_str = trade['entry_time'].strftime('%Y-%m-%d %H:%M')
        exit_str = trade['exit_time'].strftime('%Y-%m-%d %H:%M')
        duration_str = f"{trade['duration_hours']:.1f}h"
        print(f"{trade['symbol']:<10} {entry_str:<20} {exit_str:<20} {trade['pnl_pct']:>+7.2f}%  {duration_str:<15} {trade['exit_reason']:<15}")
    
    if len(results['trades_log']) > 10:
        print(f"\n... and {len(results['trades_log']) - 10} more trades")
    
    print()
    print("=" * 80)
    
    # Save detailed results
    output_file = 'trade_frequency_analysis.json'
    
    # Convert datetime objects to strings for JSON serialization
    serializable_trades = []
    for trade in results['trades_log']:
        trade_copy = trade.copy()
        trade_copy['entry_time'] = trade['entry_time'].strftime('%Y-%m-%d %H:%M:%S')
        trade_copy['exit_time'] = trade['exit_time'].strftime('%Y-%m-%d %H:%M:%S')
        serializable_trades.append(trade_copy)
    
    results_copy = results.copy()
    results_copy['trades_log'] = serializable_trades
    
    with open(output_file, 'w') as f:
        json.dump(results_copy, f, indent=2)
    
    print(f"💾 Detailed results saved to {output_file}")
    print()


if __name__ == "__main__":
    main()
