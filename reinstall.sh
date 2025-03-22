
#!/bin/bash

echo "==============================================="
echo "Docker Service Manager - Reinstallation"
echo "==============================================="
echo ""

echo "Creating required directories..."
mkdir -p ~/.local/bin

echo "Uninstalling previous versions if they exist..."
pip uninstall -y docker-service-manager

echo "Cleaning any leftover files and egg-info directories..."
rm -rf build/ dist/ *.egg-info/

echo "Installing in development mode to ensure proper module paths..."
pip install -e .

echo "Testing installation..."
if python -c "from docker_service_manager import main; print('Module import successful!')" &> /dev/null; then
    echo "Module import successful!"
    echo ""
    echo "Installation completed successfully!"
    echo "You can now run Docker Service Manager by typing:"
    echo "  docker-service-manager"
    echo "  dsm"
else
    echo "ERROR: Module import failed!"
    echo "Please check your installation and try again."
fi
echo "==============================================="
