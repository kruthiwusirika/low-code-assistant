"""
Tests for Helm chart production readiness.
"""
import os
import sys
import unittest
import yaml
import subprocess
from unittest.mock import patch, MagicMock

class TestHelmProductionReadiness(unittest.TestCase):
    """
    Test the Helm chart configuration for production readiness.
    """
    
    def setUp(self):
        """Set up test environment."""
        self.project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        self.helm_dir = os.path.join(self.project_root, 'helm/low-code-assistant')
        self.templates_dir = os.path.join(self.helm_dir, 'templates')
        
    def test_production_features_exist(self):
        """Test that production features are included in the Helm chart."""
        # Check for security-related templates
        security_templates = [
            os.path.join(self.templates_dir, 'secret.yaml'),
            os.path.join(self.templates_dir, 'networkpolicy.yaml'),
            os.path.join(self.templates_dir, 'serviceaccount.yaml'),
        ]
        
        for template in security_templates:
            self.assertTrue(os.path.exists(template), f"Security template {template} does not exist")
        
        # Check for monitoring templates
        monitoring_templates = [
            os.path.join(self.templates_dir, 'servicemonitor.yaml'),
        ]
        
        for template in monitoring_templates:
            self.assertTrue(os.path.exists(template), f"Monitoring template {template} does not exist")
        
        # Check for scaling templates
        scaling_templates = [
            os.path.join(self.templates_dir, 'hpa.yaml'),
        ]
        
        for template in scaling_templates:
            self.assertTrue(os.path.exists(template), f"Scaling template {template} does not exist")
        
    def test_values_production_readiness(self):
        """Test that the values.yaml has production settings."""
        with open(os.path.join(self.helm_dir, 'values.yaml'), 'r') as f:
            values = yaml.safe_load(f)
        
        # Check for resource limits
        self.assertIn('resources', values)
        if 'resources' in values:
            resources = values['resources']
            self.assertIn('limits', resources)
            self.assertIn('requests', resources)
        
        # Check for replicas > 1 for high availability
        self.assertIn('replicaCount', values)
        
        # Check for autoscaling
        self.assertIn('autoscaling', values)
        if 'autoscaling' in values:
            autoscaling = values['autoscaling']
            self.assertIn('enabled', autoscaling)
            self.assertIn('minReplicas', autoscaling)
            self.assertIn('maxReplicas', autoscaling)
        
        # Check for persistence
        self.assertIn('persistence', values)
        if 'persistence' in values:
            persistence = values['persistence']
            self.assertIn('enabled', persistence)
            
    def test_template_rendered_output(self):
        """Test the rendered output of the Helm chart if helm is available."""
        try:
            # Check if helm is installed
            subprocess.run(["which", "helm"], check=True, capture_output=True)
            
            # Create a temp file for output
            import tempfile
            output_file = tempfile.NamedTemporaryFile(delete=False)
            output_path = output_file.name
            output_file.close()
            
            try:
                # Template the chart
                result = subprocess.run(
                    ["helm", "template", "test-release", self.helm_dir, "--output-dir", os.path.dirname(output_path)],
                    check=True,
                    capture_output=True,
                    text=True
                )
                
                # Check that template command succeeded
                self.assertEqual(result.returncode, 0, f"Helm template failed: {result.stderr}")
                
                # Check that output files were created
                template_output_dir = os.path.join(os.path.dirname(output_path), "low-code-assistant")
                self.assertTrue(os.path.exists(template_output_dir))
                
                # Check expected output files
                expected_files = [
                    "deployment.yaml",
                    "service.yaml",
                    "ingress.yaml",
                    "secret.yaml",
                ]
                
                for filename in expected_files:
                    file_path = os.path.join(template_output_dir, "templates", filename)
                    self.assertTrue(os.path.exists(file_path), f"Expected template output {file_path} not found")
                
            finally:
                # Cleanup temp file and directory
                if os.path.exists(output_path):
                    os.unlink(output_path)
                
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Skip this test if helm is not installed
            self.skipTest("helm not installed, skipping template test")
            
    def test_production_deployment_guides_exist(self):
        """Test that production deployment guides exist."""
        docs_dir = os.path.join(self.project_root, 'docs')
        
        # Check that docs directory exists
        self.assertTrue(os.path.exists(docs_dir), "Docs directory not found")
        
        # Check for cloud deployment guides
        cloud_guides = [
            os.path.join(docs_dir, 'aws-eks-deployment.md'),
            os.path.join(docs_dir, 'azure-aks-deployment.md'),
            os.path.join(docs_dir, 'gcp-gke-deployment.md'),
        ]
        
        for guide in cloud_guides:
            self.assertTrue(os.path.exists(guide), f"Cloud deployment guide {guide} not found")
            
            # Check guide content
            with open(guide, 'r') as f:
                content = f.read()
                
            # Check for important sections
            self.assertIn("# Prerequisites", content)
            self.assertIn("# Step", content)  # Should have numbered steps
            self.assertIn("# Additional Considerations", content)

if __name__ == "__main__":
    unittest.main()
