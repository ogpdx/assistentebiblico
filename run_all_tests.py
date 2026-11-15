"""
Runner oficial de testes do projeto via pytest programático.
"""
import sys

if __name__ == "__main__":
    try:
        import pytest
        sys.exit(pytest.main(["-v", "tests"]))
    except ImportError:
        # Fallback para unittest caso pytest não esteja no ambiente
        import unittest
        loader = unittest.TestLoader()
        suite = loader.discover(start_dir="tests", pattern="test_*.py")
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        sys.exit(0 if result.wasSuccessful() else 1)
