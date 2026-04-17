import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add the src directory to the Python path to allow imports of our components
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.components import sentiment_analyzer

class TestSentimentAnalyzer(unittest.TestCase):

    @patch('src.components.sentiment_analyzer.Groq')
    def test_get_sentiment_positive(self, MockGroq):
        """
        Tests if the get_sentiment function correctly handles a 'positive' response.
        """
        # --- Setup the Mock ---
        # Mock the entire Groq client and its chain of methods/attributes
        mock_completion = MagicMock()
        mock_completion.choices[0].message.content = "positive"
        
        mock_client = MockGroq.return_value
        mock_client.chat.completions.create.return_value = mock_completion
        
        # --- Call the function ---
        headline = "This is a great news headline."
        model = "test-model"
        sentiment = sentiment_analyzer.get_sentiment(headline, model, mock_client)
        
        # --- Assert ---
        self.assertEqual(sentiment, "positive")
        # Verify that the mocked method was called correctly
        mock_client.chat.completions.create.assert_called_once()

    @patch('src.components.sentiment_analyzer.Groq')
    def test_get_sentiment_unexpected_output(self, MockGroq):
        """
        Tests if the function handles unexpected (non-standard) output from the LLM
        and defaults to 'neutral'.
        """
        # --- Setup the Mock ---
        mock_completion = MagicMock()
        # Simulate the model returning a sentence instead of a single word
        mock_completion.choices[0].message.content = "This headline seems positive."
        
        mock_client = MockGroq.return_value
        mock_client.chat.completions.create.return_value = mock_completion
        
        # --- Call the function ---
        headline = "This is another headline."
        model = "test-model"
        sentiment = sentiment_analyzer.get_sentiment(headline, model, mock_client)
        
        # --- Assert ---
        # It should default to 'neutral' as a safe fallback
        self.assertEqual(sentiment, "neutral")

    @patch('src.components.sentiment_analyzer.Groq')
    def test_get_sentiment_api_error(self, MockGroq):
        """

        Tests if the function returns 'error' when the API call raises an exception.
        """
        # --- Setup the Mock ---
        # Configure the mock to raise an exception when called
        mock_client = MockGroq.return_value
        mock_client.chat.completions.create.side_effect = Exception("API Connection Failed")
        
        # --- Call the function ---
        headline = "This headline will cause an error."
        model = "test-model"
        sentiment = sentiment_analyzer.get_sentiment(headline, model, mock_client)
        
        # --- Assert ---
        self.assertEqual(sentiment, "error")

if __name__ == '__main__':
    unittest.main()
