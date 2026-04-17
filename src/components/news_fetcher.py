import configparser
from eventregistry import EventRegistry, QueryArticlesIter

def get_news_api_key():
    """
    Reads the news API key from the configuration file.
    """
    config = configparser.ConfigParser()
    config.read('src/config.ini')
    return config['news']['api_key']

def fetch_news(symbol: str, start_date: str, end_date: str):
    """
    Fetches news for a given symbol using the newsapi.ai (Event Registry) service.
    
    Args:
        symbol: The trading symbol or keyword to search for (e.g., "BTC" or "Bitcoin").
        start_date: The start date in "YYYY-MM-DD" format.
        end_date: The end date in "YYYY-MM-DD" format.
        
    Returns:
        A list of news headline strings.
    """
    api_key = get_news_api_key()
    
    if api_key == 'YOUR_NEWS_API_KEY_HERE':
        print("Warning: News API key not set. Please get a key from https://newsapi.ai/ and add it to src/config.ini")
        print(f"INFO: Using placeholder news data for {symbol}.")
        # Fallback to placeholder data if no key is provided
        return [
            "Crypto market cap reaches $2 trillion as Bitcoin hits new all-time high.",
            "Ethereum's upcoming network upgrade 'Merge' promises lower transaction fees.",
            "SEC once again delays decision on spot Bitcoin ETF, citing manipulation concerns.",
            "Major retail chain announces it will start accepting Dogecoin as payment.",
            "DeFi platform suffers major exploit, over $50 million in assets stolen.",
            "Venture capital funding for blockchain startups has doubled in the last quarter.",
            "El Salvador's Bitcoin bond issuance is met with skepticism from IMF.",
            "NFT sales volume drops 30% in a month, signaling a cooling market.",
            "New privacy-focused cryptocurrency 'Nyx' launches on mainnet.",
            "Coinbase stock tumbles after reporting lower-than-expected Q3 earnings."
        ]

    try:
        er = EventRegistry(apiKey=api_key)
        
        # newsapi.ai uses 'BTC' for Bitcoin, not 'BTC-USD'
        query_symbol = symbol.split('-')[0] 
        
        q = QueryArticlesIter(
            keywords=query_symbol,
            lang="eng",
            dateStart=start_date,
            dateEnd=end_date
        )
        
        # We limit the number of articles to avoid excessive API usage.
        # Let's aim for one headline per day of the backtest.
        headlines = []
        for art in q.execQuery(er, sortBy="date", maxItems=15):
            headlines.append(art['title'])
            
        if not headlines:
            print(f"Warning: No real news found for '{query_symbol}' on newsapi.ai for the period. Using placeholder data.")
            # Return placeholders if the real query yields no results
            return ["Placeholder: No real news was found for this period."] * 10

        print(f"Successfully fetched {len(headlines)} real news headlines from newsapi.ai.")
        return headlines
        
    except Exception as e:
        print(f"Error fetching real news from newsapi.ai: {e}")
        print("Falling back to placeholder data.")
        return ["Error fetching news, using placeholder."] * 10


if __name__ == '__main__':
    # A simple test to demonstrate the function
    api_key = get_news_api_key()
    print(f"News API Key set: {api_key != 'YOUR_NEWS_API_KEY_HERE'}")
    
    # To test this function directly, you must have a valid key in src/config.ini
    if api_key != 'YOUR_NEWS_API_KEY_HERE':
        headlines = fetch_news("BTC-USD", "2023-01-01", "2023-01-10")
        print("\nFetched Headlines:")
        for i, headline in enumerate(headlines):
            print(f"{i+1}. {headline}")
