"""
Command-line interface for Docker service manager.
"""
import argparse
import sys
import os
from typing import List, Dict, Optional, Any

from ..core.service_manager import DockerServiceManager
from ..core.health_report import HealthReport
from ..templates.environment_templates import TemplateManager
from ..utils.display import show_banner
from .. import __version__

def setup_argparse() -> argparse.ArgumentParser:
    """Set up command line argument parsing.
    
    Returns:
        Configured ArgumentParser instance
    """
    parser = argparse.ArgumentParser(description="Cross-platform Docker service management tool")
    
    # Global arguments that apply to all commands
    parser.add_argument('--demo', action='store_true', help='Enable demo mode with simulated Docker responses')
    parser.add_argument('--interactive', '-i', action='store_true', help='Run in interactive mode with menu interface')
    parser.add_argument('--tui', action='store_true', help='Run in Terminal User Interface (TUI) mode with advanced visuals')
    parser.add_argument('--version', '-v', action='store_true', help='Show Docker Manager version and exit')
    parser.add_argument('--emoji', '-e', action='store_true', help='Enable emoji indicators in output')
    
    # Create subparsers for commands
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Service management subcommand
    service_parser = subparsers.add_parser('service', help='Docker service management')
    service_subparsers = service_parser.add_subparsers(dest='service_command', help='Service Commands')
    
    # Service status command
    status_parser = service_subparsers.add_parser('status', help='Check Docker service status')
    
    # Service start command
    start_parser = service_subparsers.add_parser('start', help='Start Docker service')
    
    # Service stop command
    stop_parser = service_subparsers.add_parser('stop', help='Stop Docker service')
    
    # Service restart command
    restart_parser = service_subparsers.add_parser('restart', help='Restart Docker service')
    
    # Service enable command
    enable_parser = service_subparsers.add_parser('enable', help='Enable Docker service to start at boot')
    
    # Service disable command
    disable_parser = service_subparsers.add_parser('disable', help='Disable Docker service from starting at boot')
    
    # Socket management subcommand
    socket_parser = subparsers.add_parser('socket', help='Docker socket management')
    socket_subparsers = socket_parser.add_subparsers(dest='socket_command', help='Socket Commands')
    
    # Socket status command
    socket_status_parser = socket_subparsers.add_parser('status', help='Check Docker socket status')
    
    # Socket start command
    socket_start_parser = socket_subparsers.add_parser('start', help='Start Docker socket')
    
    # Socket stop command
    socket_stop_parser = socket_subparsers.add_parser('stop', help='Stop Docker socket')
    
    # Socket enable command
    socket_enable_parser = socket_subparsers.add_parser('enable', help='Enable Docker socket to start at boot')
    
    # Socket disable command
    socket_disable_parser = socket_subparsers.add_parser('disable', help='Disable Docker socket from starting at boot')
    
    # Container management subcommand
    containers_parser = subparsers.add_parser('containers', help='List Docker containers')
    
    # Container logs subcommand
    logs_parser = subparsers.add_parser('logs', help='View container logs')
    logs_parser.add_argument('container_id', help='Container ID or name')
    logs_parser.add_argument('--tail', '-n', type=int, default=100, help='Number of lines to show from end of logs (default: 100)')
    logs_parser.add_argument('--follow', '-f', action='store_true', help='Follow log output (similar to tail -f)')
    
    # System information subcommand
    info_parser = subparsers.add_parser('info', help='Show Docker system information')
    
    # Health report subcommand
    health_parser = subparsers.add_parser('health', help='Generate system health report with visual metrics')
    
    # Version command
    version_parser = subparsers.add_parser('version', help='Show Docker Manager version')
    
    # Template commands
    template_parser = subparsers.add_parser('template', help='Development environment templates')
    template_subparsers = template_parser.add_subparsers(dest='template_command', help='Template commands')
    
    # List templates
    list_templates_parser = template_subparsers.add_parser('list', help='List available templates')
    
    # Create environment from template
    create_template_parser = template_subparsers.add_parser('create', help='Create environment from template')
    create_template_parser.add_argument('template_id', help='Template ID (e.g., lamp, mean, wordpress)')
    create_template_parser.add_argument('--directory', '-d', default='.', help='Target directory (default: current directory)')
    
    # Launch environment
    launch_template_parser = template_subparsers.add_parser('launch', help='Launch environment from template')
    launch_template_parser.add_argument('template_id', help='Template ID (e.g., lamp, mean, wordpress)')
    launch_template_parser.add_argument('--directory', '-d', default='.', help='Environment directory (default: current directory)')
    
    return parser

def process_args(args: argparse.Namespace) -> int:
    """Process command line arguments and execute requested commands.
    
    Args:
        args: Parsed command-line arguments
        
    Returns:
        Exit code (0 for success, non-zero for error)
    """
    # If version flag is set, show version and exit
    if args.version:
        print(f"Docker Service Manager v{__version__}")
        return 0
    
    # If TUI mode is enabled, start Terminal User Interface
    if args.tui:
        from .tui.main_simple import run_simple_tui
        run_simple_tui(demo_mode=args.demo)
        return 0
        
    # If interactive mode is enabled, start interactive console
    if args.interactive:
        from .interactive import InteractiveConsole
        console = InteractiveConsole(demo_mode=args.demo)
        console.run()
        return 0
    
    # Create service manager instance
    manager = DockerServiceManager(demo_mode=args.demo)
    
    # Handle commands
    if args.command == 'service':
        if args.service_command == 'status':
            success = manager.get_status()
        elif args.service_command == 'start':
            success = manager.start_service()
        elif args.service_command == 'stop':
            success = manager.stop_service()
        elif args.service_command == 'restart':
            success = manager.restart_service()
        elif args.service_command == 'enable':
            success = manager.enable_service()
        elif args.service_command == 'disable':
            success = manager.disable_service()
        else:
            print("Error: Please specify a service command")
            print("Run 'docker_service_manager.py service -h' for help")
            return 1
    
    elif args.command == 'socket':
        if args.socket_command == 'status':
            success = manager.get_socket_status()
        elif args.socket_command == 'start':
            success = manager.start_socket()
        elif args.socket_command == 'stop':
            success = manager.stop_socket()
        elif args.socket_command == 'enable':
            success = manager.enable_socket()
        elif args.socket_command == 'disable':
            success = manager.disable_socket()
        else:
            print("Error: Please specify a socket command")
            print("Run 'docker_service_manager.py socket -h' for help")
            return 1
    
    elif args.command == 'containers':
        success = manager.list_containers()
    
    elif args.command == 'logs':
        from ..core.container_logs import ContainerLogs
        logs_handler = ContainerLogs(demo_mode=args.demo)
        success = logs_handler.get_container_logs(
            container_id=args.container_id,
            tail=args.tail,
            follow=args.follow
        )
    
    elif args.command == 'info':
        success = manager.check_docker_info()
    
    elif args.command == 'health':
        health_reporter = HealthReport(demo_mode=args.demo)
        success = health_reporter.generate_report()
    
    elif args.command == 'template':
        # Create template manager instance
        template_manager = TemplateManager(demo_mode=args.demo)
        
        if args.template_command == 'list':
            success = template_manager.list_templates()
        elif args.template_command == 'create':
            success = template_manager.create_environment(
                template_id=args.template_id,
                target_dir=args.directory
            )
            if success:
                print(f"Environment created successfully in {args.directory}")
                print(f"To launch the environment, run:")
                print(f"  cd {args.directory} && docker-compose up -d")
        elif args.template_command == 'launch':
            success = template_manager.launch_environment(
                template_id=args.template_id,
                target_dir=args.directory
            )
        else:
            print("Error: Please specify a template command")
            print("Run 'docker_service_manager.py template -h' for help")
            return 1
    
    elif args.command == 'version':
        print(f"Docker Service Manager v{__version__}")
        success = True
    
    else:
        # No command specified, show help
        show_banner()
        print("\nError: No command specified")
        print("Run 'docker_service_manager.py -h' for help")
        print("Use --interactive for menu interface or --tui for graphical terminal interface")
        return 1
    
    return 0 if success else 1