"""
Authentication module for the Low-Code Assistant.
Provides login, registration, and session management components.
"""
import streamlit as st
import os
from pathlib import Path
import sys
from typing import Optional, Dict, Any, Callable

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Import user manager
from utils.user_manager import UserManager

def init_session_state():
    """Initialize session state variables for authentication."""
    if "user" not in st.session_state:
        st.session_state.user = None
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "login_error" not in st.session_state:
        st.session_state.login_error = None
    if "register_error" not in st.session_state:
        st.session_state.register_error = None


def login_page():
    """Render the login page."""
    # Initialize UserManager
    user_manager = UserManager()
    
    # Initialize session state
    init_session_state()
    
    # Check session cookie
    if "session_token" in st.session_state and not st.session_state.authenticated:
        user = user_manager.validate_session(st.session_state.session_token)
        if user:
            st.session_state.user = user
            st.session_state.authenticated = True
            # If API key exists in user data, set it in the environment
            if user.get('api_key'):
                os.environ["OPENAI_API_KEY"] = user.get('api_key')
                
    # If already authenticated, don't show login page
    if st.session_state.authenticated:
        return True
    
    # Main container for login/register
    login_container = st.container()
    
    with login_container:
        st.title("Low-Code Assistant")
        
        # Tabs for login and registration
        login_tab, register_tab = st.tabs(["Login", "Register"])
        
        # Login form
        with login_tab:
            st.subheader("Login")
            
            # Check for login errors
            if st.session_state.login_error:
                st.error(st.session_state.login_error)
                st.session_state.login_error = None
            
            # Login form
            with st.form("login_form"):
                username_email = st.text_input("Username or Email")
                password = st.text_input("Password", type="password")
                remember_me = st.checkbox("Remember me")
                submit_login = st.form_submit_button("Login")
                
                if submit_login:
                    if not username_email or not password:
                        st.session_state.login_error = "Username/email and password are required"
                        st.rerun()
                    
                    # Authenticate user
                    user = user_manager.authenticate_user(username_email, password)
                    
                    if user:
                        # Create session
                        session_token = user_manager.create_session(
                            user_id=user['id'],
                            ip_address=None,  # Streamlit doesn't provide this easily
                            user_agent=None   # Streamlit doesn't provide this easily
                        )
                        
                        if session_token:
                            # Store user in session state
                            st.session_state.user = user
                            st.session_state.authenticated = True
                            st.session_state.session_token = session_token
                            
                            # If API key exists in user data, set it in the environment
                            if user.get('api_key'):
                                os.environ["OPENAI_API_KEY"] = user.get('api_key')
                            
                            # Rerun to update UI
                            st.rerun()
                        else:
                            st.session_state.login_error = "Error creating session"
                            st.rerun()
                    else:
                        st.session_state.login_error = "Invalid username/email or password"
                        st.rerun()
        
        # Register form
        with register_tab:
            st.subheader("Register")
            
            # Check for registration errors
            if st.session_state.register_error:
                st.error(st.session_state.register_error)
                st.session_state.register_error = None
            
            # Registration form
            with st.form("register_form"):
                new_username = st.text_input("Username")
                new_email = st.text_input("Email")
                new_password = st.text_input("Password", type="password")
                confirm_password = st.text_input("Confirm Password", type="password")
                submit_register = st.form_submit_button("Register")
                
                if submit_register:
                    if not new_username or not new_email or not new_password:
                        st.session_state.register_error = "All fields are required"
                        st.rerun()
                    
                    if new_password != confirm_password:
                        st.session_state.register_error = "Passwords do not match"
                        st.rerun()
                    
                    # Register user
                    user = user_manager.register_user(
                        username=new_username,
                        email=new_email,
                        password=new_password
                    )
                    
                    if user:
                        # Create session
                        session_token = user_manager.create_session(
                            user_id=user['id'],
                            ip_address=None,
                            user_agent=None
                        )
                        
                        if session_token:
                            # Store user in session state
                            st.session_state.user = user
                            st.session_state.authenticated = True
                            st.session_state.session_token = session_token
                            
                            # Rerun to update UI
                            st.rerun()
                        else:
                            st.session_state.register_error = "Error creating session"
                            st.rerun()
                    else:
                        st.session_state.register_error = "Username or email already exists"
                        st.rerun()
    
    return False


def logout():
    """Log out the current user."""
    if "session_token" in st.session_state:
        user_manager = UserManager()
        user_manager.invalidate_session(st.session_state.session_token)
        del st.session_state.session_token
    
    st.session_state.user = None
    st.session_state.authenticated = False


def require_auth(func: Callable) -> Callable:
    """
    Decorator to require authentication for a page.
    
    Args:
        func (Callable): The function to decorate
        
    Returns:
        Callable: The decorated function
    """
    def wrapper(*args, **kwargs):
        # Initialize session state
        init_session_state()
        
        # If not authenticated, show login page
        if not st.session_state.authenticated:
            login_page()
        else:
            # User is authenticated, call the wrapped function
            return func(*args, **kwargs)
    
    return wrapper


def user_profile():
    """Render the user profile page."""
    # Initialize UserManager
    user_manager = UserManager()
    
    # Initialize session state
    init_session_state()
    
    if not st.session_state.authenticated:
        st.warning("You need to log in to view your profile.")
        return
    
    user = st.session_state.user
    
    st.title("User Profile")
    
    # Display user information
    st.subheader(f"Welcome, {user['username']}!")
    st.write(f"Email: {user['email']}")
    st.write(f"Role: {user['role']}")
    
    # User settings section
    with st.expander("Settings", expanded=True):
        # API Key management
        st.subheader("OpenAI API Key Management")
        
        # Information about API keys
        st.info("""
        You need to provide your own OpenAI API key to use the code generation features. 
        Get your API key from [OpenAI's website](https://platform.openai.com/api-keys).
        """)
        
        # Display current API key if it exists
        if user.get('api_key'):
            st.success("✅ API key is configured")
            mask = user.get('api_key')[:4] + "*" * 8 + user.get('api_key')[-4:] if len(user.get('api_key')) > 12 else "*" * 12
            st.text_input("Your saved OpenAI API Key", 
                         value=mask, 
                         disabled=True,
                         help="For security, only part of your API key is shown.")
            
            # Option to clear API key
            if st.button("Clear API Key", key="clear_api_key_button"):
                updated_api_key = user_manager.update_user_api_key(user['id'], "")
                user['api_key'] = ""
                st.session_state.user = user
                if "OPENAI_API_KEY" in os.environ:
                    del os.environ["OPENAI_API_KEY"]
                st.success("API key cleared successfully!")
                st.rerun()
        
        # Custom API key input
        with st.form("api_key_form"):
            st.write("Enter your OpenAI API key below:")
            custom_api_key = st.text_input("OpenAI API Key", 
                                          type="password",
                                          help="Your API key will be securely stored and never shared.")
            submit_api_key = st.form_submit_button("Save API Key")
            
            if submit_api_key and custom_api_key:
                updated_api_key = user_manager.update_user_api_key(user['id'], custom_api_key)
                if updated_api_key:
                    # Update user in session state
                    user['api_key'] = updated_api_key
                    st.session_state.user = user
                    
                    # Set in environment
                    os.environ["OPENAI_API_KEY"] = updated_api_key
                    
                    st.success("API key saved successfully!")
                else:
                    st.error("Error saving API key")
    
    # Logout button
    if st.button("Logout", key="profile_logout_button"):
        logout()
        st.rerun()
