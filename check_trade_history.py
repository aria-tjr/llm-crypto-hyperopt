"""
Script to check closed trades and realized P&L
"""
import sys
import configparser
from src.components.bybit_connector import BybitConnector
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Load config
config = configparser.ConfigParser()
config.read('src/config.ini')

# Initialize Bybit connector
bybit = BybitConnector(
    api_key=config.get('bybit', 'api_key'),
    api_secret=config.get('bybit', 'api_secret'),
    demo=True  # Demo account
)

def main():
    """Get closed trade history and calculate realized P&L"""
    logger.info("=" * 60)
    logger.info("📜 CLOSED TRADES HISTORY")
    logger.info("=" * 60)
    
    # Get current balance first
    balance = bybit.get_balance("USDT")
    
    if balance:
        logger.info(f"\n💰 CURRENT BALANCE:")
        logger.info(f"  Wallet Balance: ${balance.get('wallet_balance', 0):,.2f}")
        logger.info(f"  Equity: ${balance.get('equity', 0):,.2f}")
        logger.info(f"  Available: ${balance.get('available_balance', 0):,.2f}")
    
    # Try to get closed P&L
    logger.info(f"\n📊 FETCHING CLOSED TRADE HISTORY...")
    
    try:
        # Get closed P&L - this shows realized profits/losses
        response = bybit.session.get_closed_pnl(
            category="linear",
            limit=200  # Get last 200 closed trades
        )
        
        if response['retCode'] == 0:
            trades = response['result']['list']
            logger.info(f"  Found {len(trades)} closed trades\n")
            
            total_pnl = 0
            winning_trades = 0
            losing_trades = 0
            
            logger.info("=" * 100)
            logger.info(f"{'Symbol':<12} {'Side':<6} {'Qty':<12} {'Entry':<12} {'Exit':<12} {'P&L':<15} {'Date':<20}")
            logger.info("=" * 100)
            
            for trade in trades:
                symbol = trade.get('symbol', '')
                side = trade.get('side', '')
                qty = float(trade.get('qty', 0))
                avg_entry = float(trade.get('avgEntryPrice', 0))
                avg_exit = float(trade.get('avgExitPrice', 0))
                closed_pnl = float(trade.get('closedPnl', 0))
                created_time = trade.get('createdTime', '')
                
                # Convert timestamp to readable date
                from datetime import datetime
                date = datetime.fromtimestamp(int(created_time)/1000).strftime('%Y-%m-%d %H:%M:%S')
                
                total_pnl += closed_pnl
                
                if closed_pnl > 0:
                    winning_trades += 1
                    pnl_str = f"${closed_pnl:+,.2f} ✅"
                else:
                    losing_trades += 1
                    pnl_str = f"${closed_pnl:+,.2f} ❌"
                
                logger.info(f"{symbol:<12} {side:<6} {qty:<12.4f} ${avg_entry:<11.4f} ${avg_exit:<11.4f} {pnl_str:<15} {date}")
            
            logger.info("=" * 100)
            logger.info(f"\n📈 TRADING STATISTICS:")
            logger.info(f"  Total Closed Trades: {len(trades)}")
            logger.info(f"  Winning Trades: {winning_trades} ({winning_trades/len(trades)*100:.1f}%)")
            logger.info(f"  Losing Trades: {losing_trades} ({losing_trades/len(trades)*100:.1f}%)")
            logger.info(f"  Total Realized P&L: ${total_pnl:+,.2f}")
            
            if len(trades) > 0:
                avg_pnl = total_pnl / len(trades)
                logger.info(f"  Average P&L per Trade: ${avg_pnl:+,.2f}")
            
            # Calculate expected balance
            initial_balance = 100000
            expected_balance = initial_balance + total_pnl
            actual_wallet = balance.get('wallet_balance', 0) if balance else 0
            
            logger.info(f"\n💎 BALANCE RECONCILIATION:")
            logger.info(f"  Starting Balance: ${initial_balance:,.2f}")
            logger.info(f"  + Realized P&L: ${total_pnl:+,.2f}")
            logger.info(f"  = Expected Wallet: ${expected_balance:,.2f}")
            logger.info(f"  Actual Wallet: ${actual_wallet:,.2f}")
            logger.info(f"  Difference: ${actual_wallet - expected_balance:+,.2f}")
            
            if abs(actual_wallet - expected_balance) > 100:
                logger.info(f"\n⚠️  NOTE: Difference may be due to:")
                logger.info(f"  - Trading fees not included in closed P&L")
                logger.info(f"  - Funding fees (positive or negative)")
                logger.info(f"  - Initial balance different from $100k")
            
        else:
            logger.error(f"❌ Error getting closed P&L: {response.get('retMsg', 'Unknown error')}")
            
    except Exception as e:
        logger.error(f"❌ Error: {str(e)}")
        logger.info("\nTrying alternative method to get transaction history...")
        
        try:
            # Alternative: Get transaction log
            response = bybit.session.get_transaction_log(
                category="linear",
                limit=200
            )
            
            if response['retCode'] == 0:
                transactions = response['result']['list']
                logger.info(f"  Found {len(transactions)} transactions")
                
                total_fees = 0
                total_funding = 0
                
                for tx in transactions:
                    tx_type = tx.get('type', '')
                    amount = float(tx.get('cashFlow', 0))
                    
                    if 'TRADING_FEE' in tx_type:
                        total_fees += abs(amount)
                    elif 'FUNDING_FEE' in tx_type:
                        total_funding += amount
                
                logger.info(f"\n💸 FEES & FUNDING:")
                logger.info(f"  Total Trading Fees: ${total_fees:,.2f}")
                logger.info(f"  Total Funding Fees: ${total_funding:+,.2f}")
                
        except Exception as e2:
            logger.error(f"❌ Alternative method also failed: {str(e2)}")

if __name__ == "__main__":
    main()
