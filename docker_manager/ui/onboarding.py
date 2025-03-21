"""
Onboarding module for Docker Service Manager.

This module provides contextual help and guidance for new users
to help them learn how to use the Docker Service Manager.
"""

import os
import json
import time
from typing import Optional, List, Dict, Any

from ..utils.display import print_status, print_section


class OnboardingManager:
    """Handles onboarding for new users of Docker Service Manager."""

    CONFIG_DIR = os.path.expanduser("~/.docker_manager")
    CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")
    
    def __init__(self, demo_mode: bool = False):
        """Initialize the onboarding system.
        
        Args:
            demo_mode: Whether to use demo mode with simulated responses
        """
        self.demo_mode = demo_mode
        self.config = self._load_config()
        self.first_run = self.config.get("first_run", True)
        self.completed_topics = self.config.get("completed_topics", [])
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create default.
        
        Returns:
            Configuration dictionary
        """
        if os.path.exists(self.CONFIG_FILE):
            try:
                with open(self.CONFIG_FILE, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        
        # Default configuration
        return {
            "first_run": True,
            "completed_topics": [],
            "last_used": None
        }
    
    def _save_config(self) -> bool:
        """Save configuration to file.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure directory exists
            os.makedirs(self.CONFIG_DIR, exist_ok=True)
            
            # Update last used timestamp
            self.config["last_used"] = time.time()
            
            with open(self.CONFIG_FILE, 'w') as f:
                json.dump(self.config, f)
            return True
        except IOError:
            return False
    
    def mark_topic_completed(self, topic: str) -> None:
        """Mark a help topic as completed.
        
        Args:
            topic: Topic identifier
        """
        if topic not in self.completed_topics:
            self.completed_topics.append(topic)
            self.config["completed_topics"] = self.completed_topics
            self._save_config()
    
    def mark_first_run_complete(self) -> None:
        """Mark first run as complete."""
        self.first_run = False
        self.config["first_run"] = False
        self._save_config()
    
    def is_topic_completed(self, topic: str) -> bool:
        """Check if a help topic has been completed.
        
        Args:
            topic: Topic identifier
            
        Returns:
            True if the topic has been completed, False otherwise
        """
        return topic in self.completed_topics
        
    def is_first_time_in_section(self, section: str) -> bool:
        """Check if this is the first time a user has accessed a section.
        
        Args:
            section: Section identifier
            
        Returns:
            True if this is the first time, False otherwise
        """
        section_key = f"visited_{section}"
        visited = self.config.get("visited_sections", [])
        
        if section_key not in visited:
            visited.append(section_key)
            self.config["visited_sections"] = visited
            self._save_config()
            return True
            
        return False
        
    def show_first_time_section_help(self, section: str) -> bool:
        """Show help for a section the first time it's accessed.
        
        Args:
            section: Section identifier
            
        Returns:
            True if help was shown, False otherwise
        """
        if not self.is_first_time_in_section(section):
            return False
            
        section_help = {
            "service": (
                "Service Management",
                "This section allows you to control the Docker service (daemon).\n"
                "Start by checking the service status to see if Docker is running."
            ),
            "socket": (
                "Socket Management",
                "This section allows you to control the Docker socket.\n"
                "The socket is how applications communicate with Docker."
            ),
            "container": (
                "Container Management",
                "This section allows you to manage Docker containers.\n"
                "Try listing containers to see what's currently running."
            ),
            "templates": (
                "Environment Templates",
                "This section helps you create development environments.\n"
                "Start by listing available templates to see what's available."
            ),
            "info": (
                "System Information",
                "This section provides information about your Docker installation.\n"
                "Check Docker Info to see system-wide details."
            )
        }
        
        if section in section_help:
            title, message = section_help[section]
            print_section(f"Welcome to {title}")
            print(message)
            print("\nType '?' for more detailed help on this section.")
            print("Press Enter to continue...")
            input()
            return True
            
        return False
    
    def show_welcome(self) -> None:
        """Show welcome message for first-time users."""
        if not self.first_run:
            return
            
        print_section("Welcome to Docker Service Manager!")
        print("This appears to be your first time using Docker Service Manager.")
        print("Let's take a moment to get familiar with the tool:")
        print()
        print("- This tool helps manage Docker daemon services across different platforms")
        print("- You can start, stop, and check the status of Docker services")
        print("- You can manage containers and view their logs")
        print("- You can create and launch development environments using templates")
        print()
        print("Navigation tips:")
        print("- Type '?' at any menu to see contextual help for that section")
        print("- Type 'h' to browse all available help topics")
        print("- Use 'b' to go back to the previous menu")
        print("- Use 'q' from the main menu to exit the program")
        
        if self.demo_mode:
            print()
            print_section("Demo Mode Information")
            print("You're currently running in DEMO MODE:")
            print("- All Docker operations are simulated (no actual changes are made)")
            print("- Sample data is displayed for containers and system information")
            print("- This mode is useful for learning how the tool works without Docker installed")
            print("- To use with a real Docker installation, run without the --demo flag")
            print_status("Currently running in DEMO MODE - operations are simulated", "info", demo_mode=True)
        
        input("\nPress Enter to continue...")
        self.mark_first_run_complete()

    def show_topic(self, topic: str) -> None:
        """Show help for a specific topic.
        
        Args:
            topic: Topic identifier
        """
        topics = {
            "service": self._show_service_help,
            "socket": self._show_socket_help,
            "containers": self._show_containers_help,
            "templates": self._show_templates_help,
            "system": self._show_system_help,
            "privileges": self._show_privileges_help,
            "demo_mode": self._show_demo_mode_help
        }
        
        if topic in topics:
            topics[topic]()
            self.mark_topic_completed(topic)
        else:
            print_status(f"No help available for topic: {topic}", "error")
    
    def show_contextual_help(self, context: str) -> None:
        """Show contextual help based on user's current context.
        
        Args:
            context: Current context (menu, command, etc.)
        """
        # Map contexts to help topics
        context_map = {
            "main_menu": "main",
            "service_menu": "service",
            "socket_menu": "socket",
            "container_menu": "containers",
            "templates_menu": "templates",
            "system_menu": "system",
            "check_privileges": "privileges"
        }
        
        if context in context_map:
            self.show_topic(context_map[context])
    
    def _show_service_help(self) -> None:
        """Show help for Docker service management."""
        print_section("Docker Service Management")
        print("The Docker service (or daemon) is the background process that manages containers.")
        print()
        print("Available commands:")
        print("- status: Check if the Docker service is running")
        print("- start: Start the Docker service")
        print("- stop: Stop the Docker service")
        print("- restart: Restart the Docker service")
        print("- enable: Configure Docker to start automatically at boot")
        print("- disable: Prevent Docker from starting automatically at boot")
        print()
        print("Note: Some operations may require administrative privileges.")
        
        input("Press Enter to continue...")
    
    def _show_socket_help(self) -> None:
        """Show help for Docker socket management."""
        print_section("Docker Socket Management")
        print("The Docker socket is how applications communicate with the Docker daemon.")
        print()
        print("Available commands:")
        print("- status: Check if the Docker socket is available")
        print("- start: Start the Docker socket")
        print("- stop: Stop the Docker socket")
        print("- enable: Configure the socket to start automatically")
        print("- disable: Prevent the socket from starting automatically")
        print()
        print("Note: Socket management is primarily relevant on Linux systems.")
        
        input("Press Enter to continue...")
    
    def _show_containers_help(self) -> None:
        """Show help for container management."""
        print_section("Container Management")
        print("Containers are lightweight, portable application environments.")
        print()
        print("Available commands:")
        print("- list: Show all containers (running and stopped)")
        print("- logs: View logs for a specific container")
        print()
        print("Note: To manage individual containers (start, stop, etc.), use Docker CLI directly.")
        
        input("Press Enter to continue...")
    
    def _show_templates_help(self) -> None:
        """Show help for environment templates."""
        print_section("Environment Templates")
        print("Templates help you quickly set up development environments with predefined services.")
        print()
        print("Available commands:")
        print("- list: Show available environment templates")
        print("- create: Create an environment from a template")
        print("- launch: Create and start an environment from a template")
        print()
        print("Available templates:")
        print("- LAMP Stack: Linux, Apache, MySQL, PHP")
        print("- MEAN Stack: MongoDB, Express, Angular, Node.js")
        print("- WordPress: WordPress with MySQL database")
        
        input("Press Enter to continue...")
    
    def _show_system_help(self) -> None:
        """Show help for system information."""
        print_section("System Information")
        print("This section provides information about your Docker installation and system.")
        print()
        print("Available commands:")
        print("- info: Show Docker system information")
        print("- privileges: Check if you have administrative privileges")
        print("- health report: Generate a comprehensive system health report")
        print("- save report: Save the last generated health report to a file")
        
        input("Press Enter to continue...")
    
    def _show_privileges_help(self) -> None:
        """Show help for administrative privileges."""
        print_section("Administrative Privileges")
        print("Many Docker operations require administrative privileges.")
        print()
        print("On Linux: Use 'sudo' before commands or add your user to the 'docker' group")
        print("On Windows: Run the application as Administrator")
        print("On macOS: You may be prompted for your password")
        
        input("Press Enter to continue...")
    
    def _show_demo_mode_help(self) -> None:
        """Show help for demo mode."""
        print_section("Demo Mode")
        print("Demo mode allows you to explore Docker Service Manager without a Docker installation.")
        print()
        print("In demo mode:")
        print("- All operations are simulated")
        print("- No actual Docker commands are executed")
        print("- Sample data is displayed for containers and system information")
        print()
        print("To exit demo mode, restart the application without the --demo flag.")
        
        input("Press Enter to continue...")
        
    def _show_health_report_help(self) -> None:
        """Show help for the health report feature."""
        print_section("System Health Report")
        print("The Health Report provides a comprehensive overview of your system and Docker environment.")
        print()
        print("Health Report features:")
        print("- Real-time CPU, memory, and disk usage metrics")
        print("- Docker daemon status and performance")
        print("- Container resource utilization")
        print("- Visual charts for key performance indicators")
        print("- Actionable recommendations based on system state")
        print()
        print("You can generate a report at any time from the main menu or system information section.")
        print("Reports can be saved as JSON files for later reference or sharing with support teams.")
        
        input("Press Enter to continue...")
        
    def show_error_help(self, error_code: str) -> bool:
        """Show help for common errors.
        
        Args:
            error_code: Identifier for the error
            
        Returns:
            True if help was shown, False if no help available for this error
        """
        error_help = {
            "service_not_running": (
                "Docker Service Not Running",
                "The Docker daemon service isn't running. Try the following:\n\n"
                "1. Start the service with 'docker_service_manager.py service start'\n"
                "2. Check if Docker is installed correctly\n"
                "3. Verify you have sufficient permissions (try running with sudo)"
            ),
            "socket_not_available": (
                "Docker Socket Not Available",
                "The Docker socket is not accessible. This usually means:\n\n"
                "1. The Docker service is not running\n"
                "2. The socket has incorrect permissions\n"
                "3. You don't have permission to access the socket\n\n"
                "Try starting both the service and socket, or add your user to the 'docker' group."
            ),
            "permission_denied": (
                "Permission Denied",
                "You don't have sufficient permissions to perform this operation.\n\n"
                "On Linux: Use sudo or add your user to the 'docker' group\n"
                "On Windows: Run as Administrator\n"
                "On macOS: You may need to enter your password"
            ),
            "docker_not_installed": (
                "Docker Not Installed or Not Found",
                "Docker doesn't appear to be installed or can't be found in your PATH.\n\n"
                "1. Install Docker from https://docs.docker.com/get-docker/\n"
                "2. Ensure Docker is in your PATH environment variable\n"
                "3. You can use --demo mode to explore this tool without Docker"
            ),
            "container_not_found": (
                "Container Not Found",
                "The specified container ID or name couldn't be found.\n\n"
                "1. Check that the container exists with 'docker_service_manager.py containers'\n"
                "2. Verify you're using the correct container ID or name\n"
                "3. The container may have been removed or may not be running"
            ),
            "template_not_found": (
                "Template Not Found",
                "The specified environment template couldn't be found.\n\n"
                "Available templates are:\n"
                "- lamp: LAMP Stack (Linux, Apache, MySQL, PHP)\n"
                "- mean: MEAN Stack (MongoDB, Express, Angular, Node.js)\n"
                "- wordpress: WordPress development environment"
            )
        }
        
        if error_code in error_help:
            title, message = error_help[error_code]
            print_section(f"Error Help: {title}")
            print(message)
            print()
            input("Press Enter to continue...")
            return True
            
        return False
    
    def show_help_browser(self) -> None:
        """Show a browser for all available help topics."""
        while True:
            print_section("Help Topics")
            print("Available topics:")
            print("1 - Docker Service Management")
            print("2 - Docker Socket Management")
            print("3 - Container Management")
            print("4 - Environment Templates")
            print("5 - System Information")
            print("6 - Administrative Privileges")
            print("7 - Demo Mode")
            print("8 - System Health Report")
            print("0 - Return to previous menu")
            
            choice = input("Select a topic (0-8): ").strip()
            
            if choice == "0":
                break
            elif choice == "1":
                self._show_service_help()
            elif choice == "2":
                self._show_socket_help()
            elif choice == "3":
                self._show_containers_help()
            elif choice == "4":
                self._show_templates_help()
            elif choice == "5":
                self._show_system_help()
            elif choice == "6":
                self._show_privileges_help()
            elif choice == "7":
                self._show_demo_mode_help()
            elif choice == "8":
                self._show_health_report_help()
            else:
                print_status("Invalid selection", "error")
                
    def show_all_help_topics(self) -> None:
        """Show all available help topics in a browser."""
        self.show_help_browser()
        
    def maybe_show_suggestion(self, context: str, action: Optional[str]) -> tuple:
        """Show contextual suggestions based on user's actions.
        
        Args:
            context: Current context (menu, command, etc.)
            action: The action user performed (or None)
            
        Returns:
            Tuple of (suggestion_shown, suggestion_text)
        """
        # If action is None, no suggestion can be shown
        if action is None:
            return (False, "")
        # Define suggestions for common tasks
        suggestions = {
            # Service management suggestions
            "service_status": (
                not self.is_topic_completed("service"),
                "Tip: Docker service status shows if the daemon is running."
            ),
            "service_start": (
                not self.is_topic_completed("service"),
                "Tip: After starting the service, try 'status' to verify it's running."
            ),
            "service_stop": (
                not self.is_topic_completed("service"),
                "Tip: Stopping the service will disconnect all containers."
            ),
            "service_restart": (
                not self.is_topic_completed("service"),
                "Tip: Restarting is useful when Docker seems unresponsive."
            ),
            "service_enable": (
                not self.is_topic_completed("service"),
                "Tip: Enabling the service makes Docker start automatically at boot."
            ),
            "service_disable": (
                not self.is_topic_completed("service"),
                "Tip: Disabling prevents Docker from starting at boot."
            ),
            
            # Socket management suggestions
            "socket_status": (
                not self.is_topic_completed("socket"),
                "Tip: The Docker socket is how tools communicate with Docker."
            ),
            "socket_start": (
                not self.is_topic_completed("socket"),
                "Tip: Starting the socket allows Docker clients to connect."
            ),
            
            # Container management suggestions
            "container_list": (
                not self.is_topic_completed("containers"),
                "Tip: You can view logs for a specific container using the 'logs' command."
            ),
            "container_logs": (
                not self.is_topic_completed("containers"),
                "Tip: Container logs are helpful for troubleshooting issues."
            ),
            
            # Template suggestions
            "templates_list": (
                not self.is_topic_completed("templates"),
                "Tip: Templates help you quickly set up development environments."
            ),
            "templates_create": (
                not self.is_topic_completed("templates"),
                "Tip: Creating an environment generates all necessary configuration files."
            ),
            "templates_launch": (
                not self.is_topic_completed("templates"),
                "Tip: Launching starts all containers defined in the template."
            ),
            
            # System information suggestions
            "info_docker": (
                not self.is_topic_completed("system"),
                "Tip: Docker info shows system-wide information about your Docker setup."
            ),
            "check_privileges": (
                not self.is_topic_completed("privileges"),
                "Tip: Many Docker operations require administrative privileges."
            ),
            "health_report": (
                not self.is_topic_completed("system"),
                "Tip: Health reports provide detailed performance metrics and resource usage."
            ),
            "save_report": (
                not self.is_topic_completed("system"),
                "Tip: Save reports to track system health over time or for troubleshooting."
            )
        }
        
        # Create context_action key
        context_action = f"{context}_{action}"
        
        if context_action in suggestions:
            should_show, message = suggestions[context_action]
            if should_show:
                print_status(message, "info", demo_mode=self.demo_mode)
                return (True, message)
                
        return (False, "")


# Helper function for easy access
def get_onboarding(demo_mode: bool = False) -> OnboardingManager:
    """Get an OnboardingManager instance.
    
    Args:
        demo_mode: Whether to use demo mode with simulated responses
        
    Returns:
        OnboardingManager instance
    """
    return OnboardingManager(demo_mode=demo_mode)