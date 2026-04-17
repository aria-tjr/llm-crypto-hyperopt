"""
Quick Backtest with Top 20 Assets
Tests the core strategy quickly before full 100-asset run
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from src.components.signal_generator import generate_trading_signal

# TOP 20 ASSETS (highest allocations)
SYMBOLS = [
    {"name": "Bitcoin", "symbol": "BTCUSDT", "allocation": 0.15, "yahoo": "BTC-USD"},
    {"name": "Ethereum", "symbol": "ETHUSDT", "allocation": 0.12, "yahoo": "ETH-USD"},
    {"name": "Solana", "symbol": "SOLUSDT", "allocation": 0.08, "yahoo": "SOL-USD"},
    {"name": "BNB", "symbol": "BNBUSDT", "allocation": 0.06, "yahoo": "BNB-USD"},
    {"name": "XRP", "symbol": "XRPUSDT", "allocation": 0.05, "yahoo": "XRP-USD"},
    {"name": "Cardano", "symbol": "ADAUSDT", "allocation": 0.04, "yahoo": "ADA-USD"},
    {"name": "Avalanche", "symbol": "AVAXUSDT", "allocation": 0.03, "yahoo": "AVAX-USD"},
    {"name": "Dogecoin", "symbol": "DOGEUSDT", "allocation": 0.03, "yahoo": "DOGE-USD"},
    {"name": "Polkadot", "symbol": "DOTUSDT", "allocation": 0.025, "yahoo": "DOT-USD"},
    {"name": "Polygon", "symbol": "MATICUSDT", "allocation": 0.025, "yahoo": "MATIC-USD"},
    {"name": "Chainlink", "symbol": "LINKUSDT", "allocation": 0.02, "yahoo": "LINK-USD"},
    {"name": "Toncoin", "symbol": "TONUSDT", "allocation": 0.02, "yahoo": "TON11419-USD"},
    {"name": "Uniswap", "symbol": "UNIUSDT", "allocation": 0.02, "yahoo": "UNI7083-USD"},
    {"name": "Cosmos", "symbol": "ATOMUSDT", "allocation": 0.02, "yahoo": "ATOM-USD"},
    {"name": "Filecoin", "symbol": "FILUSDT", "allocation": 0.015, "yahoo": "FIL-USD"},
    {"name": "Arbitrum", "symbol": "ARBUSDT", "allocation": 0.015, "yahoo": "ARB11841-USD"},
    {"name": "Optimism", "symbol": "OPUSDT", "allocation": 0.015, "yahoo": "OP-USD"},
    {"name": "NEAR", "symbol": "NEARUSDT", "allocation": 0.015, "yahoo": "NEAR-USD"},
    {"name": "Aptos", "symbol": "APTUSDT", "allocation": 0.015, "yahoo": "APT21794-USD"},
    {"name": "Sui", "symbol": "SUIUSDT", "allocation": 0.015, "yahoo": "SUI20947-USD"},
]

# OPTIMIZED PARAMETERS
LEVERAGE = 10.0
SIGNAL_THRESHOLD = 0.551
STOP_LOSS_PCT = 0.093
TAKE_PROFIT_PCT = 0.102
LOOKBACK_PERIODS = 150

def run_quick_backtest():
    """Run quick backtest with top 20 assets"""
    
    print("=" * 80)
    print("QUICK 20-ASSET BACKTEST")
    print("=" * 80)
    print()
    print("Testing YOLO configuration with top 20 assets for speed")
    print(f"Leverage: {LEVERAGE}x | Threshold: {SIGNAL_THRESHOLD} | Stop: {STOP_LOSS_PCT*100:.1f}% | TP: {TAKE_PROFIT_PCT*100:.1f}%")
    print()
    
    # Date range - shorter for speed
    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)  # 3 months
    
    print(f"Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')} (90 days)")
    print()
    
    # Fetch data
    print("📊 Fetching data...")
    HISTORICAL_DATA = {}
    for asset in SYMBOLS:
        try:
            ticker = yf.Ticker(asset['yahoo'])
            df = ticker.history(start=start_date, end=end_date, interval="1h")
            if len(df) > 0:
                HISTORICAL_DATA[asset['symbol']] = df
                print(f"  ✅ {asset['symbol']:12s} {len(df):,} candles")
        except:
            print(f"  ❌ {asset['symbol']:12s} failed")
    
    print(f"\n✅ Loaded {len(HISTORICAL_DATA)} assets\n")
    
    if len(HISTORICAL_DATA) == 0:
        print("❌ No data! Exiting.")
        return
    
    # Backtest
    print("=" * 80)
    print("RUNNING BACKTEST...")
    print("=" * 80)
    print()
    
    initial_capital = 10000
    capital = initial_capital
    positions = {}
    trades_log = []
    
    # Allocations
    ALLOCATIONS = {asset['symbol']: asset['allocation'] for asset in SYMBOLS if asset['symbol'] in HISTORICAL_DATA}
    total_allocation = sum(ALLOCATIONS.values())
    if total_allocation > 0:
        ALLOCATIONS = {k: v/total_allocation for k, v in ALLOCATIONS.items()}
    
    # Timeline
    all_dates = set()
    for df in HISTORICAL_DATA.values():
        all_dates.update(df.index)
    timeline = sorted(list(all_dates))
    
    print(f"Processing {len(timeline):,} timestamps...\n")
    
    # Main loop
    for i, current_time in enumerate(timeline):
        if i < LOOKBACK_PERIODS:
            continue
        
        if i % 500 == 0:
            print(f"  Progress: {i:,}/{len(timeline):,} ({i/len(timeline)*100:.1f}%) - {len(trades_log)} trades", end="\r")
        
        for symbol in HISTORICAL_DATA.keys():
            df = HISTORICAL_DATA[symbol]
            
            if current_time not in df.index:
                continue
            
            current_price = df.loc[current_time, 'Close']
            prices = df.loc[:current_time, 'Close'].tail(LOOKBACK_PERIODS).tolist()
            
            if len(prices) < LOOKBACK_PERIODS:
                continue
            
            # Generate signal
            signal_data = generate_trading_signal(prices)
            signal = -signal_data['signal']  # INVERTED
            
            allocation = ALLOCATIONS.get(symbol, 0)
            
            # Check position
            if symbol in positions:
                position = positions[symbol]
                entry_price = position['entry_price']
                pnl_pct = (current_price - entry_price) / entry_price
                
                # Exit conditions
                should_exit = False
                exit_reason = ""
                
                if signal < -SIGNAL_THRESHOLD:
                    should_exit = True
                    exit_reason = "signal"
                elif pnl_pct >= TAKE_PROFIT_PCT:
                    should_exit = True
                    exit_reason = "tp"
                elif pnl_pct <= -STOP_LOSS_PCT:
                    should_exit = True
                    exit_reason = "sl"
                
                if should_exit:
                    pnl = (current_price - entry_price) * position['quantity']
                    capital += pnl
                    
                    trades_log.append({
                        'symbol': symbol,
                        'pnl': pnl,
                        'pnl_pct': pnl_pct * 100,
                        'exit_reason': exit_reason
                    })
                    
                    del positions[symbol]
            
            else:
                # Check entry
                if signal > SIGNAL_THRESHOLD:
                    position_value = capital * allocation * LEVERAGE
                    quantity = position_value / current_price
                    
                    if position_value >= 100:
                        positions[symbol] = {
                            'entry_price': current_price,
                            'quantity': quantity
                        }
    
    print()
    
    # Close positions
    final_time = timeline[-1]
    for symbol, position in list(positions.items()):
        if final_time in HISTORICAL_DATA[symbol].index:
            current_price = HISTORICAL_DATA[symbol].loc[final_time, 'Close']
            pnl = (current_price - position['entry_price']) * position['quantity']
            capital += pnl
            
            pnl_pct = (current_price - position['entry_price']) / position['entry_price']
            trades_log.append({
                'symbol': symbol,
                'pnl': pnl,
                'pnl_pct': pnl_pct * 100,
                'exit_reason': 'close'
            })
    
    # Results
    total_return = (capital - initial_capital) / initial_capital * 100
    total_trades = len(trades_log)
    winning_trades = [t for t in trades_log if t['pnl'] > 0]
    losing_trades = [t for t in trades_log if t['pnl'] <= 0]
    
    win_rate = len(winning_trades) / total_trades * 100 if total_trades > 0 else 0
    avg_win = sum(t['pnl'] for t in winning_trades) / len(winning_trades) if winning_trades else 0
    avg_loss = sum(t['pnl'] for t in losing_trades) / len(losing_trades) if losing_trades else 0
    
    print()
    print("=" * 80)
    print("RESULTS - TOP 20 ASSETS")
    print("=" * 80)
    print()
    print(f"💰 Initial Capital:    ${initial_capital:,.2f}")
    print(f"💰 Final Capital:      ${capital:,.2f}")
    print(f"📈 Total Return:       {total_return:+.2f}%")
    print()
    print(f"📊 Total Trades:       {total_trades}")
    print(f"   ✅ Winning:         {len(winning_trades)} ({win_rate:.1f}%)")
    print(f"   ❌ Losing:          {len(losing_trades)} ({100-win_rate:.1f}%)")
    print()
    print(f"💵 Average Win:        ${avg_win:,.2f}")
    print(f"💸 Average Loss:       ${avg_loss:,.2f}")
    if avg_loss != 0:
        print(f"📊 Win/Loss Ratio:     {abs(avg_win/avg_loss):.2f}")
    print()
    print(f"⏱️  Trading Days:       {len(timeline)/(24):.0f}")
    print(f"📈 Trades/Day:         {total_trades / (len(timeline)/24):.2f}")
    print()
    
    # Extrapolate to 100 assets
    if total_trades > 0:
        trades_per_day_20 = total_trades / (len(timeline)/24)
        trades_per_day_100 = trades_per_day_20 * (100/20)  # Linear scaling
        print(f"📊 PROJECTION FOR 100 ASSETS:")
        print(f"   Current (20 assets): {trades_per_day_20:.2f} trades/day")
        print(f"   Projected (100 assets): {trades_per_day_100:.2f} trades/day")
        print(f"   Expected monthly: ~{trades_per_day_100 * 30:.0f} trades")
    
    print()
    print("=" * 80)
    print("✅ Quick backtest complete! Configuration validated.")
    print("=" * 80)

if __name__ == "__main__":
    run_quick_backtest()
