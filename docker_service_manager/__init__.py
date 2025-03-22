
"""
Docker Service Manager - Main Module

This module serves as the entry point for the Docker Service Manager application.
"""

import sys
import os
from docker_manager.utils.display import show_banner
from docker_manager.utils.system import check_requirements
from docker_manager.ui.cli import setup_argparse, process_args

def main():
    """Main entry point for the application."""
    # Show banner
    show_banner()
    
    # Set up command line argument parsing
    parser = setup_argparse()
    args = parser.parse_args()
    
    # Check requirements (Docker SDK, tabulate, etc.)
    check_requirements()
    
    # Process arguments and execute requested commands
    # This will handle TUI and interactive modes
    exit_code = process_args(args)
    
    # Exit with appropriate code (0 for success, non-zero for error)
    sys.exit(exit_code)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(130)  # Standard exit code for SIGINT
    except ModuleNotFoundError as e:
        print(f"\nError: Required module not found - {e}")
        print("Try installing requirements with: pip install -r requirements.txt")
        print("\nYou may need to run the reinstall script: ./reinstall.sh")
        sys.exit(2)
    except PermissionError as e:
        print("\nError: Administrative privileges required")
        print("Try running with sudo (Linux/macOS) or as Administrator (Windows)")
        sys.exit(3)
    except Exception as e:
        print(f"\nError: Unexpected error - {e}")
        sys.exit(1)
