# llm-crypto-hyperopt

Adaptive crypto trading research project: LLM-driven sentiment + hyperparameter-optimized portfolio strategies on Bybit perpetuals. Explores 100-asset allocation, weekly/hourly hyperopt loops, hybrid sizing, and live Bybit demo trading.

## Highlights

- **100-asset portfolio allocator** with optimized weights
- **Multiple hyperopt pipelines**: fast, hybrid, multi-asset, tight-TP, Optuna-based
- **Adaptive parameter system**: weekly re-optimization based on recent market regime
- **LLM-driven sentiment overrides** from news + social data
- **Backtest harnesses** for 20-asset quick-check and full 100-asset runs
- **Bybit demo integration** for live paper trading

## Structure

Top-level scripts are grouped by intent:

- `backtest_*.py` — offline strategy evaluation
- `hyperopt_*.py` — parameter search (Optuna, CSV/JSON result stores)
- `analyze_*.py` — diagnostics on trade history, drawdown, PnL, timing
- `check_*.py` — live account/PnL/position snapshots
- `optimize_*.py` — portfolio allocation
- `src/` — core bot (Bybit connector, live trader, signal components, LLM overrides)
- `tests/` — unit tests

## Quick start (live demo)

1. Create Bybit demo API keys at <https://www.bybit.com/user/account>
2. Export credentials:
   ```bash
   export BYBIT_API_KEY=your_key
   export BYBIT_API_SECRET=your_secret
   ```
3. Install deps:
   ```bash
   pip install -r requirements.txt
   ```
4. Test connection:
   ```bash
   python src/test_bybit_simple.py
   ```
5. See `README_LIVE_TRADING.md` for the full setup walkthrough.

## Hyperopt workflow

```bash
# Weekly hyperopt loop (shell wrapper)
bash run_weekly_hyperopt.sh

# Or run a specific pipeline directly
python hyperopt_optuna.py
python hyperopt_multi_asset.py
python hyperopt_hybrid.py
```

Results are saved to JSON/CSV files alongside each script.

## Independent backtest (technical signal only)

An independent walk-forward test of the technical signal in `src/components/signal_generator.py` (`generate_trading_signal`, last 100 closes), **with the LLM override switched off**. Rules follow `backtest_signals.py`: long-only, enter when signal > 0.3, exit when signal < −0.3, take profit 8%, stop loss 3%. Data: Binance BTCUSDT/ETHUSDT USD-M futures, 15m, Apr–Sep 2026 out of sample. 1x leverage (not the script's 5x), 0.04% fee per side, decisions at bar close and fills at next open. Funding and slippage not modelled.

| Symbol | Trades | Win rate | Net return | Max DD | Profit factor | Sharpe | Buy & hold |
|---|---|---|---|---|---|---|---|
| BTCUSDT | 60 | 40.0% | +13.0% | −21.6% | 1.27 | 1.03 | +22.4% |
| ETHUSDT | 67 | 31.3% | −20.7% | −32.7% | 0.74 | −1.33 | +27.5% |

Mixed result: positive on BTC but below buy-and-hold, negative on ETH. The LLM-assisted path and the hyperopt pipelines were not tested. See also `BACKTEST_RESULTS.md` (Jan 2026, 5x: −17.24%).

This project does not use Freqtrade; it has its own backtest and hyperopt scripts.

## ⚠️ Disclaimer

This software is provided **for educational and research purposes only** and is **not** financial advice. LLM-driven signals are experimental; backtest metrics reflect historical simulation. Leveraged perpetuals trading can result in rapid liquidation and total loss of capital. The author assumes no liability for losses. Use Bybit demo mode for all exploration, and only switch to mainnet with capital you can afford to lose.
