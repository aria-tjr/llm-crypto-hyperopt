"""
Test Bybit Connection
Quick script to verify your Bybit API credentials are working
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import configparser
from components.bybit_connector import BybitConnector


def load_config():
    """Load configuration from config.ini"""
    config = configparser.ConfigParser()
    config_path = os.path.join(os.path.dirname(__file__), 'config.ini')
    config.read(config_path)
    return config


def main():
    print("=" * 70)
    print("BYBIT CONNECTION TEST")
    print("=" * 70)
    print()
    
    # Load config
    config = load_config()
    api_key = config.get('bybit', 'api_key')
    api_secret = config.get('bybit', 'api_secret')
    demo = config.getboolean('bybit', 'demo', fallback=True)
    
    # Check if configured
    if api_key == 'YOUR_BYBIT_API_KEY_HERE':
        print("❌ API credentials not configured!")
        print()
        print("Please follow the setup guide in BYBIT_SETUP.md")
        print()
        print("Quick steps:")
        print("1. Go to https://www.bybit.com/user/account")
        print("2. Create Demo Trading API key")
        print("3. Edit src/config.ini with your credentials")
        return
    
    print(f"Account Type: {'DEMO' if demo else 'LIVE'}")
    print(f"API Key: {api_key[:8]}...{api_key[-4:]}")
    print()
    
    # Test connection
    print("Testing connection...")
    try:
        bybit = BybitConnector(
            api_key=api_key,
            api_secret=api_secret,
            demo=demo
        )
        print("✅ Connection established!")
        print()
        
        # Get account info
        print("Fetching account information...")
        account = bybit.get_account_info()
        
        if account:
            print("✅ Account info retrieved successfully!")
            print()
            print(f"💰 Balance Information:")
            print(f"  Equity:              ${account['balance']['equity']:>12,.2f}")
            print(f"  Available Balance:   ${account['balance']['available_balance']:>12,.2f}")
            print(f"  Wallet Balance:      ${account['balance']['wallet_balance']:>12,.2f}")
            print()
            
            # Test getting ticker
            print("Testing market data access...")
            ticker = bybit.get_ticker("BTCUSDT")
            
            if ticker:
                print("✅ Market data access working!")
                print()
                print(f"📊 Bitcoin Price:")
                print(f"  Last Price:          ${ticker['last_price']:>12,.2f}")
                print(f"  Bid:                 ${ticker['bid']:>12,.2f}")
                print(f"  Ask:                 ${ticker['ask']:>12,.2f}")
                print(f"  24h Volume:          {ticker['volume_24h']:>12,.2f} BTC")
                print()
                
                # Test getting position
                print("Checking for open positions...")
                position = bybit.get_position("BTCUSDT")
                
                if position:
                    print("📈 Bitcoin Position Found:")
                    print(f"  Side:                {position['side']}")
                    print(f"  Size:                {position['size']}")
                    print(f"  Entry Price:         ${position['entry_price']:,.2f}")
                    print(f"  Leverage:            {position['leverage']}x")
                    print(f"  Unrealized PnL:      ${position['unrealised_pnl']:+,.2f}")
                else:
                    print("✅ No open positions (ready to trade)")
                print()
                
                print("=" * 70)
                print("✅ ALL TESTS PASSED!")
                print("=" * 70)
                print()
                print("Your bot is ready to trade! Run:")
                print("  python src/live_trading.py")
                
            else:
                print("❌ Failed to get market data")
        else:
            print("❌ Failed to get account info")
            print()
            print("Possible issues:")
            print("- API key/secret incorrect")
            print("- API permissions not set correctly")
            print("- Using wrong account type (live vs demo)")
    
    except Exception as e:
        print(f"❌ Connection failed: {str(e)}")
        print()
        print("Please check:")
        print("- API key and secret are correct")
        print("- API has 'Read/Write' and 'Unified Trading' permissions")
        print("- You're using Demo account API key if demo=true")


if __name__ == "__main__":
    main()
