"""
System utilities for Docker service manager.
"""
import os
import sys
import platform
import subprocess
from typing import List, Tuple, Optional, Any, Dict

def check_requirements() -> bool:
    """Check if required dependencies are installed."""
    # Check for Docker SDK
    try:
        import docker
        docker_available = True
    except ImportError:
        docker_available = False
    
    # Check for tabulate
    try:
        import tabulate
        tabulate_available = True
    except ImportError:
        tabulate_available = False
    
    # Report on requirements
    if not docker_available:
        print("Warning: Docker SDK for Python not found.")
        print("Install with: pip install docker")
    
    if not tabulate_available:
        print("Warning: tabulate package not found.")
        print("Install with: pip install tabulate for better table formatting")
    
    return docker_available or tabulate_available  # Return True if at least one is available

def check_admin_privileges() -> bool:
    """Check if running with administrative privileges."""
    try:
        system = platform.system().lower()
        if system == 'windows':
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        else:  # Linux, macOS, etc.
            return os.geteuid() == 0
    except Exception:
        # If we can't determine, assume not admin
        return False

def detect_init_system() -> Optional[str]:
    """Detect which init system is used on Linux."""
    system = platform.system().lower()
    
    if system != 'linux':
        return None
    
    # Check for systemd
    if os.path.exists('/run/systemd/system'):
        return 'systemd'
    
    # Check for SysVinit
    elif os.path.exists('/etc/init.d'):
        return 'sysvinit'
        
    # Check for Upstart
    elif os.path.exists('/sbin/initctl'):
        return 'upstart'
        
    # Couldn't determine
    return None

def get_system_info() -> Dict[str, str]:
    """Get system information.
    
    Returns:
        Dictionary containing system information
    """
    system = platform.system()
    
    info = {
        'system': system,
        'release': platform.release(),
        'version': platform.version(),
        'architecture': platform.machine(),
        'hostname': platform.node(),
        'python_version': platform.python_version(),
    }
    
    if system.lower() == 'linux':
        info['init_system'] = detect_init_system() or 'Unknown'
        info['is_admin'] = 'Yes' if check_admin_privileges() else 'No'
        
        # Try to get distribution info
        try:
            import distro
            info['distribution'] = distro.name(pretty=True)
        except ImportError:
            try:
                # Fallback if distro is not available
                with open('/etc/os-release', 'r') as f:
                    for line in f:
                        if line.startswith('PRETTY_NAME='):
                            info['distribution'] = line.split('=')[1].strip().strip('"')
                            break
            except:
                info['distribution'] = 'Unknown'
    
    return info

def run_command(command: List[str], check: bool = False) -> Tuple[bool, str]:
    """Run system command and return result.
    
    Args:
        command: Command to run as list of arguments
        check: Whether to check the return code
        
    Returns:
        Tuple of (success, output)
    """
    try:
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=check
        )
        
        # Check if command was successful
        if result.returncode == 0:
            return True, result.stdout
        else:
            return False, result.stderr
    except Exception as e:
        return False, str(e)