import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
import logging

def load_config(config_file: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from a JSON file.
    
    Args:
        config_file (str, optional): Path to the config file
        
    Returns:
        Dict[str, Any]: Configuration dictionary
    """
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # Default config path
    if not config_file:
        config_dir = Path(__file__).parent.parent / "config"
        config_file = config_dir / "settings.json"
    else:
        config_file = Path(config_file)
    
    # Create default config if it doesn't exist
    if not config_file.exists():
        logger.info(f"Config file not found at {config_file}. Creating default config.")
        
        # Create directory if it doesn't exist
        config_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Create default config
        default_config = {
            "api_provider": "OpenAI",
            "model": "gpt-3.5-turbo",
            "temperature": 0.7,
            "max_tokens": 1000
        }
        
        with open(config_file, "w") as f:
            json.dump(default_config, f, indent=2)
        
        return default_config
    
    # Load config from file
    try:
        with open(config_file, "r") as f:
            config = json.load(f)
        logger.info(f"Loaded configuration from {config_file}")
        return config
    except Exception as e:
        logger.error(f"Error loading config from {config_file}: {str(e)}")
        
        # Return default config in case of error
        return {
            "api_provider": "OpenAI",
            "model": "gpt-3.5-turbo",
            "temperature": 0.7,
            "max_tokens": 1000
        }
