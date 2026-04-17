# 🎯 OPTIMIZED POSITION ALLOCATIONS
# Based on performance analysis from February 1, 2026
# Expected improvement: +0.908% weighted return

SYMBOLS = [
    # ⭐ HIGH PERFORMERS (8 positions @ 2.0% each) - Total: 16.0%
    {'symbol': 'ALGOUSDT', 'name': 'Algorand', 'allocation': 0.020},         # +8.66%
    {'symbol': 'MANAUSDT', 'name': 'Decentraland', 'allocation': 0.020},     # +8.60%
    {'symbol': 'RPLUSDT', 'name': 'Rocket Pool', 'allocation': 0.020},       # +8.18%
    {'symbol': 'LRCUSDT', 'name': 'Loopring', 'allocation': 0.020},          # +8.12%
    {'symbol': 'FLRUSDT', 'name': 'Fluence', 'allocation': 0.020},           # +8.09%
    {'symbol': 'STXUSDT', 'name': 'Stacks', 'allocation': 0.020},            # +8.05%
    {'symbol': 'SNXUSDT', 'name': 'Synthetix', 'allocation': 0.020},         # +7.46%
    {'symbol': 'ENJUSDT', 'name': 'Enjin', 'allocation': 0.020},             # +7.13%
    
    # ✅ GOOD PERFORMERS (12 positions @ 1.5% each) - Total: 18.0%
    {'symbol': 'SUSHIUSDT', 'name': 'Sushi', 'allocation': 0.015},           # +6.98%
    {'symbol': 'BATUSDT', 'name': 'BAT', 'allocation': 0.015},               # +6.56%
    {'symbol': 'SANDUSDT', 'name': 'Sandbox', 'allocation': 0.015},          # +6.08%
    {'symbol': 'XRPUSDT', 'name': 'XRP', 'allocation': 0.015},               # +5.95%
    {'symbol': 'ONEUSDT', 'name': 'Harmony', 'allocation': 0.015},           # +5.68%
    {'symbol': 'DYDXUSDT', 'name': 'dYdX', 'allocation': 0.015},             # +5.59%
    {'symbol': 'COMPUSDT', 'name': 'Compound', 'allocation': 0.015},         # +5.47%
    {'symbol': 'RVNUSDT', 'name': 'Ravencoin', 'allocation': 0.015},         # +5.14%
    {'symbol': 'OPUSDT', 'name': 'Optimism', 'allocation': 0.015},           # +5.14%
    {'symbol': 'FILUSDT', 'name': 'Filecoin', 'allocation': 0.015},          # +5.08%
    {'symbol': 'RENDERUSDT', 'name': 'Render', 'allocation': 0.015},         # +5.04%
    {'symbol': 'TONUSDT', 'name': 'Toncoin', 'allocation': 0.015},           # +4.90%
    
    # 🔵 AVERAGE PERFORMERS (12 positions @ 1.0% each) - Total: 12.0%
    {'symbol': 'WLDUSDT', 'name': 'Worldcoin', 'allocation': 0.010},         # +4.84%
    {'symbol': 'INJUSDT', 'name': 'Injective', 'allocation': 0.010},         # +4.62%
    {'symbol': 'ZENUSDT', 'name': 'Horizen', 'allocation': 0.010},           # +4.56%
    {'symbol': 'DOTUSDT', 'name': 'Polkadot', 'allocation': 0.010},          # +4.32%
    {'symbol': 'APTUSDT', 'name': 'Aptos', 'allocation': 0.010},             # +4.00%
    {'symbol': 'AVAXUSDT', 'name': 'Avalanche', 'allocation': 0.010},        # +3.67%
    {'symbol': 'DASHUSDT', 'name': 'Dash', 'allocation': 0.010},             # +3.58%
    {'symbol': 'IMXUSDT', 'name': 'Immutable X', 'allocation': 0.010},       # +3.57%
    {'symbol': 'UNIUSDT', 'name': 'Uniswap', 'allocation': 0.010},           # +3.51%
    {'symbol': 'LINKUSDT', 'name': 'Chainlink', 'allocation': 0.010},        # +3.39%
    {'symbol': 'SUIUSDT', 'name': 'Sui', 'allocation': 0.010},               # +3.38%
    {'symbol': 'ARBUSDT', 'name': 'Arbitrum', 'allocation': 0.010},          # +3.36%
    
    # ⚠️ UNDERPERFORMERS (9 positions @ 0.5% each) - Total: 4.5%
    # Reduced allocation to manage risk
    {'symbol': 'SOLUSDT', 'name': 'Solana', 'allocation': 0.005},            # +3.03%
    {'symbol': 'JUPUSDT', 'name': 'Jupiter', 'allocation': 0.005},           # +2.83%
    {'symbol': 'LDOUSDT', 'name': 'Lido DAO', 'allocation': 0.005},          # +2.65%
    {'symbol': 'NEARUSDT', 'name': 'NEAR Protocol', 'allocation': 0.005},    # +2.49%
    {'symbol': 'WAVESUSDT', 'name': 'Waves', 'allocation': 0.005},           # +1.80%
    {'symbol': 'ETHUSDT', 'name': 'Ethereum', 'allocation': 0.005},          # +1.38%
    {'symbol': 'BTCUSDT', 'name': 'Bitcoin', 'allocation': 0.005},           # +0.82%
    {'symbol': 'BNBUSDT', 'name': 'BNB', 'allocation': 0.005},               # +0.12%
    {'symbol': 'FLOWUSDT', 'name': 'Flow', 'allocation': 0.005},             # -0.61%
    
    # Assets not currently held (keep minimal allocation for opportunities)
    {'symbol': 'DOGEUSDT', 'name': 'Dogecoin', 'allocation': 0.005},
    {'symbol': 'ADAUSDT', 'name': 'Cardano', 'allocation': 0.005},
    {'symbol': 'CRVUSDT', 'name': 'Curve', 'allocation': 0.005},
    {'symbol': 'KAVAUSDT', 'name': 'Kava', 'allocation': 0.005},
    {'symbol': '1INCHUSDT', 'name': '1inch', 'allocation': 0.005},
    {'symbol': 'QTUMUSDT', 'name': 'Qtum', 'allocation': 0.005},
    {'symbol': 'STRKUSDT', 'name': 'Starknet', 'allocation': 0.005},
    {'symbol': 'DCRUSDT', 'name': 'Decred', 'allocation': 0.005},
    {'symbol': 'JITOUSDT', 'name': 'Jito', 'allocation': 0.005},
    {'symbol': 'BONKUSDT', 'name': 'Bonk', 'allocation': 0.005},
    {'symbol': 'PEPEUSDT', 'name': 'Pepe', 'allocation': 0.005},
    {'symbol': 'SHIBUSDT', 'name': 'Shiba Inu', 'allocation': 0.005},
    {'symbol': 'FLOKIUSDT', 'name': 'Floki', 'allocation': 0.005},
    {'symbol': 'NEIROUSDT', 'name': 'Neiro', 'allocation': 0.005},
    {'symbol': 'GNSUSDT', 'name': 'Gains Network', 'allocation': 0.005},
]

# SUMMARY:
# - High Performers (8): 16.0% total allocation
# - Good Performers (12): 18.0% total allocation  
# - Average (12): 12.0% total allocation
# - Underperformers (9): 4.5% total allocation
# - Not held (15): 7.5% total allocation
# TOTAL: 58.0% allocated (adjust as needed for 100%)

# RATIONALE:
# 1. Double allocation to top 8 performers (1% → 2%) to capture momentum
# 2. Increase allocation to good performers (1% → 1.5%)
# 3. Keep average performers at 1%
# 4. Reduce underperformers to 0.5% for risk management
# 5. Large caps (BTC, ETH, BNB) underperforming despite size - reduced to 0.5%
# 6. Small-cap altcoins (ALGO, MANA, RPL, LRC, FLR) leading - increased to 2%

# EXPECTED IMPACT:
# - Current weighted return: +1.932%
# - Optimized weighted return: +2.840%
# - Expected improvement: +0.908% (+47% better performance)
