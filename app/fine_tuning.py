"""
Fine-tuning module for LLM-Driven Coding Assistant.
Handles training and fine-tuning models on GitHub repositories.
"""
import os
import logging
import subprocess
import tempfile
import json
import shutil
from typing import Dict, Any, List, Optional, Union
import importlib.util

# For GitHub API access
import requests
from pathlib import Path

# Check if training libraries are installed
torch_available = importlib.util.find_spec("torch") is not None
transformers_available = importlib.util.find_spec("transformers") is not None
datasets_available = importlib.util.find_spec("datasets") is not None
peft_available = importlib.util.find_spec("peft") is not None

if torch_available and transformers_available and datasets_available:
    import torch
    from transformers import (
        AutoTokenizer, AutoModelForCausalLM, 
        Trainer, TrainingArguments,
        DataCollatorForLanguageModeling
    )
    from datasets import load_dataset, Dataset
    
    if peft_available:
        from peft import (
            LoraConfig, 
            get_peft_model, 
            prepare_model_for_kbit_training,
            PeftModel
        )

class GitHubRepoFetcher:
    """Utility class to fetch code from GitHub repositories."""
    
    def __init__(self, github_token: Optional[str] = None):
        """
        Initialize the GitHub repo fetcher.
        
        Args:
            github_token (str, optional): GitHub API token for higher rate limits
        """
        self.github_token = github_token or os.environ.get("GITHUB_TOKEN", "")
        self.logger = logging.getLogger(__name__)
        
    def fetch_repository(self, repo_url: str, target_dir: str) -> bool:
        """
        Fetch a GitHub repository to a local directory.
        
        Args:
            repo_url (str): GitHub repository URL
            target_dir (str): Directory to clone the repository to
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Create target directory if it doesn't exist
            os.makedirs(target_dir, exist_ok=True)
            
            # Clone the repository
            command = f"git clone {repo_url} {target_dir}"
            self.logger.info(f"Cloning repository: {repo_url}")
            
            result = subprocess.run(
                command,
                shell=True,
                check=True,
                capture_output=True,
                text=True
            )
            self.logger.info(f"Repository cloned to {target_dir}")
            return True
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Error cloning repository: {e.stderr}")
            return False
        except Exception as e:
            self.logger.error(f"Error fetching repository: {str(e)}")
            return False
            
    def search_repositories(self, language: str, min_stars: int = 100, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search for popular repositories of a specific language.
        
        Args:
            language (str): Programming language to search for
            min_stars (int): Minimum number of stars
            limit (int): Maximum number of repositories to return
            
        Returns:
            List[Dict[str, Any]]: List of repository information
        """
        try:
            # Prepare the GitHub API request
            url = f"https://api.github.com/search/repositories"
            query = f"language:{language} stars:>={min_stars} fork:false"
            params = {
                "q": query,
                "sort": "stars",
                "order": "desc",
                "per_page": limit
            }
            
            headers = {}
            if self.github_token:
                headers["Authorization"] = f"token {self.github_token}"
                
            # Make the API request
            response = requests.get(url, params=params, headers=headers)
            response.raise_for_status()
            
            # Parse the response
            data = response.json()
            repos = []
            
            for item in data.get("items", []):
                repos.append({
                    "name": item["name"],
                    "full_name": item["full_name"],
                    "url": item["html_url"],
                    "clone_url": item["clone_url"],
                    "stars": item["stargazers_count"],
                    "description": item["description"],
                    "language": item["language"]
                })
                
            return repos
            
        except Exception as e:
            self.logger.error(f"Error searching repositories: {str(e)}")
            return []

class ModelFineTuner:
    """Handles fine-tuning models on code repositories."""
    
    def __init__(self, base_model_name: str, output_dir: str):
        """
        Initialize the model fine-tuner.
        
        Args:
            base_model_name (str): Name of the base model to fine-tune
            output_dir (str): Directory to save the fine-tuned model
        """
        self.base_model_name = base_model_name
        self.output_dir = output_dir
        self.logger = logging.getLogger(__name__)
        
        # Check if required libraries are available
        self.can_train = (
            torch_available and 
            transformers_available and 
            datasets_available
        )
        
        if not self.can_train:
            missing_libs = []
            if not torch_available:
                missing_libs.append("torch")
            if not transformers_available:
                missing_libs.append("transformers")
            if not datasets_available:
                missing_libs.append("datasets")
                
            self.logger.error(f"Fine-tuning requires {', '.join(missing_libs)} libraries")
        
    def prepare_code_dataset(self, 
                            repo_dir: str, 
                            language: str,
                            extensions: List[str],
                            max_files: int = 100) -> Optional[Dataset]:
        """
        Prepare a code dataset from a repository.
        
        Args:
            repo_dir (str): Directory containing the repository
            language (str): Programming language
            extensions (List[str]): File extensions to include
            max_files (int): Maximum number of files to include
            
        Returns:
            Dataset: The prepared dataset
        """
        if not self.can_train:
            self.logger.error("Training libraries not available")
            return None
        
        try:
            # Find all code files with the specified extensions
            code_files = []
            for ext in extensions:
                if not ext.startswith("."):
                    ext = f".{ext}"
                    
                for file_path in Path(repo_dir).glob(f"**/*{ext}"):
                    if file_path.is_file():
                        code_files.append(str(file_path))
                        
                        if len(code_files) >= max_files:
                            break
                            
                if len(code_files) >= max_files:
                    break
            
            self.logger.info(f"Found {len(code_files)} {language} files")
            
            # Read the contents of each file
            code_contents = []
            for file_path in code_files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as file:
                        content = file.read()
                        
                        # Skip very large files
                        if len(content) > 50000:
                            continue
                            
                        # Format as training example
                        code_contents.append({
                            "text": f"```{language}\n{content}\n```"
                        })
                except Exception as e:
                    self.logger.warning(f"Error reading file {file_path}: {str(e)}")
                    continue
            
            self.logger.info(f"Prepared {len(code_contents)} code examples")
            
            # Create a dataset
            dataset = Dataset.from_list(code_contents)
            return dataset
            
        except Exception as e:
            self.logger.error(f"Error preparing dataset: {str(e)}")
            return None
            
    def fine_tune_model(self, 
                        dataset: Dataset, 
                        use_lora: bool = True,
                        epochs: int = 3,
                        learning_rate: float = 2e-5,
                        batch_size: int = 4) -> bool:
        """
        Fine-tune a model on a code dataset.
        
        Args:
            dataset (Dataset): The dataset to fine-tune on
            use_lora (bool): Whether to use LoRA for efficient fine-tuning
            epochs (int): Number of training epochs
            learning_rate (float): Learning rate
            batch_size (int): Batch size
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.can_train:
            self.logger.error("Training libraries not available")
            return False
            
        if not peft_available and use_lora:
            self.logger.warning("PEFT library not available, disabling LoRA")
            use_lora = False
        
        try:
            # Create output directory
            os.makedirs(self.output_dir, exist_ok=True)
            
            # Load tokenizer and model
            self.logger.info(f"Loading base model: {self.base_model_name}")
            tokenizer = AutoTokenizer.from_pretrained(self.base_model_name)
            
            # Add pad token if it doesn't exist
            if tokenizer.pad_token is None:
                tokenizer.pad_token = tokenizer.eos_token
            
            # Configure model loading based on available hardware
            device_map = "auto"
            if torch.cuda.is_available():
                self.logger.info("CUDA available, using GPU")
            else:
                self.logger.info("CUDA not available, using CPU")
                device_map = "cpu"
                
            # Load the model with appropriate settings
            if use_lora:
                model = AutoModelForCausalLM.from_pretrained(
                    self.base_model_name,
                    load_in_8bit=True if torch.cuda.is_available() else False,
                    device_map=device_map,
                )
                
                # Prepare model for training if using 8-bit
                if torch.cuda.is_available():
                    model = prepare_model_for_kbit_training(model)
                
                # Set up LoRA configuration
                lora_config = LoraConfig(
                    r=16,  # Rank
                    lora_alpha=32,
                    target_modules=["q_proj", "v_proj"],
                    lora_dropout=0.05,
                    bias="none",
                    task_type="CAUSAL_LM"
                )
                
                # Create LoRA model
                model = get_peft_model(model, lora_config)
                model.print_trainable_parameters()
            else:
                model = AutoModelForCausalLM.from_pretrained(
                    self.base_model_name,
                    device_map=device_map,
                )
            
            # Tokenize the dataset
            def tokenize_function(examples):
                return tokenizer(
                    examples["text"],
                    truncation=True,
                    padding="max_length",
                    max_length=1024
                )
                
            tokenized_dataset = dataset.map(
                tokenize_function,
                batched=True,
                remove_columns=["text"]
            )
            
            # Create data collator
            data_collator = DataCollatorForLanguageModeling(
                tokenizer=tokenizer,
                mlm=False  # We're not using masked language modeling
            )
            
            # Set up training arguments
            training_args = TrainingArguments(
                output_dir=self.output_dir,
                overwrite_output_dir=True,
                num_train_epochs=epochs,
                per_device_train_batch_size=batch_size,
                learning_rate=learning_rate,
                weight_decay=0.01,
                logging_dir=os.path.join(self.output_dir, "logs"),
                logging_steps=100,
                save_strategy="epoch",
            )
            
            # Initialize trainer
            trainer = Trainer(
                model=model,
                args=training_args,
                train_dataset=tokenized_dataset,
                data_collator=data_collator,
            )
            
            # Start training
            self.logger.info("Starting fine-tuning")
            trainer.train()
            
            # Save model and tokenizer
            self.logger.info(f"Saving fine-tuned model to {self.output_dir}")
            model.save_pretrained(self.output_dir)
            tokenizer.save_pretrained(self.output_dir)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error fine-tuning model: {str(e)}")
            return False
    
    @staticmethod
    def get_file_extensions(language: str) -> List[str]:
        """
        Get file extensions for a programming language.
        
        Args:
            language (str): Programming language
            
        Returns:
            List[str]: List of file extensions
        """
        extensions = {
            "python": ["py"],
            "javascript": ["js", "jsx"],
            "typescript": ["ts", "tsx"],
            "java": ["java"],
            "c++": ["cpp", "cxx", "cc", "h", "hpp"],
            "c": ["c", "h"],
            "c#": ["cs"],
            "go": ["go"],
            "ruby": ["rb"],
            "php": ["php"],
            "rust": ["rs"],
            "swift": ["swift"],
            "kotlin": ["kt", "kts"],
            "scala": ["scala"],
            "html": ["html", "htm"],
            "css": ["css"],
            "sql": ["sql"],
        }
        
        return extensions.get(language.lower(), [])

def fine_tune_on_repositories(base_model_name: str, 
                             language: str,
                             output_dir: str,
                             num_repos: int = 3,
                             github_token: Optional[str] = None) -> bool:
    """
    Fine-tune a model on GitHub repositories for a specific language.
    
    Args:
        base_model_name (str): Name of the base model to fine-tune
        language (str): Programming language to fine-tune on
        output_dir (str): Directory to save the fine-tuned model
        num_repos (int): Number of repositories to use
        github_token (str, optional): GitHub API token
        
    Returns:
        bool: True if successful, False otherwise
    """
    logger = logging.getLogger(__name__)
    
    # Check requirements
    if not (torch_available and transformers_available and datasets_available):
        logger.error("Training libraries not available")
        return False
    
    try:
        # Create fetcher and tuner
        fetcher = GitHubRepoFetcher(github_token=github_token)
        tuner = ModelFineTuner(
            base_model_name=base_model_name,
            output_dir=output_dir
        )
        
        # Search for repositories
        repos = fetcher.search_repositories(
            language=language,
            min_stars=500,  # Popular repos
            limit=num_repos
        )
        
        if not repos:
            logger.error(f"No repositories found for language: {language}")
            return False
            
        # Get file extensions for the language
        extensions = ModelFineTuner.get_file_extensions(language)
        
        if not extensions:
            logger.error(f"No file extensions defined for language: {language}")
            return False
        
        # Prepare a temporary directory for repos
        with tempfile.TemporaryDirectory() as temp_dir:
            # Fetch repositories and prepare dataset
            all_datasets = []
            
            for repo in repos:
                repo_dir = os.path.join(temp_dir, repo["name"])
                
                # Clone the repository
                success = fetcher.fetch_repository(
                    repo_url=repo["clone_url"],
                    target_dir=repo_dir
                )
                
                if not success:
                    logger.warning(f"Failed to fetch repository: {repo['name']}")
                    continue
                
                # Prepare dataset
                dataset = tuner.prepare_code_dataset(
                    repo_dir=repo_dir,
                    language=language,
                    extensions=extensions,
                    max_files=100
                )
                
                if dataset is not None:
                    all_datasets.append(dataset)
            
            if not all_datasets:
                logger.error("No datasets were created")
                return False
            
            # Combine all datasets
            combined_dataset = datasets.concatenate_datasets(all_datasets)
            
            # Fine-tune the model
            success = tuner.fine_tune_model(
                dataset=combined_dataset,
                use_lora=True,
                epochs=3
            )
            
            return success
            
    except Exception as e:
        logger.error(f"Error in fine-tuning workflow: {str(e)}")
        return False
