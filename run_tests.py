#!/usr/bin/env python
"""
Test runner script for Low-Code Assistant.
Run this script to execute all tests or specific test modules.
"""
import os
import sys
import unittest
import argparse

def run_tests(test_modules=None, verbosity=2):
    """
    Run selected tests or all tests if no modules specified.
    
    Args:
        test_modules (list): List of test module names to run
        verbosity (int): Verbosity level for test output
    
    Returns:
        bool: True if all tests passed, False otherwise
    """
    # Add project root to path
    project_root = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, project_root)
    
    # Get all test modules if none specified
    if not test_modules:
        test_dir = os.path.join(project_root, 'tests')
        test_files = [f for f in os.listdir(test_dir) 
                     if f.startswith('test_') and f.endswith('.py')]
        test_modules = [os.path.splitext(f)[0] for f in test_files]
    
    # Initialize test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add tests from specified modules
    for module in test_modules:
        try:
            # Import the module
            if module.startswith('test_'):
                module_path = f'tests.{module}'
            else:
                module_path = f'tests.test_{module}'
            
            tests = loader.loadTestsFromName(module_path)
            suite.addTests(tests)
            print(f"Added tests from {module_path}")
        except (ImportError, AttributeError) as e:
            print(f"Warning: Could not load tests from {module}: {e}")
    
    # Run the tests
    runner = unittest.TextTestRunner(verbosity=verbosity)
    result = runner.run(suite)
    
    return result.wasSuccessful()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run tests for Low-Code Assistant")
    parser.add_argument('-m', '--modules', nargs='+', 
                        help='Specific test modules to run (without .py extension)')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Increase verbosity of output')
    
    args = parser.parse_args()
    
    verbosity = 3 if args.verbose else 2
    success = run_tests(args.modules, verbosity)
    
    # Exit with appropriate status code
    sys.exit(0 if success else 1)
