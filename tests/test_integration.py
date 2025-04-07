"""
Integration tests for the Low-Code Assistant application.
These tests simulate the full application flow from authentication to code generation.
"""
import os
import sys
import time
import unittest
import tempfile
from unittest.mock import patch, MagicMock

# Add the project root to the path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# We need to mock streamlit before importing the app
sys.modules['streamlit'] = MagicMock()
import streamlit as st

# Import application modules
from utils.auth_utils import AuthManager
from app.simple_generator import CodeGenerator
import simple_app

class TestFullApplicationFlow(unittest.TestCase):
    """Integration test for the full application flow."""
    
    def setUp(self):
        """Set up test environment."""
        # Create a temporary directory for test files
        self.temp_dir = tempfile.TemporaryDirectory()
        
        # Setup a test database
        self.db_path = os.path.join(self.temp_dir.name, 'test.db')
        self.auth_manager = AuthManager(db_path=self.db_path)
        
        # Reset streamlit mock and session state
        st.reset_mock()
        st.session_state = {
            'user': None,
            'authenticated': False,
            'editor_content': '',
            'suggestions': None,
            'selected_language': 'python'
        }
        
        # Test user credentials
        self.username = "testuser"
        self.password = "TestPassword123!"
        self.api_key = "test-api-key-123"
        
        # Register test user
        self.auth_manager.register_user(self.username, self.password)
        self.auth_manager.store_api_key(self.username, self.api_key)
    
    def tearDown(self):
        """Clean up after tests."""
        self.temp_dir.cleanup()
    
    @patch('simple_app.AuthManager')
    @patch('simple_app.CodeGenerator')
    def test_full_application_flow(self, mock_code_generator, mock_auth_manager):
        """Test the complete application flow."""
        # 1. Setup mocks
        mock_auth = MagicMock()
        mock_auth_manager.return_value = mock_auth
        mock_auth.login_user.return_value = True
        mock_auth.get_api_key.return_value = self.api_key
        
        mock_generator = MagicMock()
        mock_code_generator.return_value = mock_generator
        mock_generator.get_suggestion.return_value = "def improved_function():\n    print('This is better code')\n    return True"
        
        # 2. Simulate login
        self.assertFalse(st.session_state.authenticated)
        simple_app.login_user(self.username, self.password)
        self.assertTrue(st.session_state.authenticated)
        self.assertEqual(st.session_state.user, self.username)
        
        # 3. Simulate code entry
        original_code = "def my_function():\n    print('Hello')"
        st.session_state.editor_content = original_code
        
        # 4. Get AI suggestions
        simple_app.get_ai_suggestions()
        mock_generator.get_suggestion.assert_called_once()
        self.assertIsNotNone(st.session_state.suggestions)
        
        suggested_code = st.session_state.suggestions
        self.assertIn("improved_function", suggested_code)
        
        # 5. Implement suggestions
        simple_app.implement_suggestions()
        self.assertEqual(st.session_state.editor_content, suggested_code)
        
        # 6. Simulate logout
        simple_app.logout_user()
        self.assertFalse(st.session_state.authenticated)
        self.assertIsNone(st.session_state.user)
    
    @patch('app.simple_generator.openai.OpenAI')
    def test_code_generator_integration(self, mock_openai):
        """Test the CodeGenerator integration with minimal mocking."""
        # Mock OpenAI API response
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "```python\ndef improved_function(name):\n    \"\"\"Better function with docstring.\"\"\"\n    if not name:\n        return \"Hello, World!\"\n    return f\"Hello, {name}!\"\n```"
        mock_client.chat.completions.create.return_value = mock_response
        
        # Create CodeGenerator with test API key
        code_generator = CodeGenerator(api_key=self.api_key)
        
        # Test code to improve
        code = "def greet(name):\n    return \"Hello, \" + name"
        language = "python"
        
        # Get suggestion
        result = code_generator.get_suggestion(code, language)
        
        # Verify result
        self.assertIsNotNone(result)
        self.assertIn("improved_function", result)
        self.assertIn("docstring", result)
        
        # Verify API call
        mock_client.chat.completions.create.assert_called_once()

class TestErrorHandling(unittest.TestCase):
    """Test application error handling and recovery."""
    
    def setUp(self):
        """Set up test environment."""
        # Reset streamlit mock and session state
        st.reset_mock()
        st.session_state = {
            'user': "testuser",
            'authenticated': True,
            'editor_content': 'def test(): pass',
            'suggestions': None,
            'selected_language': 'python'
        }
    
    @patch('simple_app.CodeGenerator')
    def test_api_error_recovery(self, mock_code_generator):
        """Test recovery from API errors."""
        # Setup mock to raise an exception
        mock_generator = MagicMock()
        mock_code_generator.return_value = mock_generator
        mock_generator.get_suggestion.side_effect = Exception("API Error")
        
        # Try to get suggestions
        simple_app.get_ai_suggestions()
        
        # Verify error was handled and app didn't crash
        self.assertIsNone(st.session_state.suggestions)
        
        # Verify error message was displayed
        self.assertGreaterEqual(st.error.call_count, 1)
    
    @patch('simple_app.AuthManager')
    def test_db_error_recovery(self, mock_auth_manager):
        """Test recovery from database errors."""
        # Setup mock to raise an exception
        mock_auth = MagicMock()
        mock_auth_manager.return_value = mock_auth
        mock_auth.login_user.side_effect = Exception("Database Error")
        
        # Try to login
        simple_app.login_user("testuser", "password")
        
        # Verify app didn't crash and error was handled
        self.assertFalse(st.session_state.authenticated)
        
        # Verify error message was displayed
        self.assertGreaterEqual(st.error.call_count, 1)

if __name__ == "__main__":
    unittest.main()
