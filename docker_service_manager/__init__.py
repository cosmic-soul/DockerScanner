"""
Docker Service Manager - Package initialization

This module provides the entry point for the Docker Service Manager application.
"""

import sys
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
    exit_code = process_args(args)

    # Exit with appropriate code (0 for success, non-zero for error)
    sys.exit(exit_code)

if __name__ == "__main__":
    main()