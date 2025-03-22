
#!/bin/bash
# Reinstallation script for Docker Service Manager
# This script uninstalls any existing installation and reinstalls it

echo "==============================================="
echo "Docker Service Manager - Reinstallation"
echo "==============================================="

# Create required directories if they don't exist
echo "Creating required directories..."
mkdir -p docker_service_manager

# Uninstall previous versions if they exist
echo "Uninstalling previous versions if they exist..."
pip uninstall -y docker-service-manager

# Clean any leftover files and egg-info directories
echo "Cleaning any leftover files and egg-info directories..."
rm -rf *.egg-info
rm -rf build/ dist/

# Install in development mode to ensure proper module paths
echo "Installing in development mode to ensure proper module paths..."
pip install -e .

# Test the installation
echo "Testing installation..."
if python -c "from docker_service_manager import main; print('Module import successful!')" 2>/dev/null; then
    echo ""
    echo "Installation completed successfully!"
    echo "You can now run Docker Service Manager by typing:"
    echo "  docker-service-manager"
    echo "  dsm"
    echo "==============================================="
else
    echo ""
    echo "Installation failed. The module could not be imported."
    echo "Try running the installation manually:"
    echo "  pip install -e ."
    echo "==============================================="
    exit 1
fi
