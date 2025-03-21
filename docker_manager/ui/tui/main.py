"""
Main Terminal User Interface for Docker Service Manager.

This module provides a TUI using the py-cui library for
a more interactive and user-friendly interface.
"""

import py_cui
import os
import sys
import time
import threading
from typing import Dict, List, Any, Optional, Callable

from docker_manager.core.service_manager import DockerServiceManager
from docker_manager.templates.environment_templates import TemplateManager
from docker_manager.utils.display import print_status


class DockerTUI:
    """Terminal User Interface for Docker Service Manager."""

    def __init__(self, demo_mode: bool = False):
        """Initialize the TUI.
        
        Args:
            demo_mode: Whether to use demo mode with simulated responses
        """
        self.demo_mode = demo_mode
        self.service_manager = DockerServiceManager(demo_mode=demo_mode)
        self.template_manager = TemplateManager(demo_mode=demo_mode)
        
        # Create the CUI object
        self.root = py_cui.PyCUI(9, 12)  # 9 rows, 12 columns
        self.root.set_title("Docker Service Manager")
        self.root.toggle_unicode_borders()
        
        # Status variables
        self.docker_running = False
        self.docker_enabled = False
        self.socket_running = False
        self.socket_enabled = False
        self.container_count = 0
        self.running_containers = 0
        
        # Set up widgets
        self._create_widgets()
        self._set_keybindings()
        
        # Initial status check
        self.check_status()

    def _create_widgets(self):
        """Create widgets for the TUI layout."""
        # Status panel at the top
        self.status_panel = self.root.add_block_label(
            "Docker Status: Checking...",
            0, 0, row_span=1, column_span=12
        )
        self.status_panel.set_color(py_cui.WHITE_ON_BLACK)
        
        # Service control buttons
        self.service_buttons = self.root.add_button_menu(
            "Service Controls",
            1, 0, row_span=2, column_span=6
        )
        self.service_buttons.add_item("Start Service", self._start_service)
        self.service_buttons.add_item("Stop Service", self._stop_service)
        self.service_buttons.add_item("Restart Service", self._restart_service)
        self.service_buttons.add_item("Enable at Boot", self._enable_service)
        self.service_buttons.add_item("Disable at Boot", self._disable_service)
        
        # Socket control buttons
        self.socket_buttons = self.root.add_button_menu(
            "Socket Controls",
            1, 6, row_span=2, column_span=6
        )
        self.socket_buttons.add_item("Start Socket", self._start_socket)
        self.socket_buttons.add_item("Stop Socket", self._stop_socket)
        self.socket_buttons.add_item("Enable Socket at Boot", self._enable_socket)
        self.socket_buttons.add_item("Disable Socket at Boot", self._disable_socket)
        
        # Container list
        self.container_list = self.root.add_scroll_menu(
            "Containers",
            3, 0, row_span=4, column_span=12
        )
        self.container_list.add_item_list([
            "Loading containers...",
        ])
        self.container_list.add_key_command(py_cui.keys.KEY_ENTER, self._view_container_logs)
        
        # Templates panel
        self.templates_menu = self.root.add_button_menu(
            "Environment Templates",
            7, 0, row_span=2, column_span=6
        )
        self.templates_menu.add_item("List Templates", self._list_templates)
        self.templates_menu.add_item("Create Environment", self._create_environment)
        self.templates_menu.add_item("Launch Environment", self._launch_environment)
        
        # System info panel
        self.system_buttons = self.root.add_button_menu(
            "System Controls",
            7, 6, row_span=2, column_span=6
        )
        self.system_buttons.add_item("Docker Info", self._show_docker_info)
        self.system_buttons.add_item("Check Privileges", self._check_privileges)
        self.system_buttons.add_item("Refresh Status", self.check_status)
        self.system_buttons.add_item("Quit", self._quit)

    def _set_keybindings(self):
        """Set global key bindings."""
        self.root.add_key_command(py_cui.keys.KEY_Q_LOWER, self._quit)
        self.root.add_key_command(py_cui.keys.KEY_R_LOWER, self.check_status)

    def check_status(self):
        """Check Docker status and update UI."""
        self.status_panel.set_title("Docker Status: Checking...")
        
        # Start checking in a separate thread to avoid blocking UI
        threading.Thread(target=self._check_status_thread, daemon=True).start()

    def _check_status_thread(self):
        """Check status in a background thread."""
        try:
            # Get Docker service status
            self.docker_running = self.service_manager.get_status()
            self.docker_enabled = True  # In real mode, this would be checked
            
            # Get Docker socket status
            self.socket_running = self.service_manager.get_socket_status()
            self.socket_enabled = True  # In real mode, this would be checked
            
            # Update container list
            self._update_container_list()
            
            # Update status panel
            self._update_status_panel()
        except Exception as e:
            self.show_message(f"Error checking status: {str(e)}")

    def _update_status_panel(self):
        """Update the status panel with current information."""
        if self.docker_running:
            docker_status = "Running ✓"
            docker_color = py_cui.GREEN_ON_BLACK
        else:
            docker_status = "Stopped ✗"
            docker_color = py_cui.RED_ON_BLACK
            
        if self.socket_running:
            socket_status = "Available ✓"
            socket_color = py_cui.GREEN_ON_BLACK
        else:
            socket_status = "Unavailable ✗"
            socket_color = py_cui.RED_ON_BLACK
            
        # Update the status panel
        status_text = f"Docker Service: {docker_status} | Socket: {socket_status}"
        if self.demo_mode:
            status_text += " | [DEMO MODE]"
            
        status_text += f" | Containers: {self.running_containers}/{self.container_count}"
            
        self.status_panel.set_title(status_text)
        
        if self.docker_running:
            self.status_panel.set_color(docker_color)
        else:
            self.status_panel.set_color(socket_color)

    def _update_container_list(self):
        """Update the container list widget."""
        # Clear existing items
        self.container_list.clear()
        
        if self.demo_mode:
            # Add demo containers
            self.container_list.add_item("abc123: demo-webserver [RUNNING] (nginx:latest)")
            self.container_list.add_item("def456: demo-database [RUNNING] (mysql:8.0)")
            self.container_list.add_item("ghi789: demo-redis [RESTARTING] (redis:alpine)")
            self.container_list.add_item("jkl012: demo-backup [EXITED] (alpine:latest)")
            
            self.container_count = 4
            self.running_containers = 2
        else:
            # In real mode, this would make actual API calls
            self.container_list.add_item("No container data available")
            self.container_count = 0
            self.running_containers = 0

    def show_message(self, message: str, title: str = "Message"):
        """Show a popup message.
        
        Args:
            message: Message to display
            title: Title for the popup
        """
        self.root.show_message_popup(title, message)

    def show_loading_popup(self, message: str = "Loading..."):
        """Show a loading popup message.
        
        Args:
            message: Loading message to display
        """
        self.root.show_loading_icon_popup(message)

    def hide_loading_popup(self):
        """Hide the loading popup."""
        self.root.stop_loading_popup()

    def _start_service(self):
        """Start Docker service."""
        self.show_loading_popup("Starting Docker service...")
        
        # Use a thread to avoid blocking UI
        def thread_func():
            success = self.service_manager.start_service()
            self.hide_loading_popup()
            if success:
                self.show_message("Docker service started successfully")
                self.check_status()
            else:
                self.show_message("Failed to start Docker service", "Error")
        
        threading.Thread(target=thread_func, daemon=True).start()

    def _stop_service(self):
        """Stop Docker service."""
        self.show_loading_popup("Stopping Docker service...")
        
        def thread_func():
            success = self.service_manager.stop_service()
            self.hide_loading_popup()
            if success:
                self.show_message("Docker service stopped successfully")
                self.check_status()
            else:
                self.show_message("Failed to stop Docker service", "Error")
        
        threading.Thread(target=thread_func, daemon=True).start()

    def _restart_service(self):
        """Restart Docker service."""
        self.show_loading_popup("Restarting Docker service...")
        
        def thread_func():
            success = self.service_manager.restart_service()
            self.hide_loading_popup()
            if success:
                self.show_message("Docker service restarted successfully")
                self.check_status()
            else:
                self.show_message("Failed to restart Docker service", "Error")
        
        threading.Thread(target=thread_func, daemon=True).start()

    def _enable_service(self):
        """Enable Docker service at boot."""
        self.show_loading_popup("Enabling Docker service...")
        
        def thread_func():
            success = self.service_manager.enable_service()
            self.hide_loading_popup()
            if success:
                self.show_message("Docker service enabled at boot")
                self.docker_enabled = True
                self._update_status_panel()
            else:
                self.show_message("Failed to enable Docker service", "Error")
        
        threading.Thread(target=thread_func, daemon=True).start()

    def _disable_service(self):
        """Disable Docker service at boot."""
        self.show_loading_popup("Disabling Docker service...")
        
        def thread_func():
            success = self.service_manager.disable_service()
            self.hide_loading_popup()
            if success:
                self.show_message("Docker service disabled at boot")
                self.docker_enabled = False
                self._update_status_panel()
            else:
                self.show_message("Failed to disable Docker service", "Error")
        
        threading.Thread(target=thread_func, daemon=True).start()

    def _start_socket(self):
        """Start Docker socket."""
        self.show_loading_popup("Starting Docker socket...")
        
        def thread_func():
            success = self.service_manager.start_socket()
            self.hide_loading_popup()
            if success:
                self.show_message("Docker socket started successfully")
                self.check_status()
            else:
                self.show_message("Failed to start Docker socket", "Error")
        
        threading.Thread(target=thread_func, daemon=True).start()

    def _stop_socket(self):
        """Stop Docker socket."""
        self.show_loading_popup("Stopping Docker socket...")
        
        def thread_func():
            success = self.service_manager.stop_socket()
            self.hide_loading_popup()
            if success:
                self.show_message("Docker socket stopped successfully")
                self.check_status()
            else:
                self.show_message("Failed to stop Docker socket", "Error")
        
        threading.Thread(target=thread_func, daemon=True).start()

    def _enable_socket(self):
        """Enable Docker socket at boot."""
        self.show_loading_popup("Enabling Docker socket...")
        
        def thread_func():
            success = self.service_manager.enable_socket()
            self.hide_loading_popup()
            if success:
                self.show_message("Docker socket enabled at boot")
                self.socket_enabled = True
                self._update_status_panel()
            else:
                self.show_message("Failed to enable Docker socket", "Error")
        
        threading.Thread(target=thread_func, daemon=True).start()

    def _disable_socket(self):
        """Disable Docker socket at boot."""
        self.show_loading_popup("Disabling Docker socket...")
        
        def thread_func():
            success = self.service_manager.disable_socket()
            self.hide_loading_popup()
            if success:
                self.show_message("Docker socket disabled at boot")
                self.socket_enabled = False
                self._update_status_panel()
            else:
                self.show_message("Failed to disable Docker socket", "Error")
        
        threading.Thread(target=thread_func, daemon=True).start()

    def _view_container_logs(self):
        """View logs for the selected container."""
        selected_item = self.container_list.get()
        if not selected_item or selected_item == "Loading containers..." or selected_item == "No container data available":
            self.show_message("No container selected or no containers available", "Error")
            return
        
        # Extract container ID
        container_id = selected_item.split(":", 1)[0]
        
        self.show_message(f"Viewing logs for container {container_id}\n\nThis would open a logs view in the actual implementation.", "Container Logs")

    def _show_docker_info(self):
        """Show Docker system information."""
        self.show_loading_popup("Loading Docker info...")
        
        def thread_func():
            success = self.service_manager.check_docker_info()
            self.hide_loading_popup()
            if not success:
                self.show_message("Failed to get Docker information", "Error")
        
        threading.Thread(target=thread_func, daemon=True).start()

    def _check_privileges(self):
        """Check administrative privileges."""
        self.show_loading_popup("Checking privileges...")
        
        def thread_func():
            success = self.service_manager.check_privileges()
            self.hide_loading_popup()
            if success:
                self.show_message("Running with administrator privileges")
            else:
                self.show_message("Not running with administrator privileges\nSome operations may require elevated privileges", "Warning")
        
        threading.Thread(target=thread_func, daemon=True).start()

    def _list_templates(self):
        """List available templates."""
        self.show_loading_popup("Loading templates...")
        
        def thread_func():
            success = self.template_manager.list_templates()
            self.hide_loading_popup()
            if not success:
                self.show_message("Failed to list templates", "Error")
        
        threading.Thread(target=thread_func, daemon=True).start()

    def _create_environment(self):
        """Create an environment from a template."""
        # In a real implementation, this would show a form to select a template
        # and specify a directory
        self.show_message(
            "This would open a form to select a template and directory.\n\n"
            "Available templates:\n"
            "- LAMP Stack (lamp)\n"
            "- MEAN Stack (mean)\n"
            "- WordPress (wordpress)"
        )

    def _launch_environment(self):
        """Launch an environment from a template."""
        # Similar to create, but would also launch the environment
        self.show_message(
            "This would open a form to select a template and directory,\n"
            "then launch the environment with Docker Compose.\n\n"
            "Available templates:\n"
            "- LAMP Stack (lamp)\n"
            "- MEAN Stack (mean)\n"
            "- WordPress (wordpress)"
        )

    def _quit(self):
        """Quit the application."""
        sys.exit(0)

    def start(self):
        """Start the TUI application."""
        if self.demo_mode:
            self.show_message("Running in DEMO MODE\nOperations are simulated", "Demo Mode")
        self.root.start()


def run_tui(demo_mode: bool = False):
    """Run the TUI application.
    
    Args:
        demo_mode: Whether to use demo mode with simulated responses
    """
    tui = DockerTUI(demo_mode=demo_mode)
    tui.start()


if __name__ == "__main__":
    # Default to no demo mode
    demo_mode = "--demo" in sys.argv
    run_tui(demo_mode=demo_mode)