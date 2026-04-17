"""
LLM Signal Analyzer - Hybrid Trading System
Uses LLM to interpret technical indicators and make trading decisions
"""

import os
import configparser
from groq import Groq


def load_groq_client():
    """Load Groq API client from config"""
    config = configparser.ConfigParser()
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.ini')
    config.read(config_path)
    
    api_key = config.get('groq', 'api_key')
    model = config.get('trading', 'model', fallback='llama-3.3-70b-versatile')
    
    return Groq(api_key=api_key), model


def analyze_with_llm(signal_data, symbol, current_price, market_context=None):
    """
    Use LLM to analyze technical signals and make trading decision
    
    Args:
        signal_data: Dictionary from generate_trading_signal()
        symbol: Trading symbol (e.g., "BTCUSDT")
        current_price: Current asset price
        market_context: Optional dict with position info, recent performance
        
    Returns:
        Dictionary with LLM decision, confidence, and reasoning
    """
    try:
        client, model = load_groq_client()
        
        # Extract indicator data
        indicators = signal_data['indicators']
        signal = signal_data['signal']
        action = signal_data['action']
        strength = signal_data['strength']
        reasons = signal_data['reasons']
        
        # Build context for LLM
        prompt = f"""You are an expert crypto trading advisor. Analyze these technical indicators and provide a trading recommendation.

ASSET: {symbol}
CURRENT PRICE: ${current_price:,.2f}

TECHNICAL INDICATORS:
- RSI: {indicators['rsi']:.1f} (Oversold <30, Neutral 30-70, Overbought >70)
- Current Price: ${indicators['current_price']:.2f}
- SMA(20): ${indicators['sma_20']:.2f}
- SMA(50): ${indicators['sma_50']:.2f}
- MACD: {indicators['macd']['macd']:.2f}
- MACD Signal: {indicators['macd']['signal']:.2f}
- MACD Histogram: {indicators['macd']['histogram']:.2f}
- Bollinger Upper: ${indicators['bollinger']['upper']:.2f}
- Bollinger Middle: ${indicators['bollinger']['middle']:.2f}
- Bollinger Lower: ${indicators['bollinger']['lower']:.2f}

TECHNICAL SIGNAL SUMMARY:
- Raw Signal: {signal:+.2f} (Range: -1.0 to +1.0)
- Suggested Action: {action}
- Signal Strength: {strength:.1f}%

KEY OBSERVATIONS:
"""
        for i, reason in enumerate(reasons, 1):
            prompt += f"{i}. {reason}\n"
        
        if market_context:
            prompt += f"\nCURRENT POSITION:\n"
            if market_context.get('has_position'):
                prompt += f"- Open position: {market_context.get('side')} at ${market_context.get('entry_price'):.2f}\n"
                prompt += f"- Current P&L: {market_context.get('pnl_pct'):+.1f}%\n"
            else:
                prompt += "- No open position\n"
        
        prompt += """
Based on this analysis, provide your trading recommendation:

1. DECISION: Should we BUY, SELL, or HOLD?
2. CONFIDENCE: Rate your confidence 0-100%
3. REASONING: Explain your decision in 2-3 sentences
4. RISK_LEVEL: Rate the risk as LOW, MEDIUM, or HIGH
5. KEY_FACTOR: What's the most important factor in your decision?

Respond in this EXACT format:
DECISION: [BUY/SELL/HOLD]
CONFIDENCE: [0-100]
REASONING: [Your explanation]
RISK_LEVEL: [LOW/MEDIUM/HIGH]
KEY_FACTOR: [Most important indicator]

Be decisive and practical. Consider:
- Are multiple indicators aligned or conflicting?
- Is the market in a clear trend or ranging?
- Are signals strong enough to overcome trading fees and slippage?
- Does the risk/reward make sense?
"""
        
        # Call LLM
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert crypto trading advisor. Analyze technical indicators and provide clear, actionable trading decisions. Be conservative and prioritize capital preservation."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.3,  # Lower temperature for more consistent decisions
            max_tokens=500
        )
        
        llm_response = response.choices[0].message.content.strip()
        
        # Parse LLM response
        decision = "HOLD"
        confidence = 0
        reasoning = ""
        risk_level = "MEDIUM"
        key_factor = ""
        
        for line in llm_response.split('\n'):
            line = line.strip()
            if line.startswith('DECISION:'):
                decision = line.split(':', 1)[1].strip().upper()
            elif line.startswith('CONFIDENCE:'):
                try:
                    confidence = int(line.split(':', 1)[1].strip().replace('%', ''))
                except:
                    confidence = 50
            elif line.startswith('REASONING:'):
                reasoning = line.split(':', 1)[1].strip()
            elif line.startswith('RISK_LEVEL:'):
                risk_level = line.split(':', 1)[1].strip().upper()
            elif line.startswith('KEY_FACTOR:'):
                key_factor = line.split(':', 1)[1].strip()
        
        return {
            'decision': decision,
            'confidence': confidence,
            'reasoning': reasoning,
            'risk_level': risk_level,
            'key_factor': key_factor,
            'raw_signal': signal,
            'technical_action': action,
            'llm_response': llm_response
        }
        
    except Exception as e:
        print(f"⚠️  LLM analysis failed: {str(e)}")
        # Fallback to technical signal
        return {
            'decision': action,
            'confidence': strength,
            'reasoning': f"LLM unavailable, using technical signal: {action}",
            'risk_level': 'MEDIUM',
            'key_factor': 'Technical indicators',
            'raw_signal': signal,
            'technical_action': action,
            'llm_response': f"Error: {str(e)}"
        }


def get_hybrid_signal(signal_data, symbol, current_price, market_context=None):
    """
    Main function to get hybrid LLM + Technical signal
    
    Args:
        signal_data: Output from generate_trading_signal()
        symbol: Trading symbol
        current_price: Current price
        market_context: Optional position/context info
        
    Returns:
        Dictionary with final decision and all analysis
    """
    # Get LLM analysis
    llm_analysis = analyze_with_llm(signal_data, symbol, current_price, market_context)
    
    # Combine technical and LLM signals
    result = {
        'final_decision': llm_analysis['decision'],
        'confidence': llm_analysis['confidence'],
        'reasoning': llm_analysis['reasoning'],
        'risk_level': llm_analysis['risk_level'],
        'key_factor': llm_analysis['key_factor'],
        'technical_signal': signal_data['signal'],
        'technical_action': signal_data['action'],
        'technical_strength': signal_data['strength'],
        'technical_reasons': signal_data['reasons'],
        'indicators': signal_data['indicators'],
        'llm_agrees': llm_analysis['decision'] == signal_data['action']
    }
    
    return result


if __name__ == '__main__':
    # Test the hybrid system
    from signal_generator import generate_trading_signal
    import random
    
    print("=" * 80)
    print("HYBRID LLM + TECHNICAL SIGNAL ANALYZER TEST")
    print("=" * 80)
    print()
    
    # Generate sample price data (trending up)
    base_price = 100
    prices = [base_price]
    for i in range(100):
        change = random.uniform(-1, 2)  # Slight upward bias
        prices.append(prices[-1] * (1 + change/100))
    
    current_price = prices[-1]
    
    # Get technical signals
    print("📊 Generating technical signals...")
    signal_data = generate_trading_signal(prices)
    
    print(f"Technical Signal: {signal_data['action']} ({signal_data['signal']:+.2f})")
    print(f"Strength: {signal_data['strength']:.1f}%")
    print()
    
    # Get LLM analysis
    print("🤖 Getting LLM analysis...")
    hybrid_result = get_hybrid_signal(signal_data, "BTC-USD", current_price)
    
    print()
    print("=" * 80)
    print("HYBRID DECISION")
    print("=" * 80)
    print(f"Final Decision:     {hybrid_result['final_decision']}")
    print(f"Confidence:         {hybrid_result['confidence']}%")
    print(f"Risk Level:         {hybrid_result['risk_level']}")
    print(f"LLM Agrees w/ Tech: {'✅ Yes' if hybrid_result['llm_agrees'] else '❌ No'}")
    print()
    print(f"Reasoning: {hybrid_result['reasoning']}")
    print()
    print(f"Key Factor: {hybrid_result['key_factor']}")
    print()
    print("Technical vs LLM:")
    print(f"  Technical says: {hybrid_result['technical_action']} (signal: {hybrid_result['technical_signal']:+.2f})")
    print(f"  LLM says:       {hybrid_result['final_decision']} (confidence: {hybrid_result['confidence']}%)")
    print("=" * 80)
