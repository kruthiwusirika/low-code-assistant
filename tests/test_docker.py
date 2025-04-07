"""
Tests for Docker image and container functionality.
"""
import os
import sys
import unittest
import subprocess
from unittest.mock import patch, MagicMock

class TestDockerImage(unittest.TestCase):
    """
    Test the Docker image build and functionality.
    Note: These tests require Docker to be installed and running.
    """
    
    @classmethod
    def setUpClass(cls):
        """Build the Docker image before running tests."""
        cls.image_name = "low-code-assistant:test"
        cls.project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        
        # Build the Docker image for testing
        try:
            subprocess.run(
                ["docker", "build", "-t", cls.image_name, cls.project_root],
                check=True,
                capture_output=True
            )
        except subprocess.CalledProcessError as e:
            print(f"Error building Docker image: {e.stderr.decode()}")
            raise
    
    @classmethod
    def tearDownClass(cls):
        """Clean up the Docker image after tests."""
        try:
            subprocess.run(
                ["docker", "rmi", cls.image_name],
                check=True,
                capture_output=True
            )
        except subprocess.CalledProcessError:
            # If the image can't be removed, just log it
            print(f"Warning: Could not remove Docker image {cls.image_name}")
    
    def test_docker_image_exists(self):
        """Test that the Docker image exists."""
        try:
            result = subprocess.run(
                ["docker", "image", "inspect", self.image_name],
                check=True,
                capture_output=True
            )
            self.assertEqual(result.returncode, 0)
        except subprocess.CalledProcessError as e:
            self.fail(f"Docker image does not exist: {e.stderr.decode()}")
    
    def test_container_starts(self):
        """Test that the container starts correctly."""
        container_name = "low-code-assistant-test"
        try:
            # Start the container
            subprocess.run(
                ["docker", "run", "-d", "--name", container_name, "-p", "8501:8501", self.image_name],
                check=True,
                capture_output=True
            )
            
            # Give it a moment to start
            import time
            time.sleep(5)
            
            # Check if container is running
            result = subprocess.run(
                ["docker", "ps", "-f", f"name={container_name}", "--format", "{{.Status}}"],
                check=True,
                capture_output=True,
                text=True
            )
            self.assertIn("Up", result.stdout)
            
        finally:
            # Cleanup: Stop and remove the container
            subprocess.run(["docker", "stop", container_name], capture_output=True)
            subprocess.run(["docker", "rm", container_name], capture_output=True)
    
    def test_healthcheck(self):
        """Test that the container's health check passes."""
        container_name = "low-code-assistant-healthcheck"
        try:
            # Start the container
            subprocess.run(
                ["docker", "run", "-d", "--name", container_name, "-p", "8502:8501", self.image_name],
                check=True,
                capture_output=True
            )
            
            # Give it time to run health checks
            import time
            time.sleep(10)
            
            # Check container health status
            result = subprocess.run(
                ["docker", "inspect", "--format", "{{.State.Health.Status}}", container_name],
                check=True,
                capture_output=True,
                text=True
            )
            
            # If healthcheck is configured, it should return "healthy" or "starting"
            # If no healthcheck is configured, it may return empty string
            status = result.stdout.strip()
            self.assertTrue(status in ["healthy", "starting"] or not status)
            
        finally:
            # Cleanup
            subprocess.run(["docker", "stop", container_name], capture_output=True)
            subprocess.run(["docker", "rm", container_name], capture_output=True)
    
    def test_user_not_root(self):
        """Test that the container is not running as root."""
        try:
            result = subprocess.run(
                ["docker", "run", "--rm", self.image_name, "id", "-u"],
                check=True,
                capture_output=True,
                text=True
            )
            user_id = int(result.stdout.strip())
            self.assertNotEqual(user_id, 0, "Container should not run as root (UID 0)")
            
        except subprocess.CalledProcessError as e:
            self.fail(f"Failed to check container user: {e.stderr}")

if __name__ == "__main__":
    unittest.main()
