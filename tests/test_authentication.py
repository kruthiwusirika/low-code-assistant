"""
Unit tests for authentication functionality.
"""
import os
import sys
import unittest
import tempfile
import json
from unittest.mock import patch, MagicMock

# Add the project root to the path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.auth_utils import AuthManager

class TestAuthentication(unittest.TestCase):
    def setUp(self):
        """Set up test environment."""
        self.temp_db_file = tempfile.NamedTemporaryFile(delete=False)
        self.db_path = self.temp_db_file.name
        self.auth_manager = AuthManager(db_path=self.db_path)
        
        # Create a test user
        self.username = "testuser"
        self.password = "TestPassword123!"
        self.auth_manager.register_user(self.username, self.password)
    
    def tearDown(self):
        """Clean up after tests."""
        os.unlink(self.db_path)
    
    def test_register_user(self):
        """Test user registration."""
        # Register a new user
        username = "newuser"
        password = "NewPassword123!"
        result = self.auth_manager.register_user(username, password)
        self.assertTrue(result)
        
        # Try to register the same user again
        result = self.auth_manager.register_user(username, password)
        self.assertFalse(result)  # Should fail
    
    def test_login_user(self):
        """Test user login."""
        # Test valid login
        result = self.auth_manager.login_user(self.username, self.password)
        self.assertTrue(result)
        
        # Test invalid password
        result = self.auth_manager.login_user(self.username, "WrongPassword123!")
        self.assertFalse(result)
        
        # Test non-existent user
        result = self.auth_manager.login_user("nonexistentuser", "password123")
        self.assertFalse(result)
    
    def test_update_password(self):
        """Test password update."""
        # Update password
        new_password = "NewTestPassword123!"
        result = self.auth_manager.update_password(self.username, self.password, new_password)
        self.assertTrue(result)
        
        # Login with new password
        result = self.auth_manager.login_user(self.username, new_password)
        self.assertTrue(result)
        
        # Login with old password should fail
        result = self.auth_manager.login_user(self.username, self.password)
        self.assertFalse(result)
    
    def test_store_api_key(self):
        """Test storing API key."""
        # Store API key
        api_key = "test-api-key-123"
        result = self.auth_manager.store_api_key(self.username, api_key)
        self.assertTrue(result)
        
        # Retrieve API key
        retrieved_key = self.auth_manager.get_api_key(self.username)
        self.assertEqual(retrieved_key, api_key)
    
    def test_delete_user(self):
        """Test user deletion."""
        # Delete user
        result = self.auth_manager.delete_user(self.username)
        self.assertTrue(result)
        
        # Login should fail
        result = self.auth_manager.login_user(self.username, self.password)
        self.assertFalse(result)
        
        # Delete non-existent user
        result = self.auth_manager.delete_user("nonexistentuser")
        self.assertFalse(result)

if __name__ == "__main__":
    unittest.main()
