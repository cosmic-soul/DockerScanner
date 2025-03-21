"""
Interactive console UI for Docker service manager.
"""
import os
import sys
import time
from typing import List, Dict, Callable, Any, Optional

from ..core.service_manager import DockerServiceManager
from ..core.health_report import HealthReport
from ..templates.environment_templates import TemplateManager
from ..utils.display import COLORS, get_terminal_size, show_banner, print_status, print_section
from .onboarding import OnboardingManager

class InteractiveConsole:
    """Interactive console interface for Docker service management."""
    
    def __init__(self, demo_mode: bool = False):
        """Initialize interactive console.
        
        Args:
            demo_mode: Whether to use demo mode for Docker operations
        """
        self.manager = DockerServiceManager(demo_mode=demo_mode)
        self.template_manager = TemplateManager(demo_mode=demo_mode)
        self.onboarding = OnboardingManager(demo_mode=demo_mode)
        self.demo_mode = demo_mode
        self.running = True
        self.current_menu = "main"
        self.menus = self._create_menus()

    def _create_menus(self) -> Dict[str, Dict[str, Any]]:
        """Create menu structure with options and actions.
        
        Returns:
            Dictionary of menus with their options and associated actions
        """
        return {
            "main": {
                "title": "Main Menu",
                "options": [
                    {"key": "1", "desc": "Service Management", "action": lambda: self._change_menu("service")},
                    {"key": "2", "desc": "Socket Management", "action": lambda: self._change_menu("socket")},
                    {"key": "3", "desc": "Container Management", "action": lambda: self._change_menu("container")},
                    {"key": "4", "desc": "Templates", "action": lambda: self._change_menu("templates")},
                    {"key": "5", "desc": "System Information", "action": lambda: self._change_menu("info")},
                    {"key": "6", "desc": "Generate Health Report", "action": self._generate_health_report},
                    {"key": "q", "desc": "Quit", "action": self._quit}
                ]
            },
            "service": {
                "title": "Service Management",
                "options": [
                    {"key": "1", "desc": "Check Service Status", "action": self._check_service_status},
                    {"key": "2", "desc": "Start Service", "action": self._start_service},
                    {"key": "3", "desc": "Stop Service", "action": self._stop_service},
                    {"key": "4", "desc": "Restart Service", "action": self._restart_service},
                    {"key": "5", "desc": "Enable Service at Boot", "action": self._enable_service},
                    {"key": "6", "desc": "Disable Service at Boot", "action": self._disable_service},
                    {"key": "b", "desc": "Back to Main Menu", "action": lambda: self._change_menu("main")}
                ]
            },
            "socket": {
                "title": "Socket Management",
                "options": [
                    {"key": "1", "desc": "Check Socket Status", "action": self._check_socket_status},
                    {"key": "2", "desc": "Start Socket", "action": self._start_socket},
                    {"key": "3", "desc": "Stop Socket", "action": self._stop_socket},
                    {"key": "4", "desc": "Enable Socket at Boot", "action": self._enable_socket},
                    {"key": "5", "desc": "Disable Socket at Boot", "action": self._disable_socket},
                    {"key": "b", "desc": "Back to Main Menu", "action": lambda: self._change_menu("main")}
                ]
            },
            "container": {
                "title": "Container Management",
                "options": [
                    {"key": "1", "desc": "List Containers", "action": self._list_containers},
                    {"key": "2", "desc": "View Container Logs", "action": self._view_container_logs},
                    {"key": "b", "desc": "Back to Main Menu", "action": lambda: self._change_menu("main")}
                ]
            },
            "info": {
                "title": "System Information",
                "options": [
                    {"key": "1", "desc": "Show Docker Info", "action": self._show_docker_info},
                    {"key": "2", "desc": "Check Admin Privileges", "action": self._check_privileges},
                    {"key": "3", "desc": "Generate Health Report", "action": self._generate_health_report},
                    {"key": "4", "desc": "Save Health Report", "action": self._save_health_report},
                    {"key": "b", "desc": "Back to Main Menu", "action": lambda: self._change_menu("main")}
                ]
            },
            "templates": {
                "title": "Development Templates",
                "options": [
                    {"key": "1", "desc": "List Available Templates", "action": self._list_templates},
                    {"key": "2", "desc": "Create Environment", "action": self._create_environment},
                    {"key": "3", "desc": "Launch Environment", "action": self._launch_environment},
                    {"key": "b", "desc": "Back to Main Menu", "action": lambda: self._change_menu("main")}
                ]
            }
        }
        
    def _clear_screen(self) -> None:
        """Clear the terminal screen."""
        os.system('cls' if os.name == 'nt' else 'clear')
        
    def _change_menu(self, menu_name: str) -> None:
        """Change to a different menu.
        
        Args:
            menu_name: Name of the menu to switch to
        """
        if menu_name in self.menus:
            self.current_menu = menu_name
            
            # Show first-time section help for this menu
            self.onboarding.show_first_time_section_help(menu_name)
        else:
            print(f"Error: Menu '{menu_name}' not found")
            input("Press Enter to continue...")
            
    def _display_menu(self) -> None:
        """Display the current menu with options."""
        self._clear_screen()
        show_banner()
        
        # Display demo mode indicator if enabled
        if self.demo_mode:
            print(f"\n{COLORS['YELLOW']}[DEMO MODE]{COLORS['RESET']} - Operations are simulated")
            
        menu = self.menus[self.current_menu]
        print_section(menu["title"])
        
        # Display options
        for option in menu["options"]:
            print(f"{COLORS['CYAN']}{option['key']}{COLORS['RESET']} - {option['desc']}")
            
        # Add back option if not in main menu
        if self.current_menu != "main":
            print(f"{COLORS['CYAN']}b{COLORS['RESET']} - Back to Main Menu")
            
        # Add help indicators at the bottom
        print(f"\n{COLORS['CYAN']}?{COLORS['RESET']} - Show help for this menu")
        print(f"{COLORS['CYAN']}h{COLORS['RESET']} - Browse all help topics")
            
    def _get_input(self) -> str:
        """Get user input for menu selection.
        
        Returns:
            User's selection
        """
        valid_keys = [option["key"] for option in self.menus[self.current_menu]["options"]]
        
        # Add help keys
        valid_keys.extend(['?', 'h'])
        
        # Add back option if not in main menu
        if self.current_menu != "main":
            valid_keys.append('b')
        
        while True:
            choice = input(f"\n{COLORS['BOLD']}Select an option (? for help):{COLORS['RESET']} ").lower()
            
            # Handle help commands
            if choice == '?':
                self.onboarding.show_contextual_help(self.current_menu)
                self._display_menu()
                continue
            elif choice == 'h':
                self.onboarding.show_all_help_topics()
                self._display_menu()
                continue
                
            if choice in valid_keys:
                return choice
                
            print(f"{COLORS['RED']}Invalid option. Please try again.{COLORS['RESET']}")
            
    def _process_action(self, choice: str) -> None:
        """Process the selected menu action.
        
        Args:
            choice: User's menu selection
        """
        # Handle help commands
        if choice == '?':
            self.onboarding.show_contextual_help(self.current_menu)
            return
            
        if choice == 'h':
            self.onboarding.show_all_help_topics()
            return
            
        # Handle back command
        if choice == 'b' and self.current_menu != "main":
            self.current_menu = "main"
            return
        
        # Handle regular menu options
        for option in self.menus[self.current_menu]["options"]:
            if option["key"] == choice:
                option["action"]()
                break
                
    def _quit(self) -> None:
        """Quit the interactive console."""
        self.running = False
        print("\nThank you for using Docker Service Manager!")
        
    def _handle_action_result(self, success: bool, action_name: str, error_code: Optional[str] = None) -> None:
        """Handle the result of an action, showing appropriate messages.
        
        Args:
            success: Whether the action was successful
            action_name: Name of the action performed
            error_code: Optional error code for showing contextual help
        """
        if success:
            print_status(f"{action_name} completed successfully", "ok", demo_mode=self.demo_mode)
        else:
            print_status(f"{action_name} failed", "error", demo_mode=self.demo_mode)
            
            # Show contextual error help if an error code is provided
            if error_code:
                self.onboarding.show_error_help(error_code)
            
        input("\nPress Enter to continue...")
        
    # Service management actions
    def _check_service_status(self) -> None:
        """Check Docker service status."""
        print_section("Docker Service Status")
        success, error_code = self.manager.get_status()
        
        # Track usage for onboarding system
        self.onboarding.maybe_show_suggestion("service", "status")
        
        # Show error help if there's an error
        if not success and error_code:
            self.onboarding.show_error_help(error_code)
        
        input("\nPress Enter to continue...")
        
    def _start_service(self) -> None:
        """Start Docker service."""
        print_section("Starting Docker Service")
        success = self.manager.start_service()
        input("\nPress Enter to continue...")
        
    def _stop_service(self) -> None:
        """Stop Docker service."""
        print_section("Stopping Docker Service")
        success = self.manager.stop_service()
        input("\nPress Enter to continue...")
        
    def _restart_service(self) -> None:
        """Restart Docker service."""
        print_section("Restarting Docker Service")
        success = self.manager.restart_service()
        input("\nPress Enter to continue...")
        
    def _enable_service(self) -> None:
        """Enable Docker service at boot."""
        print_section("Enabling Docker Service")
        success = self.manager.enable_service()
        input("\nPress Enter to continue...")
        
    def _disable_service(self) -> None:
        """Disable Docker service at boot."""
        print_section("Disabling Docker Service")
        success = self.manager.disable_service()
        input("\nPress Enter to continue...")
        
    # Socket management actions
    def _check_socket_status(self) -> None:
        """Check Docker socket status."""
        print_section("Docker Socket Status")
        success, error_code = self.manager.get_socket_status()
        
        # Track usage for onboarding system
        self.onboarding.maybe_show_suggestion("socket", "status")
        
        # Show error help if there's an error
        if not success and error_code:
            self.onboarding.show_error_help(error_code)
            
        input("\nPress Enter to continue...")
        
    def _start_socket(self) -> None:
        """Start Docker socket."""
        print_section("Starting Docker Socket")
        success = self.manager.start_socket()
        input("\nPress Enter to continue...")
        
    def _stop_socket(self) -> None:
        """Stop Docker socket."""
        print_section("Stopping Docker Socket")
        success = self.manager.stop_socket()
        input("\nPress Enter to continue...")
        
    def _enable_socket(self) -> None:
        """Enable Docker socket at boot."""
        print_section("Enabling Docker Socket")
        success = self.manager.enable_socket()
        input("\nPress Enter to continue...")
        
    def _disable_socket(self) -> None:
        """Disable Docker socket at boot."""
        print_section("Disabling Docker Socket")
        success = self.manager.disable_socket()
        input("\nPress Enter to continue...")
        
    # Container management actions
    def _list_containers(self) -> None:
        """List Docker containers."""
        print_section("Docker Containers")
        success, error_code = self.manager.list_containers()
        
        # Track usage for onboarding system
        self.onboarding.maybe_show_suggestion("container", "list")
        
        # Show error help if there's an error
        if not success and error_code:
            self.onboarding.show_error_help(error_code)
            
        input("\nPress Enter to continue...")
        
    def _view_container_logs(self) -> None:
        """View logs for a specific container."""
        from ..core.container_logs import ContainerLogs
        
        print_section("View Container Logs")
        
        # Ask for container ID
        container_id = input("Enter container ID or name: ")
        if not container_id:
            print("No container ID provided. Returning to menu.")
            input("\nPress Enter to continue...")
            return
            
        # Ask for number of lines to show
        tail_input = input("Number of lines to show (default: 100): ")
        tail = 100  # Default
        if tail_input:
            try:
                tail = int(tail_input)
            except ValueError:
                print("Invalid number. Using default (100 lines).")
                
        # Ask whether to follow logs
        follow_input = input("Follow logs? (y/N): ").lower()
        follow = follow_input == 'y'
        
        # Get container logs
        logs_handler = ContainerLogs(demo_mode=self.demo_mode)
        print("\nFetching logs...\n")
        success = logs_handler.get_container_logs(
            container_id=container_id,
            tail=tail,
            follow=follow
        )
        
        input("\nPress Enter to continue...")
        
    # System information actions
    def _show_docker_info(self) -> None:
        """Show Docker system information."""
        print_section("Docker System Information")
        success, error_code = self.manager.check_docker_info()
        
        # Track usage for onboarding system
        self.onboarding.maybe_show_suggestion("info", "docker")
        
        # Show error help if there's an error
        if not success and error_code:
            self.onboarding.show_error_help(error_code)
            
        input("\nPress Enter to continue...")
        
    def _check_privileges(self) -> None:
        """Check administrative privileges."""
        print_section("Administrative Privileges")
        success = self.manager.check_privileges()
        input("\nPress Enter to continue...")
        
    # Template management actions
    def _list_templates(self) -> None:
        """List available environment templates."""
        print_section("Available Templates")
        success = self.template_manager.list_templates()
        input("\nPress Enter to continue...")
        
    def _create_environment(self) -> None:
        """Create an environment from a template."""
        print_section("Create Environment")
        
        # List available templates
        print("Available templates:\n")
        self.template_manager.list_templates()
        
        # Ask for template ID
        template_id = input("\nEnter template ID (e.g., lamp, mean, wordpress): ")
        if not template_id:
            print("No template ID provided. Returning to menu.")
            input("\nPress Enter to continue...")
            return
            
        # Ask for target directory
        target_dir = input("Enter target directory (default: current directory): ")
        if not target_dir:
            target_dir = os.getcwd()
            
        # Create environment
        print(f"\nCreating {template_id} environment in {target_dir}...")
        success = self.template_manager.create_environment(template_id, target_dir)
        
        if success:
            print_status(f"Environment created successfully in {target_dir}", "ok", demo_mode=self.demo_mode)
            print(f"\nTo launch the environment, run:\n  cd {target_dir} && docker-compose up -d")
        else:
            print_status("Failed to create environment", "error", demo_mode=self.demo_mode)
            
        input("\nPress Enter to continue...")
        
    def _launch_environment(self) -> None:
        """Launch an environment from a template."""
        print_section("Launch Environment")
        
        # List available templates
        print("Available templates:\n")
        self.template_manager.list_templates()
        
        # Ask for template ID
        template_id = input("\nEnter template ID (e.g., lamp, mean, wordpress): ")
        if not template_id:
            print("No template ID provided. Returning to menu.")
            input("\nPress Enter to continue...")
            return
            
        # Ask for target directory
        target_dir = input("Enter environment directory (default: current directory): ")
        if not target_dir:
            target_dir = os.getcwd()
            
        # Launch environment
        print(f"\nLaunching {template_id} environment from {target_dir}...")
        success = self.template_manager.launch_environment(template_id, target_dir)
        
        if success:
            print_status("Environment launched successfully", "ok", demo_mode=self.demo_mode)
        else:
            print_status("Failed to launch environment", "error", demo_mode=self.demo_mode)
            
        input("\nPress Enter to continue...")
        
    # Health report actions
    def _generate_health_report(self) -> None:
        """Generate and display a comprehensive system health report."""
        print_section("Docker System Health Report")
        
        # Initialize health report
        health_report = HealthReport(demo_mode=self.demo_mode)
        
        # Generate and display the report
        print("Generating comprehensive system health report...")
        print("This may take a few seconds...")
        print()
        
        # Track usage for onboarding system
        self.onboarding.maybe_show_suggestion("info", "health_report")
        
        # Generate the report - this handles displaying as well
        success = health_report.generate_report()
        
        # Store report instance for potential saving
        self._last_health_report = health_report
        
        input("\nPress Enter to continue...")
        
    def _save_health_report(self) -> None:
        """Save the last generated health report to a file."""
        print_section("Save Health Report")
        
        # Check if a report has been generated
        if not hasattr(self, '_last_health_report'):
            print("No health report has been generated yet.")
            print("Please generate a health report first.")
            input("\nPress Enter to continue...")
            return
            
        # Ask for filename
        default_filename = f"docker_health_report_{time.strftime('%Y%m%d_%H%M%S')}.json"
        filename = input(f"Enter filename (default: {default_filename}): ")
        if not filename:
            filename = default_filename
        
        # Save the report
        print(f"\nSaving health report to {filename}...")
        saved_file = self._last_health_report.save_report(filename)
        
        if saved_file:
            print_status(f"Health report saved to {saved_file}", "ok", demo_mode=self.demo_mode)
        else:
            print_status("Failed to save health report", "error", demo_mode=self.demo_mode)
            
        input("\nPress Enter to continue...")
    
    def run(self) -> None:
        """Main loop for interactive console."""
        # Show welcome message for first-time users
        self.onboarding.show_welcome()
        
        # First-time help for main menu if applicable
        self.onboarding.show_first_time_section_help("main")
        
        while self.running:
            self._display_menu()
            choice = self._get_input()
            
            # Skip suggestions for navigation actions
            if choice not in ['q', 'b', '?', 'h']:
                # Extract the action name from the menu option
                action = None
                for option in self.menus[self.current_menu]["options"]:
                    if option["key"] == choice:
                        # Convert "Check Service Status" to "check_service_status"
                        action = option["desc"].lower().replace(" ", "_")
                        
                        # Mark topic as viewed if we're showing help for it
                        if self.current_menu == "service":
                            self.onboarding.mark_topic_completed("service")
                        elif self.current_menu == "socket":
                            self.onboarding.mark_topic_completed("socket")
                        elif self.current_menu == "container":
                            self.onboarding.mark_topic_completed("containers")
                        elif self.current_menu == "templates":
                            self.onboarding.mark_topic_completed("templates")
                        elif self.current_menu == "info":
                            self.onboarding.mark_topic_completed("system")
                        
                        break
                        
                # Only show suggestions for actual actions (not navigation)
                if action:
                    self.onboarding.maybe_show_suggestion(self.current_menu, action)
            
            # Process the selected action
            self._process_action(choice)