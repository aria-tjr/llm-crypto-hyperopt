"""
Check closed trades for both bot accounts via Bybit API
"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

import configparser
from components.bybit_connector import BybitConnector

def load_config(config_file='src/config.ini'):
    config = configparser.ConfigParser()
    config.read(config_file)
    return config

def check_account_trades(config_file, account_name):
    print(f"\n{'='*80}")
    print(f"📊 {account_name} - TRADE HISTORY")
    print(f"{'='*80}\n")
    
    config = load_config(config_file)
    api_key = config.get('bybit', 'api_key')
    api_secret = config.get('bybit', 'api_secret')
    
    print(f"API Key: {api_key[:10]}...")
    
    bybit = BybitConnector(api_key, api_secret, demo=True)
    
    # Get balance
    balance = bybit.get_balance("USDT")
    if balance:
        print(f"\n💰 Balance:")
        print(f"   Wallet: ${balance.get('wallet_balance', 0):,.2f}")
        print(f"   Available: ${balance.get('available_balance', 0):,.2f}")
        print(f"   Total Equity: ${balance.get('equity', 0):,.2f}")
        print(f"   Unrealized PnL: ${balance.get('unrealised_pnl', 0):+,.2f}")
    
    # Get open positions
    positions = bybit.get_all_positions()
    if positions:
        print(f"\n📈 Open Positions: {len(positions)}")
        for pos in positions:
            symbol = pos.get('symbol', 'N/A')
            side = pos.get('side', 'N/A')
            size = pos.get('size', 0)
            entry = pos.get('avgPrice', 0)
            mark = pos.get('markPrice', 0)
            pnl = pos.get('unrealisedPnl', 0)
            pnl_pct = (mark - entry) / entry * 100 if entry > 0 else 0
            
            emoji = "🟢" if pnl > 0 else "🔴"
            print(f"   {emoji} {symbol:12s} {side:5s} {size:>10} @ ${entry:>10,.2f} | "
                  f"Mark: ${mark:>10,.2f} | PnL: ${pnl:>8,.2f} ({pnl_pct:+.2f}%)")
    else:
        print(f"\n📈 Open Positions: 0")
    
    # Get closed PnL history
    print(f"\n💸 Closed Trade History (Last 50):")
    try:
        from pybit.unified_trading import HTTP
        session = HTTP(
            testnet=True,
            api_key=api_key,
            api_secret=api_secret,
        )
        
        # Get closed PnL
        response = session.get_closed_pnl(
            category="linear",
            limit=50
        )
        
        if response['retCode'] == 0:
            trades = response['result']['list']
            if trades:
                total_pnl = 0
                win_count = 0
                loss_count = 0
                
                print(f"\n   Found {len(trades)} closed trades:\n")
                print(f"   {'Symbol':<12} {'Side':<6} {'Qty':<12} {'Entry':<12} {'Exit':<12} {'PnL':<12} {'%':<8}")
                print(f"   {'-'*80}")
                
                for trade in trades:
                    symbol = trade.get('symbol', 'N/A')
                    side = trade.get('side', 'N/A')
                    qty = float(trade.get('qty', 0))
                    entry = float(trade.get('avgEntryPrice', 0))
                    exit_price = float(trade.get('avgExitPrice', 0))
                    pnl = float(trade.get('closedPnl', 0))
                    
                    pnl_pct = ((exit_price - entry) / entry * 100) if entry > 0 else 0
                    
                    total_pnl += pnl
                    if pnl > 0:
                        win_count += 1
                        emoji = "✅"
                    else:
                        loss_count += 1
                        emoji = "❌"
                    
                    print(f"   {emoji} {symbol:<10} {side:<6} {qty:<12.4f} ${entry:<11.2f} ${exit_price:<11.2f} "
                          f"${pnl:<11.2f} {pnl_pct:>+7.2f}%")
                
                print(f"\n   {'='*80}")
                print(f"   Total PnL: ${total_pnl:+,.2f}")
                print(f"   Wins: {win_count} | Losses: {loss_count} | Win Rate: {win_count/(win_count+loss_count)*100:.1f}%")
            else:
                print(f"   ℹ️  No closed trades found")
        else:
            print(f"   ⚠️  Error: {response['retMsg']}")
            
    except Exception as e:
        print(f"   ⚠️  Error fetching closed trades: {e}")
    
    print()

if __name__ == "__main__":
    # Check Bot 1
    check_account_trades('src/config.ini', 'BOT 1 (snbEe1...)')
    
    # Check Bot 2
    check_account_trades('src/config2.ini', 'BOT 2 (pzYRPP...)')
