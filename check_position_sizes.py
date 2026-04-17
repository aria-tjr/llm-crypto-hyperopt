"""Check current position sizes after leverage update"""
import sys
import os
sys.path.append(os.path.dirname(__file__))

from src.components.bybit_connector import BybitConnector
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

API_KEY = os.getenv('BYBIT_API_KEY')
API_SECRET = os.getenv('BYBIT_API_SECRET')

# Connect to Bybit
bybit = BybitConnector(API_KEY, API_SECRET, demo=True)

# Get all positions
positions = bybit.get_all_positions()

if positions:
    print(f"Found {len(positions)} open positions:\n")
    print(f"{'Symbol':<15} {'Side':<6} {'Size':<15} {'Leverage':<10} {'Entry Price':<12} {'PnL':<10}")
    print("=" * 80)
    
    for pos in positions:
        symbol = pos['symbol']
        side = pos['side']
        size = pos['size']
        leverage = pos['leverage']
        entry = pos['entry_price']
        pnl = pos['unrealised_pnl']
        
        print(f"{symbol:<15} {side:<6} {size:<15.4f} {leverage:<10.0f}x ${entry:<11.4f} ${pnl:>9.2f}")
    
    print("\n" + "=" * 80)
    print(f"Total Positions: {len(positions)}")
else:
    print("No open positions found")
