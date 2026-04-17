"""
Check current Bybit balance and open positions to diagnose balance reduction
"""
import sys
sys.path.append('src')

from components.bybit_connector import BybitConnector
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def main():
    logger.info("=" * 80)
    logger.info("🔍 BALANCE & POSITION CHECKER")
    logger.info("=" * 80)
    
    # Initialize Bybit connector
    import configparser
    config = configparser.ConfigParser()
    config.read('src/config.ini')
    
    api_key = config.get('bybit', 'api_key')
    api_secret = config.get('bybit', 'api_secret')
    
    if not api_key or api_key == 'YOUR_BYBIT_API_KEY_HERE':
        logger.error("❌ API credentials not configured in config.ini")
        return
    
    bybit = BybitConnector(api_key, api_secret)
    
    # Get current balance
    logger.info("\n💰 ACCOUNT BALANCE:")
    logger.info("-" * 80)
    balance = bybit.get_balance("USDT")
    if balance and 'total_balance' in balance:
        logger.info(f"  Total Balance: ${balance['total_balance']:,.2f} USDT")
        logger.info(f"  Available: ${balance['available_balance']:,.2f} USDT")
        logger.info(f"  Used Margin: ${balance['total_balance'] - balance['available_balance']:,.2f} USDT")
        logger.info(f"  Account Status: {balance.get('status', 'Unknown')}")
    elif balance:
        # Handle different balance format
        logger.info(f"  Balance Info: {balance}")
    else:
        logger.error("  ❌ Could not fetch balance")
        return
    
    # Get all open positions
    logger.info("\n📊 OPEN POSITIONS:")
    logger.info("-" * 80)
    
    # List of all symbols from live_trading.py
    SYMBOLS = [
        "BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", "ADAUSDT", "AVAXUSDT", 
        "DOGEUSDT", "DOTUSDT", "MATICUSDT", "LINKUSDT", "TONUSDT", "UNIUSDT", "ATOMUSDT", 
        "FILUSDT", "ARBUSDT", "OPUSDT", "NEARUSDT", "APTUSDT", "SUIUSDT", "IMXUSDT", 
        "INJUSDT", "FTMUSDT", "STXUSDT", "AAVEUSDT", "TIAUSDT", "MKRUSDT", "RENDERUSDT", 
        "VETUSDT", "ALGOUSDT", "SEIUSDT", "THETAUSDT", "FLOWUSDT", "AXSUSDT", "SANDUSDT", 
        "MANAUSDT", "CRVUSDT", "GRTUSDT", "FLRUSDT", "KAVAUSDT", "1INCHUSDT", "SNXUSDT", 
        "GALAUSDT", "ENJUSDT", "CHZUSDT", "ZILUSDT", "ONEUSDT", "RVNUSDT", "QTUMUSDT", 
        "LRCUSDT", "SUSHIUSDT", "COMPUSDT", "YFIUSDT", "BATUSDT", "ZECUSDT", "DASHUSDT", 
        "DCRUSDT", "ZENUSDT", "WAVESUSDT", "ONTUSDT", "MANTAUSDT", "STRKUSDT", "BLURUSDT", 
        "DYDXUSDT", "PENDLEUSDT", "JTOUSDT", "WLDUSDT", "PYTHUSDT", "JITOUSDT", "JUPUSDT", 
        "BONKUSDT", "PEPEUSDT", "SHIBUSDT", "FLOKIUSDT", "WIFUSDT", "MEMEUSDT", "BRETTUSDT", 
        "POPCATUSDT", "DOGSUSDT", "NEIROUSDT", "LDOUSDT", "RPLUSDT", "FXSUSDT", "SPELLUSDT", 
        "MAGICUSDT", "GMXUSDT", "GNSUSDT", "RDNTUSDT", "STGUSDT", "PERPUSDT", "CVXUSDT", 
        "BALUSDT", "BNTUSDT", "KNCUSDT", "ZRXUSDT", "RENUSDT", "OCEANUSDT", "FETUSDT", 
        "AGIXUSDT", "ROSEUSDT"
    ]
    
    open_positions = []
    total_pnl = 0.0
    total_position_value = 0.0
    
    for symbol in SYMBOLS:
        try:
            position = bybit.get_position(symbol)
            if position and float(position.get('size', 0)) > 0:
                open_positions.append(position)
                
                entry_price = position['entry_price']
                current_price = position.get('mark_price', entry_price)
                size = float(position['size'])
                side = position['side']
                
                # Calculate PnL
                if side == 'Buy':
                    pnl = (current_price - entry_price) * size
                else:
                    pnl = (entry_price - current_price) * size
                
                pnl_pct = (pnl / (entry_price * size)) * 100
                total_pnl += pnl
                
                position_value = entry_price * size
                total_position_value += position_value
                
                status = "🟢" if pnl > 0 else "🔴" if pnl < 0 else "⚪"
                logger.info(f"{status} {symbol:12} | {side:4} {size:10.2f} @ ${entry_price:10.4f} | "
                          f"Current: ${current_price:10.4f} | PnL: ${pnl:+10.2f} ({pnl_pct:+6.2f}%)")
                
        except Exception as e:
            # Skip symbols that error (not available, etc.)
            pass
    
    # Summary
    logger.info("\n📈 POSITION SUMMARY:")
    logger.info("-" * 80)
    logger.info(f"  Total Open Positions: {len(open_positions)}")
    logger.info(f"  Total Position Value: ${total_position_value:,.2f}")
    logger.info(f"  Total Unrealized PnL: ${total_pnl:+,.2f}")
    if total_position_value > 0:
        total_return_pct = (total_pnl / total_position_value) * 100
        logger.info(f"  Overall Return: {total_return_pct:+.2f}%")
    
    # Account equity
    if balance:
        wallet_balance = balance.get('wallet_balance', balance.get('total_balance', 0))
        equity = balance.get('equity', wallet_balance)
        available = balance.get('available_balance', wallet_balance)
        
        logger.info(f"\n💎 ACCOUNT EQUITY: ${equity:,.2f} USDT")
        logger.info(f"   Wallet Balance: ${wallet_balance:,.2f} USDT")
        logger.info(f"   Available: ${available:,.2f} USDT")
        logger.info(f"   Used in Positions: ${equity - available:,.2f} USDT")
        
        # Calculate overall performance
        initial_balance = 100000  # Demo account starts with 100k typically
        profit_loss = wallet_balance - initial_balance
        profit_loss_pct = (profit_loss / initial_balance) * 100
        
        logger.info(f"\n📊 OVERALL PERFORMANCE:")
        logger.info(f"  Starting Balance: ${initial_balance:,.2f}")
        logger.info(f"  Current Wallet: ${wallet_balance:,.2f}")
        logger.info(f"  Realized P&L: ${profit_loss:+,.2f} ({profit_loss_pct:+.2f}%)")
        logger.info(f"  Current Equity: ${equity:,.2f}")
        
        # Explain the difference
        if wallet_balance < initial_balance:
            loss_amount = initial_balance - wallet_balance
            logger.info(f"\n⚠️  BALANCE REDUCTION ANALYSIS:")
            logger.info(f"  Total Loss: ${loss_amount:,.2f}")
            logger.info(f"  Percentage: {profit_loss_pct:.2f}%")
            logger.info(f"\n  Likely causes:")
            logger.info(f"  - Stop losses hit on losing positions")
            logger.info(f"  - Closed trades at a loss")
            logger.info(f"  - Trading fees accumulation")
            logger.info(f"  - Unrealized losses realized when positions closed")
    
    logger.info("\n" + "=" * 80)

if __name__ == "__main__":
    main()
