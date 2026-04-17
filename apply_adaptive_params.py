"""
Apply optimized adaptive parameters from hyperopt to live_trading.py

This script reads the best parameters from hyperopt_adaptive_results.json
and updates the corresponding values in src/live_trading.py
"""

import json
import re


def apply_adaptive_params():
    """Apply hyperopt results to live trading configuration"""
    
    # Load hyperopt results
    try:
        with open('hyperopt_adaptive_results.json', 'r') as f:
            results = json.load(f)
    except FileNotFoundError:
        print("❌ Error: hyperopt_adaptive_results.json not found!")
        print("   Run: python hyperopt_optuna.py --trials 300")
        return False
    
    best_params = results['best_params']
    best_return = results['best_return']
    
    print("=" * 80)
    print("APPLYING ADAPTIVE HYPEROPT RESULTS TO LIVE TRADING")
    print("=" * 80)
    print()
    print(f"📊 Best Backtest Return: {best_return:+.2f}%")
    print()
    print("Parameters to apply:")
    print()
    print("📊 Base Parameters:")
    for key, value in best_params.items():
        if not key.startswith('volatility_') and not key.startswith('atr_'):
            print(f"  {key:25s}: {value}")
    print()
    print("🎯 Adaptive Parameters:")
    for key, value in best_params.items():
        if key.startswith('volatility_') or key.startswith('atr_'):
            print(f"  {key:25s}: {value}")
    print()
    
    # Read live_trading.py
    with open('src/live_trading.py', 'r') as f:
        content = f.read()
    
    # Backup original
    with open('src/live_trading.py.backup', 'w') as f:
        f.write(content)
    print("💾 Backup created: src/live_trading.py.backup")
    print()
    
    # Apply base parameters
    replacements = {
        r'MAX_LEVERAGE = [\d.]+': f'MAX_LEVERAGE = {best_params["leverage"]:.1f}',
        r'BASE_LEVERAGE = [\d.]+': f'BASE_LEVERAGE = {best_params["leverage"]:.1f}',
        r'BASE_SIGNAL_THRESHOLD = [\d.]+': f'BASE_SIGNAL_THRESHOLD = {best_params["base_signal_threshold"]:.3f}',
        r'STOP_LOSS_PCT = [\d.]+': f'STOP_LOSS_PCT = {best_params["base_stop_loss_pct"]:.4f}',
        r'TAKE_PROFIT_PCT = [\d.]+': f'TAKE_PROFIT_PCT = {best_params["base_take_profit_pct"]:.4f}',
        r'LOOKBACK_PERIODS = \d+': f'LOOKBACK_PERIODS = {best_params["lookback_periods"]}',
    }
    
    # Apply adaptive parameters
    adaptive_replacements = {
        r'ATR_LOOKBACK = \d+': f'ATR_LOOKBACK = {best_params["atr_lookback"]}',
        r'VOLATILITY_HIGH_MULTIPLIER = [\d.]+': f'VOLATILITY_HIGH_MULTIPLIER = {best_params["volatility_high_mult"]:.2f}',
        r'VOLATILITY_LOW_MULTIPLIER = [\d.]+': f'VOLATILITY_LOW_MULTIPLIER = {best_params["volatility_low_mult"]:.2f}',
    }
    
    print("🔄 Applying parameters...")
    changes_made = []
    
    for pattern, replacement in {**replacements, **adaptive_replacements}.items():
        old_match = re.search(pattern, content)
        if old_match:
            old_value = old_match.group(0)
            content = re.sub(pattern, replacement, content)
            changes_made.append(f"  ✓ {old_value} → {replacement}")
        else:
            print(f"  ⚠️  Pattern not found: {pattern}")
    
    # Add adaptive SL and TP parameters if not present
    atr_sl_mult = best_params.get('atr_stop_loss_mult', 0.5)
    vol_tp_mult = best_params.get('volatility_tp_mult', 2.0)
    
    # Check if adaptive parameters exist
    if 'ATR_STOP_LOSS_MULTIPLIER' not in content:
        # Add after VOLATILITY_LOW_MULTIPLIER
        insert_point = content.find('VOLATILITY_LOW_MULTIPLIER')
        if insert_point != -1:
            # Find end of line
            line_end = content.find('\n', insert_point)
            new_params = f'\n    ATR_STOP_LOSS_MULTIPLIER = {atr_sl_mult:.2f}  # ATR multiplier for adaptive stop loss\n    VOLATILITY_TP_MULTIPLIER = {vol_tp_mult:.2f}  # Volatility multiplier for adaptive take profit'
            content = content[:line_end] + new_params + content[line_end:]
            changes_made.append(f"  ✓ Added: ATR_STOP_LOSS_MULTIPLIER = {atr_sl_mult:.2f}")
            changes_made.append(f"  ✓ Added: VOLATILITY_TP_MULTIPLIER = {vol_tp_mult:.2f}")
    else:
        # Update existing
        content = re.sub(r'ATR_STOP_LOSS_MULTIPLIER = [\d.]+', 
                        f'ATR_STOP_LOSS_MULTIPLIER = {atr_sl_mult:.2f}', content)
        content = re.sub(r'VOLATILITY_TP_MULTIPLIER = [\d.]+', 
                        f'VOLATILITY_TP_MULTIPLIER = {vol_tp_mult:.2f}', content)
        changes_made.append(f"  ✓ Updated: ATR_STOP_LOSS_MULTIPLIER = {atr_sl_mult:.2f}")
        changes_made.append(f"  ✓ Updated: VOLATILITY_TP_MULTIPLIER = {vol_tp_mult:.2f}")
    
    # Write updated content
    with open('src/live_trading.py', 'w') as f:
        f.write(content)
    
    print()
    print("✅ Changes applied:")
    for change in changes_made:
        print(change)
    
    print()
    print("=" * 80)
    print("✅ PARAMETERS SUCCESSFULLY APPLIED!")
    print("=" * 80)
    print()
    print("📝 Next steps:")
    print("   1. Review changes: diff src/live_trading.py.backup src/live_trading.py")
    print("   2. Restart bot: pkill -f live_trading.py && nohup python src/live_trading.py > trading_bot.log 2>&1 &")
    print("   3. Monitor: tail -f trading_bot.log")
    print()
    print("💡 The bot will now use adaptive risk management:")
    print(f"   • Threshold adapts: {best_params['base_signal_threshold'] * best_params['volatility_low_mult']:.3f} (low vol) → {best_params['base_signal_threshold'] * best_params['volatility_high_mult']:.3f} (high vol)")
    print(f"   • Stop loss adapts based on ATR (multiplier: {atr_sl_mult:.2f})")
    print(f"   • Take profit adapts based on volatility (multiplier: {vol_tp_mult:.2f})")
    print()
    
    return True


if __name__ == "__main__":
    apply_adaptive_params()
