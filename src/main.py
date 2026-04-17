import configparser
from components import news_fetcher, sentiment_analyzer, trading_engine

def main():
    """
    Main function to run the LLM trading strategy simulation with real data.
    """
    print("--- Starting LLM-Based Trading Strategy Simulation (Real Data) ---")
    
    # --- 1. Load Configuration ---
    config = configparser.ConfigParser()
    config.read('src/config.ini')
    # Let's use a real stock ticker for this simulation
    ticker = "BTC-USD" 
    start_date = "2026-01-13"
    end_date = "2026-01-28" # A recent 15-day period
    
    print(f"\n[Step 1] Configuration Loaded")
    print(f"Trading Symbol: {ticker}")
    print(f"Backtest Period: {start_date} to {end_date}")

    # --- 2. Fetch Real Price Data ---
    print("\n[Step 2] Fetching Historical Price Data...")
    price_data = trading_engine.fetch_price_data(ticker, start_date, end_date)
    if price_data is None:
        print("Could not fetch price data. Exiting.")
        return
    
    # --- 3. Fetch News ---
    # Note: This currently returns placeholder headlines. To use real news,
    # you must add your NewsAPI key to src/config.ini and uncomment the
    # code inside news_fetcher.py.
    print("\n[Step 3] Fetching News Headlines...")
    headlines = news_fetcher.fetch_news(ticker, start_date, end_date)
    if not headlines:
        print("Could not fetch news headlines. Exiting.")
        return
    
    # --- 4. Analyze Sentiment for Scores ---
    print("\n[Step 4] Analyzing Sentiment with LLM (Scoring V2)...")
    scores = sentiment_analyzer.analyze_headlines_for_scores(headlines)
    if scores is None:
        print("Could not analyze sentiment for headlines. Exiting.")
        return
    print("Sentiment analysis complete.")

    # --- 5. Run Trading Simulation ---
    print("\n[Step 5] Running Backtest Simulation (V2)...")
    trading_engine.run_simulation(scores, price_data)
    
    print("\n--- LLM Trading Strategy Simulation Finished ---")

if __name__ == "__main__":
    main()