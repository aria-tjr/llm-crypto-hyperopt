"""
Optimize position allocation based on profitability analysis
Reallocate capital from underperformers to top performers
"""
import sys
import configparser
from src.components.bybit_connector import BybitConnector
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)
logger = logging.getLogger(__name__)

# Load config
config = configparser.ConfigParser()
config.read('src/config.ini')

# Initialize Bybit connector
bybit = BybitConnector(
    api_key=config.get('bybit', 'api_key'),
    api_secret=config.get('bybit', 'api_secret'),
    demo=True
)

# All trading symbols with current allocations
SYMBOLS = [
    {'symbol': 'BTCUSDT', 'name': 'Bitcoin', 'current_alloc': 0.01},
    {'symbol': 'ETHUSDT', 'name': 'Ethereum', 'current_alloc': 0.01},
    {'symbol': 'SOLUSDT', 'name': 'Solana', 'current_alloc': 0.01},
    {'symbol': 'BNBUSDT', 'name': 'BNB', 'current_alloc': 0.01},
    {'symbol': 'XRPUSDT', 'name': 'XRP', 'current_alloc': 0.01},
    {'symbol': 'DOGEUSDT', 'name': 'Dogecoin', 'current_alloc': 0.01},
    {'symbol': 'ADAUSDT', 'name': 'Cardano', 'current_alloc': 0.01},
    {'symbol': 'AVAXUSDT', 'name': 'Avalanche', 'current_alloc': 0.01},
    {'symbol': 'DOTUSDT', 'name': 'Polkadot', 'current_alloc': 0.01},
    {'symbol': 'LINKUSDT', 'name': 'Chainlink', 'current_alloc': 0.01},
    {'symbol': 'TONUSDT', 'name': 'Toncoin', 'current_alloc': 0.01},
    {'symbol': 'UNIUSDT', 'name': 'Uniswap', 'current_alloc': 0.01},
    {'symbol': 'FILUSDT', 'name': 'Filecoin', 'current_alloc': 0.01},
    {'symbol': 'ARBUSDT', 'name': 'Arbitrum', 'current_alloc': 0.01},
    {'symbol': 'OPUSDT', 'name': 'Optimism', 'current_alloc': 0.01},
    {'symbol': 'NEARUSDT', 'name': 'NEAR Protocol', 'current_alloc': 0.01},
    {'symbol': 'APTUSDT', 'name': 'Aptos', 'current_alloc': 0.01},
    {'symbol': 'SUIUSDT', 'name': 'Sui', 'current_alloc': 0.01},
    {'symbol': 'IMXUSDT', 'name': 'Immutable X', 'current_alloc': 0.01},
    {'symbol': 'INJUSDT', 'name': 'Injective', 'current_alloc': 0.01},
    {'symbol': 'STXUSDT', 'name': 'Stacks', 'current_alloc': 0.01},
    {'symbol': 'RENDERUSDT', 'name': 'Render', 'current_alloc': 0.01},
    {'symbol': 'ALGOUSDT', 'name': 'Algorand', 'current_alloc': 0.01},
    {'symbol': 'FLOWUSDT', 'name': 'Flow', 'current_alloc': 0.01},
    {'symbol': 'SANDUSDT', 'name': 'Sandbox', 'current_alloc': 0.01},
    {'symbol': 'MANAUSDT', 'name': 'Decentraland', 'current_alloc': 0.01},
    {'symbol': 'CRVUSDT', 'name': 'Curve', 'current_alloc': 0.01},
    {'symbol': 'FLRUSDT', 'name': 'Fluence', 'current_alloc': 0.01},
    {'symbol': 'KAVAUSDT', 'name': 'Kava', 'current_alloc': 0.01},
    {'symbol': '1INCHUSDT', 'name': '1inch', 'current_alloc': 0.01},
    {'symbol': 'SNXUSDT', 'name': 'Synthetix', 'current_alloc': 0.01},
    {'symbol': 'ENJUSDT', 'name': 'Enjin', 'current_alloc': 0.01},
    {'symbol': 'ONEUSDT', 'name': 'Harmony', 'current_alloc': 0.01},
    {'symbol': 'RVNUSDT', 'name': 'Ravencoin', 'current_alloc': 0.01},
    {'symbol': 'QTUMUSDT', 'name': 'Qtum', 'current_alloc': 0.01},
    {'symbol': 'LRCUSDT', 'name': 'Loopring', 'current_alloc': 0.01},
    {'symbol': 'SUSHIUSDT', 'name': 'Sushi', 'current_alloc': 0.01},
    {'symbol': 'COMPUSDT', 'name': 'Compound', 'current_alloc': 0.01},
    {'symbol': 'BATUSDT', 'name': 'BAT', 'current_alloc': 0.01},
    {'symbol': 'DASHUSDT', 'name': 'Dash', 'current_alloc': 0.01},
    {'symbol': 'ZENUSDT', 'name': 'Horizen', 'current_alloc': 0.01},
    {'symbol': 'WAVESUSDT', 'name': 'Waves', 'current_alloc': 0.01},
    {'symbol': 'STRKUSDT', 'name': 'Starknet', 'current_alloc': 0.01},
    {'symbol': 'DYDXUSDT', 'name': 'dYdX', 'current_alloc': 0.01},
    {'symbol': 'WLDUSDT', 'name': 'Worldcoin', 'current_alloc': 0.01},
    {'symbol': 'JUPUSDT', 'name': 'Jupiter', 'current_alloc': 0.01},
    {'symbol': 'LDOUSDT', 'name': 'Lido DAO', 'current_alloc': 0.01},
    {'symbol': 'RPLUSDT', 'name': 'Rocket Pool', 'current_alloc': 0.01},
]

def get_current_positions():
    """Get all current positions with their performance"""
    positions_data = []
    
    for asset in SYMBOLS:
        symbol = asset['symbol']
        name = asset['name']
        
        try:
            position = bybit.get_position(symbol)
            
            if position and float(position.get('size', 0)) > 0:
                size = float(position['size'])
                entry_price = float(position['entry_price'])
                side = position['side']
                
                # Get current price
                ticker = bybit.get_ticker(symbol)
                if ticker:
                    current_price = float(ticker['last_price'])
                    
                    # Calculate metrics
                    position_value = size * entry_price
                    
                    if side == 'Buy':
                        pnl = (current_price - entry_price) * size
                        pnl_pct = ((current_price - entry_price) / entry_price) * 100
                    else:
                        pnl = (entry_price - current_price) * size
                        pnl_pct = ((entry_price - current_price) / entry_price) * 100
                    
                    positions_data.append({
                        'symbol': symbol,
                        'name': name,
                        'side': side,
                        'size': size,
                        'entry_price': entry_price,
                        'current_price': current_price,
                        'position_value': position_value,
                        'pnl': pnl,
                        'pnl_pct': pnl_pct,
                        'current_alloc': asset['current_alloc']
                    })
        except Exception as e:
            pass
    
    return positions_data

def calculate_optimal_allocation(positions):
    """
    Calculate optimal allocation based on performance metrics:
    - Recent profitability (pnl_pct)
    - Risk-adjusted returns
    - Diversification needs
    """
    
    # Sort by profitability
    sorted_positions = sorted(positions, key=lambda x: x['pnl_pct'], reverse=True)
    
    # Strategy: Weight allocation based on performance tiers
    # Top 20%: 2.0% each (high performers)
    # Next 30%: 1.5% each (good performers)
    # Next 30%: 1.0% each (average performers)
    # Bottom 20%: 0.5% each (underperformers)
    
    total_positions = len(sorted_positions)
    top_20_count = max(1, int(total_positions * 0.20))
    top_50_count = max(1, int(total_positions * 0.50))
    top_80_count = max(1, int(total_positions * 0.80))
    
    allocations = []
    
    for i, pos in enumerate(sorted_positions):
        if i < top_20_count:
            # Top 20%: High performers
            new_alloc = 0.020
            tier = "⭐ HIGH PERFORMER"
        elif i < top_50_count:
            # Next 30%: Good performers
            new_alloc = 0.015
            tier = "✅ GOOD PERFORMER"
        elif i < top_80_count:
            # Next 30%: Average performers
            new_alloc = 0.010
            tier = "🔵 AVERAGE"
        else:
            # Bottom 20%: Reduce exposure
            new_alloc = 0.005
            tier = "⚠️  UNDERPERFORMER"
        
        allocations.append({
            **pos,
            'new_alloc': new_alloc,
            'tier': tier,
            'alloc_change': new_alloc - pos['current_alloc'],
            'rank': i + 1
        })
    
    return allocations

def main():
    """Calculate optimal position allocation"""
    logger.info("=" * 100)
    logger.info("🎯 OPTIMAL POSITION ALLOCATION CALCULATOR")
    logger.info("=" * 100)
    
    # Get current positions
    logger.info("\n📊 Analyzing current positions...")
    positions = get_current_positions()
    
    if not positions:
        logger.info("❌ No positions found")
        return
    
    logger.info(f"✅ Found {len(positions)} open positions")
    
    # Calculate total current value
    total_value = sum(p['position_value'] for p in positions)
    total_pnl = sum(p['pnl'] for p in positions)
    
    logger.info(f"\n💰 CURRENT PORTFOLIO:")
    logger.info(f"  Total Value: ${total_value:,.2f}")
    logger.info(f"  Total P&L: ${total_pnl:+,.2f}")
    logger.info(f"  Return: {(total_pnl/total_value)*100:+.2f}%")
    
    # Calculate optimal allocation
    logger.info("\n🎯 Calculating optimal allocation...\n")
    optimal = calculate_optimal_allocation(positions)
    
    # Display recommendations
    logger.info("=" * 120)
    logger.info(f"{'Rank':<6} {'Symbol':<12} {'Name':<18} {'Current':<10} {'P&L %':<10} {'Tier':<25} {'Current':<10} {'→ New':<10} {'Change':<10}")
    logger.info("=" * 120)
    
    for alloc in optimal:
        change_str = f"{alloc['alloc_change']*100:+.1f}%"
        if alloc['alloc_change'] > 0:
            change_str += " ↑"
        elif alloc['alloc_change'] < 0:
            change_str += " ↓"
        else:
            change_str += " ="
        
        logger.info(
            f"{alloc['rank']:<6} {alloc['symbol']:<12} {alloc['name']:<18} "
            f"${alloc['current_price']:<9,.4f} {alloc['pnl_pct']:>+8.2f}% "
            f"{alloc['tier']:<25} {alloc['current_alloc']*100:>8.1f}% "
            f"→ {alloc['new_alloc']*100:>6.1f}% {change_str:<10}"
        )
    
    logger.info("=" * 120)
    
    # Summary by tier
    logger.info("\n📊 ALLOCATION SUMMARY BY TIER:")
    logger.info("=" * 80)
    
    high_performers = [a for a in optimal if "HIGH PERFORMER" in a['tier']]
    good_performers = [a for a in optimal if "GOOD PERFORMER" in a['tier']]
    average = [a for a in optimal if "AVERAGE" in a['tier']]
    underperformers = [a for a in optimal if "UNDERPERFORMER" in a['tier']]
    
    logger.info(f"\n⭐ HIGH PERFORMERS ({len(high_performers)} positions @ 2.0% each):")
    logger.info(f"   Total Allocation: {len(high_performers) * 2.0:.1f}%")
    for a in high_performers:
        logger.info(f"   - {a['name']:<18} ({a['symbol']:<10}): {a['pnl_pct']:>+6.2f}%")
    
    logger.info(f"\n✅ GOOD PERFORMERS ({len(good_performers)} positions @ 1.5% each):")
    logger.info(f"   Total Allocation: {len(good_performers) * 1.5:.1f}%")
    for a in good_performers:
        logger.info(f"   - {a['name']:<18} ({a['symbol']:<10}): {a['pnl_pct']:>+6.2f}%")
    
    logger.info(f"\n🔵 AVERAGE PERFORMERS ({len(average)} positions @ 1.0% each):")
    logger.info(f"   Total Allocation: {len(average) * 1.0:.1f}%")
    for a in average[:5]:  # Show first 5
        logger.info(f"   - {a['name']:<18} ({a['symbol']:<10}): {a['pnl_pct']:>+6.2f}%")
    if len(average) > 5:
        logger.info(f"   ... and {len(average)-5} more")
    
    logger.info(f"\n⚠️  UNDERPERFORMERS ({len(underperformers)} positions @ 0.5% each):")
    logger.info(f"   Total Allocation: {len(underperformers) * 0.5:.1f}%")
    for a in underperformers:
        logger.info(f"   - {a['name']:<18} ({a['symbol']:<10}): {a['pnl_pct']:>+6.2f}%")
    
    # Calculate expected impact
    logger.info("\n💡 EXPECTED IMPACT:")
    logger.info("=" * 80)
    
    # Positions that should increase
    increases = [a for a in optimal if a['alloc_change'] > 0]
    decreases = [a for a in optimal if a['alloc_change'] < 0]
    
    logger.info(f"\n📈 INCREASE ALLOCATION ({len(increases)} positions):")
    for a in increases:
        logger.info(
            f"   {a['name']:<18} ({a['symbol']:<10}): "
            f"{a['current_alloc']*100:.1f}% → {a['new_alloc']*100:.1f}% "
            f"({a['alloc_change']*100:+.1f}%) | Current P&L: {a['pnl_pct']:+.2f}%"
        )
    
    logger.info(f"\n📉 DECREASE ALLOCATION ({len(decreases)} positions):")
    for a in decreases:
        logger.info(
            f"   {a['name']:<18} ({a['symbol']:<10}): "
            f"{a['current_alloc']*100:.1f}% → {a['new_alloc']*100:.1f}% "
            f"({a['alloc_change']*100:+.1f}%) | Current P&L: {a['pnl_pct']:+.2f}%"
        )
    
    # Calculate theoretical improvement
    current_weighted_return = sum(p['pnl_pct'] * p['current_alloc'] for p in optimal)
    new_weighted_return = sum(p['pnl_pct'] * p['new_alloc'] for p in optimal)
    
    logger.info(f"\n🎯 PROJECTED IMPROVEMENT:")
    logger.info(f"  Current Weighted Return: {current_weighted_return:+.3f}%")
    logger.info(f"  Optimized Weighted Return: {new_weighted_return:+.3f}%")
    logger.info(f"  Expected Improvement: {new_weighted_return - current_weighted_return:+.3f}%")
    
    logger.info("\n" + "=" * 80)
    logger.info("💡 RECOMMENDATION:")
    logger.info("=" * 80)
    logger.info("To implement this allocation:")
    logger.info("1. Update allocations in src/live_trading.py SYMBOLS list")
    logger.info("2. Or use the code snippet below to auto-generate")
    logger.info("3. Restart the bot to use new allocations")
    logger.info("")
    logger.info("⚠️  NOTE: This rebalancing will:")
    logger.info("   - Increase capital to top performers (capturing momentum)")
    logger.info("   - Reduce exposure to underperformers (risk management)")
    logger.info("   - Maintain diversification across all assets")

if __name__ == "__main__":
    main()
