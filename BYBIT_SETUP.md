# Bybit Live Trading Setup Guide

## 🎯 Overview
This guide will help you connect your LLM crypto trading bot to Bybit's demo account for live trading with virtual funds.

## 📋 Prerequisites
- Python 3.8+
- Active Bybit account
- All required packages installed (`pybit` has been added)

## 🔧 Step 1: Create Bybit Demo Account API Keys

### Option A: Using Demo Account (Recommended for Testing)
1. **Visit Bybit**: Go to [https://www.bybit.com](https://www.bybit.com)
2. **Login**: Sign into your Bybit account
3. **Go to API Management**: 
   - Click your profile icon (top right)
   - Select "API Management" or go to [https://www.bybit.com/user/account](https://www.bybit.com/user/account)
4. **Create Demo API Key**:
   - Look for "Demo Trading" or "Unified Trading Account (Demo)"
   - Click "Create New Key"
   - Give it a name (e.g., "LLM Trading Bot")
5. **Set Permissions**:
   - ✅ Enable: **Read/Write** (for placing orders)
   - ✅ Enable: **Unified Trading** (for futures/perpetual contracts)
   - ❌ Disable: Withdrawals (not needed for trading)
6. **Save Credentials**:
   - Copy your **API Key**
   - Copy your **API Secret** (shown only once!)
   - Store them securely

### Important Notes:
- **Demo account** uses virtual funds (fake money) - perfect for testing
- Demo trading simulates real market conditions
- No risk of losing real money
- API keys are different for demo vs live accounts

## 🔐 Step 2: Configure Your Bot

Edit `src/config.ini` and replace the placeholder values:

```ini
[bybit]
api_key = YOUR_ACTUAL_API_KEY_HERE
api_secret = YOUR_ACTUAL_API_SECRET_HERE
demo = true
```

**Example** (don't use these - they're fake):
```ini
[bybit]
api_key = xCpJ9K3mF2nR8vL1
api_secret = 7hG4kP8mN2qT5wR9vX3cB6fJ1nL4sD8m
demo = true
```

⚠️ **Security Best Practices:**
- Never commit `config.ini` to version control (it's in `.gitignore`)
- Never share your API keys publicly
- Use demo keys for testing first
- Enable IP whitelist restrictions on Bybit if possible

## 🚀 Step 3: Run Live Trading

Once configured, start the live trading bot:

```bash
python src/live_trading.py
```

## 📊 What the Bot Does

### Trading Strategy:
1. **Analyzes Sentiment**: Uses LLM to analyze crypto news headlines
2. **Multi-Asset Trading**: Trades 8 cryptocurrencies simultaneously
3. **Leveraged Positions**: Uses 5x leverage for amplified returns
4. **Risk Management**: 
   - Stop Loss: 3% per trade
   - Take Profit: 8% per trade
   - Automatic position sizing based on portfolio allocation

### Trading Cycle:
1. Every 5 minutes, the bot:
   - Fetches latest news for each crypto
   - Analyzes sentiment using Groq LLM
   - Checks existing positions
   - Opens new positions on strong positive sentiment (>0.65)
   - Closes positions on negative sentiment (<-0.20) or stop/take profit levels

### Assets Traded:
- Bitcoin (BTC) - 25% allocation
- Ethereum (ETH) - 20% allocation
- Solana (SOL) - 10% allocation
- Avalanche (AVAX) - 10% allocation
- BNB - 10% allocation
- Ripple (XRP) - 10% allocation
- Cardano (ADA) - 8% allocation
- Dogecoin (DOGE) - 7% allocation

## 📈 Monitoring Your Bot

The bot will display:
- Current market prices
- Sentiment scores for each asset
- Position status (open/closed)
- Trade execution confirmations
- P&L for each position

**Example Output:**
```
2026-01-28 10:30:15 | INFO | Analyzing Bitcoin (BTCUSDT) @ $92,450.00
2026-01-28 10:30:16 | INFO |   Sentiment Score: 0.78
2026-01-28 10:30:17 | INFO |   🟢 OPENING POSITION: Score=0.78
2026-01-28 10:30:18 | INFO |   ✅ Order placed: 0.135 BTCUSDT
```

## 🛑 Stopping the Bot

To stop the bot safely:
1. Press `Ctrl+C` in the terminal
2. The bot will display final statistics
3. Existing positions will remain open (close them manually on Bybit if needed)

## 🔍 Checking Your Results

### On Bybit Dashboard:
1. Go to [https://www.bybit.com](https://www.bybit.com)
2. Switch to **Demo Trading** mode
3. View:
   - **Positions**: See open trades
   - **Orders**: View order history
   - **Assets**: Check your P&L
   - **Transaction History**: Detailed trade logs

## ⚙️ Customizing Trading Parameters

Edit `src/live_trading.py` to adjust:

```python
LEVERAGE = 5.0              # Change leverage (1x to 10x)
CHECK_INTERVAL = 300        # How often to check (seconds)
BUY_THRESHOLD = 0.65        # Sentiment threshold to buy
SELL_THRESHOLD = -0.20      # Sentiment threshold to sell
STOP_LOSS_PCT = 0.03        # Stop loss percentage (3%)
TAKE_PROFIT_PCT = 0.08      # Take profit percentage (8%)
```

## 🚨 Important Warnings

1. **Start with Demo**: Always test with demo account first
2. **Monitor Regularly**: Check bot performance frequently
3. **Leverage Risk**: 5x leverage can amplify both gains AND losses
4. **API Limits**: Bybit has rate limits - don't modify intervals too aggressively
5. **News Quality**: Bot performance depends on news quality and LLM accuracy
6. **Not Financial Advice**: This is experimental software for educational purposes

## 🐛 Troubleshooting

### "API credentials not configured"
- Make sure you edited `src/config.ini`
- Check that you replaced the placeholder text

### "Failed to get account information"
- Verify your API key and secret are correct
- Check that you created a **Demo Trading** API key
- Ensure API has "Read/Write" and "Unified Trading" permissions

### "Could not get ticker for SYMBOL"
- Check your internet connection
- Verify Bybit API is not down (check status.bybit.com)
- Some symbols may have different names on Bybit

### "Failed to place order"
- Check you have sufficient demo balance
- Verify leverage settings are within Bybit limits
- Position size may be too small (minimum $100)

## 📚 Next Steps

1. ✅ Run in demo mode for at least 1 week
2. ✅ Monitor performance and adjust parameters
3. ✅ Review trade logs and P&L
4. ⚠️ Only switch to live trading if consistently profitable in demo
5. ⚠️ Start with small amounts on live account

## 🆘 Support

- Bybit API Documentation: [https://bybit-exchange.github.io/docs/](https://bybit-exchange.github.io/docs/)
- Pybit Library: [https://github.com/bybit-exchange/pybit](https://github.com/bybit-exchange/pybit)

---

**Disclaimer**: Cryptocurrency trading involves substantial risk. This bot is provided as-is for educational purposes. Past performance does not guarantee future results. Only trade with funds you can afford to lose.
