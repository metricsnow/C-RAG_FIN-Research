#!/usr/bin/env python3
"""
Validation script to verify environment setup and dependencies.
Run this after setting up the virtual environment and installing dependencies.
"""

import importlib
import sys
from pathlib import Path


def check_python_version():
    """Verify Python version is 3.11+"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 11):
        print(
            f"❌ Python version {version.major}.{version.minor} is below required 3.11+"
        )
        return False
    print(f"✅ Python version {version.major}.{version.minor}.{version.micro}")
    return True


def check_dependency(package_name, import_name=None):
    """Check if a Python package is installed and importable"""
    if import_name is None:
        import_name = package_name

    try:
        importlib.import_module(import_name)
        print(f"✅ {package_name}")
        return True
    except ImportError:
        print(f"❌ {package_name} - Not installed or importable")
        return False


def check_env_file():
    """Check if .env file exists"""
    env_path = Path(".env")
    if env_path.exists():
        print("✅ .env file exists")
        return True
    else:
        print("⚠️  .env file not found - copy from .env.example")
        return False


def check_directory_structure():
    """Verify required directories exist"""
    required_dirs = [
        "app",
        "app/ingestion",
        "app/rag",
        "app/ui",
        "app/vector_db",
        "app/utils",
        "data",
        "data/documents",
        "data/chroma_db",
        "tests",
    ]

    all_exist = True
    for dir_path in required_dirs:
        path = Path(dir_path)
        if path.exists() and path.is_dir():
            print(f"✅ {dir_path}/")
        else:
            print(f"❌ {dir_path}/ - Missing")
            all_exist = False

    return all_exist


def main():
    """Run all validation checks"""
    print("=" * 60)
    print("Environment Setup Validation")
    print("=" * 60)
    print()

    results = []

    print("Python Version:")
    results.append(check_python_version())
    print()

    print("Dependencies:")
    dependencies = [
        ("langchain", "langchain"),
        ("langchain-community", "langchain_community"),
        ("streamlit", "streamlit"),
        ("chromadb", "chromadb"),
        ("python-dotenv", "dotenv"),
        ("openai", "openai"),
    ]

    for package, import_name in dependencies:
        results.append(check_dependency(package, import_name))
    print()

    print("Configuration:")
    results.append(check_env_file())
    print()

    print("Directory Structure:")
    results.append(check_directory_structure())
    print()

    print("=" * 60)
    if all(results):
        print("✅ All checks passed! Environment is ready.")
        return 0
    else:
        print("❌ Some checks failed. Please review and fix issues.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
