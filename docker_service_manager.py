#!/usr/bin/env python3
import docker
import sys
import os
import time
import argparse
import subprocess
import platform
import shutil
from tabulate import tabulate
from datetime import datetime

class DockerServiceManager:
    """Manage Docker daemon and service operations."""
    
    def __init__(self):
        """Initialize service manager with system detection."""
        self.system = platform.system().lower()
        self.is_admin = self._check_admin_privileges()
        
    def _check_admin_privileges(self):
        """Check if script is running with administrative privileges."""
        try:
            if self.system == 'windows':
                # Check Windows admin privileges
                import ctypes
                return ctypes.windll.shell32.IsUserAnAdmin() != 0
            else:
                # Check Unix-like sudo/root
                return os.geteuid() == 0
        except:
            # Default to False if check fails
            return False
            
    def _run_command(self, command, shell=False):
        """Run system command and return result."""
        try:
            result = subprocess.run(
                command, 
                shell=shell, 
                check=True, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            return True, result.stdout
        except subprocess.CalledProcessError as e:
            return False, e.stderr
        except Exception as e:
            return False, str(e)
    
    def _get_service_commands(self):
        """Get appropriate commands based on OS."""
        if self.system == 'linux':
            # Check which init system is used
            if os.path.exists('/run/systemd/system'):
                # systemd
                return {
                    'status': ['systemctl', 'status', 'docker'],
                    'start': ['systemctl', 'start', 'docker'],
                    'stop': ['systemctl', 'stop', 'docker'],
                    'restart': ['systemctl', 'restart', 'docker'],
                    'enable': ['systemctl', 'enable', 'docker'],
                    'disable': ['systemctl', 'disable', 'docker'],
                    'socket_enable': ['systemctl', 'enable', 'docker.socket'],
                    'socket_disable': ['systemctl', 'disable', 'docker.socket'],
                    'socket_start': ['systemctl', 'start', 'docker.socket'],
                    'socket_stop': ['systemctl', 'stop', 'docker.socket'],
                    'socket_status': ['systemctl', 'status', 'docker.socket']
                }
            elif os.path.exists('/etc/init.d/docker'):
                # SysVinit
                return {
                    'status': ['service', 'docker', 'status'],
                    'start': ['service', 'docker', 'start'],
                    'stop': ['service', 'docker', 'stop'],
                    'restart': ['service', 'docker', 'restart'],
                    'enable': ['update-rc.d', 'docker', 'defaults'],
                    'disable': ['update-rc.d', 'docker', 'disable'],
                    # No direct socket management for SysVinit
                    'socket_status': ['echo', 'Socket management not supported with SysVinit'],
                    'socket_start': ['echo', 'Socket management not supported with SysVinit'],
                    'socket_stop': ['echo', 'Socket management not supported with SysVinit'],
                    'socket_enable': ['echo', 'Socket management not supported with SysVinit'],
                    'socket_disable': ['echo', 'Socket management not supported with SysVinit']
                }
            else:
                # Replit or other environment without standard systemd/SysVinit
                return {
                    'status': ['echo', 'Docker service not detected (NixOS or container environment)'],
                    'start': ['echo', 'Docker service not detected (NixOS or container environment)'],
                    'stop': ['echo', 'Docker service not detected (NixOS or container environment)'],
                    'restart': ['echo', 'Docker service not detected (NixOS or container environment)'],
                    'enable': ['echo', 'Docker service not detected (NixOS or container environment)'],
                    'disable': ['echo', 'Docker service not detected (NixOS or container environment)'],
                    'socket_status': ['echo', 'Docker socket not detected (NixOS or container environment)'],
                    'socket_start': ['echo', 'Docker socket not detected (NixOS or container environment)'],
                    'socket_stop': ['echo', 'Docker socket not detected (NixOS or container environment)'],
                    'socket_enable': ['echo', 'Docker socket not detected (NixOS or container environment)'],
                    'socket_disable': ['echo', 'Docker socket not detected (NixOS or container environment)']
                }
        elif self.system == 'darwin':  # macOS
            return {
                'status': ['launchctl', 'list', 'com.docker.docker'],
                'start': ['open', '-a', 'Docker'],
                'stop': ["osascript", "-e", 'quit app "Docker"'],
                'restart': ["osascript", "-e", 'quit app "Docker"', "&&", "open", "-a", "Docker"],
                # macOS uses launchd, Docker Desktop handles its own persistence
                'enable': ['echo', 'Use Docker Desktop preferences to enable auto-start'],
                'disable': ['echo', 'Use Docker Desktop preferences to disable auto-start'],
                # No separate socket management for macOS
                'socket_status': ['echo', 'Socket management not applicable on macOS'],
                'socket_start': ['echo', 'Socket management not applicable on macOS'],
                'socket_stop': ['echo', 'Socket management not applicable on macOS'],
                'socket_enable': ['echo', 'Socket management not applicable on macOS'],
                'socket_disable': ['echo', 'Socket management not applicable on macOS']
            }
        elif self.system == 'windows':
            # Windows Service Management
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
            
    def check_privileges(self):
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
    
    def get_status(self):
        """Get Docker service status."""
        print("Checking Docker service status...")
        if not self.check_privileges():
            print("Attempting to check status anyway...")
            
        commands = self._get_service_commands()
        success, output = self._run_command(commands['status'])
        
        if success:
            print("Docker service status:")
            print(output)
        else:
            print(f"Error checking Docker service status: {output}")
            
        return success
        
    def start_service(self):
        """Start Docker service."""
        print("Starting Docker service...")
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
            
        return success
        
    def stop_service(self):
        """Stop Docker service."""
        print("Stopping Docker service...")
        if not self.check_privileges():
            print("Attempting to stop service anyway...")
            
        commands = self._get_service_commands()
        success, output = self._run_command(commands['stop'])
        
        if success:
            print("✓ Docker service stopped successfully")
        else:
            print(f"Error stopping Docker service: {output}")
            
        return success
        
    def restart_service(self):
        """Restart Docker service."""
        print("Restarting Docker service...")
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
            
        return success
        
    def enable_service(self):
        """Enable Docker service to start at boot."""
        print("Enabling Docker service to start at boot...")
        if not self.check_privileges():
            print("Attempting to enable service anyway...")
            
        commands = self._get_service_commands()
        success, output = self._run_command(commands['enable'])
        
        if success:
            print("✓ Docker service enabled successfully")
        else:
            print(f"Error enabling Docker service: {output}")
            
        return success
        
    def disable_service(self):
        """Disable Docker service from starting at boot."""
        print("Disabling Docker service from starting at boot...")
        if not self.check_privileges():
            print("Attempting to disable service anyway...")
            
        commands = self._get_service_commands()
        success, output = self._run_command(commands['disable'])
        
        if success:
            print("✓ Docker service disabled successfully")
        else:
            print(f"Error disabling Docker service: {output}")
            
        return success
    
    def get_socket_status(self):
        """Get Docker socket status."""
        print("Checking Docker socket status...")
        if not self.check_privileges():
            print("Attempting to check socket status anyway...")
            
        commands = self._get_service_commands()
        success, output = self._run_command(commands['socket_status'])
        
        if success:
            print("Docker socket status:")
            print(output)
        else:
            print(f"Error checking Docker socket status: {output}")
            
        return success
    
    def start_socket(self):
        """Start Docker socket."""
        print("Starting Docker socket...")
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
            
        return success
    
    def stop_socket(self):
        """Stop Docker socket."""
        print("Stopping Docker socket...")
        if not self.check_privileges():
            print("Attempting to stop socket anyway...")
            
        commands = self._get_service_commands()
        success, output = self._run_command(commands['socket_stop'])
        
        if success:
            print("✓ Docker socket stopped successfully")
        else:
            print(f"Error stopping Docker socket: {output}")
            
        return success
    
    def enable_socket(self):
        """Enable Docker socket to start at boot."""
        print("Enabling Docker socket to start at boot...")
        if not self.check_privileges():
            print("Attempting to enable socket anyway...")
            
        commands = self._get_service_commands()
        success, output = self._run_command(commands['socket_enable'])
        
        if success:
            print("✓ Docker socket enabled successfully")
        else:
            print(f"Error enabling Docker socket: {output}")
            
        return success
    
    def disable_socket(self):
        """Disable Docker socket from starting at boot."""
        print("Disabling Docker socket from starting at boot...")
        if not self.check_privileges():
            print("Attempting to disable socket anyway...")
            
        commands = self._get_service_commands()
        success, output = self._run_command(commands['socket_disable'])
        
        if success:
            print("✓ Docker socket disabled successfully")
        else:
            print(f"Error disabling Docker socket: {output}")
            
        return success
    
    def list_containers(self):
        """List all Docker containers."""
        try:
            print("Connecting to Docker...")
            client = docker.from_env()
            containers = client.containers.list(all=True)
            
            if not containers:
                print("No containers found.")
                return True
            
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
            print(tabulate(table_data, headers=headers, tablefmt="pretty"))
            
            return True
        except docker.errors.DockerException as e:
            print(f"Error connecting to Docker: {e}")
            print("Make sure Docker service is running.")
            return False
        except Exception as e:
            print(f"Error listing containers: {e}")
            return False
    
    def check_docker_info(self):
        """Get Docker system info."""
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
            print(tabulate(basic_info, tablefmt="plain"))
            
            # Print storage driver info
            print("\n=== Storage Driver ===")
            driver_info = [
                ["Driver", info.get('Driver', 'Unknown')],
                ["Root Dir", info.get('DockerRootDir', 'Unknown')]
            ]
            print(tabulate(driver_info, tablefmt="plain"))
            
            # Print networking info
            print("\n=== Network ===")
            net_info = []
            for net_name, net_data in info.get('Plugins', {}).get('Network', {}).items():
                net_info.append([net_name, str(net_data)])
            print(tabulate(net_info, tablefmt="plain"))
            
            return True
        except docker.errors.DockerException as e:
            print(f"Error connecting to Docker: {e}")
            print("Make sure Docker service is running.")
            return False
        except Exception as e:
            print(f"Error getting Docker info: {e}")
            return False

def show_banner():
    """Display tool banner."""
    banner = r"""
    ____             __                __  ___                                 
   / __ \____  _____/ /_____  _____   /  |/  /___ _____  ____ _____ ____  _____
  / / / / __ \/ ___/ //_/ _ \/ ___/  / /|_/ / __ `/ __ \/ __ `/ __ `/ _ \/ ___/
 / /_/ / /_/ / /__/ ,< /  __/ /     / /  / / /_/ / / / / /_/ / /_/ /  __/ /    
/_____/\____/\___/_/|_|\___/_/     /_/  /_/\__,_/_/ /_/\__,_/\__, /\___/_/     
                                                             /____/             
 Service Manager v1.0 - Cross-platform Docker daemon control
    """
    print(banner)

def setup_argparse():
    """Set up command line argument parsing."""
    parser = argparse.ArgumentParser(
        description="Cross-platform Docker service management tool", 
        formatter_class=argparse.RawTextHelpFormatter
    )
    
    # Create subparsers for different command groups
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Service management commands
    service_parser = subparsers.add_parser('service', help='Docker service management')
    service_subparsers = service_parser.add_subparsers(dest='service_action', help='Service actions')
    
    # Service start
    service_start = service_subparsers.add_parser('start', help='Start Docker service')
    
    # Service stop
    service_stop = service_subparsers.add_parser('stop', help='Stop Docker service')
    
    # Service restart
    service_restart = service_subparsers.add_parser('restart', help='Restart Docker service')
    
    # Service status
    service_status = service_subparsers.add_parser('status', help='Show Docker service status')
    
    # Service enable
    service_enable = service_subparsers.add_parser('enable', help='Enable Docker service at boot')
    
    # Service disable
    service_disable = service_subparsers.add_parser('disable', help='Disable Docker service at boot')
    
    # Socket management commands
    socket_parser = subparsers.add_parser('socket', help='Docker socket management')
    socket_subparsers = socket_parser.add_subparsers(dest='socket_action', help='Socket actions')
    
    # Socket start
    socket_start = socket_subparsers.add_parser('start', help='Start Docker socket')
    
    # Socket stop
    socket_stop = socket_subparsers.add_parser('stop', help='Stop Docker socket')
    
    # Socket status
    socket_status = socket_subparsers.add_parser('status', help='Show Docker socket status')
    
    # Socket enable
    socket_enable = socket_subparsers.add_parser('enable', help='Enable Docker socket at boot')
    
    # Socket disable
    socket_disable = socket_subparsers.add_parser('disable', help='Disable Docker socket at boot')
    
    # Docker container commands
    container_parser = subparsers.add_parser('containers', help='List Docker containers')
    
    # Docker info command
    info_parser = subparsers.add_parser('info', help='Show Docker system information')
    
    # Version
    version_parser = subparsers.add_parser('version', help='Show Docker Manager version')
    
    return parser

def check_requirements():
    """Check if required dependencies are installed."""
    missing_deps = []
    
    # Check for docker-py
    try:
        import docker
    except ImportError:
        missing_deps.append("docker")
    
    # Check for tabulate
    try:
        import tabulate
    except ImportError:
        missing_deps.append("tabulate")
    
    if missing_deps:
        print("Missing required dependencies:")
        for dep in missing_deps:
            print(f"  - {dep}")
        print("\nInstall them using pip:")
        print(f"  pip install {' '.join(missing_deps)}")
        return False
    
    return True

def main():
    """Main entry point for the application."""
    # Check requirements first
    if not check_requirements():
        sys.exit(1)
    
    # Show banner
    show_banner()
    
    # Setup argument parser
    parser = setup_argparse()
    args = parser.parse_args()
    
    # Initialize the Docker service manager
    manager = DockerServiceManager()
    
    # Check if no command was provided
    if not hasattr(args, 'command') or args.command is None:
        parser.print_help()
        sys.exit(0)
    
    # Handle service commands
    if args.command == 'service':
        if not hasattr(args, 'service_action') or args.service_action is None:
            print("Error: Please specify a service action.")
            print("Available actions: start, stop, restart, status, enable, disable")
            sys.exit(1)
            
        if args.service_action == 'start':
            success = manager.start_service()
        elif args.service_action == 'stop':
            success = manager.stop_service()
        elif args.service_action == 'restart':
            success = manager.restart_service()
        elif args.service_action == 'status':
            success = manager.get_status()
        elif args.service_action == 'enable':
            success = manager.enable_service()
        elif args.service_action == 'disable':
            success = manager.disable_service()
    
    # Handle socket commands
    elif args.command == 'socket':
        if not hasattr(args, 'socket_action') or args.socket_action is None:
            print("Error: Please specify a socket action.")
            print("Available actions: start, stop, status, enable, disable")
            sys.exit(1)
            
        if args.socket_action == 'start':
            success = manager.start_socket()
        elif args.socket_action == 'stop':
            success = manager.stop_socket()
        elif args.socket_action == 'status':
            success = manager.get_socket_status()
        elif args.socket_action == 'enable':
            success = manager.enable_socket()
        elif args.socket_action == 'disable':
            success = manager.disable_socket()
    
    # Handle container listing
    elif args.command == 'containers':
        success = manager.list_containers()
    
    # Handle Docker info
    elif args.command == 'info':
        success = manager.check_docker_info()
    
    # Handle version
    elif args.command == 'version':
        print("Docker Service Manager v1.0")
        print("A cross-platform tool for managing Docker daemon services")
        print("Platform:", platform.system(), platform.release())
        success = True
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
