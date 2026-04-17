"""
Analyze potential trade frequency with more assets
"""

import json

# Load current results
with open('hyperopt_optuna_inverted_results.json', 'r') as f:
    results = json.load(f)

backtest_return = results['best_return']
backtest_days = 180
signal_threshold = results['best_params']['signal_threshold']

# Current setup
current_assets = 5  # BTC, ETH, SOL, AVAX, BNB
estimated_trades_per_day = 0.18  # From backtest analysis
estimated_total_trades = 32

print("=" * 80)
print("TRADE FREQUENCY SCALING ANALYSIS")
print("=" * 80)
print()

print("📊 Current Configuration:")
print(f"  Assets: {current_assets}")
print(f"  Trades per day: {estimated_trades_per_day:.2f}")
print(f"  Trades per month: {estimated_trades_per_day * 30:.0f}")
print(f"  Total trades (6 months): {estimated_total_trades}")
print()

# Potential additional assets
additional_crypto_assets = [
    # Large caps
    "XRP", "ADA", "DOGE",  # Already in live_trading.py!
    
    # Additional large caps
    "DOT", "MATIC", "LINK", "UNI", "ATOM",
    
    # Mid caps
    "APT", "ARB", "OP", "SUI", "INJ",
    "FTM", "NEAR", "IMX", "TIA", "SEI",
    
    # DeFi
    "AAVE", "MKR", "CRV", "LDO", "SNX",
    
    # Layer 2s
    "STRK", "MANTA", "BLAST",
    
    # Meme/Community
    "SHIB", "PEPE", "WIF", "BONK"
]

print("🎯 Potential Asset Pool:")
print(f"  Current in backtest: {current_assets} (BTC, ETH, SOL, AVAX, BNB)")
print(f"  Already in live bot: 8 (+ XRP, ADA, DOGE)")
print(f"  Additional available: {len(additional_crypto_assets)}")
print(f"  Total potential: {len(additional_crypto_assets) + 8}")
print()

# Calculate scaling scenarios
scenarios = [
    ("Current Backtest", 5, estimated_trades_per_day),
    ("Current Live Bot", 8, estimated_trades_per_day * 8/5),
    ("Top 10 Assets", 10, estimated_trades_per_day * 10/5),
    ("Top 15 Assets", 15, estimated_trades_per_day * 15/5),
    ("Top 20 Assets", 20, estimated_trades_per_day * 20/5),
    ("Top 30 Assets", 30, estimated_trades_per_day * 30/5),
]

print("=" * 80)
print("TRADE FREQUENCY PROJECTIONS")
print("=" * 80)
print()

print(f"{'Scenario':<25} {'Assets':<10} {'Trades/Day':<15} {'Trades/Week':<15} {'Trades/Month'}")
print("-" * 80)

for scenario_name, num_assets, trades_per_day in scenarios:
    trades_per_week = trades_per_day * 7
    trades_per_month = trades_per_day * 30
    print(f"{scenario_name:<25} {num_assets:<10} {trades_per_day:<15.2f} {trades_per_week:<15.1f} {trades_per_month:.0f}")

print()
print("=" * 80)
print("CONSIDERATIONS FOR ADDING MORE ASSETS")
print("=" * 80)
print()

print("✅ BENEFITS:")
print("  • More trading opportunities (scales linearly with assets)")
print("  • Better diversification across market sectors")
print("  • Reduced correlation risk")
print("  • More chances to catch strong signals")
print()

print("⚠️  CHALLENGES:")
print("  • Signal threshold (0.551) is VERY high - most assets won't qualify")
print("  • LLM API costs increase linearly with assets")
print("  • More API calls = higher Bybit & Groq usage")
print("  • Need to manage position limits (capital allocation)")
print("  • Lower liquidity assets = higher slippage")
print()

print("💡 RECOMMENDATIONS:")
print()

print("1. IMMEDIATE (Quick Win):")
print("   Already done! Live bot has 8 assets vs backtest's 5")
print("   Expected: ~0.29 trades/day (2 trades/week, 9 trades/month)")
print()

print("2. CONSERVATIVE EXPANSION (10-15 assets):")
print("   Add: DOT, MATIC, LINK, ATOM, UNI")
print("   Expected: ~0.36-0.54 trades/day (2-4 trades/week, 11-16 trades/month)")
print("   Risk: Low - all large cap, liquid assets")
print()

print("3. MODERATE EXPANSION (20 assets):")
print("   Add above + Layer 2s + DeFi blue chips")
print("   Expected: ~0.72 trades/day (5 trades/week, 22 trades/month)")
print("   Risk: Medium - some lower liquidity")
print()

print("4. AGGRESSIVE EXPANSION (30+ assets):")
print("   Add everything including memes and small caps")
print("   Expected: ~1.08+ trades/day (7-8 trades/week, 32+ trades/month)")
print("   Risk: High - slippage, correlation, management overhead")
print()

print("=" * 80)
print("OPTIMAL STRATEGY")
print("=" * 80)
print()

print("🎯 Recommended: 10-15 ASSETS")
print()
print("   Suggested additions to current 8:")
print("   • Polkadot (DOT) - Large cap, L0 platform")
print("   • Polygon (MATIC) - Ethereum scaling")
print("   • Chainlink (LINK) - Oracle leader")
print("   • Cosmos (ATOM) - Interoperability")
print("   • Uniswap (UNI) - DeFi leader")
print("   • Optimism (OP) - L2 leader")
print("   • Arbitrum (ARB) - L2 leader")
print()

print("   Expected Results:")
print(f"   • ~0.36-0.54 trades per day")
print(f"   • ~2-4 trades per week")
print(f"   • ~11-16 trades per month")
print(f"   • Maintain high signal quality (threshold 0.551)")
print(f"   • Diversified across sectors")
print()

print("   Portfolio Allocation Suggestion:")
print("   • BTC: 20%")
print("   • ETH: 15%")
print("   • Large caps (SOL, AVAX, BNB, XRP): 40% (10% each)")
print("   • Mid caps (ADA, DOGE, DOT, MATIC, LINK): 20% (4% each)")
print("   • Optional (ATOM, UNI): 5% (2.5% each)")
print()

# Calculate API costs
print("=" * 80)
print("API COST ESTIMATION")
print("=" * 80)
print()

groq_cost_per_call = 0.0001  # Rough estimate for Llama 3.3 70B
checks_per_day = 288  # Every 5 minutes

for scenario_name, num_assets, trades_per_day in scenarios:
    llm_calls_per_day = checks_per_day * num_assets
    daily_cost = llm_calls_per_day * groq_cost_per_call
    monthly_cost = daily_cost * 30
    
    print(f"{scenario_name}:")
    print(f"  LLM calls/day: {llm_calls_per_day}")
    print(f"  Est. cost/day: ${daily_cost:.2f}")
    print(f"  Est. cost/month: ${monthly_cost:.2f}")
    print()

print("=" * 80)
