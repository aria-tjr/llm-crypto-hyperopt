"""
Intensive Hyperparameter Optimization for Hybrid LLM Trading System
Tests different configurations to find optimal parameters
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from src.components.signal_generator import generate_trading_signal
from src.components.llm_signal_analyzer import get_hybrid_signal
from itertools import product
import json


def fetch_historical_data(symbol, start_date, end_date, interval="1h"):
    """Fetch historical price data"""
    ticker = yf.Ticker(symbol)
    df = ticker.history(start=start_date, end=end_date, interval=interval)
    return df


def run_backtest_with_params(historical_data, params, allocations):
    """
    Run backtest with specific parameters
    
    Args:
        historical_data: Dict of symbol -> DataFrame
        params: Dict with configuration
        allocations: Dict of symbol -> allocation %
        
    Returns:
        Dict with results
    """
    initial_capital = params['initial_capital']
    leverage = params['leverage']
    confidence_threshold = params['confidence_threshold']
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
            
            # Generate technical signals
            signal_data = generate_trading_signal(prices)
            allocation = allocations.get(symbol, 0)
            
            # Check existing position
            if symbol in positions:
                position = positions[symbol]
                entry_price = position['entry_price']
                pnl_pct = (current_price - entry_price) / entry_price
                
                # Build market context
                market_context = {
                    'has_position': True,
                    'side': 'Buy',
                    'entry_price': entry_price,
                    'pnl_pct': pnl_pct * 100
                }
                
                # Get LLM analysis
                hybrid_result = get_hybrid_signal(signal_data, symbol, current_price, market_context)
                llm_decision = hybrid_result['final_decision']
                confidence = hybrid_result['confidence']
                
                # Check exit conditions
                should_exit = False
                exit_reason = ""
                
                if llm_decision == 'SELL' and confidence >= confidence_threshold:
                    should_exit = True
                    exit_reason = "LLM_SELL"
                elif pnl_pct >= take_profit_pct:
                    should_exit = True
                    exit_reason = "TAKE_PROFIT"
                elif pnl_pct <= -stop_loss_pct:
                    should_exit = True
                    exit_reason = "STOP_LOSS"
                
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
                # No position
                market_context = {'has_position': False}
                
                # Get LLM analysis
                hybrid_result = get_hybrid_signal(signal_data, symbol, current_price, market_context)
                llm_decision = hybrid_result['final_decision']
                confidence = hybrid_result['confidence']
                
                if llm_decision == 'BUY' and confidence >= confidence_threshold:
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
                            'confidence': confidence
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
    
    # Sharpe ratio approximation
    if closed_trades:
        returns = [t['pnl_pct'] for t in closed_trades]
        avg_return = sum(returns) / len(returns)
        std_return = (sum((r - avg_return) ** 2 for r in returns) / len(returns)) ** 0.5
        sharpe = (avg_return / std_return) if std_return > 0 else 0
    else:
        sharpe = 0
    
    return {
        'final_capital': final_capital,
        'total_return': total_return,
        'total_trades': len(trades_log),
        'closed_trades': total_closed,
        'winning_trades': len(winning_trades),
        'losing_trades': len(losing_trades),
        'win_rate': win_rate,
        'max_drawdown': max_drawdown,
        'sharpe_ratio': sharpe,
        'avg_win': sum(t['pnl'] for t in winning_trades) / len(winning_trades) if winning_trades else 0,
        'avg_loss': sum(t['pnl'] for t in losing_trades) / len(losing_trades) if losing_trades else 0
    }


def run_intensive_hyperopt():
    """
    Run intensive hyperparameter optimization
    """
    print("=" * 80)
    print("INTENSIVE HYPERPARAMETER OPTIMIZATION - HYBRID LLM SYSTEM")
    print("=" * 80)
    print()
    
    # Fetch historical data
    symbols = ["BTC-USD", "ETH-USD"]
    end_date = datetime.now()
    start_date = end_date - timedelta(days=14)  # 2 weeks
    
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
        "BTC-USD": 0.50,
        "ETH-USD": 0.50
    }
    
    print()
    print("=" * 80)
    print("PARAMETER SEARCH SPACE")
    print("=" * 80)
    
    # Define parameter grid
    param_grid = {
        'initial_capital': [10000],
        'leverage': [3, 5, 7],
        'confidence_threshold': [50, 60, 70, 80],
        'stop_loss_pct': [0.03, 0.05, 0.07],
        'take_profit_pct': [0.06, 0.08, 0.10, 0.12],
        'lookback_periods': [50, 100, 150]
    }
    
    print(f"Leverage: {param_grid['leverage']}")
    print(f"Confidence Threshold: {param_grid['confidence_threshold']}%")
    print(f"Stop Loss: {[f'{x*100:.0f}%' for x in param_grid['stop_loss_pct']]}")
    print(f"Take Profit: {[f'{x*100:.0f}%' for x in param_grid['take_profit_pct']]}")
    print(f"Lookback Periods: {param_grid['lookback_periods']}")
    print()
    
    # Calculate total combinations
    total_combinations = 1
    for key, values in param_grid.items():
        total_combinations *= len(values)
    
    print(f"Total combinations to test: {total_combinations}")
    print()
    print("⚠️  This will take 30-60 minutes due to LLM API calls...")
    print("=" * 80)
    print()
    
    # Generate all parameter combinations
    param_names = list(param_grid.keys())
    param_values = [param_grid[name] for name in param_names]
    
    results = []
    best_result = None
    best_params = None
    best_return = -float('inf')
    
    # Test each combination
    for i, combination in enumerate(product(*param_values), 1):
        params = dict(zip(param_names, combination))
        
        print(f"\n[{i}/{total_combinations}] Testing configuration:")
        print(f"  Leverage: {params['leverage']}x")
        print(f"  Confidence: {params['confidence_threshold']}%")
        print(f"  Stop Loss: {params['stop_loss_pct']*100:.0f}%")
        print(f"  Take Profit: {params['take_profit_pct']*100:.0f}%")
        print(f"  Lookback: {params['lookback_periods']}")
        
        try:
            result = run_backtest_with_params(historical_data, params, allocations)
            result['params'] = params
            results.append(result)
            
            print(f"  → Return: {result['total_return']:+.2f}% | Win Rate: {result['win_rate']:.1f}% | Trades: {result['closed_trades']} | Drawdown: {result['max_drawdown']:.1f}%")
            
            # Track best result
            if result['total_return'] > best_return:
                best_return = result['total_return']
                best_result = result
                best_params = params
                print(f"  ✨ NEW BEST RESULT! ✨")
        
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
            continue
    
    # Print results
    print()
    print("=" * 80)
    print("OPTIMIZATION RESULTS")
    print("=" * 80)
    print()
    
    # Sort by return
    results.sort(key=lambda x: x['total_return'], reverse=True)
    
    print("TOP 10 CONFIGURATIONS:")
    print("-" * 80)
    print(f"{'Rank':<5} {'Return':<10} {'WinRate':<10} {'Trades':<8} {'Drawdown':<10} {'Leverage':<8} {'Conf':<6} {'SL':<6} {'TP':<6}")
    print("-" * 80)
    
    for i, result in enumerate(results[:10], 1):
        p = result['params']
        print(f"{i:<5} {result['total_return']:>+7.2f}%  {result['win_rate']:>6.1f}%  {result['closed_trades']:>6}  {result['max_drawdown']:>6.1f}%  {p['leverage']:>5}x  {p['confidence_threshold']:>4}%  {p['stop_loss_pct']*100:>4.0f}%  {p['take_profit_pct']*100:>4.0f}%")
    
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
    print(f"Sharpe Ratio:       {best_result['sharpe_ratio']:.2f}")
    if best_result['avg_win'] != 0:
        print(f"Average Win:        ${best_result['avg_win']:,.2f}")
    if best_result['avg_loss'] != 0:
        print(f"Average Loss:       ${best_result['avg_loss']:,.2f}")
    print()
    print("Parameters:")
    print(f"  Leverage:           {best_params['leverage']}x")
    print(f"  Confidence:         {best_params['confidence_threshold']}%")
    print(f"  Stop Loss:          {best_params['stop_loss_pct']*100:.0f}%")
    print(f"  Take Profit:        {best_params['take_profit_pct']*100:.0f}%")
    print(f"  Lookback Periods:   {best_params['lookback_periods']}")
    print()
    
    # Save results to JSON
    output_file = 'hyperopt_results.json'
    with open(output_file, 'w') as f:
        json.dump({
            'best_params': best_params,
            'best_result': {k: v for k, v in best_result.items() if k != 'params'},
            'all_results': [{k: v for k, v in r.items() if k != 'params'} for r in results[:20]]
        }, f, indent=2, default=str)
    
    print(f"💾 Results saved to {output_file}")
    print("=" * 80)
    
    return best_params, best_result, results


if __name__ == "__main__":
    best_params, best_result, all_results = run_intensive_hyperopt()
