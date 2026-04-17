"""
Check highest P&L using Bybit API
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import configparser
from pybit.unified_trading import HTTP
from datetime import datetime, timedelta

def load_config(config_file):
    """Load configuration from ini file"""
    config = configparser.ConfigParser()
    config.read(config_file)
    return config

def check_highest_pnl(config_file, account_name, starting_balance):
    """Check highest P&L from position history"""
    print(f"\n{'='*60}")
    print(f"  {account_name}")
    print(f"{'='*60}")
    
    config = load_config(config_file)
    api_key = config.get('bybit', 'api_key')
    api_secret = config.get('bybit', 'api_secret')
    is_demo = config.getboolean('bybit', 'demo', fallback=True)
    
    session = HTTP(
        testnet=False,
        api_key=api_key,
        api_secret=api_secret,
        demo=True
    )
    
    try:
        # Get current wallet balance
        wallet_response = session.get_wallet_balance(accountType="UNIFIED", coin="USDT")
        if wallet_response['retCode'] == 0:
            usdt_balance = None
            for coin in wallet_response['result']['list'][0]['coin']:
                if coin['coin'] == 'USDT':
                    usdt_balance = coin
                    break
            
            if usdt_balance:
                current_equity = float(usdt_balance['equity'])
                wallet_balance = float(usdt_balance['walletBalance'])
                unrealized_pnl = float(usdt_balance['unrealisedPnl'])
                
                print(f"💰 Starting Balance: ${starting_balance:,.2f}")
                print(f"💰 Current Equity: ${current_equity:,.2f}")
                print(f"📊 Current Unrealized PnL: ${unrealized_pnl:,.2f}")
                
                # Get closed P&L records
                print(f"\n🔍 Checking P&L history...")
                try:
                    end_time = int(datetime.now().timestamp() * 1000)
                    start_time = int((datetime.now() - timedelta(days=7)).timestamp() * 1000)
                    
                    pnl_response = session.get_closed_pnl(
                        category="linear",
                        startTime=start_time,
                        endTime=end_time,
                        limit=100
                    )
                    
                    if pnl_response['retCode'] == 0:
                        pnl_list = pnl_response['result'].get('list', [])
                        print(f"✅ Found {len(pnl_list)} closed P&L records")
                        
                        if pnl_list:
                            total_realized_pnl = 0
                            highest_trade_pnl = 0
                            lowest_trade_pnl = 0
                            
                            for record in pnl_list:
                                pnl = float(record.get('closedPnl', 0))
                                total_realized_pnl += pnl
                                highest_trade_pnl = max(highest_trade_pnl, pnl)
                                lowest_trade_pnl = min(lowest_trade_pnl, pnl)
                            
                            print(f"\n📈 Total Realized P&L: ${total_realized_pnl:,.2f}")
                            print(f"🎯 Highest Single Trade: ${highest_trade_pnl:,.2f}")
                            print(f"📉 Lowest Single Trade: ${lowest_trade_pnl:,.2f}")
                        else:
                            print("⚠️  No closed trades found yet")
                    else:
                        print(f"⚠️  Could not fetch P&L: {pnl_response['retMsg']}")
                
                except Exception as e:
                    print(f"⚠️  P&L history error: {e}")
                
                # Get transaction log for balance changes
                print(f"\n🔍 Checking transaction history for equity peaks...")
                try:
                    tx_response = session.get_transaction_log(
                        accountType="UNIFIED",
                        category="linear",
                        startTime=start_time,
                        endTime=end_time,
                        limit=200
                    )
                    
                    if tx_response['retCode'] == 0:
                        tx_list = tx_response['result'].get('list', [])
                        print(f"✅ Found {len(tx_list)} transactions")
                        
                        # Track balance over time
                        equity_points = [starting_balance]
                        
                        for tx in tx_list:
                            if 'cashBalance' in tx:
                                balance = float(tx['cashBalance'])
                                equity_points.append(balance)
                        
                        # Add current equity
                        equity_points.append(current_equity)
                        
                        if len(equity_points) > 1:
                            highest_equity = max(equity_points)
                            lowest_equity = min(equity_points)
                            
                            print(f"\n{'='*60}")
                            print(f"🎯 HIGHEST EQUITY: ${highest_equity:,.2f}")
                            print(f"📉 LOWEST EQUITY: ${lowest_equity:,.2f}")
                            print(f"📊 Current Equity: ${current_equity:,.2f}")
                            
                            highest_pnl = highest_equity - starting_balance
                            current_pnl = current_equity - starting_balance
                            
                            print(f"\n💰 HIGHEST P&L: ${highest_pnl:+,.2f} ({(highest_pnl/starting_balance*100):+.2f}%)")
                            print(f"💰 Current P&L: ${current_pnl:+,.2f} ({(current_pnl/starting_balance*100):+.2f}%)")
                            
                            if current_equity >= highest_equity:
                                print(f"🚀 Currently AT peak equity!")
                            else:
                                drawdown = highest_equity - current_equity
                                print(f"📊 Drawdown from peak: ${drawdown:,.2f} ({(drawdown/highest_equity*100):.2f}%)")
                        else:
                            print("⚠️  Insufficient transaction data")
                    else:
                        print(f"⚠️  Could not fetch transactions: {tx_response['retMsg']}")
                
                except Exception as e:
                    print(f"⚠️  Transaction history error: {e}")
                    
        else:
            print(f"❌ API Error: {wallet_response['retMsg']}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("\n" + "="*60)
    print("  HIGHEST P&L ANALYZER")
    print("="*60)
    
    # Bot 1
    check_highest_pnl('src/config.ini', 'BOT 1 (snbEe...)', 6000.00)
    
    # Bot 2
    check_highest_pnl('src/config2.ini', 'BOT 2 (pzYRP...)', 10000.00)
    
    print("\n" + "="*60)
    print("  ANALYSIS COMPLETE")
    print("="*60 + "\n")
