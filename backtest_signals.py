"""
Backtest Trading Bot with Technical Signal Generation
Tests the signal-based trading strategy against historical data
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from src.components.signal_generator import generate_trading_signal


def fetch_historical_data(symbol, start_date, end_date, interval="15m"):
    """
    Fetch historical price data from Yahoo Finance
    
    Args:
        symbol: Trading pair symbol (e.g., "BTC-USD")
        start_date: Start date for data
        end_date: End date for data
        interval: Data interval (1m, 5m, 15m, 1h, 1d, etc.)
        
    Returns:
        DataFrame with OHLCV data
    """
    print(f"Fetching {symbol} data from {start_date} to {end_date}...")
    ticker = yf.Ticker(symbol)
    df = ticker.history(start=start_date, end=end_date, interval=interval)
    print(f"✅ Fetched {len(df)} candles")
    return df


def run_backtest(symbols, start_date, end_date, initial_capital=10000, leverage=5):
    """
    Run backtest simulation with signal-based trading
    
    Args:
        symbols: List of symbols to trade
        start_date: Start date for backtest
        end_date: End date for backtest
        initial_capital: Starting capital in USD
        leverage: Trading leverage
        
    Returns:
        Dictionary with backtest results
    """
    print("=" * 80)
    print("SIGNAL-BASED TRADING BACKTEST")
    print("=" * 80)
    print(f"Period: {start_date} to {end_date}")
    print(f"Initial Capital: ${initial_capital:,.2f}")
    print(f"Leverage: {leverage}x")
    print(f"Assets: {len(symbols)}")
    print("=" * 80)
    print()
    
    # Portfolio settings
    SIGNAL_THRESHOLD = 0.3
    STOP_LOSS_PCT = 0.03
    TAKE_PROFIT_PCT = 0.08
    LOOKBACK_PERIODS = 100
    
    allocations = {
        "BTC-USD": 0.25,
        "ETH-USD": 0.20,
        "SOL-USD": 0.10,
        "AVAX-USD": 0.10,
        "BNB-USD": 0.10
    }
    
    # Track portfolio
    capital = initial_capital
    positions = {}
    trades_log = []
    equity_curve = []
    
    # Fetch historical data for all symbols
    print("📊 Fetching historical data...")
    historical_data = {}
    for symbol in symbols:
        try:
            df = fetch_historical_data(symbol, start_date, end_date, interval="1h")
            if len(df) > 0:
                historical_data[symbol] = df
            else:
                print(f"⚠️  No data for {symbol}, skipping")
        except Exception as e:
            print(f"⚠️  Error fetching {symbol}: {str(e)}")
    
    if not historical_data:
        print("❌ No data fetched. Exiting.")
        return None
    
    print(f"✅ Fetched data for {len(historical_data)} assets")
    print()
    
    # Get the common timeline
    all_dates = set()
    for df in historical_data.values():
        all_dates.update(df.index)
    
    timeline = sorted(list(all_dates))
    
    if len(timeline) < LOOKBACK_PERIODS:
        print(f"⚠️  Warning: Only {len(timeline)} periods available, less than lookback period of {LOOKBACK_PERIODS}")
    
    print(f"📈 Running backtest simulation ({len(timeline)} periods)...")
    print()
    
    # Main backtest loop
    for i, current_time in enumerate(timeline):
        if i < LOOKBACK_PERIODS:
            continue  # Need enough history for signals
        
        # Check each asset
        for symbol in historical_data.keys():
            df = historical_data[symbol]
            
            # Skip if no data at this time
            if current_time not in df.index:
                continue
            
            current_price = df.loc[current_time, 'Close']
            
            # Get historical prices for signal generation
            prices = df.loc[:current_time, 'Close'].tail(LOOKBACK_PERIODS).tolist()
            
            if len(prices) < LOOKBACK_PERIODS:
                continue
            
            # Generate trading signal
            signal_data = generate_trading_signal(prices)
            signal = signal_data['signal']
            action = signal_data['action']
            
            allocation = allocations.get(symbol, 0)
            
            # Check existing position
            if symbol in positions:
                position = positions[symbol]
                entry_price = position['entry_price']
                pnl_pct = (current_price - entry_price) / entry_price
                
                # Check exit conditions
                should_exit = False
                exit_reason = ""
                
                # Opposite signal
                if signal < -SIGNAL_THRESHOLD:
                    should_exit = True
                    exit_reason = "SELL_SIGNAL"
                
                # Take profit
                elif pnl_pct >= TAKE_PROFIT_PCT:
                    should_exit = True
                    exit_reason = "TAKE_PROFIT"
                
                # Stop loss
                elif pnl_pct <= -STOP_LOSS_PCT:
                    should_exit = True
                    exit_reason = "STOP_LOSS"
                
                if should_exit:
                    # Close position
                    position_value = position['quantity'] * current_price
                    pnl = (current_price - entry_price) * position['quantity']
                    capital += pnl
                    
                    trades_log.append({
                        'time': current_time,
                        'symbol': symbol,
                        'action': 'CLOSE',
                        'reason': exit_reason,
                        'price': current_price,
                        'quantity': position['quantity'],
                        'pnl': pnl,
                        'pnl_pct': pnl_pct * 100,
                        'capital': capital
                    })
                    
                    del positions[symbol]
            
            else:
                # No position - check if we should open one
                if signal > SIGNAL_THRESHOLD:
                    # Calculate position size
                    position_value = capital * allocation * leverage
                    quantity = position_value / current_price
                    
                    if position_value >= 100:  # Minimum trade
                        positions[symbol] = {
                            'entry_price': current_price,
                            'quantity': quantity,
                            'entry_time': current_time
                        }
                        
                        trades_log.append({
                            'time': current_time,
                            'symbol': symbol,
                            'action': 'OPEN',
                            'reason': 'BUY_SIGNAL',
                            'price': current_price,
                            'quantity': quantity,
                            'signal': signal,
                            'capital': capital
                        })
        
        # Calculate current equity
        equity = capital
        for symbol, position in positions.items():
            if current_time in historical_data[symbol].index:
                current_price = historical_data[symbol].loc[current_time, 'Close']
                position_value = position['quantity'] * current_price
                entry_value = position['quantity'] * position['entry_price']
                unrealized_pnl = position_value - entry_value
                equity += unrealized_pnl
        
        equity_curve.append({
            'time': current_time,
            'equity': equity,
            'capital': capital,
            'positions': len(positions)
        })
    
    # Close all remaining positions at end
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
                'reason': 'END_OF_BACKTEST',
                'price': current_price,
                'quantity': position['quantity'],
                'pnl': pnl,
                'pnl_pct': pnl_pct * 100,
                'capital': capital
            })
    
    # Calculate results
    final_capital = capital
    total_return = (final_capital - initial_capital) / initial_capital * 100
    
    # Calculate max drawdown
    peak = initial_capital
    max_drawdown = 0
    for point in equity_curve:
        if point['equity'] > peak:
            peak = point['equity']
        drawdown = (peak - point['equity']) / peak * 100
        if drawdown > max_drawdown:
            max_drawdown = drawdown
    
    # Win rate
    winning_trades = [t for t in trades_log if t['action'] == 'CLOSE' and t.get('pnl', 0) > 0]
    losing_trades = [t for t in trades_log if t['action'] == 'CLOSE' and t.get('pnl', 0) < 0]
    total_closed_trades = len(winning_trades) + len(losing_trades)
    win_rate = (len(winning_trades) / total_closed_trades * 100) if total_closed_trades > 0 else 0
    
    # Print results
    print()
    print("=" * 80)
    print("BACKTEST RESULTS")
    print("=" * 80)
    print(f"Initial Capital:    ${initial_capital:,.2f}")
    print(f"Final Capital:      ${final_capital:,.2f}")
    print(f"Total Return:       {total_return:+.2f}%")
    print(f"Max Drawdown:       {max_drawdown:.2f}%")
    print()
    print(f"Total Trades:       {len(trades_log)}")
    print(f"Closed Trades:      {total_closed_trades}")
    print(f"Winning Trades:     {len(winning_trades)}")
    print(f"Losing Trades:      {len(losing_trades)}")
    print(f"Win Rate:           {win_rate:.1f}%")
    print()
    
    if winning_trades:
        avg_win = sum(t['pnl'] for t in winning_trades) / len(winning_trades)
        print(f"Average Win:        ${avg_win:,.2f}")
    
    if losing_trades:
        avg_loss = sum(t['pnl'] for t in losing_trades) / len(losing_trades)
        print(f"Average Loss:       ${avg_loss:,.2f}")
    
    print()
    print("Recent Trades:")
    print("-" * 80)
    for trade in trades_log[-10:]:
        if trade['action'] == 'OPEN':
            print(f"{trade['time']} | {trade['symbol']:8s} | OPEN  | ${trade['price']:8,.2f} | Signal: {trade.get('signal', 0):+.2f}")
        else:
            print(f"{trade['time']} | {trade['symbol']:8s} | CLOSE | ${trade['price']:8,.2f} | {trade['reason']:15s} | PnL: ${trade.get('pnl', 0):+,.2f} ({trade.get('pnl_pct', 0):+.1f}%)")
    
    print("=" * 80)
    
    return {
        'initial_capital': initial_capital,
        'final_capital': final_capital,
        'total_return': total_return,
        'max_drawdown': max_drawdown,
        'trades': trades_log,
        'equity_curve': equity_curve,
        'win_rate': win_rate,
        'total_trades': len(trades_log),
        'winning_trades': len(winning_trades),
        'losing_trades': len(losing_trades)
    }


if __name__ == "__main__":
    # Backtest configuration
    symbols = ["BTC-USD", "ETH-USD", "SOL-USD", "AVAX-USD", "BNB-USD"]
    
    # Use last 14 days
    end_date = datetime.now()
    start_date = end_date - timedelta(days=14)
    
    results = run_backtest(
        symbols=symbols,
        start_date=start_date.strftime("%Y-%m-%d"),
        end_date=end_date.strftime("%Y-%m-%d"),
        initial_capital=10000,
        leverage=5
    )
