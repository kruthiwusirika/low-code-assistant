"""
Unit tests for AI integration and code suggestion functionality.
"""
import os
import sys
import unittest
from unittest.mock import patch, MagicMock, mock_open

# Add the project root to the path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.simple_generator import CodeGenerator

class TestAIIntegration(unittest.TestCase):
    def setUp(self):
        """Set up test environment."""
        self.api_key = "test-api-key-123"
        self.code_generator = CodeGenerator(api_key=self.api_key)
    
    @patch('app.simple_generator.openai.OpenAI')
    def test_get_code_suggestion(self, mock_openai):
        """Test getting code suggestions from the API."""
        # Configure the mock
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        
        # Mock response
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "def improved_function():\n    print('Improved code')\n    return True"
        mock_client.chat.completions.create.return_value = mock_response
        
        # Test code to improve
        code = "def my_function():\n    print('Hello')\n    return True"
        language = "python"
        
        # Get suggestion
        result = self.code_generator.get_suggestion(code, language)
        
        # Verify the result
        self.assertIsNotNone(result)
        self.assertIn("def improved_function", result)
        
        # Verify the API was called correctly
        mock_client.chat.completions.create.assert_called_once()
        args, kwargs = mock_client.chat.completions.create.call_args
        self.assertEqual(kwargs["model"], "gpt-4")  # Assuming GPT-4 is the default model
        self.assertGreaterEqual(len(kwargs["messages"]), 1)
        
    @patch('app.simple_generator.openai.OpenAI')
    def test_api_error_handling(self, mock_openai):
        """Test handling API errors gracefully."""
        # Configure the mock to raise an exception
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        
        # Test code
        code = "def my_function():\n    print('Hello')\n    return True"
        language = "python"
        
        # Get suggestion
        result = self.code_generator.get_suggestion(code, language)
        
        # Verify result is an error message
        self.assertIsNone(result)
        
    @patch('app.simple_generator.openai.OpenAI')
    def test_improve_code_quality(self, mock_openai):
        """Test improving code quality."""
        # Configure the mock
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        
        # Mock response
        mock_response = MagicMock()
        mock_response.choices[0].message.content = """```python
def improved_function(name: str) -> str:
    \"\"\"Return a greeting message.\"\"\"
    if not name:
        raise ValueError("Name cannot be empty")
    return f"Hello, {name}!"
```"""
        mock_client.chat.completions.create.return_value = mock_response
        
        # Test code with quality issues
        code = "def hello(n):\n    return 'Hello, ' + n + '!'\n"
        language = "python"
        quality_focus = "Add type hints and error handling"
        
        # Get improved code
        result = self.code_generator.improve_code_quality(code, language, quality_focus)
        
        # Verify the result
        self.assertIsNotNone(result)
        self.assertIn("def improved_function", result)
        self.assertIn("str) -> str", result)  # Check for type hints
        self.assertIn("ValueError", result)   # Check for error handling
        
        # Verify API call
        mock_client.chat.completions.create.assert_called_once()

if __name__ == "__main__":
    unittest.main()
