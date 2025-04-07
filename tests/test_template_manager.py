"""
Unit tests for the template manager functionality.
"""
import os
import sys
import json
import unittest
import tempfile
import shutil
from unittest.mock import patch, mock_open, MagicMock

# Add the project root to the path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.template_manager import TemplateManager

class TestTemplateManager(unittest.TestCase):
    def setUp(self):
        """Set up test environment."""
        # Create a temporary directory for templates
        self.temp_dir = tempfile.mkdtemp()
        self.template_manager = TemplateManager(templates_dir=self.temp_dir)
    
    def tearDown(self):
        """Clean up after tests."""
        shutil.rmtree(self.temp_dir)
    
    def test_load_templates_nonexistent_file(self):
        """Test loading templates from a non-existent file."""
        # Ensure the file doesn't exist
        if os.path.exists(self.template_manager.templates_file):
            os.remove(self.template_manager.templates_file)
        
        # Load templates
        templates = self.template_manager.load_templates()
        self.assertEqual(templates, [])
    
    def test_load_templates_existing_file(self):
        """Test loading templates from an existing file."""
        # Create a templates file with some test templates
        test_templates = [
            {"id": "test1", "name": "Test Template 1", "content": "Test content 1"},
            {"id": "test2", "name": "Test Template 2", "content": "Test content 2"}
        ]
        with open(self.template_manager.templates_file, 'w') as f:
            json.dump(test_templates, f)
        
        # Load templates
        templates = self.template_manager.load_templates()
        self.assertEqual(templates, test_templates)
    
    def test_save_templates(self):
        """Test saving templates to a file."""
        # Set up some test templates
        test_templates = [
            {"id": "test1", "name": "Test Template 1", "content": "Test content 1"},
            {"id": "test2", "name": "Test Template 2", "content": "Test content 2"}
        ]
        self.template_manager.templates = test_templates
        
        # Save templates
        self.template_manager.save_templates()
        
        # Verify the templates were saved correctly
        with open(self.template_manager.templates_file, 'r') as f:
            saved_templates = json.load(f)
        self.assertEqual(saved_templates, test_templates)
    
    def test_add_template(self):
        """Test adding a template."""
        # New template to add
        new_template = {"name": "New Template", "content": "New content"}
        
        # Add the template
        added_template = self.template_manager.add_template(new_template)
        
        # Verify the template was added with an ID
        self.assertIn("id", added_template)
        self.assertEqual(added_template["name"], new_template["name"])
        self.assertEqual(added_template["content"], new_template["content"])
        
        # Verify the template was added to the list
        self.assertIn(added_template, self.template_manager.templates)
        
        # Verify that the templates were saved
        with open(self.template_manager.templates_file, 'r') as f:
            saved_templates = json.load(f)
        self.assertIn(added_template, saved_templates)
    
    def test_get_template(self):
        """Test getting a template by ID."""
        # Add a test template
        test_template = {"name": "Test Template", "content": "Test content"}
        added_template = self.template_manager.add_template(test_template)
        template_id = added_template["id"]
        
        # Get the template
        retrieved_template = self.template_manager.get_template(template_id)
        
        # Verify the template was retrieved correctly
        self.assertEqual(retrieved_template, added_template)
        
        # Try to get a non-existent template
        retrieved_template = self.template_manager.get_template("non-existent-id")
        self.assertIsNone(retrieved_template)
    
    def test_update_template(self):
        """Test updating a template."""
        # Add a test template
        test_template = {"name": "Test Template", "content": "Test content"}
        added_template = self.template_manager.add_template(test_template)
        template_id = added_template["id"]
        
        # Update the template
        updates = {"name": "Updated Name", "content": "Updated content"}
        updated_template = self.template_manager.update_template(template_id, updates)
        
        # Verify the template was updated correctly
        self.assertEqual(updated_template["name"], updates["name"])
        self.assertEqual(updated_template["content"], updates["content"])
        self.assertEqual(updated_template["id"], template_id)
        
        # Verify the templates were saved
        with open(self.template_manager.templates_file, 'r') as f:
            saved_templates = json.load(f)
        self.assertIn(updated_template, saved_templates)
        
        # Try to update a non-existent template
        result = self.template_manager.update_template("non-existent-id", updates)
        self.assertIsNone(result)
    
    def test_delete_template(self):
        """Test deleting a template."""
        # Add a test template
        test_template = {"name": "Test Template", "content": "Test content"}
        added_template = self.template_manager.add_template(test_template)
        template_id = added_template["id"]
        
        # Delete the template
        result = self.template_manager.delete_template(template_id)
        
        # Verify the template was deleted
        self.assertTrue(result)
        self.assertNotIn(added_template, self.template_manager.templates)
        
        # Verify the templates were saved
        with open(self.template_manager.templates_file, 'r') as f:
            saved_templates = json.load(f)
        self.assertNotIn(added_template, saved_templates)
        
        # Try to delete a non-existent template
        result = self.template_manager.delete_template("non-existent-id")
        self.assertFalse(result)
    
    def test_get_all_templates(self):
        """Test getting all templates."""
        # Add some test templates
        test_templates = [
            {"name": "Template 1", "content": "Content 1"},
            {"name": "Template 2", "content": "Content 2"},
            {"name": "Template 3", "content": "Content 3"}
        ]
        for template in test_templates:
            self.template_manager.add_template(template)
        
        # Get all templates
        all_templates = self.template_manager.get_all_templates()
        
        # Verify we got the correct number of templates
        self.assertEqual(len(all_templates), len(test_templates))

if __name__ == "__main__":
    unittest.main()
