"""
Script de execução de testes sem dependência de PATH do pytest externo.
Permite executar a suíte com o Python nativo.
"""
import sys
import unittest

if __name__ == "__main__":
    # Test runner via unittest para garantir execução mesmo sem pytest instalado
    loader = unittest.TestLoader()
    suite = unittest.defaultTestLoader.discover(start_dir="tests", pattern="test_*.py")
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
