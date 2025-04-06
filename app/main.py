import streamlit as st
import os
import sys
from pathlib import Path
import json

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Import utility modules
from utils.code_generator import CodeGenerator
from utils.template_manager import TemplateManager
from utils.config_loader import load_config

# Page configuration
st.set_page_config(
    page_title="Low-Code Assistant",
    page_icon="🧩",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load configuration
config = load_config()

# Initialize components
code_generator = CodeGenerator()
template_manager = TemplateManager()

# Custom CSS
with open(project_root / "static" / "styles.css", "r") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Session state initialization
if "generated_code" not in st.session_state:
    st.session_state.generated_code = ""
if "current_template" not in st.session_state:
    st.session_state.current_template = None
if "history" not in st.session_state:
    st.session_state.history = []

# Sidebar
with st.sidebar:
    st.image(project_root / "static" / "logo.png", width=200)
    st.title("Low-Code Assistant")
    
    # API Key input
    api_key = st.text_input("OpenAI API Key", type="password")
    if api_key:
        os.environ["OPENAI_API_KEY"] = api_key
    
    st.divider()
    
    # Navigation
    st.subheader("Navigation")
    page = st.radio(
        "Select a page",
        ["Code Generator", "Template Library", "Code Translator", "Settings"]
    )
    
    st.divider()
    
    # Template selection if on Template Library page
    if page == "Template Library":
        st.subheader("Available Templates")
        templates = template_manager.get_template_list()
        selected_template = st.selectbox("Select a template", templates)
        
        if selected_template and st.button("Load Template"):
            st.session_state.current_template = template_manager.get_template(selected_template)
            st.session_state.generated_code = st.session_state.current_template["code"]
    
    st.divider()
    st.markdown("Made with ❤️ for low-code teams")

# Main content
if page == "Code Generator":
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
            
        if st.button("Generate Code"):
            with st.spinner("Generating code..."):
                generated_code = code_generator.generate(
                    description=description,
                    language=programming_language,
                    code_type=code_type,
                    include_comments=include_comments,
                    error_handling=error_handling,
                    code_style=code_style
                )
                
                st.session_state.generated_code = generated_code
                
                # Add to history
                st.session_state.history.append({
                    "description": description,
                    "language": programming_language,
                    "code_type": code_type,
                    "code": generated_code,
                    "timestamp": import_module("datetime").datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
    
    with col2:
        st.subheader("Generated Code")
        
        # Code editor for the generated code
        if st.session_state.generated_code:
            from streamlit_ace import st_ace
            
            edited_code = st_ace(
                value=st.session_state.generated_code,
                language=programming_language.lower(),
                theme="monokai",
                height=400,
                key="code_editor"
            )
            
            col3, col4 = st.columns([1, 1])
            
            with col3:
                if st.button("Save as Template"):
                    template_name = st.text_input("Template Name")
                    if template_name:
                        template_manager.save_template(
                            name=template_name,
                            code=edited_code,
                            description=description,
                            language=programming_language,
                            code_type=code_type
                        )
                        st.success(f"Template '{template_name}' saved successfully!")
            
            with col4:
                if st.button("Download Code"):
                    import base64
                    
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
                    b64 = base64.b64encode(edited_code.encode()).decode()
                    href = f'<a href="data:file/text;base64,{b64}" download="generated_code.{ext}">Download {programming_language} File</a>'
                    st.markdown(href, unsafe_allow_html=True)
        else:
            st.info("Describe your requirements and click 'Generate Code' to see the results here.")

elif page == "Template Library":
    st.header("Template Library")
    
    if st.session_state.current_template:
        st.subheader(f"Template: {st.session_state.current_template['name']}")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown("**Template Information**")
            st.markdown(f"**Language:** {st.session_state.current_template['language']}")
            st.markdown(f"**Type:** {st.session_state.current_template['code_type']}")
            st.markdown(f"**Description:**")
            st.markdown(st.session_state.current_template['description'])
        
        with col2:
            st.markdown("**Code**")
            from streamlit_ace import st_ace
            
            edited_template_code = st_ace(
                value=st.session_state.current_template["code"],
                language=st.session_state.current_template["language"].lower(),
                theme="monokai",
                height=300,
                key="template_editor"
            )
            
            if st.button("Update Template"):
                template_manager.update_template(
                    name=st.session_state.current_template["name"],
                    code=edited_template_code
                )
                st.success(f"Template '{st.session_state.current_template['name']}' updated successfully!")
    else:
        st.info("Select a template from the sidebar to view and edit it.")
    
    st.divider()
    
    st.subheader("Create New Template")
    
    col3, col4 = st.columns([1, 1])
    
    with col3:
        new_template_name = st.text_input("Template Name")
        new_template_language = st.selectbox(
            "Programming Language",
            ["Python", "JavaScript", "TypeScript", "Java", "C#", "PHP", "Go", "Ruby", "Swift", "Kotlin"]
        )
        new_template_type = st.selectbox(
            "Code Type",
            ["Function", "Class", "API Endpoint", "Database Query", "UI Component", "Full Script", "Configuration"]
        )
        new_template_description = st.text_area("Description", height=100)
    
    with col4:
        new_template_code = st_ace(
            value="# Enter your code here",
            language=new_template_language.lower(),
            theme="monokai",
            height=200,
            key="new_template_editor"
        )
        
        if st.button("Save New Template"):
            if new_template_name:
                template_manager.save_template(
                    name=new_template_name,
                    code=new_template_code,
                    description=new_template_description,
                    language=new_template_language,
                    code_type=new_template_type
                )
                st.success(f"Template '{new_template_name}' created successfully!")
            else:
                st.error("Please provide a template name.")

elif page == "Code Translator":
    st.header("Code Translator")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("Source Code")
        
        source_language = st.selectbox(
            "Source Language",
            ["Python", "JavaScript", "TypeScript", "Java", "C#", "PHP", "Go", "Ruby", "Swift", "Kotlin"],
            key="source_language"
        )
        
        from streamlit_ace import st_ace
        
        source_code = st_ace(
            value="# Enter the code you want to translate",
            language=source_language.lower(),
            theme="monokai",
            height=350,
            key="source_code_editor"
        )
    
    with col2:
        st.subheader("Translated Code")
        
        target_language = st.selectbox(
            "Target Language",
            ["Python", "JavaScript", "TypeScript", "Java", "C#", "PHP", "Go", "Ruby", "Swift", "Kotlin"],
            key="target_language"
        )
        
        if st.button("Translate"):
            if source_language == target_language:
                st.error("Source and target languages must be different.")
            else:
                with st.spinner(f"Translating from {source_language} to {target_language}..."):
                    translated_code = code_generator.translate(
                        source_code=source_code,
                        source_language=source_language,
                        target_language=target_language
                    )
                    
                    translated_editor = st_ace(
                        value=translated_code,
                        language=target_language.lower(),
                        theme="monokai",
                        height=350,
                        key="translated_code_editor"
                    )
                    
                    # Download button for translated code
                    import base64
                    
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
                    
                    ext = extension_map.get(target_language, "txt")
                    b64 = base64.b64encode(translated_code.encode()).decode()
                    href = f'<a href="data:file/text;base64,{b64}" download="translated_code.{ext}">Download {target_language} File</a>'
                    st.markdown(href, unsafe_allow_html=True)

elif page == "Settings":
    st.header("Settings")
    
    st.subheader("API Configuration")
    
    # API Provider
    api_provider = st.selectbox(
        "API Provider",
        ["OpenAI", "Azure OpenAI", "Anthropic", "Google Vertex AI"]
    )
    
    # Model selection based on provider
    if api_provider == "OpenAI":
        model = st.selectbox(
            "Model",
            ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"]
        )
    elif api_provider == "Azure OpenAI":
        model = st.selectbox(
            "Model",
            ["gpt-4", "gpt-3.5-turbo"]
        )
        azure_endpoint = st.text_input("Azure Endpoint")
        deployment_name = st.text_input("Deployment Name")
    elif api_provider == "Anthropic":
        model = st.selectbox(
            "Model",
            ["claude-2", "claude-instant"]
        )
    elif api_provider == "Google Vertex AI":
        model = st.selectbox(
            "Model",
            ["text-bison", "code-bison", "codechat-bison"]
        )
    
    # General settings
    st.subheader("General Settings")
    
    temperature = st.slider("Temperature", min_value=0.0, max_value=1.0, value=0.7, step=0.1)
    max_tokens = st.slider("Max Tokens", min_value=50, max_value=4000, value=1000, step=50)
    
    # Save settings
    if st.button("Save Settings"):
        settings = {
            "api_provider": api_provider,
            "model": model,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        if api_provider == "Azure OpenAI":
            settings["azure_endpoint"] = azure_endpoint
            settings["deployment_name"] = deployment_name
        
        # Save to config file
        with open(project_root / "config" / "settings.json", "w") as f:
            json.dump(settings, f, indent=2)
        
        st.success("Settings saved successfully!")
        
    # Export/Import settings
    st.subheader("Backup & Restore")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        if st.button("Export Settings"):
            # Create downloadable link for settings
            with open(project_root / "config" / "settings.json", "r") as f:
                settings_json = f.read()
                
            import base64
            b64 = base64.b64encode(settings_json.encode()).decode()
            href = f'<a href="data:file/json;base64,{b64}" download="low_code_assistant_settings.json">Download Settings</a>'
            st.markdown(href, unsafe_allow_html=True)
    
    with col2:
        uploaded_file = st.file_uploader("Import Settings", type=["json"])
        if uploaded_file is not None:
            try:
                settings = json.load(uploaded_file)
                with open(project_root / "config" / "settings.json", "w") as f:
                    json.dump(settings, f, indent=2)
                st.success("Settings imported successfully!")
            except Exception as e:
                st.error(f"Error importing settings: {str(e)}")

# Footer
st.divider()
st.caption("Low-Code Assistant v1.0 | © 2025")
