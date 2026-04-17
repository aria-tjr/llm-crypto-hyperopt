"""
Analyze WHEN the peak happened
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

def analyze_peak_timing(config_file, account_name, starting_balance):
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
    
    try:
        # Get transaction log
        end_time = int(datetime.now().timestamp() * 1000)
        start_time = int((datetime.now() - timedelta(days=7)).timestamp() * 1000)
        
        print(f"🔍 Fetching transaction history...")
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
            
            # Build equity timeline
            equity_timeline = []
            for tx in tx_list:
                if 'cashBalance' in tx and 'transactionTime' in tx:
                    timestamp = int(tx['transactionTime'])
                    dt = datetime.fromtimestamp(timestamp / 1000)
                    balance = float(tx['cashBalance'])
                    tx_type = tx.get('type', 'unknown')
                    
                    equity_timeline.append({
                        'time': dt,
                        'balance': balance,
                        'type': tx_type
                    })
            
            # Sort by time
            equity_timeline.sort(key=lambda x: x['time'])
            
            # Add starting point
            if equity_timeline:
                first_tx_time = equity_timeline[0]['time']
                equity_timeline.insert(0, {
                    'time': first_tx_time - timedelta(minutes=1),
                    'balance': starting_balance,
                    'type': 'START'
                })
            
            if equity_timeline:
                print(f"\n{'='*60}")
                print(f"📊 EQUITY TIMELINE (First 20 points)")
                print("="*60)
                
                for i, point in enumerate(equity_timeline[:20]):
                    equity_change = point['balance'] - starting_balance
                    equity_pct = (equity_change / starting_balance) * 100
                    
                    if i > 0:
                        prev_balance = equity_timeline[i-1]['balance']
                        change = point['balance'] - prev_balance
                        emoji = "📈" if change > 0 else "📉" if change < 0 else "➡️"
                    else:
                        emoji = "🟢"
                        change = 0
                    
                    print(f"{emoji} {point['time'].strftime('%m/%d %H:%M')} | "
                          f"${point['balance']:>10,.2f} | "
                          f"Change: ${change:>+8.2f} | "
                          f"Total: ${equity_change:>+8.2f} ({equity_pct:>+6.2f}%)")
                
                # Find peak
                peak = max(equity_timeline, key=lambda x: x['balance'])
                peak_idx = equity_timeline.index(peak)
                
                print(f"\n{'='*60}")
                print(f"🎯 PEAK EQUITY DETAILS")
                print("="*60)
                print(f"💰 Peak Balance: ${peak['balance']:,.2f}")
                print(f"📅 Peak Time: {peak['time'].strftime('%B %d, %Y at %H:%M:%S')}")
                print(f"📈 Gain at Peak: ${peak['balance'] - starting_balance:+,.2f} "
                      f"({((peak['balance'] - starting_balance) / starting_balance * 100):+.2f}%)")
                
                # Time from start to peak
                start_time_dt = equity_timeline[0]['time']
                time_to_peak = peak['time'] - start_time_dt
                hours = time_to_peak.total_seconds() / 3600
                print(f"⏱️  Time to Peak: {hours:.1f} hours from start")
                
                # Show transactions around peak
                print(f"\n📋 Transactions around peak time:")
                start_idx = max(0, peak_idx - 3)
                end_idx = min(len(equity_timeline), peak_idx + 4)
                
                for i in range(start_idx, end_idx):
                    point = equity_timeline[i]
                    marker = " 🎯 PEAK" if i == peak_idx else ""
                    print(f"  {point['time'].strftime('%m/%d %H:%M')} | ${point['balance']:,.2f}{marker}")
                
                # Current status
                current = equity_timeline[-1]
                drawdown = peak['balance'] - current['balance']
                drawdown_pct = (drawdown / peak['balance']) * 100
                time_since_peak = current['time'] - peak['time']
                hours_since = time_since_peak.total_seconds() / 3600
                
                print(f"\n{'='*60}")
                print(f"📊 CURRENT STATUS")
                print("="*60)
                print(f"💰 Current: ${current['balance']:,.2f}")
                print(f"📉 Drawdown: ${drawdown:,.2f} ({drawdown_pct:.2f}%)")
                print(f"⏱️  Hours since peak: {hours_since:.1f} hours")
                
        else:
            print(f"❌ Error: {tx_response['retMsg']}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("\n" + "="*60)
    print("  PEAK TIMING ANALYSIS")
    print(f"  Bot started: Feb 5, 2026 at 1:38 AM")
    print("="*60)
    
    # Bot 2 (the one with big peak)
    analyze_peak_timing('src/config2.ini', 'BOT 2', 10000.00)
    
    print("\n" + "="*60)
    print("  ANALYSIS COMPLETE")
    print("="*60 + "\n")
