
import os
from groq import Groq

# --- Configuration ---
# 1. Set your GROQ_API_KEY as an environment variable before running the script.
#    In your terminal: export GROQ_API_KEY='your_api_key_here'
#
# 2. Choose the models you want to compare from the Groq pricing page.
MODELS_TO_COMPARE = [
    "llama-3.1-8b-instant",
    "llama-3.3-70b-versatile",
    "meta-llama/llama-4-scout-17b-16e-instruct",
    "meta-llama/llama-4-maverick-17b-128e-instruct",
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
    "qwen/qwen3-32b",
    "moonshotai/kimi-k2-instruct-0905",
]

# 3. Add the news headlines you want to analyze.
NEWS_HEADLINES = [
    "Company CEO sells 1 million shares in a planned disposition.",
    "The FDA has delayed the approval decision for Company Y's new drug, requesting more data.",
    "Market analysts are divided on the impact of the new government regulations.",
    "Despite a quarterly loss, Company Z's user growth exceeded all expectations, and the stock is up in after-hours trading."
]

# --- Main Script ---

def get_sentiment(client, model, headline):
    """
    Analyzes the sentiment of a single headline using a specified Groq model.
    """
    prompt = f"""
    Analyze the sentiment of the following financial news headline.
    Classify it as "positive", "negative", or "neutral".
    Return only the single word classification.

    Headline: "{headline}"

    Sentiment:
    """
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model=model,
            temperature=0,
            max_tokens=10,
        )
        sentiment = chat_completion.choices[0].message.content.strip().lower()
        return sentiment
    except Exception as e:
        return f"Error: {e}"


def main():
    """
    Main function to compare sentiment analysis across different Groq models.
    """
    try:
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            print("Error: The GROQ_API_KEY environment variable is not set.")
            print("Please set it by running: export GROQ_API_KEY='your_api_key'")
            return
        
        client = Groq(api_key=api_key)
        
    except Exception as e:
        print(f"Error initializing Groq client: {e}")
        return

    results = {model: [] for model in MODELS_TO_COMPARE}

    for model in MODELS_TO_COMPARE:
        print(f"--- Analyzing with model: {model} ---")
        for headline in NEWS_HEADLINES:
            sentiment = get_sentiment(client, model, headline)
            results[model].append(sentiment)
            print(f'  - Headline: "{headline}"')
            print(f'    Sentiment: {sentiment}\n')
        print("-" * (len(model) + 26) + "\n")


    # --- Print Summary Table ---
    print("--- Sentiment Analysis Comparison Summary ---")
    
    # Header
    header = "| Headline No. | " + " | ".join(MODELS_TO_COMPARE) + " |"
    print(header)
    print("|" + "-" * (14) + "|" + ("-" * 18 + "|") * len(MODELS_TO_COMPARE))

    # Rows
    for i, headline in enumerate(NEWS_HEADLINES):
        row_str = f"| Headline #{i+1}  | "
        for model in MODELS_TO_COMPARE:
            sentiment = results[model][i]
            row_str += f"{sentiment:<16} | "
        print(row_str)
        
    print("-" * len(header))
    print("\nFull headlines can be referenced in the detailed analysis above.")


if __name__ == "__main__":
    main()
