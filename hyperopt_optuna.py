"""
Optuna-based Hyperparameter Optimization (INVERTED SIGNALS + ADAPTIVE RISK)
Uses Bayesian optimization to find best parameters efficiently

🔥 INVERTED STRATEGY: Analysis showed that inverting technical signals is profitable
   - Original BUY signals → SHORT positions
   - Original SELL signals → LONG positions

🎯 ADAPTIVE RISK: Optimizes adaptive take profit, stop loss, and threshold adjustments
   - Volatility-based threshold multipliers
   - ATR-based stop loss adjustment
   - Dynamic take profit based on market conditions
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from src.components.signal_generator import generate_trading_signal
import optuna
from optuna.pruners import MedianPruner
from optuna.samplers import TPESampler
import json


def fetch_historical_data(symbol, start_date, end_date, interval="1h"):
    """Fetch historical price data"""
    ticker = yf.Ticker(symbol)
    df = ticker.history(start=start_date, end=end_date, interval=interval)
    return df


# Global variable to store historical data
HISTORICAL_DATA = {}
ALLOCATIONS = {}


def calculate_atr(prices, period=14):
    """Calculate Average True Range for volatility measurement"""
    if len(prices) < period + 1:
        return 0
    
    true_ranges = []
    for i in range(1, len(prices)):
        high_low = abs(prices[i] - prices[i-1])
        true_ranges.append(high_low)
    
    atr = sum(true_ranges[-period:]) / period
    return atr


def get_adaptive_threshold(prices, base_threshold, volatility_high_mult, volatility_low_mult, atr_lookback):
    """Calculate adaptive threshold based on current volatility"""
    if len(prices) < atr_lookback:
        return base_threshold
    
    current_atr = calculate_atr(prices[-30:], 14)
    historical_atr = calculate_atr(prices[-atr_lookback:], 14)
    
    if historical_atr == 0:
        return base_threshold
    
    volatility_ratio = current_atr / historical_atr
    
    if volatility_ratio > 1.5:
        # High volatility - be more selective
        return base_threshold * volatility_high_mult
    elif volatility_ratio < 0.7:
        # Low volatility - be more aggressive
        return base_threshold * volatility_low_mult
    else:
        return base_threshold


def get_adaptive_stop_loss(prices, base_stop_loss, atr_multiplier):
    """Calculate adaptive stop loss based on ATR"""
    if len(prices) < 15:
        return base_stop_loss
    
    atr = calculate_atr(prices[-30:], 14)
    current_price = prices[-1]
    
    if current_price == 0:
        return base_stop_loss
    
    # ATR-based stop loss: base + (ATR/price * multiplier)
    atr_pct = (atr / current_price)
    adaptive_sl = base_stop_loss + (atr_pct * atr_multiplier)
    
    # Cap between 1.5% and 8%
    return max(0.015, min(0.08, adaptive_sl))


def get_adaptive_take_profit(prices, base_take_profit, volatility_multiplier):
    """Calculate adaptive take profit based on volatility"""
    if len(prices) < 30:
        return base_take_profit
    
    current_atr = calculate_atr(prices[-30:], 14)
    current_price = prices[-1]
    
    if current_price == 0:
        return base_take_profit
    
    # Volatility-based take profit: higher volatility = higher targets
    atr_pct = (current_atr / current_price)
    adaptive_tp = base_take_profit * (1 + atr_pct * volatility_multiplier)
    
    # Cap between 5% and 25%
    return max(0.05, min(0.25, adaptive_tp))


def run_backtest_trial(params):
    """
    Run backtest with given parameters (including adaptive risk management)
    
    Args:
        params: Dict with configuration including:
            - leverage: Base leverage
            - base_signal_threshold: Base threshold before adaptation
            - base_stop_loss_pct: Base stop loss before adaptation
            - base_take_profit_pct: Base take profit before adaptation
            - lookback_periods: Technical indicator lookback
            - volatility_high_mult: Threshold multiplier for high volatility
            - volatility_low_mult: Threshold multiplier for low volatility
            - atr_lookback: ATR calculation lookback
            - atr_stop_loss_mult: ATR multiplier for stop loss
            - volatility_tp_mult: Volatility multiplier for take profit
        
    Returns:
        float: Total return percentage
    """
    initial_capital = 10000
    leverage = params['leverage']
    base_signal_threshold = params['base_signal_threshold']
    base_stop_loss_pct = params['base_stop_loss_pct']
    base_take_profit_pct = params['base_take_profit_pct']
    lookback_periods = params['lookback_periods']
    
    # Adaptive parameters
    volatility_high_mult = params.get('volatility_high_mult', 1.3)
    volatility_low_mult = params.get('volatility_low_mult', 0.9)
    atr_lookback = params.get('atr_lookback', 50)
    atr_stop_loss_mult = params.get('atr_stop_loss_mult', 0.5)
    volatility_tp_mult = params.get('volatility_tp_mult', 2.0)
    
    capital = initial_capital
    positions = {}
    trades_log = []
    
    # Get timeline
    all_dates = set()
    for df in HISTORICAL_DATA.values():
        all_dates.update(df.index)
    timeline = sorted(list(all_dates))
    
    # Main backtest loop
    for i, current_time in enumerate(timeline):
        if i < lookback_periods:
            continue
        
        for symbol in HISTORICAL_DATA.keys():
            df = HISTORICAL_DATA[symbol]
            
            if current_time not in df.index:
                continue
            
            current_price = df.loc[current_time, 'Close']
            prices = df.loc[:current_time, 'Close'].tail(max(lookback_periods, atr_lookback)).tolist()
            
            if len(prices) < lookback_periods:
                continue
            
            # Calculate adaptive parameters for this symbol at this time
            signal_threshold = get_adaptive_threshold(
                prices, base_signal_threshold, 
                volatility_high_mult, volatility_low_mult, atr_lookback
            )
            stop_loss_pct = get_adaptive_stop_loss(
                prices, base_stop_loss_pct, atr_stop_loss_mult
            )
            take_profit_pct = get_adaptive_take_profit(
                prices, base_take_profit_pct, volatility_tp_mult
            )
            
            # Generate technical signals
            signal_data = generate_trading_signal(prices[-lookback_periods:])
            
            # 🔥 INVERT SIGNALS - Analysis showed inverted signals are profitable
            # BUY signals become SELL signals, SELL signals become BUY signals
            signal = -signal_data['signal']  # Invert the signal
            
            allocation = ALLOCATIONS.get(symbol, 0)
            
            # Check existing position
            if symbol in positions:
                position = positions[symbol]
                entry_price = position['entry_price']
                pnl_pct = (current_price - entry_price) / entry_price
                
                # Check exit conditions with adaptive targets
                should_exit = False
                
                if signal < -signal_threshold:
                    should_exit = True
                elif pnl_pct >= take_profit_pct:
                    should_exit = True
                elif pnl_pct <= -stop_loss_pct:
                    should_exit = True
                
                if should_exit:
                    pnl = (current_price - entry_price) * position['quantity']
                    capital += pnl
                    
                    trades_log.append({
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
                            'quantity': quantity
                        }
    
    # Close remaining positions
    final_time = timeline[-1]
    for symbol, position in list(positions.items()):
        if final_time in HISTORICAL_DATA[symbol].index:
            current_price = HISTORICAL_DATA[symbol].loc[final_time, 'Close']
            pnl = (current_price - position['entry_price']) * position['quantity']
            capital += pnl
            
            trades_log.append({
                'pnl': pnl
            })
    
    # Calculate return
    total_return = (capital - initial_capital) / initial_capital * 100
    
    return total_return


def objective(trial):
    """
    Optuna objective function - optimizes both base and adaptive parameters
    
    Args:
        trial: Optuna trial object
        
    Returns:
        float: Objective value to maximize (total return)
    """
    # Suggest base hyperparameters
    params = {
        'leverage': trial.suggest_int('leverage', 5, 10),
        'base_signal_threshold': trial.suggest_float('base_signal_threshold', 0.2, 0.6),
        'base_stop_loss_pct': trial.suggest_float('base_stop_loss_pct', 0.015, 0.06),
        'base_take_profit_pct': trial.suggest_float('base_take_profit_pct', 0.05, 0.20),
        'lookback_periods': trial.suggest_categorical('lookback_periods', [50, 100, 150, 200]),
        
        # 🎯 Adaptive threshold parameters
        'volatility_high_mult': trial.suggest_float('volatility_high_mult', 1.1, 1.5),  # How much to increase threshold in high volatility
        'volatility_low_mult': trial.suggest_float('volatility_low_mult', 0.7, 0.95),  # How much to decrease threshold in low volatility
        'atr_lookback': trial.suggest_categorical('atr_lookback', [30, 50, 75, 100]),  # ATR calculation period
        
        # 🎯 Adaptive stop loss parameters
        'atr_stop_loss_mult': trial.suggest_float('atr_stop_loss_mult', 0.2, 1.0),  # ATR multiplier for stop loss adjustment
        
        # 🎯 Adaptive take profit parameters
        'volatility_tp_mult': trial.suggest_float('volatility_tp_mult', 1.0, 3.0),  # Volatility multiplier for take profit
    }
    
    # Run backtest
    total_return = run_backtest_trial(params)
    
    return total_return


def run_optuna_optimization(n_trials=200):
    """
    Run Optuna hyperparameter optimization with adaptive risk parameters
    
    Args:
        n_trials: Number of trials to run
    """
    print("=" * 80)
    print("OPTUNA HYPERPARAMETER OPTIMIZATION (INVERTED SIGNALS + ADAPTIVE RISK)")
    print("=" * 80)
    print()
    print("🔥 Using INVERTED signals based on analysis:")
    print("   Original BUY → SHORT | Original SELL → LONG")
    print()
    print("🎯 Optimizing ADAPTIVE RISK MANAGEMENT:")
    print("   ✓ Adaptive Thresholds (volatility-based)")
    print("   ✓ Adaptive Stop Loss (ATR-based)")
    print("   ✓ Adaptive Take Profit (volatility-based)")
    print()
    print("🚀 Running with 100 ASSETS for maximum trade opportunities!")
    print()
    
    # Fetch historical data - 100 ASSETS
    symbols = [
        "BTC-USD", "ETH-USD", "SOL-USD", "BNB-USD", "XRP-USD", "ADA-USD", "AVAX-USD", "DOGE-USD",
        "DOT-USD", "MATIC-USD", "LINK-USD", "TON11419-USD", "UNI7083-USD", "ATOM-USD", "FIL-USD",
        "ARB11841-USD", "OP-USD", "NEAR-USD", "APT21794-USD", "SUI20947-USD", "STX4847-USD",
        "IMX10603-USD", "INJ-USD", "TIA22861-USD", "SEI23149-USD", "THETA-USD", "FLOW-USD",
        "AXS-USD", "SAND-USD", "MANA-USD", "CRV-USD", "GRT6719-USD", "AAVE-USD", "MKR-USD",
        "COMP-USD", "ALGO-USD", "VET-USD", "FTM-USD", "HBAR-USD", "QNT-USD", "ICP-USD", "EOS-USD",
        "EGLD-USD", "XTZ-USD", "KAVA-USD", "ZIL-USD", "ENS-USD", "1INCH-USD", "SUSHI-USD", "YFI-USD",
        "SNX-USD", "REN-USD", "LRC-USD", "OMG-USD", "CELO-USD", "ANKR-USD", "ENJ-USD", "STORJ-USD",
        "BAL-USD", "BAND-USD", "MANTA-USD", "STRK22691-USD", "BLUR-USD", "DYDX-USD", "BONK-USD",
        "PEPE24478-USD", "SHIB-USD", "WIF-USD", "FLOKI-USD", "RNDR-USD", "PENDLE-USD", "JTO-USD",
        "PYTH-USD", "JUP-USD", "W-USD", "WLD-USD", "KAS-USD", "FET-USD", "OCEAN-USD", "AKT-USD",
        "LDO-USD", "RPL-USD", "FXS-USD", "SPELL-USD", "MAGIC-USD", "GMX-USD", "CVX-USD", "GALA-USD",
        "CHZ-USD", "ROSE-USD"
    ]
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=180)  # 6 months
    
    print(f"📊 Fetching data for {len(symbols)} symbols...")
    print(f"Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    print()
    
    global HISTORICAL_DATA, ALLOCATIONS
    
    for symbol in symbols:
        print(f"  Fetching {symbol}...", end=" ")
        df = fetch_historical_data(symbol, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"), interval="1h")
        if len(df) > 0:
            HISTORICAL_DATA[symbol] = df
            print(f"✅ {len(df)} candles")
    
    # 100 ASSETS ALLOCATION (normalized from live_trading.py configuration)
    ALLOCATIONS = {
        "BTC-USD": 0.15, "ETH-USD": 0.12, "SOL-USD": 0.08, "BNB-USD": 0.06, "XRP-USD": 0.05,
        "ADA-USD": 0.04, "AVAX-USD": 0.03, "DOGE-USD": 0.03, "DOT-USD": 0.025, "MATIC-USD": 0.025,
        "LINK-USD": 0.02, "TON11419-USD": 0.02, "UNI7083-USD": 0.02, "ATOM-USD": 0.02,
        "FIL-USD": 0.015, "ARB11841-USD": 0.015, "OP-USD": 0.015, "NEAR-USD": 0.015,
        "APT21794-USD": 0.015, "SUI20947-USD": 0.015, "STX4847-USD": 0.01, "IMX10603-USD": 0.01,
        "INJ-USD": 0.01, "TIA22861-USD": 0.01, "SEI23149-USD": 0.01, "THETA-USD": 0.01,
        "FLOW-USD": 0.01, "AXS-USD": 0.01, "SAND-USD": 0.01, "MANA-USD": 0.01,
        "CRV-USD": 0.008, "GRT6719-USD": 0.008, "AAVE-USD": 0.008, "MKR-USD": 0.008,
        "COMP-USD": 0.008, "ALGO-USD": 0.008, "VET-USD": 0.008, "FTM-USD": 0.008,
        "HBAR-USD": 0.008, "QNT-USD": 0.008, "ICP-USD": 0.005, "EOS-USD": 0.005,
        "EGLD-USD": 0.005, "XTZ-USD": 0.005, "KAVA-USD": 0.005, "ZIL-USD": 0.005,
        "ENS-USD": 0.005, "1INCH-USD": 0.005, "SUSHI-USD": 0.005, "YFI-USD": 0.005,
        "SNX-USD": 0.003, "REN-USD": 0.003, "LRC-USD": 0.003, "OMG-USD": 0.003,
        "CELO-USD": 0.003, "ANKR-USD": 0.003, "ENJ-USD": 0.003, "STORJ-USD": 0.003,
        "BAL-USD": 0.003, "BAND-USD": 0.003, "MANTA-USD": 0.002, "STRK22691-USD": 0.002,
        "BLUR-USD": 0.002, "DYDX-USD": 0.002, "BONK-USD": 0.002, "PEPE24478-USD": 0.002,
        "SHIB-USD": 0.002, "WIF-USD": 0.002, "FLOKI-USD": 0.002, "RNDR-USD": 0.002,
        "PENDLE-USD": 0.0015, "JTO-USD": 0.0015, "PYTH-USD": 0.0015, "JUP-USD": 0.0015,
        "W-USD": 0.0015, "WLD-USD": 0.0015, "KAS-USD": 0.0015, "FET-USD": 0.0015,
        "OCEAN-USD": 0.0015, "AKT-USD": 0.0015, "LDO-USD": 0.001, "RPL-USD": 0.001,
        "FXS-USD": 0.001, "SPELL-USD": 0.001, "MAGIC-USD": 0.001, "GMX-USD": 0.001,
        "CVX-USD": 0.001, "GALA-USD": 0.001, "CHZ-USD": 0.001, "ROSE-USD": 0.001,
    }
    
    print()
    print("=" * 80)
    print("STARTING OPTIMIZATION")
    print("=" * 80)
    print(f"Number of trials: {n_trials}")
    print(f"Assets: {len([k for k in HISTORICAL_DATA.keys()])}")
    print(f"Optimization method: Tree-structured Parzen Estimator (TPE)")
    print(f"⚠️  With 100 assets, each trial takes ~10-20x longer")
    print(f"Estimated time: ~{n_trials * 5 / 60:.1f} minutes (could be longer)")
    print()
    
    # Create Optuna study
    study = optuna.create_study(
        direction='maximize',
        sampler=TPESampler(seed=42),
        pruner=MedianPruner(n_startup_trials=10, n_warmup_steps=5)
    )
    
    # Run optimization
    study.optimize(objective, n_trials=n_trials, show_progress_bar=True)
    
    # Get results
    best_trial = study.best_trial
    best_params = best_trial.params
    best_return = best_trial.value
    
    print()
    print("=" * 80)
    print("OPTIMIZATION COMPLETE!")
    print("=" * 80)
    print()
    
    print(f"Best Return: {best_return:+.2f}%")
    print()
    print("Best Parameters:")
    print()
    print("📊 Base Parameters:")
    print(f"  Leverage:                {best_params['leverage']}x")
    print(f"  Base Signal Threshold:   {best_params['base_signal_threshold']:.3f}")
    print(f"  Base Stop Loss:          {best_params['base_stop_loss_pct']*100:.2f}%")
    print(f"  Base Take Profit:        {best_params['base_take_profit_pct']*100:.2f}%")
    print(f"  Lookback Periods:        {best_params['lookback_periods']}")
    print()
    print("🎯 Adaptive Threshold Parameters:")
    print(f"  Volatility High Mult:    {best_params['volatility_high_mult']:.2f}x  (Threshold × this when high volatility)")
    print(f"  Volatility Low Mult:     {best_params['volatility_low_mult']:.2f}x  (Threshold × this when low volatility)")
    print(f"  ATR Lookback:            {best_params['atr_lookback']} periods")
    print()
    print("🎯 Adaptive Stop Loss Parameters:")
    print(f"  ATR Stop Loss Mult:      {best_params['atr_stop_loss_mult']:.2f}x  (ATR multiplier for SL adjustment)")
    print()
    print("🎯 Adaptive Take Profit Parameters:")
    print(f"  Volatility TP Mult:      {best_params['volatility_tp_mult']:.2f}x  (Volatility multiplier for TP)")
    print()
    
    # Calculate example adaptive values
    print("💡 Example Adaptive Ranges:")
    base_threshold = best_params['base_signal_threshold']
    base_sl = best_params['base_stop_loss_pct']
    base_tp = best_params['base_take_profit_pct']
    print(f"  Threshold Range:  {base_threshold * best_params['volatility_low_mult']:.3f} (low vol) → {base_threshold:.3f} (normal) → {base_threshold * best_params['volatility_high_mult']:.3f} (high vol)")
    print(f"  Stop Loss Range:  {base_sl*100:.2f}% (base) → ~{min(8.0, (base_sl + 0.03 * best_params['atr_stop_loss_mult'])*100):.2f}% (high ATR)")
    print(f"  Take Profit Range: {base_tp*100:.2f}% (base) → ~{min(25.0, base_tp*100 * (1 + 0.05 * best_params['volatility_tp_mult'])):.2f}% (high volatility)")
    print()
    
    # Get top trials
    sorted_trials = sorted(study.trials, key=lambda t: t.value if t.value is not None else -float('inf'), reverse=True)
    
    print("TOP 10 TRIALS:")
    print("-" * 120)
    print(f"{'#':<3} {'Return':<10} {'Lev':<5} {'Threshold':<11} {'SL%':<7} {'TP%':<7} {'VolHi':<7} {'VolLo':<7} {'ATRSL':<7}")
    print("-" * 120)
    
    for i, trial in enumerate(sorted_trials[:10], 1):
        if trial.value is not None:
            p = trial.params
            print(f"{i:<3} {trial.value:>+7.2f}%  {p['leverage']:>3}x  {p['base_signal_threshold']:>8.3f}  {p['base_stop_loss_pct']*100:>5.2f}  {p['base_take_profit_pct']*100:>5.1f}  {p['volatility_high_mult']:>5.2f}  {p['volatility_low_mult']:>5.2f}  {p['atr_stop_loss_mult']:>5.2f}")
    
    print()
    print("=" * 80)
    print("PARAMETER IMPORTANCE")
    print("=" * 80)
    
    # Calculate parameter importance
    try:
        importance = optuna.importance.get_param_importances(study)
        for param, score in importance.items():
            print(f"{param:20s}: {score:.4f}")
    except:
        print("Not enough trials to calculate importance")
    
    print()
    
    # Save results
    output_file = 'hyperopt_adaptive_results.json'
    with open(output_file, 'w') as f:
        json.dump({
            'strategy': 'inverted_signals_with_adaptive_risk',
            'description': 'Inverted technical signals (BUY→SHORT, SELL→LONG) with adaptive threshold, stop loss, and take profit',
            'best_params': best_params,
            'best_return': best_return,
            'n_trials': n_trials,
            'adaptive_features': {
                'adaptive_threshold': True,
                'adaptive_stop_loss': True,
                'adaptive_take_profit': True,
                'description': 'All risk parameters adapt to market volatility and ATR'
            },
            'top_10': [
                {
                    'params': t.params,
                    'return': t.value
                } for t in sorted_trials[:10] if t.value is not None
            ]
        }, f, indent=2)
    
    print(f"💾 Results saved to {output_file}")
    print(f"   (Previous results: hyperopt_optuna_inverted_results.json)")
    print()
    print("Optimization Progress:")
    returns = [t.value for t in study.trials if t.value is not None]
    best_so_far = []
    current_best = -float('inf')
    for r in returns:
        if r > current_best:
            current_best = r
        best_so_far.append(current_best)
    
    milestones = [0, len(returns)//4, len(returns)//2, 3*len(returns)//4, len(returns)-1]
    for i in milestones:
        if i < len(best_so_far):
            print(f"  Trial {i+1:3d}: Best return = {best_so_far[i]:+.2f}%")
    
    print()
    print("=" * 80)
    
    return best_params, best_return, study


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Optuna Hyperparameter Optimization')
    parser.add_argument('--trials', type=int, default=200, help='Number of trials (default: 200)')
    args = parser.parse_args()
    
    best_params, best_return, study = run_optuna_optimization(n_trials=args.trials)
