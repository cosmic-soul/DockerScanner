"""
Core service management functionality for Docker.
"""
import sys
import os
import platform
import time
import subprocess
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any, Union

try:
    import docker
    from docker.errors import DockerException
    DOCKER_AVAILABLE = True
except ImportError:
    DOCKER_AVAILABLE = False

try:
    from tabulate import tabulate
    TABULATE_AVAILABLE = True
except ImportError:
    TABULATE_AVAILABLE = False

class DockerServiceManager:
    """Manage Docker daemon and service operations."""

    def __init__(self, demo_mode=False):
        """Initialize service manager with system detection.
        
        Args:
            demo_mode (bool): If True, enables demo mode with simulated responses
        """
        self.demo_mode = demo_mode
        self.system = platform.system().lower()
        
        # Check for administrative privileges
        self.is_admin = self._check_admin_privileges()
        
        # Detect init system for Linux
        if self.system == 'linux':
            self.init_system = self._detect_init_system()
        else:
            self.init_system = None

    def _check_admin_privileges(self) -> bool:
        """Check if script is running with administrative privileges."""
        try:
            if self.system == 'windows':
                import ctypes
                return ctypes.windll.shell32.IsUserAnAdmin() != 0
            else:  # Linux, macOS, etc.
                return os.geteuid() == 0
        except Exception:
            # If we can't determine, assume not admin
            return False
            
    def _detect_init_system(self) -> Optional[str]:
        """Detect which init system is used on Linux."""
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
            
    def _run_command(self, command: List[str]) -> Tuple[bool, str]:
        """Run system command and return result."""
        try:
            result = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False
            )
            
            # Check if command was successful
            if result.returncode == 0:
                return True, result.stdout
            else:
                return False, result.stderr
        except Exception as e:
            return False, str(e)

    def _get_service_commands(self) -> Dict[str, List[str]]:
        """Get appropriate commands based on OS."""
        if self.system == 'linux':
            if self.init_system == 'systemd':
                return {
                    'status': ['systemctl', 'status', 'docker'],
                    'start': ['systemctl', 'start', 'docker'],
                    'stop': ['systemctl', 'stop', 'docker'],
                    'restart': ['systemctl', 'restart', 'docker'],
                    'enable': ['systemctl', 'enable', 'docker'],
                    'disable': ['systemctl', 'disable', 'docker'],
                    'socket_status': ['systemctl', 'status', 'docker.socket'],
                    'socket_start': ['systemctl', 'start', 'docker.socket'],
                    'socket_stop': ['systemctl', 'stop', 'docker.socket'],
                    'socket_enable': ['systemctl', 'enable', 'docker.socket'],
                    'socket_disable': ['systemctl', 'disable', 'docker.socket']
                }
            elif self.init_system == 'sysvinit':
                return {
                    'status': ['service', 'docker', 'status'],
                    'start': ['service', 'docker', 'start'],
                    'stop': ['service', 'docker', 'stop'],
                    'restart': ['service', 'docker', 'restart'],
                    'enable': ['update-rc.d', 'docker', 'defaults'],
                    'disable': ['update-rc.d', 'docker', 'remove'],
                    'socket_status': ['echo', 'Socket management not supported with SysVinit'],
                    'socket_start': ['echo', 'Socket management not supported with SysVinit'],
                    'socket_stop': ['echo', 'Socket management not supported with SysVinit'],
                    'socket_enable': ['echo', 'Socket management not supported with SysVinit'],
                    'socket_disable': ['echo', 'Socket management not supported with SysVinit']
                }
            else:
                # Neither systemd nor SysVinit detected
                return {
                    'status': ['echo', 'Docker service not detected (NixOS or container environment)'],
                    'start': ['echo', 'Docker service not detected (NixOS or container environment)'],
                    'stop': ['echo', 'Docker service not detected (NixOS or container environment)'],
                    'restart': ['echo', 'Docker service not detected (NixOS or container environment)'],
                    'enable': ['echo', 'Docker service not detected (NixOS or container environment)'],
                    'disable': ['echo', 'Docker service not detected (NixOS or container environment)'],
                    'socket_status': ['echo', 'Docker service not detected (NixOS or container environment)'],
                    'socket_start': ['echo', 'Docker service not detected (NixOS or container environment)'],
                    'socket_stop': ['echo', 'Docker service not detected (NixOS or container environment)'],
                    'socket_enable': ['echo', 'Docker service not detected (NixOS or container environment)'],
                    'socket_disable': ['echo', 'Docker service not detected (NixOS or container environment)']
                }
        elif self.system == 'darwin':  # macOS
            return {
                'status': ['launchctl', 'list', 'com.docker.docker'],
                'start': ['launchctl', 'start', 'com.docker.docker'],
                'stop': ['launchctl', 'stop', 'com.docker.docker'],
                'restart': ['launchctl', 'stop', 'com.docker.docker', '&&', 'launchctl', 'start', 'com.docker.docker'],
                'enable': ['launchctl', 'load', '-w', '/Library/LaunchDaemons/com.docker.docker.plist'],
                'disable': ['launchctl', 'unload', '-w', '/Library/LaunchDaemons/com.docker.docker.plist'],
                'socket_status': ['echo', 'Socket management not applicable on macOS'],
                'socket_start': ['echo', 'Socket management not applicable on macOS'],
                'socket_stop': ['echo', 'Socket management not applicable on macOS'],
                'socket_enable': ['echo', 'Socket management not applicable on macOS'],
                'socket_disable': ['echo', 'Socket management not applicable on macOS']
            }
        elif self.system == 'windows':
            return {
                'status': ['sc', 'query', 'docker'],
                'start': ['net', 'start', 'docker'],
                'stop': ['net', 'stop', 'docker'],
                'restart': ['net', 'stop', 'docker', '&&', 'net', 'start', 'docker'],
                'enable': ['sc', 'config', 'docker', 'start=', 'auto'],
                'disable': ['sc', 'config', 'docker', 'start=', 'disabled'],
                # Windows uses named pipes instead of sockets
                'socket_status': ['echo', 'Socket management not applicable on Windows'],
                'socket_start': ['echo', 'Socket management not applicable on Windows'],
                'socket_stop': ['echo', 'Socket management not applicable on Windows'],
                'socket_enable': ['echo', 'Socket management not applicable on Windows'],
                'socket_disable': ['echo', 'Socket management not applicable on Windows']
            }
        else:
            # Default to commands that will show helpful error
            return {
                'status': ['echo', f'Service management not implemented for {self.system}'],
                'start': ['echo', f'Service management not implemented for {self.system}'],
                'stop': ['echo', f'Service management not implemented for {self.system}'],
                'restart': ['echo', f'Service management not implemented for {self.system}'],
                'enable': ['echo', f'Service management not implemented for {self.system}'],
                'disable': ['echo', f'Service management not implemented for {self.system}'],
                'socket_status': ['echo', f'Socket management not implemented for {self.system}'],
                'socket_start': ['echo', f'Socket management not implemented for {self.system}'],
                'socket_stop': ['echo', f'Socket management not implemented for {self.system}'],
                'socket_enable': ['echo', f'Socket management not implemented for {self.system}'],
                'socket_disable': ['echo', f'Socket management not implemented for {self.system}']
            }
            
    def check_privileges(self) -> bool:
        """Check and inform about admin privileges."""
        if not self.is_admin:
            print("⚠️  Warning: Administrative privileges required for service management")
            print("   Some operations may fail without proper permissions")
            if self.system == 'linux' or self.system == 'darwin':
                print("   Try running with 'sudo' or as root")
            elif self.system == 'windows':
                print("   Try running as Administrator")
            return False
        return True
    
    def get_status(self) -> Tuple[bool, Optional[str]]:
        """Get Docker service status.
        
        Returns:
            Tuple of (success, error_code) where error_code is None on success
        """
        print("Checking Docker service status...")
        
        # If in demo mode, show simulated service status
        if self.demo_mode:
            print("\033[93mDEMO MODE\033[0m: Simulating Docker service status")
            print("Docker service is \033[92mrunning\033[0m")
            print("Status: Active")
            print("Docker version: 20.10.12")
            print("Containers: 4 (3 Running, 1 Stopped)")
            print("Images: 12")
            return True, None
            
        # Normal mode
        if not self.check_privileges():
            print("Attempting to check status anyway...")
            
        commands = self._get_service_commands()
        success, output = self._run_command(commands['status'])
        
        if success:
            print("Docker service status:")
            print(output)
            
            # Check if service is actually running
            if self.system == 'linux' and 'active' not in output.lower():
                return False, "service_not_running" 
            elif self.system == 'darwin' and not any(status in output.lower() for status in ['running', 'active']):
                return False, "service_not_running"
            elif self.system == 'windows' and 'running' not in output.lower():
                return False, "service_not_running"
                
            return True, None
        else:
            print(f"Error checking Docker service status: {output}")
            print("You can use --demo mode to see simulated output")
            
            if 'permission denied' in output.lower() or 'access is denied' in output.lower():
                return False, "permission_denied"
            
            return False, "docker_not_installed"
        
    def start_service(self) -> bool:
        """Start Docker service."""
        print("Starting Docker service...")
        
        # If in demo mode, simulate starting the service
        if self.demo_mode:
            print("\033[93mDEMO MODE\033[0m: Simulating Docker service start")
            print("✓ Docker service started successfully")
            time.sleep(1)  # Simulate startup time
            self.get_status()  # Will show demo status
            return True
            
        # Normal mode
        if not self.check_privileges():
            print("Attempting to start service anyway...")
            
        commands = self._get_service_commands()
        success, output = self._run_command(commands['start'])
        
        if success:
            print("✓ Docker service started successfully")
            # Verify service is running
            time.sleep(2)  # Give it time to start
            self.get_status()
        else:
            print(f"Error starting Docker service: {output}")
            print("You can use --demo mode to see simulated output")
            
        return success
        
    def stop_service(self) -> bool:
        """Stop Docker service."""
        print("Stopping Docker service...")
        
        # If in demo mode, simulate stopping the service
        if self.demo_mode:
            print("\033[93mDEMO MODE\033[0m: Simulating Docker service stop")
            time.sleep(1)  # Simulate shutdown time
            print("✓ Docker service stopped successfully")
            return True
        
        # Normal mode
        if not self.check_privileges():
            print("Attempting to stop service anyway...")
            
        commands = self._get_service_commands()
        success, output = self._run_command(commands['stop'])
        
        if success:
            print("✓ Docker service stopped successfully")
        else:
            print(f"Error stopping Docker service: {output}")
            print("You can use --demo mode to see simulated output")
            
        return success
        
    def restart_service(self) -> bool:
        """Restart Docker service."""
        print("Restarting Docker service...")
        
        # If in demo mode, simulate restarting the service
        if self.demo_mode:
            print("\033[93mDEMO MODE\033[0m: Simulating Docker service restart")
            time.sleep(1)  # Simulate restart time
            print("✓ Docker service restarted successfully")
            self.get_status()  # Will show demo status
            return True
            
        # Normal mode
        if not self.check_privileges():
            print("Attempting to restart service anyway...")
            
        commands = self._get_service_commands()
        success, output = self._run_command(commands['restart'])
        
        if success:
            print("✓ Docker service restarted successfully")
            # Verify service is running
            time.sleep(3)  # Give it time to restart
            self.get_status()
        else:
            print(f"Error restarting Docker service: {output}")
            print("You can use --demo mode to see simulated output")
            
        return success
        
    def enable_service(self) -> bool:
        """Enable Docker service to start at boot."""
        print("Enabling Docker service to start at boot...")
        
        # If in demo mode, simulate enabling the service
        if self.demo_mode:
            print("\033[93mDEMO MODE\033[0m: Simulating Docker service enable")
            time.sleep(1)  # Simulate enable time
            print("✓ Docker service enabled successfully")
            return True
            
        # Normal mode
        if not self.check_privileges():
            print("Attempting to enable service anyway...")
            
        commands = self._get_service_commands()
        success, output = self._run_command(commands['enable'])
        
        if success:
            print("✓ Docker service enabled successfully")
        else:
            print(f"Error enabling Docker service: {output}")
            print("You can use --demo mode to see simulated output")
            
        return success
        
    def disable_service(self) -> bool:
        """Disable Docker service from starting at boot."""
        print("Disabling Docker service from starting at boot...")
        
        # If in demo mode, simulate disabling the service
        if self.demo_mode:
            print("\033[93mDEMO MODE\033[0m: Simulating Docker service disable")
            time.sleep(1)  # Simulate disable time
            print("✓ Docker service disabled successfully")
            return True
            
        # Normal mode
        if not self.check_privileges():
            print("Attempting to disable service anyway...")
            
        commands = self._get_service_commands()
        success, output = self._run_command(commands['disable'])
        
        if success:
            print("✓ Docker service disabled successfully")
        else:
            print(f"Error disabling Docker service: {output}")
            print("You can use --demo mode to see simulated output")
            
        return success
    
    def get_socket_status(self) -> Tuple[bool, Optional[str]]:
        """Get Docker socket status.
        
        Returns:
            Tuple of (success, error_code) where error_code is None on success
        """
        print("Checking Docker socket status...")
        
        # If in demo mode, simulate socket status
        if self.demo_mode:
            print("\033[93mDEMO MODE\033[0m: Simulating Docker socket status")
            print("Docker socket is \033[92mactive\033[0m")
            print("Socket listening at: /var/run/docker.sock")
            return True, None
            
        # Normal mode
        if not self.check_privileges():
            print("Attempting to check socket status anyway...")
            
        commands = self._get_service_commands()
        success, output = self._run_command(commands['socket_status'])
        
        if success:
            print("Docker socket status:")
            print(output)
            
            # Check if socket is actually available
            if self.system == 'linux' and 'active' not in output.lower():
                return False, "socket_not_available"
                
            return True, None
        else:
            print(f"Error checking Docker socket status: {output}")
            print("You can use --demo mode to see simulated output")
            
            if 'permission denied' in output.lower() or 'access is denied' in output.lower():
                return False, "permission_denied"
            
            return False, "socket_not_available"
    
    def start_socket(self) -> bool:
        """Start Docker socket."""
        print("Starting Docker socket...")
        
        # If in demo mode, simulate starting the socket
        if self.demo_mode:
            print("\033[93mDEMO MODE\033[0m: Simulating Docker socket start")
            time.sleep(1)  # Simulate socket startup time
            print("✓ Docker socket started successfully")
            self.get_socket_status()  # Will show demo status
            return True
            
        # Normal mode
        if not self.check_privileges():
            print("Attempting to start socket anyway...")
            
        commands = self._get_service_commands()
        success, output = self._run_command(commands['socket_start'])
        
        if success:
            print("✓ Docker socket started successfully")
            # Verify socket is running
            time.sleep(2)  # Give it time to start
            self.get_socket_status()
        else:
            print(f"Error starting Docker socket: {output}")
            print("You can use --demo mode to see simulated output")
            
        return success
    
    def stop_socket(self) -> bool:
        """Stop Docker socket."""
        print("Stopping Docker socket...")
        
        # If in demo mode, simulate stopping the socket
        if self.demo_mode:
            print("\033[93mDEMO MODE\033[0m: Simulating Docker socket stop")
            time.sleep(1)  # Simulate socket shutdown time
            print("✓ Docker socket stopped successfully")
            return True
            
        # Normal mode
        if not self.check_privileges():
            print("Attempting to stop socket anyway...")
            
        commands = self._get_service_commands()
        success, output = self._run_command(commands['socket_stop'])
        
        if success:
            print("✓ Docker socket stopped successfully")
        else:
            print(f"Error stopping Docker socket: {output}")
            print("You can use --demo mode to see simulated output")
            
        return success
    
    def enable_socket(self) -> bool:
        """Enable Docker socket to start at boot."""
        print("Enabling Docker socket to start at boot...")
        
        # If in demo mode, simulate enabling the socket
        if self.demo_mode:
            print("\033[93mDEMO MODE\033[0m: Simulating Docker socket enable")
            time.sleep(1)  # Simulate enable time
            print("✓ Docker socket enabled successfully")
            return True
            
        # Normal mode
        if not self.check_privileges():
            print("Attempting to enable socket anyway...")
            
        commands = self._get_service_commands()
        success, output = self._run_command(commands['socket_enable'])
        
        if success:
            print("✓ Docker socket enabled successfully")
        else:
            print(f"Error enabling Docker socket: {output}")
            print("You can use --demo mode to see simulated output")
            
        return success
    
    def disable_socket(self) -> bool:
        """Disable Docker socket from starting at boot."""
        print("Disabling Docker socket from starting at boot...")
        
        # If in demo mode, simulate disabling the socket
        if self.demo_mode:
            print("\033[93mDEMO MODE\033[0m: Simulating Docker socket disable")
            time.sleep(1)  # Simulate disable time
            print("✓ Docker socket disabled successfully")
            return True
            
        # Normal mode
        if not self.check_privileges():
            print("Attempting to disable socket anyway...")
            
        commands = self._get_service_commands()
        success, output = self._run_command(commands['socket_disable'])
        
        if success:
            print("✓ Docker socket disabled successfully")
        else:
            print(f"Error disabling Docker socket: {output}")
            print("You can use --demo mode to see simulated output")
            
        return success
    
    def list_containers(self) -> Tuple[bool, Optional[str]]:
        """List all Docker containers.
        
        Returns:
            Tuple of (success, error_code) where error_code is None on success
        """
        # If in demo mode, show simulated containers
        if self.demo_mode:
            print("Connecting to Docker... (Demo Mode)")
            
            # Create sample containers for demonstration
            table_data = [
                ["abc123", "demo-webserver", "\033[92mrunning\033[0m", "2023-01-01 09:00:00", "nginx:latest"],
                ["def456", "demo-database", "\033[92mrunning\033[0m", "2023-01-01 09:01:15", "mysql:8.0"],
                ["ghi789", "demo-redis", "\033[93mrestarting\033[0m", "2023-01-01 09:02:30", "redis:alpine"],
                ["jkl012", "demo-backup", "\033[91mexited\033[0m", "2023-01-01 09:03:45", "alpine:latest"]
            ]
            
            # Display the table
            headers = ["ID", "Name", "Status", "Created", "Image"]
            if TABULATE_AVAILABLE:
                print(tabulate(table_data, headers=headers, tablefmt="pretty"))
            else:
                print("CONTAINER ID | NAME | STATUS | CREATED | IMAGE")
                print("-" * 80)
                for row in table_data:
                    print(" | ".join(row))
                    
            return True, None
            
        # Normal mode - try to connect to real Docker
        if not DOCKER_AVAILABLE:
            print("Error: Docker Python SDK not installed.")
            print("Install with: pip install docker")
            print("Or run with --demo mode to see simulated output")
            return False, "docker_not_installed"
            
        try:
            print("Connecting to Docker...")
            client = docker.from_env()
            containers = client.containers.list(all=True)
            
            if not containers:
                print("No containers found.")
                return True, None
            
            # Prepare table data
            table_data = []
            for container in containers:
                # Format container created time
                created = datetime.fromtimestamp(container.attrs['Created'])
                created_str = created.strftime('%Y-%m-%d %H:%M:%S')
                
                # Get status with color
                status = container.status
                if status == 'running':
                    status_display = f"\033[92m{status}\033[0m"  # Green for running
                elif status == 'exited':
                    status_display = f"\033[91m{status}\033[0m"  # Red for exited
                else:
                    status_display = f"\033[93m{status}\033[0m"  # Yellow for others
                
                # Add row to table
                table_data.append([
                    container.short_id, 
                    container.name, 
                    status_display,
                    created_str, 
                    container.image.tags[0] if container.image.tags else "none"
                ])
            
            # Display the table
            headers = ["ID", "Name", "Status", "Created", "Image"]
            if TABULATE_AVAILABLE:
                print(tabulate(table_data, headers=headers, tablefmt="pretty"))
            else:
                print("CONTAINER ID | NAME | STATUS | CREATED | IMAGE")
                print("-" * 80)
                for row in table_data:
                    print(" | ".join(row))
            
            return True, None
        except DockerException as e:
            print(f"Error connecting to Docker: {e}")
            print("Make sure Docker service is running.")
            print("Or try running with --demo mode for demonstration")
            
            # Check if the error indicates service not running
            if "connect to the Docker daemon" in str(e) or "Is the docker daemon running" in str(e):
                return False, "service_not_running"
                
            return False, "docker_not_installed"
        except Exception as e:
            print(f"Error listing containers: {e}")
            return False, None
    
    def check_docker_info(self) -> Tuple[bool, Optional[str]]:
        """Get Docker system info.
        
        Returns:
            Tuple of (success, error_code) where error_code is None on success
        """
        # If in demo mode, show simulated Docker info
        if self.demo_mode:
            print("Connecting to Docker... (Demo Mode)")
            
            # Prepare demo data for basic info
            basic_info = [
                ["Docker Version", "20.10.12"],
                ["OS/Arch", "Linux/x86_64"],
                ["Kernel Version", "5.4.0-81-generic"],
                ["Containers", "4"],
                ["Images", "12"],
                ["CPUs", "8"],
                ["Memory", "16.00 GB"]
            ]
            
            print("\n=== Docker System Information (Demo Mode) ===")
            if TABULATE_AVAILABLE:
                print(tabulate(basic_info, tablefmt="plain"))
            else:
                for key, value in basic_info:
                    print(f"{key}: {value}")
            
            # Print storage driver info
            print("\n=== Storage Driver ===")
            driver_info = [
                ["Driver", "overlay2"],
                ["Root Dir", "/var/lib/docker"]
            ]
            if TABULATE_AVAILABLE:
                print(tabulate(driver_info, tablefmt="plain"))
            else:
                for key, value in driver_info:
                    print(f"{key}: {value}")
            
            # Print networking info
            print("\n=== Network ===")
            net_info = [
                ["bridge", "Bridge network driver"],
                ["host", "Host network driver"],
                ["overlay", "Overlay network driver"],
                ["macvlan", "Macvlan network driver"]
            ]
            if TABULATE_AVAILABLE:
                print(tabulate(net_info, tablefmt="plain"))
            else:
                for key, value in net_info:
                    print(f"{key}: {value}")
            
            return True, None
            
        # Normal mode - try to connect to real Docker
        if not DOCKER_AVAILABLE:
            print("Error: Docker Python SDK not installed.")
            print("Install with: pip install docker")
            print("Or run with --demo mode to see simulated output")
            return False, "docker_not_installed"
            
        try:
            print("Connecting to Docker...")
            client = docker.from_env()
            info = client.info()
            
            # Prepare table for basic info
            basic_info = [
                ["Docker Version", info.get('ServerVersion', 'Unknown')],
                ["OS/Arch", f"{info.get('OperatingSystem', 'Unknown')}/{info.get('Architecture', 'Unknown')}"],
                ["Kernel Version", info.get('KernelVersion', 'Unknown')],
                ["Containers", str(info.get('Containers', 'Unknown'))],
                ["Images", str(info.get('Images', 'Unknown'))],
                ["CPUs", str(info.get('NCPU', 'Unknown'))],
                ["Memory", f"{info.get('MemTotal', 0) / (1024*1024*1024):.2f} GB"]
            ]
            
            print("\n=== Docker System Information ===")
            if TABULATE_AVAILABLE:
                print(tabulate(basic_info, tablefmt="plain"))
            else:
                for key, value in basic_info:
                    print(f"{key}: {value}")
            
            # Print storage driver info
            print("\n=== Storage Driver ===")
            driver_info = [
                ["Driver", info.get('Driver', 'Unknown')],
                ["Root Dir", info.get('DockerRootDir', 'Unknown')]
            ]
            if TABULATE_AVAILABLE:
                print(tabulate(driver_info, tablefmt="plain"))
            else:
                for key, value in driver_info:
                    print(f"{key}: {value}")
            
            # Print networking info
            print("\n=== Network ===")
            net_info = []
            for net_name, net_data in info.get('Plugins', {}).get('Network', {}).items():
                net_info.append([net_name, str(net_data)])
                
            if TABULATE_AVAILABLE:
                print(tabulate(net_info, tablefmt="plain"))
            else:
                for name, details in net_info:
                    print(f"{name}: {details}")
            
            return True, None
        except DockerException as e:
            print(f"Error connecting to Docker: {e}")
            print("Make sure Docker service is running.")
            print("Or try running with --demo mode for demonstration")
            
            # Check if the error indicates service not running
            if "connect to the Docker daemon" in str(e) or "Is the docker daemon running" in str(e):
                return False, "service_not_running"
                
            return False, "docker_not_installed"
        except Exception as e:
            print(f"Error getting Docker info: {e}")
            return False, None