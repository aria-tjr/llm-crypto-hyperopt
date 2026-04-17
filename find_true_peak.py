"""
Find peak including unrealized P&L from open positions
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

def find_true_peak(config_file, account_name, starting_balance, restart_time_str):
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
    
    restart_time = datetime.strptime(restart_time_str, "%Y-%m-%d %H:%M")
    
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
                current_unrealized = float(usdt_balance['unrealisedPnl'])
                
                print(f"💰 Starting Balance: ${starting_balance:,.2f}")
                print(f"💰 Current Equity: ${current_equity:,.2f}")
                print(f"📊 Current Unrealized P&L: ${current_unrealized:+,.2f}")
                
                # Get all position history (open and closed)
                print(f"\n🔍 Fetching position history...")
                end_time = int(datetime.now().timestamp() * 1000)
                start_time = int(restart_time.timestamp() * 1000)
                
                # Get execution history which shows all fills
                exec_response = session.get_executions(
                    category="linear",
                    startTime=start_time,
                    endTime=end_time,
                    limit=200
                )
                
                if exec_response['retCode'] == 0:
                    exec_list = exec_response['result'].get('list', [])
                    print(f"✅ Found {len(exec_list)} executions")
                    
                    # Track balance after each execution
                    print(f"\n📋 EXECUTION TIMELINE (showing balance changes):")
                    print("="*100)
                    
                    balance_points = []
                    
                    for i, exec in enumerate(exec_list[:50]):  # First 50
                        symbol = exec.get('symbol', 'N/A')
                        side = exec.get('side', 'N/A')
                        exec_type = exec.get('execType', 'N/A')
                        exec_price = float(exec.get('execPrice', 0))
                        exec_qty = float(exec.get('execQty', 0))
                        exec_value = float(exec.get('execValue', 0))
                        closed_pnl = float(exec.get('closedSize', 0))
                        exec_time = datetime.fromtimestamp(int(exec.get('execTime', 0)) / 1000)
                        
                        print(f"{exec_time.strftime('%m/%d %H:%M')} | {symbol:12} {side:4} {exec_type:10} | "
                              f"${exec_price:>10.4f} x {exec_qty:>8.2f}")
                    
                    print("="*100)
                
                # Get wallet balance history from transactions
                print(f"\n🔍 Analyzing wallet balance history...")
                tx_response = session.get_transaction_log(
                    accountType="UNIFIED", 
                    category="linear",
                    startTime=start_time,
                    endTime=end_time,
                    limit=200
                )
                
                if tx_response['retCode'] == 0:
                    tx_list = tx_response['result'].get('list', [])
                    
                    # Build complete balance timeline
                    balance_timeline = []
                    
                    for tx in tx_list:
                        tx_time = datetime.fromtimestamp(int(tx.get('transactionTime', 0)) / 1000)
                        if tx_time >= restart_time:
                            wallet_bal = float(tx.get('walletBalance', 0))
                            cash_bal = float(tx.get('cashBalance', 0))
                            
                            balance_timeline.append({
                                'time': tx_time,
                                'wallet': wallet_bal,
                                'cash': cash_bal,
                                'type': tx.get('type', 'unknown')
                            })
                    
                    # Sort by time
                    balance_timeline.sort(key=lambda x: x['time'])
                    
                    if balance_timeline:
                        print(f"\n{'='*60}")
                        print(f"📊 WALLET BALANCE OVER TIME")
                        print("="*60)
                        
                        peak_wallet = starting_balance
                        peak_time = None
                        
                        print(f"START | ${starting_balance:>10,.2f}")
                        
                        for point in balance_timeline[:30]:  # Show first 30
                            wallet = point['wallet'] if point['wallet'] > 0 else point['cash']
                            if wallet > peak_wallet:
                                peak_wallet = wallet
                                peak_time = point['time']
                                emoji = "🎯"
                            else:
                                emoji = "  "
                            
                            pnl = wallet - starting_balance
                            pnl_pct = (pnl / starting_balance * 100)
                            
                            print(f"{emoji} {point['time'].strftime('%m/%d %H:%M')} | "
                                  f"${wallet:>10,.2f} | "
                                  f"P&L: ${pnl:>+8.2f} ({pnl_pct:>+6.2f}%)")
                        
                        print(f"\n{'='*60}")
                        print(f"🎯 HIGHEST WALLET BALANCE")
                        print("="*60)
                        print(f"💰 Peak: ${peak_wallet:,.2f}")
                        if peak_time:
                            print(f"📅 Time: {peak_time.strftime('%B %d, %Y at %H:%M')}")
                        print(f"📈 Gain: ${peak_wallet - starting_balance:+,.2f} ({((peak_wallet - starting_balance) / starting_balance * 100):+.2f}%)")
                        print(f"💰 Current: ${current_equity:,.2f}")
                        print(f"📉 From Peak: ${current_equity - peak_wallet:+,.2f}")
                        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("\n" + "="*60)
    print("  TRUE PEAK FINDER (Including Unrealized P&L)")
    print("="*60)
    
    # Bot 2
    find_true_peak('src/config2.ini', 'BOT 2', 10000.00, "2026-02-05 01:38")
    
    print("\n" + "="*60)
    print("  ANALYSIS COMPLETE")
    print("="*60 + "\n")
