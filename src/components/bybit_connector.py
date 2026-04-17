"""
Bybit Exchange Connector for Live Trading
Handles connection, order execution, and position management with Bybit Demo/Live account
"""

from pybit.unified_trading import HTTP
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BybitConnector:
    """
    Connects to Bybit exchange for live trading operations.
    Supports both demo and live accounts.
    """
    
    def __init__(self, api_key, api_secret, demo=True):
        """
        Initialize Bybit connection.
        
        Args:
            api_key: Bybit API key
            api_secret: Bybit API secret
            demo: True for demo account (demo.bybit.com), False for live
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.demo = demo
        
        # Initialize Bybit client
        if demo:
            # Demo account endpoint
            self.session = HTTP(
                testnet=False,
                api_key=api_key,
                api_secret=api_secret,
                demo=True
            )
            logger.info("🔗 Connected to Bybit DEMO account")
        else:
            # Live account endpoint
            self.session = HTTP(
                testnet=False,
                api_key=api_key,
                api_secret=api_secret
            )
            logger.info("🔗 Connected to Bybit LIVE account")
    
    def get_balance(self, coin="USDT"):
        """
        Get account balance for specific coin.
        
        Args:
            coin: Coin symbol (default: USDT)
            
        Returns:
            dict with balance information
        """
        try:
            response = self.session.get_wallet_balance(
                accountType="UNIFIED",
                coin=coin
            )
            
            if response['retCode'] == 0:
                balance_data = response['result']['list'][0]['coin'][0]
                # Handle empty strings from API
                equity = balance_data.get('equity', '0')
                available = balance_data.get('availableToBorrow', '0')  # For trading
                wallet = balance_data.get('walletBalance', '0')
                
                # Use equity as available balance (this is what we can trade with)
                return {
                    'coin': balance_data['coin'],
                    'equity': float(equity) if equity else 0.0,
                    'available_balance': float(equity) if equity else 0.0,  # Use equity for trading
                    'wallet_balance': float(wallet) if wallet else 0.0
                }
            else:
                logger.error(f"Error getting balance: {response['retMsg']}")
                return None
        except Exception as e:
            logger.error(f"Exception getting balance: {str(e)}")
            return None
    
    def get_position(self, symbol):
        """
        Get current position for a symbol.
        
        Args:
            symbol: Trading pair (e.g., 'BTCUSDT')
            
        Returns:
            dict with position information or None if no position
        """
        try:
            response = self.session.get_positions(
                category="linear",
                symbol=symbol
            )
            
            if response['retCode'] == 0 and len(response['result']['list']) > 0:
                pos = response['result']['list'][0]
                position_size = float(pos['size'])
                
                if position_size > 0:
                    return {
                        'symbol': pos['symbol'],
                        'side': pos['side'],
                        'size': position_size,
                        'entry_price': float(pos['avgPrice']),
                        'leverage': float(pos['leverage']),
                        'unrealised_pnl': float(pos['unrealisedPnl']),
                        'liq_price': float(pos['liqPrice']) if pos['liqPrice'] else 0
                    }
            return None
        except Exception as e:
            logger.error(f"Exception getting position: {str(e)}")
            return None
    
    def get_all_positions(self):
        """
        Get all open positions.
        
        Returns:
            list of position dicts
        """
        try:
            response = self.session.get_positions(
                category="linear",
                settleCoin="USDT"
            )
            
            positions = []
            if response['retCode'] == 0:
                for pos in response['result']['list']:
                    position_size = float(pos['size'])
                    if position_size > 0:
                        positions.append({
                            'symbol': pos['symbol'],
                            'side': pos['side'],
                            'size': position_size,
                            'entry_price': float(pos['avgPrice']),
                            'leverage': float(pos['leverage']),
                            'unrealised_pnl': float(pos['unrealisedPnl']),
                            'liq_price': float(pos['liqPrice']) if pos['liqPrice'] else 0
                        })
            return positions
        except Exception as e:
            logger.error(f"Exception getting all positions: {str(e)}")
            return []
    
    def update_position_leverage(self, symbol, leverage):
        """
        Update leverage for an existing position.
        
        Args:
            symbol: Trading pair (e.g., 'BTCUSDT')
            leverage: New leverage value
            
        Returns:
            bool indicating success
        """
        try:
            # Try to set requested leverage
            try:
                self.session.set_leverage(
                    category="linear",
                    symbol=symbol,
                    buyLeverage=str(leverage),
                    sellLeverage=str(leverage)
                )
                logger.info(f"✅ Updated {symbol} leverage to {leverage}x")
                return True
            except Exception as lev_error:
                error_msg = str(lev_error)
                if "leverage" in error_msg.lower():
                    # Try to get max leverage and use a safe value (min of requested or max/2)
                    try:
                        info = self.session.get_instruments_info(
                            category="linear",
                            symbol=symbol
                        )
                        if info['retCode'] == 0 and info['result']['list']:
                            max_leverage = float(info['result']['list'][0].get('leverageFilter', {}).get('maxLeverage', '1'))
                            # Use the requested leverage or max leverage divided by 2, whichever is smaller
                            actual_leverage = min(int(leverage), max(5, int(max_leverage / 2)))
                            logger.warning(f"⚠️  {symbol} doesn't support {leverage}x, using {actual_leverage}x (max: {int(max_leverage)}x)")
                            
                            self.session.set_leverage(
                                category="linear",
                                symbol=symbol,
                                buyLeverage=str(actual_leverage),
                                sellLeverage=str(actual_leverage)
                            )
                            return True
                    except Exception as fallback_error:
                        logger.error(f"❌ Failed to update leverage for {symbol}: {str(fallback_error)}")
                        return False
                else:
                    logger.error(f"❌ Failed to update leverage: {error_msg}")
                    return False
        except Exception as e:
            logger.error(f"Exception updating leverage: {str(e)}")
            return False
    
    def get_ticker(self, symbol):
        """
        Get current market price for a symbol.
        
        Args:
            symbol: Trading pair (e.g., 'BTCUSDT')
            
        Returns:
            dict with price information
        """
        try:
            response = self.session.get_tickers(
                category="linear",
                symbol=symbol
            )
            
            if response['retCode'] == 0:
                ticker = response['result']['list'][0]
                return {
                    'symbol': ticker['symbol'],
                    'last_price': float(ticker['lastPrice']),
                    'bid': float(ticker['bid1Price']),
                    'ask': float(ticker['ask1Price']),
                    'volume_24h': float(ticker['volume24h'])
                }
            return None
        except Exception as e:
            logger.error(f"Exception getting ticker: {str(e)}")
            return None
    
    def place_market_order(self, symbol, side, quantity, leverage=1):
        """
        Place a market order.
        
        Args:
            symbol: Trading pair (e.g., 'BTCUSDT')
            side: 'Buy' or 'Sell'
            quantity: Order quantity
            leverage: Leverage multiplier (default: 1)
            
        Returns:
            dict with order information or None if failed
        """
        try:
            # Try to set requested leverage first
            actual_leverage = leverage
            try:
                self.session.set_leverage(
                    category="linear",
                    symbol=symbol,
                    buyLeverage=str(leverage),
                    sellLeverage=str(leverage)
                )
                logger.debug(f"✅ Set {leverage}x leverage for {symbol}")
            except Exception as lev_error:
                # If leverage fails, try to get instrument info to find max leverage
                error_msg = str(lev_error)
                if "leverage" in error_msg.lower():
                    try:
                        # Get instrument info to find max leverage
                        info = self.session.get_instruments_info(
                            category="linear",
                            symbol=symbol
                        )
                        if info['retCode'] == 0 and info['result']['list']:
                            max_leverage = float(info['result']['list'][0].get('leverageFilter', {}).get('maxLeverage', '1'))
                            # Use the requested leverage or max leverage divided by 2, whichever is smaller
                            actual_leverage = min(int(leverage), max(5, int(max_leverage / 2)))
                            logger.warning(f"⚠️  {symbol} doesn't support {leverage}x, using {actual_leverage}x (max: {int(max_leverage)}x)")
                            
                            # Try setting safe leverage
                            self.session.set_leverage(
                                category="linear",
                                symbol=symbol,
                                buyLeverage=str(actual_leverage),
                                sellLeverage=str(actual_leverage)
                            )
                        else:
                            logger.warning(f"⚠️  Could not get max leverage for {symbol}, continuing with default")
                    except Exception as fallback_error:
                        logger.debug(f"Leverage fallback failed: {str(fallback_error)}, continuing anyway")
                else:
                    # Leverage already set or not modifiable - continue anyway
                    logger.debug(f"Leverage setting skipped: {error_msg}")
            
            # Place market order
            response = self.session.place_order(
                category="linear",
                symbol=symbol,
                side=side,
                orderType="Market",
                qty=str(quantity),
                timeInForce="GTC"
            )
            
            if response['retCode'] == 0:
                logger.info(f"✅ {side} order placed: {quantity} {symbol} @ {actual_leverage}x leverage")
                return {
                    'order_id': response['result']['orderId'],
                    'symbol': symbol,
                    'side': side,
                    'quantity': quantity,
                    'leverage': actual_leverage
                }
            else:
                logger.error(f"❌ Order failed: {response['retMsg']}")
                return None
        except Exception as e:
            logger.error(f"Exception placing order: {str(e)}")
            return None
    
    def close_position(self, symbol):
        """
        Close entire position for a symbol.
        
        Args:
            symbol: Trading pair (e.g., 'BTCUSDT')
            
        Returns:
            bool indicating success
        """
        try:
            position = self.get_position(symbol)
            if not position:
                logger.info(f"No position to close for {symbol}")
                return True
            
            # Close position by placing opposite side order
            close_side = "Sell" if position['side'] == "Buy" else "Buy"
            
            response = self.session.place_order(
                category="linear",
                symbol=symbol,
                side=close_side,
                orderType="Market",
                qty=str(position['size']),
                reduceOnly=True,
                timeInForce="GTC"
            )
            
            if response['retCode'] == 0:
                logger.info(f"✅ Position closed: {symbol}")
                return True
            else:
                logger.error(f"❌ Failed to close position: {response['retMsg']}")
                return False
        except Exception as e:
            logger.error(f"Exception closing position: {str(e)}")
            return False
    
    def set_stop_loss(self, symbol, stop_loss_price):
        """
        Set stop loss for existing position.
        
        Args:
            symbol: Trading pair (e.g., 'BTCUSDT')
            stop_loss_price: Stop loss trigger price
            
        Returns:
            bool indicating success
        """
        try:
            position = self.get_position(symbol)
            if not position:
                logger.warning(f"No position found for {symbol}, cannot set stop loss")
                return False
            
            response = self.session.set_trading_stop(
                category="linear",
                symbol=symbol,
                stopLoss=str(stop_loss_price),
                positionIdx=0
            )
            
            if response['retCode'] == 0:
                logger.info(f"✅ Stop loss set at ${stop_loss_price:.2f} for {symbol}")
                return True
            else:
                logger.error(f"❌ Failed to set stop loss: {response['retMsg']}")
                return False
        except Exception as e:
            logger.error(f"Exception setting stop loss: {str(e)}")
            return False
    
    def set_take_profit(self, symbol, take_profit_price):
        """
        Set take profit for existing position.
        
        Args:
            symbol: Trading pair (e.g., 'BTCUSDT')
            take_profit_price: Take profit trigger price
            
        Returns:
            bool indicating success
        """
        try:
            position = self.get_position(symbol)
            if not position:
                logger.warning(f"No position found for {symbol}, cannot set take profit")
                return False
            
            response = self.session.set_trading_stop(
                category="linear",
                symbol=symbol,
                takeProfit=str(take_profit_price),
                positionIdx=0
            )
            
            if response['retCode'] == 0:
                logger.info(f"✅ Take profit set at ${take_profit_price:.2f} for {symbol}")
                return True
            else:
                logger.error(f"❌ Failed to set take profit: {response['retMsg']}")
                return False
        except Exception as e:
            logger.error(f"Exception setting take profit: {str(e)}")
            return False
    
    def get_account_info(self):
        """
        Get comprehensive account information.
        
        Returns:
            dict with account details
        """
        try:
            balance = self.get_balance("USDT")
            if not balance:
                return None
            
            return {
                'account_type': 'DEMO' if self.demo else 'LIVE',
                'balance': balance,
                'timestamp': time.time()
            }
        except Exception as e:
            logger.error(f"Exception getting account info: {str(e)}")
            return None
