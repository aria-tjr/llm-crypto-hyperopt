#!/usr/bin/env python3
"""
Analyze trade history to diagnose balance reduction from $13,000 to $12,533
"""
import configparser
from pybit.unified_trading import HTTP
from datetime import datetime, timedelta

# Load config
config = configparser.ConfigParser()
config.read('src/config.ini')

api_key = config.get('bybit', 'api_key')
api_secret = config.get('bybit', 'api_secret')

# Initialize connection
session = HTTP(
    testnet=False,
    api_key=api_key,
    api_secret=api_secret,
    demo=True
)

print("=" * 100)
print("🔍 TRADE HISTORY ANALYSIS - Balance Reduction Diagnosis".center(100))
print("=" * 100)
print()

print("📊 Current Status:")
print("-" * 100)
print(f"  Starting Balance (estimated): $13,000.00")
print(f"  Current Wallet Balance:       $12,533.16")
print(f"  Current Equity (with PnL):    $12,855.56")
print(f"  Unrealized P&L:               +$322.40")
print(f"  Balance Reduction:            -$466.84 (-3.59%)")
print()
print("  🔍 Analysis Goal: Find realized losses that caused the $467 reduction")
print()

# Get closed P&L records
print("💰 CLOSED P&L HISTORY (Last 50 trades):")
print("-" * 100)

try:
    # Get closed P&L from the last 7 days
    response = session.get_closed_pnl(
        category="linear",
        limit=50
    )
    
    if response['retCode'] == 0:
        closed_trades = response['result']['list']
        
        if not closed_trades:
            print("  ℹ️  No closed trades found in recent history")
            print("  💡 Balance reduction may be from:")
            print("     - Trading fees on opening current positions")
            print("     - Previous closed trades outside the query window")
            print("     - Initial demo account setup")
        else:
            print(f"{'Date':<20} {'Symbol':<15} {'Side':<6} {'Qty':<12} {'Entry':<10} {'Exit':<10} {'PnL':<12} {'Fee':<10}")
            print("-" * 100)
            
            total_realized_pnl = 0
            total_fees = 0
            winning_trades = 0
            losing_trades = 0
            trades_by_symbol = {}
            
            for trade in closed_trades:
                symbol = trade['symbol']
                side = trade['side']
                qty = float(trade['qty'])
                avg_entry = float(trade['avgEntryPrice'])
                avg_exit = float(trade['avgExitPrice'])
                closed_pnl = float(trade['closedPnl'])
                created_time = int(trade['createdTime'])
                
                # Convert timestamp
                dt = datetime.fromtimestamp(created_time / 1000)
                date_str = dt.strftime('%Y-%m-%d %H:%M:%S')
                
                # Estimate fee (Bybit maker/taker fees ~0.055%)
                position_value = qty * avg_entry
                estimated_fee = position_value * 0.00055 * 2  # Entry + exit
                
                total_realized_pnl += closed_pnl
                total_fees += estimated_fee
                
                if closed_pnl > 0:
                    winning_trades += 1
                else:
                    losing_trades += 1
                
                # Track by symbol
                if symbol not in trades_by_symbol:
                    trades_by_symbol[symbol] = {'count': 0, 'pnl': 0, 'fees': 0}
                trades_by_symbol[symbol]['count'] += 1
                trades_by_symbol[symbol]['pnl'] += closed_pnl
                trades_by_symbol[symbol]['fees'] += estimated_fee
                
                side_emoji = "🟢" if side == "Buy" else "🔴"
                pnl_str = f"${closed_pnl:+.2f}"
                
                print(f"{date_str:<20} {symbol:<15} {side_emoji:<6} {qty:<12.2f} ${avg_entry:<9.4f} ${avg_exit:<9.4f} {pnl_str:<12} ${estimated_fee:<9.2f}")
            
            print("-" * 100)
            print(f"{'TOTALS':<54} {'Realized PnL:':<22} ${total_realized_pnl:+.2f}")
            print(f"{'':54} {'Estimated Fees:':<22} -${total_fees:.2f}")
            print(f"{'':54} {'Net Impact:':<22} ${total_realized_pnl - total_fees:+.2f}")
            
            print()
            print()
            print("📊 TRADE STATISTICS:")
            print("-" * 100)
            print(f"  Total Closed Trades:    {len(closed_trades)}")
            print(f"  Winning Trades:         {winning_trades} ({winning_trades/len(closed_trades)*100:.1f}%)")
            print(f"  Losing Trades:          {losing_trades} ({losing_trades/len(closed_trades)*100:.1f}%)")
            print(f"  Win Rate:               {winning_trades/len(closed_trades)*100:.1f}%")
            print()
            print(f"  Total Realized P&L:     ${total_realized_pnl:+.2f}")
            print(f"  Total Trading Fees:     -${total_fees:.2f}")
            print(f"  Net Realized:           ${total_realized_pnl - total_fees:+.2f}")
            
            # Analysis by symbol
            if trades_by_symbol:
                print()
                print("📈 PERFORMANCE BY SYMBOL:")
                print("-" * 100)
                print(f"{'Symbol':<15} {'Trades':<10} {'Total PnL':<15} {'Avg PnL':<15} {'Total Fees':<15}")
                print("-" * 100)
                
                sorted_symbols = sorted(trades_by_symbol.items(), key=lambda x: x[1]['pnl'])
                
                for symbol, data in sorted_symbols:
                    avg_pnl = data['pnl'] / data['count']
                    print(f"{symbol:<15} {data['count']:<10} ${data['pnl']:+14.2f} ${avg_pnl:+14.2f} ${data['fees']:<14.2f}")
            
            print()
            print()
            print("🔍 DIAGNOSIS:")
            print("-" * 100)
            
            net_realized = total_realized_pnl - total_fees
            unaccounted = -466.84 - net_realized
            
            print(f"  Balance Lost:               -$466.84")
            print(f"  Realized PnL from trades:   ${total_realized_pnl:+.2f}")
            print(f"  Trading fees:               -${total_fees:.2f}")
            print(f"  Net from closed trades:     ${net_realized:+.2f}")
            print(f"  Unaccounted difference:     ${unaccounted:+.2f}")
            print()
            
            if abs(unaccounted) > 10:
                print("  ⚠️  Possible causes of unaccounted loss:")
                print("     1. Fees from opening current 7 positions (~$70-100 estimated)")
                print("     2. Trades closed before the history window")
                print("     3. Funding fees (8-hour intervals)")
                print("     4. Initial demo account balance was actually lower than $13,000")
            else:
                print("  ✅ Loss fully explained by closed trades and fees")
                
except Exception as e:
    print(f"  ❌ Error fetching trade history: {str(e)}")

print()

# Check transaction history for more details
print()
print("💳 TRANSACTION HISTORY (All recent activity):")
print("-" * 100)

try:
    response = session.get_transaction_log(
        category="linear",
        limit=30
    )
    
    if response['retCode'] == 0:
        transactions = response['result']['list']
        
        if transactions:
            print(f"{'Date':<20} {'Type':<20} {'Symbol':<15} {'Amount':<15} {'Balance':<15}")
            print("-" * 100)
            
            for txn in transactions[:20]:  # Show last 20
                txn_type = txn.get('type', 'UNKNOWN')
                symbol = txn.get('symbol', '-')
                amount = float(txn.get('cashFlow', 0))
                balance = float(txn.get('walletBalance', 0))
                timestamp = int(txn.get('transactionTime', 0))
                
                dt = datetime.fromtimestamp(timestamp / 1000) if timestamp else datetime.now()
                date_str = dt.strftime('%Y-%m-%d %H:%M:%S')
                
                amount_str = f"${amount:+.2f}" if amount != 0 else "$0.00"
                balance_str = f"${balance:.2f}" if balance != 0 else "-"
                
                print(f"{date_str:<20} {txn_type:<20} {symbol:<15} {amount_str:<15} {balance_str:<15}")
                
        else:
            print("  ℹ️  No transaction history available")
            
except Exception as e:
    print(f"  ⚠️  Transaction history not available: {str(e)}")

print()
print("=" * 100)
