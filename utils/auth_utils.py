"""
Authentication utilities for the LLM-Driven Coding Assistant.
Provides user authentication and session management.
"""
import os
import json
import hashlib
import secrets
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

class AuthManager:
    """
    Handles user authentication and session management.
    """
    
    def __init__(self, auth_file_path: Optional[str] = None):
        """
        Initialize the AuthManager.
        
        Args:
            auth_file_path (str, optional): Path to the auth file
        """
        # Set up logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Set auth file path
        if auth_file_path is None:
            # Default to project's auth directory
            auth_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
            os.makedirs(auth_dir, exist_ok=True)
            self.auth_file = os.path.join(auth_dir, "users.json")
        else:
            self.auth_file = auth_file_path
        
        # Initialize users database
        self.users = self.load_users()
        self.sessions = {}
        
    def load_users(self) -> Dict[str, Dict[str, Any]]:
        """Load users from the auth file."""
        if os.path.exists(self.auth_file):
            try:
                with open(self.auth_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                self.logger.error("Error decoding users JSON file. Creating new users database.")
                return {}
        return {}
    
    def save_users(self) -> None:
        """Save users to the auth file."""
        with open(self.auth_file, 'w') as f:
            json.dump(self.users, f, indent=2)
    
    def hash_password(self, password: str) -> str:
        """Hash a password securely."""
        # In a real app, use a better password hashing method like bcrypt
        return hashlib.sha256(password.encode()).hexdigest()
    
    def register_user(self, username: str, password: str, email: str) -> bool:
        """
        Register a new user.
        
        Args:
            username (str): Username to register
            password (str): Password for the user
            email (str): Email for the user
            
        Returns:
            bool: True if registration was successful, False otherwise
        """
        # Check if user already exists
        if username in self.users:
            self.logger.warning(f"User {username} already exists")
            return False
        
        # Create new user
        self.users[username] = {
            "username": username,
            "password_hash": self.hash_password(password),
            "email": email,
            "created_at": datetime.now().isoformat(),
            "settings": {
                "theme": "light",
                "api_keys": {}
            }
        }
        
        # Save users
        self.save_users()
        
        self.logger.info(f"User {username} registered successfully")
        return True
    
    def authenticate(self, username: str, password: str) -> Optional[str]:
        """
        Authenticate a user and return a session token.
        
        Args:
            username (str): Username to authenticate
            password (str): Password to check
            
        Returns:
            Optional[str]: Session token if authentication was successful, None otherwise
        """
        # Check if user exists
        if username not in self.users:
            self.logger.warning(f"Authentication failed: User {username} does not exist")
            return None
        
        # Check password
        if self.users[username]["password_hash"] != self.hash_password(password):
            self.logger.warning(f"Authentication failed: Invalid password for user {username}")
            return None
        
        # Generate session token
        session_token = secrets.token_hex(16)
        
        # Store session
        self.sessions[session_token] = {
            "username": username,
            "created_at": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(days=1)).isoformat()
        }
        
        self.logger.info(f"User {username} authenticated successfully")
        return session_token
    
    def validate_session(self, session_token: str) -> Optional[str]:
        """
        Validate a session token and return the associated username.
        
        Args:
            session_token (str): Session token to validate
            
        Returns:
            Optional[str]: Username if session token is valid, None otherwise
        """
        # Check if session exists
        if session_token not in self.sessions:
            return None
        
        # Check if session has expired
        session = self.sessions[session_token]
        expires_at = datetime.fromisoformat(session["expires_at"])
        if expires_at < datetime.now():
            # Remove expired session
            del self.sessions[session_token]
            return None
        
        # Return username
        return session["username"]
    
    def get_user_data(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Get user data.
        
        Args:
            username (str): Username to get data for
            
        Returns:
            Optional[Dict[str, Any]]: User data if user exists, None otherwise
        """
        # Check if user exists
        if username not in self.users:
            return None
        
        # Return user data (excluding password hash)
        user_data = self.users[username].copy()
        del user_data["password_hash"]
        return user_data
    
    def update_user_settings(self, username: str, settings: Dict[str, Any]) -> bool:
        """
        Update user settings.
        
        Args:
            username (str): Username to update settings for
            settings (Dict[str, Any]): New settings
            
        Returns:
            bool: True if update was successful, False otherwise
        """
        # Check if user exists
        if username not in self.users:
            return False
        
        # Update settings
        self.users[username]["settings"].update(settings)
        
        # Save users
        self.save_users()
        
        return True
    
    def store_api_key(self, username: str, provider: str, api_key: str) -> bool:
        """
        Store an API key for a user.
        
        Args:
            username (str): Username to store API key for
            provider (str): Provider of the API key (e.g., "openai")
            api_key (str): API key to store
            
        Returns:
            bool: True if storage was successful, False otherwise
        """
        # Check if user exists
        if username not in self.users:
            return False
        
        # Store API key (in a real app, encrypt this!)
        self.users[username]["settings"]["api_keys"][provider] = api_key
        
        # Save users
        self.save_users()
        
        return True
    
    def get_api_key(self, username: str, provider: str) -> Optional[str]:
        """
        Get an API key for a user.
        
        Args:
            username (str): Username to get API key for
            provider (str): Provider of the API key (e.g., "openai")
            
        Returns:
            Optional[str]: API key if it exists, None otherwise
        """
        # Check if user exists
        if username not in self.users:
            return None
        
        # Return API key
        return self.users[username]["settings"]["api_keys"].get(provider)
