# Low-Code Assistant

![Low-Code Assistant Logo](https://img.shields.io/badge/Low--Code%20Assistant-v1.0-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-1.22.0+-red)
![Python](https://img.shields.io/badge/Python-3.8+-green)
![OpenAI](https://img.shields.io/badge/OpenAI-API-orange)

A powerful AI-powered code generation tool designed specifically for low-code teams. This application helps developers quickly generate, understand, and transform code using OpenAI's language models.

## 🚀 Features

- **AI-Powered Code Generation**: Generate code snippets in multiple programming languages
- **Multiple Programming Languages**: Support for Python, JavaScript, Java, C#, and more
- **Customizable Output**: Control verbosity, comments, and error handling
- **Secure API Key Management**: Your OpenAI API key is stored securely
- **Simple, Intuitive UI**: Built with Streamlit for a clean, responsive interface

## 📋 Prerequisites

- Python 3.8 or higher
- OpenAI API key ([Get one here](https://platform.openai.com/account/api-keys))
- Git (for cloning the repository)

## 🔧 Local Setup

### 1. Clone the Repository

```bash
# Clone the repository
git clone https://github.com/yourusername/low-code-assistant.git
cd low-code-assistant
```

### 2. Create a Virtual Environment

```bash
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Up Your OpenAI API Key

Create a `.env` file in the project root directory:

```env
# OpenAI API Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Application Settings
APP_ENV=development
```

Alternatively, you can add your API key through the application's User Account Setup section when you run the app.

### 5. Run the Application

```bash
# Run the simplified version (recommended for first-time users)
streamlit run simple_app.py

# Or run the full application (requires fixing template_manager.py first)
# streamlit run app/main.py
```

The application will open in your browser at `http://localhost:8501`

## 🧠 Using the Application

1. **Configure API Key**: Use the "User Account Setup" section in the sidebar to configure your OpenAI API key (if not set in .env)
2. **Select Settings**: Choose the AI model, temperature, and token limit
3. **Generate Code**: 
   - Select your programming language
   - Choose the type of code you want to generate
   - Describe what you want the code to do
   - Set advanced options for comments, error handling, and code style
   - Click "Generate Code"
4. **Use Generated Code**: View, edit, and download the generated code

## 🔄 Making Changes & Pushing to Git

### Setting Up Git Repository

```bash
# Initialize Git repository (if not cloned)
git init

# Add all files
git add .

# Create initial commit
git commit -m "Initial commit of Low-Code Assistant"

# Add remote repository
git remote add origin https://github.com/yourusername/low-code-assistant.git

# Push to GitHub
git push -u origin main
```

### Important: Protect Your API Key

Make sure your `.env` file is included in `.gitignore` to prevent your API key from being pushed to GitHub:

```bash
# Create or edit .gitignore
echo ".env" >> .gitignore
git add .gitignore
git commit -m "Add .gitignore to protect API keys"
```

## 🧩 Project Structure

```
low_code_assistant/
├── app/               # Full application code
│   ├── __init__.py
│   └── main.py       # Main application entry point
├── utils/            # Utility modules
│   ├── __init__.py
│   ├── code_generator.py  # AI code generation logic
│   └── template_manager.py  # Template management
├── templates/        # Code templates
├── static/           # Static assets (CSS, images)
├── config/           # Configuration files
├── .env              # Environment variables (not in git)
├── .env.template     # Template for environment variables
├── requirements.txt  # Project dependencies
├── simple_app.py     # Simplified application version
├── run.py            # Helper script to run the application
└── README.md         # Project documentation
```

## 🛠️ Troubleshooting

- **API Key Issues**: If you get errors about the API key, check that it's correctly set in `.env` or in the UI
- **Model Not Found**: If you get a "model not found" error, try selecting a different model from the dropdown
- **Dependency Errors**: If you have issues with dependencies, try updating pip: `pip install --upgrade pip`
- **Connectivity Issues**: Make sure you have an internet connection to access the OpenAI API

## 📄 License

MIT

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---

Created with ❤️ for low-code teams
