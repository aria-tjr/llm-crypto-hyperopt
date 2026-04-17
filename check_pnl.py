"""Check current P&L and bot performance"""
import sys
import os
sys.path.append(os.path.dirname(__file__))

from src.components.bybit_connector import BybitConnector
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

API_KEY = os.getenv('BYBIT_API_KEY')
API_SECRET = os.getenv('BYBIT_API_SECRET')

# Connect to Bybit
bybit = BybitConnector(API_KEY, API_SECRET, demo=True)

print("=" * 80)
print("📊 TRADING BOT PERFORMANCE CHECK")
print("=" * 80)
print()

# Get account balance
balance_info = bybit.get_balance()
if balance_info:
    equity = balance_info['equity']
    available = balance_info['available_balance']
    wallet = balance_info['wallet_balance']
    
    print("💰 Account Balance:")
    print(f"  Equity:    ${equity:,.2f}")
    print(f"  Wallet:    ${wallet:,.2f}")
    print(f"  Available: ${available:,.2f}")
    print()

# Get all positions
positions = bybit.get_all_positions()

if positions:
    print(f"📈 Open Positions: {len(positions)}")
    print()
    print(f"{'Symbol':<15} {'Side':<6} {'Size':<12} {'Leverage':<8} {'Entry':<10} {'Current':<10} {'PnL $':<12} {'PnL %':<8}")
    print("=" * 100)
    
    total_pnl = 0
    total_value = 0
    long_count = 0
    short_count = 0
    profitable = 0
    losing = 0
    
    for pos in positions:
        symbol = pos['symbol']
        side = pos['side']
        size = pos['size']
        leverage = pos['leverage']
        entry = pos['entry_price']
        pnl = pos['unrealised_pnl']
        
        # Get current price
        ticker = bybit.get_ticker(symbol)
        if ticker:
            current_price = ticker['last_price']
            position_value = size * entry
            pnl_pct = (pnl / position_value) * 100 if position_value > 0 else 0
            
            # Count statistics
            total_pnl += pnl
            total_value += position_value
            
            if side == "Buy":
                long_count += 1
            else:
                short_count += 1
                
            if pnl > 0:
                profitable += 1
                pnl_symbol = "🟢"
            else:
                losing += 1
                pnl_symbol = "🔴"
            
            print(f"{symbol:<15} {side:<6} {size:<12.4f} {leverage:<8.0f}x ${entry:<9.4f} ${current_price:<9.4f} {pnl_symbol}${pnl:>10.2f} {pnl_pct:>7.2f}%")
    
    print("=" * 100)
    print()
    print("📊 Summary:")
    print(f"  Total Positions:      {len(positions)}")
    print(f"  Long Positions:       {long_count}")
    print(f"  Short Positions:      {short_count}")
    print(f"  Profitable Positions: {profitable} ({profitable/len(positions)*100:.1f}%)")
    print(f"  Losing Positions:     {losing} ({losing/len(positions)*100:.1f}%)")
    print()
    print(f"  Total Position Value: ${total_value:,.2f}")
    print(f"  Total Unrealized P&L: ${total_pnl:,.2f}")
    if total_value > 0:
        avg_return = (total_pnl / total_value) * 100
        print(f"  Average Return:       {avg_return:.2f}%")
    print()
    
    # Calculate leverage usage
    if balance_info:
        leverage_used = total_value / wallet if wallet > 0 else 0
        print(f"  Leverage Used:        {leverage_used:.2f}x (of available capital)")
        print(f"  Margin Used:          ${total_value/leverage:.2f} ({total_value/leverage/wallet*100:.1f}% of wallet)")
    
else:
    print("No open positions found")

print()
print("=" * 80)
