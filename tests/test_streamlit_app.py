"""
Tests for the Streamlit application interface.
"""
import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Add the project root to the path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock streamlit before importing the app
sys.modules['streamlit'] = MagicMock()
import streamlit as st

# After mocking streamlit, import the app
import simple_app

class TestStreamlitApp(unittest.TestCase):
    def setUp(self):
        """Set up test environment."""
        # Reset streamlit mock
        st.reset_mock()
        
        # Mock session state
        st.session_state = {}
        
        # Setup default session state values
        st.session_state.user = None
        st.session_state.authenticated = False
        st.session_state.editor_content = ""
        st.session_state.suggestions = None
        st.session_state.selected_language = "python"
    
    @patch('simple_app.AuthManager')
    def test_login_user(self, mock_auth_manager):
        """Test user login functionality."""
        # Configure mock
        mock_auth = MagicMock()
        mock_auth_manager.return_value = mock_auth
        mock_auth.login_user.return_value = True
        
        # Set up test credentials
        username = "testuser"
        password = "password123"
        
        # Call login function
        simple_app.login_user(username, password)
        
        # Verify auth manager was called correctly
        mock_auth.login_user.assert_called_once_with(username, password)
        
        # Verify session state was updated
        self.assertEqual(st.session_state.user, username)
        self.assertTrue(st.session_state.authenticated)
        
    @patch('simple_app.AuthManager')
    def test_login_user_failure(self, mock_auth_manager):
        """Test user login failure."""
        # Configure mock
        mock_auth = MagicMock()
        mock_auth_manager.return_value = mock_auth
        mock_auth.login_user.return_value = False
        
        # Set up test credentials
        username = "testuser"
        password = "wrongpassword"
        
        # Call login function
        simple_app.login_user(username, password)
        
        # Verify auth manager was called correctly
        mock_auth.login_user.assert_called_once_with(username, password)
        
        # Verify session state was not updated
        self.assertNotEqual(st.session_state.user, username)
        self.assertFalse(st.session_state.authenticated)
        
    @patch('simple_app.CodeGenerator')
    def test_get_ai_suggestions(self, mock_code_generator):
        """Test getting AI suggestions."""
        # Set up test data
        st.session_state.editor_content = "def test():\n    pass"
        st.session_state.selected_language = "python"
        user_api_key = "test-api-key"
        
        # Configure mock
        mock_generator = MagicMock()
        mock_code_generator.return_value = mock_generator
        mock_generator.get_suggestion.return_value = "def test_improved():\n    return True"
        
        # Call function
        simple_app.get_ai_suggestions(user_api_key)
        
        # Verify code generator was called correctly
        mock_generator.get_suggestion.assert_called_once()
        
        # Verify session state was updated
        self.assertIsNotNone(st.session_state.suggestions)
        
    @patch('simple_app.CodeGenerator')
    def test_implement_suggestions(self, mock_code_generator):
        """Test implementing suggestions."""
        # Set up test data
        original_code = "def test():\n    pass"
        improved_code = "def test_improved():\n    return True"
        st.session_state.editor_content = original_code
        st.session_state.suggestions = improved_code
        user_api_key = "test-api-key"
        
        # Configure mock
        mock_generator = MagicMock()
        mock_code_generator.return_value = mock_generator
        
        # Call function
        simple_app.implement_suggestions(user_api_key)
        
        # Verify session state was updated
        self.assertEqual(st.session_state.editor_content, improved_code)
        
    def test_register_page_layout(self):
        """Test register page layout."""
        # Call function
        simple_app.register_page()
        
        # Verify streamlit components were created
        st.title.assert_called()
        st.text_input.assert_called()
        
    def test_login_page_layout(self):
        """Test login page layout."""
        # Call function
        simple_app.login_page()
        
        # Verify streamlit components were created
        st.title.assert_called()
        st.text_input.assert_called()
        
    def test_main_app_layout(self):
        """Test main app layout."""
        # Setup authenticated state
        st.session_state.authenticated = True
        st.session_state.user = "testuser"
        
        # Call function
        simple_app.main_app()
        
        # Verify streamlit components were created
        st.title.assert_called()

if __name__ == "__main__":
    unittest.main()
