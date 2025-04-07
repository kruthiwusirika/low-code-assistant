"""
Local model utilities for code generation using Hugging Face models.
"""
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Safely import torch and transformers
try:
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    TORCH_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Error importing torch or transformers: {e}")
    TORCH_AVAILABLE = False



# Dict of supported models with their Hugging Face IDs
SUPPORTED_MODELS = {
    "StarCoder (1B)": "bigcode/starcoder-1b",
    "CodeLlama (7B)": "codellama/CodeLlama-7b-hf",
    "TinyLlama-1.1B-Chat": "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
    "Phi-2": "microsoft/phi-2",
}

# Cache for loaded models and tokenizers
loaded_models = {}
loaded_tokenizers = {}

def get_model_size(model_name):
    """Get approximate model size in GB based on model name"""
    size_map = {
        "bigcode/starcoder-1b": 2,  # ~2GB
        "codellama/CodeLlama-7b-hf": 14,  # ~14GB
        "TinyLlama/TinyLlama-1.1B-Chat-v1.0": 2.5,  # ~2.5GB
        "microsoft/phi-2": 2,  # ~2GB
    }
    return size_map.get(model_name, 5)  # Default to 5GB if unknown

def load_model(model_key):
    """Load a model and tokenizer from Hugging Face Hub.
    Caches models to avoid reloading.
    
    Args:
        model_key: Key from SUPPORTED_MODELS dict
        
    Returns:
        Tuple of (model, tokenizer)
    """
    if not TORCH_AVAILABLE:
        logger.error("PyTorch or Transformers not available. Please install the required dependencies.")
        return None, None
        
    try:
        model_name = SUPPORTED_MODELS.get(model_key)
        if not model_name:
            logger.error(f"Model {model_key} not found in supported models")
            return None, None
            
        # Check if model is already loaded
        if model_name in loaded_models:
            logger.info(f"Using cached model: {model_name}")
            return loaded_models[model_name], loaded_tokenizers[model_name]
            
        # Check available GPU memory
        if torch.cuda.is_available():
            free_gpu_memory = torch.cuda.get_device_properties(0).total_memory / (1024**3)  # in GB
            model_size = get_model_size(model_name)
            
            if free_gpu_memory < model_size * 1.5:  # Need ~1.5x model size as free memory
                logger.warning(f"Limited GPU memory ({free_gpu_memory:.2f}GB) for {model_name} ({model_size}GB). Using CPU.")
                device_map = "cpu"
                torch_dtype = torch.float32
            else:
                logger.info(f"Using GPU for model inference")
                device_map = "auto"
                torch_dtype = torch.float16
        else:
            logger.info("No GPU detected, using CPU")
            device_map = "cpu"
            torch_dtype = torch.float32
            
        # Load tokenizer
        logger.info(f"Loading tokenizer for {model_name}")
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        
        # Load model with appropriate settings
        logger.info(f"Loading model {model_name}")
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch_dtype,
            device_map=device_map,
            low_cpu_mem_usage=True,
        )
        
        # Cache the loaded model and tokenizer
        loaded_models[model_name] = model
        loaded_tokenizers[model_name] = tokenizer
        
        return model, tokenizer
        
    except Exception as e:
        logger.error(f"Error loading model {model_key}: {str(e)}")
        return None, None
        
def is_available():
    """Check if local models are available"""
    return TORCH_AVAILABLE

def generate_code_local(model, tokenizer, prompt, max_tokens=500, temperature=0.7):
    """
    Generate code using a local Hugging Face model
    
    Args:
        model: Loaded model
        tokenizer: Loaded tokenizer
        prompt: Text prompt for code generation
        max_tokens: Maximum tokens to generate
        temperature: Temperature for sampling (0.0 to 1.0)
        
    Returns:
        Generated code as string
    """
    try:
        # Prepare input
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
        
        # Generate
        with torch.no_grad():
            outputs = model.generate(
                inputs.input_ids,
                max_new_tokens=max_tokens,
                temperature=temperature if temperature > 0 else 1.0,
                do_sample=temperature > 0,
                top_p=0.95,
                pad_token_id=tokenizer.eos_token_id,
            )
        
        # Decode
        generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Extract just the generated part (not the prompt)
        if generated_text.startswith(prompt):
            generated_text = generated_text[len(prompt):]
            
        return generated_text.strip()
        
    except Exception as e:
        logger.error(f"Error generating code with local model: {str(e)}")
        return f"Error generating code: {str(e)}"

def get_system_info():
    """Get system information for model loading guidance"""
    if not TORCH_AVAILABLE:
        return {
            "cuda_available": False,
            "device_count": 0,
            "device_name": "N/A",
            "error": "PyTorch not available"
        }
        
    try:
        info = {
            "cuda_available": torch.cuda.is_available(),
            "device_count": torch.cuda.device_count() if torch.cuda.is_available() else 0,
            "device_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "N/A",
        }
        
        if torch.cuda.is_available():
            info["gpu_memory"] = round(torch.cuda.get_device_properties(0).total_memory / (1024**3), 2)  # GB
            
        return info
    except Exception as e:
        logger.error(f"Error getting system info: {e}")
        return {
            "cuda_available": False,
            "device_count": 0,
            "device_name": "Error detecting GPU",
            "error": str(e)
        }

def clean_generated_code(generated_text, language):
    """Clean up the generated code to extract just the code part"""
    # If the text contains markdown code blocks, extract them
    if "```" in generated_text:
        blocks = generated_text.split("```")
        # Look for a block that starts with the language or is the second block
        for i, block in enumerate(blocks):
            if i % 2 == 1:  # This is a code block (after an opening ```)
                # If first line might be the language identifier, remove it
                lines = block.split('\n')
                if len(lines) > 1 and (lines[0].strip().lower() == language.lower() or 
                                     not lines[0].strip() or
                                     not any(c.isalnum() for c in lines[0])):
                    return '\n'.join(lines[1:]).strip()
                return block.strip()
        
    return generated_text.strip()
