#!/usr/bin/env python3
"""
Live Trading Bot - Instance 2
Uses config2.ini with different API credentials
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set config path before importing anything
os.environ['CONFIG_FILE'] = 'src/config2.ini'

# Now run the bot
if __name__ == "__main__":
    print("=" * 80)
    print("🚀 STARTING BOT INSTANCE 2 (Account 2 - pzYRPP...)")
    print("=" * 80)
    print()
    
    # Execute the main bot file
    with open('src/live_trading.py') as f:
        exec(f.read())
