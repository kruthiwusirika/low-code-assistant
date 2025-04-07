"""
Basic tests to verify the testing framework works properly.
"""
import unittest
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class TestBasicFunctionality(unittest.TestCase):
    """Basic tests to verify the testing framework is working."""
    
    def test_environment_setup(self):
        """Test that the environment is set up correctly."""
        # Check that we can import from the project
        self.assertTrue(os.path.exists(os.path.join(os.path.dirname(__file__), '..', 'simple_app.py')))
        
    def test_project_structure(self):
        """Test that the project structure is correct."""
        # Check for required directories
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        required_dirs = ['k8s', 'helm', 'docs']
        for dir_name in required_dirs:
            self.assertTrue(os.path.isdir(os.path.join(project_root, dir_name)),
                           f"Directory {dir_name} should exist")
        
        # Check for required files
        required_files = ['Dockerfile', 'README.md', 'simple_app.py']
        for file_name in required_files:
            self.assertTrue(os.path.isfile(os.path.join(project_root, file_name)),
                          f"File {file_name} should exist")
    
    def test_kubernetes_config(self):
        """Test that Kubernetes config files exist."""
        k8s_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'k8s'))
        required_k8s_files = ['deployment.yaml', 'service.yaml', 'secret.yaml']
        for file_name in required_k8s_files:
            self.assertTrue(os.path.isfile(os.path.join(k8s_dir, file_name)),
                          f"Kubernetes file {file_name} should exist")
    
    def test_helm_config(self):
        """Test that Helm chart files exist."""
        helm_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'helm/low-code-assistant'))
        required_helm_files = ['Chart.yaml', 'values.yaml']
        for file_name in required_helm_files:
            self.assertTrue(os.path.isfile(os.path.join(helm_dir, file_name)),
                          f"Helm file {file_name} should exist")
        
        # Check templates directory
        templates_dir = os.path.join(helm_dir, 'templates')
        self.assertTrue(os.path.isdir(templates_dir), "Helm templates directory should exist")
        
        # Check template files
        required_templates = ['deployment.yaml', 'service.yaml', 'ingress.yaml']
        for file_name in required_templates:
            self.assertTrue(os.path.isfile(os.path.join(templates_dir, file_name)),
                          f"Helm template {file_name} should exist")
    
    def test_documentation(self):
        """Test that documentation files exist."""
        docs_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'docs'))
        required_docs = ['aws-eks-deployment.md', 'azure-aks-deployment.md', 'gcp-gke-deployment.md']
        for file_name in required_docs:
            self.assertTrue(os.path.isfile(os.path.join(docs_dir, file_name)),
                          f"Documentation file {file_name} should exist")

if __name__ == "__main__":
    unittest.main()
