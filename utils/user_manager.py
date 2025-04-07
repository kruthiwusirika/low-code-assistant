"""
User Management module for the Low-Code Assistant.
Handles user authentication, registration, and session management.
"""
import os
import json
import sqlite3
import hashlib
import secrets
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple

class UserManager:
    """
    Manages user accounts, authentication, and sessions for the Low-Code Assistant.
    """
    
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        """Implement singleton pattern."""
        if cls._instance is None:
            cls._instance = super(UserManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize the UserManager.
        
        Args:
            db_path (str, optional): Path to the SQLite database file
        """
        # Only initialize once (singleton pattern)
        if hasattr(self, '_initialized') and self._initialized:
            return
            
        # Set up logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Set database path
        if db_path is None:
            # Default to project's data directory
            data_dir = Path(__file__).parent.parent / "data"
            data_dir.mkdir(exist_ok=True)
            self.db_path = str(data_dir / "users.db")
        else:
            self.db_path = db_path
        
        # Initialize session store
        self.sessions = {}
        
        # Initialize database
        self._initialize_db()
        
        # Flag as initialized
        self._initialized = True
    
    def _initialize_db(self) -> None:
        """Initialize the database schema if it doesn't exist."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create users table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                created_at TEXT NOT NULL,
                last_login TEXT,
                is_active BOOLEAN NOT NULL DEFAULT 1,
                role TEXT DEFAULT 'user',
                api_key TEXT
            )
            ''')
            
            # Create sessions table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                session_token TEXT UNIQUE NOT NULL,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                ip_address TEXT,
                user_agent TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
            ''')
            
            # Create user_settings table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                setting_key TEXT NOT NULL,
                setting_value TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id),
                UNIQUE(user_id, setting_key)
            )
            ''')
            
            # Create an admin user if no users exist
            cursor.execute('SELECT COUNT(*) FROM users')
            if cursor.fetchone()[0] == 0:
                self._create_default_admin()
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"Database initialized: {self.db_path}")
        except Exception as e:
            self.logger.error(f"Error initializing database: {str(e)}")
            raise
    
    def _create_default_admin(self) -> None:
        """Create a default admin user."""
        try:
            # Generate a random password for the admin
            admin_password = secrets.token_urlsafe(12)
            
            # Create the admin user
            self.register_user(
                username="admin",
                email="admin@lowcodeassistant.local",
                password=admin_password,
                role="admin"
            )
            
            # Log the credentials for first-time setup
            self.logger.info(f"Created default admin user:")
            self.logger.info(f"Username: admin")
            self.logger.info(f"Password: {admin_password}")
            self.logger.info(f"Please change this password immediately after first login!")
        except Exception as e:
            self.logger.error(f"Error creating default admin: {str(e)}")
    
    def _hash_password(self, password: str, salt: Optional[str] = None) -> Tuple[str, str]:
        """
        Hash a password with a random salt.
        
        Args:
            password (str): The password to hash
            salt (str, optional): Salt to use, generates new one if None
            
        Returns:
            Tuple[str, str]: (password_hash, salt)
        """
        if salt is None:
            salt = secrets.token_hex(16)
        
        # Hash the password with the salt
        password_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000
        ).hex()
        
        return password_hash, salt
    
    def register_user(self, username: str, email: str, password: str, role: str = "user") -> Optional[Dict[str, Any]]:
        """
        Register a new user.
        
        Args:
            username (str): Username
            email (str): Email address
            password (str): Password
            role (str, optional): User role (default: "user")
            
        Returns:
            Optional[Dict[str, Any]]: User info if registration successful, None if failed
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if username or email already exists
            cursor.execute('SELECT id FROM users WHERE username = ? OR email = ?', 
                          (username, email))
            if cursor.fetchone():
                conn.close()
                self.logger.warning(f"Registration failed: Username or email already exists")
                return None
            
            # Hash the password
            password_hash, salt = self._hash_password(password)
            
            # Insert the new user
            cursor.execute('''
            INSERT INTO users (username, email, password_hash, salt, created_at, role)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (username, email, password_hash, salt, datetime.now().isoformat(), role))
            
            # Get the new user ID
            user_id = cursor.lastrowid
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"User registered: {username}")
            
            return {
                'id': user_id,
                'username': username,
                'email': email,
                'role': role,
                'created_at': datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Error registering user: {str(e)}")
            return None
    
    def authenticate_user(self, username_or_email: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Authenticate a user.
        
        Args:
            username_or_email (str): Username or email
            password (str): Password
            
        Returns:
            Optional[Dict[str, Any]]: User info if authentication successful, None if failed
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get the user
            cursor.execute('''
            SELECT id, username, email, password_hash, salt, role, api_key
            FROM users
            WHERE (username = ? OR email = ?) AND is_active = 1
            ''', (username_or_email, username_or_email))
            
            row = cursor.fetchone()
            if not row:
                conn.close()
                self.logger.warning(f"Authentication failed: User not found or inactive")
                return None
            
            user_id, username, email, stored_hash, salt, role, api_key = row
            
            # Hash the provided password with the stored salt
            password_hash, _ = self._hash_password(password, salt)
            
            # Check if the hashes match
            if password_hash != stored_hash:
                conn.close()
                self.logger.warning(f"Authentication failed: Incorrect password for {username}")
                return None
            
            # Update last login timestamp
            cursor.execute('''
            UPDATE users SET last_login = ? WHERE id = ?
            ''', (datetime.now().isoformat(), user_id))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"User authenticated: {username}")
            
            return {
                'id': user_id,
                'username': username,
                'email': email,
                'role': role,
                'api_key': api_key
            }
        except Exception as e:
            self.logger.error(f"Error authenticating user: {str(e)}")
            return None
    
    def create_session(self, user_id: int, ip_address: Optional[str] = None, user_agent: Optional[str] = None) -> Optional[str]:
        """
        Create a new session for a user.
        
        Args:
            user_id (int): User ID
            ip_address (str, optional): Client IP address
            user_agent (str, optional): Client user agent
            
        Returns:
            Optional[str]: Session token if successful, None if failed
        """
        try:
            # Generate a unique session token
            session_token = secrets.token_urlsafe(32)
            
            # Set expiration (24 hours from now)
            created_at = datetime.now()
            expires_at = created_at + timedelta(hours=24)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Store the session
            cursor.execute('''
            INSERT INTO sessions (user_id, session_token, created_at, expires_at, ip_address, user_agent)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, session_token, created_at.isoformat(), expires_at.isoformat(), 
                  ip_address, user_agent))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"Session created for user ID: {user_id}")
            
            return session_token
        except Exception as e:
            self.logger.error(f"Error creating session: {str(e)}")
            return None
    
    def validate_session(self, session_token: str) -> Optional[Dict[str, Any]]:
        """
        Validate a session token and get the associated user.
        
        Args:
            session_token (str): Session token
            
        Returns:
            Optional[Dict[str, Any]]: User info if session valid, None if invalid or expired
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get the session
            cursor.execute('''
            SELECT s.user_id, s.expires_at, u.username, u.email, u.role, u.api_key
            FROM sessions s
            JOIN users u ON s.user_id = u.id
            WHERE s.session_token = ? AND u.is_active = 1
            ''', (session_token,))
            
            row = cursor.fetchone()
            if not row:
                conn.close()
                return None
            
            user_id, expires_at_str, username, email, role, api_key = row
            
            # Check if session is expired
            expires_at = datetime.fromisoformat(expires_at_str)
            if expires_at < datetime.now():
                # Delete expired session
                cursor.execute('DELETE FROM sessions WHERE session_token = ?', (session_token,))
                conn.commit()
                conn.close()
                return None
            
            conn.close()
            
            return {
                'id': user_id,
                'username': username,
                'email': email,
                'role': role,
                'api_key': api_key,
                'session_token': session_token
            }
        except Exception as e:
            self.logger.error(f"Error validating session: {str(e)}")
            return None
    
    def invalidate_session(self, session_token: str) -> bool:
        """
        Invalidate a session (logout).
        
        Args:
            session_token (str): Session token
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Delete the session
            cursor.execute('DELETE FROM sessions WHERE session_token = ?', (session_token,))
            
            result = cursor.rowcount > 0
            
            conn.commit()
            conn.close()
            
            if result:
                self.logger.info(f"Session invalidated: {session_token[:8]}...")
            
            return result
        except Exception as e:
            self.logger.error(f"Error invalidating session: {str(e)}")
            return False
    
    def update_user_setting(self, user_id: int, key: str, value: str) -> bool:
        """
        Update a user setting.
        
        Args:
            user_id (int): User ID
            key (str): Setting key
            value (str): Setting value
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Insert or update the setting
            cursor.execute('''
            INSERT INTO user_settings (user_id, setting_key, setting_value)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id, setting_key) 
            DO UPDATE SET setting_value = ?
            ''', (user_id, key, value, value))
            
            conn.commit()
            conn.close()
            
            return True
        except Exception as e:
            self.logger.error(f"Error updating user setting: {str(e)}")
            return False
    
    def get_user_setting(self, user_id: int, key: str) -> Optional[str]:
        """
        Get a user setting.
        
        Args:
            user_id (int): User ID
            key (str): Setting key
            
        Returns:
            Optional[str]: Setting value if found, None otherwise
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get the setting
            cursor.execute('''
            SELECT setting_value FROM user_settings
            WHERE user_id = ? AND setting_key = ?
            ''', (user_id, key))
            
            row = cursor.fetchone()
            
            conn.close()
            
            return row[0] if row else None
        except Exception as e:
            self.logger.error(f"Error getting user setting: {str(e)}")
            return None
    
    def get_user_settings(self, user_id: int) -> Dict[str, str]:
        """
        Get all settings for a user.
        
        Args:
            user_id (int): User ID
            
        Returns:
            Dict[str, str]: Dictionary of settings (key-value pairs)
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get all settings for the user
            cursor.execute('''
            SELECT setting_key, setting_value FROM user_settings
            WHERE user_id = ?
            ''', (user_id,))
            
            settings = {row[0]: row[1] for row in cursor.fetchall()}
            
            conn.close()
            
            return settings
        except Exception as e:
            self.logger.error(f"Error getting user settings: {str(e)}")
            return {}
    
    def update_user_api_key(self, user_id: int, api_key: Optional[str] = None) -> Optional[str]:
        """
        Update a user's API key.
        
        Args:
            user_id (int): User ID
            api_key (str, optional): New API key, generates one if None
            
        Returns:
            Optional[str]: New API key if successful, None otherwise
        """
        try:
            # Generate API key if not provided
            if api_key is None:
                api_key = secrets.token_urlsafe(32)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Update the API key
            cursor.execute('''
            UPDATE users SET api_key = ? WHERE id = ?
            ''', (api_key, user_id))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"API key updated for user ID: {user_id}")
            
            return api_key
        except Exception as e:
            self.logger.error(f"Error updating API key: {str(e)}")
            return None
