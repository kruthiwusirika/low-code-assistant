"""
LLM-Driven Coding Assistant

A web application that uses LLMs (both API-based and open-source) to provide coding assistance,
auto-completions, and "explain code" functionalities.
"""
import os
import sys
import time
import logging
import streamlit as st
from typing import Dict, Any, List, Optional

# Import custom modules
from app.model_manager import ModelManager
from app.code_editor import CodeEditor
from app.fine_tuning import GitHubRepoFetcher, ModelFineTuner, fine_tune_on_repositories
from utils.auth_utils import AuthManager

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Check for required libraries
def check_dependencies():
    """Check if optional dependencies are installed"""
    missing = []
    try:
        import torch
    except ImportError:
        missing.append("torch")
    
    try:
        import transformers
    except ImportError:
        missing.append("transformers")
        
    try:
        import datasets
    except ImportError:
        missing.append("datasets")
    
    try:
        import peft
    except ImportError:
        missing.append("peft")
        
    return missing

# App title and configuration
st.set_page_config(
    page_title="LLM-Driven Coding Assistant",
    page_icon="💻",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state variables
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    
if "user" not in st.session_state:
    st.session_state.user = None
    
if "model_manager" not in st.session_state:
    st.session_state.model_manager = None
    
if "api_key" not in st.session_state:
    st.session_state.api_key = ""
    
if "model_type" not in st.session_state:
    st.session_state.model_type = "api"
    
if "selected_model" not in st.session_state:
    st.session_state.selected_model = "openai"

# Authentication functions
def register_user(username: str, password: str) -> bool:
    """Register a new user"""
    auth_manager = AuthManager()
    return auth_manager.register_user(username, password)

def login_user(username: str, password: str) -> bool:
    """Log in an existing user"""
    auth_manager = AuthManager()
    if auth_manager.login_user(username, password):
        st.session_state.authenticated = True
        st.session_state.user = username
        
        # Load API key if available
        api_key = auth_manager.get_api_key(username)
        if api_key:
            st.session_state.api_key = api_key
            
        return True
    return False

def logout_user():
    """Log out the current user"""
    st.session_state.authenticated = False
    st.session_state.user = None
    st.session_state.api_key = ""
    st.session_state.model_manager = None

def store_api_key(username: str, api_key: str) -> bool:
    """Store a user's API key"""
    auth_manager = AuthManager()
    return auth_manager.store_api_key(username, api_key)

# Model management functions
def initialize_model_manager() -> ModelManager:
    """Initialize the model manager"""
    if st.session_state.model_manager is None:
        st.session_state.model_manager = ModelManager()
        
    # Configure the model manager with API key if available
    if st.session_state.api_key and st.session_state.model_type == "api":
        st.session_state.model_manager.use_api_model(
            api_name=st.session_state.selected_model,
            api_key=st.session_state.api_key
        )
    elif st.session_state.model_type == "local":
        st.session_state.model_manager.use_local_model(
            model_name=st.session_state.selected_model
        )
        
    return st.session_state.model_manager

def get_ai_suggestions(editor: CodeEditor):
    """Get AI suggestions for the code in the editor"""
    code = editor.get_content()
    language = editor.get_language()
    
    if not code:
        st.warning("Please enter some code first")
        return
        
    # Initialize model manager
    model_manager = initialize_model_manager()
    
    # Check if model is ready
    if (st.session_state.model_type == "api" and not st.session_state.api_key) or \
       (st.session_state.model_type == "local" and not model_manager.is_local_model_available(st.session_state.selected_model)):
        st.error("Model not available. Please configure the model settings.")
        return
        
    try:
        with st.spinner("Generating suggestions..."):
            suggestions = model_manager.get_code_suggestion(
                code=code,
                language=language,
                instruction="Improve this code. Focus on performance, readability, and best practices."
            )
            
        if suggestions:
            editor.set_suggestions(suggestions)
        else:
            st.error("Failed to generate suggestions")
            
    except Exception as e:
        st.error(f"Error generating suggestions: {str(e)}")

def explain_code(editor: CodeEditor):
    """Generate an explanation for the code"""
    code = editor.get_content()
    language = editor.get_language()
    
    if not code:
        st.warning("Please enter some code first")
        return
        
    # Initialize model manager
    model_manager = initialize_model_manager()
    
    try:
        with st.spinner("Analyzing code..."):
            explanation = model_manager.get_code_suggestion(
                code=code,
                language=language,
                instruction="Explain this code in detail. Describe what it does, how it works, and any notable patterns or algorithms used."
            )
            
        if explanation:
            st.subheader("Code Explanation")
            st.markdown(explanation)
        else:
            st.error("Failed to generate explanation")
            
    except Exception as e:
        st.error(f"Error explaining code: {str(e)}")

# Page rendering functions
def render_login_page():
    """Render the login page"""
    st.title("LLM-Driven Coding Assistant")
    
    # Center the login form
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        tab1, tab2 = st.tabs(["Login", "Register"])
        
        with tab1:  # Login tab
            st.subheader("Login")
            username = st.text_input("Username", key="login_username")
            password = st.text_input("Password", type="password", key="login_password")
            
            if st.button("Login", key="login_button"):
                if login_user(username, password):
                    st.success("Login successful")
                    st.experimental_rerun()
                else:
                    st.error("Invalid username or password")
        
        with tab2:  # Register tab
            st.subheader("Register")
            new_username = st.text_input("Username", key="register_username")
            new_password = st.text_input("Password", type="password", key="register_password")
            confirm_password = st.text_input("Confirm Password", type="password", key="confirm_password")
            
            if st.button("Register", key="register_button"):
                if new_password != confirm_password:
                    st.error("Passwords do not match")
                else:
                    if register_user(new_username, new_password):
                        st.success("Registration successful")
                        # Auto-login
                        login_user(new_username, new_password)
                        st.experimental_rerun()
                    else:
                        st.error("Username already exists")

def render_sidebar():
    """Render the sidebar"""
    st.sidebar.title("LLM Coding Assistant")
    
    if st.session_state.authenticated:
        st.sidebar.success(f"Logged in as: {st.session_state.user}")
        
        # Model settings
        st.sidebar.subheader("Model Settings")
        
        # Model type selection
        model_type = st.sidebar.radio(
            "Model Type",
            ["API-based", "Local"],
            index=0 if st.session_state.model_type == "api" else 1,
            key="model_type_radio"
        )
        st.session_state.model_type = "api" if model_type == "API-based" else "local"
        
        # API key input for API-based models
        if st.session_state.model_type == "api":
            available_apis = ["OpenAI", "Anthropic", "Google"]
            selected_api = st.sidebar.selectbox(
                "API Provider",
                available_apis,
                index=0,
                key="api_provider_select"
            )
            st.session_state.selected_model = selected_api.lower()
            
            api_key = st.sidebar.text_input(
                f"{selected_api} API Key",
                type="password",
                value=st.session_state.api_key,
                key="api_key_input"
            )
            
            if api_key != st.session_state.api_key:
                st.session_state.api_key = api_key
                
                # Save the API key if user is logged in
                if st.session_state.authenticated and st.session_state.user:
                    store_api_key(st.session_state.user, api_key)
                    
                # Reset model manager to use new key
                st.session_state.model_manager = None
        
        # Local model selection
        else:
            # Check if required libraries are installed
            missing = check_dependencies()
            if missing:
                st.sidebar.warning(f"Missing libraries for local models: {', '.join(missing)}")
                st.sidebar.info("Install these libraries to use local models.")
            else:
                # Get available local models
                model_manager = initialize_model_manager()
                available_models = model_manager.get_available_models()
                
                if available_models and "local" in available_models:
                    local_models = available_models["local"]
                    if local_models:
                        selected_model = st.sidebar.selectbox(
                            "Local Model",
                            local_models,
                            index=0,
                            key="local_model_select"
                        )
                        st.session_state.selected_model = selected_model
                        
                        # Check if model is available locally
                        is_available = model_manager.is_local_model_available(selected_model)
                        
                        if not is_available:
                            st.sidebar.warning(f"Model '{selected_model}' not available locally.")
                            st.sidebar.info("You need to download or fine-tune this model first.")
                    else:
                        st.sidebar.info("No local models configured.")
        
        # Fine-tuning section
        st.sidebar.subheader("Model Fine-tuning")
        
        # Check if required libraries are installed
        missing_for_tuning = check_dependencies()
        if missing_for_tuning:
            st.sidebar.warning(f"Missing libraries for fine-tuning: {', '.join(missing_for_tuning)}")
        else:
            # Fine-tuning form in an expander
            with st.sidebar.expander("Fine-tune on GitHub Repos"):
                base_model = st.text_input(
                    "Base Model ID",
                    value="codellama/CodeLlama-7b-Instruct-hf",
                    help="Hugging Face model ID to fine-tune"
                )
                
                language = st.selectbox(
                    "Programming Language",
                    ["python", "javascript", "typescript", "java", "c++", "go", "rust"],
                    index=0
                )
                
                num_repos = st.slider(
                    "Number of Repositories",
                    min_value=1,
                    max_value=10,
                    value=3
                )
                
                github_token = st.text_input(
                    "GitHub Token (Optional)",
                    type="password",
                    help="GitHub token for higher API rate limits"
                )
                
                output_dir = st.text_input(
                    "Output Directory",
                    value="./fine_tuned_models"
                )
                
                if st.button("Start Fine-tuning"):
                    # Check for required model libraries
                    if not missing_for_tuning:
                        with st.spinner("Fine-tuning model..."):
                            # Create output directory if it doesn't exist
                            os.makedirs(output_dir, exist_ok=True)
                            
                            # Start fine-tuning process
                            success = fine_tune_on_repositories(
                                base_model_name=base_model,
                                language=language,
                                output_dir=output_dir,
                                num_repos=num_repos,
                                github_token=github_token if github_token else None
                            )
                            
                            if success:
                                st.success(f"Fine-tuning completed! Model saved to {output_dir}")
                            else:
                                st.error("Fine-tuning failed. Check the logs for details.")
                    else:
                        st.error(f"Missing required libraries: {', '.join(missing_for_tuning)}")
        
        # Logout button
        if st.sidebar.button("Logout"):
            logout_user()
            st.experimental_rerun()

def render_main_app():
    """Render the main application"""
    st.title("LLM-Driven Coding Assistant")
    
    # Create code editor
    editor = CodeEditor(key_prefix="main_editor")
    
    # Create columns for editor and suggestions
    col1, col2 = st.columns([3, 2])
    
    with col1:
        # Render the editor
        content, language = editor.render()
        
        # Action buttons below editor
        col1_1, col1_2, col1_3 = st.columns(3)
        
        with col1_1:
            if st.button("Get Suggestions", key="get_suggestions_button"):
                get_ai_suggestions(editor)
                
        with col1_2:
            if st.button("Explain Code", key="explain_code_button"):
                explain_code(editor)
                
        with col1_3:
            if st.button("Clear Editor", key="clear_editor_button"):
                editor.reset()
                st.experimental_rerun()
    
    with col2:
        # Show suggestions if available
        editor.render_suggestions(
            implement_callback=lambda: editor.implement_suggestions()
        )
    
    # Check for auto-suggestions if enabled
    if editor.should_auto_suggest(idle_seconds=3):
        get_ai_suggestions(editor)
        st.experimental_rerun()

def main():
    """Main application entry point"""
    # Check if user is authenticated
    if not st.session_state.authenticated:
        render_login_page()
    else:
        # Render sidebar
        render_sidebar()
        
        # Render main application
        render_main_app()

if __name__ == "__main__":
    main()
