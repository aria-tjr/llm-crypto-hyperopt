"""
Hyperparameter optimization for multi-asset LLM trading strategy.
Finds optimal parameters for maximum profit with minimum drawdown across multiple assets.
"""
import configparser
import random
import sys
sys.path.insert(0, 'src')
from components import news_fetcher, sentiment_analyzer, trading_engine
import pandas as pd

def run_multi_asset_backtest(assets_data, params, initial_capital=10000):
    """
    Runs multi-asset backtest with specific parameters.
    """
    cash_reserve = initial_capital * 0.1
    tradable_capital = initial_capital - cash_reserve
    
    portfolio = {
        'cash': cash_reserve,
        'positions': {}
    }
    
    for asset in assets_data:
        portfolio['positions'][asset['ticker']] = {
            'allocated_capital': tradable_capital * asset['allocation'],
            'cash': tradable_capital * asset['allocation'],
            'holdings': 0.0,
            'purchase_price': 0.0,
            'trailing_stop': 0.0,
            'peak_price': 0.0,
            'trades': 0,
            'winning_trades': 0
        }
    
    num_days = min(len(asset['price_data']) for asset in assets_data)
    portfolio_values = []
    
    for day_idx in range(num_days):
        daily_portfolio_value = portfolio['cash']
        
        for asset in assets_data:
            ticker = asset['ticker']
            price_data = asset['price_data'].iloc[day_idx]
            score = asset['scores'][day_idx]
            current_price = float(price_data['Close'])
            position = portfolio['positions'][ticker]
            
            # Detect regime
            prices_list = [float(row['Close']) for _, row in asset['price_data'].iterrows()]
            regime, volatility = trading_engine.detect_market_regime(prices_list, day_idx, params['regime_lookback'])
            
            # Set parameters based on regime
            if regime == 'bullish':
                buy_threshold = params['buy_threshold_bull']
                sell_threshold = params['sell_threshold_bull']
                max_position_pct = params['max_position_bull']
                take_profit_pct = params['take_profit_bull']
                trailing_stop_pct = params['trailing_stop_bull']
                max_loss_pct = params['max_loss_bull']
            elif regime == 'bearish':
                buy_threshold = params['buy_threshold_bear']
                sell_threshold = params['sell_threshold_bear']
                max_position_pct = params['max_position_bear']
                take_profit_pct = params['take_profit_bear']
                trailing_stop_pct = params['trailing_stop_bear']
                max_loss_pct = params['max_loss_bear']
            else:
                buy_threshold = params['buy_threshold_neutral']
                sell_threshold = params['sell_threshold_neutral']
                max_position_pct = params['max_position_neutral']
                take_profit_pct = params['take_profit_neutral']
                trailing_stop_pct = params['trailing_stop_neutral']
                max_loss_pct = params['max_loss_neutral']
            
            # Volatility adjustment
            if volatility > 0.03:
                trailing_stop_pct *= params['volatility_adjustment']
                max_loss_pct *= params['volatility_adjustment']
            
            # Momentum
            momentum_positive = False
            if day_idx >= params['momentum_lookback']:
                recent_prices = prices_list[day_idx-params['momentum_lookback']:day_idx]
                momentum_positive = current_price > sum(recent_prices) / len(recent_prices)
            
            # TAKE PROFIT
            if position['holdings'] > 0 and position['purchase_price'] > 0:
                profit_pct = (current_price - position['purchase_price']) / position['purchase_price']
                if profit_pct >= take_profit_pct:
                    cash_from_sale = position['holdings'] * current_price
                    position['cash'] += cash_from_sale
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
                    position['holdings'] = 0.0
                    position['purchase_price'] = 0.0
                    position['trailing_stop'] = 0.0
                    position['trades'] += 1
            
            # TRAILING STOP
            if position['holdings'] > 0 and position['trailing_stop'] > 0 and current_price < position['trailing_stop']:
                cash_from_sale = position['holdings'] * current_price
                position['cash'] += cash_from_sale
                if current_price > position['purchase_price']:
                    position['winning_trades'] += 1
                position['holdings'] = 0.0
                position['purchase_price'] = 0.0
                position['trailing_stop'] = 0.0
                position['trades'] += 1
            
            # BUY
            if position['holdings'] == 0 and score > buy_threshold:
                strong_signal = (regime == 'bearish' and score >= params['strong_signal_threshold'] and momentum_positive) or \
                               (regime != 'bearish' and score >= buy_threshold and (momentum_positive or score >= params['strong_signal_threshold']))
                
                if strong_signal:
                    available_capital = position['cash']
                    position_size = available_capital * max_position_pct
                    
                    if position_size >= 100:
                        units_to_buy = position_size / current_price
                        position['holdings'] = units_to_buy
                        position['cash'] -= position_size
                        position['purchase_price'] = current_price
                        position['trailing_stop'] = current_price * (1 - trailing_stop_pct)
                        position['peak_price'] = current_price
            
            # SELL
            if position['holdings'] > 0 and score < sell_threshold:
                cash_from_sale = position['holdings'] * current_price
                position['cash'] += cash_from_sale
                if current_price > position['purchase_price']:
                    position['winning_trades'] += 1
                position['holdings'] = 0.0
                position['purchase_price'] = 0.0
                position['trailing_stop'] = 0.0
                position['trades'] += 1
            
            # REGIME CHANGE EXIT
            if position['holdings'] > 0 and regime == 'bearish':
                loss_pct = (current_price - position['purchase_price']) / position['purchase_price']
                if loss_pct < -params['regime_exit_threshold']:
                    cash_from_sale = position['holdings'] * current_price
                    position['cash'] += cash_from_sale
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
            
            position_value = position['cash'] + (position['holdings'] * current_price)
            daily_portfolio_value += position_value
        
        portfolio_values.append(daily_portfolio_value)
    
    # Calculate metrics
    final_value = portfolio_values[-1]
    total_return = ((final_value - initial_capital) / initial_capital) * 100
    
    peak = portfolio_values[0]
    max_drawdown = 0
    for value in portfolio_values:
        if value > peak:
            peak = value
        drawdown = (peak - value) / peak
        if drawdown > max_drawdown:
            max_drawdown = drawdown
    
    total_trades = sum(pos['trades'] for pos in portfolio['positions'].values())
    total_winning = sum(pos['winning_trades'] for pos in portfolio['positions'].values())
    win_rate = (total_winning / total_trades * 100) if total_trades > 0 else 0
    
    # Fitness: maximize return while minimizing drawdown
    if max_drawdown > 0:
        fitness = total_return / (max_drawdown * 100) + (total_return * 0.5) - (max_drawdown * 30)
    else:
        fitness = total_return
    
    return {
        'total_return': total_return,
        'max_drawdown': max_drawdown * 100,
        'fitness': fitness,
        'num_trades': total_trades,
        'win_rate': win_rate,
        'final_value': final_value
    }


def main():
    """
    Run hyperparameter optimization for multi-asset strategy
    """
    print("=" * 80)
    print("MULTI-ASSET HYPERPARAMETER OPTIMIZATION")
    print("=" * 80)
    
    # Load configuration
    config = configparser.ConfigParser()
    config.read('src/config.ini')
    
    # Define assets
    assets = [
        {"ticker": "BTC-USD", "name": "Bitcoin", "allocation": 0.40},
        {"ticker": "ETH-USD", "name": "Ethereum", "allocation": 0.30},
        {"ticker": "SOL-USD", "name": "Solana", "allocation": 0.15},
        {"ticker": "AVAX-USD", "name": "Avalanche", "allocation": 0.15}
    ]
    
    start_date = "2026-01-13"
    end_date = "2026-01-28"
    
    print(f"\nFetching data for {len(assets)} assets...")
    
    # Fetch data for all assets
    assets_data = []
    for asset in assets:
        print(f"  Loading {asset['name']}...", end=" ")
        price_data = trading_engine.fetch_price_data(asset['ticker'], start_date, end_date)
        if price_data is None:
            print("❌ Failed")
            continue
        
        headlines = news_fetcher.fetch_news(asset['ticker'], start_date, end_date)
        if not headlines:
            scores = [0.0] * len(price_data)
        else:
            scores = sentiment_analyzer.analyze_headlines_for_scores(headlines)
            if scores is None:
                scores = [0.0] * len(price_data)
        
        assets_data.append({
            'ticker': asset['ticker'],
            'name': asset['name'],
            'allocation': asset['allocation'],
            'price_data': price_data,
            'scores': scores
        })
        print("✓")
    
    if len(assets_data) < 2:
        print("\n❌ Need at least 2 assets. Exiting.")
        return
    
    print("\n" + "=" * 80)
    print("STARTING RANDOM SEARCH OPTIMIZATION (Fast)")
    print("=" * 80)
    
    # Random search - sample from parameter ranges
    def random_params():
        return {
            # Bullish parameters
            'buy_threshold_bull': random.choice([0.55, 0.60, 0.65]),
            'sell_threshold_bull': random.choice([-0.25, -0.30]),
            'max_position_bull': random.choice([0.80, 0.90]),
            'take_profit_bull': random.choice([0.06, 0.08, 0.10]),
            'trailing_stop_bull': random.choice([0.04, 0.05]),
            'max_loss_bull': random.choice([0.04, 0.05]),
            
            # Bearish parameters
            'buy_threshold_bear': random.choice([0.70, 0.75, 0.80]),
            'sell_threshold_bear': random.choice([-0.15, -0.20]),
            'max_position_bear': random.choice([0.40, 0.50]),
            'take_profit_bear': random.choice([0.03, 0.04]),
            'trailing_stop_bear': random.choice([0.025, 0.03]),
            'max_loss_bear': random.choice([0.025, 0.03]),
            
            # Neutral parameters
            'buy_threshold_neutral': random.choice([0.60, 0.65, 0.70]),
            'sell_threshold_neutral': random.choice([-0.20, -0.25]),
            'max_position_neutral': random.choice([0.60, 0.70]),
            'take_profit_neutral': random.choice([0.04, 0.05, 0.06]),
            'trailing_stop_neutral': random.choice([0.03, 0.035, 0.04]),
            'max_loss_neutral': random.choice([0.03, 0.04]),
            
            # Other parameters
            'regime_lookback': random.choice([5, 7]),
            'momentum_lookback': random.choice([2, 3]),
            'strong_signal_threshold': random.choice([0.75, 0.80]),
            'volatility_adjustment': random.choice([0.75, 0.80, 0.85]),
            'regime_exit_threshold': random.choice([0.02, 0.025])
        }
    
    # Test fewer combinations with random search
    num_tests = 500  # Much faster!
    
    print(f"\nTesting {num_tests} random parameter combinations...")
    print("This should take 2-3 minutes...\n")
    
    results = []
    best_fitness = float('-inf')
    best_params = None
    
    for i in range(num_tests):
        if (i + 1) % 50 == 0:
            print(f"Progress: {i + 1}/{num_tests} ({(i+1)/num_tests*100:.1f}%)")
        
        params = random_params()
        result = run_multi_asset_backtest(assets_data, params)
        result['params'] = params
        results.append(result)
        
        if result['fitness'] > best_fitness:
            best_fitness = result['fitness']
            best_params = params
    
    # Sort by fitness
    results.sort(key=lambda x: x['fitness'], reverse=True)
    
    print("\n" + "=" * 80)
    print("OPTIMIZATION COMPLETE - TOP 10 PARAMETER SETS")
    print("=" * 80)
    
    for i, result in enumerate(results[:10]):
        print(f"\n{'='*80}")
        print(f"Rank #{i+1} | Fitness Score: {result['fitness']:.2f}")
        print(f"{'='*80}")
        print(f"Performance:")
        print(f"  Total Return:     {result['total_return']:>8.2f}%")
        print(f"  Max Drawdown:     {result['max_drawdown']:>8.2f}%")
        print(f"  Final Value:      ${result['final_value']:>8,.2f}")
        print(f"  Number of Trades: {result['num_trades']:>8}")
        print(f"  Win Rate:         {result['win_rate']:>8.1f}%")
        
        if i < 3:  # Show parameters for top 3
            print(f"\nKey Parameters:")
            print(f"  Bullish:  Buy>{result['params']['buy_threshold_bull']:.2f}, Pos={result['params']['max_position_bull']:.0%}, TP={result['params']['take_profit_bull']:.0%}")
            print(f"  Bearish:  Buy>{result['params']['buy_threshold_bear']:.2f}, Pos={result['params']['max_position_bear']:.0%}, TP={result['params']['take_profit_bear']:.0%}")
            print(f"  Neutral:  Buy>{result['params']['buy_threshold_neutral']:.2f}, Pos={result['params']['max_position_neutral']:.0%}, TP={result['params']['take_profit_neutral']:.0%}")
    
    print("\n" + "=" * 80)
    print("BEST PARAMETERS (Rank #1)")
    print("=" * 80)
    print("\nBullish Market:")
    print(f"  buy_threshold_bull = {best_params['buy_threshold_bull']}")
    print(f"  sell_threshold_bull = {best_params['sell_threshold_bull']}")
    print(f"  max_position_bull = {best_params['max_position_bull']}")
    print(f"  take_profit_bull = {best_params['take_profit_bull']}")
    print(f"  trailing_stop_bull = {best_params['trailing_stop_bull']}")
    print(f"  max_loss_bull = {best_params['max_loss_bull']}")
    
    print("\nBearish Market:")
    print(f"  buy_threshold_bear = {best_params['buy_threshold_bear']}")
    print(f"  sell_threshold_bear = {best_params['sell_threshold_bear']}")
    print(f"  max_position_bear = {best_params['max_position_bear']}")
    print(f"  take_profit_bear = {best_params['take_profit_bear']}")
    print(f"  trailing_stop_bear = {best_params['trailing_stop_bear']}")
    print(f"  max_loss_bear = {best_params['max_loss_bear']}")
    
    print("\nNeutral Market:")
    print(f"  buy_threshold_neutral = {best_params['buy_threshold_neutral']}")
    print(f"  sell_threshold_neutral = {best_params['sell_threshold_neutral']}")
    print(f"  max_position_neutral = {best_params['max_position_neutral']}")
    print(f"  take_profit_neutral = {best_params['take_profit_neutral']}")
    print(f"  trailing_stop_neutral = {best_params['trailing_stop_neutral']}")
    print(f"  max_loss_neutral = {best_params['max_loss_neutral']}")
    
    print("\nOther:")
    print(f"  regime_lookback = {best_params['regime_lookback']}")
    print(f"  momentum_lookback = {best_params['momentum_lookback']}")
    print(f"  strong_signal_threshold = {best_params['strong_signal_threshold']}")
    print(f"  volatility_adjustment = {best_params['volatility_adjustment']}")
    print(f"  regime_exit_threshold = {best_params['regime_exit_threshold']}")
    
    # Save results
    results_df = pd.DataFrame([
        {
            **r['params'],
            'total_return': r['total_return'],
            'max_drawdown': r['max_drawdown'],
            'fitness': r['fitness'],
            'num_trades': r['num_trades'],
            'win_rate': r['win_rate']
        }
        for r in results
    ])
    results_df.to_csv('hyperopt_multi_asset_results.csv', index=False)
    print("\n✓ Full results saved to: hyperopt_multi_asset_results.csv")
    
    print("\n" + "=" * 80)
    print("OPTIMIZATION FINISHED")
    print("=" * 80)


if __name__ == "__main__":
    main()
