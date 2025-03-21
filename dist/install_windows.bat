@echo off
REM Windows installation script for Docker Service Manager
REM This script will install the Docker Service Manager and its dependencies

echo ===============================================
echo Docker Service Manager - Windows Installation
echo ===============================================
echo.

REM Check for Python installation
python --version > nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Python is not installed or not in the PATH.
    echo Please install Python 3.11 or higher from https://www.python.org/downloads/
    echo Ensure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

REM Run the Python installation script
echo Installing Docker Service Manager...
echo.
python install.py

if %ERRORLEVEL% neq 0 (
    echo.
    echo Installation failed. Please check the output above for errors.
    pause
    exit /b 1
)

echo.
echo Installation completed successfully!
echo You can now run Docker Service Manager by typing:
echo   docker-service-manager
echo   dsm
echo.
echo Thank you for installing Docker Service Manager!
echo ===============================================
pause