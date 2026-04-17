"""
Analyze why equity dropped from peak without hitting TP
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

def analyze_drawdown(config_file, account_name, starting_balance, peak_equity):
    """Analyze trades that caused drawdown from peak"""
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
                drawdown = peak_equity - current_equity
                
                print(f"🎯 Peak Equity: ${peak_equity:,.2f}")
                print(f"📊 Current Equity: ${current_equity:,.2f}")
                print(f"📉 Drawdown: ${drawdown:,.2f} ({(drawdown/peak_equity*100):.2f}%)")
                
                # Get recent closed trades
                print(f"\n🔍 Analyzing recent closed trades...")
                end_time = int(datetime.now().timestamp() * 1000)
                start_time = int((datetime.now() - timedelta(days=7)).timestamp() * 1000)
                
                pnl_response = session.get_closed_pnl(
                    category="linear",
                    startTime=start_time,
                    endTime=end_time,
                    limit=200
                )
                
                if pnl_response['retCode'] == 0:
                    pnl_list = pnl_response['result'].get('list', [])
                    
                    # Sort by updated time (most recent first)
                    pnl_list_sorted = sorted(pnl_list, key=lambda x: int(x.get('updatedTime', 0)), reverse=True)
                    
                    print(f"\n📋 RECENT TRADES (Last 30):")
                    print("="*100)
                    
                    big_losses = []
                    big_wins = []
                    total_pnl = 0
                    
                    for i, record in enumerate(pnl_list_sorted[:30]):
                        symbol = record.get('symbol', 'N/A')
                        side = record.get('side', 'N/A')
                        qty = float(record.get('closedSize', 0))
                        entry_price = float(record.get('avgEntryPrice', 0))
                        exit_price = float(record.get('avgExitPrice', 0))
                        pnl = float(record.get('closedPnl', 0))
                        pnl_pct = (pnl / (qty * entry_price) * 100) if (qty * entry_price) > 0 else 0
                        updated_time = datetime.fromtimestamp(int(record.get('updatedTime', 0)) / 1000)
                        
                        total_pnl += pnl
                        
                        # Track significant losses and wins
                        if pnl < -50:
                            big_losses.append({
                                'symbol': symbol,
                                'pnl': pnl,
                                'pnl_pct': pnl_pct,
                                'time': updated_time,
                                'side': side,
                                'entry': entry_price,
                                'exit': exit_price
                            })
                        elif pnl > 50:
                            big_wins.append({
                                'symbol': symbol,
                                'pnl': pnl,
                                'pnl_pct': pnl_pct,
                                'time': updated_time,
                                'side': side,
                                'entry': entry_price,
                                'exit': exit_price
                            })
                        
                        emoji = "🔴" if pnl < 0 else "🟢"
                        print(f"{i+1:2}. {emoji} {symbol:12} {side:4} | Entry: ${entry_price:>10.4f} → Exit: ${exit_price:>10.4f} | "
                              f"P&L: ${pnl:>8.2f} ({pnl_pct:>6.2f}%) | {updated_time.strftime('%m/%d %H:%M')}")
                    
                    print("="*100)
                    print(f"📊 Total P&L (last 30 trades): ${total_pnl:+,.2f}")
                    
                    # Analyze big losses
                    if big_losses:
                        print(f"\n{'='*60}")
                        print(f"🔴 BIG LOSSES (>${50} each):")
                        print("="*60)
                        big_losses_sorted = sorted(big_losses, key=lambda x: x['pnl'])
                        total_big_losses = sum(l['pnl'] for l in big_losses_sorted)
                        
                        for loss in big_losses_sorted:
                            print(f"❌ {loss['symbol']:12} {loss['side']:4} | ${loss['pnl']:>8.2f} ({loss['pnl_pct']:>6.2f}%) | "
                                  f"${loss['entry']:.4f} → ${loss['exit']:.4f} | {loss['time'].strftime('%m/%d %H:%M')}")
                        
                        print(f"\n💥 Total Big Losses: ${total_big_losses:,.2f} ({len(big_losses)} trades)")
                    
                    # Analyze big wins
                    if big_wins:
                        print(f"\n{'='*60}")
                        print(f"🟢 BIG WINS (>${50} each):")
                        print("="*60)
                        big_wins_sorted = sorted(big_wins, key=lambda x: x['pnl'], reverse=True)
                        total_big_wins = sum(w['pnl'] for w in big_wins_sorted)
                        
                        for win in big_wins_sorted[:10]:  # Top 10
                            print(f"✅ {win['symbol']:12} {win['side']:4} | ${win['pnl']:>8.2f} ({win['pnl_pct']:>6.2f}%) | "
                                  f"${win['entry']:.4f} → ${win['exit']:.4f} | {win['time'].strftime('%m/%d %H:%M')}")
                        
                        print(f"\n💰 Total Big Wins: ${total_big_wins:,.2f} ({len(big_wins)} trades)")
                    
                    # Summary
                    print(f"\n{'='*60}")
                    print(f"📊 DRAWDOWN ANALYSIS SUMMARY")
                    print("="*60)
                    if big_losses:
                        print(f"⚠️  Primary cause: {len(big_losses)} large losing trades totaling ${sum(l['pnl'] for l in big_losses):,.2f}")
                    if big_wins:
                        print(f"✅ Offset by: {len(big_wins)} large winning trades totaling ${sum(w['pnl'] for w in big_wins):,.2f}")
                    
                    net_big_trades = sum(w['pnl'] for w in big_wins) + sum(l['pnl'] for l in big_losses)
                    print(f"📈 Net P&L from significant trades: ${net_big_trades:+,.2f}")
                    
                    # Check if stop losses hit
                    sl_count = sum(1 for record in pnl_list_sorted[:30] if abs(float(record.get('closedPnl', 0)) / (float(record.get('closedSize', 1)) * float(record.get('avgEntryPrice', 1)))) > 0.025)
                    print(f"\n🛑 Trades hitting ~3.45% stop loss: {sl_count}")
                    
                else:
                    print(f"❌ Could not fetch P&L: {pnl_response['retMsg']}")
                    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("\n" + "="*60)
    print("  DRAWDOWN ANALYSIS")
    print("="*60)
    
    # Analyze Bot 1
    analyze_drawdown('src/config.ini', 'BOT 1', 6000.00, 6265.97)
    
    # Analyze Bot 2 (the one with big drawdown)
    analyze_drawdown('src/config2.ini', 'BOT 2', 10000.00, 13301.81)
    
    print("\n" + "="*60)
    print("  ANALYSIS COMPLETE")
    print("="*60 + "\n")
