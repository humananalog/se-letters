#!/usr/bin/env python3
"""Setup script for the SE Letters project."""

import sys
from pathlib import Path
import subprocess
import shutil


def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 9):
        print("❌ Python 3.9 or higher is required")
        sys.exit(1)
    major, minor = sys.version_info.major, sys.version_info.minor
    print(f"✅ Python {major}.{minor} detected")


def check_tesseract():
    """Check if Tesseract OCR is installed."""
    try:
        subprocess.run(
            ["tesseract", "--version"],
            capture_output=True,
            text=True,
            check=True
        )
        print("✅ Tesseract OCR found")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠️  Tesseract OCR not found")
        print("   Install it from: https://github.com/tesseract-ocr/tesseract")
        return False


def create_virtual_environment():
    """Create a virtual environment if it doesn't exist."""
    venv_path = Path("venv")
    if venv_path.exists():
        print("✅ Virtual environment already exists")
        return
    
    print("📦 Creating virtual environment...")
    subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
    print("✅ Virtual environment created")


def install_dependencies():
    """Install project dependencies."""
    print("📦 Installing dependencies...")
    
    # Determine the correct pip path
    if sys.platform == "win32":
        pip_path = Path("venv/Scripts/pip")
    else:
        pip_path = Path("venv/bin/pip")
    
    # Install requirements
    subprocess.run([
        str(pip_path), "install", "-r", "requirements.txt"
    ], check=True)
    
    # Install project in development mode
    subprocess.run([
        str(pip_path), "install", "-e", "."
    ], check=True)
    
    print("✅ Dependencies installed")


def setup_environment_file():
    """Set up the environment file."""
    env_file = Path(".env")
    env_example = Path("config/env.example")
    
    if env_file.exists():
        print("✅ Environment file already exists")
        return
    
    if env_example.exists():
        shutil.copy(env_example, env_file)
        print("✅ Environment file created from template")
        print("   📝 Please edit .env and add your xAI API key")
    else:
        print("⚠️  Environment template not found")


def setup_pre_commit():
    """Set up pre-commit hooks."""
    try:
        if sys.platform == "win32":
            pre_commit_path = Path("venv/Scripts/pre-commit")
        else:
            pre_commit_path = Path("venv/bin/pre-commit")
        
        subprocess.run([str(pre_commit_path), "install"], check=True)
        print("✅ Pre-commit hooks installed")
    except subprocess.CalledProcessError:
        print("⚠️  Failed to install pre-commit hooks")


def create_data_directories():
    """Create necessary data directories."""
    directories = [
        "data/input/letters",
        "data/output/json",
        "data/temp",
        "logs",
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    print("✅ Data directories created")


def run_tests():
    """Run tests to verify setup."""
    print("🧪 Running tests...")
    
    try:
        if sys.platform == "win32":
            pytest_path = Path("venv/Scripts/pytest")
        else:
            pytest_path = Path("venv/bin/pytest")
        
        result = subprocess.run([
            str(pytest_path), "tests/", "-v", "--tb=short"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ All tests passed")
        else:
            print("⚠️  Some tests failed")
            print(result.stdout)
            print(result.stderr)
    except Exception as e:
        print(f"⚠️  Could not run tests: {e}")


def main():
    """Main setup function."""
    print("🚀 Setting up SE Letters project...")
    print("=" * 50)
    
    # Check requirements
    check_python_version()
    tesseract_available = check_tesseract()
    
    # Setup project
    create_virtual_environment()
    install_dependencies()
    setup_environment_file()
    setup_pre_commit()
    create_data_directories()
    
    # Run tests
    run_tests()
    
    print("=" * 50)
    print("🎉 Setup complete!")
    print()
    print("Next steps:")
    print("1. Edit .env file and add your xAI API key")
    print("2. Add your input files to data/input/letters/")
    print("3. Add your Excel file to data/input/")
    print("4. Run: se-letters run")
    print()
    
    if not tesseract_available:
        print("⚠️  Don't forget to install Tesseract OCR for image processing")
    
    print("For more information, see README.md")


if __name__ == "__main__":
    main() 