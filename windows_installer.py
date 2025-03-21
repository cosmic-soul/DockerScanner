#!/usr/bin/env python3
"""
Windows Installer Generator for Docker Service Manager

This script creates a Windows installer (.exe) for the Docker Service Manager
using PyInstaller. It bundles all dependencies into a single executable file.

Requirements:
- PyInstaller must be installed: pip install pyinstaller
- Only run this on Windows for best results
"""

import os
import sys
import subprocess
import platform
import shutil
from pathlib import Path

def check_platform():
    """Check if running on Windows."""
    if platform.system() != "Windows":
        print("Warning: This script is designed to run on Windows.")
        print(f"Current platform: {platform.system()}")
        return False
    return True

def install_dependencies():
    """Install required build dependencies."""
    print("Installing build dependencies...")
    dependencies = ["pyinstaller", "build", "wheel", "setuptools>=42"]
    
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade"] + dependencies)
        print("Dependencies installed successfully.\n")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error installing dependencies: {e}")
        return False

def clean_build_dirs():
    """Clean up build directories before starting a new build."""
    dirs_to_clean = ['build', 'dist', 'docker_service_manager.spec']
    print("Cleaning up previous build directories...")
    for directory in dirs_to_clean:
        if os.path.exists(directory):
            print(f"  Removing {directory}...")
            if os.path.isdir(directory):
                shutil.rmtree(directory)
            else:
                os.remove(directory)
    print("Clean up complete.\n")

def build_executable():
    """Build the Windows executable."""
    print("Building Windows executable...")
    
    # PyInstaller command to create a single-file executable
    command = [
        "pyinstaller",
        "--name=docker-service-manager",
        "--onefile",
        "--windowed",
        "--add-data=README.md;.",
        "--add-data=LICENSE;.",
        "--icon=generated-icon.png",
        "docker_service_manager.py"
    ]
    
    try:
        subprocess.check_call(command)
        print("Executable build complete.\n")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error building executable: {e}")
        return False

def create_installer():
    """Create a standalone installer using NSIS (if available)."""
    # Check if NSIS is installed
    nsis_path = shutil.which("makensis.exe")
    
    if not nsis_path:
        print("NSIS not found. Skipping installer creation.")
        print("To create an installer, install NSIS from https://nsis.sourceforge.io/\n")
        return False
    
    print("Creating installer using NSIS...")
    
    # Create NSIS script
    nsis_script = """
    !include "MUI2.nsh"
    
    ; Application name and version
    Name "Docker Service Manager"
    OutFile "Docker_Service_Manager_Setup.exe"
    
    ; Default installation directory
    InstallDir "$PROGRAMFILES\\Docker Service Manager"
    
    ; Request application privileges
    RequestExecutionLevel admin
    
    ; Interface settings
    !define MUI_ABORTWARNING
    !define MUI_ICON "generated-icon.png"
    
    ; Pages
    !insertmacro MUI_PAGE_WELCOME
    !insertmacro MUI_PAGE_DIRECTORY
    !insertmacro MUI_PAGE_INSTFILES
    !insertmacro MUI_PAGE_FINISH
    
    ; Language
    !insertmacro MUI_LANGUAGE "English"
    
    ; Installation section
    Section "Install"
        SetOutPath "$INSTDIR"
        
        ; Add files
        File "dist\\docker-service-manager.exe"
        File "README.md"
        File "LICENSE"
        
        ; Create start menu shortcut
        CreateDirectory "$SMPROGRAMS\\Docker Service Manager"
        CreateShortcut "$SMPROGRAMS\\Docker Service Manager\\Docker Service Manager.lnk" "$INSTDIR\\docker-service-manager.exe"
        
        ; Create uninstaller
        WriteUninstaller "$INSTDIR\\uninstall.exe"
        
        ; Add uninstaller to Add/Remove Programs
        WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\DockerServiceManager" "DisplayName" "Docker Service Manager"
        WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\DockerServiceManager" "UninstallString" "$INSTDIR\\uninstall.exe"
        WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\DockerServiceManager" "DisplayIcon" "$INSTDIR\\docker-service-manager.exe"
        WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\DockerServiceManager" "DisplayVersion" "1.0.0"
        WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\DockerServiceManager" "Publisher" "Docker Service Manager"
    SectionEnd
    
    ; Uninstaller section
    Section "Uninstall"
        ; Remove files
        Delete "$INSTDIR\\docker-service-manager.exe"
        Delete "$INSTDIR\\README.md"
        Delete "$INSTDIR\\LICENSE"
        Delete "$INSTDIR\\uninstall.exe"
        
        ; Remove shortcuts
        Delete "$SMPROGRAMS\\Docker Service Manager\\Docker Service Manager.lnk"
        RMDir "$SMPROGRAMS\\Docker Service Manager"
        
        ; Remove installation directory
        RMDir "$INSTDIR"
        
        ; Remove registry keys
        DeleteRegKey HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\DockerServiceManager"
    SectionEnd
    """
    
    # Write NSIS script to file
    with open("installer.nsi", "w") as f:
        f.write(nsis_script)
    
    # Run NSIS to create installer
    try:
        subprocess.check_call([nsis_path, "installer.nsi"])
        print("Installer created successfully.\n")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error creating installer: {e}")
        return False
    finally:
        # Clean up NSIS script
        if os.path.exists("installer.nsi"):
            os.remove("installer.nsi")

def main():
    """Main build process."""
    print("===============================================")
    print("Docker Service Manager - Windows Installer Builder")
    print("===============================================\n")
    
    print(f"Detected platform: {platform.system()} {platform.release()}")
    print(f"Python version: {sys.version.split()[0]}\n")
    
    # Warn if not on Windows but continue anyway
    check_platform()
    
    if not install_dependencies():
        print("Failed to install required dependencies. Exiting.")
        sys.exit(1)
    
    clean_build_dirs()
    
    if build_executable():
        print("Windows executable created successfully at:")
        print(f"  {os.path.abspath('dist/docker-service-manager.exe')}")
    else:
        print("Failed to build Windows executable. Exiting.")
        sys.exit(1)
    
    create_installer()
    
    print("\nBuild process completed!")
    print("===============================================")

if __name__ == "__main__":
    main()