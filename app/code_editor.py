"""
Code Editor component for the LLM-Driven Coding Assistant.
Provides a live code editor with real-time suggestions.
"""
import streamlit as st
from typing import Dict, Any, List, Optional, Tuple, Callable
import difflib
import time

class CodeEditor:
    """
    Interactive code editor component with real-time suggestions.
    """
    
    def __init__(self, key_prefix: str = "editor"):
        """
        Initialize the code editor.
        
        Args:
            key_prefix (str): Prefix for Streamlit session state keys
        """
        self.key_prefix = key_prefix
        
        # Initialize session state variables if they don't exist
        if f"{self.key_prefix}_content" not in st.session_state:
            st.session_state[f"{self.key_prefix}_content"] = ""
            
        if f"{self.key_prefix}_language" not in st.session_state:
            st.session_state[f"{self.key_prefix}_language"] = "python"
            
        if f"{self.key_prefix}_suggestions" not in st.session_state:
            st.session_state[f"{self.key_prefix}_suggestions"] = None
            
        if f"{self.key_prefix}_suggestion_time" not in st.session_state:
            st.session_state[f"{self.key_prefix}_suggestion_time"] = 0
            
        if f"{self.key_prefix}_diff" not in st.session_state:
            st.session_state[f"{self.key_prefix}_diff"] = None
            
        if f"{self.key_prefix}_autosuggest" not in st.session_state:
            st.session_state[f"{self.key_prefix}_autosuggest"] = False
        
        # Editor height
        self.editor_height = 400
        
        # Available languages
        self.available_languages = [
            "python", "javascript", "typescript", "java", "c++", "c", "c#", 
            "go", "rust", "php", "ruby", "swift", "kotlin", "sql", "bash",
            "html", "css", "markdown"
        ]
    
    def render(self, placeholder: Optional[st.delta_generator.DeltaGenerator] = None) -> Tuple[str, str]:
        """
        Render the code editor in the Streamlit app.
        
        Args:
            placeholder (st.delta_generator.DeltaGenerator): Optional placeholder for the editor
            
        Returns:
            Tuple[str, str]: Current code content and selected language
        """
        # Use the provided placeholder or the current Streamlit context
        editor_container = placeholder if placeholder else st
        
        # Create columns for the language selector and auto-suggest toggle
        col1, col2 = editor_container.columns([4, 1])
        
        # Language selector
        selected_language = col1.selectbox(
            "Programming Language",
            options=self.available_languages,
            index=self.available_languages.index(st.session_state[f"{self.key_prefix}_language"]),
            key=f"{self.key_prefix}_language_selector"
        )
        
        # Auto-suggest toggle
        auto_suggest = col2.checkbox(
            "Auto-suggest",
            value=st.session_state[f"{self.key_prefix}_autosuggest"],
            key=f"{self.key_prefix}_autosuggest_toggle"
        )
        
        # Update session state
        st.session_state[f"{self.key_prefix}_language"] = selected_language
        st.session_state[f"{self.key_prefix}_autosuggest"] = auto_suggest
        
        # Code editor
        editor_content = editor_container.text_area(
            "Code Editor",
            value=st.session_state[f"{self.key_prefix}_content"],
            height=self.editor_height,
            key=f"{self.key_prefix}_text_area"
        )
        
        # Update session state with the editor content
        st.session_state[f"{self.key_prefix}_content"] = editor_content
        
        return editor_content, selected_language
    
    def set_content(self, content: str) -> None:
        """
        Set the content of the editor.
        
        Args:
            content (str): Content to set
        """
        st.session_state[f"{self.key_prefix}_content"] = content
    
    def get_content(self) -> str:
        """
        Get the current content of the editor.
        
        Returns:
            str: Current editor content
        """
        return st.session_state[f"{self.key_prefix}_content"]
    
    def set_language(self, language: str) -> None:
        """
        Set the programming language.
        
        Args:
            language (str): Language to set
        """
        if language in self.available_languages:
            st.session_state[f"{self.key_prefix}_language"] = language
    
    def get_language(self) -> str:
        """
        Get the current programming language.
        
        Returns:
            str: Current language
        """
        return st.session_state[f"{self.key_prefix}_language"]
    
    def set_suggestions(self, suggestions: Optional[str]) -> None:
        """
        Set code suggestions.
        
        Args:
            suggestions (Optional[str]): Code suggestions
        """
        st.session_state[f"{self.key_prefix}_suggestions"] = suggestions
        if suggestions:
            st.session_state[f"{self.key_prefix}_suggestion_time"] = time.time()
            self._calculate_diff()
    
    def get_suggestions(self) -> Optional[str]:
        """
        Get current code suggestions.
        
        Returns:
            Optional[str]: Current suggestions
        """
        return st.session_state[f"{self.key_prefix}_suggestions"]
    
    def _calculate_diff(self) -> None:
        """Calculate the diff between original code and suggestions."""
        original = st.session_state[f"{self.key_prefix}_content"]
        suggested = st.session_state[f"{self.key_prefix}_suggestions"]
        
        if not original or not suggested:
            st.session_state[f"{self.key_prefix}_diff"] = None
            return
            
        # Extract code from Markdown code blocks if present
        if "```" in suggested:
            lines = suggested.split("\n")
            code_lines = []
            in_code_block = False
            
            for line in lines:
                if line.startswith("```"):
                    in_code_block = not in_code_block
                    continue
                if in_code_block:
                    code_lines.append(line)
                    
            if code_lines:
                suggested = "\n".join(code_lines)
        
        # Generate diff
        diff = difflib.unified_diff(
            original.splitlines(),
            suggested.splitlines(),
            lineterm="",
            n=3
        )
        
        st.session_state[f"{self.key_prefix}_diff"] = "\n".join(diff)
    
    def render_suggestions(self, 
                          placeholder: Optional[st.delta_generator.DeltaGenerator] = None,
                          implement_callback: Optional[Callable[[], None]] = None) -> None:
        """
        Render code suggestions in the Streamlit app.
        
        Args:
            placeholder (st.delta_generator.DeltaGenerator): Optional placeholder
            implement_callback (Callable): Callback for implementing suggestions
        """
        # Use the provided placeholder or the current Streamlit context
        suggestions_container = placeholder if placeholder else st
        
        suggestions = st.session_state[f"{self.key_prefix}_suggestions"]
        
        if suggestions:
            # Display the suggestions
            suggestions_container.subheader("Code Suggestions")
            
            # Extract code from markdown code blocks if present
            if "```" in suggestions:
                # Display as is since Streamlit will render the markdown
                suggestions_container.markdown(suggestions)
            else:
                # Display as code block
                language = st.session_state[f"{self.key_prefix}_language"]
                suggestions_container.code(suggestions, language=language)
            
            # Show diff if available
            diff = st.session_state[f"{self.key_prefix}_diff"]
            if diff:
                suggestions_container.subheader("Changes")
                suggestions_container.code(diff, language="diff")
            
            # Button to implement suggestions
            if implement_callback and st.session_state[f"{self.key_prefix}_suggestions"]:
                if suggestions_container.button("Implement Suggestions", key=f"{self.key_prefix}_implement_button"):
                    implement_callback()
    
    def implement_suggestions(self) -> None:
        """Implement the current suggestions in the editor."""
        suggestions = st.session_state[f"{self.key_prefix}_suggestions"]
        
        if suggestions:
            # Extract code from markdown code blocks if present
            if "```" in suggestions:
                lines = suggestions.split("\n")
                code_lines = []
                in_code_block = False
                
                for line in lines:
                    if line.startswith("```"):
                        in_code_block = not in_code_block
                        continue
                    if in_code_block:
                        code_lines.append(line)
                        
                if code_lines:
                    suggestions = "\n".join(code_lines)
            
            # Update the editor content
            st.session_state[f"{self.key_prefix}_content"] = suggestions
            
            # Clear suggestions
            st.session_state[f"{self.key_prefix}_suggestions"] = None
            st.session_state[f"{self.key_prefix}_diff"] = None
    
    def should_auto_suggest(self, idle_seconds: int = 5) -> bool:
        """
        Determine if auto-suggestions should be triggered.
        
        Args:
            idle_seconds (int): Seconds to wait before suggesting
            
        Returns:
            bool: True if auto-suggest should be triggered
        """
        if not st.session_state[f"{self.key_prefix}_autosuggest"]:
            return False
            
        if not st.session_state[f"{self.key_prefix}_content"]:
            return False
            
        # Check if content is available and there are no current suggestions
        has_content = bool(st.session_state[f"{self.key_prefix}_content"])
        has_suggestions = bool(st.session_state[f"{self.key_prefix}_suggestions"])
        
        # Calculate time since last edit
        last_suggestion_time = st.session_state[f"{self.key_prefix}_suggestion_time"]
        current_time = time.time()
        time_since_last_suggestion = current_time - last_suggestion_time
        
        # Trigger suggestion if:
        # - Auto-suggest is enabled
        # - There is content
        # - No current suggestions
        # - Last suggestion was more than idle_seconds ago
        return (
            has_content and 
            not has_suggestions and 
            (time_since_last_suggestion > idle_seconds)
        )
    
    def explain_code(self, placeholder: Optional[st.delta_generator.DeltaGenerator] = None) -> None:
        """
        Show code explanation UI.
        
        Args:
            placeholder (st.delta_generator.DeltaGenerator): Optional placeholder
        """
        explain_container = placeholder if placeholder else st
        
        code = st.session_state[f"{self.key_prefix}_content"]
        
        if code:
            explain_container.subheader("Code Explanation")
            explain_container.info("Select 'Explain Code' from the actions menu to get an explanation of your code.")
    
    def reset(self) -> None:
        """Reset the editor to its initial state."""
        st.session_state[f"{self.key_prefix}_content"] = ""
        st.session_state[f"{self.key_prefix}_suggestions"] = None
        st.session_state[f"{self.key_prefix}_diff"] = None
