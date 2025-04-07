"""
Model Manager for LLM-Driven Coding Assistant.
Handles different model types, including API-based and local open-source models.
"""
import os
import json
import logging
from typing import Dict, Any, List, Optional, Union
import importlib.util

# Support for various LLM providers
import openai
# Check if transformers is installed for local models
transformers_available = importlib.util.find_spec("transformers") is not None
if transformers_available:
    import torch
    from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline

class ModelManager:
    """
    Manager for handling different LLM models for code generation.
    Supports both API-based models like OpenAI and local open-source models.
    """
    
    def __init__(self, model_config: Optional[Dict[str, Any]] = None):
        """
        Initialize the ModelManager with configuration.
        
        Args:
            model_config (Dict[str, Any], optional): Model configuration
        """
        # Set up logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Default configurations
        self.default_config = {
            "api_models": {
                "openai": {
                    "model": "gpt-4",
                    "temperature": 0.3,
                    "max_tokens": 2048,
                }
            },
            "local_models": {
                "code_llama": {
                    "model_name": "codellama/CodeLlama-7b-Instruct-hf",
                    "device": "cpu",  # or "cuda" if GPU available
                    "load_in_8bit": False,
                }
            }
        }
        
        # Initialize with provided or default config
        self.config = model_config or self.default_config
        
        # Initialized models
        self.api_clients = {}
        self.local_models = {}
        
        # Environment variables
        self.openai_api_key = os.environ.get("OPENAI_API_KEY", "")
        
        # Current active model
        self.active_model_type = "api"  # 'api' or 'local'
        self.active_model_name = "openai"
        
    def use_api_model(self, api_name: str = "openai", api_key: Optional[str] = None) -> None:
        """
        Configure the manager to use an API-based model.
        
        Args:
            api_name (str): The API provider name ("openai", etc.)
            api_key (str, optional): API key to use
        """
        if api_name == "openai":
            if api_key:
                self.openai_api_key = api_key
            
            if not self.openai_api_key:
                self.logger.error("OpenAI API key is required")
                return
            
            self.api_clients["openai"] = openai.OpenAI(api_key=self.openai_api_key)
            self.active_model_type = "api"
            self.active_model_name = "openai"
            self.logger.info(f"Using OpenAI API model: {self.config['api_models']['openai']['model']}")
        else:
            self.logger.error(f"API provider '{api_name}' not supported")
    
    def use_local_model(self, model_name: str = "code_llama") -> None:
        """
        Configure the manager to use a local model.
        
        Args:
            model_name (str): Name of the local model as specified in config
        """
        if not transformers_available:
            self.logger.error("Transformers library not installed. Cannot use local models.")
            return
            
        if model_name not in self.config["local_models"]:
            self.logger.error(f"Local model '{model_name}' not found in configuration")
            return
        
        if model_name not in self.local_models:
            # Load model if not already loaded
            try:
                model_config = self.config["local_models"][model_name]
                model_id = model_config["model_name"]
                device = model_config["device"]
                
                self.logger.info(f"Loading local model: {model_id} on {device}")
                
                tokenizer = AutoTokenizer.from_pretrained(model_id)
                
                # Configure loading options based on hardware
                load_options = {}
                if device == "cuda" and torch.cuda.is_available():
                    if model_config.get("load_in_8bit", False):
                        load_options["load_in_8bit"] = True
                    
                model = AutoModelForCausalLM.from_pretrained(
                    model_id,
                    device_map=device,
                    **load_options
                )
                
                # Create a text generation pipeline
                gen_pipeline = pipeline(
                    "text-generation", 
                    model=model, 
                    tokenizer=tokenizer
                )
                
                self.local_models[model_name] = {
                    "pipeline": gen_pipeline,
                    "tokenizer": tokenizer,
                    "model": model,
                }
                
                self.active_model_type = "local"
                self.active_model_name = model_name
                self.logger.info(f"Local model '{model_name}' loaded successfully")
            
            except Exception as e:
                self.logger.error(f"Error loading local model '{model_name}': {str(e)}")
                return
        else:
            # Model already loaded
            self.active_model_type = "local"
            self.active_model_name = model_name
            self.logger.info(f"Using previously loaded local model '{model_name}'")
    
    def get_code_suggestion(self, code: str, language: str, instruction: str = "Improve this code") -> str:
        """
        Get code suggestions from the active model.
        
        Args:
            code (str): The code to improve
            language (str): Programming language
            instruction (str): Specific instruction for improvement
            
        Returns:
            str: Improved code or error message
        """
        if self.active_model_type == "api":
            return self._get_api_suggestion(code, language, instruction)
        elif self.active_model_type == "local":
            return self._get_local_suggestion(code, language, instruction)
        else:
            return "Error: No active model configured"
    
    def _get_api_suggestion(self, code: str, language: str, instruction: str) -> str:
        """Get suggestion using API-based model."""
        if self.active_model_name == "openai":
            try:
                client = self.api_clients.get("openai")
                if not client:
                    return "Error: OpenAI client not initialized"
                
                model_config = self.config["api_models"]["openai"]
                
                # Prepare the prompt
                prompt = f"""
                You are an AI assistant specialized in {language} programming.
                
                {instruction}
                
                ```{language}
                {code}
                ```
                
                Please provide the improved code wrapped in triple backticks with the language specifier.
                Only include the improved code, not explanations.
                """
                
                response = client.chat.completions.create(
                    model=model_config["model"],
                    messages=[{"role": "user", "content": prompt}],
                    temperature=model_config["temperature"],
                    max_tokens=model_config["max_tokens"],
                )
                
                return response.choices[0].message.content
                
            except Exception as e:
                self.logger.error(f"OpenAI API error: {str(e)}")
                return f"Error: {str(e)}"
        else:
            return f"Error: API provider '{self.active_model_name}' not supported"
    
    def _get_local_suggestion(self, code: str, language: str, instruction: str) -> str:
        """Get suggestion using local model."""
        if not transformers_available:
            return "Error: Transformers library not installed"
            
        if self.active_model_name not in self.local_models:
            return f"Error: Local model '{self.active_model_name}' not loaded"
        
        try:
            model_data = self.local_models[self.active_model_name]
            gen_pipeline = model_data["pipeline"]
            
            # Format prompt based on the model
            if "llama" in self.active_model_name.lower():
                # CodeLlama style prompt
                prompt = f"""<s>[INST] 
                You are an AI assistant specialized in {language} programming.
                
                {instruction}
                
                ```{language}
                {code}
                ```
                
                Provide only the improved code wrapped in triple backticks with the language specifier.
                [/INST]
                """
            else:
                # Generic prompt
                prompt = f"""
                You are an AI assistant specialized in {language} programming.
                
                {instruction}
                
                ```{language}
                {code}
                ```
                
                Provide only the improved code wrapped in triple backticks with the language specifier.
                """
            
            # Generate text with the local model
            result = gen_pipeline(
                prompt,
                max_length=len(prompt) + 2048,
                do_sample=True,
                temperature=0.3,
                top_p=0.95,
                num_return_sequences=1,
            )
            
            generated_text = result[0]["generated_text"]
            # Extract only the added content (remove the prompt)
            if len(generated_text) > len(prompt):
                suggestion = generated_text[len(prompt):].strip()
            else:
                suggestion = generated_text.strip()
                
            return suggestion
            
        except Exception as e:
            self.logger.error(f"Local model error: {str(e)}")
            return f"Error: {str(e)}"
    
    def get_available_models(self) -> Dict[str, List[str]]:
        """
        Get a list of available models.
        
        Returns:
            Dict[str, List[str]]: Dictionary of available models by type
        """
        return {
            "api": list(self.config["api_models"].keys()),
            "local": list(self.config["local_models"].keys())
        }
    
    def is_local_model_available(self, model_name: str) -> bool:
        """
        Check if a local model is available and can be loaded.
        
        Args:
            model_name (str): Name of model to check
            
        Returns:
            bool: True if model is available
        """
        if not transformers_available:
            return False
            
        if model_name not in self.config["local_models"]:
            return False
            
        model_config = self.config["local_models"][model_name]
        model_id = model_config["model_name"]
        
        # Check if model exists in Hugging Face
        try:
            AutoTokenizer.from_pretrained(model_id, local_files_only=True)
            return True
        except:
            # Model not available locally, would need to be downloaded
            return False
