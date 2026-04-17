import yfinance as yf
import pandas as pd

def fetch_price_data(ticker: str, start_date: str, end_date: str):
    """
    Fetches real historical price data from Yahoo Finance.
    """
    try:
        print(f"Fetching {ticker} price data from {start_date} to {end_date}...")
        data = yf.download(ticker, start=start_date, end=end_date)
        if data.empty:
            print(f"Error: No data found for ticker {ticker} in the specified date range.")
            return None
        print("Price data fetched successfully.")
        return data
    except Exception as e:
        print(f"Error fetching price data: {e}")
        return None

def detect_market_regime(prices_list, current_idx, lookback=7):
    """
    Detects market regime: bullish, bearish, or neutral.
    Returns: ('bullish', volatility) or ('bearish', volatility) or ('neutral', volatility)
    """
    if current_idx < lookback:
        return 'neutral', 0.02
    
    recent_prices = prices_list[max(0, current_idx - lookback):current_idx + 1]
    
    # Calculate trend
    price_change = (recent_prices[-1] - recent_prices[0]) / recent_prices[0]
    
    # Calculate volatility
    returns = [(recent_prices[i] - recent_prices[i-1]) / recent_prices[i-1] 
               for i in range(1, len(recent_prices))]
    volatility = (sum(r**2 for r in returns) / len(returns)) ** 0.5 if returns else 0.02
    
    # Determine regime
    if price_change > 0.03:  # Up more than 3%
        return 'bullish', volatility
    elif price_change < -0.03:  # Down more than 3%
        return 'bearish', volatility
    else:
        return 'neutral', volatility


def run_simulation(scores: list[float], price_data: pd.DataFrame):
    """
    Runs an ADAPTIVE trading simulation that performs well in all market conditions.
    
    Features:
    - Market regime detection (bullish/bearish/neutral)
    - Adaptive position sizing based on conditions
    - Dynamic thresholds that adjust to volatility
    - Smart risk management for all scenarios
    
    Args:
        scores: A list of sentiment scores (floats from -1.0 to 1.0).
        price_data: A pandas DataFrame with historical price data.
    """
    print("\n--- Running ADAPTIVE Trading Simulation (All Market Conditions) ---")
    
    # --- BASE Strategy Parameters (will be adjusted dynamically) ---
    initial_cash = 10000.0
    regime_lookback = 7  # Days to determine market regime
    
    # --- Data Alignment ---
    num_days = min(len(scores), len(price_data))
    if num_days == 0:
        print("Cannot run simulation: No overlapping sentiment and price data.")
        return None
    price_data = price_data.head(num_days)
    scores = scores[:num_days]
    
    prices_list = [float(row['Close']) for _, row in price_data.iterrows()]
    
    # --- State Variables ---
    cash = initial_cash
    asset_holdings = 0.0
    portfolio_values = []
    purchase_price = 0
    trailing_stop_price = 0
    peak_price = 0
    current_regime = 'neutral'
    
    # Trading statistics
    num_trades = 0
    winning_trades = 0

    print(f"Initial Cash: ${cash:,.2f}")
    print(f"Strategy: Adaptive to market conditions (bullish/bearish/neutral)")
    print(f"Features: Dynamic thresholds, adaptive position sizing, regime-aware risk management")
    print(f"Simulating over {num_days} trading days...\n")
    
    for i, (date, row) in enumerate(price_data.iterrows()):
        current_price = float(row['Close'])
        score = scores[i]
        action = "HOLD"
        
        # --- DETECT MARKET REGIME ---
        regime, volatility = detect_market_regime(prices_list, i, regime_lookback)
        current_regime = regime
        
        # --- ADAPTIVE PARAMETERS BASED ON MARKET REGIME ---
        if regime == 'bullish':
            # In uptrend: be aggressive, ride winners
            buy_threshold = 0.60
            sell_threshold = -0.25
            max_position_pct = 0.45
            take_profit_pct = 0.08  # Let profits run
            trailing_stop_pct = 0.04
            max_loss_pct = 0.05
            
        elif regime == 'bearish':
            # In downtrend: be defensive, quick exits
            buy_threshold = 0.75  # Only very strong signals
            sell_threshold = -0.15  # Exit fast
            max_position_pct = 0.25  # Smaller positions
            take_profit_pct = 0.04  # Take quick profits
            trailing_stop_pct = 0.03  # Tight stop
            max_loss_pct = 0.03
            
        else:  # neutral
            # In sideways: balanced approach
            buy_threshold = 0.65
            sell_threshold = -0.20
            max_position_pct = 0.35
            take_profit_pct = 0.05
            trailing_stop_pct = 0.035
            max_loss_pct = 0.04
        
        # Adjust for volatility - tighter stops in high volatility
        if volatility > 0.03:
            trailing_stop_pct *= 0.8
            max_loss_pct *= 0.8
        
        # Calculate momentum
        momentum_lookback = 3
        momentum_positive = False
        if i >= momentum_lookback:
            recent_prices = prices_list[i-momentum_lookback:i]
            momentum_positive = current_price > sum(recent_prices) / len(recent_prices)
        
        current_portfolio_value = cash + (asset_holdings * current_price)

        # --- TAKE PROFIT Logic (Priority 1) ---
        if asset_holdings > 0 and purchase_price > 0:
            profit_pct = (current_price - purchase_price) / purchase_price
            if profit_pct >= take_profit_pct:
                cash_from_sale = asset_holdings * current_price
                cash += cash_from_sale
                profit = cash_from_sale - (asset_holdings * purchase_price)
                action = f"TAKE PROFIT [{regime}] (+{profit_pct*100:.1f}%) at ${current_price:,.2f}"
                asset_holdings = 0.0
                purchase_price = 0
                trailing_stop_price = 0
                peak_price = 0
                num_trades += 1
                winning_trades += 1

        # --- HARD STOP-LOSS Logic (Priority 2) ---
        elif asset_holdings > 0 and purchase_price > 0:
            loss_pct = (current_price - purchase_price) / purchase_price
            if loss_pct <= -max_loss_pct:
                cash_from_sale = asset_holdings * current_price
                cash += cash_from_sale
                action = f"STOP-LOSS [{regime}] ({loss_pct*100:+.1f}%) at ${current_price:,.2f}"
                asset_holdings = 0.0
                purchase_price = 0
                trailing_stop_price = 0
                peak_price = 0
                num_trades += 1
        
        # --- TRAILING STOP Logic (Priority 3) ---
        elif asset_holdings > 0 and trailing_stop_price > 0 and current_price < trailing_stop_price:
            cash_from_sale = asset_holdings * current_price
            cash += cash_from_sale
            pnl_pct = (current_price - purchase_price) / purchase_price
            action = f"TRAIL-STOP [{regime}] ({pnl_pct*100:+.1f}%) at ${current_price:,.2f} (stop was ${trailing_stop_price:,.2f})"
            if current_price > purchase_price:
                winning_trades += 1
            asset_holdings = 0.0
            purchase_price = 0
            trailing_stop_price = 0
            peak_price = 0
            num_trades += 1
        
        # --- BUY Logic (Priority 4) ---
        elif score > buy_threshold and asset_holdings == 0:
            # In bullish: buy on good sentiment
            # In bearish: only buy on very strong sentiment + momentum
            # In neutral: balanced approach
            
            if regime == 'bearish':
                strong_signal = score >= 0.80 and momentum_positive
            else:
                strong_signal = score >= buy_threshold and (momentum_positive or score >= 0.75)
            
            if strong_signal:
                # Dynamic position sizing
                sentiment_multiplier = min((score - buy_threshold) / (1.0 - buy_threshold), 1.0)
                min_position_pct = max_position_pct * 0.7
                position_size_pct = min_position_pct + (sentiment_multiplier * (max_position_pct - min_position_pct))
                
                trade_size_cash = current_portfolio_value * position_size_pct
                
                if cash >= trade_size_cash:
                    assets_to_buy = trade_size_cash / current_price
                    asset_holdings += assets_to_buy
                    cash -= trade_size_cash
                    purchase_price = current_price
                    trailing_stop_price = purchase_price * (1 - trailing_stop_pct)
                    peak_price = current_price
                    action = f"BUY [{regime}] {assets_to_buy:.4f} units ({position_size_pct*100:.0f}%) at ${current_price:,.2f}"
        
        # --- SELL Logic (Priority 5) ---
        elif score < sell_threshold and asset_holdings > 0:
            cash_from_sale = asset_holdings * current_price
            cash += cash_from_sale
            pnl_pct = (current_price - purchase_price) / purchase_price
            action = f"SELL [{regime}] Negative sentiment ({pnl_pct*100:+.1f}%) at ${current_price:,.2f}"
            if current_price > purchase_price:
                winning_trades += 1
            asset_holdings = 0.0
            purchase_price = 0
            trailing_stop_price = 0
            peak_price = 0
            num_trades += 1
        
        # --- REGIME CHANGE EXIT Logic (Priority 6) ---
        # Exit if we entered in different regime and now it's worse
        elif asset_holdings > 0 and regime == 'bearish':
            loss_pct = (current_price - purchase_price) / purchase_price
            if loss_pct < -0.02:  # Down 2%+ in bearish regime, exit
                cash_from_sale = asset_holdings * current_price
                cash += cash_from_sale
                action = f"EXIT [regime change to bearish] ({loss_pct*100:+.1f}%) at ${current_price:,.2f}"
                asset_holdings = 0.0
                purchase_price = 0
                trailing_stop_price = 0
                peak_price = 0
                num_trades += 1

        # --- Update Trailing Stop (Dynamic) ---
        if asset_holdings > 0:
            if current_price > peak_price:
                peak_price = current_price
                # Tighten stop as we profit more
                profit_pct = (current_price - purchase_price) / purchase_price
                if profit_pct > 0.05:  # If up 5%+, tighten stop
                    trailing_stop_price = current_price * (1 - trailing_stop_pct * 0.5)
                else:
                    trailing_stop_price = current_price * (1 - trailing_stop_pct)

        # --- Portfolio Valuation ---
        current_portfolio_value = cash + (asset_holdings * current_price)
        portfolio_values.append(current_portfolio_value)
        
        regime_emoji = "🚀" if regime == 'bullish' else "📉" if regime == 'bearish' else "➡️"
        momentum_emoji = "📈" if momentum_positive else "�"
        print(f"{date.date()} | ${current_price:7.2f} | Score:{score:5.2f} {regime_emoji} {momentum_emoji} | {action:<50} | ${current_portfolio_value:,.2f}")

    # --- Performance Calculation ---
    print("\n" + "="*80)
    print("ADAPTIVE STRATEGY PERFORMANCE METRICS")
    print("="*80)
    final_portfolio_value = portfolio_values[-1]
    total_return_pct = ((final_portfolio_value - initial_cash) / initial_cash) * 100
    
    peak = portfolio_values[0]
    max_drawdown = 0
    for value in portfolio_values:
        if value > peak:
            peak = value
        drawdown = (peak - value) / peak
        if drawdown > max_drawdown:
            max_drawdown = drawdown
    
    # Calculate Sharpe Ratio
    returns = [(portfolio_values[i] - portfolio_values[i-1]) / portfolio_values[i-1] 
               for i in range(1, len(portfolio_values))]
    if returns:
        avg_return = sum(returns) / len(returns)
        std_return = (sum((r - avg_return) ** 2 for r in returns) / len(returns)) ** 0.5
        sharpe_ratio = (avg_return / std_return * (252 ** 0.5)) if std_return > 0 else 0
    else:
        sharpe_ratio = 0
    
    win_rate = (winning_trades / num_trades * 100) if num_trades > 0 else 0
            
    print(f"\nPortfolio Performance:")
    print(f"  Initial Value:        ${initial_cash:>10,.2f}")
    print(f"  Final Value:          ${final_portfolio_value:>10,.2f}")
    print(f"  Total Return:         {total_return_pct:>10.2f}%")
    print(f"  Maximum Drawdown:     {max_drawdown:>10.2%}")
    print(f"  Sharpe Ratio:         {sharpe_ratio:>10.2f}")
    
    print(f"\nTrading Statistics:")
    print(f"  Total Trades:         {num_trades:>10}")
    print(f"  Winning Trades:       {winning_trades:>10}")
    print(f"  Win Rate:             {win_rate:>10.1f}%")
    print(f"  Return/Drawdown:      {total_return_pct / (max_drawdown * 100) if max_drawdown > 0 else float('inf'):>10.2f}")
    
    print(f"\nAdaptive Features:")
    print(f"  ✓ Market regime detection (bullish/bearish/neutral)")
    print(f"  ✓ Dynamic thresholds based on conditions")
    print(f"  ✓ Adaptive position sizing (25-45%)")
    print(f"  ✓ Volatility-adjusted risk management")
    print("="*80)
    
    return {
        "total_return_pct": total_return_pct,
        "max_drawdown_pct": max_drawdown * 100,
        "sharpe_ratio": sharpe_ratio,
        "num_trades": num_trades,
        "win_rate": win_rate,
    }

if __name__ == '__main__':
    pass # Main test logic moved to main.py
