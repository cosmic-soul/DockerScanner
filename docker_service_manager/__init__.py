
#!/usr/bin/env python3
"""
Docker Service Manager - Package initialization
"""
from docker_manager.utils.display import show_banner
from docker_manager.utils.system import check_requirements
from docker_manager.ui.cli import setup_argparse, process_args
from docker_manager.ui.interactive import InteractiveConsole

def main():
    """Main entry point for the application."""
    # Import these locally to reduce startup time
    import sys
    
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

# Version information
__version__ = "1.0.0"
