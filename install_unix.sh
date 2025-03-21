#!/bin/bash
# Installation script for Docker Service Manager on Linux/macOS
# This script will install the Docker Service Manager and its dependencies

echo "==============================================="
echo "Docker Service Manager - Unix Installation"
echo "==============================================="
echo ""

# Check for Python installation
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is not installed or not in the PATH."
    echo "Please install Python 3.11 or higher using your package manager:"
    echo "  - For Ubuntu/Debian: sudo apt install python3 python3-pip"
    echo "  - For Fedora: sudo dnf install python3 python3-pip"
    echo "  - For macOS: brew install python3"
    echo ""
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
if [[ $(echo "$PYTHON_VERSION < 3.11" | bc) -eq 1 ]]; then
    echo "Python version 3.11 or higher is required."
    echo "Current version: $PYTHON_VERSION"
    echo "Please update your Python installation."
    echo ""
    exit 1
fi

# Run the Python installation script
echo "Installing Docker Service Manager..."
echo ""
python3 install.py

if [ $? -ne 0 ]; then
    echo ""
    echo "Installation failed. Please check the output above for errors."
    exit 1
fi

# Check if the command is available in PATH
if command -v docker-service-manager &> /dev/null; then
    echo ""
    echo "Installation completed successfully!"
    echo "You can now run Docker Service Manager by typing:"
    echo "  docker-service-manager"
    echo "  dsm"
else
    echo ""
    echo "Installation completed, but the command may not be in your PATH."
    echo "You may need to restart your terminal or add the installation directory to your PATH."
    echo "You can still run the tool using:"
    echo "  python3 -m docker_service_manager"
fi

echo ""
echo "Thank you for installing Docker Service Manager!"
echo "==============================================="