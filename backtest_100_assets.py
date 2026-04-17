"""
Backtest with 100 Assets Configuration
Tests the YOLO 100-asset strategy with optimized parameters
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from src.components.signal_generator import generate_trading_signal
import time

# 100 ASSETS CONFIGURATION (same as live_trading.py)
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
    # Top 20 assets - continue with mid caps
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
    # 21-40
    {"name": "Stacks", "symbol": "STXUSDT", "allocation": 0.01, "yahoo": "STX4847-USD"},
    {"name": "Immutable", "symbol": "IMXUSDT", "allocation": 0.01, "yahoo": "IMX10603-USD"},
    {"name": "Injective", "symbol": "INJUSDT", "allocation": 0.01, "yahoo": "INJ-USD"},
    {"name": "Celestia", "symbol": "TIAUSDT", "allocation": 0.01, "yahoo": "TIA22861-USD"},
    {"name": "Sei", "symbol": "SEIUSDT", "allocation": 0.01, "yahoo": "SEI23149-USD"},
    {"name": "Theta", "symbol": "THETAUSDT", "allocation": 0.01, "yahoo": "THETA-USD"},
    {"name": "Flow", "symbol": "FLOWUSDT", "allocation": 0.01, "yahoo": "FLOW-USD"},
    {"name": "Axie", "symbol": "AXSUSDT", "allocation": 0.01, "yahoo": "AXS-USD"},
    {"name": "Sandbox", "symbol": "SANDUSDT", "allocation": 0.01, "yahoo": "SAND-USD"},
    {"name": "Decentraland", "symbol": "MANAUSDT", "allocation": 0.01, "yahoo": "MANA-USD"},
    # 31-50
    {"name": "Curve", "symbol": "CRVUSDT", "allocation": 0.008, "yahoo": "CRV-USD"},
    {"name": "Graph", "symbol": "GRTUSDT", "allocation": 0.008, "yahoo": "GRT6719-USD"},
    {"name": "Aave", "symbol": "AAVEUSDT", "allocation": 0.008, "yahoo": "AAVE-USD"},
    {"name": "Maker", "symbol": "MKRUSDT", "allocation": 0.008, "yahoo": "MKR-USD"},
    {"name": "Comp", "symbol": "COMPUSDT", "allocation": 0.008, "yahoo": "COMP-USD"},
    {"name": "Algorand", "symbol": "ALGOUSDT", "allocation": 0.008, "yahoo": "ALGO-USD"},
    {"name": "VeChain", "symbol": "VETUSDT", "allocation": 0.008, "yahoo": "VET-USD"},
    {"name": "Fantom", "symbol": "FTMUSDT", "allocation": 0.008, "yahoo": "FTM-USD"},
    {"name": "Hedera", "symbol": "HBARUSDT", "allocation": 0.008, "yahoo": "HBAR-USD"},
    {"name": "Quant", "symbol": "QNTUSDT", "allocation": 0.008, "yahoo": "QNT-USD"},
    # 41-60
    {"name": "ICP", "symbol": "ICPUSDT", "allocation": 0.005, "yahoo": "ICP-USD"},
    {"name": "EOS", "symbol": "EOSUSDT", "allocation": 0.005, "yahoo": "EOS-USD"},
    {"name": "Elrond", "symbol": "EGLDUSDT", "allocation": 0.005, "yahoo": "EGLD-USD"},
    {"name": "Tezos", "symbol": "XTZUSDT", "allocation": 0.005, "yahoo": "XTZ-USD"},
    {"name": "Kava", "symbol": "KAVAUSDT", "allocation": 0.005, "yahoo": "KAVA-USD"},
    {"name": "Zilliqa", "symbol": "ZILUSDT", "allocation": 0.005, "yahoo": "ZIL-USD"},
    {"name": "ENS", "symbol": "ENSUSDT", "allocation": 0.005, "yahoo": "ENS-USD"},
    {"name": "1inch", "symbol": "1INCHUSDT", "allocation": 0.005, "yahoo": "1INCH-USD"},
    {"name": "Sushi", "symbol": "SUSHIUSDT", "allocation": 0.005, "yahoo": "SUSHI-USD"},
    {"name": "Yearn", "symbol": "YFIUSDT", "allocation": 0.005, "yahoo": "YFI-USD"},
    # 51-70
    {"name": "Synthetix", "symbol": "SNXUSDT", "allocation": 0.003, "yahoo": "SNX-USD"},
    {"name": "Ren", "symbol": "RENUSDT", "allocation": 0.003, "yahoo": "REN-USD"},
    {"name": "Loopring", "symbol": "LRCUSDT", "allocation": 0.003, "yahoo": "LRC-USD"},
    {"name": "OMG", "symbol": "OMGUSDT", "allocation": 0.003, "yahoo": "OMG-USD"},
    {"name": "Celo", "symbol": "CELOUSDT", "allocation": 0.003, "yahoo": "CELO-USD"},
    {"name": "Ankr", "symbol": "ANKRUSDT", "allocation": 0.003, "yahoo": "ANKR-USD"},
    {"name": "Enjin", "symbol": "ENJUSDT", "allocation": 0.003, "yahoo": "ENJ-USD"},
    {"name": "Storj", "symbol": "STORJUSDT", "allocation": 0.003, "yahoo": "STORJ-USD"},
    {"name": "Balancer", "symbol": "BALUSDT", "allocation": 0.003, "yahoo": "BAL-USD"},
    {"name": "Band", "symbol": "BANDUSDT", "allocation": 0.003, "yahoo": "BAND-USD"},
    # 61-80 (Layer 2s, Memecoins, New projects)
    {"name": "Manta", "symbol": "MANTAUSDT", "allocation": 0.002, "yahoo": "MANTA-USD"},
    {"name": "Starknet", "symbol": "STRKUSDT", "allocation": 0.002, "yahoo": "STRK22691-USD"},
    {"name": "Blur", "symbol": "BLURUSDT", "allocation": 0.002, "yahoo": "BLUR-USD"},
    {"name": "dYdX", "symbol": "DYDXUSDT", "allocation": 0.002, "yahoo": "DYDX-USD"},
    {"name": "Bonk", "symbol": "BONKUSDT", "allocation": 0.002, "yahoo": "BONK-USD"},
    {"name": "Pepe", "symbol": "PEPEUSDT", "allocation": 0.002, "yahoo": "PEPE24478-USD"},
    {"name": "Shiba", "symbol": "SHIBUSDT", "allocation": 0.002, "yahoo": "SHIB-USD"},
    {"name": "WIF", "symbol": "WIFUSDT", "allocation": 0.002, "yahoo": "WIF-USD"},
    {"name": "Floki", "symbol": "FLOKIUSDT", "allocation": 0.002, "yahoo": "FLOKI-USD"},
    {"name": "Render", "symbol": "RENDERUSDT", "allocation": 0.002, "yahoo": "RNDR-USD"},
    # 71-90
    {"name": "Pendle", "symbol": "PENDLEUSDT", "allocation": 0.0015, "yahoo": "PENDLE-USD"},
    {"name": "JTO", "symbol": "JTOUSDT", "allocation": 0.0015, "yahoo": "JTO-USD"},
    {"name": "Pyth", "symbol": "PYTHUSDT", "allocation": 0.0015, "yahoo": "PYTH-USD"},
    {"name": "Jupiter", "symbol": "JUPUSDT", "allocation": 0.0015, "yahoo": "JUP-USD"},
    {"name": "Wormhole", "symbol": "WUSDT", "allocation": 0.0015, "yahoo": "W-USD"},
    {"name": "Worldcoin", "symbol": "WLDUSDT", "allocation": 0.0015, "yahoo": "WLD-USD"},
    {"name": "Kaspa", "symbol": "KASUSDT", "allocation": 0.0015, "yahoo": "KAS-USD"},
    {"name": "Fetch", "symbol": "FETUSDT", "allocation": 0.0015, "yahoo": "FET-USD"},
    {"name": "Ocean", "symbol": "OCEANUSDT", "allocation": 0.0015, "yahoo": "OCEAN-USD"},
    {"name": "Akash", "symbol": "AKTUSDT", "allocation": 0.0015, "yahoo": "AKT-USD"},
    # 91-100 (Micro caps)
    {"name": "Lido", "symbol": "LDOUSDT", "allocation": 0.001, "yahoo": "LDO-USD"},
    {"name": "Rocket", "symbol": "RPLUSDT", "allocation": 0.001, "yahoo": "RPL-USD"},
    {"name": "Frax", "symbol": "FXSUSDT", "allocation": 0.001, "yahoo": "FXS-USD"},
    {"name": "Spell", "symbol": "SPELLUSDT", "allocation": 0.001, "yahoo": "SPELL-USD"},
    {"name": "Magic", "symbol": "MAGICUSDT", "allocation": 0.001, "yahoo": "MAGIC-USD"},
    {"name": "GMX", "symbol": "GMXUSDT", "allocation": 0.001, "yahoo": "GMX-USD"},
    {"name": "Convex", "symbol": "CVXUSDT", "allocation": 0.001, "yahoo": "CVX-USD"},
    {"name": "Gala", "symbol": "GALAUSDT", "allocation": 0.001, "yahoo": "GALA-USD"},
    {"name": "CHZ", "symbol": "CHZUSDT", "allocation": 0.001, "yahoo": "CHZ-USD"},
    {"name": "Rose", "symbol": "ROSEUSDT", "allocation": 0.001, "yahoo": "ROSE-USD"},
]

# OPTIMIZED PARAMETERS (from hyperopt results)
LEVERAGE = 10.0
SIGNAL_THRESHOLD = 0.551
STOP_LOSS_PCT = 0.093
TAKE_PROFIT_PCT = 0.102
LOOKBACK_PERIODS = 150

def fetch_historical_data(yahoo_symbol, start_date, end_date, interval="1h"):
    """Fetch historical price data from Yahoo Finance"""
    try:
        ticker = yf.Ticker(yahoo_symbol)
        df = ticker.history(start=start_date, end=end_date, interval=interval)
        return df
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return pd.DataFrame()

def run_backtest_100_assets():
    """Run backtest with 100 assets"""
    
    print("=" * 80)
    print("100 ASSETS BACKTEST (YOLO MODE)")
    print("=" * 80)
    print()
    print("Strategy: Inverted Signals (Buy → Short, Sell → Long)")
    print(f"Leverage: {LEVERAGE}x")
    print(f"Signal Threshold: {SIGNAL_THRESHOLD}")
    print(f"Stop Loss: {STOP_LOSS_PCT*100:.1f}%")
    print(f"Take Profit: {TAKE_PROFIT_PCT*100:.1f}%")
    print(f"Lookback: {LOOKBACK_PERIODS} periods")
    print()
    
    # Date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=180)  # 6 months
    
    print(f"Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    print(f"Total Assets: {len(SYMBOLS)}")
    print()
    
    # Fetch data for all assets
    print("📊 Fetching historical data...")
    print("-" * 80)
    
    HISTORICAL_DATA = {}
    successful = 0
    failed = 0
    
    for i, asset in enumerate(SYMBOLS, 1):
        symbol = asset['symbol']
        yahoo_symbol = asset['yahoo']
        allocation = asset['allocation']
        
        print(f"[{i:3d}/100] {symbol:15s} ({allocation*100:5.2f}%) ", end="", flush=True)
        
        df = fetch_historical_data(yahoo_symbol, start_date, end_date, interval="1h")
        
        if len(df) > 0:
            HISTORICAL_DATA[symbol] = df
            successful += 1
            print(f"✅ {len(df):,} candles")
        else:
            failed += 1
            print(f"❌ Failed")
        
        # Small delay to avoid rate limiting
        if i % 10 == 0:
            time.sleep(1)
    
    print()
    print(f"✅ Successfully loaded: {successful} assets")
    print(f"❌ Failed to load: {failed} assets")
    print()
    
    if successful == 0:
        print("❌ No data loaded! Cannot run backtest.")
        return
    
    # Run backtest
    print("=" * 80)
    print("RUNNING BACKTEST...")
    print("=" * 80)
    print()
    
    initial_capital = 10000
    capital = initial_capital
    positions = {}
    trades_log = []
    
    # Create allocation map for successful symbols only
    ALLOCATIONS = {asset['symbol']: asset['allocation'] for asset in SYMBOLS if asset['symbol'] in HISTORICAL_DATA}
    
    # Normalize allocations (in case some assets failed)
    total_allocation = sum(ALLOCATIONS.values())
    if total_allocation > 0:
        ALLOCATIONS = {k: v/total_allocation for k, v in ALLOCATIONS.items()}
    
    # Get timeline
    all_dates = set()
    for df in HISTORICAL_DATA.values():
        all_dates.update(df.index)
    timeline = sorted(list(all_dates))
    
    print(f"Timeline: {len(timeline):,} unique timestamps")
    print(f"Scanning for trading opportunities...")
    print()
    
    # Main backtest loop
    signals_checked = 0
    for i, current_time in enumerate(timeline):
        if i < LOOKBACK_PERIODS:
            continue
        
        # Progress indicator every 1000 timestamps
        if i % 1000 == 0:
            print(f"  Progress: {i:,}/{len(timeline):,} ({i/len(timeline)*100:.1f}%) - {len(trades_log)} trades", end="\r")
        
        for symbol in HISTORICAL_DATA.keys():
            df = HISTORICAL_DATA[symbol]
            
            if current_time not in df.index:
                continue
            
            current_price = df.loc[current_time, 'Close']
            prices = df.loc[:current_time, 'Close'].tail(LOOKBACK_PERIODS).tolist()
            
            if len(prices) < LOOKBACK_PERIODS:
                continue
            
            signals_checked += 1
            
            # Generate technical signals
            signal_data = generate_trading_signal(prices)
            
            # 🔥 INVERT SIGNALS
            signal = -signal_data['signal']
            
            allocation = ALLOCATIONS.get(symbol, 0)
            
            # Check existing position
            if symbol in positions:
                position = positions[symbol]
                entry_price = position['entry_price']
                pnl_pct = (current_price - entry_price) / entry_price
                
                # Check exit conditions
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
                        'entry_time': position['entry_time'],
                        'exit_time': current_time,
                        'entry_price': entry_price,
                        'exit_price': current_price,
                        'pnl': pnl,
                        'pnl_pct': pnl_pct * 100,
                        'exit_reason': exit_reason
                    })
                    
                    del positions[symbol]
            
            else:
                # No position - check for buy signal
                if signal > SIGNAL_THRESHOLD:
                    position_value = capital * allocation * LEVERAGE
                    quantity = position_value / current_price
                    
                    if position_value >= 100:  # Minimum position size
                        positions[symbol] = {
                            'entry_price': current_price,
                            'quantity': quantity,
                            'entry_time': current_time
                        }
    
    print()
    print()
    
    # Close remaining positions
    final_time = timeline[-1]
    for symbol, position in list(positions.items()):
        if final_time in HISTORICAL_DATA[symbol].index:
            current_price = HISTORICAL_DATA[symbol].loc[final_time, 'Close']
            entry_price = position['entry_price']
            pnl_pct = (current_price - entry_price) / entry_price
            pnl = (current_price - position['entry_price']) * position['quantity']
            capital += pnl
            
            trades_log.append({
                'symbol': symbol,
                'entry_time': position['entry_time'],
                'exit_time': final_time,
                'entry_price': entry_price,
                'exit_price': current_price,
                'pnl': pnl,
                'pnl_pct': pnl_pct * 100,
                'exit_reason': 'close'
            })
    
    # Calculate metrics
    total_return = (capital - initial_capital) / initial_capital * 100
    total_trades = len(trades_log)
    winning_trades = [t for t in trades_log if t['pnl'] > 0]
    losing_trades = [t for t in trades_log if t['pnl'] <= 0]
    
    win_rate = len(winning_trades) / total_trades * 100 if total_trades > 0 else 0
    
    avg_win = sum(t['pnl'] for t in winning_trades) / len(winning_trades) if winning_trades else 0
    avg_loss = sum(t['pnl'] for t in losing_trades) / len(losing_trades) if losing_trades else 0
    
    # Calculate trades per asset
    trades_by_symbol = {}
    for trade in trades_log:
        symbol = trade['symbol']
        if symbol not in trades_by_symbol:
            trades_by_symbol[symbol] = 0
        trades_by_symbol[symbol] += 1
    
    # Results
    print("=" * 80)
    print("BACKTEST RESULTS")
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
    print(f"🔍 Signals Checked:    {signals_checked:,}")
    print(f"⏱️  Trading Days:       {len(timeline)/(24):.0f}")
    print(f"📈 Trades/Day:         {total_trades / (len(timeline)/24):.2f}")
    print()
    
    # Show top trading assets
    print("Top 10 Most Active Assets:")
    sorted_assets = sorted(trades_by_symbol.items(), key=lambda x: x[1], reverse=True)[:10]
    for symbol, count in sorted_assets:
        print(f"  {symbol:15s} {count:3d} trades")
    print()
    
    # Show recent trades
    if trades_log:
        print("Last 5 Trades:")
        for trade in trades_log[-5:]:
            pnl_emoji = "✅" if trade['pnl'] > 0 else "❌"
            print(f"  {pnl_emoji} {trade['symbol']:10s} {trade['pnl_pct']:+6.2f}% (${trade['pnl']:+8.2f}) - {trade['exit_reason']}")
    
    print()
    print("=" * 80)

if __name__ == "__main__":
    run_backtest_100_assets()
