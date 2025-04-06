import os
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime

class TemplateManager:
    """
    Manages code templates for the Low-Code Assistant.
    """
    
    def __init__(self, templates_dir: Optional[str] = None):
        """
        Initialize the TemplateManager.
        
        Args:
            templates_dir (str, optional): Directory to store templates
        """
        # Set up logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Set templates directory
        if templates_dir:
            self.templates_dir = Path(templates_dir)
        else:
            # Default to project's templates directory
            self.templates_dir = Path(__file__).parent.parent / "templates"
        
        # Create templates directory if it doesn't exist
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize templates index file if it doesn't exist
        self.index_file = self.templates_dir / "index.json"
        if not self.index_file.exists():
            self._initialize_index()
    
    def _initialize_index(self) -> None:
        """Initialize the templates index file."""
        initial_index = {
            "templates": [],
            "last_updated": datetime.now().isoformat()
        }
        
        with open(self.index_file, "w") as f:
            json.dump(initial_index, f, indent=2)
            
        self.logger.info(f"Initialized templates index at {self.index_file}")
    
    def _load_index(self) -> Dict[str, Any]:
        """
        Load the templates index from disk.
        
        Returns:
            Dict[str, Any]: The templates index
        """
        try:
            with open(self.index_file, "r") as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Error loading templates index: {str(e)}")
            # If there's an error, reinitialize the index
            self._initialize_index()
            return {"templates": [], "last_updated": datetime.now().isoformat()}
    
    def _save_index(self, index: Dict[str, Any]) -> None:
        """
        Save the templates index to disk.
        
        Args:
            index (Dict[str, Any]): The templates index to save
        """
        try:
            index["last_updated"] = datetime.now().isoformat()
            with open(self.index_file, "w") as f:
                json.dump(index, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving templates index: {str(e)}")
    
    def get_template_list(self) -> List[str]:
        """
        Get a list of all available template names.
        
        Returns:
            List[str]: List of template names
        """
        index = self._load_index()
        return [template["name"] for template in index["templates"]]
    
    def get_template(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get a template by name.
        
        Args:
            name (str): Name of the template
            
        Returns:
            Dict[str, Any]: Template data or None if not found
        """
        index = self._load_index()
        for template in index["templates"]:
            if template["name"] == name:
                try:
                    # Load full template from its file
                    template_file = self.templates_dir / f"{self._sanitize_filename(name)}.json"
                    with open(template_file, "r") as f:
                        return json.load(f)
                except Exception as e:
                    self.logger.error(f"Error loading template {name}: {str(e)}")
                    return None
        
        self.logger.warning(f"Template {name} not found")
        return None
    
    def save_template(self, 
                     name: str, 
                     code: str, 
                     description: str = "", 
                     language: str = "python", 
                     code_type: str = "function") -> bool:
        """
        Save a new template.
        
        Args:
            name (str): Name of the template
            code (str): Code content
            description (str): Description of the template
            language (str): Programming language
            code_type (str): Type of code
            
        Returns:
            bool: Success status
        """
        try:
            # Prepare template data
            template_data = {
                "name": name,
                "description": description,
                "language": language,
                "code_type": code_type,
                "code": code,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            # Save template to its own file
            template_file = self.templates_dir / f"{self._sanitize_filename(name)}.json"
            with open(template_file, "w") as f:
                json.dump(template_data, f, indent=2)
            
            # Update index
            index = self._load_index()
            
            # Check if template with this name already exists
            existing = False
            for i, template in enumerate(index["templates"]):
                if template["name"] == name:
                    # Update existing entry
                    index["templates"][i] = {
                        "name": name,
                        "language": language,
                        "code_type": code_type,
                        "updated_at": datetime.now().isoformat()
                    }
                    existing = True
                    break
            
            if not existing:
                # Add new entry to index
                index["templates"].append({
                    "name": name,
                    "language": language,
                    "code_type": code_type,
                    "updated_at": datetime.now().isoformat()
                })
            
            # Save updated index
            self._save_index(index)
            
            self.logger.info(f"Template {name} saved successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving template {name}: {str(e)}")
            return False
    
    def update_template(self, name: str, code: str) -> bool:
        """
        Update an existing template's code.
        
        Args:
            name (str): Name of the template
            code (str): Updated code content
            
        Returns:
            bool: Success status
        """
        try:
            # Get existing template
            template = self.get_template(name)
            if not template:
                self.logger.warning(f"Cannot update template {name}: not found")
                return False
            
            # Update code and timestamp
            template["code"] = code
            template["updated_at"] = datetime.now().isoformat()
            
            # Save updated template
            template_file = self.templates_dir / f"{self._sanitize_filename(name)}.json"
            with open(template_file, "w") as f:
                json.dump(template, f, indent=2)
            
            # Update index entry
            index = self._load_index()
            for i, idx_template in enumerate(index["templates"]):
                if idx_template["name"] == name:
                    index["templates"][i]["updated_at"] = datetime.now().isoformat()
                    break
            
            # Save updated index
            self._save_index(index)
            
            self.logger.info(f"Template {name} updated successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating template {name}: {str(e)}")
            return False
    
    def delete_template(self, name: str) -> bool:
        """
        Delete a template.
        
        Args:
            name (str): Name of the template
            
        Returns:
            bool: Success status
        """
        try:
            # Delete template file
            template_file = self.templates_dir / f"{self._sanitize_filename(name)}.json"
            if template_file.exists():
                template_file.unlink()
            
            # Update index
            index = self._load_index()
            index["templates"] = [t for t in index["templates"] if t["name"] != name]
            self._save_index(index)
            
            self.logger.info(f"Template {name} deleted successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error deleting template {name}: {str(e)}")
            return False
    
    def _sanitize_filename(self, name: str) -> str:
        """
        Sanitize a name for use as a filename.
        
        Args:
            name (str): Name to sanitize
            
        Returns:
            str: Sanitized filename
        """
        # Replace spaces with underscores and remove special characters
        sanitized = name.replace(" ", "_")
        sanitized = "".join(c for c in sanitized if c.isalnum() or c in "_-")
        return sanitized
    
    def create_default_templates(self) -> None:
        """Create some default templates for users to start with."""
        default_templates = [
            {
                "name": "Python API Endpoint",
                "description": "A Flask API endpoint template with request validation and error handling.",
                "language": "Python",
                "code_type": "API Endpoint",
                "code": """from flask import Flask, request, jsonify
from werkzeug.exceptions import BadRequest
from functools import wraps
import json

app = Flask(__name__)

def validate_json(f):
    @wraps(f)
    def wrapper(*args, **kw):
        try:
            request.json
        except BadRequest:
            return jsonify({"error": "Invalid JSON payload"}), 400
        return f(*args, **kw)
    return wrapper

@app.route('/api/resource', methods=['POST'])
@validate_json
def create_resource():
    data = request.json
    
    # Validate required fields
    required_fields = ['name', 'type']
    missing_fields = [field for field in required_fields if field not in data]
    
    if missing_fields:
        return jsonify({
            "error": "Missing required fields",
            "fields": missing_fields
        }), 400
    
    # Process the request (replace with your actual logic)
    resource_id = 12345  # In a real app, this would be generated or retrieved from a database
    
    # Return success response
    return jsonify({
        "status": "success",
        "message": "Resource created successfully",
        "resource_id": resource_id
    }), 201

if __name__ == '__main__':
    app.run(debug=True)"""
            },
            {
                "name": "JavaScript Form Validation",
                "description": "Client-side form validation with error handling and submission.",
                "language": "JavaScript",
                "code_type": "Function",
                "code": """/**
 * Validates a form and handles submission
 * @param {string} formId - The ID of the form to validate
 * @param {function} onSuccess - Callback function to execute on successful validation
 * @returns {boolean} - Whether the form is valid
 */
function validateForm(formId, onSuccess) {
    const form = document.getElementById(formId);
    if (!form) {
        console.error(`Form with ID "${formId}" not found`);
        return false;
    }
    
    // Get all form inputs that require validation
    const requiredInputs = form.querySelectorAll('[required]');
    const emailInputs = form.querySelectorAll('input[type="email"]');
    
    // Clear previous error messages
    const errorElements = form.querySelectorAll('.error-message');
    errorElements.forEach(el => el.remove());
    
    let isValid = true;
    
    // Validate required fields
    requiredInputs.forEach(input => {
        if (!input.value.trim()) {
            isValid = false;
            showError(input, 'This field is required');
        }
    });
    
    // Validate email format
    emailInputs.forEach(input => {
        if (input.value.trim() && !isValidEmail(input.value)) {
            isValid = false;
            showError(input, 'Please enter a valid email address');
        }
    });
    
    // If the form is valid, call the success callback
    if (isValid && typeof onSuccess === 'function') {
        onSuccess(form);
    }
    
    return isValid;
}

/**
 * Checks if an email address is valid
 * @param {string} email - The email address to validate
 * @returns {boolean} - Whether the email is valid
 */
function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

/**
 * Shows an error message for a form input
 * @param {HTMLElement} input - The input element
 * @param {string} message - The error message
 */
function showError(input, message) {
    const errorElement = document.createElement('div');
    errorElement.className = 'error-message';
    errorElement.style.color = 'red';
    errorElement.style.fontSize = '12px';
    errorElement.style.marginTop = '5px';
    errorElement.textContent = message;
    
    input.style.borderColor = 'red';
    input.parentNode.appendChild(errorElement);
    
    // Remove error styling when input changes
    input.addEventListener('input', function() {
        input.style.borderColor = '';
        const error = input.parentNode.querySelector('.error-message');
        if (error) {
            error.remove();
        }
    });
}"""
            },
            {
                "name": "Python Database Connection",
                "description": "A template for connecting to a database with error handling and connection pooling.",
                "language": "Python",
                "code_type": "Class",
                "code": """import os
import logging
from typing import Dict, Any, Optional, List
import pymysql
from pymysql.cursors import DictCursor
from dbutils.pooled_db import PooledDB

class DatabaseManager:
    # Database connection manager with connection pooling.
    
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        """Implement singleton pattern."""
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the database manager with connection config."""
        # Only initialize once (singleton pattern)
        if self._initialized:
            return
            
        # Set up logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Load configuration
        self.config = config or {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', 3306)),
            'user': os.getenv('DB_USER', 'root'),
            'password': os.getenv('DB_PASSWORD', ''),
            'database': os.getenv('DB_NAME', 'database'),
            'charset': 'utf8mb4',
            'cursorclass': DictCursor,
            'autocommit': True
        }
        
        # Initialize connection pool
        try:
            self.pool = PooledDB(
                creator=pymysql,
                maxconnections=10,  # Maximum number of connections
                mincached=2,        # Minimum number of idle connections in the pool
                maxcached=5,        # Maximum number of idle connections in the pool
                blocking=True,      # Block when pool is full
                **self.config
            )
            self.logger.info("Database connection pool initialized successfully")
            self._initialized = True
        except Exception as e:
            self.logger.error(f"Error initializing database pool: {str(e)}")
            raise
    
    def get_connection(self):
        """Get a connection from the pool."""
        try:
            return self.pool.connection()
        except Exception as e:
            self.logger.error(f"Error getting database connection: {str(e)}")
            raise
    
    def execute_query(self, query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """
        Execute a SQL query and return the results.
        
        Args:
            query (str): SQL query to execute
            params (tuple, optional): Parameters for the query
            
        Returns:
            List[Dict[str, Any]]: Query results as a list of dictionaries
        """
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                try:
                    cursor.execute(query, params or ())
                    return cursor.fetchall()
                except Exception as e:
                    self.logger.error(f"Error executing query: {str(e)}")
                    self.logger.error(f"Query: {query}")
                    self.logger.error(f"Params: {params}")
                    raise
    
    def execute_update(self, query: str, params: Optional[tuple] = None) -> int:
        """
        Execute an update query (INSERT, UPDATE, DELETE).
        
        Args:
            query (str): SQL query to execute
            params (tuple, optional): Parameters for the query
            
        Returns:
            int: Number of affected rows
        """
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                try:
                    affected_rows = cursor.execute(query, params or ())
                    return affected_rows
                except Exception as e:
                    conn.rollback()
                    self.logger.error(f"Error executing update: {str(e)}")
                    self.logger.error(f"Query: {query}")
                    self.logger.error(f"Params: {params}")
                    raise
    
    def execute_transaction(self, queries: List[Dict[str, Any]]) -> bool:
        """
        Execute multiple queries in a transaction.
        
        Args:
            queries (List[Dict[str, Any]]): List of query dictionaries with 'query' and 'params' keys
            
        Returns:
            bool: Success status
        """
        conn = self.get_connection()
        try:
            with conn:
                conn.begin()
                cursor = conn.cursor()
                
                for query_info in queries:
                    cursor.execute(query_info['query'], query_info.get('params', ()))
                
                conn.commit()
                return True
        except Exception as e:
            conn.rollback()
            self.logger.error(f"Error executing transaction: {str(e)}")
            raise
        finally:
            conn.close()

# Example usage
if __name__ == "__main__":
    # Initialize the database manager
    db = DatabaseManager()
    
    # Example query
    try:
        results = db.execute_query("SELECT * FROM users WHERE status = %s", ('active',))
        print(f"Found {len(results)} active users")
    except Exception as e:
        print(f"Error querying users: {str(e)}")"""
            }
        ]
        
        for template in default_templates:
            self.save_template(
                name=template["name"],
                code=template["code"],
                description=template["description"],
                language=template["language"],
                code_type=template["code_type"]
            )
