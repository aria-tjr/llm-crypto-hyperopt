"""
Weekly Hyperopt Script - Optimizes on Last 30 Days
Runs every Sunday at 2 AM via cron job
Focuses on: leverage, stop_loss, take_profit, threshold
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
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Global variables
HISTORICAL_DATA = {}
ALLOCATIONS = {}

def fetch_historical_data(symbol, days=30, interval="1h"):
    """Fetch last N days of historical data"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    ticker = yf.Ticker(symbol)
    df = ticker.history(start=start_date, end=end_date, interval=interval)
    return df


def run_backtest_trial(params):
    """Run backtest with given parameters"""
    initial_capital = 10000
    max_leverage = params['max_leverage']
    signal_threshold = params['signal_threshold']
    stop_loss_pct = params['stop_loss_pct']
    take_profit_pct = params['take_profit_pct']
    lookback_periods = params['lookback_periods']
    
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
            prices = df.loc[:current_time, 'Close'].tail(lookback_periods).tolist()
            
            if len(prices) < lookback_periods:
                continue
            
            # Generate technical signals
            signal_data = generate_trading_signal(prices)
            
            # INVERT SIGNALS
            signal = -signal_data['signal']
            
            allocation = ALLOCATIONS.get(symbol, 0)
            
            # Check existing position
            if symbol in positions:
                position = positions[symbol]
                entry_price = position['entry_price']
                pnl_pct = (current_price - entry_price) / entry_price
                
                # Check exit conditions
                should_exit = False
                
                if signal < -signal_threshold:
                    should_exit = True
                elif pnl_pct >= take_profit_pct:
                    should_exit = True
                elif pnl_pct <= -stop_loss_pct:
                    should_exit = True
                
                if should_exit:
                    # Close position
                    position_value = position['quantity'] * current_price
                    pnl = position_value - position['initial_value']
                    capital += position_value
                    
                    trades_log.append({
                        'symbol': symbol,
                        'type': 'CLOSE',
                        'price': current_price,
                        'pnl': pnl,
                        'pnl_pct': pnl_pct
                    })
                    
                    del positions[symbol]
            
            else:
                # Check entry conditions
                if signal > signal_threshold and capital > 0:
                    # Open position
                    position_value = capital * allocation * max_leverage
                    position_value = min(position_value, capital)  # Don't exceed available capital
                    
                    if position_value >= 100:  # Minimum trade size
                        quantity = position_value / current_price
                        capital -= position_value / max_leverage  # Reserve margin
                        
                        positions[symbol] = {
                            'entry_price': current_price,
                            'quantity': quantity,
                            'initial_value': position_value / max_leverage,
                            'timestamp': current_time
                        }
                        
                        trades_log.append({
                            'symbol': symbol,
                            'type': 'OPEN',
                            'price': current_price,
                            'quantity': quantity
                        })
    
    # Close all remaining positions
    for symbol, position in positions.items():
        if symbol in HISTORICAL_DATA:
            final_price = HISTORICAL_DATA[symbol].iloc[-1]['Close']
            position_value = position['quantity'] * final_price
            capital += position_value
    
    final_return = ((capital - initial_capital) / initial_capital) * 100
    
    return final_return


def objective(trial):
    """Optuna objective function"""
    # Define hyperparameter search space
    params = {
        'max_leverage': trial.suggest_int('max_leverage', 5, 10),  # 5x-10x max
        'signal_threshold': trial.suggest_float('signal_threshold', 0.3, 0.7),
        'stop_loss_pct': trial.suggest_float('stop_loss_pct', 0.015, 0.035),  # 1.5%-3.5%
        'take_profit_pct': trial.suggest_float('take_profit_pct', 0.08, 0.15),  # 8%-15%
        'lookback_periods': trial.suggest_int('lookback_periods', 100, 200, step=25)
    }
    
    return_pct = run_backtest_trial(params)
    
    return return_pct


def main():
    logger.info("=" * 80)
    logger.info("🔬 WEEKLY HYPEROPT - INTENSIVE OPTIMIZATION")
    logger.info("=" * 80)
    logger.info(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Data Window: Last 30 days")
    logger.info(f"Trials: 300")
    logger.info(f"Focus: Leverage, Stop Loss, Take Profit, Threshold")
    logger.info("=" * 80)
    
    # Load top performing assets (quality over quantity)
    top_assets = [
        ('BTCUSDT', 'Bitcoin', 0.15),
        ('ETHUSDT', 'Ethereum', 0.12),
        ('SOLUSDT', 'Solana', 0.08),
        ('BNBUSDT', 'BNB', 0.07),
        ('XRPUSDT', 'XRP', 0.06),
        ('ADAUSDT', 'Cardano', 0.05),
        ('AVAXUSDT', 'Avalanche', 0.05),
        ('DOTUSDT', 'Polkadot', 0.04),
        ('MATICUSDT', 'Polygon', 0.04),
        ('LINKUSDT', 'Chainlink', 0.04),
        ('UNIUSDT', 'Uniswap', 0.03),
        ('LTCUSDT', 'Litecoin', 0.03),
        ('ATOMUSDT', 'Cosmos', 0.03),
        ('APTUSDT', 'Aptos', 0.03),
        ('ARBUSDT', 'Arbitrum', 0.03),
    ]
    
    logger.info(f"📊 Loading historical data for {len(top_assets)} assets...")
    
    for symbol, name, allocation in top_assets:
        try:
            logger.info(f"  Fetching {name} ({symbol})...")
            df = fetch_historical_data(symbol, days=30, interval="1h")
            
            if len(df) > 100:
                HISTORICAL_DATA[symbol] = df
                ALLOCATIONS[symbol] = allocation
                logger.info(f"    ✅ Loaded {len(df)} candles")
            else:
                logger.warning(f"    ⚠️  Insufficient data ({len(df)} candles)")
        except Exception as e:
            logger.error(f"    ❌ Failed: {str(e)}")
    
    logger.info(f"✅ Successfully loaded {len(HISTORICAL_DATA)} assets")
    logger.info("")
    
    # Create Optuna study
    study = optuna.create_study(
        direction='maximize',
        sampler=TPESampler(seed=42),
        pruner=MedianPruner(n_startup_trials=20, n_warmup_steps=10)
    )
    
    logger.info("🚀 Starting optimization (300 trials)...")
    logger.info("This will take approximately 30-45 minutes...")
    logger.info("")
    
    study.optimize(objective, n_trials=300, show_progress_bar=True)
    
    # Get best parameters
    best_params = study.best_params
    best_return = study.best_value
    
    logger.info("")
    logger.info("=" * 80)
    logger.info("🎯 OPTIMIZATION COMPLETE!")
    logger.info("=" * 80)
    logger.info(f"Best Return: +{best_return:.2f}%")
    logger.info(f"Best Parameters:")
    for key, value in best_params.items():
        logger.info(f"  {key}: {value}")
    logger.info("=" * 80)
    
    # Save best parameters
    output = {
        'best_params': best_params,
        'best_return': best_return,
        'optimization_date': datetime.now().isoformat(),
        'data_window_days': 30,
        'n_trials': 300,
        'assets_optimized': len(HISTORICAL_DATA)
    }
    
    with open('best_params_weekly.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    logger.info("✅ Parameters saved to best_params_weekly.json")
    
    # Parameter importance
    if len(study.trials) >= 10:
        importance = optuna.importance.get_param_importances(study)
        logger.info("")
        logger.info("📊 Parameter Importance:")
        for param, imp in importance.items():
            logger.info(f"  {param}: {imp*100:.1f}%")


if __name__ == '__main__':
    main()
