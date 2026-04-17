import configparser
import os
import json
from groq import Groq

def get_groq_config():
    """
    Reads the Groq API key and model from the configuration file.
    """
    config = configparser.ConfigParser()
    config.read('src/config.ini')
    api_key = config['groq']['api_key']
    model = config['trading']['model']
    return api_key, model

def get_sentiment_score(headline: str, model: str, client: Groq):
    """
    Analyzes the sentiment of a headline and returns a numerical score.

    Args:
        headline: The news headline to analyze.
        model: The model identifier to use for the analysis.
        client: An initialized Groq client.

    Returns:
        A float score between -1.0 and 1.0. Defaults to 0.0 on error.
    """
    prompt = f"""
    Analyze the sentiment of the following financial news headline and return a score
    from -1.0 (extremely negative) to 1.0 (extremely positive). Your response must
    be a JSON object with two keys: "score" (a float) and "reason" (a brief justification).

    Headline: "{headline}"
    """
    try:
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=model,
            temperature=0,
            max_tokens=150,
            response_format={"type": "json_object"},
        )
        response_text = chat_completion.choices[0].message.content
        response_json = json.loads(response_text)
        
        score = float(response_json.get("score", 0.0))
        # Clamp the score to be within -1.0 and 1.0
        return max(-1.0, min(1.0, score))
        
    except Exception as e:
        print(f"Error analyzing sentiment score for headline '{headline}': {e}")
        return 0.0 # Default to neutral on any error

def analyze_headlines_for_scores(headlines: list[str]):
    """
    Analyzes a list of headlines and returns their sentiment scores.

    Args:
        headlines: A list of news headline strings.

    Returns:
        A list of sentiment scores (floats).
    """
    api_key, model = get_groq_config()
    
    if api_key == 'YOUR_GROQ_API_KEY_HERE':
        print("Error: Groq API key is not set in src/config.ini")
        # Return a list of neutral scores so the app can run without a key
        return [0.0] * len(headlines)
        
    try:
        client = Groq(api_key=api_key)
    except Exception as e:
        print(f"Error initializing Groq client: {e}")
        return [0.0] * len(headlines)

    scores = []
    for headline in headlines:
        score = get_sentiment_score(headline, model, client)
        scores.append(score)
        print(f'  - Analyzed: "{headline}" -> Score: {score:.2f}')
    
    return scores

if __name__ == '__main__':
    # A simple test to demonstrate the function
    print("--- Testing Sentiment Analyzer (Scoring) ---")
    sample_headlines = [
        "Market soars to new all-time high on positive economic data.",
        "Tech startup files for bankruptcy after failing to secure funding."
    ]
    # This test requires a valid Groq API key in src/config.ini
    scores = analyze_headlines_for_scores(sample_headlines)
    print("\nAnalysis Complete:")
    for i, headline in enumerate(sample_headlines):
        print(f'Headline: "{headline}"\nScore: {scores[i]:.2f}')