#!/usr/bin/env python
"""
Script d'exécution des tests avec rapport de couverture.
Usage: python run_tests.py [OPTIONS]
"""

import subprocess
import sys
from pathlib import Path


def run_tests(verbose=False, coverage=False, specific_file=None):
    """Exécuter les tests unitaires"""
    
    cmd = ["pytest"]
    
    if specific_file:
        cmd.append(specific_file)
    else:
        cmd.append("test/")
    
    if verbose:
        cmd.append("-v")
    
    if coverage:
        cmd.extend(["--cov=app", "--cov-report=html", "--cov-report=term"])
    
    cmd.append("--tb=short")
    
    print(f"📊 Exécution: {' '.join(cmd)}")
    print("-" * 60)
    
    result = subprocess.run(cmd)
    
    if coverage:
        print("\n📈 Rapport de couverture généré dans: htmlcov/index.html")
    
    return result.returncode


if __name__ == "__main__":
    verbose = "-v" in sys.argv or "--verbose" in sys.argv
    coverage = "-c" in sys.argv or "--coverage" in sys.argv
    specific_file = None
    
    # Chercher un argument de fichier spécifique
    for arg in sys.argv[1:]:
        if arg.endswith(".py") and arg.startswith("test"):
            specific_file = arg
            break
    
    exit_code = run_tests(verbose=verbose, coverage=coverage, specific_file=specific_file)
    sys.exit(exit_code)
