"""
Script to check liquidation history from Bybit
"""
import sys
import configparser
from src.components.bybit_connector import BybitConnector
import logging
from datetime import datetime

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
    demo=True
)

def main():
    """Get liquidation history"""
    logger.info("=" * 60)
    logger.info("⚡ LIQUIDATION HISTORY CHECK")
    logger.info("=" * 60)
    
    # Get current balance first
    balance = bybit.get_balance("USDT")
    
    if balance:
        logger.info(f"\n💰 CURRENT BALANCE:")
        logger.info(f"  Wallet Balance: ${balance.get('wallet_balance', 0):,.2f}")
        logger.info(f"  Equity: ${balance.get('equity', 0):,.2f}")
    
    logger.info(f"\n🔍 CHECKING FOR LIQUIDATIONS...\n")
    
    try:
        # Method 1: Check execution history for liquidations
        response = bybit.session.get_executions(
            category="linear",
            limit=200
        )
        
        if response['retCode'] == 0:
            executions = response['result']['list']
            logger.info(f"Found {len(executions)} execution records")
            
            liquidations = []
            for exec in executions:
                exec_type = exec.get('execType', '')
                if 'Liquidation' in exec_type or exec.get('isMaker') == False and exec.get('orderType') == 'Market':
                    liquidations.append(exec)
            
            if liquidations:
                logger.info(f"\n⚡ FOUND {len(liquidations)} POTENTIAL LIQUIDATIONS:\n")
                logger.info("=" * 100)
                logger.info(f"{'Time':<20} {'Symbol':<12} {'Side':<6} {'Qty':<12} {'Price':<12} {'Value':<15} {'Type':<20}")
                logger.info("=" * 100)
                
                total_liquidation_value = 0
                
                for liq in liquidations:
                    timestamp = int(liq.get('execTime', 0))
                    date = datetime.fromtimestamp(timestamp/1000).strftime('%Y-%m-%d %H:%M:%S')
                    symbol = liq.get('symbol', '')
                    side = liq.get('side', '')
                    qty = float(liq.get('execQty', 0))
                    price = float(liq.get('execPrice', 0))
                    value = qty * price
                    exec_type = liq.get('execType', '')
                    
                    total_liquidation_value += value
                    
                    logger.info(f"{date:<20} {symbol:<12} {side:<6} {qty:<12.4f} ${price:<11.4f} ${value:<14.2f} {exec_type:<20}")
                
                logger.info("=" * 100)
                logger.info(f"\n💥 TOTAL LIQUIDATION VALUE: ${total_liquidation_value:,.2f}")
            else:
                logger.info("✅ No obvious liquidations found in execution history")
        
        # Method 2: Get wallet transaction log to find liquidations
        logger.info(f"\n📜 CHECKING TRANSACTION LOG...\n")
        
        response = bybit.session.get_transaction_log(
            category="linear",
            limit=200
        )
        
        if response['retCode'] == 0:
            transactions = response['result']['list']
            logger.info(f"Found {len(transactions)} transactions")
            
            logger.info("\n" + "=" * 120)
            logger.info(f"{'Time':<20} {'Type':<30} {'Symbol':<12} {'Qty':<12} {'Amount':<15} {'Balance':<15}")
            logger.info("=" * 120)
            
            total_fees = 0
            total_funding = 0
            total_realized_pnl = 0
            liquidation_losses = 0
            
            for tx in transactions:
                timestamp = int(tx.get('transactionTime', 0))
                date = datetime.fromtimestamp(timestamp/1000).strftime('%Y-%m-%d %H:%M:%S')
                tx_type = tx.get('type', '')
                symbol = tx.get('symbol', '')
                qty = tx.get('qty', '')
                amount = float(tx.get('cashFlow', 0))
                balance = float(tx.get('walletBalance', 0))
                
                # Track different transaction types
                if 'TRADING_FEE' in tx_type:
                    total_fees += abs(amount)
                elif 'FUNDING_FEE' in tx_type:
                    total_funding += amount
                elif 'REALIZED_PNL' in tx_type:
                    total_realized_pnl += amount
                elif 'LIQUIDATION' in tx_type:
                    liquidation_losses += amount
                    logger.info(f"{date:<20} {tx_type:<30} {symbol:<12} {qty:<12} ${amount:>+14.2f} ${balance:>14.2f} ⚡")
                elif amount < -100:  # Large losses
                    logger.info(f"{date:<20} {tx_type:<30} {symbol:<12} {qty:<12} ${amount:>+14.2f} ${balance:>14.2f} ❗")
                elif abs(amount) > 10:  # Significant transactions
                    logger.info(f"{date:<20} {tx_type:<30} {symbol:<12} {qty:<12} ${amount:>+14.2f} ${balance:>14.2f}")
            
            logger.info("=" * 120)
            logger.info(f"\n💸 TRANSACTION SUMMARY:")
            logger.info(f"  Trading Fees Paid: ${total_fees:,.2f}")
            logger.info(f"  Funding Fees: ${total_funding:+,.2f}")
            logger.info(f"  Realized P&L: ${total_realized_pnl:+,.2f}")
            if liquidation_losses != 0:
                logger.info(f"  Liquidation Losses: ${liquidation_losses:+,.2f} ⚡")
            
            # Calculate the mystery
            logger.info(f"\n🔍 MYSTERY ANALYSIS:")
            logger.info(f"  Starting Balance: $100,000.00")
            logger.info(f"  Current Wallet: ${balance.get('wallet_balance', 0) if balance else 0:,.2f}")
            logger.info(f"  Total Loss: ${(balance.get('wallet_balance', 0) if balance else 0) - 100000:+,.2f}")
            logger.info(f"\n  Accounted for:")
            logger.info(f"    - Closed P&L: $-2,214.78")
            logger.info(f"    - Trading Fees: $-{total_fees:.2f}")
            logger.info(f"    - Funding Fees: ${total_funding:+.2f}")
            logger.info(f"    - Liquidations: ${liquidation_losses:+.2f}")
            logger.info(f"  ----------------------------------------")
            accounted = -2214.78 - total_fees + total_funding + liquidation_losses
            logger.info(f"  Total Accounted: ${accounted:+,.2f}")
            
            actual_loss = (balance.get('wallet_balance', 0) if balance else 0) - 100000
            unaccounted = actual_loss - accounted
            logger.info(f"  Still Unaccounted: ${unaccounted:+,.2f} ❓")
            
        else:
            logger.error(f"Failed to get transaction log: {response.get('retMsg', 'Unknown error')}")
            
    except Exception as e:
        logger.error(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
