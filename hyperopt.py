"""
Hyperparameter optimization for the LLM trading strategy.
Finds optimal parameters for maximum profit with minimum drawdown.
"""
import configparser
import itertools
import sys
sys.path.insert(0, 'src')
from components import news_fetcher, sentiment_analyzer, trading_engine
import pandas as pd

def run_backtest_with_params(scores, price_data, params):
    """
    Runs a backtest with specific parameters.
    
    Args:
        scores: List of sentiment scores
        price_data: DataFrame with price data
        params: Dictionary of strategy parameters
        
    Returns:
        Dictionary with performance metrics
    """
    initial_cash = 10000.0
    num_days = min(len(scores), len(price_data))
    price_data = price_data.head(num_days)
    scores = scores[:num_days]
    
    prices_list = [float(row['Close']) for _, row in price_data.iterrows()]
    
    cash = initial_cash
    asset_holdings = 0.0
    portfolio_values = []
    purchase_price = 0
    trailing_stop_price = 0
    peak_price = 0
    num_trades = 0
    winning_trades = 0
    
    for i, (date, row) in enumerate(price_data.iterrows()):
        current_price = float(row['Close'])
        score = scores[i]
        
        # Calculate momentum
        momentum_positive = False
        if i >= params['momentum_lookback']:
            recent_prices = prices_list[i-params['momentum_lookback']:i]
            momentum_positive = current_price > sum(recent_prices) / len(recent_prices)
        
        current_portfolio_value = cash + (asset_holdings * current_price)
        
        # TAKE PROFIT
        if asset_holdings > 0 and purchase_price > 0:
            profit_pct = (current_price - purchase_price) / purchase_price
            if profit_pct >= params['take_profit_pct']:
                cash_from_sale = asset_holdings * current_price
                cash += cash_from_sale
                asset_holdings = 0.0
                purchase_price = 0
                trailing_stop_price = 0
                peak_price = 0
                num_trades += 1
                winning_trades += 1
                continue
        
        # STOP-LOSS (hard stop)
        if asset_holdings > 0 and purchase_price > 0:
            loss_pct = (current_price - purchase_price) / purchase_price
            if loss_pct <= -params['max_loss_pct']:
                cash_from_sale = asset_holdings * current_price
                cash += cash_from_sale
                asset_holdings = 0.0
                purchase_price = 0
                trailing_stop_price = 0
                peak_price = 0
                num_trades += 1
                continue
        
        # TRAILING STOP
        if asset_holdings > 0 and current_price < trailing_stop_price:
            cash_from_sale = asset_holdings * current_price
            cash += cash_from_sale
            if current_price > purchase_price:
                winning_trades += 1
            asset_holdings = 0.0
            purchase_price = 0
            trailing_stop_price = 0
            peak_price = 0
            num_trades += 1
            continue
        
        # BUY
        if score > params['buy_threshold'] and asset_holdings == 0:
            strong_signal = score >= 0.75 or momentum_positive
            
            if strong_signal:
                sentiment_multiplier = min((score - params['buy_threshold']) / (1.0 - params['buy_threshold']), 1.0)
                position_size_pct = params['min_position_pct'] + (sentiment_multiplier * (params['max_position_pct'] - params['min_position_pct']))
                
                trade_size_cash = current_portfolio_value * position_size_pct
                
                if cash >= trade_size_cash:
                    assets_to_buy = trade_size_cash / current_price
                    asset_holdings += assets_to_buy
                    cash -= trade_size_cash
                    purchase_price = current_price
                    trailing_stop_price = purchase_price * (1 - params['trailing_stop_pct'])
                    peak_price = current_price
        
        # SELL
        elif score < params['sell_threshold'] and asset_holdings > 0:
            cash_from_sale = asset_holdings * current_price
            cash += cash_from_sale
            if current_price > purchase_price:
                winning_trades += 1
            asset_holdings = 0.0
            purchase_price = 0
            trailing_stop_price = 0
            peak_price = 0
            num_trades += 1
        
        # Update trailing stop
        if asset_holdings > 0:
            if current_price > peak_price:
                peak_price = current_price
                profit_pct = (current_price - purchase_price) / purchase_price
                if profit_pct > 0.03:  # If up 3%+, tighten stop
                    trailing_stop_price = current_price * (1 - params['trailing_stop_pct'] * 0.6)
                else:
                    trailing_stop_price = current_price * (1 - params['trailing_stop_pct'])
        
        portfolio_values.append(current_portfolio_value)
    
    # Calculate metrics
    final_portfolio_value = portfolio_values[-1] if portfolio_values else initial_cash
    total_return_pct = ((final_portfolio_value - initial_cash) / initial_cash) * 100
    
    peak = portfolio_values[0] if portfolio_values else initial_cash
    max_drawdown = 0
    for value in portfolio_values:
        if value > peak:
            peak = value
        drawdown = (peak - value) / peak
        if drawdown > max_drawdown:
            max_drawdown = drawdown
    
    win_rate = (winning_trades / num_trades * 100) if num_trades > 0 else 0
    
    # Custom fitness: maximize return while minimizing drawdown
    if max_drawdown > 0:
        fitness = total_return_pct / (max_drawdown * 100) - abs(max_drawdown * 50)
    else:
        fitness = total_return_pct
    
    return {
        'total_return_pct': total_return_pct,
        'max_drawdown_pct': max_drawdown * 100,
        'fitness': fitness,
        'num_trades': num_trades,
        'win_rate': win_rate,
        'final_value': final_portfolio_value
    }


def main():
    """
    Run hyperparameter optimization
    """
    print("=" * 80)
    print("HYPERPARAMETER OPTIMIZATION FOR LLM TRADING STRATEGY")
    print("=" * 80)
    
    # Load configuration
    config = configparser.ConfigParser()
    config.read('src/config.ini')
    ticker = "BTC-USD"
    start_date = "2026-01-13"
    end_date = "2026-01-28"
    
    print(f"\nFetching data for {ticker} from {start_date} to {end_date}...")
    
    # Fetch data
    price_data = trading_engine.fetch_price_data(ticker, start_date, end_date)
    if price_data is None:
        print("Could not fetch price data. Exiting.")
        return
    
    print("Fetching news headlines...")
    headlines = news_fetcher.fetch_news(ticker, start_date, end_date)
    if not headlines:
        print("Could not fetch news headlines. Exiting.")
        return
    
    print("Analyzing sentiment...")
    scores = sentiment_analyzer.analyze_headlines_for_scores(headlines)
    if scores is None:
        print("Could not analyze sentiment. Exiting.")
        return
    
    print("\n" + "=" * 80)
    print("STARTING HYPERPARAMETER GRID SEARCH")
    print("=" * 80)
    
    # Define parameter grid
    param_grid = {
        'buy_threshold': [0.60, 0.65, 0.70, 0.75],
        'sell_threshold': [-0.15, -0.20, -0.25, -0.30],
        'trailing_stop_pct': [0.03, 0.04, 0.05],
        'take_profit_pct': [0.04, 0.05, 0.06, 0.07],
        'max_loss_pct': [0.03, 0.04, 0.05],
        'min_position_pct': [0.25, 0.30],
        'max_position_pct': [0.35, 0.40],
        'momentum_lookback': [2, 3]
    }
    
    # Generate all combinations
    keys = param_grid.keys()
    values = param_grid.values()
    combinations = [dict(zip(keys, v)) for v in itertools.product(*values)]
    
    print(f"\nTesting {len(combinations)} parameter combinations...")
    print("This may take a few minutes...\n")
    
    results = []
    best_fitness = float('-inf')
    best_params = None
    
    for i, params in enumerate(combinations):
        if (i + 1) % 50 == 0:
            print(f"Progress: {i + 1}/{len(combinations)} ({(i+1)/len(combinations)*100:.1f}%)")
        
        result = run_backtest_with_params(scores, price_data, params)
        result['params'] = params
        results.append(result)
        
        if result['fitness'] > best_fitness:
            best_fitness = result['fitness']
            best_params = params
    
    # Sort results by fitness
    results.sort(key=lambda x: x['fitness'], reverse=True)
    
    print("\n" + "=" * 80)
    print("OPTIMIZATION COMPLETE - TOP 10 PARAMETER SETS")
    print("=" * 80)
    
    for i, result in enumerate(results[:10]):
        print(f"\n{'='*80}")
        print(f"Rank #{i+1} | Fitness Score: {result['fitness']:.2f}")
        print(f"{'='*80}")
        print(f"Performance:")
        print(f"  Total Return:     {result['total_return_pct']:>8.2f}%")
        print(f"  Max Drawdown:     {result['max_drawdown_pct']:>8.2f}%")
        print(f"  Final Value:      ${result['final_value']:>8,.2f}")
        print(f"  Number of Trades: {result['num_trades']:>8}")
        print(f"  Win Rate:         {result['win_rate']:>8.1f}%")
        print(f"\nParameters:")
        for key, value in result['params'].items():
            print(f"  {key:20s}: {value}")
    
    print("\n" + "=" * 80)
    print("BEST PARAMETERS (Rank #1)")
    print("=" * 80)
    print("\nCopy these parameters to your trading_engine.py:")
    print("-" * 80)
    for key, value in best_params.items():
        print(f"{key} = {value}")
    print("-" * 80)
    
    # Save results to CSV
    results_df = pd.DataFrame([
        {
            **r['params'],
            'total_return_pct': r['total_return_pct'],
            'max_drawdown_pct': r['max_drawdown_pct'],
            'fitness': r['fitness'],
            'num_trades': r['num_trades'],
            'win_rate': r['win_rate']
        }
        for r in results
    ])
    results_df.to_csv('hyperopt_results.csv', index=False)
    print("\nFull results saved to: hyperopt_results.csv")
    
    print("\n" + "=" * 80)
    print("OPTIMIZATION FINISHED")
    print("=" * 80)


if __name__ == "__main__":
    main()
