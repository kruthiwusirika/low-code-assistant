import os
import openai
from typing import Dict, Any, List, Optional
import logging

class CodeGenerator:
    """
    Handles code generation using OpenAI's language models.
    """
    
    def __init__(self):
        """Initialize the CodeGenerator."""
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model = os.getenv("OPENAI_MODEL", "gpt-4")
        
        # Set up logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Validate API key
        if not self.api_key:
            self.logger.warning("OpenAI API key not found in environment variables")
    
    def _set_api_key(self, api_key: str) -> None:
        """
        Set the OpenAI API key.
        
        Args:
            api_key (str): The OpenAI API key
        """
        self.api_key = api_key
        os.environ["OPENAI_API_KEY"] = api_key
    
    def _create_prompt(self, 
                       description: str, 
                       language: str, 
                       code_type: str,
                       include_comments: bool = True,
                       error_handling: bool = True,
                       code_style: str = "Standard") -> str:
        """
        Create a prompt for code generation.
        
        Args:
            description (str): Description of the code to generate
            language (str): Programming language
            code_type (str): Type of code (function, class, etc.)
            include_comments (bool): Whether to include detailed comments
            error_handling (bool): Whether to include error handling
            code_style (str): Code style preference
            
        Returns:
            str: Formatted prompt for the language model
        """
        # Build system message with specific instructions
        system_message = (
            f"You are an expert {language} developer specializing in creating {code_type.lower()}s for low-code teams. "
            f"Your task is to generate clean, efficient, and well-structured {language} code based on the given description. "
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
            f"Generate a {language} {code_type.lower()} based on this description:\n\n{description}\n\n"
            f"Provide only the code without additional explanations. The code should be ready to use."
        )
        
        return system_message, user_message
    
    def generate(self, 
                description: str, 
                language: str, 
                code_type: str,
                include_comments: bool = True,
                error_handling: bool = True,
                code_style: str = "Standard") -> str:
        """
        Generate code based on the given parameters.
        
        Args:
            description (str): Description of the code to generate
            language (str): Programming language
            code_type (str): Type of code (function, class, etc.)
            include_comments (bool): Whether to include detailed comments
            error_handling (bool): Whether to include error handling
            code_style (str): Code style preference
            
        Returns:
            str: Generated code
        """
        try:
            if not self.api_key:
                return "Error: OpenAI API key not found. Please provide your API key in the sidebar."
            
            openai.api_key = self.api_key
            
            system_message, user_message = self._create_prompt(
                description=description,
                language=language,
                code_type=code_type,
                include_comments=include_comments,
                error_handling=error_handling,
                code_style=code_style
            )
            
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.7,
                max_tokens=2000,
                n=1,
                stop=None
            )
            
            # Extract and return the generated code
            generated_code = response.choices[0].message.content.strip()
            
            # Clean up code block markers if present
            if generated_code.startswith("```") and generated_code.endswith("```"):
                # Extract the language if present (e.g., ```python)
                lines = generated_code.split('\n')
                if len(lines) > 1:
                    first_line = lines[0].strip('`').strip()
                    if first_line.lower() == language.lower() or not first_line:
                        generated_code = '\n'.join(lines[1:-1])
                    else:
                        generated_code = '\n'.join(lines[1:-1])
            
            return generated_code
            
        except Exception as e:
            self.logger.error(f"Error generating code: {str(e)}")
            return f"Error generating code: {str(e)}"
    
    def translate(self, source_code: str, source_language: str, target_language: str) -> str:
        """
        Translate code from one programming language to another.
        
        Args:
            source_code (str): Source code to translate
            source_language (str): Source programming language
            target_language (str): Target programming language
            
        Returns:
            str: Translated code
        """
        try:
            if not self.api_key:
                return "Error: OpenAI API key not found. Please provide your API key in the sidebar."
            
            openai.api_key = self.api_key
            
            system_message = (
                f"You are an expert developer skilled in both {source_language} and {target_language}. "
                f"Your task is to translate the given {source_language} code to equivalent {target_language} code. "
                f"Maintain the same functionality, logic, and structure. "
                f"Include appropriate comments in the translated code."
            )
            
            user_message = (
                f"Translate this {source_language} code to {target_language}:\n\n"
                f"{source_code}\n\n"
                f"Provide only the translated code without additional explanations."
            )
            
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.7,
                max_tokens=2000,
                n=1,
                stop=None
            )
            
            # Extract and return the translated code
            translated_code = response.choices[0].message.content.strip()
            
            # Clean up code block markers if present
            if translated_code.startswith("```") and translated_code.endswith("```"):
                lines = translated_code.split('\n')
                if len(lines) > 1:
                    first_line = lines[0].strip('`').strip()
                    if first_line.lower() == target_language.lower() or not first_line:
                        translated_code = '\n'.join(lines[1:-1])
                    else:
                        translated_code = '\n'.join(lines[1:-1])
            
            return translated_code
            
        except Exception as e:
            self.logger.error(f"Error translating code: {str(e)}")
            return f"Error translating code: {str(e)}"
    
    def explain(self, code: str, language: str, detail_level: str = "medium") -> str:
        """
        Generate an explanation for the given code.
        
        Args:
            code (str): Code to explain
            language (str): Programming language
            detail_level (str): Level of detail in the explanation (low, medium, high)
            
        Returns:
            str: Code explanation
        """
        try:
            if not self.api_key:
                return "Error: OpenAI API key not found. Please provide your API key in the sidebar."
            
            openai.api_key = self.api_key
            
            detail_mapping = {
                "low": "Provide a brief, high-level overview of what this code does.",
                "medium": "Explain the main functionality and key parts of this code.",
                "high": "Provide a detailed line-by-line explanation of this code, including any technical concepts."
            }
            
            detail_instruction = detail_mapping.get(detail_level.lower(), detail_mapping["medium"])
            
            system_message = (
                f"You are an expert {language} developer specializing in explaining code to low-code teams. "
                f"Your task is to explain the given {language} code in clear, concise terms. "
                f"{detail_instruction}"
            )
            
            user_message = f"Explain this {language} code:\n\n{code}"
            
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.7,
                max_tokens=1000,
                n=1,
                stop=None
            )
            
            # Extract and return the explanation
            explanation = response.choices[0].message.content.strip()
            return explanation
            
        except Exception as e:
            self.logger.error(f"Error explaining code: {str(e)}")
            return f"Error explaining code: {str(e)}"
    
    def improve(self, code: str, language: str, improvement_type: str = "general") -> str:
        """
        Suggest improvements for the given code.
        
        Args:
            code (str): Code to improve
            language (str): Programming language
            improvement_type (str): Type of improvement (general, performance, readability, security)
            
        Returns:
            str: Improved code with explanations
        """
        try:
            if not self.api_key:
                return "Error: OpenAI API key not found. Please provide your API key in the sidebar."
            
            openai.api_key = self.api_key
            
            improvement_mapping = {
                "general": "Provide general improvements including readability, performance, and best practices.",
                "performance": "Focus specifically on performance optimizations and efficiency improvements.",
                "readability": "Focus on making the code more readable and maintainable.",
                "security": "Focus on improving the security aspects of the code and preventing vulnerabilities."
            }
            
            improvement_instruction = improvement_mapping.get(improvement_type.lower(), improvement_mapping["general"])
            
            system_message = (
                f"You are an expert {language} developer specializing in code improvement. "
                f"Your task is to suggest improvements for the given {language} code. "
                f"{improvement_instruction}"
            )
            
            user_message = (
                f"Suggest improvements for this {language} code:\n\n{code}\n\n"
                f"Format your response with two sections:\n"
                f"1. Improved Code (just the code)\n"
                f"2. Explanation of Improvements (bulleted list)"
            )
            
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.7,
                max_tokens=2000,
                n=1,
                stop=None
            )
            
            # Extract and return the improved code with explanations
            improvements = response.choices[0].message.content.strip()
            return improvements
            
        except Exception as e:
            self.logger.error(f"Error improving code: {str(e)}")
            return f"Error improving code: {str(e)}"
