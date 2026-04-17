"""
Generate 100 crypto assets configuration for maximum trade frequency
"""

# Top 100 crypto assets by market cap and liquidity on Bybit
CRYPTO_100 = [
    # Top 10 - Large Caps (55% allocation)
    ("Bitcoin", "BTCUSDT", 0.15),
    ("Ethereum", "ETHUSDT", 0.12),
    ("Solana", "SOLUSDT", 0.08),
    ("BNB", "BNBUSDT", 0.06),
    ("Ripple", "XRPUSDT", 0.05),
    ("Cardano", "ADAUSDT", 0.03),
    ("Avalanche", "AVAXUSDT", 0.03),
    ("Dogecoin", "DOGEUSDT", 0.02),
    ("Polkadot", "DOTUSDT", 0.005),
    ("Polygon", "MATICUSDT", 0.005),
    
    # 11-30 - Mid Caps (25% allocation)
    ("Chainlink", "LINKUSDT", 0.015),
    ("Toncoin", "TONUSDT", 0.015),
    ("Uniswap", "UNIUSDT", 0.012),
    ("Cosmos", "ATOMUSDT", 0.012),
    ("Filecoin", "FILUSDT", 0.01),
    ("Arbitrum", "ARBUSDT", 0.01),
    ("Optimism", "OPUSDT", 0.01),
    ("Near", "NEARUSDT", 0.01),
    ("Aptos", "APTUSDT", 0.01),
    ("Sui", "SUIUSDT", 0.01),
    ("ImmutableX", "IMXUSDT", 0.008),
    ("Injective", "INJUSDT", 0.008),
    ("Fantom", "FTMUSDT", 0.008),
    ("Stacks", "STXUSDT", 0.008),
    ("Aave", "AAVEUSDT", 0.007),
    ("Celestia", "TIAUSDT", 0.007),
    ("Maker", "MKRUSDT", 0.006),
    ("Render", "RENDERUSDT", 0.006),
    ("VeChain", "VETUSDT", 0.006),
    ("Algorand", "ALGOUSDT", 0.005),
    
    # 31-60 - Small/Mid Caps (12% allocation)
    ("Sei", "SEIUSDT", 0.004),
    ("Theta", "THETAUSDT", 0.004),
    ("Flow", "FLOWUSDT", 0.004),
    ("Axie", "AXSUSDT", 0.004),
    ("Sandbox", "SANDUSDT", 0.004),
    ("Decentraland", "MANAUSDT", 0.004),
    ("Curve", "CRVUSDT", 0.004),
    ("Graph", "GRTUSDT", 0.004),
    ("Flare", "FLRUSDT", 0.003),
    ("Kava", "KAVAUSDT", 0.003),
    ("1inch", "1INCHUSDT", 0.003),
    ("Synthetix", "SNXUSDT", 0.003),
    ("Gala", "GALAUSDT", 0.003),
    ("Enjin", "ENJUSDT", 0.003),
    ("Chiliz", "CHZUSDT", 0.003),
    ("Zilliqa", "ZILUSDT", 0.003),
    ("Harmony", "ONEUSDT", 0.003),
    ("Ravencoin", "RVNUSDT", 0.003),
    ("Qtum", "QTUMUSDT", 0.003),
    ("Loopring", "LRCUSDT", 0.003),
    ("Sushi", "SUSHIUSDT", 0.003),
    ("Compound", "COMPUSDT", 0.003),
    ("Yearn", "YFIUSDT", 0.002),
    ("Basic Attention", "BATUSDT", 0.002),
    ("Zcash", "ZECUSDT", 0.002),
    ("Dash", "DASHUSDT", 0.002),
    ("Decred", "DCRUSDT", 0.002),
    ("Horizen", "ZENUSDT", 0.002),
    ("Waves", "WAVESUSDT", 0.002),
    ("Ontology", "ONTUSDT", 0.002),
    
    # 61-80 - Layer 2s & New Projects (5% allocation)
    ("Manta", "MANTAUSDT", 0.003),
    ("Starknet", "STRKUSDT", 0.003),
    ("Blur", "BLURUSDT", 0.003),
    ("dYdX", "DYDXUSDT", 0.003),
    ("Pendle", "PENDLEUSDT", 0.002),
    ("JTO", "JTOUSDT", 0.002),
    ("WLD", "WLDUSDT", 0.002),
    ("Pyth", "PYTHUSDT", 0.002),
    ("Jito", "JITOUSDT", 0.002),
    ("Jupiter", "JUPUSDT", 0.002),
    ("Bonk", "BONKUSDT", 0.002),
    ("Pepe", "PEPEUSDT", 0.002),
    ("Shiba", "SHIBUSDT", 0.002),
    ("Floki", "FLOKIUSDT", 0.002),
    ("WIF", "WIFUSDT", 0.002),
    ("Meme", "MEMEUSDT", 0.001),
    ("Brett", "BRETTUSDT", 0.001),
    ("Popcat", "POPCATUSDT", 0.001),
    ("Dogs", "DOGSUSDT", 0.001),
    ("Neiro", "NEIROUSDT", 0.001),
    
    # 81-100 - Micro caps & Altcoins (3% allocation)
    ("Lido", "LDOUSDT", 0.002),
    ("Rocket Pool", "RPLUSDT", 0.002),
    ("Frax", "FXSUSDT", 0.002),
    ("Spell", "SPELLUSDT", 0.001),
    ("Magic", "MAGICUSDT", 0.001),
    ("GMX", "GMXUSDT", 0.001),
    ("Gains", "GNSUSDT", 0.001),
    ("Radiant", "RDNTUSDT", 0.001),
    ("Stargate", "STGUSDT", 0.001),
    ("Perpetual", "PERPUSDT", 0.001),
    ("Convex", "CVXUSDT", 0.001),
    ("Balancer", "BALUSDT", 0.001),
    ("Bancor", "BNTUSDT", 0.001),
    ("Kyber", "KNCUSDT", 0.001),
    ("0x", "ZRXUSDT", 0.001),
    ("Ren", "RENUSDT", 0.001),
    ("Ocean", "OCEANUSDT", 0.001),
    ("Fetch", "FETUSDT", 0.001),
    ("Agix", "AGIXUSDT", 0.001),
    ("Rose", "ROSEUSDT", 0.001),
]

print("=" * 80)
print("100 CRYPTO ASSETS CONFIGURATION")
print("=" * 80)
print()

# Verify allocations sum to ~1.0
total_allocation = sum(alloc for _, _, alloc in CRYPTO_100)
print(f"📊 Portfolio Structure:")
print(f"  Total Assets: {len(CRYPTO_100)}")
print(f"  Total Allocation: {total_allocation:.3f} (should be ~1.0)")
print()

# Group by size
large_caps = [a for a in CRYPTO_100 if a[2] >= 0.02]
mid_caps = [a for a in CRYPTO_100 if 0.005 <= a[2] < 0.02]
small_caps = [a for a in CRYPTO_100 if a[2] < 0.005]

print(f"  Large Caps (≥2%): {len(large_caps)} assets, {sum(a[2] for a in large_caps):.1%} allocation")
print(f"  Mid Caps (0.5-2%): {len(mid_caps)} assets, {sum(a[2] for a in mid_caps):.1%} allocation")
print(f"  Small Caps (<0.5%): {len(small_caps)} assets, {sum(a[2] for a in small_caps):.1%} allocation")
print()

# Trade frequency estimation
base_trades_per_day = 0.18  # From 5 assets
assets_factor = len(CRYPTO_100) / 5
estimated_trades_per_day = base_trades_per_day * assets_factor

print("=" * 80)
print("TRADE FREQUENCY PROJECTION")
print("=" * 80)
print()
print(f"📈 With 100 assets:")
print(f"  Trades per day: {estimated_trades_per_day:.2f}")
print(f"  Trades per week: {estimated_trades_per_day * 7:.0f}")
print(f"  Trades per month: {estimated_trades_per_day * 30:.0f}")
print(f"  Trades per year: {estimated_trades_per_day * 365:.0f}")
print()

# API costs
groq_cost_per_call = 0.0001
checks_per_day = 288  # Every 5 minutes
llm_calls_per_day = checks_per_day * len(CRYPTO_100)
daily_cost = llm_calls_per_day * groq_cost_per_call
monthly_cost = daily_cost * 30
yearly_cost = daily_cost * 365

print("=" * 80)
print("OPERATIONAL COSTS")
print("=" * 80)
print()
print(f"💰 LLM API Costs (Groq):")
print(f"  Calls per day: {llm_calls_per_day:,}")
print(f"  Cost per day: ${daily_cost:.2f}")
print(f"  Cost per month: ${monthly_cost:.2f}")
print(f"  Cost per year: ${yearly_cost:.2f}")
print()

# Management complexity
print("=" * 80)
print("OPERATIONAL CONSIDERATIONS")
print("=" * 80)
print()

print("✅ BENEFITS:")
print(f"  • {estimated_trades_per_day:.0f}x more trading opportunities than 5 assets")
print(f"  • Maximum diversification across crypto market")
print(f"  • ~{estimated_trades_per_day * 30:.0f} trades per month (vs 5 with 5 assets)")
print(f"  • Exposure to all market sectors (L1, L2, DeFi, memes, etc.)")
print(f"  • More chances to catch strong signals (≥0.551)")
print()

print("⚠️  CHALLENGES:")
print(f"  • High API costs: ${monthly_cost:.2f}/month (vs $4.32 for 5 assets)")
print(f"  • {llm_calls_per_day:,} LLM calls per day")
print(f"  • Need {llm_calls_per_day * 0.5 / 3600:.1f} hours of LLM processing per day")
print(f"  • Many micro-cap assets = higher slippage")
print(f"  • Lower liquidity on smaller pairs")
print(f"  • Complex position management")
print(f"  • Higher correlation during market crashes")
print()

print("🎯 REALITY CHECK:")
print(f"  • Signal threshold (0.551) is VERY high")
print(f"  • Current market: 0% of assets show signals ≥0.551")
print(f"  • Even with 100 assets, if market is weak = 0 trades")
print(f"  • Quality > Quantity - threshold prevents bad trades")
print()

print("=" * 80)
print("PYTHON CODE FOR live_trading.py")
print("=" * 80)
print()
print("Replace the SYMBOLS array around line 98 with:")
print()
print("```python")
print("SYMBOLS = [")

for name, symbol, allocation in CRYPTO_100:
    print(f'    {{"name": "{name}", "symbol": "{symbol}", "allocation": {allocation}}},')

print("]")
print("```")
print()

# Save to file
output_file = "100_assets_config.py"
with open(output_file, 'w') as f:
    f.write("# 100 Crypto Assets Configuration\n")
    f.write("# Generated for maximum trade frequency\n\n")
    f.write("SYMBOLS = [\n")
    for name, symbol, allocation in CRYPTO_100:
        f.write(f'    {{"name": "{name}", "symbol": "{symbol}", "allocation": {allocation}}},\n')
    f.write("]\n")

print(f"💾 Configuration saved to: {output_file}")
print()

print("=" * 80)
print("RECOMMENDATION")
print("=" * 80)
print()
print("🤔 Is 100 assets worth it?")
print()
print("PROS:")
print(f"  ✅ {estimated_trades_per_day * 30:.0f} trades/month (vs 5 with 5 assets)")
print(f"  ✅ Maximum market coverage")
print(f"  ✅ Only ${monthly_cost:.2f}/month in LLM costs")
print()
print("CONS:")
print(f"  ❌ Current market = 0 signals above 0.551 anyway")
print(f"  ❌ Diminishing returns (most trades from top 20 assets)")
print(f"  ❌ Complexity increases errors/bugs")
print(f"  ❌ Many assets too illiquid for 10x leverage")
print()
print("💡 BETTER APPROACH:")
print("   Start with 15-20 high-quality liquid assets")
print("   Monitor which ones generate signals")
print("   Expand only if seeing good signals")
print("   Quality (0.551 threshold) > Quantity")
print()
print("=" * 80)
