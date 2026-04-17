#!/usr/bin/env python3
"""
Direct Bybit API check - bypasses connector to test API
"""
import configparser
import os
from pybit.unified_trading import HTTP

# Load config
config = configparser.ConfigParser()
config.read('src/config.ini')

api_key = config.get('bybit', 'api_key')
api_secret = config.get('bybit', 'api_secret')

print("=" * 80)
print("📊 DIRECT BYBIT API STATUS CHECK")
print("=" * 80)
print()

# Initialize direct connection
session = HTTP(
    testnet=False,
    api_key=api_key,
    api_secret=api_secret,
    demo=True
)

print("✅ Connected to Bybit Demo\n")

# Get wallet balance
print("💰 Fetching wallet balance...")
try:
    response = session.get_wallet_balance(accountType="UNIFIED", coin="USDT")
    if response['retCode'] == 0:
        balance_list = response['result']['list']
        if balance_list:
            account = balance_list[0]
            equity = float(account['totalEquity'])
            wallet = float(account['totalWalletBalance'])
            available = float(account['totalAvailableBalance'])
            used = wallet - available
            
            print(f"  Equity:    ${equity:>12,.2f}")
            print(f"  Wallet:    ${wallet:>12,.2f}")
            print(f"  Available: ${available:>12,.2f}")
            print(f"  Used:      ${used:>12,.2f}")
        else:
            print("  ⚠️ No balance data")
    else:
        print(f"  ❌ Error: {response['retMsg']}")
except Exception as e:
    print(f"  ❌ Exception: {str(e)}")

print()

# Get positions
print("📈 Fetching open positions...")
try:
    response = session.get_positions(category="linear", settleCoin="USDT")
    if response['retCode'] == 0:
        positions = [p for p in response['result']['list'] if float(p['size']) > 0]
        
        if not positions:
            print("  ✓ No open positions (0 positions)")
        else:
            print(f"  Total Positions: {len(positions)}\n")
            total_pnl = 0
            
            for i, pos in enumerate(positions, 1):
                symbol = pos['symbol']
                side = pos['side']
                size = float(pos['size'])
                entry = float(pos['avgPrice'])
                leverage = float(pos['leverage'])
                pnl = float(pos['unrealisedPnl'])
                mark_price = float(pos['markPrice'])
                
                total_pnl += pnl
                pnl_pct = (pnl / (entry * size)) * 100 if entry > 0 else 0
                
                side_emoji = "🟢" if side == "Buy" else "🔴"
                
                print(f"  {i}. {side_emoji} {symbol}")
                print(f"     Size: {size:.4f} | Leverage: {leverage:.0f}x")
                print(f"     Entry: ${entry:.4f} | Mark: ${mark_price:.4f}")
                print(f"     PnL: ${pnl:>+10,.2f} ({pnl_pct:>+6.2f}%)")
                print()
            
            print(f"  💰 Total Unrealized PnL: ${total_pnl:>+12,.2f}")
    else:
        print(f"  ❌ Error: {response['retMsg']}")
except Exception as e:
    print(f"  ❌ Exception: {str(e)}")

print()
print("=" * 80)
