"""
Analyze performance since Feb 5th 1:38 AM restart only
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import configparser
from pybit.unified_trading import HTTP
from datetime import datetime, timedelta

def load_config(config_file):
    config = configparser.ConfigParser()
    config.read(config_file)
    return config

def analyze_since_restart(config_file, account_name, starting_balance, restart_time_str):
    print(f"\n{'='*60}")
    print(f"  {account_name}")
    print(f"{'='*60}")
    
    config = load_config(config_file)
    api_key = config.get('bybit', 'api_key')
    api_secret = config.get('bybit', 'api_secret')
    
    session = HTTP(
        testnet=False,
        api_key=api_key,
        api_secret=api_secret,
        demo=True
    )
    
    # Parse restart time
    restart_time = datetime.strptime(restart_time_str, "%Y-%m-%d %H:%M")
    print(f"🔄 Bot Restart: {restart_time.strftime('%B %d, %Y at %H:%M')}")
    print(f"💰 Starting Balance: ${starting_balance:,.2f}")
    
    try:
        # Get current wallet
        wallet_response = session.get_wallet_balance(accountType="UNIFIED", coin="USDT")
        if wallet_response['retCode'] == 0:
            usdt_balance = None
            for coin in wallet_response['result']['list'][0]['coin']:
                if coin['coin'] == 'USDT':
                    usdt_balance = coin
                    break
            
            if usdt_balance:
                current_equity = float(usdt_balance['equity'])
                print(f"💰 Current Equity: ${current_equity:,.2f}")
                print(f"📈 Change: ${current_equity - starting_balance:+,.2f} ({((current_equity - starting_balance) / starting_balance * 100):+.2f}%)")
                
                # Get closed trades since restart
                print(f"\n🔍 Analyzing trades since restart...")
                end_time = int(datetime.now().timestamp() * 1000)
                start_time = int(restart_time.timestamp() * 1000)
                
                pnl_response = session.get_closed_pnl(
                    category="linear",
                    startTime=start_time,
                    endTime=end_time,
                    limit=200
                )
                
                if pnl_response['retCode'] == 0:
                    pnl_list = pnl_response['result'].get('list', [])
                    
                    # Filter trades after restart
                    trades_since_restart = []
                    for record in pnl_list:
                        trade_time = datetime.fromtimestamp(int(record.get('updatedTime', 0)) / 1000)
                        if trade_time >= restart_time:
                            trades_since_restart.append(record)
                    
                    print(f"✅ Found {len(trades_since_restart)} closed trades since restart")
                    
                    if trades_since_restart:
                        # Sort by time
                        trades_sorted = sorted(trades_since_restart, key=lambda x: int(x.get('updatedTime', 0)))
                        
                        print(f"\n{'='*60}")
                        print(f"📋 ALL TRADES SINCE RESTART")
                        print("="*100)
                        
                        total_pnl = 0
                        wins = 0
                        losses = 0
                        
                        for i, record in enumerate(trades_sorted):
                            symbol = record.get('symbol', 'N/A')
                            side = record.get('side', 'N/A')
                            entry_price = float(record.get('avgEntryPrice', 0))
                            exit_price = float(record.get('avgExitPrice', 0))
                            pnl = float(record.get('closedPnl', 0))
                            qty = float(record.get('closedSize', 0))
                            pnl_pct = (pnl / (qty * entry_price) * 100) if (qty * entry_price) > 0 else 0
                            trade_time = datetime.fromtimestamp(int(record.get('updatedTime', 0)) / 1000)
                            
                            total_pnl += pnl
                            if pnl > 0:
                                wins += 1
                                emoji = "🟢"
                            else:
                                losses += 1
                                emoji = "🔴"
                            
                            print(f"{i+1:2}. {emoji} {symbol:12} {side:4} | "
                                  f"${entry_price:>10.4f} → ${exit_price:>10.4f} | "
                                  f"P&L: ${pnl:>8.2f} ({pnl_pct:>6.2f}%) | "
                                  f"{trade_time.strftime('%m/%d %H:%M')}")
                        
                        print("="*100)
                        print(f"\n{'='*60}")
                        print(f"📊 STATISTICS SINCE RESTART")
                        print("="*60)
                        print(f"Total Trades: {len(trades_since_restart)}")
                        print(f"Wins: {wins} ({(wins/len(trades_since_restart)*100):.1f}%)")
                        print(f"Losses: {losses} ({(losses/len(trades_since_restart)*100):.1f}%)")
                        print(f"Total Realized P&L: ${total_pnl:+,.2f}")
                        
                        # Check for transaction log to find peak
                        print(f"\n🔍 Checking for equity peak since restart...")
                        tx_response = session.get_transaction_log(
                            accountType="UNIFIED",
                            category="linear",
                            startTime=start_time,
                            endTime=end_time,
                            limit=200
                        )
                        
                        if tx_response['retCode'] == 0:
                            tx_list = tx_response['result'].get('list', [])
                            
                            # Build equity curve
                            equity_points = [starting_balance]
                            for tx in tx_list:
                                tx_time = datetime.fromtimestamp(int(tx.get('transactionTime', 0)) / 1000)
                                if tx_time >= restart_time and 'cashBalance' in tx:
                                    balance = float(tx['cashBalance'])
                                    equity_points.append(balance)
                            
                            equity_points.append(current_equity)
                            
                            if len(equity_points) > 1:
                                highest_equity = max(equity_points)
                                lowest_equity = min(equity_points)
                                
                                print(f"\n{'='*60}")
                                print(f"🎯 EQUITY ANALYSIS (Since Restart)")
                                print("="*60)
                                print(f"💰 Starting: ${starting_balance:,.2f}")
                                print(f"🎯 Highest: ${highest_equity:,.2f} ({((highest_equity - starting_balance) / starting_balance * 100):+.2f}%)")
                                print(f"📉 Lowest: ${lowest_equity:,.2f} ({((lowest_equity - starting_balance) / starting_balance * 100):+.2f}%)")
                                print(f"💰 Current: ${current_equity:,.2f} ({((current_equity - starting_balance) / starting_balance * 100):+.2f}%)")
                                
                                if current_equity < highest_equity:
                                    drawdown = highest_equity - current_equity
                                    print(f"\n📊 Drawdown from Peak: ${drawdown:,.2f} ({(drawdown / highest_equity * 100):.2f}%)")
                                else:
                                    print(f"\n🚀 Currently at peak equity!")
                        
                    else:
                        print("⚠️  No closed trades found since restart")
                        print(f"💰 Equity change: ${current_equity - starting_balance:+,.2f} must be from open positions")
                        
                else:
                    print(f"❌ Could not fetch P&L: {pnl_response['retMsg']}")
                    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("\n" + "="*60)
    print("  PERFORMANCE SINCE LAST RESTART")
    print("  (Current Hyperopt Settings)")
    print("="*60)
    
    # Bot 1 - Started Feb 5 at 1:38 AM
    analyze_since_restart('src/config.ini', 'BOT 1', 6000.00, "2026-02-05 01:38")
    
    # Bot 2 - Started Feb 5 at 1:38 AM  
    analyze_since_restart('src/config2.ini', 'BOT 2', 10000.00, "2026-02-05 01:38")
    
    print("\n" + "="*60)
    print("  ANALYSIS COMPLETE")
    print("="*60 + "\n")
