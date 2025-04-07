"""
Template Manager for the Low-Code Assistant.
This is a simplified version that handles template management functionality.
"""
import os
import json
import re
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
        if templates_dir is None:
            # Default to project's templates directory
            self.templates_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "templates")
        else:
            self.templates_dir = templates_dir
        
        # Create templates directory if it doesn't exist
        os.makedirs(self.templates_dir, exist_ok=True)
        
        # Templates file path
        self.templates_file = os.path.join(self.templates_dir, "templates.json")
        
        # Load existing templates or create empty list
        self.templates = self.load_templates()
        
        # Create default templates if none exist
        if not self.templates:
            self.create_default_templates()
    
    def load_templates(self) -> List[Dict[str, Any]]:
        """Load templates from the templates file."""
        if os.path.exists(self.templates_file):
            try:
                with open(self.templates_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                self.logger.error("Error decoding templates JSON file. Creating new templates.")
                return []
        return []
    
    def save_templates(self) -> None:
        """Save templates to the templates file."""
        with open(self.templates_file, 'w') as f:
            json.dump(self.templates, f, indent=2)
    
    def add_template(self, template: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add a new template.
        
        Args:
            template (Dict[str, Any]): Template to add
            
        Returns:
            Dict[str, Any]: Added template with ID
        """
        # Add timestamp and ID
        template["id"] = self.generate_id(template.get("name", "Untitled"))
        template["created_at"] = datetime.now().isoformat()
        template["updated_at"] = template["created_at"]
        
        # Add template to list
        self.templates.append(template)
        
        # Save templates
        self.save_templates()
        
        return template
    
    def get_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a template by ID.
        
        Args:
            template_id (str): ID of template to get
            
        Returns:
            Optional[Dict[str, Any]]: Template if found, None otherwise
        """
        for template in self.templates:
            if template.get("id") == template_id:
                return template
        return None
    
    def update_template(self, template_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update a template.
        
        Args:
            template_id (str): ID of template to update
            updates (Dict[str, Any]): Updates to apply
            
        Returns:
            Optional[Dict[str, Any]]: Updated template if found, None otherwise
        """
        for i, template in enumerate(self.templates):
            if template.get("id") == template_id:
                # Apply updates
                template.update(updates)
                # Update timestamp
                template["updated_at"] = datetime.now().isoformat()
                # Update in list
                self.templates[i] = template
                # Save templates
                self.save_templates()
                return template
        return None
    
    def delete_template(self, template_id: str) -> bool:
        """
        Delete a template.
        
        Args:
            template_id (str): ID of template to delete
            
        Returns:
            bool: True if deleted, False otherwise
        """
        for i, template in enumerate(self.templates):
            if template.get("id") == template_id:
                # Remove from list
                del self.templates[i]
                # Save templates
                self.save_templates()
                return True
        return False
    
    def get_all_templates(self) -> List[Dict[str, Any]]:
        """Get all templates."""
        return self.templates
    
    def generate_id(self, name: str) -> str:
        """Generate a unique ID based on name and timestamp."""
        timestamp = int(datetime.now().timestamp())
        sanitized = self.sanitize_name(name)
        return f"{sanitized}_{timestamp}"
    
    def sanitize_name(self, name: str) -> str:
        """Sanitize a name for use in an ID."""
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
    def wrapper(*args, **kwargs):
        try:
            if request.get_data():
                request.json
        except BadRequest:
            return jsonify({"error": "Invalid JSON format"}), 400
        return f(*args, **kwargs)
    return wrapper

@app.route('/api/v1/resource', methods=['POST'])
@validate_json
def create_resource():
    # Get JSON data
    data = request.get_json()
    
    # Validate required fields
    if 'name' not in data:
        return jsonify({"error": "Missing required field: name"}), 400
    
    # Process the request (in a real app, you'd interact with a database or other service)
    try:
        # Example processing logic
        resource_id = 123  # In a real app, this would be generated or returned from a database
        
        # Return success response
        return jsonify({
            "id": resource_id,
            "name": data['name'],
            "message": "Resource created successfully"
        }), 201
    except Exception as e:
        # Log the error (in a real app)
        app.logger.error(f"Error creating resource: {str(e)}")
        
        # Return error response
        return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    app.run(debug=True)
"""
            },
            {
                "name": "JavaScript Form Validation",
                "description": "Client-side form validation script with error handling and feedback.",
                "language": "JavaScript",
                "code_type": "Utility Function",
                "code": """/**
 * Validate a form with customizable rules
 * @param {string} formId - The ID of the form to validate
 * @param {Object} rules - Validation rules for each field
 * @param {Object} messages - Custom error messages (optional)
 * @returns {boolean} - Whether the form is valid
 */
function validateForm(formId, rules, messages = {}) {
    const form = document.getElementById(formId);
    if (!form) {
        console.error(`Form with ID "${formId}" not found`);
        return false;
    }
    
    // Track validation status
    let isValid = true;
    
    // Clear previous error messages
    const errorElements = form.querySelectorAll('.error-message');
    errorElements.forEach(el => el.remove());
    
    // Validate each field according to rules
    for (const fieldName in rules) {
        const input = form.querySelector(`[name="${fieldName}"]`);
        if (!input) {
            console.warn(`Field "${fieldName}" not found in form`);
            continue;
        }
        
        // Get field rules
        const fieldRules = rules[fieldName];
        
        // Get field value and trim if it's a string
        let value = input.value;
        if (typeof value === 'string') {
            value = value.trim();
        }
        
        // Check required
        if (fieldRules.required && !value) {
            const message = messages[fieldName]?.required || `${fieldName} is required`;
            markInvalid(input, message);
            isValid = false;
            continue;
        }
        
        # Skip other validations if empty and not required
        if not value and not field_rules.get('required', False):
            continue
        
        # Check minimum length
        if field_rules.get('min_length') and len(value) < field_rules['min_length']:
            message = messages.get(field_name, {}).get('min_length') or \
                f"{field_name} must be at least {field_rules['min_length']} characters"
            mark_invalid(input_field, message)
            is_valid = False
            continue
        
        # Check maximum length
        if field_rules.get('max_length') and len(value) > field_rules['max_length']:
            message = messages.get(field_name, {}).get('max_length') or \
                f"{field_name} must be at most {field_rules['max_length']} characters"
            mark_invalid(input_field, message)
            is_valid = False
            continue
        
        # Check pattern
        if field_rules.get('pattern') and not re.match(field_rules['pattern'], value):
            message = messages.get(field_name, {}).get('pattern') or \
                f"{field_name} must match pattern {field_rules['pattern']}"
            mark_invalid(input_field, message)
            is_valid = False
            continue
        
        # Check if email
        if field_rules.get('email') and not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', value):
            message = messages.get(field_name, {}).get('email') or \
                f"{field_name} must be a valid email address"
            mark_invalid(input_field, message)
            is_valid = False
            continue
        
        # Check custom validator
        if field_rules.get('custom') and callable(field_rules['custom']):
            custom_result = field_rules['custom'](value)
            if custom_result is not True:
                message = custom_result if isinstance(custom_result, str) else \
                    messages.get(field_name, {}).get('custom') or f"{field_name} is invalid"
                mark_invalid(input_field, message)
                is_valid = False
                continue
    
    return is_valid

def mark_invalid(input_field, message):
    """
    Mark a field as invalid with an error message.
    
    Args:
        input_field: The input field element
        message: Error message to display
    """
    # In Python/Streamlit context, this would use streamlit's error display
    # or return error information to be displayed
    # This is a simplified version for the template
    
    # Log the error for debugging
    logging.error(f"Validation error: {message}")
    
    # In a real app, we might set some state or return the error
    # For now, we'll just pass since this is template code
    pass

# Complete the default_templates list with more templates
default_templates.extend([
            {
                "name": "Python Database Connection",
                "description": "A template for connecting to a database with error handling and connection pooling.",
                "language": "Python",
                "code_type": "Class",
                "code": """import os
import logging
from typing import Dict, Any, Optional, List
import sqlite3
from contextlib import contextmanager

class DatabaseManager:
    # Database connection manager with connection pooling
    
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        """Implement singleton pattern."""
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize the database manager with connection config."""
        # Only initialize once (singleton pattern)
        if hasattr(self, '_initialized') and self._initialized:
            return
            
        # Set up logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Set database path
        self.db_path = db_path or os.getenv('DB_PATH', 'database.sqlite')
        
        # Flag as initialized
        self._initialized = True
        
        # Initialize database
        self._init_db()
    
    def _init_db(self) -> None:
        """Initialize the database if it doesn't exist."""
        try:
            with self.get_connection() as conn:
                # Create tables here if needed
                pass
                
            self.logger.info(f"Database initialized: {self.db_path}")
        except Exception as e:
            self.logger.error(f"Error initializing database: {str(e)}")
            raise
    
    @contextmanager
    def get_connection(self):
        """Get a database connection."""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Return rows as dictionaries
            yield conn
        except Exception as e:
            self.logger.error(f"Database connection error: {str(e)}")
            raise
        finally:
            if conn:
                conn.close()
    
    def execute_query(self, query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """Execute a query and return results."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params or ())
                conn.commit()
                
                # Convert results to dictionaries
                if cursor.description:
                    columns = [col[0] for col in cursor.description]
                    return [dict(zip(columns, row)) for row in cursor.fetchall()]
                return []
        except Exception as e:
            self.logger.error(f"Query execution error: {str(e)}")
            raise
    
    def execute_many(self, query: str, params_list: List[tuple]) -> None:
        """Execute a query with multiple parameter sets."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.executemany(query, params_list)
                conn.commit()
        except Exception as e:
            self.logger.error(f"Batch query execution error: {str(e)}")
            raise
    
    def insert_one(self, table: str, data: Dict[str, Any]) -> int:
        """Insert a single record and return the ID."""
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['?' for _ in data])
        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, tuple(data.values()))
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            self.logger.error(f"Insert error: {str(e)}")
            raise
    
    def get_by_id(self, table: str, id_value: int, id_column: str = 'id') -> Optional[Dict[str, Any]]:
        """Get a record by ID."""
        query = f"SELECT * FROM {table} WHERE {id_column} = ?"
        
        try:
            results = self.execute_query(query, (id_value,))
            return results[0] if results else None
        except Exception as e:
            self.logger.error(f"Get by ID error: {str(e)}")
            raise
                """
            }
        ])
        
        for template in default_templates:
            self.add_template(template)