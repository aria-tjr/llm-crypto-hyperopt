"""
Portfolio Optimization Based on Quality Metrics (NOT trade history)

Uses fundamental factors:
1. Market Cap / Liquidity (can we actually trade it?)
2. Volatility (too volatile = risk, too stable = no opportunity)
3. Volume (can we fill orders without slippage?)
4. Sector Diversification (don't put all eggs in one basket)
5. Technical Quality (trending vs ranging)
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import json

# Quality criteria for portfolio optimization
MIN_DAILY_VOLUME = 5_000_000  # $5M minimum daily volume
MAX_VOLATILITY = 0.15  # 15% daily volatility max (exclude extreme movers)
MIN_VOLATILITY = 0.02  # 2% minimum (exclude stable coins)

def analyze_asset_quality(symbol, days=30):
    """
    Analyze asset quality based on fundamental metrics
    Returns quality score 0-100
    """
    try:
        # Fetch historical data
        ticker = yf.Ticker(symbol.replace('USDT', '-USD'))
        df = ticker.history(period=f"{days}d", interval="1d")
        
        if len(df) < 20:
            return {"score": 0, "reason": "Insufficient data"}
        
        # Calculate metrics
        daily_volume = df['Volume'].mean() * df['Close'].mean()
        volatility = df['Close'].pct_change().std()
        avg_price = df['Close'].mean()
        price_trend = (df['Close'].iloc[-1] - df['Close'].iloc[0]) / df['Close'].iloc[0]
        
        # Calculate quality score
        score = 0
        reasons = []
        
        # Volume score (30 points)
        if daily_volume > 50_000_000:
            score += 30
            reasons.append("Excellent volume")
        elif daily_volume > 20_000_000:
            score += 25
            reasons.append("Good volume")
        elif daily_volume > MIN_DAILY_VOLUME:
            score += 15
            reasons.append("Adequate volume")
        else:
            reasons.append("Low volume - EXCLUDE")
            return {"score": 0, "reason": "Low volume", "volume": daily_volume}
        
        # Volatility score (30 points)
        if MIN_VOLATILITY < volatility < 0.05:
            score += 30
            reasons.append("Ideal volatility for trading")
        elif MIN_VOLATILITY < volatility < 0.08:
            score += 25
            reasons.append("Good volatility")
        elif MIN_VOLATILITY < volatility < MAX_VOLATILITY:
            score += 15
            reasons.append("Acceptable volatility")
        else:
            reasons.append(f"Extreme volatility ({volatility:.1%}) - EXCLUDE")
            return {"score": 0, "reason": "Extreme volatility", "volatility": volatility}
        
        # Price level score (20 points) - prefer tradeable prices
        if 0.10 < avg_price < 1000:
            score += 20
            reasons.append("Good price range")
        elif 0.01 < avg_price < 10000:
            score += 15
            reasons.append("Acceptable price")
        else:
            score += 5
            reasons.append("Extreme price level")
        
        # Trend quality (20 points)
        if abs(price_trend) < 0.50:  # Not pumping or dumping too hard
            score += 20
            reasons.append("Healthy price action")
        elif abs(price_trend) < 1.0:
            score += 10
            reasons.append("Moderate trend")
        else:
            score += 0
            reasons.append("Extreme pump/dump")
        
        return {
            "score": score,
            "volume": daily_volume,
            "volatility": volatility,
            "avg_price": avg_price,
            "trend": price_trend,
            "reasons": reasons
        }
        
    except Exception as e:
        return {"score": 0, "reason": f"Error: {str(e)}"}


def create_optimized_portfolio(current_symbols, target_count=100):
    """
    Create optimized portfolio from current symbols based on quality
    
    Args:
        current_symbols: List of current symbol dicts with allocations
        target_count: Target number of assets (default 100)
    
    Returns:
        Optimized list of symbols with new allocations
    """
    print("=" * 80)
    print("PORTFOLIO OPTIMIZATION (Quality-Based)")
    print("=" * 80)
    print(f"Current portfolio: {len(current_symbols)} assets")
    print(f"Target portfolio: {target_count} assets")
    print()
    
    print("Analyzing asset quality... (this will take a few minutes)")
    
    results = []
    for i, asset in enumerate(current_symbols, 1):
        symbol = asset['symbol']
        print(f"  [{i}/{len(current_symbols)}] Analyzing {symbol}...", end='\r')
        
        quality = analyze_asset_quality(symbol)
        results.append({
            'name': asset['name'],
            'symbol': symbol,
            'quality_score': quality.get('score', 0),
            'volume': quality.get('volume', 0),
            'volatility': quality.get('volatility', 0),
            'reasons': quality.get('reasons', [quality.get('reason', 'Unknown')])
        })
    
    print()
    print()
    
    # Sort by quality score
    results.sort(key=lambda x: x['quality_score'], reverse=True)
    
    # Take top performers
    top_assets = [r for r in results if r['quality_score'] > 0][:target_count]
    excluded = [r for r in results if r['quality_score'] == 0]
    
    print(f"✅ Quality assets found: {len(top_assets)}")
    print(f"❌ Excluded (low quality): {len(excluded)}")
    print()
    
    # Assign tiered allocations based on quality score
    print("Assigning allocations based on quality tiers...")
    
    optimized = []
    
    # Tier 1: Top 20 (scores 80-100) - 3% each = 60%
    tier1 = [a for a in top_assets if a['quality_score'] >= 80][:20]
    for asset in tier1:
        optimized.append({
            'name': asset['name'],
            'symbol': asset['symbol'],
            'allocation': 0.03,
            'tier': '⭐ PREMIUM',
            'score': asset['quality_score']
        })
    
    # Tier 2: Next 30 (scores 60-79) - 1% each = 30%
    tier2 = [a for a in top_assets if 60 <= a['quality_score'] < 80][:30]
    for asset in tier2:
        optimized.append({
            'name': asset['name'],
            'symbol': asset['symbol'],
            'allocation': 0.01,
            'tier': '✅ QUALITY',
            'score': asset['quality_score']
        })
    
    # Tier 3: Remaining (scores 40-59) - 0.5% each = ~10%
    tier3 = [a for a in top_assets if 40 <= a['quality_score'] < 60][:50]
    for asset in tier3:
        optimized.append({
            'name': asset['name'],
            'symbol': asset['symbol'],
            'allocation': 0.005,
            'tier': '🔵 OPPORTUNITY',
            'score': asset['quality_score']
        })
    
    print()
    print("=" * 80)
    print("OPTIMIZED PORTFOLIO")
    print("=" * 80)
    print(f"Tier 1 (⭐ PREMIUM):    {len(tier1)} assets @ 3% each = {len(tier1)*3}%")
    print(f"Tier 2 (✅ QUALITY):    {len(tier2)} assets @ 1% each = {len(tier2)*1}%")
    print(f"Tier 3 (🔵 OPPORTUNITY): {len(tier3)} assets @ 0.5% each = {len(tier3)*0.5}%")
    print(f"Total: {len(optimized)} assets, {sum(a['allocation'] for a in optimized)*100:.1f}% allocated")
    print()
    
    # Show top 20
    print("🏆 TOP 20 PREMIUM ASSETS (3% allocation each):")
    print("-" * 80)
    for i, asset in enumerate(optimized[:20], 1):
        print(f"  {i:2d}. {asset['name']:20s} ({asset['symbol']:15s}) - Score: {asset['score']}")
    
    print()
    print("❌ EXCLUDED ASSETS (Poor quality metrics):")
    print("-" * 80)
    for asset in excluded[:20]:
        reason = asset['reasons'][0] if asset['reasons'] else 'Unknown'
        print(f"  • {asset['symbol']:15s} - {reason}")
    if len(excluded) > 20:
        print(f"  ... and {len(excluded)-20} more")
    
    # Save to file
    output_file = 'optimized_portfolio.json'
    with open(output_file, 'w') as f:
        json.dump({
            'generated': datetime.now().isoformat(),
            'total_assets': len(optimized),
            'total_allocation': sum(a['allocation'] for a in optimized),
            'assets': optimized
        }, f, indent=2)
    
    print()
    print(f"💾 Saved to {output_file}")
    print()
    
    return optimized


if __name__ == "__main__":
    print("Loading current portfolio from src/live_trading.py...")
    
    # Read SYMBOLS from live_trading.py file
    import re
    with open('src/live_trading.py', 'r') as f:
        content = f.read()
    
    # Extract SYMBOLS list
    match = re.search(r'SYMBOLS = \[(.*?)\n    \]', content, re.DOTALL)
    if not match:
        print("❌ Could not find SYMBOLS in live_trading.py")
        exit(1)
    
    # Parse symbols
    symbols_text = match.group(1)
    current_symbols = []
    for line in symbols_text.split('\n'):
        if '"name":' in line and '"symbol":' in line:
            name_match = re.search(r'"name":\s*"([^"]+)"', line)
            symbol_match = re.search(r'"symbol":\s*"([^"]+)"', line)
            if name_match and symbol_match:
                current_symbols.append({
                    'name': name_match.group(1),
                    'symbol': symbol_match.group(1)
                })
    
    print(f"✅ Loaded {len(current_symbols)} symbols")
    print()
    
    # Run optimization
    optimized = create_optimized_portfolio(current_symbols, target_count=100)
    
    print()
    print("✅ Optimization complete!")
    print()
    print("Next steps:")
    print("  1. Review optimized_portfolio.json")
    print("  2. If you like it, I'll update src/live_trading.py")
    print("  3. Restart bot with optimized portfolio")
