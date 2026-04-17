"""
Fast Hyperparameter Optimization - Pure Technical Analysis
No LLM calls, tests parameters quickly to find best configuration
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from src.components.signal_generator import generate_trading_signal
from itertools import product
import json


def fetch_historical_data(symbol, start_date, end_date, interval="1h"):
    """Fetch historical price data"""
    ticker = yf.Ticker(symbol)
    df = ticker.history(start=start_date, end=end_date, interval=interval)
    return df


def run_fast_backtest(historical_data, params, allocations):
    """
    Fast backtest using technical signals only (no LLM)
    
    Args:
        historical_data: Dict of symbol -> DataFrame
        params: Dict with configuration
        allocations: Dict of symbol -> allocation %
        
    Returns:
        Dict with results
    """
    initial_capital = params['initial_capital']
    leverage = params['leverage']
    signal_threshold = params['signal_threshold']
    stop_loss_pct = params['stop_loss_pct']
    take_profit_pct = params['take_profit_pct']
    lookback_periods = params['lookback_periods']
    
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
            
            # Generate technical signals (fast, no LLM)
            signal_data = generate_trading_signal(prices)
            signal = signal_data['signal']
            
            allocation = allocations.get(symbol, 0)
            
            # Check existing position
            if symbol in positions:
                position = positions[symbol]
                entry_price = position['entry_price']
                pnl_pct = (current_price - entry_price) / entry_price
                
                # Check exit conditions
                should_exit = False
                exit_reason = ""
                
                # Exit on opposite signal
                if signal < -signal_threshold:
                    should_exit = True
                    exit_reason = "SIGNAL"
                elif pnl_pct >= take_profit_pct:
                    should_exit = True
                    exit_reason = "TP"
                elif pnl_pct <= -stop_loss_pct:
                    should_exit = True
                    exit_reason = "SL"
                
                if should_exit:
                    pnl = (current_price - entry_price) * position['quantity']
                    capital += pnl
                    
                    trades_log.append({
                        'time': current_time,
                        'symbol': symbol,
                        'action': 'CLOSE',
                        'reason': exit_reason,
                        'pnl': pnl,
                        'pnl_pct': pnl_pct * 100
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
                            'quantity': quantity,
                            'entry_time': current_time
                        }
                        
                        trades_log.append({
                            'time': current_time,
                            'symbol': symbol,
                            'action': 'OPEN',
                            'signal': signal
                        })
    
    # Close remaining positions
    final_time = timeline[-1]
    for symbol, position in list(positions.items()):
        if final_time in historical_data[symbol].index:
            current_price = historical_data[symbol].loc[final_time, 'Close']
            pnl = (current_price - position['entry_price']) * position['quantity']
            pnl_pct = (current_price - position['entry_price']) / position['entry_price']
            capital += pnl
            
            trades_log.append({
                'time': final_time,
                'symbol': symbol,
                'action': 'CLOSE',
                'reason': 'END',
                'pnl': pnl,
                'pnl_pct': pnl_pct * 100
            })
    
    # Calculate results
    final_capital = capital
    total_return = (final_capital - initial_capital) / initial_capital * 100
    
    closed_trades = [t for t in trades_log if t['action'] == 'CLOSE' and 'pnl' in t]
    winning_trades = [t for t in closed_trades if t['pnl'] > 0]
    losing_trades = [t for t in closed_trades if t['pnl'] < 0]
    total_closed = len(closed_trades)
    win_rate = (len(winning_trades) / total_closed * 100) if total_closed > 0 else 0
    
    # Calculate max drawdown
    equity_curve = [initial_capital]
    running_capital = initial_capital
    for trade in closed_trades:
        running_capital += trade['pnl']
        equity_curve.append(running_capital)
    
    peak = initial_capital
    max_drawdown = 0
    for equity in equity_curve:
        if equity > peak:
            peak = equity
        drawdown = (peak - equity) / peak * 100
        if drawdown > max_drawdown:
            max_drawdown = drawdown
    
    # Profit factor
    total_profit = sum(t['pnl'] for t in winning_trades) if winning_trades else 0
    total_loss = abs(sum(t['pnl'] for t in losing_trades)) if losing_trades else 1
    profit_factor = total_profit / total_loss if total_loss > 0 else 0
    
    return {
        'final_capital': final_capital,
        'total_return': total_return,
        'total_trades': len(trades_log),
        'closed_trades': total_closed,
        'winning_trades': len(winning_trades),
        'losing_trades': len(losing_trades),
        'win_rate': win_rate,
        'max_drawdown': max_drawdown,
        'profit_factor': profit_factor,
        'avg_win': sum(t['pnl'] for t in winning_trades) / len(winning_trades) if winning_trades else 0,
        'avg_loss': sum(t['pnl'] for t in losing_trades) / len(losing_trades) if losing_trades else 0
    }


def run_fast_hyperopt():
    """
    Run fast hyperparameter optimization (no LLM calls)
    """
    print("=" * 80)
    print("FAST HYPERPARAMETER OPTIMIZATION - TECHNICAL SIGNALS")
    print("=" * 80)
    print()
    
    # Fetch historical data
    symbols = ["BTC-USD", "ETH-USD", "SOL-USD", "AVAX-USD", "BNB-USD"]
    end_date = datetime.now()
    start_date = end_date - timedelta(days=21)  # 3 weeks
    
    print(f"📊 Fetching data for {len(symbols)} symbols...")
    print(f"Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    print()
    
    historical_data = {}
    for symbol in symbols:
        print(f"  Fetching {symbol}...", end=" ")
        df = fetch_historical_data(symbol, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"), interval="1h")
        if len(df) > 0:
            historical_data[symbol] = df
            print(f"✅ {len(df)} candles")
    
    allocations = {
        "BTC-USD": 0.25,
        "ETH-USD": 0.20,
        "SOL-USD": 0.15,
        "AVAX-USD": 0.15,
        "BNB-USD": 0.15
    }
    
    print()
    print("=" * 80)
    print("PARAMETER SEARCH SPACE")
    print("=" * 80)
    
    # Define parameter grid
    param_grid = {
        'initial_capital': [10000],
        'leverage': [3, 5, 7, 10],
        'signal_threshold': [0.2, 0.3, 0.4, 0.5],
        'stop_loss_pct': [0.02, 0.03, 0.05, 0.07],
        'take_profit_pct': [0.06, 0.08, 0.10, 0.15],
        'lookback_periods': [50, 75, 100, 150]
    }
    
    print(f"Leverage: {param_grid['leverage']}")
    print(f"Signal Threshold: {param_grid['signal_threshold']}")
    print(f"Stop Loss: {[f'{x*100:.0f}%' for x in param_grid['stop_loss_pct']]}")
    print(f"Take Profit: {[f'{x*100:.0f}%' for x in param_grid['take_profit_pct']]}")
    print(f"Lookback Periods: {param_grid['lookback_periods']}")
    print()
    
    # Calculate total combinations
    total_combinations = 1
    for key, values in param_grid.items():
        total_combinations *= len(values)
    
    print(f"Total combinations to test: {total_combinations}")
    print(f"Estimated time: ~{total_combinations * 0.5 / 60:.1f} minutes")
    print("=" * 80)
    print()
    
    # Generate all parameter combinations
    param_names = list(param_grid.keys())
    param_values = [param_grid[name] for name in param_names]
    
    results = []
    best_return = -float('inf')
    
    # Test each combination
    for i, combination in enumerate(product(*param_values), 1):
        params = dict(zip(param_names, combination))
        
        if i % 50 == 1:
            print(f"\n[{i}/{total_combinations}] Testing configuration:")
            print(f"  Leverage: {params['leverage']}x, Signal: {params['signal_threshold']}, SL: {params['stop_loss_pct']*100:.0f}%, TP: {params['take_profit_pct']*100:.0f}%, Lookback: {params['lookback_periods']}")
        
        try:
            result = run_fast_backtest(historical_data, params, allocations)
            result['params'] = params
            results.append(result)
            
            if i % 50 == 0:
                print(f"  → Return: {result['total_return']:+.2f}% | Win Rate: {result['win_rate']:.1f}% | Trades: {result['closed_trades']}")
            
            # Track best
            if result['total_return'] > best_return:
                best_return = result['total_return']
                if result['total_return'] > 0:
                    print(f"  ✨ NEW BEST: {result['total_return']:+.2f}% return!")
        
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
            continue
    
    # Print results
    print()
    print("=" * 80)
    print("OPTIMIZATION COMPLETE!")
    print("=" * 80)
    print()
    
    # Sort by return
    results.sort(key=lambda x: x['total_return'], reverse=True)
    
    print("TOP 15 CONFIGURATIONS:")
    print("-" * 80)
    print(f"{'#':<3} {'Return':<9} {'WinRate':<9} {'Trades':<7} {'MaxDD':<8} {'PF':<6} {'Lev':<4} {'Sig':<5} {'SL':<5} {'TP':<5}")
    print("-" * 80)
    
    for i, result in enumerate(results[:15], 1):
        p = result['params']
        print(f"{i:<3} {result['total_return']:>+7.2f}% {result['win_rate']:>6.1f}% {result['closed_trades']:>6} {result['max_drawdown']:>6.1f}% {result['profit_factor']:>5.2f} {p['leverage']:>3}x {p['signal_threshold']:>4.2f} {p['stop_loss_pct']*100:>3.0f}% {p['take_profit_pct']*100:>3.0f}%")
    
    best_result = results[0]
    best_params = best_result['params']
    
    print()
    print("=" * 80)
    print("BEST CONFIGURATION")
    print("=" * 80)
    print(f"Total Return:       {best_result['total_return']:+.2f}%")
    print(f"Win Rate:           {best_result['win_rate']:.1f}%")
    print(f"Total Trades:       {best_result['closed_trades']}")
    print(f"Winning Trades:     {best_result['winning_trades']}")
    print(f"Losing Trades:      {best_result['losing_trades']}")
    print(f"Max Drawdown:       {best_result['max_drawdown']:.2f}%")
    print(f"Profit Factor:      {best_result['profit_factor']:.2f}")
    if best_result['avg_win'] != 0:
        print(f"Average Win:        ${best_result['avg_win']:,.2f}")
    if best_result['avg_loss'] != 0:
        print(f"Average Loss:       ${best_result['avg_loss']:,.2f}")
    print()
    print("Optimal Parameters:")
    print(f"  Leverage:           {best_params['leverage']}x")
    print(f"  Signal Threshold:   {best_params['signal_threshold']}")
    print(f"  Stop Loss:          {best_params['stop_loss_pct']*100:.0f}%")
    print(f"  Take Profit:        {best_params['take_profit_pct']*100:.0f}%")
    print(f"  Lookback Periods:   {best_params['lookback_periods']}")
    print()
    
    # Save results
    output_file = 'hyperopt_fast_results.json'
    with open(output_file, 'w') as f:
        json.dump({
            'best_params': best_params,
            'best_result': {k: v for k, v in best_result.items() if k != 'params'},
            'top_20': [{
                'params': r['params'],
                'return': r['total_return'],
                'win_rate': r['win_rate'],
                'trades': r['closed_trades'],
                'max_drawdown': r['max_drawdown']
            } for r in results[:20]]
        }, f, indent=2, default=str)
    
    print(f"💾 Results saved to {output_file}")
    print("=" * 80)
    
    return best_params, best_result, results


if __name__ == "__main__":
    best_params, best_result, all_results = run_fast_hyperopt()
