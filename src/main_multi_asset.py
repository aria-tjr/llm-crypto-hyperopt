import configparser
from components import news_fetcher, sentiment_analyzer, trading_engine
import pandas as pd

def main():
    """
    Multi-asset LLM trading strategy simulation.
    Trades multiple cryptocurrencies with intelligent capital allocation.
    """
    print("=" * 80)
    print("MULTI-ASSET LLM TRADING STRATEGY SIMULATION")
    print("=" * 80)
    
    # --- 1. Configuration ---
    config = configparser.ConfigParser()
    config.read('src/config.ini')
    
    # Define optimal 8-asset portfolio for best diversification vs concentration
    assets = [
        {"ticker": "BTC-USD", "name": "Bitcoin", "allocation": 0.25},
        {"ticker": "ETH-USD", "name": "Ethereum", "allocation": 0.20},
        {"ticker": "SOL-USD", "name": "Solana", "allocation": 0.10},
        {"ticker": "AVAX-USD", "name": "Avalanche", "allocation": 0.10},
        {"ticker": "BNB-USD", "name": "BNB", "allocation": 0.10},
        {"ticker": "XRP-USD", "name": "Ripple", "allocation": 0.10},
        {"ticker": "ADA-USD", "name": "Cardano", "allocation": 0.08},
        {"ticker": "DOGE-USD", "name": "Dogecoin", "allocation": 0.07}
    ]
    
    # Try a longer period - last 30 days
    start_date = "2025-12-29"
    end_date = "2026-01-28"
    initial_capital = 10000.0
    leverage = 5.0  # 5x leverage
    
    print(f"\nTrading Assets:")
    for asset in assets:
        print(f"  - {asset['name']} ({asset['ticker']}): {asset['allocation']*100:.0f}% allocation")
    print(f"\nBacktest Period: {start_date} to {end_date}")
    print(f"Initial Capital: ${initial_capital:,.2f}")
    print(f"⚡ LEVERAGE: {leverage}x")
    print("=" * 80)
    
    # --- 2. Fetch Data for All Assets ---
    assets_data = []
    
    for asset in assets:
        print(f"\n[{asset['name']}] Fetching data...")
        
        # Fetch price data
        price_data = trading_engine.fetch_price_data(asset['ticker'], start_date, end_date)
        if price_data is None:
            print(f"  ⚠️  Could not fetch price data for {asset['name']}. Skipping.")
            continue
        
        # Fetch news
        headlines = news_fetcher.fetch_news(asset['ticker'], start_date, end_date)
        if not headlines:
            print(f"  ⚠️  Could not fetch news for {asset['name']}. Using neutral sentiment.")
            scores = [0.0] * len(price_data)
        else:
            # Analyze sentiment
            print(f"  Analyzing sentiment for {asset['name']}...")
            scores = sentiment_analyzer.analyze_headlines_for_scores(headlines)
            if scores is None:
                print(f"  ⚠️  Could not analyze sentiment for {asset['name']}. Using neutral.")
                scores = [0.0] * len(price_data)
        
        assets_data.append({
            'ticker': asset['ticker'],
            'name': asset['name'],
            'allocation': asset['allocation'],
            'price_data': price_data,
            'scores': scores
        })
        
        print(f"  ✓ {asset['name']} data ready")
    
    if not assets_data:
        print("\n❌ No asset data available. Exiting.")
        return
    
    print("\n" + "=" * 80)
    print("RUNNING MULTI-ASSET PORTFOLIO SIMULATION")
    print("=" * 80)
    
    # --- 3. Run Multi-Asset Simulation ---
    results = run_multi_asset_simulation(assets_data, initial_capital, start_date, end_date, leverage)
    
    # --- 4. Display Results ---
    print("\n" + "=" * 80)
    print("MULTI-ASSET PORTFOLIO PERFORMANCE")
    print("=" * 80)
    
    print(f"\nOverall Portfolio:")
    print(f"  Initial Capital:      ${results['initial_capital']:>10,.2f}")
    print(f"  Final Value:          ${results['final_value']:>10,.2f}")
    print(f"  Total Return:         {results['total_return']:>10.2f}%")
    print(f"  Maximum Drawdown:     {results['max_drawdown']:>10.2f}%")
    print(f"  Sharpe Ratio:         {results['sharpe_ratio']:>10.2f}")
    
    print(f"\nTrading Statistics:")
    print(f"  Total Trades:         {results['total_trades']:>10}")
    print(f"  Winning Trades:       {results['winning_trades']:>10}")
    print(f"  Win Rate:             {results['win_rate']:>10.1f}%")
    
    print(f"\nPer-Asset Performance:")
    for asset_result in results['per_asset']:
        print(f"\n  {asset_result['name']} ({asset_result['ticker']}):")
        print(f"    Return:             {asset_result['return']:>10.2f}%")
        print(f"    Trades:             {asset_result['trades']:>10}")
        print(f"    Win Rate:           {asset_result['win_rate']:>10.1f}%")
        print(f"    Final Position:     ${asset_result['final_value']:>10,.2f}")
    
    print("\n" + "=" * 80)
    print("SIMULATION COMPLETE")
    print("=" * 80)


def run_multi_asset_simulation(assets_data, initial_capital, start_date, end_date, leverage=1.0):
    """
    Runs a multi-asset portfolio simulation with adaptive strategy and leverage.
    
    Args:
        assets_data: List of asset data dictionaries
        initial_capital: Starting capital
        start_date: Start date
        end_date: End date
        leverage: Leverage multiplier (default 1.0 for no leverage)
        
    Returns:
        Dictionary with portfolio results
    """
    # Allocate capital to each asset
    cash_reserve = initial_capital * 0.1  # Keep 10% in cash
    tradable_capital = initial_capital - cash_reserve
    
    # Initialize portfolio state for each asset
    portfolio = {
        'cash': cash_reserve,
        'positions': {},
        'history': []
    }
    
    for asset in assets_data:
        portfolio['positions'][asset['ticker']] = {
            'name': asset['name'],
            'allocated_capital': tradable_capital * asset['allocation'],
            'cash': tradable_capital * asset['allocation'],
            'holdings': 0.0,
            'purchase_price': 0.0,
            'trailing_stop': 0.0,
            'peak_price': 0.0,
            'trades': 0,
            'winning_trades': 0,
            'regime': 'neutral'
        }
    
    # Get the length of simulation (use shortest asset data)
    num_days = min(len(asset['price_data']) for asset in assets_data)
    
    print(f"\nSimulating {num_days} trading days with {len(assets_data)} assets...")
    print()
    
    # Simulate each day
    for day_idx in range(num_days):
        date = None
        daily_portfolio_value = portfolio['cash']
        
        # Process each asset
        for asset in assets_data:
            ticker = asset['ticker']
            name = asset['name']
            price_data = asset['price_data'].iloc[day_idx]
            
            # Handle case where we might have fewer sentiment scores than price data
            if day_idx < len(asset['scores']):
                score = asset['scores'][day_idx]
            else:
                score = 0.0  # Default to neutral if no sentiment data
            
            if date is None:
                date = price_data.name
            
            current_price = float(price_data['Close'])
            position = portfolio['positions'][ticker]
            
            # Detect market regime
            prices_list = [float(row['Close']) for _, row in asset['price_data'].iterrows()]
            regime, volatility = trading_engine.detect_market_regime(prices_list, day_idx, 7)
            position['regime'] = regime
            
            # Set adaptive parameters based on regime
            if regime == 'bullish':
                buy_threshold = 0.60
                sell_threshold = -0.25
                max_position_pct = 0.90
                take_profit_pct = 0.08
                trailing_stop_pct = 0.04
                max_loss_pct = 0.05
            elif regime == 'bearish':
                buy_threshold = 0.75
                sell_threshold = -0.15
                max_position_pct = 0.50
                take_profit_pct = 0.04
                trailing_stop_pct = 0.03
                max_loss_pct = 0.03
            else:
                buy_threshold = 0.65
                sell_threshold = -0.20
                max_position_pct = 0.70
                take_profit_pct = 0.05
                trailing_stop_pct = 0.035
                max_loss_pct = 0.04
            
            # Adjust for volatility
            if volatility > 0.03:
                trailing_stop_pct *= 0.8
                max_loss_pct *= 0.8
            
            # Calculate momentum
            momentum_positive = False
            if day_idx >= 3:
                recent_prices = prices_list[day_idx-3:day_idx]
                momentum_positive = current_price > sum(recent_prices) / len(recent_prices)
            
            action = "HOLD"
            
            # --- TRADING LOGIC ---
            
            # TAKE PROFIT
            if position['holdings'] > 0 and position['purchase_price'] > 0:
                profit_pct = (current_price - position['purchase_price']) / position['purchase_price']
                if profit_pct >= take_profit_pct:
                    cash_from_sale = position['holdings'] * current_price
                    position['cash'] += cash_from_sale
                    action = f"TAKE PROFIT (+{profit_pct*100:.1f}%)"
                    position['holdings'] = 0.0
                    position['purchase_price'] = 0.0
                    position['trailing_stop'] = 0.0
                    position['trades'] += 1
                    position['winning_trades'] += 1
            
            # HARD STOP-LOSS
            if position['holdings'] > 0 and position['purchase_price'] > 0:
                loss_pct = (current_price - position['purchase_price']) / position['purchase_price']
                if loss_pct <= -max_loss_pct:
                    cash_from_sale = position['holdings'] * current_price
                    position['cash'] += cash_from_sale
                    action = f"STOP-LOSS ({loss_pct*100:+.1f}%)"
                    position['holdings'] = 0.0
                    position['purchase_price'] = 0.0
                    position['trailing_stop'] = 0.0
                    position['trades'] += 1
            
            # LIQUIDATION (for leveraged positions)
            if leverage > 1.0 and position['holdings'] > 0 and position['purchase_price'] > 0:
                loss_pct = (current_price - position['purchase_price']) / position['purchase_price']
                liquidation_threshold = -0.95 / leverage  # e.g., -19% for 5x leverage
                if loss_pct <= liquidation_threshold:
                    # Position is liquidated, lose all invested capital
                    position['cash'] = 0.0  # All margin is lost
                    action = f"💀 LIQUIDATED ({loss_pct*100:+.1f}%)"
                    position['holdings'] = 0.0
                    position['purchase_price'] = 0.0
                    position['trailing_stop'] = 0.0
                    position['trades'] += 1
            
            # TRAILING STOP
            if position['holdings'] > 0 and position['trailing_stop'] > 0 and current_price < position['trailing_stop']:
                cash_from_sale = position['holdings'] * current_price
                position['cash'] += cash_from_sale
                pnl = (current_price - position['purchase_price']) / position['purchase_price']
                action = f"TRAIL-STOP ({pnl*100:+.1f}%)"
                if current_price > position['purchase_price']:
                    position['winning_trades'] += 1
                position['holdings'] = 0.0
                position['purchase_price'] = 0.0
                position['trailing_stop'] = 0.0
                position['trades'] += 1
            
            # BUY
            if position['holdings'] == 0 and score > buy_threshold:
                strong_signal = (regime == 'bearish' and score >= 0.80 and momentum_positive) or \
                               (regime != 'bearish' and (score >= buy_threshold) and (momentum_positive or score >= 0.75))
                
                if strong_signal:
                    available_capital = position['cash']
                    position_size = available_capital * max_position_pct * leverage  # Apply leverage
                    
                    if position_size >= 100:  # Minimum $100 trade
                        units_to_buy = position_size / current_price
                        position['holdings'] = units_to_buy
                        position['cash'] -= (position_size / leverage)  # Only actual capital is spent
                        position['purchase_price'] = current_price
                        position['trailing_stop'] = current_price * (1 - trailing_stop_pct)
                        position['peak_price'] = current_price
                        action = f"BUY {units_to_buy:.4f} units ({max_position_pct*100:.0f}% @ {leverage}x)"
            
            # SELL on negative sentiment
            if position['holdings'] > 0 and score < sell_threshold:
                cash_from_sale = position['holdings'] * current_price
                position['cash'] += cash_from_sale
                pnl = (current_price - position['purchase_price']) / position['purchase_price']
                action = f"SELL sentiment ({pnl*100:+.1f}%)"
                if current_price > position['purchase_price']:
                    position['winning_trades'] += 1
                position['holdings'] = 0.0
                position['purchase_price'] = 0.0
                position['trailing_stop'] = 0.0
                position['trades'] += 1
            
            # REGIME CHANGE EXIT
            if position['holdings'] > 0 and regime == 'bearish':
                loss_pct = (current_price - position['purchase_price']) / position['purchase_price']
                if loss_pct < -0.02:
                    cash_from_sale = position['holdings'] * current_price
                    position['cash'] += cash_from_sale
                    action = f"EXIT regime change ({loss_pct*100:+.1f}%)"
                    position['holdings'] = 0.0
                    position['purchase_price'] = 0.0
                    position['trailing_stop'] = 0.0
                    position['trades'] += 1
            
            # Update trailing stop
            if position['holdings'] > 0 and current_price > position['peak_price']:
                position['peak_price'] = current_price
                profit_pct = (current_price - position['purchase_price']) / position['purchase_price']
                if profit_pct > 0.05:
                    position['trailing_stop'] = current_price * (1 - trailing_stop_pct * 0.5)
                else:
                    position['trailing_stop'] = current_price * (1 - trailing_stop_pct)
            
            # Calculate position value
            position_value = position['cash'] + (position['holdings'] * current_price)
            daily_portfolio_value += position_value
            
            # Print daily update
            regime_emoji = "🚀" if regime == 'bullish' else "📉" if regime == 'bearish' else "➡️"
            if action != "HOLD":
                print(f"{date.date()} | {name:8s} {regime_emoji} | ${current_price:8,.2f} | Score:{score:5.2f} | {action:<35} | ${position_value:>9,.2f}")
        
        # Record portfolio value for this day
        portfolio['history'].append({
            'date': date,
            'value': daily_portfolio_value
        })
    
    # Calculate final results
    portfolio_values = [h['value'] for h in portfolio['history']]
    final_value = portfolio_values[-1]
    total_return = ((final_value - initial_capital) / initial_capital) * 100
    
    # Calculate max drawdown
    peak = portfolio_values[0]
    max_drawdown = 0
    for value in portfolio_values:
        if value > peak:
            peak = value
        drawdown = ((peak - value) / peak) * 100
        if drawdown > max_drawdown:
            max_drawdown = drawdown
    
    # Calculate Sharpe ratio
    returns = [(portfolio_values[i] - portfolio_values[i-1]) / portfolio_values[i-1] 
               for i in range(1, len(portfolio_values))]
    if returns:
        avg_return = sum(returns) / len(returns)
        std_return = (sum((r - avg_return) ** 2 for r in returns) / len(returns)) ** 0.5
        sharpe_ratio = (avg_return / std_return * (252 ** 0.5)) if std_return > 0 else 0
    else:
        sharpe_ratio = 0
    
    # Calculate totals
    total_trades = sum(pos['trades'] for pos in portfolio['positions'].values())
    total_winning = sum(pos['winning_trades'] for pos in portfolio['positions'].values())
    win_rate = (total_winning / total_trades * 100) if total_trades > 0 else 0
    
    # Per-asset results
    per_asset_results = []
    for ticker, position in portfolio['positions'].items():
        asset_data = next(a for a in assets_data if a['ticker'] == ticker)
        final_prices = [float(row['Close']) for _, row in asset_data['price_data'].iterrows()]
        current_price = final_prices[-1]
        position_value = position['cash'] + (position['holdings'] * current_price)
        asset_return = ((position_value - position['allocated_capital']) / position['allocated_capital']) * 100
        asset_win_rate = (position['winning_trades'] / position['trades'] * 100) if position['trades'] > 0 else 0
        
        per_asset_results.append({
            'ticker': ticker,
            'name': position['name'],
            'return': asset_return,
            'trades': position['trades'],
            'win_rate': asset_win_rate,
            'final_value': position_value
        })
    
    return {
        'initial_capital': initial_capital,
        'final_value': final_value,
        'total_return': total_return,
        'max_drawdown': max_drawdown,
        'sharpe_ratio': sharpe_ratio,
        'total_trades': total_trades,
        'winning_trades': total_winning,
        'win_rate': win_rate,
        'per_asset': per_asset_results
    }


if __name__ == "__main__":
    main()
