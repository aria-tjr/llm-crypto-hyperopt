"""
Simple Bybit Connection Test
Tests basic connectivity and market data access
"""

from pybit.unified_trading import HTTP

# Set credentials via environment variables; do NOT commit real keys.
import os
api_key = os.getenv("BYBIT_API_KEY", "")
api_secret = os.getenv("BYBIT_API_SECRET", "")
if not api_key or not api_secret:
    raise SystemExit("Set BYBIT_API_KEY and BYBIT_API_SECRET environment variables before running this test.")

print("=" * 70)
print("BYBIT SIMPLE CONNECTION TEST")
print("=" * 70)
print()

# Test 1: Connect to demo account
print("1️⃣  Testing connection to Bybit DEMO account...")
try:
    session = HTTP(
        testnet=False,
        api_key=api_key,
        api_secret=api_secret,
        demo=True
    )
    print("   ✅ Connection successful!")
except Exception as e:
    print(f"   ❌ Connection failed: {e}")
    exit(1)

print()

# Test 2: Get market data (doesn't require account balance)
print("2️⃣  Testing market data access...")
try:
    response = session.get_tickers(
        category="linear",
        symbol="BTCUSDT"
    )
    
    if response['retCode'] == 0:
        ticker = response['result']['list'][0]
        price = float(ticker['lastPrice'])
        volume = float(ticker['volume24h'])
        print(f"   ✅ Market data access working!")
        print(f"   📊 BTC Price: ${price:,.2f}")
        print(f"   📊 24h Volume: {volume:,.2f} BTC")
    else:
        print(f"   ❌ Error: {response['retMsg']}")
except Exception as e:
    print(f"   ❌ Failed: {e}")

print()

# Test 3: Get wallet balance
print("3️⃣  Testing account balance...")
try:
    response = session.get_wallet_balance(
        accountType="UNIFIED",
        coin="USDT"
    )
    
    print(f"   Response code: {response['retCode']}")
    print(f"   Response message: {response['retMsg']}")
    
    if response['retCode'] == 0:
        if len(response['result']['list']) > 0:
            coins = response['result']['list'][0]['coin']
            if len(coins) > 0:
                balance = coins[0]
                equity = balance.get('equity', '0')
                available = balance.get('availableToWithdraw', '0')
                
                print(f"   ✅ Balance retrieved!")
                print(f"   💰 Equity: ${equity}")
                print(f"   💰 Available: ${available}")
                
                if equity == '0' or equity == '':
                    print()
                    print("   ⚠️  Your demo account has $0 balance!")
                    print("   📝 To add funds to demo account:")
                    print("      1. Go to https://www.bybit.com")
                    print("      2. Switch to Demo Trading mode")
                    print("      3. Look for 'Add Demo Funds' or similar option")
                    print("      4. Demo accounts usually start with 100,000 USDT")
            else:
                print("   ⚠️  No coin data found")
        else:
            print("   ⚠️  No account data found")
    else:
        print(f"   ❌ Error getting balance: {response['retMsg']}")
        
except Exception as e:
    print(f"   ⚠️  Exception: {e}")

print()

# Test 4: Check API permissions
print("4️⃣  Checking API permissions...")
try:
    response = session.get_api_key_information()
    
    if response['retCode'] == 0:
        print("   ✅ API key is valid!")
        permissions = response['result'].get('permissions', {})
        print(f"   Permissions: {permissions}")
    else:
        print(f"   ❌ Error: {response['retMsg']}")
except Exception as e:
    print(f"   ⚠️  Could not check permissions: {e}")

print()
print("=" * 70)
print("TEST COMPLETE")
print("=" * 70)
