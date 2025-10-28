#!/usr/bin/env python3
"""Verify that the GitAI package structure is correct."""

import sys
from pathlib import Path

def check_file_exists(file_path: str) -> bool:
    """Check if a file exists."""
    path = Path(file_path)
    exists = path.exists()
    print(f"{'✓' if exists else '✗'} {file_path}")
    return exists

def main():
    """Verify package structure."""
    print("GitAI Package Structure Verification")
    print("=" * 40)
    
    required_files = [
        # Core package files
        "src/gitai/__init__.py",
        "src/gitai/cli.py",
        
        # Core modules
        "src/gitai/core/__init__.py",
        "src/gitai/core/git_analyzer.py",
        "src/gitai/core/models.py",
        
        # Providers
        "src/gitai/providers/__init__.py",
        "src/gitai/providers/base.py",
        "src/gitai/providers/ollama.py",
        "src/gitai/providers/factory.py",
        
        # Commands
        "src/gitai/commands/__init__.py",
        "src/gitai/commands/commit.py",
        "src/gitai/commands/pr.py",
        "src/gitai/commands/config.py",
        "src/gitai/commands/templates.py",
        
        # Utils
        "src/gitai/utils/__init__.py",
        "src/gitai/utils/exceptions.py",
        "src/gitai/utils/logger.py",
        
        # Project files
        "pyproject.toml",
        ".gitignore",
        ".pre-commit-config.yaml",
        ".github/workflows/ci.yml",
        
        # Tests
        "tests/__init__.py",
    ]
    
    all_exist = True
    for file_path in required_files:
        if not check_file_exists(file_path):
            all_exist = False
    
    print("\nStructure Check:", "✓ PASSED" if all_exist else "✗ FAILED")
    
    # Check package imports (without dependencies)
    print("\nBasic Import Check:")
    try:
        sys.path.insert(0, "src")
        
        # Test basic imports that don't require external dependencies
        from gitai.utils.exceptions import GitAIError
        print("✓ gitai.utils.exceptions")
        
        from gitai.utils.logger import setup_logger
        print("✓ gitai.utils.logger")
        
        print("✓ Basic imports successful")
        
    except Exception as e:
        print(f"✗ Import error: {e}")
        all_exist = False
    
    print("\nOverall Status:", "✓ SUCCESS" if all_exist else "✗ FAILURE")
    return 0 if all_exist else 1

if __name__ == "__main__":
    sys.exit(main())