#!/usr/bin/env python3
"""
Installation script for Docker Service Manager

This script automates the installation of Docker Service Manager
and its dependencies. It can be run directly without requiring users
to understand Python packaging.
"""

import os
import sys
import subprocess
import platform
import argparse
from pathlib import Path

def check_python_version():
    """Check if Python version meets requirements."""
    required_version = (3, 11)
    current_version = sys.version_info
    
    if current_version < required_version:
        print(f"Error: Python {required_version[0]}.{required_version[1]} or higher is required.")
        print(f"Current Python version is {current_version[0]}.{current_version[1]}.{current_version[2]}")
        return False
    return True

def install_dependencies():
    """Install required dependencies."""
    print("Installing dependencies...")
    dependencies = [
        "blessed>=1.20.0",
        "docker>=7.1.0",
        "matplotlib>=3.10.1",
        "psutil>=7.0.0",
        "py-cui>=0.1.6",
        "tabulate>=0.9.0",
    ]
    
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade"] + dependencies)
    print("Dependencies installed successfully.\n")

def install_package(editable=False):
    """Install the package."""
    print("Installing Docker Service Manager...")
    cmd = [sys.executable, "-m", "pip", "install"]
    
    if editable:
        cmd.append("-e")
    
    cmd.append(".")
    
    subprocess.check_call(cmd)
    print("Docker Service Manager installed successfully!\n")

def verify_installation():
    """Verify the installation by running a simple command."""
    try:
        print("Verifying installation...")
        # Import the module to verify it's installed correctly
        from importlib import import_module
        import_module("docker_manager")
        
        print("Docker Service Manager has been successfully installed!")
        print("\nTo use the tool, run one of the following commands:")
        print("  docker-service-manager --help")
        print("  dsm --help")
        print("  python -m docker_service_manager --help")
        return True
    except ImportError as e:
        print(f"Error verifying installation: {e}")
        return False

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Install Docker Service Manager")
    parser.add_argument("--editable", "-e", action="store_true", 
                      help="Install in editable mode for development")
    return parser.parse_args()

def main():
    """Main installation process."""
    args = parse_args()
    
    print("===============================================")
    print("Docker Service Manager - Installation")
    print("===============================================\n")
    
    print(f"Detected platform: {platform.system()} {platform.release()}")
    print(f"Python version: {sys.version.split()[0]}\n")
    
    if not check_python_version():
        sys.exit(1)
    
    try:
        install_dependencies()
        install_package(args.editable)
        if verify_installation():
            print("\nInstallation completed successfully!")
        else:
            print("\nInstallation completed with warnings. Please check the output above.")
    except Exception as e:
        print(f"\nError during installation: {e}")
        sys.exit(1)
    
    print("===============================================")

if __name__ == "__main__":
    main()