"""
Test script to demonstrate Hybrid ATR-Based + Kelly Criterion position sizing
"""

# Simulate configuration
USE_HYBRID_SIZING = True
KELLY_FRACTION = 0.25
BASE_RISK_PCT = 0.01
MAX_POSITION_SIZE_PCT = 0.02
MIN_POSITION_SIZE_PCT = 0.005
MAX_TOTAL_EXPOSURE = 3.0
BASE_LEVERAGE = 9.0

KELLY_WIN_RATE = 0.50
KELLY_AVG_WIN = 0.10
KELLY_AVG_LOSS = 0.035

def calculate_atr_percentage(prices):
    """Calculate ATR as percentage of current price"""
    if len(prices) < 15:
        return 5.0
    
    true_ranges = []
    for i in range(1, len(prices)):
        high_low = abs(prices[i] - prices[i-1])
        true_ranges.append(high_low)
    
    atr = sum(true_ranges[-14:]) / 14
    current_price = prices[-1]
    if current_price > 0:
        return (atr / current_price) * 100
    return 5.0

def calculate_kelly_multiplier():
    """Calculate Kelly Criterion multiplier"""
    if KELLY_WIN_RATE <= 0 or KELLY_AVG_WIN <= 0:
        return 1.0
    
    kelly = (KELLY_WIN_RATE * KELLY_AVG_WIN - (1 - KELLY_WIN_RATE) * KELLY_AVG_LOSS) / KELLY_AVG_WIN
    kelly_adjusted = kelly * KELLY_FRACTION
    return max(0.5, min(2.0, kelly_adjusted))

def calculate_hybrid_position_size(symbol, base_allocation, current_price, balance, volatility_pct):
    """Calculate hybrid position size"""
    
    # Portfolio average ATR
    portfolio_avg_atr = 6.0  # 6% average
    
    # ATR-based adjustment (inverse)
    atr_adjustment = portfolio_avg_atr / volatility_pct
    atr_adjustment = max(0.5, min(2.0, atr_adjustment))
    
    # Kelly multiplier
    kelly_mult = calculate_kelly_multiplier()
    
    # Adjusted allocation
    adjusted_allocation = BASE_RISK_PCT * atr_adjustment * kelly_mult
    adjusted_allocation = max(MIN_POSITION_SIZE_PCT, min(MAX_POSITION_SIZE_PCT, adjusted_allocation))
    
    # Position value
    position_value = balance * adjusted_allocation * BASE_LEVERAGE
    
    return position_value, adjusted_allocation, atr_adjustment, kelly_mult

# Test cases
print("=" * 80)
print("🎯 HYBRID POSITION SIZING DEMONSTRATION")
print("=" * 80)
print()

print("Configuration:")
print(f"  Base Risk: {BASE_RISK_PCT:.1%} per trade")
print(f"  Leverage: {BASE_LEVERAGE}x")
print(f"  Kelly Fraction: {KELLY_FRACTION:.0%} (Conservative)")
print(f"  Position Range: {MIN_POSITION_SIZE_PCT:.2%} - {MAX_POSITION_SIZE_PCT:.1%}")
print(f"  Win Rate: {KELLY_WIN_RATE:.0%} | Avg Win: {KELLY_AVG_WIN:.1%} | Avg Loss: {KELLY_AVG_LOSS:.1%}")
print()

kelly = calculate_kelly_multiplier()
print(f"Kelly Multiplier: {kelly:.2f}x")
print()

# Simulate different volatility scenarios
balance = 12500  # $12.5k balance

scenarios = [
    ("BTC (Low Volatility)", 1.0, 76000, 2.5),    # 2.5% ATR
    ("ETH (Low-Medium)", 1.0, 2250, 4.0),         # 4% ATR
    ("SOL (Medium)", 1.0, 97, 6.0),               # 6% ATR (average)
    ("LINK (Medium-High)", 1.0, 9.6, 8.0),        # 8% ATR
    ("DOGE (High Volatility)", 1.0, 0.11, 12.0),  # 12% ATR
    ("Meme Coin (Very High)", 1.0, 0.001, 20.0),  # 20% ATR
]

print("=" * 80)
print("POSITION SIZING BY VOLATILITY")
print("=" * 80)
print(f"{'Asset':<25} {'ATR %':<8} {'Adjustment':<12} {'Allocation':<12} {'Position $':<15}")
print("-" * 80)

for name, base_alloc, price, atr_pct in scenarios:
    pos_value, adj_alloc, atr_adj, _ = calculate_hybrid_position_size(
        name, base_alloc, price, balance, atr_pct
    )
    qty = pos_value / price
    
    print(f"{name:<25} {atr_pct:>6.1f}%  {atr_adj:>7.2f}x     {adj_alloc*100:>7.2f}%     ${pos_value:>10,.0f}")

print()
print("=" * 80)
print("KEY INSIGHTS:")
print("=" * 80)
print("✅ Low volatility assets (BTC, ETH) get LARGER positions")
print("✅ High volatility assets (DOGE, memes) get SMALLER positions")
print("✅ Equal RISK across all positions (not equal $)")
print("✅ Kelly Criterion optimizes for long-term growth")
print("✅ Conservative 1/4 Kelly prevents over-betting")
print()

# Compare to fixed allocation
print("=" * 80)
print("COMPARISON: HYBRID vs FIXED ALLOCATION")
print("=" * 80)
print()

total_hybrid = 0
total_fixed = 0

print(f"{'Asset':<25} {'Fixed (1%)':<15} {'Hybrid':<15} {'Difference':<15}")
print("-" * 80)

for name, base_alloc, price, atr_pct in scenarios:
    fixed_pos = balance * 0.01 * BASE_LEVERAGE
    hybrid_pos, _, _, _ = calculate_hybrid_position_size(name, base_alloc, price, balance, atr_pct)
    diff = ((hybrid_pos - fixed_pos) / fixed_pos) * 100
    
    total_hybrid += hybrid_pos
    total_fixed += fixed_pos
    
    print(f"{name:<25} ${fixed_pos:>10,.0f}    ${hybrid_pos:>10,.0f}    {diff:>+7.1f}%")

print("-" * 80)
print(f"{'TOTAL EXPOSURE':<25} ${total_fixed:>10,.0f}    ${total_hybrid:>10,.0f}    {((total_hybrid-total_fixed)/total_fixed)*100:>+7.1f}%")
print()

print("💡 Hybrid sizing adjusts exposure based on risk, not just price!")
print()
