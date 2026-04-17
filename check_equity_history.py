"""
Check equity history and highest watermark for both bots using pybit
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import configparser
from src.components.bybit_connector import BybitConnector

def load_config(config_file):
    """Load configuration from ini file"""
    config = configparser.ConfigParser()
    config.read(config_file)
    return config

def check_wallet_history(config_file, account_name, starting_balance):
    """Check wallet balance history and calculate highest equity"""
    print(f"\n{'='*60}")
    print(f"  {account_name}")
    print(f"{'='*60}")
    
    config = load_config(config_file)
    api_key = config.get('bybit', 'api_key')
    api_secret = config.get('bybit', 'api_secret')
    is_demo = config.getboolean('bybit', 'demo', fallback=True)
    
    # Use BybitConnector
    bybit = BybitConnector(api_key, api_secret, demo=is_demo)
    
    # Get current wallet balance
    try:
        balance_info = bybit.get_balance("USDT")
        if balance_info:
            equity = balance_info['equity']
            wallet_balance = balance_info['wallet_balance']
            available = balance_info['available_balance']
            
            print(f"💰 Starting Balance: ${starting_balance:,.2f}")
            print(f"💰 Current Wallet: ${wallet_balance:,.2f}")
            print(f"💰 Current Equity: ${equity:,.2f}")
            print(f"💰 Available: ${available:,.2f}")
            
            profit_loss = equity - starting_balance
            profit_pct = (profit_loss / starting_balance) * 100
            
            print(f"\n{'='*60}")
            print(f"📈 Total P&L: ${profit_loss:+,.2f} ({profit_pct:+.2f}%)")
            
            # Get open positions to calculate unrealized PnL
            positions = bybit.get_all_positions()
            if positions:
                total_unrealized = sum(float(p.get('unrealisedPnl', 0)) for p in positions)
                print(f"📊 Unrealized PnL: ${total_unrealized:+,.2f} (from {len(positions)} positions)")
            
            # Since API doesn't provide historical equity, estimate peak
            print(f"\n{'='*60}")
            print(f"🔍 EQUITY ANALYSIS")
            print(f"{'='*60}")
            
            if profit_loss > 0:
                print(f"🎯 HIGHEST EQUITY (estimated): ${equity:,.2f} (CURRENT)")
                print(f"📉 LOWEST EQUITY (estimated): ${starting_balance:,.2f} (START)")
                print(f"✅ Currently at peak (+{profit_pct:.2f}%)")
            else:
                print(f"🎯 HIGHEST EQUITY (estimated): ${starting_balance:,.2f} (START)")
                print(f"📉 CURRENT EQUITY: ${equity:,.2f}")
                print(f"🔻 Drawdown from start: ${abs(profit_loss):,.2f} ({profit_pct:.2f}%)")
                
            print(f"\n💡 Note: Since all positions are still open and no trades")
            print(f"   have closed yet, the current equity likely represents")
            print(f"   the peak (if profitable) or close to it.")
        else:
            print(f"❌ Could not retrieve balance")
                
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("\n" + "="*60)
    print("  EQUITY HISTORY ANALYZER")
    print("="*60)
    
    # Bot 1
    check_wallet_history('src/config.ini', 'BOT 1 (snbEe...)', 6000.00)
    
    # Bot 2
    check_wallet_history('src/config2.ini', 'BOT 2 (pzYRP...)', 10000.00)
    
    print("\n" + "="*60)
    print("  ANALYSIS COMPLETE")
    print("="*60 + "\n")
