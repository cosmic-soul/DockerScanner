"""
Display utilities for Docker service manager.
"""
import os
import shutil
from typing import List, Tuple, Optional, Any, Dict

# ANSI color codes
COLORS = {
    "RESET": "\033[0m",
    "RED": "\033[91m",
    "GREEN": "\033[92m",
    "YELLOW": "\033[93m",
    "BLUE": "\033[94m",
    "MAGENTA": "\033[95m",
    "CYAN": "\033[96m",
    "WHITE": "\033[97m",
    "BOLD": "\033[1m",
    "UNDERLINE": "\033[4m"
}

def get_terminal_size() -> Tuple[int, int]:
    """Get terminal width and height."""
    try:
        columns, rows = shutil.get_terminal_size()
        return columns, rows
    except (AttributeError, ValueError, OSError):
        # Default values if can't determine
        return 80, 24

def show_banner() -> None:
    """Display tool banner."""
    terminal_width, _ = get_terminal_size()
    banner = f"""
    {COLORS["BOLD"]}____             __                __  ___                                 
   / __ \____  _____/ /_____  _____   /  |/  /___ _____  ____ _____ ____  _____
  / / / / __ \/ ___/ //_/ _ \/ ___/  / /|_/ / __ `/ __ \/ __ `/ __ `/ _ \/ ___/
 / /_/ / /_/ / /__/ ,< /  __/ /     / /  / / /_/ / / / / /_/ / /_/ /  __/ /    
/_____/\____/\___/_/|_|\___/_/     /_/  /_/\__,_/_/ /_/\__,_/\__, /\___/_/     
                                                             /____/             
 Service Manager v1.0 - Cross-platform Docker daemon control{COLORS["RESET"]}"""
    
    print(banner)
    print("=" * terminal_width)
    
def print_status(message: str, status: str, *, demo_mode: bool = False) -> None:
    """Print a status message with color-coded status indicator.
    
    Args:
        message: The message to display
        status: Status string ('ok', 'error', 'warning', 'info')
        demo_mode: Whether to prefix with demo mode indicator
    """
    status_lower = status.lower()
    
    if status_lower == 'ok':
        status_display = f"{COLORS['GREEN']}[OK]{COLORS['RESET']}"
    elif status_lower == 'error':
        status_display = f"{COLORS['RED']}[ERROR]{COLORS['RESET']}"
    elif status_lower == 'warning':
        status_display = f"{COLORS['YELLOW']}[WARNING]{COLORS['RESET']}"
    elif status_lower == 'info':
        status_display = f"{COLORS['BLUE']}[INFO]{COLORS['RESET']}"
    else:
        status_display = f"[{status}]"
    
    demo_prefix = f"{COLORS['YELLOW']}[DEMO MODE]{COLORS['RESET']} " if demo_mode else ""
    print(f"{demo_prefix}{status_display} {message}")

def print_table(headers: List[str], rows: List[List[Any]]) -> None:
    """Print a formatted table.
    
    Args:
        headers: List of column headers
        rows: List of rows, each containing list of values
    """
    try:
        from tabulate import tabulate
        print(tabulate(rows, headers=headers, tablefmt="pretty"))
        return
    except ImportError:
        pass
    
    # Fallback if tabulate is not available
    if not rows:
        print("No data available")
        return
    
    # Calculate column widths
    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], len(str(cell)))
    
    # Print headers
    header_formatted = " | ".join(h.ljust(col_widths[i]) for i, h in enumerate(headers))
    print(header_formatted)
    print("-" * len(header_formatted))
    
    # Print rows
    for row in rows:
        row_formatted = " | ".join(str(cell).ljust(col_widths[i]) for i, cell in enumerate(row))
        print(row_formatted)

def print_section(title: str) -> None:
    """Print a section title with formatting.
    
    Args:
        title: Section title
    """
    terminal_width, _ = get_terminal_size()
    print()
    print(f"{COLORS['BOLD']}=== {title} ==={COLORS['RESET']}")
    print("-" * min(len(title) + 8, terminal_width))