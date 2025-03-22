
#!/bin/bash
# Reinstallation script for Docker Service Manager

echo "==============================================="
echo "Docker Service Manager - Reinstallation"
echo "==============================================="
echo ""

echo "Creating required directories..."
mkdir -p docker_service_manager

echo "Uninstalling previous versions if they exist..."
pip uninstall -y docker-service-manager

echo "Installing in development mode to ensure proper module paths..."
pip install -e .

echo "Testing installation..."
python -c "from docker_service_manager import main; print('Module import successful!')"

if [ $? -eq 0 ]; then
    echo ""
    echo "Installation completed successfully!"
    echo "You can now run Docker Service Manager by typing:"
    echo "  docker-service-manager"
    echo "  dsm"
else
    echo ""
    echo "Installation had issues. Please check the output above."
fi

echo "==============================================="
