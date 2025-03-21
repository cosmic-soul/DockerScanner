#!/usr/bin/env python3
"""
Build script for Docker Service Manager

This script builds the package for distribution in various formats:
1. Source distribution (.tar.gz)
2. Wheel distribution (.whl)
3. Optional Windows executable (.exe) using PyInstaller
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def clean_build_dirs():
    """Clean up build directories before starting a new build."""
    dirs_to_clean = ['build', 'dist', 'docker_service_manager.egg-info']
    print("Cleaning up previous build directories...")
    for directory in dirs_to_clean:
        if os.path.exists(directory):
            print(f"  Removing {directory}...")
            shutil.rmtree(directory)
    print("Clean up complete.\n")

def install_build_dependencies():
    """Install required build dependencies if needed."""
    dependencies = ["build", "wheel", "setuptools>=42"]
    print("Installing build dependencies...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade"] + dependencies)
    print("Dependencies installed.\n")

def build_package():
    """Build source and wheel distributions."""
    print("Building package distributions...")
    subprocess.check_call([sys.executable, "-m", "build"])
    print("\nPackage build complete. Distribution files are in the 'dist' directory.\n")

def list_distribution_files():
    """List the generated distribution files."""
    if os.path.exists('dist'):
        print("Generated distribution files:")
        for file in os.listdir('dist'):
            file_path = os.path.join('dist', file)
            size = os.path.getsize(file_path) / 1024  # size in KB
            print(f"  - {file} ({size:.1f} KB)")
    else:
        print("No distribution files found.")

def main():
    """Main build process."""
    print("===============================================")
    print("Docker Service Manager - Package Builder")
    print("===============================================\n")
    
    clean_build_dirs()
    install_build_dependencies()
    build_package()
    list_distribution_files()
    
    print("\nBuild process completed successfully!")
    print("To install the package, run: pip install dist/*.whl")
    print("To publish to PyPI, run: python -m twine upload dist/*")
    print("===============================================")

if __name__ == "__main__":
    main()