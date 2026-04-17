"""
Find most profitable pairs by analyzing position sizes and current prices
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

# All trading symbols
SYMBOLS = [
    {'symbol': 'BTCUSDT', 'name': 'Bitcoin'},
    {'symbol': 'ETHUSDT', 'name': 'Ethereum'},
    {'symbol': 'SOLUSDT', 'name': 'Solana'},
    {'symbol': 'BNBUSDT', 'name': 'BNB'},
    {'symbol': 'XRPUSDT', 'name': 'XRP'},
    {'symbol': 'DOGEUSDT', 'name': 'Dogecoin'},
    {'symbol': 'ADAUSDT', 'name': 'Cardano'},
    {'symbol': 'AVAXUSDT', 'name': 'Avalanche'},
    {'symbol': 'DOTUSDT', 'name': 'Polkadot'},
    {'symbol': 'LINKUSDT', 'name': 'Chainlink'},
    {'symbol': 'TONUSDT', 'name': 'Toncoin'},
    {'symbol': 'UNIUSDT', 'name': 'Uniswap'},
    {'symbol': 'FILUSDT', 'name': 'Filecoin'},
    {'symbol': 'ARBUSDT', 'name': 'Arbitrum'},
    {'symbol': 'OPUSDT', 'name': 'Optimism'},
    {'symbol': 'NEARUSDT', 'name': 'NEAR Protocol'},
    {'symbol': 'APTUSDT', 'name': 'Aptos'},
    {'symbol': 'SUIUSDT', 'name': 'Sui'},
    {'symbol': 'IMXUSDT', 'name': 'Immutable X'},
    {'symbol': 'INJUSDT', 'name': 'Injective'},
    {'symbol': 'STXUSDT', 'name': 'Stacks'},
    {'symbol': 'RENDERUSDT', 'name': 'Render'},
    {'symbol': 'ALGOUSDT', 'name': 'Algorand'},
    {'symbol': 'FLOWUSDT', 'name': 'Flow'},
    {'symbol': 'SANDUSDT', 'name': 'Sandbox'},
    {'symbol': 'MANAUSDT', 'name': 'Decentraland'},
    {'symbol': 'CRVUSDT', 'name': 'Curve'},
    {'symbol': 'FLRUSDT', 'name': 'Fluence'},
    {'symbol': 'KAVAUSDT', 'name': 'Kava'},
    {'symbol': '1INCHUSDT', 'name': '1inch'},
    {'symbol': 'SNXUSDT', 'name': 'Synthetix'},
    {'symbol': 'ENJUSDT', 'name': 'Enjin'},
    {'symbol': 'ONEUSDT', 'name': 'Harmony'},
    {'symbol': 'RVNUSDT', 'name': 'Ravencoin'},
    {'symbol': 'QTUMUSDT', 'name': 'Qtum'},
    {'symbol': 'LRCUSDT', 'name': 'Loopring'},
    {'symbol': 'SUSHIUSDT', 'name': 'Sushi'},
    {'symbol': 'COMPUSDT', 'name': 'Compound'},
    {'symbol': 'BATUSDT', 'name': 'BAT'},
    {'symbol': 'DASHUSDT', 'name': 'Dash'},
    {'symbol': 'ZENUSDT', 'name': 'Horizen'},
    {'symbol': 'WAVESUSDT', 'name': 'Waves'},
    {'symbol': 'STRKUSDT', 'name': 'Starknet'},
    {'symbol': 'DYDXUSDT', 'name': 'dYdX'},
    {'symbol': 'WLDUSDT', 'name': 'Worldcoin'},
    {'symbol': 'JUPUSDT', 'name': 'Jupiter'},
    {'symbol': 'LDOUSDT', 'name': 'Lido DAO'},
    {'symbol': 'RPLUSDT', 'name': 'Rocket Pool'},
]

def main():
    """Find most profitable pairs by position size"""
    logger.info("=" * 80)
    logger.info("💰 ANALYZING POSITIONS BY SIZE & PROFITABILITY")
    logger.info("=" * 80)
    
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
                
                # Get current price from ticker
                ticker = bybit.get_ticker(symbol)
                if ticker:
                    current_price = float(ticker['last_price'])
                    
                    # Calculate P&L
                    position_value = size * entry_price
                    current_value = size * current_price
                    
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
                        'current_value': current_value,
                        'pnl': pnl,
                        'pnl_pct': pnl_pct
                    })
        except Exception as e:
            # Skip symbols that don't exist or have errors
            pass
    
    if not positions_data:
        logger.info("No open positions found")
        return
    
    # Sort by position value (largest first)
    positions_data.sort(key=lambda x: x['position_value'], reverse=True)
    
    logger.info(f"\n📊 FOUND {len(positions_data)} OPEN POSITIONS")
    logger.info(f"\n{'='*100}")
    logger.info(f"{'Rank':<6} {'Symbol':<12} {'Name':<18} {'Side':<6} {'Entry $':<12} {'Current $':<12} {'Size':<12} {'Value $':<12} {'P&L $':<12} {'P&L %':<10}")
    logger.info(f"{'='*100}")
    
    total_position_value = 0
    total_pnl = 0
    
    for i, pos in enumerate(positions_data, 1):
        total_position_value += pos['position_value']
        total_pnl += pos['pnl']
        
        # Color coding
        if pos['pnl'] > 0:
            pnl_str = f"${pos['pnl']:>+10,.2f} ✅"
            pct_str = f"{pos['pnl_pct']:>+8.2f}% ✅"
        elif pos['pnl'] < 0:
            pnl_str = f"${pos['pnl']:>+10,.2f} ❌"
            pct_str = f"{pos['pnl_pct']:>+8.2f}% ❌"
        else:
            pnl_str = f"${pos['pnl']:>+10,.2f}"
            pct_str = f"{pos['pnl_pct']:>+8.2f}%"
        
        logger.info(
            f"{i:<6} {pos['symbol']:<12} {pos['name']:<18} {pos['side']:<6} "
            f"${pos['entry_price']:<11,.4f} ${pos['current_price']:<11,.4f} "
            f"{pos['size']:<12,.2f} ${pos['position_value']:<11,.2f} "
            f"{pnl_str:<12} {pct_str:<10}"
        )
    
    logger.info(f"{'='*100}")
    logger.info(f"\n💎 SUMMARY:")
    logger.info(f"  Total Position Value: ${total_position_value:,.2f}")
    logger.info(f"  Total P&L: ${total_pnl:+,.2f}")
    logger.info(f"  Overall Return: {(total_pnl/total_position_value)*100:+.2f}%")
    
    # Top 10 by position size
    logger.info(f"\n🏆 TOP 10 LARGEST POSITIONS:")
    logger.info(f"{'='*80}")
    for i, pos in enumerate(positions_data[:10], 1):
        logger.info(
            f"  {i}. {pos['name']:<18} ({pos['symbol']:<10}): "
            f"${pos['position_value']:>10,.2f} | "
            f"P&L: ${pos['pnl']:>+8,.2f} ({pos['pnl_pct']:>+6.2f}%)"
        )
    
    # Top 10 by profitability %
    positions_by_profit = sorted(positions_data, key=lambda x: x['pnl_pct'], reverse=True)
    logger.info(f"\n🚀 TOP 10 MOST PROFITABLE (by %):")
    logger.info(f"{'='*80}")
    for i, pos in enumerate(positions_by_profit[:10], 1):
        logger.info(
            f"  {i}. {pos['name']:<18} ({pos['symbol']:<10}): "
            f"{pos['pnl_pct']:>+6.2f}% | "
            f"P&L: ${pos['pnl']:>+8,.2f} | "
            f"Value: ${pos['position_value']:>10,.2f}"
        )
    
    # Top 10 by absolute profit $
    positions_by_dollar = sorted(positions_data, key=lambda x: x['pnl'], reverse=True)
    logger.info(f"\n💵 TOP 10 HIGHEST PROFIT (by $):")
    logger.info(f"{'='*80}")
    for i, pos in enumerate(positions_by_dollar[:10], 1):
        logger.info(
            f"  {i}. {pos['name']:<18} ({pos['symbol']:<10}): "
            f"${pos['pnl']:>+8,.2f} | "
            f"{pos['pnl_pct']:>+6.2f}% | "
            f"Value: ${pos['position_value']:>10,.2f}"
        )
    
    # Bottom 10 (if any losers)
    losers = [p for p in positions_data if p['pnl'] < 0]
    if losers:
        logger.info(f"\n📉 LOSING POSITIONS ({len(losers)} total):")
        logger.info(f"{'='*80}")
        losers_sorted = sorted(losers, key=lambda x: x['pnl'])
        for i, pos in enumerate(losers_sorted[:10], 1):
            logger.info(
                f"  {i}. {pos['name']:<18} ({pos['symbol']:<10}): "
                f"${pos['pnl']:>+8,.2f} ({pos['pnl_pct']:>+6.2f}%) | "
                f"Value: ${pos['position_value']:>10,.2f}"
            )
    else:
        logger.info(f"\n✅ ALL POSITIONS ARE PROFITABLE!")

if __name__ == "__main__":
    main()
