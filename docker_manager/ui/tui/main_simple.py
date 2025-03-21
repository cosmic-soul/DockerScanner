"""
Terminal User Interface (TUI) for Docker Service Manager.

This module provides a simple but effective TUI using py-cui,
offering a more visual and intuitive interface than the basic
interactive console.
"""

import os
import sys
import time
import json
import threading
import datetime
from typing import Dict, List, Any, Optional, Callable, Tuple

import py_cui
import psutil
try:
    import docker
    from docker.errors import DockerException
    DOCKER_AVAILABLE = True
except ImportError:
    DOCKER_AVAILABLE = False

from ...core.service_manager import DockerServiceManager
from ...core.health_report import HealthReport
from ...core.container_visualization import ContainerVisualizer
from ...utils.display import print_status
from ...utils.system import get_system_info, check_admin_privileges
from ...templates.environment_templates import TemplateManager

# Status indicators
STATUS_INDICATORS = {
    "ok": "[+]",
    "error": "[-]",
    "warning": "[!]",
    "info": "[i]",
    "running": "[RUNNING]",
    "stopped": "[STOPPED]",
    "paused": "[PAUSED]",
    "exited": "[EXITED]",
    "restarting": "[RESTARTING]",
    "created": "[CREATED]",
    "unknown": "[UNKNOWN]",
}

class DockerSimpleTUI:
    """Simple Terminal User Interface for Docker Service Manager using py-cui."""
    
    def __init__(self, root: py_cui.PyCUI, demo_mode: bool = False):
        """Initialize the Docker TUI.
        
        Args:
            root: The py-cui root window
            demo_mode: Whether to use demo mode with simulated responses
        """
        self.root = root
        self.demo_mode = demo_mode
        self.service_manager = DockerServiceManager(demo_mode=demo_mode)
        self.health_report = HealthReport(demo_mode=demo_mode)
        self.container_visualizer = ContainerVisualizer(demo_mode=demo_mode)
        self.template_manager = TemplateManager(demo_mode=demo_mode)
        
        self.containers = []
        self.is_admin = check_admin_privileges()
        
        # Create the UI layout
        self._create_ui()
        
        # Start background refresh thread
        self.stop_refresh = False
        self.refresh_thread = threading.Thread(target=self._background_refresh)
        self.refresh_thread.daemon = True
        self.refresh_thread.start()
        
    def _create_ui(self):
        """Create the TUI layout and widgets."""
        # Define titles for later use
        status_title = "Docker Status"
        system_title = "System Information"
        containers_title = "Containers"
        service_actions_title = "Service Actions"
        container_actions_title = "Container Actions"
        log_title = "Operation Log"
        
        # Dashboard - status box (use text block instead of block label)
        self.status_box = self.root.add_text_block(
            status_title, 0, 0, row_span=2, column_span=2, padx=1, pady=0
        )
        self.status_box.set_text("Loading Docker status...")
        
        # System Information (use text block instead of block label)
        self.system_box = self.root.add_text_block(
            system_title, 0, 2, row_span=2, column_span=2, padx=1, pady=0
        )
        self.system_box.set_text("Loading system information...")
        
        # Containers List
        self.container_list = self.root.add_scroll_menu(
            containers_title, 2, 0, row_span=3, column_span=2, padx=1, pady=0
        )
        self.container_list.add_key_command(py_cui.keys.KEY_ENTER, self._select_container)
        
        # Service Actions
        self.action_menu = self.root.add_scroll_menu(
            service_actions_title, 2, 2, row_span=1, column_span=2, padx=1, pady=0
        )
        service_actions = [
            "Start Docker Service",
            "Stop Docker Service",
            "Restart Docker Service",
            "Enable Docker Service",
            "Disable Docker Service",
            "Generate Health Report"
        ]
        for action in service_actions:
            self.action_menu.add_item(action)
        self.action_menu.add_key_command(py_cui.keys.KEY_ENTER, self._perform_action)
        
        # Container Actions
        self.container_actions = self.root.add_scroll_menu(
            container_actions_title, 3, 2, row_span=1, column_span=2, padx=1, pady=0
        )
        container_actions = [
            "View Logs",
            "Start Container",
            "Stop Container",
            "Restart Container",
            "View Details",
            "Visualize Containers"
        ]
        for action in container_actions:
            self.container_actions.add_item(action)
        self.container_actions.add_key_command(py_cui.keys.KEY_ENTER, self._perform_container_action)
        
        # Output Log
        self.log_box = self.root.add_text_block(
            log_title, 4, 2, row_span=1, column_span=2, padx=1, pady=0
        )
        
        # Initial log message
        self.log_message("Docker Service Manager TUI initialized")
        
        # Set status bar text
        self.root.set_status_bar_text(
            f"Docker Service Manager TUI | "
            f"Demo Mode: {'ON' if self.demo_mode else 'OFF'} | "
            f"Admin: {'YES' if self.is_admin else 'NO'} | "
            f"Press 'q' to quit, 'h' for help"
        )
        
    def _background_refresh(self):
        """Background thread to refresh the UI data periodically."""
        while not self.stop_refresh:
            try:
                self._refresh_data()
                time.sleep(3)  # Refresh every 3 seconds
            except Exception as e:
                self.log_message(f"Error refreshing data: {e}")
                time.sleep(5)  # Wait longer on error
    
    def _refresh_data(self):
        """Refresh UI data."""
        try:
            # Get system info
            system_info = get_system_info()
            
            try:
                # Create a short summary of system info for display
                sys_summary = f"OS: {system_info.get('os', 'Unknown')} | CPU: {system_info.get('cpu', 'Unknown')}"
                self.system_box.set_text(sys_summary)
            except Exception as e:
                self.log_message(f"Error updating system info: {e}")
            
            try:
                # Get Docker service status
                service_status, _ = self.service_manager.get_status()
                socket_status, _ = self.service_manager.get_socket_status()
                
                # Create a simplified status display
                status_summary = f"Docker Service: {'Running' if service_status else 'Stopped'} | " \
                                 f"Demo Mode: {'ON' if self.demo_mode else 'OFF'}"
                self.status_box.set_text(status_summary)
            except Exception as e:
                self.log_message(f"Error updating Docker status: {e}")
            
            # Update container list
            if service_status or self.demo_mode:
                # For demo mode, generate sample containers
                if self.demo_mode:
                    self.containers = [
                        {"id": "abc123", "name": "web-server", "status": "running", "image": "nginx:latest"},
                        {"id": "def456", "name": "database", "status": "running", "image": "postgres:13"},
                        {"id": "ghi789", "name": "cache", "status": "exited", "image": "redis:alpine"},
                        {"id": "jkl012", "name": "api", "status": "paused", "image": "node:14"},
                        {"id": "mno345", "name": "worker", "status": "restarting", "image": "python:3.9"}
                    ]
                
                # Update container list UI
                self.container_list.clear()
                for container in self.containers:
                    status = container.get('status', 'unknown')
                    indicator = STATUS_INDICATORS.get(status, STATUS_INDICATORS['unknown'])
                    self.container_list.add_item(f"{indicator} {container.get('name', 'Unknown')} [{container.get('id', '')[:8]}]")
            else:
                self.container_list.clear()
                self.container_list.add_item("Docker service is not running")
                
        except Exception as e:
            self.log_message(f"Error updating UI: {e}")
    
    def _select_container(self):
        """Handle container selection."""
        selected_index = self.container_list.get_selected_item_index()
        
        if selected_index is not None and 0 <= selected_index < len(self.containers):
            container = self.containers[selected_index]
            container_info = [
                f"ID: {container.get('id', 'Unknown')}",
                f"Name: {container.get('name', 'Unknown')}",
                f"Status: {container.get('status', 'Unknown')}",
                f"Image: {container.get('image', 'Unknown')}"
            ]
            self.log_message('\n'.join(container_info))
    
    def _perform_action(self):
        """Perform a service action."""
        selected_index = self.action_menu.get_selected_item_index()
        
        if selected_index == 0:  # Start Docker Service
            success = self.service_manager.start_service()
            self.log_message(f"{'Successfully started' if success else 'Failed to start'} Docker service")
        elif selected_index == 1:  # Stop Docker Service
            success = self.service_manager.stop_service()
            self.log_message(f"{'Successfully stopped' if success else 'Failed to stop'} Docker service")
        elif selected_index == 2:  # Restart Docker Service
            success = self.service_manager.restart_service()
            self.log_message(f"{'Successfully restarted' if success else 'Failed to restart'} Docker service")
        elif selected_index == 3:  # Enable Docker Service
            success = self.service_manager.enable_service()
            self.log_message(f"{'Successfully enabled' if success else 'Failed to enable'} Docker service at boot")
        elif selected_index == 4:  # Disable Docker Service
            success = self.service_manager.disable_service()
            self.log_message(f"{'Successfully disabled' if success else 'Failed to disable'} Docker service at boot")
        elif selected_index == 5:  # Generate Health Report
            self.log_message("Generating health report...")
            success = self.health_report.generate_report()
            if success:
                self.log_message("Health report generated successfully")
                report_path = self.health_report.save_report("health_report.json")
                if report_path:
                    self.log_message(f"Report saved to {report_path}")
            else:
                self.log_message("Failed to generate health report")
        
        # Refresh data after action
        self._refresh_data()
    
    def _perform_container_action(self):
        """Perform a container action."""
        selected_container_index = self.container_list.get_selected_item_index()
        selected_action_index = self.container_actions.get_selected_item_index()
        
        if selected_container_index is None or selected_container_index >= len(self.containers):
            self.log_message("Please select a container first")
            return
        
        container = self.containers[selected_container_index]
        
        if selected_action_index == 0:  # View Logs
            self.log_message(f"Showing logs for container {container.get('name', 'Unknown')}")
            if self.demo_mode:
                sample_logs = [
                    "2023-01-01 12:00:00 | Starting application",
                    "2023-01-01 12:00:01 | Loading configuration",
                    "2023-01-01 12:00:02 | Configuration loaded successfully",
                    "2023-01-01 12:00:03 | Connecting to database",
                    "2023-01-01 12:00:04 | Database connection established",
                    "2023-01-01 12:00:05 | Server listening on port 8080",
                    "2023-01-01 12:00:10 | Received request from 192.168.1.1",
                    "2023-01-01 12:00:15 | Request processed successfully"
                ]
                self.log_message('\n'.join(sample_logs))
        elif selected_action_index == 1:  # Start Container
            self.log_message(f"Starting container {container.get('name', 'Unknown')}")
            if self.demo_mode:
                self.log_message("Container started successfully (demo mode)")
                container['status'] = 'running'
        elif selected_action_index == 2:  # Stop Container
            self.log_message(f"Stopping container {container.get('name', 'Unknown')}")
            if self.demo_mode:
                self.log_message("Container stopped successfully (demo mode)")
                container['status'] = 'exited'
        elif selected_action_index == 3:  # Restart Container
            self.log_message(f"Restarting container {container.get('name', 'Unknown')}")
            if self.demo_mode:
                self.log_message("Container restarted successfully (demo mode)")
                container['status'] = 'running'
        elif selected_action_index == 4:  # View Details
            self.log_message(f"Viewing details for container {container.get('name', 'Unknown')}")
            if self.demo_mode:
                details = [
                    f"ID: {container.get('id', 'Unknown')}",
                    f"Name: {container.get('name', 'Unknown')}",
                    f"Status: {container.get('status', 'Unknown')}",
                    f"Image: {container.get('image', 'Unknown')}",
                    "Network: bridge",
                    "IP: 172.17.0.2",
                    "Created: 2023-01-01 09:00:00",
                    "Ports: 80/tcp -> 0.0.0.0:8080",
                    "Command: nginx -g 'daemon off;'"
                ]
                self.log_message('\n'.join(details))
        elif selected_action_index == 5:  # Visualize Containers
            self.log_message("Generating container visualization...")
            if self.demo_mode:
                visualization = self._generate_ascii_visualization()
                self.log_message('\n' + visualization)
        
        # Refresh data after action
        self._refresh_data()
    
    def log_message(self, message: str):
        """Add a message to the log box."""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        
        # Append the new message to the log box
        self.log_box.set_text(f"[{timestamp}] {message}")
    
    def _generate_ascii_visualization(self):
        """Generate a simple ASCII visualization of containers.
        
        Returns:
            ASCII visualization as a string
        """
        if not self.containers:
            return "No containers to visualize"
        
        # Count container status
        status_count = {}
        for container in self.containers:
            status = container.get('status', 'unknown')
            status_count[status] = status_count.get(status, 0) + 1
        
        # Generate visualization
        lines = ["== Container Status Visualization ==", ""]
        
        # Header
        lines.append("Status    | Count | Visualization")
        lines.append("-" * 50)
        
        # Generate status bars
        for status, count in status_count.items():
            indicator = STATUS_INDICATORS.get(status, STATUS_INDICATORS['unknown'])
            bar = "█" * count
            lines.append(f"{status:<9} | {count:^5} | {bar} {indicator}")
        
        lines.append("")
        lines.append("== Container Network Diagram ==")
        lines.append("")
        lines.append("        ┌───────────┐")
        lines.append("        │  Docker   │")
        lines.append("        │  Engine   │")
        lines.append("        └─────┬─────┘")
        lines.append("              │")
        lines.append("       ┌──────┴──────┐")
        lines.append("       │  Network    │")
        lines.append("       │  Bridge     │")
        lines.append("       └──────┬──────┘")
        lines.append("              │")
        
        # Generate container boxes
        for i, container in enumerate(self.containers[:5]):  # Limit to 5 containers to avoid clutter
            status = container.get('status', 'unknown')
            indicator = STATUS_INDICATORS.get(status, STATUS_INDICATORS['unknown'])
            name = container.get('name', 'Unknown')
            
            if i == 0:
                lines.append("    ┌─────┴─────┐     ")
            else:
                lines.append("    │             │     ")
                
            lines.append(f"    │  {name:<10} │ {indicator}")
            
            if i == len(self.containers[:5]) - 1:
                lines.append("    └─────────────┘     ")
            else:
                lines.append("    └──────┬──────┘     ")
                lines.append("           │            ")
        
        return "\n".join(lines)
        
    def stop(self):
        """Stop the TUI gracefully."""
        self.stop_refresh = True
        if self.refresh_thread.is_alive():
            self.refresh_thread.join(timeout=1.0)


def run_simple_tui(demo_mode: bool = False):
    """Run the simplified Docker TUI application.
    
    Args:
        demo_mode: Whether to use demo mode with simulated responses
    """
    # Create the py_cui window - use smaller size for better compatibility
    root = py_cui.PyCUI(5, 4)
    
    # Set title
    root.set_title('Docker Service Manager TUI')
    
    # Enable unicode support
    root.toggle_unicode_borders()
    
    # Create Docker TUI instance
    tui = DockerSimpleTUI(root, demo_mode=demo_mode)
    
    # Add keyboard shortcut to quit
    root.add_key_command(py_cui.keys.KEY_Q_LOWER, root.stop)
    root.add_key_command(py_cui.keys.KEY_H_LOWER, lambda: root.show_message_popup(
        "Help", 
        "Docker Service Manager TUI\n\n"
        "Navigation:\n"
        "- Arrow keys: Move between widgets\n"
        "- Tab: Next widget\n"
        "- Enter: Select action or container\n"
        "- H: Show this help\n"
        "- Q: Quit application\n\n"
        "Use the Service Actions menu to manage Docker service\n"
        "Use the Container Actions menu to manage containers\n"
        "Select a container from the list to see its details"
    ))
    
    # Start the CUI with error handling
    try:
        root.start()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"Error in TUI: {e}")
    finally:
        tui.stop()


if __name__ == "__main__":
    # Default to no demo mode
    demo_mode = "--demo" in sys.argv
    run_simple_tui(demo_mode=demo_mode)