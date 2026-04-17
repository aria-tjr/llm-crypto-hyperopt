"""
Backtest Hybrid Trading System (Technical + LLM)
Tests LLM-enhanced trading against historical data
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from src.components.signal_generator import generate_trading_signal
from src.components.llm_signal_analyzer import get_hybrid_signal


def fetch_historical_data(symbol, start_date, end_date, interval="1h"):
    """Fetch historical price data"""
    print(f"Fetching {symbol} data from {start_date} to {end_date}...")
    ticker = yf.Ticker(symbol)
    df = ticker.history(start=start_date, end=end_date, interval=interval)
    print(f"✅ Fetched {len(df)} candles")
    return df


def run_hybrid_backtest(symbols, start_date, end_date, initial_capital=10000, leverage=5):
    """
    Run backtest with hybrid LLM + technical system
    """
    print("=" * 80)
    print("HYBRID LLM + TECHNICAL TRADING BACKTEST")
    print("=" * 80)
    print(f"Period: {start_date} to {end_date}")
    print(f"Initial Capital: ${initial_capital:,.2f}")
    print(f"Leverage: {leverage}x")
    print(f"Mode: LLM interprets technical indicators")
    print("=" * 80)
    print()
    
    # Settings
    CONFIDENCE_THRESHOLD = 60  # LLM must be 60%+ confident
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
    
    # Portfolio tracking
    capital = initial_capital
    positions = {}
    trades_log = []
    
    # Fetch data
    print("📊 Fetching historical data...")
    historical_data = {}
    for symbol in symbols:
        try:
            df = fetch_historical_data(symbol, start_date, end_date, interval="1h")
            if len(df) > 0:
                historical_data[symbol] = df
        except Exception as e:
            print(f"⚠️  Error fetching {symbol}: {str(e)}")
    
    if not historical_data:
        print("❌ No data fetched.")
        return None
    
    print(f"✅ Fetched data for {len(historical_data)} assets")
    print()
    
    # Get timeline
    all_dates = set()
    for df in historical_data.values():
        all_dates.update(df.index)
    timeline = sorted(list(all_dates))
    
    print(f"📈 Running hybrid backtest ({len(timeline)} periods)...")
    print("This may take a while due to LLM API calls...")
    print()
    
    # Main backtest loop
    for i, current_time in enumerate(timeline):
        if i < LOOKBACK_PERIODS:
            continue
        
        # Progress indicator
        if i % 50 == 0:
            progress = (i / len(timeline)) * 100
            print(f"Progress: {progress:.1f}% | Capital: ${capital:,.2f}")
        
        for symbol in historical_data.keys():
            df = historical_data[symbol]
            
            if current_time not in df.index:
                continue
            
            current_price = df.loc[current_time, 'Close']
            prices = df.loc[:current_time, 'Close'].tail(LOOKBACK_PERIODS).tolist()
            
            if len(prices) < LOOKBACK_PERIODS:
                continue
            
            # Generate technical signals
            signal_data = generate_trading_signal(prices)
            
            allocation = allocations.get(symbol, 0)
            
            # Check existing position
            if symbol in positions:
                position = positions[symbol]
                entry_price = position['entry_price']
                pnl_pct = (current_price - entry_price) / entry_price
                
                # Build market context for LLM
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
                
                # LLM says sell with high confidence
                if llm_decision == 'SELL' and confidence >= CONFIDENCE_THRESHOLD:
                    should_exit = True
                    exit_reason = f"LLM_SELL_{confidence}%"
                
                # Take profit
                elif pnl_pct >= TAKE_PROFIT_PCT:
                    should_exit = True
                    exit_reason = "TAKE_PROFIT"
                
                # Stop loss
                elif pnl_pct <= -STOP_LOSS_PCT:
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
                        'price': current_price,
                        'quantity': position['quantity'],
                        'pnl': pnl,
                        'pnl_pct': pnl_pct * 100,
                        'capital': capital,
                        'llm_decision': llm_decision,
                        'confidence': confidence
                    })
                    
                    del positions[symbol]
            
            else:
                # No position - check if LLM says buy
                market_context = {'has_position': False}
                
                # Get LLM analysis
                hybrid_result = get_hybrid_signal(signal_data, symbol, current_price, market_context)
                llm_decision = hybrid_result['final_decision']
                confidence = hybrid_result['confidence']
                
                if llm_decision == 'BUY' and confidence >= CONFIDENCE_THRESHOLD:
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
                            'reason': f'LLM_BUY_{confidence}%',
                            'price': current_price,
                            'quantity': quantity,
                            'capital': capital,
                            'llm_decision': llm_decision,
                            'confidence': confidence,
                            'technical_signal': hybrid_result['technical_signal'],
                            'llm_agrees': hybrid_result['llm_agrees']
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
                'reason': 'END_OF_BACKTEST',
                'price': current_price,
                'pnl': pnl,
                'pnl_pct': pnl_pct * 100,
                'capital': capital
            })
    
    # Calculate results
    final_capital = capital
    total_return = (final_capital - initial_capital) / initial_capital * 100
    
    # Win/loss stats
    closed_trades = [t for t in trades_log if t['action'] == 'CLOSE' and 'pnl' in t]
    winning_trades = [t for t in closed_trades if t['pnl'] > 0]
    losing_trades = [t for t in closed_trades if t['pnl'] < 0]
    total_closed = len(closed_trades)
    win_rate = (len(winning_trades) / total_closed * 100) if total_closed > 0 else 0
    
    # LLM agreement stats
    opens = [t for t in trades_log if t['action'] == 'OPEN' and 'llm_agrees' in t]
    llm_agrees_count = len([t for t in opens if t['llm_agrees']])
    llm_overrides_count = len([t for t in opens if not t['llm_agrees']])
    
    # Print results
    print()
    print("=" * 80)
    print("HYBRID BACKTEST RESULTS")
    print("=" * 80)
    print(f"Initial Capital:    ${initial_capital:,.2f}")
    print(f"Final Capital:      ${final_capital:,.2f}")
    print(f"Total Return:       {total_return:+.2f}%")
    print()
    print(f"Total Trades:       {len(trades_log)}")
    print(f"Closed Trades:      {total_closed}")
    print(f"Winning Trades:     {len(winning_trades)}")
    print(f"Losing Trades:      {len(losing_trades)}")
    print(f"Win Rate:           {win_rate:.1f}%")
    print()
    print("LLM Analysis:")
    print(f"  LLM Agreed w/ Technical:  {llm_agrees_count} trades")
    print(f"  LLM Overrode Technical:   {llm_overrides_count} trades")
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
    for trade in trades_log[-15:]:
        if trade['action'] == 'OPEN':
            agrees = "✅" if trade.get('llm_agrees') else "⚠️ "
            print(f"{trade['time']} | {trade['symbol']:8s} | OPEN  | ${trade['price']:8,.2f} | {agrees} {trade['reason']} | Tech:{trade.get('technical_signal', 0):+.2f}")
        else:
            print(f"{trade['time']} | {trade['symbol']:8s} | CLOSE | ${trade['price']:8,.2f} | {trade['reason']:20s} | PnL: ${trade.get('pnl', 0):+,.2f} ({trade.get('pnl_pct', 0):+.1f}%)")
    
    print("=" * 80)
    
    return {
        'initial_capital': initial_capital,
        'final_capital': final_capital,
        'total_return': total_return,
        'trades': trades_log,
        'win_rate': win_rate,
        'llm_agrees': llm_agrees_count,
        'llm_overrides': llm_overrides_count
    }


if __name__ == "__main__":
    # Test with last 7 days (shorter period for faster LLM testing)
    symbols = ["BTC-USD", "ETH-USD"]  # Just 2 symbols to reduce API calls
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    
    print("⚠️  NOTE: This will make many LLM API calls and may take 5-10 minutes!")
    print()
    
    results = run_hybrid_backtest(
        symbols=symbols,
        start_date=start_date.strftime("%Y-%m-%d"),
        end_date=end_date.strftime("%Y-%m-%d"),
        initial_capital=10000,
        leverage=5
    )
