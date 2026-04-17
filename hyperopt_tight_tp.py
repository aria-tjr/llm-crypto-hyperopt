"""
Intensive Hyperopt for Tighter TP/SL with Higher Trade Frequency
Optimizes: Take Profit, Stop Loss, Signal Threshold, Leverage
Goal: More frequent trades with better win rate
"""

import optuna
from optuna.samplers import TPESampler
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.components.bybit_connector import BybitConnector
from src.components.signal_generator import generate_trading_signal

# Load configuration
import configparser
config = configparser.ConfigParser()
config.read('src/config.ini')

API_KEY = config.get('bybit', 'api_key')
API_SECRET = config.get('bybit', 'api_secret')
IS_DEMO = config.getboolean('bybit', 'demo', fallback=True)

# Test symbols (diverse volatility)
TEST_SYMBOLS = [
    'BTCUSDT',   # Low volatility
    'ETHUSDT',   # Low-medium volatility
    'SOLUSDT',   # Medium volatility
    'DOGEUSDT',  # High volatility
    'AVAXUSDT',  # Medium volatility
    'LINKUSDT',  # Medium volatility
]

def fetch_historical_data(symbol, interval='60', limit=500):
    """Fetch historical kline data"""
    bybit = BybitConnector(API_KEY, API_SECRET, demo=IS_DEMO)
    
    try:
        klines = bybit.session.get_kline(
            category="linear",
            symbol=symbol,
            interval=interval,
            limit=limit
        )
        
        if klines and klines.get('retCode') == 0:
            data = klines['result']['list']
            # Convert to DataFrame [timestamp, open, high, low, close, volume, turnover]
            df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'turnover'])
            df['timestamp'] = pd.to_datetime(df['timestamp'].astype(float), unit='ms')
            df[['open', 'high', 'low', 'close', 'volume']] = df[['open', 'high', 'low', 'close', 'volume']].astype(float)
            df = df.sort_values('timestamp').reset_index(drop=True)
            return df
    except Exception as e:
        print(f"Error fetching {symbol}: {e}")
    
    return None

def backtest_strategy(params, data_dict):
    """
    Backtest trading strategy with given parameters
    
    Returns: dict with performance metrics
    """
    take_profit_pct = params['take_profit_pct']
    stop_loss_pct = params['stop_loss_pct']
    signal_threshold = params['signal_threshold']
    leverage = params['leverage']
    lookback = params['lookback']
    
    # Track performance
    total_trades = 0
    winning_trades = 0
    total_return = 0.0
    max_drawdown = 0.0
    equity_curve = [1.0]  # Start with 1.0 (100%)
    
    for symbol, df in data_dict.items():
        if df is None or len(df) < lookback + 50:
            continue
        
        # Simulate trading
        position = None
        entry_price = 0
        
        for i in range(lookback, len(df) - 1):
            prices = df['close'].iloc[i-lookback:i].values
            current_price = df['close'].iloc[i]
            
            # Generate signal
            signal_data = generate_trading_signal(prices)
            signal_strength = abs(signal_data['signal'])
            action = signal_data['action']
            
            # Invert signals (strategy uses inverted signals)
            if action == 'BUY':
                action = 'SELL'
            elif action == 'SELL':
                action = 'BUY'
            
            # Check if we have a position
            if position is not None:
                # Check exit conditions
                pnl_pct = (current_price - entry_price) / entry_price
                
                if position == 'LONG':
                    # Take profit or stop loss
                    if pnl_pct >= take_profit_pct:
                        # Win
                        profit = pnl_pct * leverage
                        total_return += profit
                        winning_trades += 1
                        total_trades += 1
                        position = None
                        equity_curve.append(equity_curve[-1] * (1 + profit))
                    elif pnl_pct <= -stop_loss_pct:
                        # Loss
                        loss = pnl_pct * leverage
                        total_return += loss
                        total_trades += 1
                        position = None
                        equity_curve.append(equity_curve[-1] * (1 + loss))
                
                elif position == 'SHORT':
                    pnl_pct = -pnl_pct  # Inverse for short
                    if pnl_pct >= take_profit_pct:
                        # Win
                        profit = pnl_pct * leverage
                        total_return += profit
                        winning_trades += 1
                        total_trades += 1
                        position = None
                        equity_curve.append(equity_curve[-1] * (1 + profit))
                    elif pnl_pct <= -stop_loss_pct:
                        # Loss
                        loss = pnl_pct * leverage
                        total_return += loss
                        total_trades += 1
                        position = None
                        equity_curve.append(equity_curve[-1] * (1 + loss))
            
            # Check for entry
            if position is None and signal_strength >= signal_threshold:
                if action == 'BUY':
                    position = 'LONG'
                    entry_price = current_price
                elif action == 'SELL':
                    position = 'SHORT'
                    entry_price = current_price
    
    # Calculate metrics
    if total_trades == 0:
        return {
            'total_return': -100.0,  # Penalize no trades
            'total_trades': 0,
            'win_rate': 0.0,
            'max_drawdown': 0.0,
            'sharpe_ratio': -10.0,
            'profit_factor': 0.0
        }
    
    # Calculate max drawdown
    peak = equity_curve[0]
    for equity in equity_curve:
        if equity > peak:
            peak = equity
        drawdown = (peak - equity) / peak
        if drawdown > max_drawdown:
            max_drawdown = drawdown
    
    win_rate = winning_trades / total_trades if total_trades > 0 else 0
    
    # Calculate Sharpe ratio (simplified)
    returns = np.diff(equity_curve) / np.array(equity_curve[:-1])
    sharpe_ratio = np.mean(returns) / np.std(returns) if np.std(returns) > 0 else 0
    sharpe_ratio = sharpe_ratio * np.sqrt(252)  # Annualized
    
    # Profit factor
    wins = [r for r in returns if r > 0]
    losses = [abs(r) for r in returns if r < 0]
    profit_factor = sum(wins) / sum(losses) if sum(losses) > 0 else 0
    
    return {
        'total_return': total_return * 100,  # As percentage
        'total_trades': total_trades,
        'win_rate': win_rate * 100,
        'max_drawdown': max_drawdown * 100,
        'sharpe_ratio': sharpe_ratio,
        'profit_factor': profit_factor
    }

def objective(trial):
    """Optuna objective function"""
    
    # Parameters to optimize
    params = {
        'take_profit_pct': trial.suggest_float('take_profit_pct', 0.025, 0.08, step=0.005),  # 2.5% to 8%
        'stop_loss_pct': trial.suggest_float('stop_loss_pct', 0.015, 0.04, step=0.005),     # 1.5% to 4%
        'signal_threshold': trial.suggest_float('signal_threshold', 0.35, 0.65, step=0.05),  # Lower threshold = more trades
        'leverage': trial.suggest_int('leverage', 5, 12),                                     # 5x to 12x
        'lookback': trial.suggest_categorical('lookback', [100, 150, 200, 250]),             # Lookback periods
    }
    
    # Run backtest
    results = backtest_strategy(params, data_cache)
    
    # Multi-objective optimization
    # Prioritize: Total Return, Win Rate, Trade Frequency, Low Drawdown
    total_return = results['total_return']
    win_rate = results['win_rate']
    total_trades = results['total_trades']
    max_drawdown = results['max_drawdown']
    sharpe_ratio = results['sharpe_ratio']
    
    # Calculate composite score
    # Goal: High return, high win rate, decent trade count, low drawdown
    trade_frequency_bonus = min(total_trades / 50, 2.0)  # Bonus for more trades (cap at 2x)
    win_rate_bonus = (win_rate / 100) * 2.0  # 2x multiplier for win rate
    drawdown_penalty = max_drawdown / 100  # Penalty for drawdown
    
    # Risk-reward ratio check
    risk_reward = params['take_profit_pct'] / params['stop_loss_pct']
    if risk_reward < 1.2:  # TP should be at least 1.2x SL
        return -1000.0
    
    # Composite score
    score = (
        total_return * 0.4 +           # 40% weight on returns
        win_rate * 0.3 +                # 30% weight on win rate
        trade_frequency_bonus * 10 +    # Bonus for trade frequency
        sharpe_ratio * 5 -              # Sharpe ratio bonus
        drawdown_penalty * 20           # Drawdown penalty
    )
    
    # Store results for analysis
    trial.set_user_attr('total_return', total_return)
    trial.set_user_attr('win_rate', win_rate)
    trial.set_user_attr('total_trades', total_trades)
    trial.set_user_attr('max_drawdown', max_drawdown)
    trial.set_user_attr('sharpe_ratio', sharpe_ratio)
    trial.set_user_attr('risk_reward', risk_reward)
    
    return score

if __name__ == "__main__":
    print("="*80)
    print("  INTENSIVE HYPEROPT: TIGHTER TP/SL + HIGHER FREQUENCY")
    print("="*80)
    print()
    
    # Fetch data for all test symbols
    print("📊 Fetching historical data...")
    data_cache = {}
    for symbol in TEST_SYMBOLS:
        print(f"  Loading {symbol}...", end=" ")
        df = fetch_historical_data(symbol, interval='60', limit=500)
        if df is not None:
            data_cache[symbol] = df
            print(f"✅ {len(df)} candles")
        else:
            print("❌ Failed")
    
    print(f"\n✅ Loaded {len(data_cache)} symbols")
    print()
    
    # Create Optuna study
    print("🔬 Starting hyperparameter optimization...")
    print(f"   Parameters:")
    print(f"   - Take Profit: 2.5% to 8%")
    print(f"   - Stop Loss: 1.5% to 4%")
    print(f"   - Signal Threshold: 0.35 to 0.65")
    print(f"   - Leverage: 5x to 12x")
    print(f"   - Lookback: 100/150/200/250")
    print()
    
    study = optuna.create_study(
        direction='maximize',
        sampler=TPESampler(seed=42)
    )
    
    # Run optimization
    n_trials = 300  # Intensive optimization
    study.optimize(objective, n_trials=n_trials, show_progress_bar=True)
    
    # Get best results
    best_trial = study.best_trial
    best_params = best_trial.params
    
    print()
    print("="*80)
    print("  OPTIMIZATION COMPLETE")
    print("="*80)
    print()
    print("🏆 BEST PARAMETERS:")
    print(f"   Take Profit: {best_params['take_profit_pct']*100:.2f}%")
    print(f"   Stop Loss: {best_params['stop_loss_pct']*100:.2f}%")
    print(f"   Risk:Reward Ratio: {best_params['take_profit_pct']/best_params['stop_loss_pct']:.2f}:1")
    print(f"   Signal Threshold: {best_params['signal_threshold']:.3f}")
    print(f"   Leverage: {best_params['leverage']}x")
    print(f"   Lookback: {best_params['lookback']}")
    print()
    print("📊 PERFORMANCE METRICS:")
    print(f"   Total Return: {best_trial.user_attrs['total_return']:+.2f}%")
    print(f"   Win Rate: {best_trial.user_attrs['win_rate']:.1f}%")
    print(f"   Total Trades: {best_trial.user_attrs['total_trades']}")
    print(f"   Max Drawdown: {best_trial.user_attrs['max_drawdown']:.2f}%")
    print(f"   Sharpe Ratio: {best_trial.user_attrs['sharpe_ratio']:.2f}")
    print(f"   Composite Score: {best_trial.value:.2f}")
    print()
    
    # Compare with current settings
    print("📈 COMPARISON WITH CURRENT SETTINGS:")
    print(f"   Current TP: 9.79% → New TP: {best_params['take_profit_pct']*100:.2f}% ({((best_params['take_profit_pct'] - 0.0979) / 0.0979 * 100):+.1f}%)")
    print(f"   Current SL: 3.45% → New SL: {best_params['stop_loss_pct']*100:.2f}% ({((best_params['stop_loss_pct'] - 0.0345) / 0.0345 * 100):+.1f}%)")
    print(f"   Current Threshold: 0.560 → New: {best_params['signal_threshold']:.3f} ({((best_params['signal_threshold'] - 0.560) / 0.560 * 100):+.1f}%)")
    print(f"   Current Leverage: 9x → New: {best_params['leverage']}x ({((best_params['leverage'] - 9) / 9 * 100):+.1f}%)")
    print()
    
    # Save results
    results = {
        'timestamp': datetime.now().isoformat(),
        'n_trials': n_trials,
        'best_params': best_params,
        'best_metrics': {
            'total_return': best_trial.user_attrs['total_return'],
            'win_rate': best_trial.user_attrs['win_rate'],
            'total_trades': best_trial.user_attrs['total_trades'],
            'max_drawdown': best_trial.user_attrs['max_drawdown'],
            'sharpe_ratio': best_trial.user_attrs['sharpe_ratio'],
            'risk_reward': best_trial.user_attrs['risk_reward'],
            'composite_score': best_trial.value
        }
    }
    
    with open('hyperopt_tight_tp_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print("💾 Results saved to: hyperopt_tight_tp_results.json")
    print()
    print("="*80)
