#!/usr/bin/env python3
"""
Quick check of account balance and positions
"""
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.components.bybit_connector import BybitConnector

def main():
    print("=" * 80)
    print("📊 BYBIT DEMO ACCOUNT STATUS")
    print("=" * 80)
    print()
    
    # Initialize connector
    api_key = os.getenv('BYBIT_API_KEY')
    api_secret = os.getenv('BYBIT_API_SECRET')
    bybit = BybitConnector(api_key=api_key, api_secret=api_secret, demo=True)
    
    # Get balance
    print("💰 Account Balance:")
    balance = bybit.get_balance()
    if balance:
        print(f"  Equity:    ${balance['equity']:>12,.2f}")
        print(f"  Wallet:    ${balance['wallet_balance']:>12,.2f}")
        print(f"  Available: ${balance['available_balance']:>12,.2f}")
        print(f"  Used:      ${balance['wallet_balance'] - balance['available_balance']:>12,.2f}")
    else:
        print("  ❌ Failed to fetch balance")
    print()
    
    # Get positions
    print("📈 Open Positions:")
    positions = bybit.get_all_positions()
    
    if not positions:
        print("  ✓ No open positions (0 positions)")
    else:
        print(f"  Total Positions: {len(positions)}")
        print()
        total_pnl = 0
        
        for i, pos in enumerate(positions, 1):
            side_emoji = "🟢" if pos['side'] == "Buy" else "🔴"
            pnl = pos['unrealised_pnl']
            total_pnl += pnl
            pnl_pct = (pnl / (pos['entry_price'] * pos['size'])) * 100 if pos['entry_price'] > 0 else 0
            
            print(f"  {i}. {side_emoji} {pos['symbol']}")
            print(f"     Size: {pos['size']:.4f} | Leverage: {pos['leverage']:.0f}x")
            print(f"     Entry: ${pos['entry_price']:.4f}")
            print(f"     PnL: ${pnl:>+10,.2f} ({pnl_pct:>+6.2f}%)")
            print()
        
        print(f"  Total Unrealized PnL: ${total_pnl:>+12,.2f}")
    
    print("=" * 80)

if __name__ == '__main__':
    main()
