# 🤖 Hybrid Trading System: LLM + Technical Analysis

## What It Does

The hybrid system combines **mathematical technical indicators** with **AI reasoning** to make smarter trading decisions.

### Flow:
```
Price Data → Technical Indicators → LLM Analysis → Final Decision
```

## How It Works

### Step 1: Technical Analysis (Math-Based)
Calculates 5 indicators from price data:

1. **RSI** - Is the asset oversold (<30) or overbought (>70)?
2. **Moving Averages** - Is price trending up or down vs MA(20) and MA(50)?
3. **MACD** - What's the momentum direction?
4. **Bollinger Bands** - Is price at extremes?
5. **Price Momentum** - Recent % change over 10 periods

→ Outputs: Technical signal from -1.0 (SELL) to +1.0 (BUY)

### Step 2: LLM Analysis (AI Reasoning)
The LLM (Llama 3.3 70B) receives:
- All 5 technical indicators with exact values
- Current price and market context
- Any existing position info (entry price, P&L%)

The LLM then:
- **Analyzes conflicts** - "RSI says overbought but MACD says bullish"
- **Considers context** - "In a strong uptrend, overbought can continue"
- **Weighs risk** - "High RSI + near Bollinger upper = reversal risk"
- **Makes decision** - BUY, SELL, or HOLD with confidence %

### Step 3: Final Decision
- **Only trades if LLM confidence ≥ 60%**
- LLM can override technical signals
- Provides reasoning for every decision

## Example: LLM Override

**Test Result from Earlier:**

```
Technical Indicators Say: BUY (+0.40 signal)
- MACD: Bullish
- Momentum: Strong upward
- Moving averages: Trending up

LLM Decision: SELL (80% confidence)
Reasoning: "Despite bullish MACD and momentum, the extremely 
overbought RSI (94.6) suggests high likelihood of correction. 
Price near Bollinger upper band confirms reversal risk."

Key Factor: RSI (94.6)
```

**Result:** LLM **overrode** the technical BUY signal to prevent buying at the top!

## Benefits

### vs Pure Technical Signals:
- ✅ **Contextual understanding** - Not just "RSI > 70 = sell"
- ✅ **Handles conflicts** - Knows when to trust which indicator
- ✅ **Market awareness** - Understands trend strength
- ✅ **Risk assessment** - Evaluates probability of success

### vs Pure Sentiment (Old System):
- ✅ **No news delays** - Instant technical analysis
- ✅ **More objective** - Not swayed by hype/FUD
- ✅ **Always available** - No dependency on news APIs
- ✅ **Faster decisions** - Processes every 5 minutes

## Trading Rules

### Open Position:
- LLM decision = BUY
- Confidence ≥ 60%
- Minimum $100 trade size

### Close Position:
1. **LLM Exit**: LLM says SELL with ≥60% confidence
2. **Take Profit**: +8% gain
3. **Stop Loss**: -3% loss

## Configuration

Current settings in `live_trading.py`:

```python
CONFIDENCE_THRESHOLD = 60   # LLM must be 60%+ confident
STOP_LOSS_PCT = 0.03       # 3% stop loss
TAKE_PROFIT_PCT = 0.08     # 8% take profit
LEVERAGE = 5x              # 5x leverage
LOOKBACK_PERIODS = 100     # Analyze last 100 candles
CHECK_INTERVAL = 300s      # Check every 5 minutes
```

## Output Example

When bot runs, you'll see:

```
INFO: Analyzing Bitcoin (BTCUSDT) @ $84,655.00
INFO:   📊 Technical: BUY (+0.35)
INFO:   🤖 LLM Decision: HOLD | Confidence: 55% | ⚠️  Overrides
INFO:   💡 Reasoning: Mixed signals - RSI neutral but MACD weak
INFO:   📈 RSI=52.3, Risk=MEDIUM
INFO:   ⏸️  LLM says HOLD but confidence too low (55% < 60%)
```

## Backtest Performance

### Pure Technical (No LLM):
- 14-day return: **-17.24%**
- Win rate: 0%
- All trades hit stop loss

### Hybrid System:
- To be tested!
- Expected: Better filtering of bad signals
- LLM should prevent overtrading

## Running Hybrid Backtest

**Warning:** Makes many LLM API calls (~5-10 min for 7 days of data)

```bash
python backtest_hybrid.py
```

Tests last 7 days on BTC and ETH with LLM analysis.

## Running Live with Hybrid

The bot is now configured for hybrid mode:

```bash
python src/live_trading.py
```

Will show:
- Technical indicator values
- LLM decision + confidence
- Reasoning for each decision
- Whether LLM agrees or overrides

## Cost Considerations

**LLM API Calls:**
- 8 assets × 12 checks/hour = 96 calls/hour
- ~2,300 calls/day
- Using Groq (free tier or cheap)

**Solution:** Reduce check frequency or number of assets if needed.

## Next Steps

1. **Run hybrid backtest** - See if LLM improves performance
2. **Test on demo** - Deploy to Bybit demo account
3. **Monitor LLM decisions** - See when it agrees vs overrides
4. **Tune confidence** - Maybe require 70% instead of 60%
5. **Compare strategies** - Hybrid vs Pure Technical vs Sentiment

The hybrid system should be **smarter and more conservative** than pure technical signals!
