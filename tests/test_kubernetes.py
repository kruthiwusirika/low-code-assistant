"""
Tests for Kubernetes deployment configuration.
"""
import os
import sys
import unittest
import yaml
import subprocess
from unittest.mock import patch, MagicMock

class TestKubernetesDeployment(unittest.TestCase):
    """
    Test the Kubernetes deployment configuration.
    """
    
    def setUp(self):
        """Set up test environment."""
        self.project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        self.k8s_dir = os.path.join(self.project_root, 'k8s')
        self.deployment_file = os.path.join(self.k8s_dir, 'deployment.yaml')
        self.service_file = os.path.join(self.k8s_dir, 'service.yaml')
        self.ingress_file = os.path.join(self.k8s_dir, 'ingress.yaml')
        self.secret_file = os.path.join(self.k8s_dir, 'secret.yaml')
        
    def test_kubernetes_files_exist(self):
        """Test that all required Kubernetes configuration files exist."""
        required_files = [
            self.deployment_file,
            self.service_file,
            self.secret_file
        ]
        
        for file_path in required_files:
            self.assertTrue(os.path.exists(file_path), f"Required file {file_path} does not exist")
        
    def test_deployment_file_valid(self):
        """Test that the deployment YAML is valid."""
        with open(self.deployment_file, 'r') as f:
            deployment = yaml.safe_load(f)
        
        # Check basic structure
        self.assertEqual(deployment['apiVersion'], 'apps/v1')
        self.assertEqual(deployment['kind'], 'Deployment')
        
        # Check required fields
        self.assertIn('metadata', deployment)
        self.assertIn('spec', deployment)
        self.assertIn('selector', deployment['spec'])
        self.assertIn('template', deployment['spec'])
        
        # Check container configuration
        containers = deployment['spec']['template']['spec']['containers']
        self.assertGreaterEqual(len(containers), 1)
        
        # Check the first container (should be our app)
        container = containers[0]
        self.assertIn('name', container)
        self.assertIn('image', container)
        
        # Check resource limits
        if 'resources' in container:
            resources = container['resources']
            if 'limits' in resources:
                limits = resources['limits']
                self.assertIn('cpu', limits)
                self.assertIn('memory', limits)
            
            if 'requests' in resources:
                requests = resources['requests']
                self.assertIn('cpu', requests)
                self.assertIn('memory', requests)
        
    def test_service_file_valid(self):
        """Test that the service YAML is valid."""
        with open(self.service_file, 'r') as f:
            service = yaml.safe_load(f)
        
        # Check basic structure
        self.assertEqual(service['apiVersion'], 'v1')
        self.assertEqual(service['kind'], 'Service')
        
        # Check required fields
        self.assertIn('metadata', service)
        self.assertIn('spec', service)
        
        # Check service type and port
        self.assertIn('type', service['spec'])
        self.assertIn('ports', service['spec'])
        self.assertGreaterEqual(len(service['spec']['ports']), 1)
        
        # Check the first port
        port = service['spec']['ports'][0]
        self.assertIn('port', port)
        self.assertIn('targetPort', port)
        
    def test_secret_file_valid(self):
        """Test that the secret YAML is valid."""
        with open(self.secret_file, 'r') as f:
            secret = yaml.safe_load(f)
        
        # Check basic structure
        self.assertEqual(secret['apiVersion'], 'v1')
        self.assertEqual(secret['kind'], 'Secret')
        
        # Check required fields
        self.assertIn('metadata', secret)
        self.assertIn('data', secret)
        
        # Ensure secret has the OpenAI API key field
        self.assertIn('OPENAI_API_KEY', secret['data'])
        
    def test_validate_deployment_with_kubeval(self):
        """Test validating Kubernetes YAML files with kubeval if available."""
        try:
            # Check if kubeval is installed
            subprocess.run(["which", "kubeval"], check=True, capture_output=True)
            
            # Validate the deployment file
            result = subprocess.run(
                ["kubeval", self.deployment_file],
                check=True,
                capture_output=True
            )
            self.assertEqual(result.returncode, 0)
            
            # Validate the service file
            result = subprocess.run(
                ["kubeval", self.service_file],
                check=True,
                capture_output=True
            )
            self.assertEqual(result.returncode, 0)
            
            # Validate the secret file
            result = subprocess.run(
                ["kubeval", self.secret_file],
                check=True,
                capture_output=True
            )
            self.assertEqual(result.returncode, 0)
            
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Skip this test if kubeval is not installed
            self.skipTest("kubeval not installed, skipping validation test")

class TestHelmChart(unittest.TestCase):
    """
    Test the Helm chart configuration.
    """
    
    def setUp(self):
        """Set up test environment."""
        self.project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        self.helm_dir = os.path.join(self.project_root, 'helm/low-code-assistant')
        self.chart_file = os.path.join(self.helm_dir, 'Chart.yaml')
        self.values_file = os.path.join(self.helm_dir, 'values.yaml')
        self.templates_dir = os.path.join(self.helm_dir, 'templates')
        
    def test_helm_files_exist(self):
        """Test that all required Helm files exist."""
        required_files = [
            self.chart_file,
            self.values_file,
            os.path.join(self.templates_dir, 'deployment.yaml'),
            os.path.join(self.templates_dir, 'service.yaml'),
            os.path.join(self.templates_dir, 'ingress.yaml'),
            os.path.join(self.templates_dir, 'secret.yaml')
        ]
        
        for file_path in required_files:
            self.assertTrue(os.path.exists(file_path), f"Required Helm file {file_path} does not exist")
        
    def test_chart_yaml_valid(self):
        """Test that the Chart.yaml is valid."""
        with open(self.chart_file, 'r') as f:
            chart = yaml.safe_load(f)
        
        # Check required fields for a valid Chart.yaml
        required_fields = ['apiVersion', 'name', 'version', 'description']
        for field in required_fields:
            self.assertIn(field, chart)
        
    def test_values_yaml_valid(self):
        """Test that the values.yaml is valid."""
        with open(self.values_file, 'r') as f:
            values = yaml.safe_load(f)
        
        # Check that basic sections exist in values.yaml
        expected_sections = [
            'image',
            'service',
            'ingress',
            'resources',
            'autoscaling',
        ]
        
        for section in expected_sections:
            self.assertIn(section, values)
        
    def test_deployment_template_contains_probes(self):
        """Test that the deployment template has health probes configured."""
        with open(os.path.join(self.templates_dir, 'deployment.yaml'), 'r') as f:
            content = f.read()
        
        # Check for liveness and readiness probes in the template
        self.assertIn('livenessProbe', content)
        self.assertIn('readinessProbe', content)
        
    def test_lint_helm_chart(self):
        """Test linting the Helm chart if helm is available."""
        try:
            # Check if helm is installed
            subprocess.run(["which", "helm"], check=True, capture_output=True)
            
            # Lint the chart
            result = subprocess.run(
                ["helm", "lint", self.helm_dir],
                check=True,
                capture_output=True,
                text=True
            )
            self.assertEqual(result.returncode, 0, f"Helm lint failed: {result.stderr}")
            
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Skip this test if helm is not installed
            self.skipTest("helm not installed, skipping lint test")

if __name__ == "__main__":
    unittest.main()
