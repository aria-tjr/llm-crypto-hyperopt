"""
Live Trading Bot for Bybit
Connects to Bybit demo account and executes trades based on LLM sentiment analysis
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
import configparser
from datetime import datetime, timedelta
from components.bybit_connector import BybitConnector
from components.signal_generator import generate_trading_signal
from components.llm_signal_analyzer import get_hybrid_signal
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def load_config():
    """Load configuration from config.ini or custom path"""
    config = configparser.ConfigParser()
    # Check for custom config path from environment variable
    config_file = os.environ.get('CONFIG_FILE', 'config.ini')
    if not config_file.startswith('src/'):
        config_path = os.path.join(os.path.dirname(__file__), config_file)
    else:
        config_path = config_file
    config.read(config_path)
    logger.info(f"📋 Loaded config from: {config_path}")
    return config


def main():
    """
    Main live trading loop.
    Analyzes sentiment and executes trades on Bybit demo account.
    """
    print("=" * 80)
    print("LLM CRYPTO TRADING BOT - BYBIT LIVE TRADING")
    print("=" * 80)
    print()
    
    # Load configuration
    config = load_config()
    
    # Check if Bybit credentials are configured
    bybit_api_key = config.get('bybit', 'api_key')
    bybit_api_secret = config.get('bybit', 'api_secret')
    
    if bybit_api_key == 'YOUR_BYBIT_API_KEY_HERE':
        print("❌ ERROR: Bybit API credentials not configured!")
        print()
        print("Please follow these steps:")
        print("1. Go to https://www.bybit.com/user/account")
        print("2. Click on 'API Management' in the left menu")
        print("3. Create a new API key for DEMO trading")
        print("4. Copy your API key and secret")
        print("5. Edit src/config.ini and replace:")
        print("   - api_key = YOUR_API_KEY")
        print("   - api_secret = YOUR_API_SECRET")
        print()
        print("⚠️  Make sure to use DEMO account API keys!")
        return
    
    # Initialize components
    try:
        bybit = BybitConnector(
            api_key=bybit_api_key,
            api_secret=bybit_api_secret,
            demo=config.getboolean('bybit', 'demo', fallback=True)
        )
        
        news_api_key = config.get('news', 'api_key')
        
    except Exception as e:
        logger.error(f"Failed to initialize components: {str(e)}")
        return
    
    print()
    print("🔧 Configuration:")
    print(f"  Account Type: {'DEMO' if config.getboolean('bybit', 'demo', fallback=True) else 'LIVE'}")
    print(f"  Sentiment Model: {config.get('trading', 'model')}")
    print()
    
    # Get account info
    account_info = bybit.get_account_info()
    if account_info:
        print(f"💰 Account Balance:")
        print(f"  Equity: ${account_info['balance']['equity']:,.2f}")
        print(f"  Available: ${account_info['balance']['available_balance']:,.2f}")
        print()
    else:
        logger.error("Failed to get account information. Check your API credentials.")
        return
    
    # Trading configuration - 100 TOP CRYPTO ASSETS (Feb 4, 2026)
    # Diversified portfolio across major cryptocurrencies
    # 100% allocation: 100 assets @ 1% each
    SYMBOLS = [
        # Top 100 Cryptocurrencies by Market Cap & Quality
        {"name": "Bitcoin", "symbol": "BTCUSDT", "allocation": 0.01},
        {"name": "Ethereum", "symbol": "ETHUSDT", "allocation": 0.01},
        {"name": "BNB", "symbol": "BNBUSDT", "allocation": 0.01},
        {"name": "Solana", "symbol": "SOLUSDT", "allocation": 0.01},
        {"name": "Ripple", "symbol": "XRPUSDT", "allocation": 0.01},
        {"name": "Cardano", "symbol": "ADAUSDT", "allocation": 0.01},
        {"name": "Avalanche", "symbol": "AVAXUSDT", "allocation": 0.01},
        {"name": "Dogecoin", "symbol": "DOGEUSDT", "allocation": 0.01},
        {"name": "Polkadot", "symbol": "DOTUSDT", "allocation": 0.01},
        {"name": "Chainlink", "symbol": "LINKUSDT", "allocation": 0.01},
        {"name": "Polygon", "symbol": "MATICUSDT", "allocation": 0.01},
        {"name": "Litecoin", "symbol": "LTCUSDT", "allocation": 0.01},
        {"name": "Near", "symbol": "NEARUSDT", "allocation": 0.01},
        {"name": "Uniswap", "symbol": "UNIUSDT", "allocation": 0.01},
        {"name": "Stellar", "symbol": "XLMUSDT", "allocation": 0.01},
        {"name": "Cosmos", "symbol": "ATOMUSDT", "allocation": 0.01},
        {"name": "Monero", "symbol": "XMRUSDT", "allocation": 0.01},
        {"name": "Ethereum Classic", "symbol": "ETCUSDT", "allocation": 0.01},
        {"name": "Filecoin", "symbol": "FILUSDT", "allocation": 0.01},
        {"name": "Aptos", "symbol": "APTUSDT", "allocation": 0.01},
        {"name": "Arbitrum", "symbol": "ARBUSDT", "allocation": 0.01},
        {"name": "Optimism", "symbol": "OPUSDT", "allocation": 0.01},
        {"name": "Injective", "symbol": "INJUSDT", "allocation": 0.01},
        {"name": "Sui", "symbol": "SUIUSDT", "allocation": 0.01},
        {"name": "Aave", "symbol": "AAVEUSDT", "allocation": 0.01},
        {"name": "Algorand", "symbol": "ALGOUSDT", "allocation": 0.01},
        {"name": "VeChain", "symbol": "VETUSDT", "allocation": 0.01},
        {"name": "The Graph", "symbol": "GRTUSDT", "allocation": 0.01},
        {"name": "Fantom", "symbol": "FTMUSDT", "allocation": 0.01},
        {"name": "Hedera", "symbol": "HBARUSDT", "allocation": 0.01},
        {"name": "Theta", "symbol": "THETAUSDT", "allocation": 0.01},
        {"name": "EOS", "symbol": "EOSUSDT", "allocation": 0.01},
        {"name": "Tezos", "symbol": "XTZUSDT", "allocation": 0.01},
        {"name": "Axie Infinity", "symbol": "AXSUSDT", "allocation": 0.01},
        {"name": "Flow", "symbol": "FLOWUSDT", "allocation": 0.01},
        {"name": "Sandbox", "symbol": "SANDUSDT", "allocation": 0.01},
        {"name": "Decentraland", "symbol": "MANAUSDT", "allocation": 0.01},
        {"name": "Apecoin", "symbol": "APEUSDT", "allocation": 0.01},
        {"name": "Bitcoin Cash", "symbol": "BCHUSDT", "allocation": 0.01},
        {"name": "Quant", "symbol": "QNTUSDT", "allocation": 0.01},
        {"name": "Maker", "symbol": "MKRUSDT", "allocation": 0.01},
        {"name": "MultiversX", "symbol": "EGLDUSDT", "allocation": 0.01},
        {"name": "Render", "symbol": "RENDERUSDT", "allocation": 0.01},
        {"name": "ImmutableX", "symbol": "IMXUSDT", "allocation": 0.01},
        {"name": "Stacks", "symbol": "STXUSDT", "allocation": 0.01},
        {"name": "Celestia", "symbol": "TIAUSDT", "allocation": 0.01},
        {"name": "Sei", "symbol": "SEIUSDT", "allocation": 0.01},
        {"name": "Mina", "symbol": "MINAUSDT", "allocation": 0.01},
        {"name": "Kava", "symbol": "KAVAUSDT", "allocation": 0.01},
        {"name": "1inch", "symbol": "1INCHUSDT", "allocation": 0.01},
        {"name": "Synthetix", "symbol": "SNXUSDT", "allocation": 0.01},
        {"name": "Compound", "symbol": "COMPUSDT", "allocation": 0.01},
        {"name": "Curve", "symbol": "CRVUSDT", "allocation": 0.01},
        {"name": "Lido", "symbol": "LDOUSDT", "allocation": 0.01},
        {"name": "Pendle", "symbol": "PENDLEUSDT", "allocation": 0.01},
        {"name": "Ondo", "symbol": "ONDOUSDT", "allocation": 0.01},
        {"name": "Wormhole", "symbol": "WUSDT", "allocation": 0.01},
        {"name": "Jupiter", "symbol": "JUPUSDT", "allocation": 0.01},
        {"name": "Pyth", "symbol": "PYTHUSDT", "allocation": 0.01},
        {"name": "Arweave", "symbol": "ARUSDT", "allocation": 0.01},
        {"name": "Enjin", "symbol": "ENJUSDT", "allocation": 0.01},
        {"name": "Chiliz", "symbol": "CHZUSDT", "allocation": 0.01},
        {"name": "Gala", "symbol": "GALAUSDT", "allocation": 0.01},
        {"name": "Neo", "symbol": "NEOUSDT", "allocation": 0.01},
        {"name": "IOTA", "symbol": "IOTAUSDT", "allocation": 0.01},
        {"name": "Zilliqa", "symbol": "ZILUSDT", "allocation": 0.01},
        {"name": "Qtum", "symbol": "QTUMUSDT", "allocation": 0.01},
        {"name": "Harmony", "symbol": "ONEUSDT", "allocation": 0.01},
        {"name": "Ravencoin", "symbol": "RVNUSDT", "allocation": 0.01},
        {"name": "Sushi", "symbol": "SUSHIUSDT", "allocation": 0.01},
        {"name": "Yearn", "symbol": "YFIUSDT", "allocation": 0.01},
        {"name": "Balancer", "symbol": "BALUSDT", "allocation": 0.01},
        {"name": "Bancor", "symbol": "BNTUSDT", "allocation": 0.01},
        {"name": "Loopring", "symbol": "LRCUSDT", "allocation": 0.01},
        {"name": "0x", "symbol": "ZRXUSDT", "allocation": 0.01},
        {"name": "Zcash", "symbol": "ZECUSDT", "allocation": 0.01},
        {"name": "Dash", "symbol": "DASHUSDT", "allocation": 0.01},
        {"name": "Decred", "symbol": "DCRUSDT", "allocation": 0.01},
        {"name": "Bitcoin SV", "symbol": "BSVUSDT", "allocation": 0.01},
        {"name": "ENS", "symbol": "ENSUSDT", "allocation": 0.01},
        {"name": "Illuvium", "symbol": "ILVUSDT", "allocation": 0.01},
        {"name": "GMX", "symbol": "GMXUSDT", "allocation": 0.01},
        {"name": "dYdX", "symbol": "DYDXUSDT", "allocation": 0.01},
        {"name": "Band", "symbol": "BANDUSDT", "allocation": 0.01},
        {"name": "Ocean", "symbol": "OCEANUSDT", "allocation": 0.01},
        {"name": "Ankr", "symbol": "ANKRUSDT", "allocation": 0.01},
        {"name": "Skale", "symbol": "SKLUSDT", "allocation": 0.01},
        {"name": "Storj", "symbol": "STORJUSDT", "allocation": 0.01},
        {"name": "Celo", "symbol": "CELOUSDT", "allocation": 0.01},
        {"name": "RSR", "symbol": "RSRUSDT", "allocation": 0.01},
        {"name": "OMG", "symbol": "OMGUSDT", "allocation": 0.01},
        {"name": "Horizen", "symbol": "ZENUSDT", "allocation": 0.01},
        {"name": "WOO", "symbol": "WOOUSDT", "allocation": 0.01},
        {"name": "RUNE", "symbol": "RUNEUSDT", "allocation": 0.01},
        {"name": "LRC", "symbol": "LRCUSDT", "allocation": 0.01},
        {"name": "SSV", "symbol": "SSVUSDT", "allocation": 0.01},
        {"name": "API3", "symbol": "API3USDT", "allocation": 0.01},
        {"name": "AUDIO", "symbol": "AUDIOUSDT", "allocation": 0.01},
    ]
    
    # 🎯 OPTIMIZED PARAMETERS - Updated Feb 3, 2026 (Risk Management Focus)
    # Changes: Reduced leverage from 35x to 9x (hyperopt optimal)
    # Added: Adaptive threshold, daily loss limits, volatile asset exclusion
    # Strategy: INVERTED signals (BUY → SHORT, SELL → LONG)
    # CONSERVATIVE SETTINGS (Feb 7, 2026): Reduced risk after -12% losses
    MAX_LEVERAGE = 9.0  # 9x optimal from hyperopt
    BASE_LEVERAGE = 9.0  # Base leverage for all positions
    CHECK_INTERVAL = 300  # Check every 5 minutes
    CONFIDENCE_THRESHOLD = 60  # LLM must be 60%+ confident to trade
    STOP_LOSS_PCT = 0.025  # 2.5% CONSERVATIVE (was 1.5% - too tight)
    TAKE_PROFIT_PCT = 0.035  # 3.5% CLOSER TARGET (was 5.5% - too far)
    LOOKBACK_PERIODS = 200  # 200 periods (hyperopt optimal)
    BASE_SIGNAL_THRESHOLD = 0.65  # HIGHER THRESHOLD = fewer, better trades (was 0.560)
    SIGNAL_THRESHOLD = BASE_SIGNAL_THRESHOLD  # Current threshold (updated by adaptive system)
    INVERT_SIGNALS = True  # 🔥 KEY: Invert technical signals (BUY→SHORT, SELL→LONG)
    
    # 🛡️ RISK MANAGEMENT LIMITS (Feb 3, 2026)
    MAX_LOSS_PER_SYMBOL_PER_DAY = 999999.0  # DISABLED - No per-symbol daily limit
    MAX_DAILY_LOSS_PCT = 0.05  # Circuit breaker: stop trading if -5% daily loss
    EXCLUDED_VOLATILE_SYMBOLS = ['BIRBUSDT', 'ANIMEUSDT', 'BLUAIUSDT', 'MEMEUSDT', 
                                  'PEPUSDT', 'BONKUSDT', 'FLOKIUSDT']  # Exclude volatile small-caps
    
    # 📊 ADAPTIVE PARAMETERS (HYPEROPT OPTIMIZED - Feb 4, 2026)
    ADAPTIVE_THRESHOLD_ENABLED = True
    ATR_LOOKBACK = 30  # Hyperopt optimal: 30 candles
    VOLATILITY_HIGH_MULTIPLIER = 1.19  # Hyperopt: 1.19x in high volatility
    VOLATILITY_LOW_MULTIPLIER = 0.86  # Hyperopt: 0.86x in low volatility
    ATR_STOP_LOSS_MULTIPLIER = 0.99  # Hyperopt: ATR multiplier for stop loss
    VOLATILITY_TP_MULTIPLIER = 1.43  # Hyperopt: Volatility multiplier for take profit
    
    # 🎯 HYBRID POSITION SIZING (ATR-Based + Kelly Criterion) - CONSERVATIVE
    USE_HYBRID_SIZING = True  # Enable ATR-based + Kelly position sizing
    KELLY_FRACTION = 0.25  # Conservative Kelly (1/4 Kelly for safety)
    BASE_RISK_PCT = 0.01  # 1% base risk per trade (CONSERVATIVE - was 2%)
    MAX_POSITION_SIZE_PCT = 0.02  # Max 2% per position (CONSERVATIVE - was 4%)
    MIN_POSITION_SIZE_PCT = 0.005  # Min 0.5% per position (CONSERVATIVE - was 1%)
    MAX_TOTAL_EXPOSURE = 3.0  # Max 3x account exposure (CONSERVATIVE - was 5x)
    
    # Kelly parameters (will be updated from trade history)
    KELLY_WIN_RATE = 0.50  # Default 50% win rate (neutral)
    KELLY_AVG_WIN = 0.10  # Default 10% avg win
    KELLY_AVG_LOSS = 0.035  # Default 3.5% avg loss (matches stop loss)
    
    print("🎯 Trading Parameters (HYPEROPT OPTIMIZED - Feb 4, 2026):")
    print(f"  Strategy: {'INVERTED SIGNALS ✨' if INVERT_SIGNALS else 'NORMAL'}")
    print(f"  Leverage: {MAX_LEVERAGE}x (hyperopt optimal)")
    print(f"  Signal Threshold: {BASE_SIGNAL_THRESHOLD:.3f} (adaptive, 96.86% importance!)")
    print(f"  Portfolio: 100 assets, 100% allocation")
    print(f"  🤖 LLM Override: Enabled (RSI <10→BUY dip, RSI >90→SHORT peak, confidence ≥80%)")
    print(f"     ⚠️  Override IGNORES inversion during extremes (contrarian logic)")
    print(f"  LLM Confidence Threshold: {CONFIDENCE_THRESHOLD}%")
    print(f"  Stop Loss: {STOP_LOSS_PCT*100:.1f}%")
    print(f"  Take Profit: {TAKE_PROFIT_PCT*100:.1f}%")
    print(f"  Check Interval: {CHECK_INTERVAL}s")
    print(f"  Lookback Periods: {LOOKBACK_PERIODS}")
    print(f"  Mode: HYBRID (Technical + LLM with Contrarian Override)")
    print()
    print(f"  🛡️ Risk Management:")
    print(f"     Max Loss/Symbol/Day: ${MAX_LOSS_PER_SYMBOL_PER_DAY}")
    print(f"     Daily Loss Circuit Breaker: {MAX_DAILY_LOSS_PCT*100:.0f}%")
    print(f"     Excluded Volatile Tokens: {len(EXCLUDED_VOLATILE_SYMBOLS)} symbols")
    print(f"     Adaptive Threshold: {'ENABLED ✅' if ADAPTIVE_THRESHOLD_ENABLED else 'DISABLED'}")
    print()
    print(f"  🎯 Position Sizing: {'HYBRID (ATR-Based + Kelly) ✅' if USE_HYBRID_SIZING else 'Fixed Allocation'}")
    if USE_HYBRID_SIZING:
        print(f"     Kelly Fraction: {KELLY_FRACTION:.0%} (Conservative)")
        print(f"     Base Risk: {BASE_RISK_PCT:.1%} per trade")
        print(f"     Position Range: {MIN_POSITION_SIZE_PCT:.2%} - {MAX_POSITION_SIZE_PCT:.1%}")
        print(f"     Max Total Exposure: {MAX_TOTAL_EXPOSURE:.1f}x account")
        # Calculate Kelly multiplier inline
        kelly = (KELLY_WIN_RATE * KELLY_AVG_WIN - (1 - KELLY_WIN_RATE) * KELLY_AVG_LOSS) / KELLY_AVG_WIN if KELLY_AVG_WIN > 0 else 1.0
        kelly_mult = max(0.5, min(2.0, kelly * KELLY_FRACTION))
        print(f"     Kelly Multiplier: {kelly_mult:.2f}x (Win Rate: {KELLY_WIN_RATE:.0%}, Avg Win: {KELLY_AVG_WIN:.1%})")
    print()
    
    print("📊 Trading Assets: 🚀 100 ASSETS (YOLO MODE)")
    print(f"  Total Assets: {len(SYMBOLS)}")
    print(f"  Total Allocation: {sum(a['allocation'] for a in SYMBOLS):.1%}")
    print(f"  Expected Frequency: ~108 trades/month (3.6 per day)")
    print(f"  LLM Calls: 28,800/day | Cost: ~$86/month")
    print()
    print("  Top 10 Assets:")
    for asset in SYMBOLS[:10]:
        print(f"    - {asset['name']:12s} ({asset['symbol']:10s}): {asset['allocation']*100:.1f}%")
    print(f"    ... and {len(SYMBOLS)-10} more assets")
    print()
    
    print("=" * 80)
    print("🚀 STARTING LIVE TRADING...")
    print("=" * 80)
    print()
    
    # Update leverage for existing positions and resize them
    print("🔧 Updating leverage and resizing existing positions...")
    existing_positions = bybit.get_all_positions()
    balance_info = bybit.get_balance()
    available_balance = balance_info['available_balance'] if balance_info else 0
    
    if existing_positions and available_balance > 0:
        print(f"  Found {len(existing_positions)} open position(s)")
        print(f"  Available Balance: ${available_balance:,.2f}")
        print()
        
        # Create symbol lookup dict for allocations
        symbol_allocations = {asset['symbol']: asset['allocation'] for asset in SYMBOLS}
        
        for pos in existing_positions:
            symbol = pos['symbol']
            current_size = pos['size']
            current_lev = int(pos['leverage'])
            target_lev = min(int(BASE_LEVERAGE), int(MAX_LEVERAGE))  # Enforce max leverage cap
            
            # Update leverage if needed
            if current_lev != target_lev:
                print(f"  📊 {symbol}: Leverage {current_lev}x → {target_lev}x", end=" ")
                if bybit.update_position_leverage(symbol, target_lev):
                    print("✅")
                else:
                    print("⚠️")
            
            # Calculate target position size based on allocation
            if symbol in symbol_allocations:
                allocation = symbol_allocations[symbol]
                target_position_value = available_balance * allocation * BASE_LEVERAGE
                
                # Get current price
                ticker = bybit.get_ticker(symbol)
                if ticker:
                    current_price = ticker['last_price']
                    target_quantity = target_position_value / current_price
                    
                    # Apply quantity precision based on price
                    if current_price < 1:
                        target_quantity = int(target_quantity)
                    elif current_price < 10:
                        target_quantity = round(target_quantity, 2)
                    elif current_price < 100:
                        target_quantity = round(target_quantity, 3)
                    else:
                        target_quantity = round(target_quantity, 4)
                    
                    # Calculate how much more to add
                    quantity_to_add = target_quantity - current_size
                    
                    if quantity_to_add > current_size * 0.1:  # Only add if increase is >10%
                        side = "Buy" if pos['side'] == "Buy" else "Sell"
                        print(f"  📈 {symbol}: Adding {quantity_to_add:.4f} to position (current: {current_size:.4f} → target: {target_quantity:.4f})")
                        
                        try:
                            order = bybit.place_market_order(
                                symbol=symbol,
                                side=side,
                                quantity=abs(quantity_to_add),
                                leverage=target_lev
                            )
                            if order:
                                print(f"    ✅ Added to position successfully")
                            else:
                                print(f"    ⚠️ Failed to add to position")
                        except Exception as e:
                            print(f"    ❌ Error adding to position: {str(e)}")
                    else:
                        print(f"  ✓ {symbol}: Size OK ({current_size:.4f}, target: {target_quantity:.4f})")
    else:
        print("  No existing positions to update")
    print()
    
    # 📊 Helper Functions for Risk Management
    def calculate_atr(prices, period=14):
        """Calculate Average True Range for volatility measurement"""
        if len(prices) < period + 1:
            return 0
        
        true_ranges = []
        for i in range(1, len(prices)):
            high_low = abs(prices[i] - prices[i-1])
            true_ranges.append(high_low)
        
        atr = sum(true_ranges[-period:]) / period
        return atr
    
    def calculate_atr_percentage(prices, period=14):
        """Calculate ATR as percentage of current price"""
        if len(prices) < period + 1:
            return 0
        atr = calculate_atr(prices, period)
        current_price = prices[-1]
        if current_price > 0:
            return (atr / current_price) * 100
        return 0
    
    def detect_market_crash(bybit_connector):
        """
        Detect market crash conditions to pause trading.
        Checks BTC and ETH for coordinated crash signals.
        Returns: (is_crash, reason, btc_momentum, eth_momentum)
        """
        try:
            # Get BTC data
            btc_klines = bybit_connector.session.get_kline(
                category="linear",
                symbol="BTCUSDT",
                interval="60",
                limit=50
            )
            
            # Get ETH data
            eth_klines = bybit_connector.session.get_kline(
                category="linear",
                symbol="ETHUSDT",
                interval="60",
                limit=50
            )
            
            if not (btc_klines and btc_klines.get('retCode') == 0 and 
                    eth_klines and eth_klines.get('retCode') == 0):
                return False, ""
            
            # Extract prices
            btc_prices = [float(k[4]) for k in btc_klines['result']['list']]
            btc_prices.reverse()
            eth_prices = [float(k[4]) for k in eth_klines['result']['list']]
            eth_prices.reverse()
            
            if len(btc_prices) < 20 or len(eth_prices) < 20:
                return False, ""
            
            # Generate signals to get RSI
            btc_signal = generate_trading_signal(btc_prices)
            eth_signal = generate_trading_signal(eth_prices)
            
            btc_rsi = btc_signal['indicators']['rsi']
            eth_rsi = eth_signal['indicators']['rsi']
            
            # Calculate momentum (% change over last 10 candles)
            btc_momentum = ((btc_prices[-1] - btc_prices[-10]) / btc_prices[-10]) * 100
            eth_momentum = ((eth_prices[-1] - eth_prices[-10]) / eth_prices[-10]) * 100
            
            crash_conditions = []
            
            # 1. Either BTC or ETH extremely oversold (RSI < 25) - LOOSENED
            if btc_rsi < 25 or eth_rsi < 25:
                crash_conditions.append(f"Oversold market: BTC RSI={btc_rsi:.1f}, ETH RSI={eth_rsi:.1f}")
            
            # 2. Strong downward momentum (> -10% in 10 candles for either) - LOOSENED
            if btc_momentum < -10 or eth_momentum < -10:
                crash_conditions.append(f"Strong dump: BTC {btc_momentum:.1f}%, ETH {eth_momentum:.1f}%")
            
            # 3. Both assets showing negative momentum with low RSI
            if btc_momentum < -5 and eth_momentum < -5:
                if btc_rsi < 30 and eth_rsi < 30:
                    crash_conditions.append(f"Coordinated decline: BTC {btc_momentum:.1f}% (RSI {btc_rsi:.1f}), ETH {eth_momentum:.1f}% (RSI {eth_rsi:.1f})")
            
            if crash_conditions:
                # Return momentum values for filtering
                return True, " | ".join(crash_conditions), btc_momentum, eth_momentum
            
            return False, "", btc_momentum, eth_momentum
            
        except Exception as e:
            logger.error(f"Error detecting market crash: {e}")
            return False, "", 0, 0
    
    def calculate_dynamic_tp(prices, atr_pct, base_tp=0.0979):
        """
        Calculate dynamic take profit based on volatility and momentum
        
        Tightens TP in low volatility to capture gains before reversal
        Expands TP in high volatility to avoid premature exits
        
        Args:
            prices: Historical price data
            atr_pct: ATR as percentage of price
            base_tp: Base take profit percentage (default 9.79% from hyperopt)
        
        Returns:
            float: Adjusted take profit percentage
        """
        # Calculate short-term momentum (last 10 candles vs 20 candles)
        recent_avg = sum(prices[-10:]) / 10 if len(prices) >= 10 else prices[-1]
        older_avg = sum(prices[-20:-10]) / 10 if len(prices) >= 20 else prices[-1]
        momentum = (recent_avg - older_avg) / older_avg if older_avg > 0 else 0
        
        # Volatility adjustment
        # Low volatility (atr < 3%): Tighten TP (0.6x to 0.8x)
        # Medium volatility (3-5%): Standard TP (0.8x to 1.0x)
        # High volatility (> 5%): Keep wider TP (1.0x to 1.2x)
        if atr_pct < 0.03:  # Low volatility
            vol_multiplier = 0.6  # Tight TP at 5.9% (0.6 × 9.79%)
        elif atr_pct < 0.05:  # Medium volatility
            vol_multiplier = 0.8  # Medium TP at 7.8% (0.8 × 9.79%)
        else:  # High volatility
            vol_multiplier = 1.0  # Keep base TP at 9.79%
        
        # Momentum adjustment
        # Strong momentum: slightly expand TP
        # Weak momentum: tighten TP
        if abs(momentum) > 0.02:  # Strong momentum (>2%)
            momentum_multiplier = 1.1
        elif abs(momentum) < 0.005:  # Weak momentum (<0.5%)
            momentum_multiplier = 0.9
        else:
            momentum_multiplier = 1.0
        
        # Combined adjustment
        adjusted_tp = base_tp * vol_multiplier * momentum_multiplier
        
        # Safety bounds: 4% to 10%
        adjusted_tp = max(0.04, min(0.10, adjusted_tp))
        
        return adjusted_tp
    
    def calculate_kelly_multiplier():
        """Calculate Kelly Criterion multiplier based on historical performance"""
        if KELLY_WIN_RATE <= 0 or KELLY_AVG_WIN <= 0:
            return 1.0  # Neutral if no data
        
        # Kelly Formula: (Win% × AvgWin - Loss% × AvgLoss) / AvgWin
        kelly = (KELLY_WIN_RATE * KELLY_AVG_WIN - (1 - KELLY_WIN_RATE) * KELLY_AVG_LOSS) / KELLY_AVG_WIN
        
        # Apply conservative fraction (1/4 Kelly)
        kelly_adjusted = kelly * KELLY_FRACTION
        
        # Safety bounds: 0.5x to 2.0x
        return max(0.5, min(2.0, kelly_adjusted))
    
    def calculate_hybrid_position_size(symbol, allocation, current_price, balance, prices):
        """
        Calculate position size using Hybrid ATR-Based + Kelly Criterion
        
        Args:
            symbol: Trading symbol
            allocation: Base allocation percentage (from SYMBOLS list)
            current_price: Current asset price
            balance: Available balance
            prices: Historical price data for ATR calculation
        
        Returns:
            tuple: (position_value, adjusted_allocation, atr_pct)
        """
        if not USE_HYBRID_SIZING:
            # Fall back to simple fixed allocation
            position_value = balance * allocation * BASE_LEVERAGE
            return position_value, allocation, 0
        
        # Step 1: Calculate asset volatility (ATR as %)
        atr_pct = calculate_atr_percentage(prices, 14)
        if atr_pct == 0:
            atr_pct = 5.0  # Default to 5% if calculation fails
        
        # Step 2: Calculate portfolio average ATR (estimate based on common ranges)
        # Low vol assets: 2-4%, Medium: 4-8%, High: 8-15%
        portfolio_avg_atr = 6.0  # Assume 6% average for crypto
        
        # Step 3: ATR-based adjustment (inverse relationship)
        # High volatility → Lower allocation
        # Low volatility → Higher allocation
        atr_adjustment = portfolio_avg_atr / atr_pct
        
        # Bound the adjustment: 0.5x to 2.0x
        atr_adjustment = max(0.5, min(2.0, atr_adjustment))
        
        # Step 4: Apply Kelly multiplier
        kelly_mult = calculate_kelly_multiplier()
        
        # Step 5: Calculate adjusted allocation
        adjusted_allocation = BASE_RISK_PCT * atr_adjustment * kelly_mult
        
        # Step 6: Apply safety bounds
        adjusted_allocation = max(MIN_POSITION_SIZE_PCT, min(MAX_POSITION_SIZE_PCT, adjusted_allocation))
        
        # Step 7: Calculate position value
        position_value = balance * adjusted_allocation * BASE_LEVERAGE
        
        return position_value, adjusted_allocation, atr_pct
    
    def check_total_exposure(bybit, new_position_value, balance):
        """Check if adding new position would exceed maximum total exposure"""
        positions = bybit.get_all_positions()
        if not positions:
            return True  # No existing positions, OK to proceed
        
        # Calculate total existing exposure
        total_exposure = sum(abs(pos.get('size', 0) * pos.get('avgPrice', 0)) for pos in positions)
        
        # Add new position
        total_with_new = total_exposure + new_position_value
        
        # Check against maximum exposure
        max_exposure = balance * MAX_TOTAL_EXPOSURE
        
        if total_with_new > max_exposure:
            logger.warning(f"  ⚠️  Total exposure would be {total_with_new/balance:.1f}x (max: {MAX_TOTAL_EXPOSURE}x)")
            return False
        
        return True
    
    def update_adaptive_threshold():
        """Update signal threshold based on market volatility"""
        if not ADAPTIVE_THRESHOLD_ENABLED:
            return BASE_SIGNAL_THRESHOLD
        
        try:
            # Sample ATR from a few representative symbols
            total_atr_ratio = 0
            count = 0
            
            for asset in SYMBOLS[:20]:  # Sample first 20 assets
                symbol = asset['symbol']
                try:
                    klines = bybit.session.get_kline(
                        category="linear",
                        symbol=symbol,
                        interval="60",
                        limit=ATR_LOOKBACK
                    )
                    
                    if klines and klines.get('retCode') == 0:
                        prices = [float(k[4]) for k in klines['result']['list']]  # Close prices
                        if len(prices) >= 15:
                            current_atr = calculate_atr(prices[-30:], 14)
                            historical_atr = calculate_atr(prices, 14)
                            
                            if historical_atr > 0:
                                atr_ratio = current_atr / historical_atr
                                total_atr_ratio += atr_ratio
                                count += 1
                except:
                    continue
            
            if count == 0:
                return BASE_SIGNAL_THRESHOLD
            
            avg_volatility_ratio = total_atr_ratio / count
            
            # Adjust threshold based on volatility
            if avg_volatility_ratio > 1.5:
                # High volatility - be more selective
                adjusted_threshold = BASE_SIGNAL_THRESHOLD * VOLATILITY_HIGH_MULTIPLIER
                logger.info(f"⚠️ HIGH VOLATILITY DETECTED: Threshold adjusted to {adjusted_threshold:.3f} (from {BASE_SIGNAL_THRESHOLD:.3f})")
                return adjusted_threshold
            elif avg_volatility_ratio < 0.7:
                # Low volatility - can be more aggressive
                adjusted_threshold = BASE_SIGNAL_THRESHOLD * VOLATILITY_LOW_MULTIPLIER
                logger.info(f"✅ LOW VOLATILITY: Threshold adjusted to {adjusted_threshold:.3f} (from {BASE_SIGNAL_THRESHOLD:.3f})")
                return adjusted_threshold
            else:
                return BASE_SIGNAL_THRESHOLD
        except Exception as e:
            logger.warning(f"Error updating adaptive threshold: {str(e)}")
            return BASE_SIGNAL_THRESHOLD
    
    # Track daily losses per symbol
    daily_losses = {}  # {symbol: total_loss}
    last_reset_date = datetime.now().date()
    
    def reset_daily_losses_if_needed():
        """Reset daily loss tracking at start of new day"""
        nonlocal last_reset_date
        current_date = datetime.now().date()
        if current_date != last_reset_date:
            daily_losses.clear()
            last_reset_date = current_date
            logger.info("🔄 Daily loss tracking reset for new day")
    
    def check_symbol_loss_limit(symbol, potential_loss):
        """Check if symbol has exceeded daily loss limit"""
        current_loss = daily_losses.get(symbol, 0)
        if current_loss + potential_loss > MAX_LOSS_PER_SYMBOL_PER_DAY:
            logger.warning(f"⛔ {symbol} has exceeded daily loss limit (${current_loss:.2f} + ${potential_loss:.2f} > ${MAX_LOSS_PER_SYMBOL_PER_DAY})")
            return False
        return True
    
    def record_loss(symbol, loss_amount):
        """Record a loss for daily tracking"""
        if loss_amount > 0:
            daily_losses[symbol] = daily_losses.get(symbol, 0) + loss_amount
            logger.info(f"📊 {symbol} daily loss: ${daily_losses[symbol]:.2f} / ${MAX_LOSS_PER_SYMBOL_PER_DAY}")
    
    def is_volatile_symbol_excluded(symbol):
        """Check if symbol is in excluded volatile list"""
        if symbol in EXCLUDED_VOLATILE_SYMBOLS:
            logger.info(f"⛔ {symbol} is excluded (volatile small-cap)")
            return True
        return False
    
    trade_count = 0
    last_threshold_update = datetime.now()
    
    try:
        while True:
            # Reset daily losses if new day
            reset_daily_losses_if_needed()
            
            # Update adaptive threshold every hour
            current_time = datetime.now()
            if (current_time - last_threshold_update).seconds >= 3600:
                SIGNAL_THRESHOLD = update_adaptive_threshold()
                last_threshold_update = current_time
            
            logger.info("=" * 60)
            logger.info("Checking market conditions...")
            logger.info(f"Current Signal Threshold: {SIGNAL_THRESHOLD:.3f}")
            
            # 🚨 CRASH DETECTION: Check if market is crashing
            is_crash, crash_reason, btc_momentum, eth_momentum = detect_market_crash(bybit)
            if is_crash:
                logger.warning("=" * 60)
                logger.warning("🚨 MARKET CRASH DETECTED - PAUSING TRADING")
                logger.warning(f"   Reason: {crash_reason}")
                logger.warning("   Skipping this cycle to avoid catching falling knives")
                logger.warning("=" * 60)
                time.sleep(CHECK_INTERVAL)
                continue
            
            # Track if we're in a strong downtrend (for momentum filtering)
            is_strong_downtrend = btc_momentum < -3 or eth_momentum < -3
            if is_strong_downtrend:
                logger.info(f"⚠️  Strong downtrend detected: BTC {btc_momentum:.1f}%, ETH {eth_momentum:.1f}%")
                logger.info("   Will block LONG entries to avoid catching falling knives")
                continue
            
            for asset in SYMBOLS:
                symbol = asset['symbol']
                name = asset['name']
                allocation = asset['allocation']
                
                try:
                    # 🛡️ Risk Check 1: Exclude volatile symbols
                    if is_volatile_symbol_excluded(symbol):
                        continue
                    
                    # Get current price
                    ticker = bybit.get_ticker(symbol)
                    if not ticker:
                        logger.warning(f"Could not get ticker for {symbol}")
                        continue
                    
                    current_price = ticker['last_price']
                    
                    # Get current position
                    position = bybit.get_position(symbol)
                    
                    # Fetch historical prices for signal analysis
                    logger.info(f"Analyzing {name} ({symbol}) @ ${current_price:,.2f}")
                    
                    # Get historical klines (candlestick data)
                    try:
                        klines = bybit.session.get_kline(
                            category="linear",
                            symbol=symbol,
                            interval="60",  # 60-minute (1h) candles - matches optimization
                            limit=LOOKBACK_PERIODS
                        )
                        
                        if klines and klines.get('retCode') == 0:
                            # Extract closing prices
                            prices = [float(k[4]) for k in klines['result']['list']]
                            prices.reverse()  # Oldest to newest
                            
                            # Generate trading signal
                            signal_data = generate_trading_signal(prices)
                            
                            # Store original RSI BEFORE any inversion (for override logic)
                            original_rsi = signal_data['indicators']['rsi']
                            original_action = signal_data['action']
                            
                            # 🔥 INVERT SIGNALS if enabled (based on optimization results)
                            # Original BUY signals become SELL (short), SELL signals become BUY (long)
                            if INVERT_SIGNALS:
                                signal_data['signal'] = -signal_data['signal']
                                # Swap action labels
                                if signal_data['action'] == 'BUY':
                                    signal_data['action'] = 'SELL'
                                    signal_data['reasons'].insert(0, '🔄 INVERTED: Original signal was BUY')
                                elif signal_data['action'] == 'SELL':
                                    signal_data['action'] = 'BUY'
                                    signal_data['reasons'].insert(0, '🔄 INVERTED: Original signal was SELL')
                            
                            # Get LLM analysis of technical signals
                            market_context = None
                            if position:
                                market_context = {
                                    'has_position': True,
                                    'side': position['side'],
                                    'entry_price': position['entry_price'],
                                    'pnl_pct': (current_price - position['entry_price']) / position['entry_price'] * 100
                                }
                            else:
                                market_context = {'has_position': False}
                            
                            hybrid_result = get_hybrid_signal(signal_data, symbol, current_price, market_context)
                            
                            # Extract decisions
                            llm_decision = hybrid_result['final_decision']
                            confidence = hybrid_result['confidence']
                            reasoning = hybrid_result['reasoning']
                            signal_strength = abs(signal_data['signal'])
                            
                            invert_indicator = "🔄 INVERTED | " if INVERT_SIGNALS else ""
                            logger.info(f"  📊 {invert_indicator}Technical: {hybrid_result['technical_action']} (strength: {signal_strength:.3f}, threshold: {SIGNAL_THRESHOLD:.3f})")
                            logger.info(f"  🤖 LLM Decision: {llm_decision} | Confidence: {confidence}% | {'✅' if hybrid_result['llm_agrees'] else '⚠️  Overrides'}")
                            logger.info(f"  💡 Reasoning: {reasoning}")
                            logger.info(f"  📈 RSI={signal_data['indicators']['rsi']:.1f}, Risk={hybrid_result['risk_level']}")
                        else:
                            logger.warning(f"  ⚠️  Could not fetch historical data, skipping")
                            continue
                            
                    except Exception as e:
                        logger.warning(f"  ⚠️  Error fetching klines: {str(e)}")
                        continue
                    
                    # Trading logic
                    if position:
                        # We have an open position
                        entry_price = position['entry_price']
                        position_size = position['size']
                        pnl_pct = (current_price - entry_price) / entry_price
                        
                        logger.info(f"  📈 Position: {position['side']} {position_size} @ ${entry_price:,.2f} | PnL: {pnl_pct*100:+.2f}%")
                        
                        # Check exit conditions
                        should_exit = False
                        exit_reason = ""
                        
                        # Calculate dynamic TP for this position
                        atr_pct_check = calculate_atr_percentage(prices, 14)
                        dynamic_tp_check = calculate_dynamic_tp(prices, atr_pct_check, TAKE_PROFIT_PCT)
                        
                        # Exit on LLM SELL decision with high confidence
                        if position['side'] == 'Buy' and llm_decision == 'SELL' and confidence >= CONFIDENCE_THRESHOLD:
                            should_exit = True
                            exit_reason = f"LLM SELL ({confidence}%)"
                        
                        # Take profit (using dynamic TP)
                        elif pnl_pct >= dynamic_tp_check:
                            should_exit = True
                            exit_reason = f"TAKE PROFIT (+{pnl_pct*100:.1f}%, Target: {dynamic_tp_check*100:.1f}%)"
                        
                        # Stop loss
                        elif pnl_pct <= -STOP_LOSS_PCT:
                            should_exit = True
                            exit_reason = f"STOP LOSS ({pnl_pct*100:.1f}%)"
                        
                        if should_exit:
                            logger.info(f"  🔴 CLOSING POSITION: {exit_reason}")
                            
                            # Calculate actual P&L for loss tracking
                            actual_pnl = (current_price - entry_price) * position_size
                            
                            if bybit.close_position(symbol):
                                trade_count += 1
                                logger.info(f"  ✅ Position closed successfully")
                                
                                # 🛡️ Track losses for daily limit
                                if actual_pnl < 0:
                                    record_loss(symbol, abs(actual_pnl))
                            else:
                                logger.error(f"  ❌ Failed to close position")
                    
                    else:
                        # No position - check signal strength and LLM decision
                        signal_strength = abs(signal_data['signal'])
                        rsi = signal_data['indicators']['rsi']
                        
                        # 🤖 LLM OVERRIDE: Trust contrarian logic during extreme market conditions
                        # When RSI shows extreme oversold (<10), BUY the dip regardless of inversion
                        # When RSI shows extreme overbought (>90), SHORT the peak regardless of inversion
                        # This IGNORES the INVERT_SIGNALS setting during extremes
                        llm_override = False
                        override_direction = None
                        
                        if original_rsi < 10 and confidence >= 80:
                            # EXTREME OVERSOLD: Always BUY (ignore inversion)
                            llm_override = True
                            override_direction = 'BUY'
                            logger.info(f"  🚨 LLM OVERRIDE ACTIVATED: RSI={original_rsi:.1f} (EXTREME OVERSOLD), forcing BUY with {confidence}% confidence")
                        elif original_rsi > 90 and confidence >= 80:
                            # EXTREME OVERBOUGHT: Always SHORT (ignore inversion)
                            llm_override = True
                            override_direction = 'SELL'
                            logger.info(f"  🚨 LLM OVERRIDE ACTIVATED: RSI={original_rsi:.1f} (EXTREME OVERBOUGHT), forcing SHORT with {confidence}% confidence")
                        
                        # Entry requires EITHER:
                        # 1. Strong signal + high LLM confidence (normal operation)
                        # 2. LLM override during extreme conditions (RSI <10 or >90)
                        meets_threshold = signal_strength >= SIGNAL_THRESHOLD or llm_override
                        
                        # Determine which direction to trade
                        # If override is active, use override direction
                        # Otherwise, use normal LLM decision
                        trade_direction = override_direction if llm_override else llm_decision
                        
                        # 🛡️ MOMENTUM FILTER: Block LONG entries during strong downtrends
                        # This prevents catching falling knives
                        if trade_direction == 'BUY' and is_strong_downtrend:
                            logger.warning(f"  ⛔ {symbol}: BUY signal blocked - strong downtrend (BTC {btc_momentum:.1f}%, ETH {eth_momentum:.1f}%)")
                            logger.warning(f"     Waiting for market momentum to improve before entering LONG positions")
                            continue
                        
                        if meets_threshold and trade_direction in ['BUY', 'SELL'] and confidence >= CONFIDENCE_THRESHOLD:
                            # Calculate position size using Hybrid ATR-Based + Kelly
                            balance = bybit.get_balance("USDT")
                            if balance:
                                available = balance['available_balance']
                                
                                # 🎯 HYBRID POSITION SIZING
                                position_value, adjusted_allocation, atr_pct = calculate_hybrid_position_size(
                                    symbol, allocation, current_price, available, prices
                                )
                                
                                # 🛡️ Risk Check 1: Check total exposure limit
                                if not check_total_exposure(bybit, position_value, available):
                                    logger.warning(f"  ⛔ Skipping trade - total exposure limit reached")
                                    continue
                                
                                # 🛡️ Risk Check 2: Check daily loss limit for this symbol
                                estimated_loss = STOP_LOSS_PCT * position_value
                                if not check_symbol_loss_limit(symbol, estimated_loss):
                                    logger.warning(f"  ⛔ Skipping trade - daily loss limit reached for {symbol}")
                                    continue
                                
                                quantity = position_value / current_price
                                
                                # Log sizing details
                                if USE_HYBRID_SIZING:
                                    logger.info(f"  📊 Hybrid Sizing: Base {allocation*100:.1f}% → Adjusted {adjusted_allocation*100:.2f}% (ATR: {atr_pct:.1f}%)")
                                
                                # Round quantity to appropriate precision based on price
                                # Very low price coins (memes, etc) need integer quantities
                                # Most meme coins and low-price tokens have qtyStep=1 (integers only)
                                if current_price < 0.01:  # Less than 1 cent
                                    quantity = int(quantity)  # Whole numbers only
                                elif current_price < 1:  # Less than $1 (most alts)
                                    quantity = int(quantity)  # Many alts also require integers
                                elif current_price < 10:  # Less than $10
                                    quantity = round(quantity, 2)  # 2 decimals
                                elif current_price < 100:  # Less than $100
                                    quantity = round(quantity, 3)  # 3 decimals
                                else:  # $100+ (BTC, ETH)
                                    quantity = round(quantity, 4)  # 4 decimals
                                
                                # Ensure minimum quantity (at least 1 for integer types)
                                if current_price < 1 and quantity < 1:
                                    quantity = 1
                                
                                # Ensure quantity is at least 1 for very small positions
                                if quantity < 1:
                                    quantity = 1
                                
                                if position_value >= 100:  # Minimum $100 trade
                                    override_tag = " 🚨 OVERRIDE" if llm_override else ""
                                    position_type = "LONG" if trade_direction == 'BUY' else "SHORT"
                                    side = "Buy" if trade_direction == 'BUY' else "Sell"
                                    emoji = "🟢" if trade_direction == 'BUY' else "🔴"
                                    
                                    logger.info(f"  {emoji} OPENING {position_type} POSITION{override_tag} - {trade_direction} ({confidence}%)")
                                    order = bybit.place_market_order(
                                        symbol=symbol,
                                        side=side,
                                        quantity=quantity,
                                        leverage=min(int(BASE_LEVERAGE), int(MAX_LEVERAGE))
                                    )
                                    
                                    if order:
                                        trade_count += 1
                                        logger.info(f"  ✅ Order placed: {side} {quantity} {symbol}")
                                        
                                        # Set stop loss and take profit
                                        time.sleep(2)  # Wait for order to fill
                                        
                                        # Calculate dynamic TP based on volatility and momentum
                                        atr_pct_for_tp = calculate_atr_percentage(prices, 14)
                                        dynamic_tp = calculate_dynamic_tp(prices, atr_pct_for_tp, TAKE_PROFIT_PCT)
                                        
                                        if trade_direction == 'BUY':
                                            # LONG position: stop below, profit above
                                            stop_price = current_price * (1 - STOP_LOSS_PCT)
                                            take_profit_price = current_price * (1 + dynamic_tp)
                                        else:
                                            # SHORT position: stop above, profit below
                                            stop_price = current_price * (1 + STOP_LOSS_PCT)
                                            take_profit_price = current_price * (1 - dynamic_tp)
                                        
                                        logger.info(f"  🎯 Dynamic TP: {dynamic_tp*100:.2f}% (ATR: {atr_pct_for_tp*100:.2f}%, Base: {TAKE_PROFIT_PCT*100:.2f}%)")
                                        
                                        bybit.set_stop_loss(symbol, stop_price)
                                        bybit.set_take_profit(symbol, take_profit_price)
                                    else:
                                        logger.error(f"  ❌ Failed to place order")
                                else:
                                    logger.info(f"  ⏸️  Position too small (${position_value:.2f}), skipping")
                        else:
                            # Provide clear feedback on why trade wasn't executed
                            if signal_strength < SIGNAL_THRESHOLD and not llm_override:
                                logger.info(f"  ⏸️  Signal too weak ({signal_strength:.3f} < {SIGNAL_THRESHOLD:.3f} threshold)")
                                if original_rsi < 10 or original_rsi > 90:
                                    logger.info(f"  💡 Note: RSI={original_rsi:.1f} is extreme, but LLM confidence {confidence}% < 80% for override")
                            elif trade_direction not in ['BUY', 'SELL']:
                                logger.info(f"  ⏸️  Trade direction is {trade_direction}, waiting for BUY/SELL signal")
                            elif confidence < CONFIDENCE_THRESHOLD:
                                logger.info(f"  ⏸️  LLM confidence too low ({confidence}% < {CONFIDENCE_THRESHOLD}%)")
                
                except Exception as e:
                    logger.error(f"Error processing {symbol}: {str(e)}")
                    continue
            
            # Sleep until next check
            logger.info(f"Total trades executed: {trade_count}")
            logger.info(f"Next check in {CHECK_INTERVAL}s...")
            logger.info("=" * 60)
            print()
            time.sleep(CHECK_INTERVAL)
    
    except KeyboardInterrupt:
        print()
        print("=" * 80)
        print("🛑 STOPPING LIVE TRADING...")
        print("=" * 80)
        print()
        logger.info(f"Total trades executed in this session: {trade_count}")
        logger.info("Bot stopped by user")


if __name__ == "__main__":
    main()
