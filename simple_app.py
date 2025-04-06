import streamlit as st
import os
import openai
import time
from collections import defaultdict
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Low-Code Assistant",
    page_icon="🧩",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize OpenAI API key
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

# Custom CSS for styling
st.markdown("""
<style>
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    h1, h2, h3 {
        color: #0066cc;
    }
    .stButton>button {
        border-radius: 5px;
    }
    pre {
        background-color: #222222;
        border-radius: 5px;
        padding: 1rem;
        margin-bottom: 1rem;
        overflow-x: auto;
    }
    code {
        color: #e6e6e6;
    }
</style>
""", unsafe_allow_html=True)

# Session state initialization
if "generated_code" not in st.session_state:
    st.session_state.generated_code = ""

# Sidebar
with st.sidebar:
    st.title("Low-Code Assistant")
    
    # User account setup section
    user_section = st.expander("User Account Setup", expanded=False)
    with user_section:
        st.write("Your API key is securely stored in the .env file and never displayed in the UI.")
        has_api_key = bool(api_key)
        
        # Show API key status
        if has_api_key:
            st.success("✅ API key is configured")
            if st.button("Update API Key"):
                st.session_state.show_key_input = True
        else:
            st.error("❌ API key not found")
            st.session_state.show_key_input = True
        
        # Show API key input only when needed
        if not has_api_key or st.session_state.get('show_key_input', False):
            new_api_key = st.text_input("Enter your OpenAI API Key", type="password", key="new_api_key")
            if st.button("Save API Key"):
                if new_api_key:
                    # Save to environment and to .env file
                    os.environ["OPENAI_API_KEY"] = new_api_key
                    openai.api_key = new_api_key
                    
                    # Update .env file
                    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
                    try:
                        # Read existing .env content
                        env_content = ""
                        if os.path.exists(env_path):
                            with open(env_path, 'r') as f:
                                lines = f.readlines()
                                # Replace or add API key
                                key_found = False
                                for i, line in enumerate(lines):
                                    if line.startswith('OPENAI_API_KEY='):
                                        lines[i] = f"OPENAI_API_KEY={new_api_key}\n"
                                        key_found = True
                                        break
                                if not key_found:
                                    lines.append(f"OPENAI_API_KEY={new_api_key}\n")
                                env_content = "".join(lines)
                        else:
                            env_content = f"OPENAI_API_KEY={new_api_key}\n\n# Application Settings\nAPP_ENV=development\n"
                        
                        # Write back to .env file
                        with open(env_path, 'w') as f:
                            f.write(env_content)
                            
                        st.success("API key saved successfully!")
                        st.session_state.show_key_input = False
                        # Refresh the page to use the new API key
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error saving API key: {str(e)}")
                else:
                    st.error("Please enter a valid API key")
    
    st.divider()
    
    # Settings
    st.subheader("Settings")
    model = st.selectbox(
        "Model",
        ["gpt-3.5-turbo", "gpt-3.5-turbo-1106", "gpt-4-turbo", "gpt-4"]
    )
    temperature = st.slider("Temperature", min_value=0.0, max_value=1.0, value=0.7, step=0.1)
    max_tokens = st.slider("Max Tokens", min_value=100, max_value=2000, value=1000, step=100)
    
    st.divider()
    st.markdown("Made with ❤️ for low-code teams")

# Main content
st.header("AI Code Generator")

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("Describe what you need")
    
    # Input options
    programming_language = st.selectbox(
        "Programming Language",
        ["Python", "JavaScript", "TypeScript", "Java", "C#", "PHP", "Go", "Ruby", "Swift", "Kotlin"]
    )
    
    code_type = st.selectbox(
        "Type of Code",
        ["Function", "Class", "API Endpoint", "Database Query", "UI Component", "Full Script", "Configuration"]
    )
    
    description = st.text_area(
        "Describe what you want the code to do",
        height=150,
        placeholder="Example: A function that takes a list of numbers and returns the average, handling empty lists and non-numeric values."
    )
    
    advanced_options = st.expander("Advanced Options")
    with advanced_options:
        include_comments = st.checkbox("Include detailed comments", value=True)
        error_handling = st.checkbox("Add error handling", value=True)
        code_style = st.selectbox("Code Style", ["Standard", "Concise", "Verbose", "Production-Ready"])
        
    def generate_code():
        # Get a unique identifier for the user (session ID in this case)
        user_id = st.session_state.get("_session_id", "default_user")
        
        # Check rate limit
        if not rate_limiter.is_allowed(user_id):
            st.error("Rate limit exceeded. Please try again later. (Limit: 10 calls per hour)")
            return
            
        if not api_key and not openai.api_key:
            st.error("Please configure your OpenAI API key in the User Account Setup section first.")
            return
        
        if not description:
            st.error("Please provide a description of what code you need.")
            return
        
        with st.spinner("Generating code..."):
            try:
                # Build system message with specific instructions
                system_message = (
                    f"You are an expert {programming_language} developer specializing in creating {code_type.lower()}s for low-code teams. "
                    f"Your task is to generate clean, efficient, and well-structured {programming_language} code based on the given description. "
                )
                
                # Add style preferences
                if code_style == "Concise":
                    system_message += "Generate concise code that focuses on efficiency with minimal verbosity. "
                elif code_style == "Verbose":
                    system_message += "Generate detailed code with clear variable names and comprehensive structure. "
                elif code_style == "Production-Ready":
                    system_message += "Generate production-quality code with best practices for security, performance, and maintainability. "
                
                # Add comment preferences
                comment_instruction = (
                    "Include detailed comments explaining the code's functionality, parameters, and return values. "
                    if include_comments else 
                    "Include minimal comments, focusing on the most critical parts only. "
                )
                system_message += comment_instruction
                
                # Add error handling preferences
                error_instruction = (
                    "Implement robust error handling and input validation. "
                    if error_handling else
                    "Keep error handling minimal and focus on the core functionality. "
                )
                system_message += error_instruction
                
                # Create user message with the description
                user_message = (
                    f"Generate a {programming_language} {code_type.lower()} based on this description:\n\n{description}\n\n"
                    f"Provide only the code without additional explanations. The code should be ready to use."
                )
                
                response = openai.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": user_message}
                    ],
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                
                # Extract the generated code
                generated_code = response.choices[0].message.content.strip()
                
                # Clean up code block markers if present
                if generated_code.startswith("```") and generated_code.endswith("```"):
                    lines = generated_code.split('\n')
                    if len(lines) > 1:
                        first_line = lines[0].strip('`').strip()
                        if first_line.lower() == programming_language.lower() or not first_line:
                            generated_code = '\n'.join(lines[1:-1])
                        else:
                            generated_code = '\n'.join(lines[1:-1])
                
                st.session_state.generated_code = generated_code
                
            except Exception as e:
                st.error(f"Error generating code: {str(e)}")
    
    if st.button("Generate Code"):
        generate_code()

with col2:
    st.subheader("Generated Code")
    
    # Code display area
    if st.session_state.generated_code:
        st.code(st.session_state.generated_code, language=programming_language.lower())
        
        # Download button
        code_to_download = st.session_state.generated_code
        extension_map = {
            "Python": "py",
            "JavaScript": "js",
            "TypeScript": "ts",
            "Java": "java",
            "C#": "cs",
            "PHP": "php",
            "Go": "go",
            "Ruby": "rb",
            "Swift": "swift",
            "Kotlin": "kt"
        }
        ext = extension_map.get(programming_language, "txt")
        
        st.download_button(
            label=f"Download {programming_language} Code",
            data=code_to_download,
            file_name=f"generated_code.{ext}",
            mime="text/plain"
        )
    else:
        st.info("Describe your requirements and click 'Generate Code' to see the results here.")

# Footer
st.divider()
st.caption("Low-Code Assistant v1.0 | © 2025")
