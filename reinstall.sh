#!/bin/bash
# Reinstallation script for Docker Service Manager

echo "==============================================="
echo "Docker Service Manager - Reinstallation"
echo "==============================================="

# Creating required directories...
mkdir -p docker_service_manager docker_manager

# Uninstalling previous versions if they exist...
pip uninstall -y docker-service-manager

# Cleaning any leftover files and egg-info directories...
rm -rf *.egg-info build/ dist/ docker_service_manager.egg-info/

# Installing in development mode to ensure proper module paths...
pip install -e .

# Testing installation...
echo "Testing installation..."
python -c "from docker_service_manager import main; print('Module import successful!')"

echo ""
echo "Installation completed successfully!"
echo "You can now run Docker Service Manager by typing:"
echo "  docker-service-manager"
echo "  dsm"
echo "==============================================="