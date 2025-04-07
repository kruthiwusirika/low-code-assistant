import streamlit as st
import os
import openai
import time
import sys
from collections import defaultdict
from dotenv import load_dotenv

# Add utils directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'utils'))

# Import user manager and authentication utilities
from utils.user_manager import UserManager
from app.auth import login_page, logout, user_profile, init_session_state

# Import local model utilities
try:
    import local_model
    HAVE_LOCAL_MODELS = True
except ImportError:
    HAVE_LOCAL_MODELS = False

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Low-Code Assistant",
    page_icon="🧩",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize authentication session state
init_session_state()

# Initialize OpenAI API key from user's profile if authenticated, otherwise from env
if st.session_state.authenticated and st.session_state.user.get('api_key'):
    api_key = st.session_state.user.get('api_key')
    os.environ["OPENAI_API_KEY"] = api_key
else:
    api_key = os.getenv("OPENAI_API_KEY")

# Rate limiting implementation
class RateLimiter:
    def __init__(self, max_calls, time_frame):
        self.max_calls = max_calls  # Maximum calls allowed in time_frame
        self.time_frame = time_frame  # Time frame in seconds
        self.calls = defaultdict(list)  # Store call timestamps by user
    
    def is_allowed(self, user_id):
        """Check if user is allowed to make a call"""
        current_time = time.time()
        user_calls = self.calls[user_id]
        
        # Remove timestamps older than time_frame
        while user_calls and user_calls[0] < current_time - self.time_frame:
            user_calls.pop(0)
        
        # Check if user has made fewer calls than max_calls
        if len(user_calls) < self.max_calls:
            user_calls.append(current_time)
            return True
        return False

# Initialize rate limiter (e.g., 10 calls per hour)
rate_limiter = RateLimiter(max_calls=10, time_frame=3600)

# Helper function to get file extension for code downloads
def get_file_extension(language):
    """Get the appropriate file extension for a given programming language"""
    extension_map = {
        "Python": ".py",
        "JavaScript": ".js",
        "TypeScript": ".ts",
        "Java": ".java",
        "C#": ".cs",
        "C++": ".cpp",
        "C": ".c",
        "Go": ".go",
        "Ruby": ".rb",
        "PHP": ".php",
        "Swift": ".swift",
        "Kotlin": ".kt",
        "Rust": ".rs",
        "SQL": ".sql",
        "HTML": ".html",
        "CSS": ".css",
        "Bash": ".sh",
        "PowerShell": ".ps1",
        "R": ".r",
        "Scala": ".scala",
        "Perl": ".pl",
        "Haskell": ".hs",
        "Lua": ".lua",
        "Dart": ".dart",
        "YAML": ".yaml",
        "JSON": ".json",
        "XML": ".xml"
    }
    return extension_map.get(language, ".txt")

# Custom CSS for styling
st.markdown("""
<style>
    .main .block-container {
        padding-top: 2rem;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 40px;
        white-space: pre-wrap;
        border-radius: 4px;
        padding: 0 10px;
    }
    .stTabs [aria-selected="true"] {
        background-color: rgba(0, 104, 201, 0.1);
    }
    .stSelectbox {
        margin-bottom: 1rem;
    }
    .success-message {
        color: #0f5132;
        background-color: #d1e7dd;
        border-color: #badbcc;
        padding: 1rem;
        border-radius: 0.25rem;
        margin-bottom: 1rem;
    }
    .success-message strong {
        font-weight: bold;
    }
    .description-textarea textarea {
        height: 150px;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state for various app features
if "model_type" not in st.session_state:
    st.session_state.model_type = "openai"
if "openai_model" not in st.session_state:
    st.session_state.openai_model = "gpt-3.5-turbo"
if "local_model_name" not in st.session_state:
    st.session_state.local_model_name = None
if "temperature" not in st.session_state:
    st.session_state.temperature = 0.7
if "max_tokens" not in st.session_state:
    st.session_state.max_tokens = 1000
if "code_type" not in st.session_state:
    st.session_state.code_type = None
if "language" not in st.session_state:
    st.session_state.language = None
if "description" not in st.session_state:
    st.session_state.description = None
if "generated_code" not in st.session_state:
    st.session_state.generated_code = None
if "editor_content" not in st.session_state:
    st.session_state.editor_content = None
if "suggestions" not in st.session_state:
    st.session_state.suggestions = None

# Sidebar
with st.sidebar:
    st.title("Low-Code Assistant")
    
    # Show user info if authenticated, otherwise show login button
    if st.session_state.authenticated:
        st.write(f"Welcome, {st.session_state.user['username']}!")
        if st.button("View Profile", key="sidebar_view_profile"):
            st.session_state.show_profile = True
            st.rerun()
        if st.button("Logout", key="sidebar_logout"):
            logout()
            st.rerun()
            
        # Only show these sections if user is authenticated
        # API Key section
        api_key_section = st.expander("OpenAI API Key", expanded=False)
        with api_key_section:
            # Information about API keys
            st.info("You need to provide your own OpenAI API key to use the code generation features.")
            
            if st.session_state.user.get('api_key'):
                st.success("✅ API key is configured in your profile")
                # Show a masked version of the API key
                mask = st.session_state.user.get('api_key')[:4] + "*" * 6 + "..." if len(st.session_state.user.get('api_key')) > 10 else "*" * 10
                st.code(mask, language=None)
                
                if st.button("Manage API Key", key="manage_api_key"):
                    st.session_state.show_profile = True
                    st.rerun()
            else:
                # API Key configuration for authenticated users without API key
                st.warning("⚠️ No API key configured. Code generation features will not work.")
                st.write("Configure your OpenAI API Key:")
                new_api_key = st.text_input(
                    "OpenAI API Key", 
                    value="", 
                    type="password",
                    help="Your API key will be securely saved to your profile."
                )
                
                if new_api_key:
                    os.environ["OPENAI_API_KEY"] = new_api_key
                    api_key = new_api_key
                    
                    # Save API key to user profile
                    user_manager = UserManager()
                    user_manager.update_user_api_key(st.session_state.user['id'], new_api_key)
                    st.session_state.user['api_key'] = new_api_key
                    st.success("API Key saved to your profile")
                    st.rerun()
        
        # Model settings section
        model_section = st.expander("Model Settings", expanded=False)
        with model_section:
            # Model source selection
            model_source = st.radio(
                "Model Source",
                ["OpenAI API", "Local Model"] if HAVE_LOCAL_MODELS else ["OpenAI API"],
                disabled=not api_key
            )
            
            # Set model type based on selection
            st.session_state.model_type = "openai" if model_source == "OpenAI API" else "local"
    else:
        # Show only login button for non-authenticated users
        st.info("Please login or register to use the Low-Code Assistant")
        if st.button("Login / Register", key="sidebar_login_register"):
            st.session_state.show_login = True
            st.rerun()
        
        # Default model type for non-authenticated users
        st.session_state.model_type = "openai"
        
        # OpenAI model settings
        if st.session_state.model_type == "openai":
            st.session_state.openai_model = st.selectbox(
                "OpenAI Model",
                ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo"],
                disabled=not api_key
            )
        # Local model settings
        else:  # Local Model
            if HAVE_LOCAL_MODELS:
                # Get system info for guidance
                system_info = local_model.get_system_info()
                cuda_available = system_info.get("cuda_available", False)
                
                st.info(f"GPU Acceleration: {'Available' if cuda_available else 'Not Available'}")
                
                st.session_state.local_model_name = st.selectbox(
                    "Local Model",
                    local_model.list_available_models(),
                    disabled=not api_key
                )
            else:
                st.error("Local models not available. Please install the required dependencies.")
        
        # Common model parameters
        st.session_state.temperature = st.slider(
            "Temperature",
            min_value=0.0,
            max_value=1.0,
            value=st.session_state.temperature,
            step=0.1,
            disabled=not api_key,
            help="Lower values make output more deterministic, higher values more creative."
        )
        
        st.session_state.max_tokens = st.slider(
            "Max Tokens",
            min_value=50,
            max_value=4000,
            value=st.session_state.max_tokens,
            step=50,
            disabled=not api_key,
            help="Maximum number of tokens in the generated response."
        )
    
    st.divider()
    st.markdown("Made with ❤️ for low-code teams")

# Initialize session state variables for auth pages
if "show_login" not in st.session_state:
    st.session_state.show_login = False
if "show_profile" not in st.session_state:
    st.session_state.show_profile = False

# Check if we should show login page
if st.session_state.show_login:
    login_result = login_page()
    if login_result:
        # User logged in successfully
        st.session_state.show_login = False
        st.rerun()
    else:
        # Still on login page or login failed
        st.stop()

# Check if we should show profile page
if st.session_state.show_profile:
    user_profile()
    if st.button("Return to Code Generator", key="return_from_profile"):
        st.session_state.show_profile = False
        st.rerun()
    st.stop()

# Main content
# If not authenticated, show a welcome message instead of the code generator
if not st.session_state.authenticated:
    st.header("Welcome to Low-Code Assistant")
    st.write("""
    The Low-Code Assistant helps you quickly generate code using AI. 
    Please login or register to get started.
    """)
    
    # Show features
    st.subheader("🚀 Features")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""  
        - **AI-Powered Code Generation**
        - **Multiple Programming Languages**
        - **Customizable Output**
        - **Secure API Key Management**
        """)
    
    with col2:
        st.markdown("""
        - **Live Code Editor**
        - **AI Code Suggestions**
        - **User Accounts & Settings**
        - **Simple, Intuitive UI**
        """)
    
    # Call to action
    st.info("Click 'Login / Register' in the sidebar to get started")
    
    # Stop execution here for non-authenticated users
    st.stop()

# If we get here, user is authenticated
st.header("AI Code Generator")

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("Input")
    
    # Programming language selection
    language = st.selectbox(
        "Programming Language",
        ["Python", "JavaScript", "TypeScript", "Java", "C#", "C++", "Go", "Ruby", "PHP", "Swift", "Kotlin", "Rust", "SQL"],
        index=0 if st.session_state.language is None else list(["Python", "JavaScript", "TypeScript", "Java", "C#", "C++", "Go", "Ruby", "PHP", "Swift", "Kotlin", "Rust", "SQL"]).index(st.session_state.language)
    )
    st.session_state.language = language
    
    # Code type selection
    code_type = st.selectbox(
        "Type of Code",
        ["Function", "Class", "API Endpoint", "Algorithm", "Data Structure", "Utility", "Full Script"],
        index=0 if st.session_state.code_type is None else list(["Function", "Class", "API Endpoint", "Algorithm", "Data Structure", "Utility", "Full Script"]).index(st.session_state.code_type)
    )
    st.session_state.code_type = code_type
    
    # Description input
    description = st.text_area(
        "Describe what you want the code to do",
        value=st.session_state.description if st.session_state.description else "",
        height=150,
        max_chars=1000,
        help="Be as specific as possible for better results."
    )
    st.session_state.description = description
    
    # Advanced options
    with st.expander("Advanced Options"):
        col1a, col1b = st.columns(2)
        
        with col1a:
            include_comments = st.checkbox("Include Comments", value=True)
            error_handling = st.checkbox("Include Error Handling", value=True)
        
        with col1b:
            code_style = st.radio("Code Style", ["Concise", "Detailed", "Production-Ready"])
    
    def generate_code():
        """Generate code based on user inputs"""
        try:
            # Validate inputs
            if not st.session_state.language or not st.session_state.code_type or not st.session_state.description:
                st.error("Please fill in all required fields.")
                return
            
            # Check if API key is configured
            if not api_key and st.session_state.model_type == "openai":
                st.error("API key not configured. Please enter your OpenAI API key in the sidebar.")
                return
            
            # Show spinner during generation
            with st.spinner("Generating code..."):
                # Prepare the prompt
                comments_str = "with detailed comments" if include_comments else "with minimal comments"
                error_str = "with robust error handling" if error_handling else "with basic error handling"
                style_str = f"using a {code_style.lower()} style"
                
                prompt = f"""Create a {st.session_state.code_type.lower()} in {st.session_state.language} {comments_str} and {error_str}, {style_str}, that does the following:
                
                {st.session_state.description}
                
                Please provide only the code without additional explanations.
                """
                
                # Generate code based on model type
                if st.session_state.model_type == "openai":
                    # Generate code using OpenAI
                    
                    # Configure OpenAI
                    openai_client = openai.OpenAI(api_key=api_key)
                    
                    # Call the API
                    response = openai_client.chat.completions.create(
                        model=st.session_state.openai_model,
                        messages=[
                            {"role": "system", "content": f"You are an expert {st.session_state.language} developer. Generate clean, efficient, and well-structured code."},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=st.session_state.temperature,
                        max_tokens=st.session_state.max_tokens
                    )
                    
                    # Extract the code from the response
                    generated_code = response.choices[0].message.content
                else:
                    # Generate code using local model
                    if HAVE_LOCAL_MODELS and st.session_state.local_model_name:
                        generated_code = local_model.generate_code(
                            prompt=prompt,
                            model_name=st.session_state.local_model_name,
                            temperature=st.session_state.temperature,
                            max_tokens=st.session_state.max_tokens
                        )
                    else:
                        st.error("Local model not configured properly.")
                        return
                
                # Clean up the generated code
                generated_code = generated_code.strip()
                
                # Remove markdown code blocks if present
                if generated_code.startswith("```") and generated_code.endswith("```"):
                    # Extract the language from the code block if present
                    lines = generated_code.split("\n")
                    if len(lines) > 2:
                        # Remove the first and last lines (```language and ```)
                        generated_code = "\n".join(lines[1:-1])
                    else:
                        # Just remove the ``` markers
                        generated_code = generated_code.replace("```", "").strip()
                
                # Store generated code in session state
                st.session_state.generated_code = generated_code
                
                # Initialize editor content if it's None
                if st.session_state.editor_content is None:
                    st.session_state.editor_content = generated_code
                
                # Clear suggestions when new code is generated
                st.session_state.suggestions = None
                
                # Generate a filename for download
                st.session_state.file_extension = get_file_extension(st.session_state.language)
        
        except Exception as e:
            st.error(f"An error occurred during code generation: {str(e)}")
    
    if st.button("Generate Code"):
        generate_code()

with col2:
    st.subheader("Generated Code")
    
    # Add tabs for Generated Code and Live Editor
    generated_tab, live_editor_tab = st.tabs(["Generated Code", "Live Editor"])
    
    with generated_tab:
        if st.session_state.generated_code:
            # Show the generated code
            st.code(st.session_state.generated_code, language=st.session_state.language.lower())
            
            # Add a button to download the code
            if st.session_state.file_extension:
                file_name = f"generated_code{st.session_state.file_extension}"
                
                st.download_button(
                    label="Download Code",
                    data=st.session_state.generated_code,
                    file_name=file_name,
                    mime="text/plain"
                )
        else:
            st.info("Generate code to see results here.")
    
    with live_editor_tab:
        from streamlit_ace import st_ace
        
        # Initialize session state for editor content if not exists
        if 'editor_content' not in st.session_state:
            st.session_state.editor_content = ""
        
        # No need for this function anymore as we're updating directly
        # Keeping as a placeholder for compatibility
        
        # Editor options based on programming language
        language_mode = {
            "Python": "python",
            "JavaScript": "javascript",
            "TypeScript": "typescript",
            "Java": "java",
            "C#": "csharp",
            "C++": "c_cpp",
            "Go": "golang",
            "Ruby": "ruby",
            "PHP": "php",
            "Swift": "swift",
            "Kotlin": "kotlin",
            "Rust": "rust",
            "SQL": "sql",
        }.get(st.session_state.language, "text")
        
        # Live editor with syntax highlighting
        editor_content = st_ace(
            value=st.session_state.editor_content,
            language=language_mode,
            theme="monokai",
            keybinding="vscode",
            min_lines=20,
            font_size=14,
            wrap=True,
            show_gutter=True,
            show_print_margin=True,
            auto_update=True,
            key="ace_editor"
        )
        
        # Update editor content in session state
        if editor_content:
            st.session_state.editor_content = editor_content
        
        # Save and download buttons
        col_save, col_download = st.columns(2)
        
        with col_save:
            if st.button("Get AI Suggestions"):
                # Simulate AI suggestions
                if st.session_state.editor_content:
                    try:
                        # Get API key from user profile if authenticated, otherwise use session API key
                        user_api_key = ""
                        if st.session_state.authenticated and st.session_state.user.get('api_key'):
                            user_api_key = st.session_state.user.get('api_key')
                        else:
                            user_api_key = api_key
                            
                        if not user_api_key:
                            st.error("No API key found. Please add your OpenAI API key in the settings.")
                            st.stop()
                            
                        # Set the API key in the environment
                        os.environ["OPENAI_API_KEY"] = user_api_key
                        openai_client = openai.OpenAI(api_key=user_api_key)
                        
                        prompt = f"""Analyze this {st.session_state.language} code and provide suggestions for improvements:
                        
                        ```{st.session_state.language.lower()}
                        {st.session_state.editor_content}
                        ```
                        
                        Focus on:
                        1. Code efficiency and performance
                        2. Best practices for {st.session_state.language}
                        3. Error handling and edge cases
                        4. Code readability and maintainability
                        
                        Provide concise, actionable suggestions. Use markdown formatting.
                        """
                        
                        # Call the API
                        response = openai_client.chat.completions.create(
                            model="gpt-3.5-turbo",
                            messages=[
                                {"role": "system", "content": f"You are an expert {st.session_state.language} code reviewer who gives concise, helpful suggestions."},
                                {"role": "user", "content": prompt}
                            ],
                            temperature=0.7,
                            max_tokens=500
                        )
                        
                        # Extract suggestions
                        st.session_state.suggestions = response.choices[0].message.content
                    except Exception as e:
                        st.error(f"Error generating suggestions: {str(e)}")
        
        with col_download:
            if st.session_state.editor_content:
                file_name = f"edited_code{get_file_extension(st.session_state.language)}"
                
                st.download_button(
                    label="Download Edited Code",
                    data=st.session_state.editor_content,
                    file_name=file_name,
                    mime="text/plain"
                )
        
        # Display AI suggestions
        if 'suggestions' in st.session_state and st.session_state.suggestions:
            st.subheader("AI Suggestions")
            st.markdown(st.session_state.suggestions)
            
            # Option to apply suggestions
            if st.button("Implement Suggestions"):
                # Directly set a flag to trigger implementation in session state
                st.session_state.implement_requested = True
                st.rerun()

# Helper function for showing notifications
def show_notification(message, type="success"):
    if type == "success":
        st.toast(f"✅ {message}", icon="✅")
    elif type == "error":
        st.toast(f"❌ {message}", icon="❌")
    elif type == "info":
        st.toast(f"ℹ️ {message}", icon="ℹ️")
    elif type == "warning":
        st.toast(f"⚠️ {message}", icon="⚠️")

# Processing for Implement Suggestions - moved outside the tab structure to ensure it runs
if 'implement_requested' in st.session_state and st.session_state.implement_requested and 'editor_content' in st.session_state and 'suggestions' in st.session_state:
    try:
        st.session_state.implement_requested = False  # Reset flag
        show_notification("Processing implementation request...", "info")
        
        # Store original code for diff view
        st.session_state.original_code = st.session_state.editor_content
        
        # Get API key
        user_api_key = ""
        if st.session_state.authenticated and st.session_state.user.get('api_key'):
            user_api_key = st.session_state.user.get('api_key')
        else:
            user_api_key = api_key
            
        if not user_api_key:
            show_notification("No API key found. Please add your OpenAI API key in the settings.", "error")
        else:
            try:
                # Set up OpenAI client
                os.environ["OPENAI_API_KEY"] = user_api_key
                openai_client = openai.OpenAI(api_key=user_api_key)
                
                # Create the prompt for implementation
                orig_code = st.session_state.editor_content
                orig_suggestions = st.session_state.suggestions
                lang = st.session_state.language
                
                show_notification("Sending request to OpenAI API...", "info")
                
                prompt = f"""Implement the following suggestions to improve this {lang} code:
                
                ORIGINAL CODE:
                ```{lang.lower()}
                {orig_code}
                ```
                
                SUGGESTIONS:
                {orig_suggestions}
                
                Provide ONLY the improved code without any explanations or markdown formatting.
                """
                
                # Call the API
                response = openai_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": f"You are an expert {lang} developer who implements code improvements effectively. Your task is to output ONLY the improved code with NO explanations or comments about what you changed."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.2,
                    max_tokens=1500
                )
                
                # Extract the improved code
                improved_code = response.choices[0].message.content.strip()
                
                # Clean up the code to remove markdown formatting
                if "```" in improved_code:
                    # Try to extract code between backticks
                    parts = improved_code.split("```")
                    if len(parts) >= 3:
                        # Take the content between the first set of backticks
                        code_block = parts[1]
                        # Remove the language identifier if present
                        if "\n" in code_block:
                            improved_code = code_block.split("\n", 1)[1]
                        else:
                            improved_code = code_block
                    else:
                        # Just remove all backticks
                        improved_code = improved_code.replace("`", "")
                
                # Store the improved code and show a changes view
                st.session_state.improved_code = improved_code
                st.session_state.show_changes = True
                
                # Update editor content
                st.session_state.editor_content = improved_code
                
                # Clear suggestions since they've been implemented
                st.session_state.suggestions = None
                
                # Show success notification
                show_notification("Successfully implemented suggestions! View changes below.", "success")
                
            except Exception as e:
                show_notification(f"Error: {str(e)}", "error")
                st.error(f"Error implementing suggestions: {str(e)}")
                import traceback
                st.code(traceback.format_exc(), language="python")
    except Exception as e:
        show_notification(f"Unexpected error", "error")
        st.error(f"Unexpected error: {str(e)}")

# Show changes if available (after implementation)
if 'show_changes' in st.session_state and st.session_state.show_changes and 'original_code' in st.session_state and 'improved_code' in st.session_state:
    st.session_state.show_changes = False  # Reset flag after showing
    
    st.markdown("### 🔄 Code Changes")
    st.write("The following changes were made to your code:")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Original Code")
        st.code(st.session_state.original_code, language=st.session_state.language.lower())
    
    with col2:
        st.markdown("#### Improved Code")
        st.code(st.session_state.improved_code, language=st.session_state.language.lower())
    
    # Summary of changes
    import difflib
    diff = difflib.unified_diff(
        st.session_state.original_code.splitlines(),
        st.session_state.improved_code.splitlines(),
        lineterm=''
    )
    
    diff_text = '\n'.join(list(diff)[2:])  # Skip the first two lines of diff header
    
    if diff_text.strip():
        st.markdown("#### Summary of Changes")
        st.code(diff_text, language="diff")
    else:
        st.info("No visible changes were detected in the code.")

# Footer
st.divider()
st.caption("Low-Code Assistant v1.0 | © 2025")
