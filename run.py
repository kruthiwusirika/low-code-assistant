#!/usr/bin/env python3
"""
Startup script for Low-Code Assistant
"""
import os
import sys
import subprocess
from pathlib import Path

def main():
    """Main function to set up and run the Low-Code Assistant."""
    # Get project root
    project_root = Path(__file__).parent.absolute()
    
    # Ensure we're in the project directory
    os.chdir(project_root)
    
    # Check if virtual environment exists and is activated
    venv_dir = project_root / "venv"
    if not venv_dir.exists():
        print("Virtual environment not found. Creating one...")
        try:
            subprocess.run(["python", "-m", "venv", "venv"], check=True)
            print("Virtual environment created successfully.")
        except subprocess.CalledProcessError as e:
            print(f"Error creating virtual environment: {str(e)}")
            sys.exit(1)
    
    # Determine the Python executable path in the virtual environment
    if sys.platform == "win32":
        python_executable = venv_dir / "Scripts" / "python.exe"
    else:
        python_executable = venv_dir / "bin" / "python"
    
    # Install requirements if needed
    requirements_file = project_root / "requirements.txt"
    if requirements_file.exists():
        print("Installing required packages...")
        try:
            subprocess.run([str(python_executable), "-m", "pip", "install", "-r", "requirements.txt"], check=True)
            print("Requirements installed successfully.")
        except subprocess.CalledProcessError as e:
            print(f"Error installing requirements: {str(e)}")
            sys.exit(1)
    
    # Check if .env file exists, create from template if not
    env_file = project_root / ".env"
    env_template = project_root / ".env.template"
    if not env_file.exists() and env_template.exists():
        print("Creating .env file from template...")
        with open(env_template, "r") as template_file:
            template_content = template_file.read()
        
        with open(env_file, "w") as env_file_obj:
            env_file_obj.write(template_content)
        
        print(".env file created. Please edit it to add your API keys.")
    
    # Create template directory and default templates
    from utils.template_manager import TemplateManager
    template_manager = TemplateManager()
    template_manager.create_default_templates()
    
    # Run the Streamlit app
    print("Starting Low-Code Assistant...")
    try:
        subprocess.run([str(python_executable), "-m", "streamlit", "run", "app/main.py"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running Streamlit app: {str(e)}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nShutting down Low-Code Assistant...")
        sys.exit(0)

if __name__ == "__main__":
    main()
