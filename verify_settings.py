#!/usr/bin/env python3
"""
Verify Conservative Settings (Feb 7, 2026)
After -12% losses, implementing safer parameters
"""

import re

def extract_setting(content, pattern):
    """Extract a setting value from the source code"""
    match = re.search(pattern, content)
    if match:
        return match.group(1)
    return None

# Read the live_trading.py file
with open('src/live_trading.py', 'r') as f:
    content = f.read()

# Extract settings
stop_loss = extract_setting(content, r'STOP_LOSS_PCT = ([\d.]+)')
take_profit = extract_setting(content, r'TAKE_PROFIT_PCT = ([\d.]+)')
threshold = extract_setting(content, r'BASE_SIGNAL_THRESHOLD = ([\d.]+)')
base_risk = extract_setting(content, r'BASE_RISK_PCT = ([\d.]+)')
max_position = extract_setting(content, r'MAX_POSITION_SIZE_PCT = ([\d.]+)')
max_exposure = extract_setting(content, r'MAX_TOTAL_EXPOSURE = ([\d.]+)')

print("=" * 60)
print("  CONSERVATIVE SETTINGS VERIFICATION")
print("  (Feb 7, 2026 - After -12% Loss)")
print("=" * 60)
print()
print("📊 CORE PARAMETERS:")
print(f"  Stop Loss:     {float(stop_loss)*100:.1f}% (target: 2.5%)")
print(f"  Take Profit:   {float(take_profit)*100:.1f}% (target: 3.5%)")
print(f"  Threshold:     {float(threshold):.3f} (target: 0.65)")
print()
print("💰 POSITION SIZING:")
print(f"  Base Risk:     {float(base_risk)*100:.1f}% per trade (target: 1%)")
print(f"  Max Position:  {float(max_position)*100:.1f}% (target: 2%)")
print(f"  Max Exposure:  {float(max_exposure):.1f}x (target: 3x)")
print()

# Verify all settings match targets
checks = {
    "Stop Loss": (float(stop_loss), 0.025),
    "Take Profit": (float(take_profit), 0.035),
    "Threshold": (float(threshold), 0.65),
    "Base Risk": (float(base_risk), 0.01),
    "Max Position": (float(max_position), 0.02),
    "Max Exposure": (float(max_exposure), 3.0)
}

all_correct = True
print("✅ VERIFICATION:")
for name, (actual, target) in checks.items():
    if abs(actual - target) < 0.001:
        print(f"  ✅ {name}: {actual} = {target} ✓")
    else:
        print(f"  ❌ {name}: {actual} ≠ {target} ✗")
        all_correct = False

print()
if all_correct:
    print("🎯 ALL SETTINGS CORRECT - READY FOR PAPER TRADING")
    print()
    print("Expected Improvements:")
    print("  • Win rate: 31-39% → 45-50%")
    print("  • SL hit rate: 60-70% → <50%")
    print("  • Trade frequency: 50/day → 15/day")
    print("  • Risk:Reward: 3.67:1 → 1.4:1")
    print("  • Result: Breakeven to slightly profitable")
else:
    print("⚠️  SOME SETTINGS INCORRECT - REVIEW NEEDED")

print()
print("📋 NEXT STEPS:")
print("  1. Review deep_diagnosis_report.md for full analysis")
print("  2. Paper trade for 48 hours")
print("  3. Verify win rate >45% and SL hits <50%")
print("  4. If successful, test with $1,000 per bot")
print("=" * 60)
