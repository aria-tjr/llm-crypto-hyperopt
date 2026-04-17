"""
Signal Generator for Trading Bot
Generates buy/sell signals based on technical indicators and price action
"""

import pandas as pd
import numpy as np


def calculate_rsi(prices, period=14):
    """
    Calculate Relative Strength Index (RSI)
    
    Args:
        prices: List or Series of prices
        period: RSI period (default 14)
        
    Returns:
        RSI value (0-100)
    """
    if len(prices) < period + 1:
        return 50  # Neutral if not enough data
    
    prices = pd.Series(prices)
    deltas = prices.diff()
    
    gain = deltas.where(deltas > 0, 0)
    loss = -deltas.where(deltas < 0, 0)
    
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    
    return rsi.iloc[-1] if not pd.isna(rsi.iloc[-1]) else 50


def calculate_sma(prices, period):
    """
    Calculate Simple Moving Average
    
    Args:
        prices: List or Series of prices
        period: SMA period
        
    Returns:
        SMA value
    """
    if len(prices) < period:
        return prices[-1] if prices else 0
    
    return np.mean(prices[-period:])


def calculate_ema(prices, period):
    """
    Calculate Exponential Moving Average
    
    Args:
        prices: List or Series of prices
        period: EMA period
        
    Returns:
        EMA value
    """
    if len(prices) < period:
        return prices[-1] if prices else 0
    
    prices_series = pd.Series(prices)
    ema = prices_series.ewm(span=period, adjust=False).mean()
    return ema.iloc[-1]


def calculate_macd(prices):
    """
    Calculate MACD (Moving Average Convergence Divergence)
    
    Args:
        prices: List or Series of prices
        
    Returns:
        Dictionary with macd, signal, histogram
    """
    if len(prices) < 26:
        return {'macd': 0, 'signal': 0, 'histogram': 0}
    
    ema_12 = calculate_ema(prices, 12)
    ema_26 = calculate_ema(prices, 26)
    macd = ema_12 - ema_26
    
    # Calculate signal line (9-period EMA of MACD)
    prices_series = pd.Series(prices)
    ema_12_series = prices_series.ewm(span=12, adjust=False).mean()
    ema_26_series = prices_series.ewm(span=26, adjust=False).mean()
    macd_series = ema_12_series - ema_26_series
    signal = macd_series.ewm(span=9, adjust=False).mean().iloc[-1]
    
    histogram = macd - signal
    
    return {
        'macd': macd,
        'signal': signal,
        'histogram': histogram
    }


def calculate_bollinger_bands(prices, period=20, std_dev=2):
    """
    Calculate Bollinger Bands
    
    Args:
        prices: List or Series of prices
        period: Period for moving average
        std_dev: Standard deviation multiplier
        
    Returns:
        Dictionary with upper, middle, lower bands
    """
    if len(prices) < period:
        current_price = prices[-1] if prices else 0
        return {
            'upper': current_price,
            'middle': current_price,
            'lower': current_price
        }
    
    prices_array = np.array(prices[-period:])
    middle = np.mean(prices_array)
    std = np.std(prices_array)
    
    upper = middle + (std_dev * std)
    lower = middle - (std_dev * std)
    
    return {
        'upper': upper,
        'middle': middle,
        'lower': lower
    }


def generate_trading_signal(prices, volume=None):
    """
    Generate comprehensive trading signal based on multiple indicators
    
    Args:
        prices: List of recent prices (at least 50 recommended)
        volume: List of recent volumes (optional)
        
    Returns:
        Dictionary with signal (-1 to 1), strength (0-100), and reasons
    """
    if len(prices) < 20:
        return {
            'signal': 0,
            'strength': 0,
            'action': 'HOLD',
            'reasons': ['Insufficient data for analysis']
        }
    
    current_price = prices[-1]
    signals = []
    reasons = []
    
    # 1. RSI Analysis (graduated 0-100 scale)
    rsi = calculate_rsi(prices, 14)
    if rsi < 30:
        rsi_signal = (30 - rsi) / 30  # 0.0 to 1.0 (stronger as RSI approaches 0)
        signals.append(rsi_signal)
        reasons.append(f"RSI oversold ({rsi:.1f})")
    elif rsi > 70:
        rsi_signal = -(rsi - 70) / 30  # -1.0 to 0.0 (stronger as RSI approaches 100)
        signals.append(rsi_signal)
        reasons.append(f"RSI overbought ({rsi:.1f})")
    else:
        # Graduated signal even in neutral zone
        rsi_signal = (rsi - 50) / 50  # -0.4 to +0.4 in 30-70 range
        signals.append(rsi_signal * 0.3)  # Dampen neutral zone signals
        reasons.append(f"RSI neutral ({rsi:.1f})")
    
    # 2. Moving Average Cross (graduated based on distance)
    sma_20 = calculate_sma(prices, 20)
    sma_50 = calculate_sma(prices, 50)
    
    # Calculate distance from MA as percentage
    ma_distance_20 = (current_price - sma_20) / sma_20
    ma_distance_50 = (current_price - sma_50) / sma_50
    
    if current_price > sma_20 > sma_50:
        # Stronger signal if further above MAs
        ma_signal = min((ma_distance_20 + ma_distance_50) * 10, 1.0)
        signals.append(ma_signal)
        reasons.append("Price above MA(20) & MA(50)")
    elif current_price < sma_20 < sma_50:
        # Stronger signal if further below MAs
        ma_signal = max((ma_distance_20 + ma_distance_50) * 10, -1.0)
        signals.append(ma_signal)
        reasons.append("Price below MA(20) & MA(50)")
    else:
        # Graduated signal based on distance from nearest MA
        ma_signal = ma_distance_20 * 2  # Scale to -0.2 to +0.2 typical range
        signals.append(max(min(ma_signal, 1.0), -1.0))
        reasons.append("MA cross neutral")
    
    # 3. MACD (graduated based on histogram strength)
    macd_data = calculate_macd(prices)
    # Normalize histogram to -1 to 1 range (typical histogram is small)
    macd_signal = np.tanh(macd_data['histogram'] * 2)  # tanh keeps it in -1 to 1
    signals.append(macd_signal)
    
    if macd_data['histogram'] > 0.001:
        reasons.append(f"MACD bullish ({macd_data['histogram']:.2f})")
    elif macd_data['histogram'] < -0.001:
        reasons.append(f"MACD bearish ({macd_data['histogram']:.2f})")
    else:
        reasons.append("MACD neutral")
    
    # 4. Bollinger Bands (graduated based on distance)
    bb = calculate_bollinger_bands(prices, 20, 2)
    bb_width = bb['upper'] - bb['lower']
    
    if current_price < bb['lower']:
        # Stronger signal if further below lower band
        distance_below = (bb['lower'] - current_price) / bb_width
        bb_signal = min(distance_below * 2, 1.0)
        signals.append(bb_signal)
        reasons.append("Price below Bollinger lower band")
    elif current_price > bb['upper']:
        # Stronger signal if further above upper band
        distance_above = (current_price - bb['upper']) / bb_width
        bb_signal = -min(distance_above * 2, 1.0)
        signals.append(bb_signal)
        reasons.append("Price above Bollinger upper band")
    else:
        # Graduated signal based on position within bands
        position = (current_price - bb['middle']) / (bb_width / 2)
        signals.append(position * 0.3)  # Dampen within-band signals
        reasons.append("Price within Bollinger bands")
    
    # 5. Price Momentum (graduated based on strength)
    if len(prices) >= 10:
        momentum = (prices[-1] - prices[-10]) / prices[-10]
        # Normalize momentum: 5% = signal of 1.0, scales linearly
        momentum_signal = np.tanh(momentum * 10)  # tanh keeps in -1 to 1
        signals.append(momentum_signal)
        
        if momentum > 0.05:
            reasons.append(f"Strong upward momentum ({momentum*100:.1f}%)")
        elif momentum < -0.05:
            reasons.append(f"Strong downward momentum ({momentum*100:.1f}%)")
        else:
            reasons.append(f"Weak momentum ({momentum*100:.1f}%)")
    
    # Calculate final signal (average of all signals)
    final_signal = np.mean(signals)
    strength = abs(final_signal) * 100
    
    # Determine action
    if final_signal > 0.3:
        action = 'BUY'
    elif final_signal < -0.3:
        action = 'SELL'
    else:
        action = 'HOLD'
    
    return {
        'signal': final_signal,
        'strength': strength,
        'action': action,
        'reasons': reasons,
        'indicators': {
            'rsi': rsi,
            'sma_20': sma_20,
            'sma_50': sma_50,
            'macd': macd_data,
            'bollinger': bb,
            'current_price': current_price
        }
    }


if __name__ == '__main__':
    # Test with sample data
    import random
    
    # Generate sample price data
    base_price = 100
    prices = [base_price]
    for i in range(100):
        change = random.uniform(-2, 2)
        prices.append(prices[-1] * (1 + change/100))
    
    signal = generate_trading_signal(prices)
    
    print("=" * 60)
    print("SIGNAL GENERATOR TEST")
    print("=" * 60)
    print(f"Action: {signal['action']}")
    print(f"Signal: {signal['signal']:.2f}")
    print(f"Strength: {signal['strength']:.1f}%")
    print(f"\nReasons:")
    for reason in signal['reasons']:
        print(f"  - {reason}")
    print(f"\nIndicators:")
    print(f"  RSI: {signal['indicators']['rsi']:.1f}")
    print(f"  Current Price: ${signal['indicators']['current_price']:.2f}")
    print(f"  SMA(20): ${signal['indicators']['sma_20']:.2f}")
    print(f"  SMA(50): ${signal['indicators']['sma_50']:.2f}")
