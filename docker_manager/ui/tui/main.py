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

class DockerTUI:
    """Terminal User Interface for Docker Service Manager using py-cui."""
    
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
        
        self.status_data = {}
        self.health_metrics = {}
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
        # Instead of tabs, we'll use a main menu and multiple views
        
        # Create current view tracker
        self.current_view = "overview"  # Default view
        
        # Main menu for navigation
        self.main_menu = self.root.add_scroll_menu(
            "Docker Manager Navigation", 0, 0, row_span=1, column_span=6, padx=1, pady=0
        )
        self.main_menu.add_item_list([
            "Overview",
            "Containers",
            "Services",
            "Health",
            "Templates",
            "AI Recommendations"
        ])
        self.main_menu.add_key_command(py_cui.keys.KEY_ENTER, self._switch_view)
        
        # Create all widgets, but we'll toggle visibility based on current view
        
        # OVERVIEW VIEW WIDGETS
        # System info widget
        self.system_info_widget = self.root.add_block_label(
            "System Information", 1, 0, row_span=2, column_span=3, padx=1, pady=0
        )
        
        # Docker status widget
        self.docker_status_widget = self.root.add_block_label(
            "Docker Status", 1, 3, row_span=2, column_span=3, padx=1, pady=0
        )
        
        # Quick actions menu
        self.quick_actions = self.root.add_scroll_menu(
            "Quick Actions", 3, 0, row_span=2, column_span=2, padx=1, pady=0
        )
        self.quick_actions.add_item_list([
            "Start Docker Service",
            "Stop Docker Service",
            "Restart Docker Service",
            "List Containers",
            "Generate Health Report",
            "Check Privileges"
        ])
        self.quick_actions.add_key_command(py_cui.keys.KEY_ENTER, self._handle_quick_action)
        
        # Alerts and notifications
        self.alerts_widget = self.root.add_text_block(
            "Alerts & Notifications", 3, 2, row_span=2, column_span=4, padx=1, pady=0
        )
        
        # CONTAINERS VIEW WIDGETS
        # Container list
        self.container_list = self.root.add_scroll_menu(
            "Containers", 1, 0, row_span=3, column_span=3, padx=1, pady=0
        )
        self.container_list.add_key_command(py_cui.keys.KEY_ENTER, self._handle_container_action)
        
        # Container actions
        self.container_actions = self.root.add_scroll_menu(
            "Container Actions", 4, 0, row_span=1, column_span=3, padx=1, pady=0
        )
        self.container_actions.add_item_list([
            "View Logs",
            "Start Container",
            "Stop Container",
            "Restart Container",
            "Remove Container",
            "View Container Details"
        ])
        
        # Container visualization
        self.visualization_widget = self.root.add_text_block(
            "Container Visualization", 1, 3, row_span=4, column_span=3, padx=1, pady=0
        )
        
        # SERVICES VIEW WIDGETS
        # Service status
        self.service_status = self.root.add_block_label(
            "Docker Service Status", 1, 0, row_span=2, column_span=3, padx=1, pady=0
        )
        
        # Socket status
        self.socket_status = self.root.add_block_label(
            "Docker Socket Status", 1, 3, row_span=2, column_span=3, padx=1, pady=0
        )
        
        # Service actions
        self.service_actions = self.root.add_scroll_menu(
            "Service Actions", 3, 0, row_span=2, column_span=3, padx=1, pady=0
        )
        self.service_actions.add_item_list([
            "Start Service",
            "Stop Service",
            "Restart Service",
            "Enable Service at Boot",
            "Disable Service at Boot"
        ])
        self.service_actions.add_key_command(py_cui.keys.KEY_ENTER, self._handle_service_action)
        
        # Socket actions
        self.socket_actions = self.root.add_scroll_menu(
            "Socket Actions", 3, 3, row_span=2, column_span=3, padx=1, pady=0
        )
        self.socket_actions.add_item_list([
            "Start Socket",
            "Stop Socket",
            "Enable Socket at Boot",
            "Disable Socket at Boot"
        ])
        self.socket_actions.add_key_command(py_cui.keys.KEY_ENTER, self._handle_socket_action)
        
        # HEALTH VIEW WIDGETS
        # CPU usage
        self.cpu_widget = self.root.add_text_block(
            "CPU Usage", 1, 0, row_span=2, column_span=3, padx=1, pady=0
        )
        
        # Memory usage
        self.memory_widget = self.root.add_text_block(
            "Memory Usage", 1, 3, row_span=2, column_span=3, padx=1, pady=0
        )
        
        # Disk usage
        self.disk_widget = self.root.add_text_block(
            "Disk Usage", 3, 0, row_span=2, column_span=3, padx=1, pady=0
        )
        
        # Container resources
        self.container_resources = self.root.add_text_block(
            "Container Resources", 3, 3, row_span=2, column_span=3, padx=1, pady=0
        )
        
        # TEMPLATES VIEW WIDGETS
        # Template list
        self.template_list = self.root.add_scroll_menu(
            "Environment Templates", 1, 0, row_span=3, column_span=3, padx=1, pady=0
        )
        self.template_list.add_key_command(py_cui.keys.KEY_ENTER, self._handle_template_action)
        
        # Template actions
        self.template_actions = self.root.add_scroll_menu(
            "Template Actions", 4, 0, row_span=1, column_span=3, padx=1, pady=0
        )
        self.template_actions.add_item_list([
            "Create Environment",
            "Launch Environment"
        ])
        
        # Template details
        self.template_details = self.root.add_text_block(
            "Template Details", 1, 3, row_span=4, column_span=3, padx=1, pady=0
        )
        
        # Set up status bar with emoji indicators
        self.root.set_status_bar_text(
            f"{EMOJI_STATUS['running' if self.demo_mode else 'unknown']} Docker Manager TUI   "
            f"Demo Mode: {'ON' if self.demo_mode else 'OFF'}   "
            f"Admin: {EMOJI_STATUS['enabled'] if self.is_admin else EMOJI_STATUS['disabled']}   "
            f"Press 'q' to quit, 'h' for help"
        )
        
        # Initialize UI data
        self._refresh_ui_data()
        
    def _background_refresh(self):
        """Background thread to refresh UI data periodically."""
        while not self.stop_refresh:
            try:
                # Refresh UI data
                self._refresh_ui_data()
                
                # The version of py-cui we're using may not have schedule_update
                # Instead, we'll directly update widgets but be cautious about thread safety
                try:
                    # Only update the UI if we're not in the middle of processing an event
                    # This avoids race conditions with the main UI thread
                    self._update_widgets()
                except:
                    # If there's an error, it might be due to thread conflicts
                    # We'll ignore it and try again next cycle
                    pass
                
                # Sleep for a bit before next refresh
                time.sleep(3)
            except Exception as e:
                # Log the error but don't crash
                print(f"Error in background refresh: {e}")
                time.sleep(5)  # Sleep longer on error
    
    def _refresh_ui_data(self):
        """Refresh all UI data."""
        try:
            # Get system info
            system_info = get_system_info()
            self.status_data["system_info"] = system_info
            
            # Get Docker service status
            service_status, _ = self.service_manager.get_status()
            self.status_data["service_status"] = service_status
            
            # Get Docker socket status
            socket_status, _ = self.service_manager.get_socket_status()
            self.status_data["socket_status"] = socket_status
            
            # Get container list if Docker is available
            if DOCKER_AVAILABLE or self.demo_mode:
                self.service_manager.list_containers()
                # In real implementation, we would store container data
                # For demo mode, generate sample containers
                if self.demo_mode:
                    self.containers = [
                        {"id": "abc123", "name": "web-server", "status": "running", "image": "nginx:latest"},
                        {"id": "def456", "name": "database", "status": "running", "image": "postgres:13"},
                        {"id": "ghi789", "name": "cache", "status": "exited", "image": "redis:alpine"},
                        {"id": "jkl012", "name": "api", "status": "paused", "image": "node:14"},
                        {"id": "mno345", "name": "worker", "status": "restarting", "image": "python:3.9"}
                    ]
                    
            # Get health metrics (CPU, memory, disk, etc.)
            self.health_metrics = self._get_health_metrics()
            
            # Get template list
            templates = self.template_manager.get_templates()
            self.status_data["templates"] = list(templates.keys())
            
        except Exception as e:
            print(f"Error refreshing UI data: {e}")
    
    def _switch_view(self):
        """Switch between different views based on main menu selection."""
        selected_view = self.main_menu.get_selected_item_index()
        view_mapping = {
            0: "overview",
            1: "containers",
            2: "services",
            3: "health",
            4: "templates", 
            5: "ai_recommendations"
        }
        
        self.current_view = view_mapping.get(selected_view, "overview")
        self._show_current_view()
        
        # Update the status bar to indicate current view
        view_name = self.current_view.capitalize()
        self.root.set_status_bar_text(
            f"{EMOJI_STATUS['running' if self.demo_mode else 'unknown']} Docker Manager TUI | "
            f"View: {view_name} | "
            f"Demo Mode: {'ON' if self.demo_mode else 'OFF'} | "
            f"Admin: {EMOJI_STATUS['enabled'] if self.is_admin else EMOJI_STATUS['disabled']} | "
            f"Press 'q' to quit, 'h' for help"
        )
        
    def _show_current_view(self):
        """Show/hide widgets based on current view."""
        # Rather than hiding/showing widgets, we'll use an alternative approach:
        # - Clear widgets that should be hidden by setting empty content
        # - Only update widgets in the active view with real content
        
        # Get all widgets for the current UI
        all_widgets = {
            # Overview widgets
            "system_info": self.system_info_widget,
            "docker_status": self.docker_status_widget,
            "quick_actions": self.quick_actions,
            "alerts": self.alerts_widget,
            
            # Containers widgets
            "container_list": self.container_list,
            "container_actions": self.container_actions,
            "visualization": self.visualization_widget,
            
            # Services widgets
            "service_status": self.service_status,
            "socket_status": self.socket_status,
            "service_actions": self.service_actions,
            "socket_actions": self.socket_actions,
            
            # Health widgets
            "cpu": self.cpu_widget,
            "memory": self.memory_widget,
            "disk": self.disk_widget,
            "container_resources": self.container_resources,
            
            # Templates widgets
            "template_list": self.template_list,
            "template_actions": self.template_actions,
            "template_details": self.template_details,
            
            # AI Recommendations widgets
            "ai_recommendation_list": self.ai_recommendation_list,
            "ai_recommendation_actions": self.ai_recommendation_actions,
            "ai_recommendation_details": self.ai_recommendation_details
        }
        
        # Define which widgets should be visible for each view
        visible_widgets = {
            "overview": ["system_info", "docker_status", "quick_actions", "alerts"],
            "containers": ["container_list", "container_actions", "visualization"],
            "services": ["service_status", "socket_status", "service_actions", "socket_actions"],
            "health": ["cpu", "memory", "disk", "container_resources"],
            "templates": ["template_list", "template_actions", "template_details"],
            "ai_recommendations": ["ai_recommendation_list", "ai_recommendation_actions", "ai_recommendation_details"]
        }
        
        # Always keep the main menu visible
        active_widgets = ["main_menu"] + visible_widgets.get(self.current_view, [])
        
        # Set focus to first widget in the current view
        if self.current_view == "overview":
            self.root.move_focus(self.system_info_widget)
        elif self.current_view == "containers":
            self.root.move_focus(self.container_list)
        elif self.current_view == "services":
            self.root.move_focus(self.service_status)
        elif self.current_view == "health":
            self.root.move_focus(self.cpu_widget)
        elif self.current_view == "templates":
            self.root.move_focus(self.template_list)
        elif self.current_view == "ai_recommendations":
            self.root.move_focus(self.ai_recommendation_list)
            
        # Update the root title to include the current view
        view_name = self.current_view.capitalize()
        self.root.set_title(f'Docker Service Manager TUI - {view_name} View')
            
    def _update_widgets(self):
        """Update all UI widgets with current data."""
        self._update_overview_tab()
        self._update_containers_tab()
        self._update_services_tab()
        self._update_health_tab()
        self._update_templates_tab()
        
        # Make sure the current view widgets are visible
        self._show_current_view()
    
    def _update_overview_tab(self):
        """Update Overview tab widgets."""
        # Update system info widget
        system_info = self.status_data.get("system_info", {})
        system_text = [
            f"Hostname: {system_info.get('hostname', 'Unknown')}",
            f"Platform: {system_info.get('platform', 'Unknown')}",
            f"OS: {system_info.get('os', 'Unknown')}",
            f"Kernel: {system_info.get('kernel', 'Unknown')}",
            f"CPU: {system_info.get('cpu', 'Unknown')}",
            f"Memory: {system_info.get('memory', 'Unknown')}",
            f"Docker: {'Available' if DOCKER_AVAILABLE or self.demo_mode else 'Not Available'}"
        ]
        self.system_info_widget.set_title(f"🖥️  System Information")
        self.system_info_widget.set_text('\n'.join(system_text))
        
        # Update Docker status widget
        service_status = self.status_data.get("service_status", False)
        socket_status = self.status_data.get("socket_status", False)
        
        docker_text = [
            f"Service Status: {EMOJI_STATUS['running'] if service_status else EMOJI_STATUS['offline']} "
            f"{'Running' if service_status else 'Stopped'}",
            f"Socket Status: {EMOJI_STATUS['up'] if socket_status else EMOJI_STATUS['down']} "
            f"{'Available' if socket_status else 'Unavailable'}",
            f"Admin Rights: {EMOJI_STATUS['enabled'] if self.is_admin else EMOJI_STATUS['no_access']} "
            f"{'Available' if self.is_admin else 'Not Available'}",
            f"Containers: {len(self.containers)} {'Active' if self.containers else 'None'}",
            f"Demo Mode: {'Enabled' if self.demo_mode else 'Disabled'}"
        ]
        self.docker_status_widget.set_title(f"🐳 Docker Status")
        self.docker_status_widget.set_text('\n'.join(docker_text))
        
        # Update alerts widget with health warnings
        critical_resources = []
        
        # Check CPU usage
        if self.health_metrics.get('cpu_percent', 0) > 90:
            critical_resources.append(f"{EMOJI_STATUS['critical']} CPU usage critical: {self.health_metrics.get('cpu_percent')}%")
        elif self.health_metrics.get('cpu_percent', 0) > 75:
            critical_resources.append(f"{EMOJI_STATUS['warning']} CPU usage high: {self.health_metrics.get('cpu_percent')}%")
            
        # Check memory usage
        if self.health_metrics.get('memory_percent', 0) > 90:
            critical_resources.append(f"{EMOJI_STATUS['critical']} Memory usage critical: {self.health_metrics.get('memory_percent')}%")
        elif self.health_metrics.get('memory_percent', 0) > 75:
            critical_resources.append(f"{EMOJI_STATUS['warning']} Memory usage high: {self.health_metrics.get('memory_percent')}%")
            
        # Check disk usage
        if self.health_metrics.get('disk_percent', 0) > 90:
            critical_resources.append(f"{EMOJI_STATUS['critical']} Disk usage critical: {self.health_metrics.get('disk_percent')}%")
        elif self.health_metrics.get('disk_percent', 0) > 75:
            critical_resources.append(f"{EMOJI_STATUS['warning']} Disk usage high: {self.health_metrics.get('disk_percent')}%")
        
        # Add Docker service alerts
        if not service_status:
            critical_resources.append(f"{EMOJI_STATUS['error']} Docker service is not running")
        
        if not socket_status:
            critical_resources.append(f"{EMOJI_STATUS['error']} Docker socket is not available")
            
        # Check admin rights
        if not self.is_admin:
            critical_resources.append(f"{EMOJI_STATUS['no_access']} Administrative privileges not available (some operations may fail)")
        
        # Set alert text
        if critical_resources:
            self.alerts_widget.set_text('\n'.join(critical_resources))
            self.alerts_widget.set_title(f"{EMOJI_STATUS['warning']} Alerts & Notifications")
        else:
            self.alerts_widget.set_text(f"{EMOJI_STATUS['excellent']} All systems operating normally\n\n"
                                       f"Last checked: {datetime.datetime.now().strftime('%H:%M:%S')}")
            self.alerts_widget.set_title(f"✅ System Status")
    
    def _update_containers_tab(self):
        """Update Containers tab widgets."""
        # Update container list
        self.container_list.clear()
        
        for container in self.containers:
            status = container.get('status', 'unknown')
            emoji = EMOJI_STATUS.get(status, EMOJI_STATUS['unknown'])
            self.container_list.add_item(f"{emoji} {container.get('name', 'Unknown')} - {status}")
        
        # Update visualization widget with ASCII art representation
        vis_text = self._generate_container_visualization()
        self.visualization_widget.set_text(vis_text)
    
    def _update_services_tab(self):
        """Update Services tab widgets."""
        # Update service status
        service_status = self.status_data.get("service_status", False)
        service_emoji = EMOJI_STATUS['running'] if service_status else EMOJI_STATUS['offline']
        
        service_text = [
            f"Status: {service_emoji} {'Running' if service_status else 'Stopped'}",
            f"Admin Rights: {EMOJI_STATUS['enabled'] if self.is_admin else EMOJI_STATUS['no_access']}",
            "",
            "Common issues if service won't start:",
            "- Docker daemon not installed",
            "- Insufficient permissions",
            "- Service configuration issues",
            "",
            f"Demo Mode: {'Enabled' if self.demo_mode else 'Disabled'}"
        ]
        
        self.service_status.set_title(f"🐳 Docker Service Status")
        self.service_status.set_text('\n'.join(service_text))
        
        # Update socket status
        socket_status = self.status_data.get("socket_status", False)
        socket_emoji = EMOJI_STATUS['up'] if socket_status else EMOJI_STATUS['down']
        
        socket_text = [
            f"Status: {socket_emoji} {'Available' if socket_status else 'Unavailable'}",
            f"Admin Rights: {EMOJI_STATUS['enabled'] if self.is_admin else EMOJI_STATUS['no_access']}",
            "",
            "Common issues if socket won't start:",
            "- Docker daemon not running",
            "- Socket path not accessible",
            "- Permission issues with socket file",
            "",
            f"Demo Mode: {'Enabled' if self.demo_mode else 'Disabled'}"
        ]
        
        self.socket_status.set_title(f"🔌 Docker Socket Status")
        self.socket_status.set_text('\n'.join(socket_text))
    
    def _update_health_tab(self):
        """Update Health tab widgets."""
        # Update CPU widget
        cpu_percent = self.health_metrics.get('cpu_percent', 0)
        cpu_status = self._get_status_emoji(cpu_percent)
        cpu_bar = self._generate_ascii_bar(cpu_percent)
        
        cpu_text = [
            f"Current: {cpu_percent:.1f}% {cpu_status}",
            f"Cores: {psutil.cpu_count(logical=True)}",
            f"Physical: {psutil.cpu_count(logical=False)}",
            "",
            f"{cpu_bar}"
        ]
        
        self.cpu_widget.set_title(f"{EMOJI_STATUS['cpu']} CPU Usage")
        self.cpu_widget.set_text('\n'.join(cpu_text))
        
        # Update memory widget
        memory_percent = self.health_metrics.get('memory_percent', 0)
        memory_status = self._get_status_emoji(memory_percent)
        memory_bar = self._generate_ascii_bar(memory_percent)
        
        memory_text = [
            f"Current: {memory_percent:.1f}% {memory_status}",
            f"Total: {self.health_metrics.get('memory_total', 'Unknown')}",
            f"Available: {self.health_metrics.get('memory_available', 'Unknown')}",
            "",
            f"{memory_bar}"
        ]
        
        self.memory_widget.set_title(f"{EMOJI_STATUS['memory']} Memory Usage")
        self.memory_widget.set_text('\n'.join(memory_text))
        
        # Update disk widget
        disk_percent = self.health_metrics.get('disk_percent', 0)
        disk_status = self._get_status_emoji(disk_percent)
        disk_bar = self._generate_ascii_bar(disk_percent)
        
        disk_text = [
            f"Current: {disk_percent:.1f}% {disk_status}",
            f"Total: {self.health_metrics.get('disk_total', 'Unknown')}",
            f"Free: {self.health_metrics.get('disk_free', 'Unknown')}",
            "",
            f"{disk_bar}"
        ]
        
        self.disk_widget.set_title(f"{EMOJI_STATUS['disk']} Disk Usage")
        self.disk_widget.set_text('\n'.join(disk_text))
        
        # Update container resources widget
        container_count = len(self.containers)
        running_count = sum(1 for c in self.containers if c.get('status') == 'running')
        
        container_text = [
            f"Total Containers: {container_count}",
            f"Running: {running_count} {EMOJI_STATUS['running']}",
            f"Stopped: {container_count - running_count} {EMOJI_STATUS['exited']}",
            "",
            "Container Status Summary:",
        ]
        
        # Add status counts
        status_counts = {}
        for container in self.containers:
            status = container.get('status', 'unknown')
            status_counts[status] = status_counts.get(status, 0) + 1
        
        for status, count in status_counts.items():
            emoji = EMOJI_STATUS.get(status, EMOJI_STATUS['unknown'])
            container_text.append(f"{emoji} {status.capitalize()}: {count}")
        
        self.container_resources.set_title(f"{EMOJI_STATUS['containers']} Container Resources")
        self.container_resources.set_text('\n'.join(container_text))
    
    def _update_templates_tab(self):
        """Update Templates tab widgets."""
        # Update template list
        self.template_list.clear()
        
        templates = self.status_data.get("templates", [])
        for template in templates:
            self.template_list.add_item(f"📦 {template}")
        
        # Update template details
        selected_index = self.template_list.get_selected_item_index()
        
        if selected_index is not None and 0 <= selected_index < len(templates):
            template_name = templates[selected_index]
            
            # Get template details (in real implementation, these would come from the template)
            if template_name == "LAMP":
                details = [
                    "Linux, Apache, MySQL, PHP stack",
                    "",
                    "Included components:",
                    "- Apache Web Server",
                    "- MySQL Database",
                    "- PHP Runtime",
                    "",
                    "Perfect for PHP web applications"
                ]
            elif template_name == "MEAN":
                details = [
                    "MongoDB, Express, Angular, Node.js stack",
                    "",
                    "Included components:",
                    "- MongoDB Database",
                    "- Express.js Backend",
                    "- Angular Frontend",
                    "- Node.js Runtime",
                    "",
                    "Ideal for JavaScript web applications"
                ]
            elif template_name == "WordPress":
                details = [
                    "WordPress development environment",
                    "",
                    "Included components:",
                    "- WordPress Latest",
                    "- MySQL Database",
                    "- PHPMyAdmin",
                    "",
                    "Ready for WordPress theme/plugin development"
                ]
            else:
                details = [f"No details available for {template_name}"]
            
            self.template_details.set_text('\n'.join(details))
            self.template_details.set_title(f"📦 {template_name} Details")
        else:
            self.template_details.set_text("Select a template to view details")
            self.template_details.set_title("Template Details")
    
    def _get_health_metrics(self) -> Dict[str, Any]:
        """Get system health metrics.
        
        Returns:
            Dictionary of health metrics
        """
        metrics = {}
        
        if self.demo_mode:
            # Generate demo metrics
            metrics['cpu_percent'] = 45.2
            metrics['memory_percent'] = 62.7
            metrics['memory_total'] = "16.0 GB"
            metrics['memory_available'] = "6.0 GB"
            metrics['disk_percent'] = 70.5
            metrics['disk_total'] = "512.0 GB"
            metrics['disk_free'] = "151.0 GB"
        else:
            try:
                # CPU usage
                metrics['cpu_percent'] = psutil.cpu_percent(interval=0.1)
                
                # Memory usage
                memory = psutil.virtual_memory()
                metrics['memory_percent'] = memory.percent
                metrics['memory_total'] = self._format_bytes(memory.total)
                metrics['memory_available'] = self._format_bytes(memory.available)
                
                # Disk usage
                disk = psutil.disk_usage('/')
                metrics['disk_percent'] = disk.percent
                metrics['disk_total'] = self._format_bytes(disk.total)
                metrics['disk_free'] = self._format_bytes(disk.free)
            except Exception as e:
                print(f"Error getting health metrics: {e}")
        
        return metrics
    
    def _format_bytes(self, bytes_value: int) -> str:
        """Format bytes to human-readable string.
        
        Args:
            bytes_value: Bytes value to format
            
        Returns:
            Formatted string (e.g., "1.23 GB")
        """
        bytes_float = float(bytes_value)
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_float < 1024 or unit == 'TB':
                return f"{bytes_float:.1f} {unit}"
            bytes_float /= 1024
        return f"{bytes_float:.1f} TB"  # Fallback return
    
    def _generate_ascii_bar(self, percent: float, width: int = 20) -> str:
        """Generate an ASCII progress bar.
        
        Args:
            percent: Percentage value (0-100)
            width: Width of the bar in characters
            
        Returns:
            ASCII progress bar string
        """
        filled_width = int(width * percent / 100)
        bar = '█' * filled_width + '░' * (width - filled_width)
        return f"[{bar}] {percent:.1f}%"
    
    def _get_status_emoji(self, value: float) -> str:
        """Get status emoji based on value.
        
        Args:
            value: Value to evaluate (typically percentage)
            
        Returns:
            Status emoji
        """
        if value < 50:
            return EMOJI_STATUS['excellent']
        elif value < 75:
            return EMOJI_STATUS['good']
        elif value < 90:
            return EMOJI_STATUS['warning']
        else:
            return EMOJI_STATUS['critical']
    
    def _generate_container_visualization(self) -> str:
        """Generate ASCII visualization of containers.
        
        Returns:
            ASCII visualization string
        """
        visualization = []
        visualization.append("Container Status Visualization:")
        visualization.append("")
        
        # Group containers by status
        status_groups = {}
        for container in self.containers:
            status = container.get('status', 'unknown')
            if status not in status_groups:
                status_groups[status] = []
            status_groups[status].append(container)
        
        # Generate visualization for each status group
        for status, containers in status_groups.items():
            emoji = EMOJI_STATUS.get(status, EMOJI_STATUS['unknown'])
            visualization.append(f"{emoji} {status.upper()} ({len(containers)})")
            
            for container in containers:
                name = container.get('name', 'unknown')
                image = container.get('image', 'unknown')
                visualization.append(f"  ├─ {name} - {image}")
            
            visualization.append("")
        
        # Add legend
        visualization.append("Legend:")
        for status, emoji in {
            'running': EMOJI_STATUS['running'],
            'paused': EMOJI_STATUS['paused'],
            'exited': EMOJI_STATUS['exited'],
            'created': EMOJI_STATUS['created'],
            'restarting': EMOJI_STATUS['restarting']
        }.items():
            visualization.append(f"  {emoji} {status.capitalize()}")
        
        return '\n'.join(visualization)
    
    def _handle_quick_action(self):
        """Handle quick action selection."""
        selected_action = self.quick_actions.get_selected_item_index()
        
        if selected_action == 0:  # Start Docker Service
            success = self.service_manager.start_service()
            self._show_status_popup("Service", "started", success)
        elif selected_action == 1:  # Stop Docker Service
            success = self.service_manager.stop_service()
            self._show_status_popup("Service", "stopped", success)
        elif selected_action == 2:  # Restart Docker Service
            success = self.service_manager.restart_service()
            self._show_status_popup("Service", "restarted", success)
        elif selected_action == 3:  # List Containers
            self.root.set_selected_tab(1)  # Switch to Containers tab
        elif selected_action == 4:  # Generate Health Report
            self.root.set_selected_tab(3)  # Switch to Health tab
            self.health_report.generate_report()
            self._show_status_popup("Health Report", "generated", True)
        elif selected_action == 5:  # Check Privileges
            success = self.service_manager.check_privileges()
            emoji = EMOJI_STATUS['enabled'] if success else EMOJI_STATUS['no_access']
            message = f"{emoji} Administrative privileges {'available' if success else 'not available'}"
            self._show_status_popup("Privileges", "checked", True, custom_message=message)
    
    def _handle_container_action(self):
        """Handle container selection."""
        # Update container details in visualization widget based on selection
        selected_index = self.container_list.get_selected_item_index()
        
        if selected_index is not None and 0 <= selected_index < len(self.containers):
            container = self.containers[selected_index]
            details = [
                f"Container: {container.get('name', 'Unknown')}",
                f"ID: {container.get('id', 'Unknown')}",
                f"Status: {EMOJI_STATUS.get(container.get('status', 'unknown'), EMOJI_STATUS['unknown'])} {container.get('status', 'Unknown')}",
                f"Image: {container.get('image', 'Unknown')}",
                "",
                "Select an action from the Actions menu below"
            ]
            
            self.visualization_widget.set_text('\n'.join(details))
            self.visualization_widget.set_title(f"{EMOJI_STATUS.get(container.get('status', 'unknown'), EMOJI_STATUS['unknown'])} Container Details")
    
    def _handle_service_action(self):
        """Handle service action selection."""
        selected_action = self.service_actions.get_selected_item_index()
        
        if selected_action == 0:  # Start Service
            success = self.service_manager.start_service()
            self._show_status_popup("Service", "started", success)
        elif selected_action == 1:  # Stop Service
            success = self.service_manager.stop_service()
            self._show_status_popup("Service", "stopped", success)
        elif selected_action == 2:  # Restart Service
            success = self.service_manager.restart_service()
            self._show_status_popup("Service", "restarted", success)
        elif selected_action == 3:  # Enable Service at Boot
            success = self.service_manager.enable_service()
            self._show_status_popup("Service", "enabled at boot", success)
        elif selected_action == 4:  # Disable Service at Boot
            success = self.service_manager.disable_service()
            self._show_status_popup("Service", "disabled at boot", success)
    
    def _handle_socket_action(self):
        """Handle socket action selection."""
        selected_action = self.socket_actions.get_selected_item_index()
        
        if selected_action == 0:  # Start Socket
            success = self.service_manager.start_socket()
            self._show_status_popup("Socket", "started", success)
        elif selected_action == 1:  # Stop Socket
            success = self.service_manager.stop_socket()
            self._show_status_popup("Socket", "stopped", success)
        elif selected_action == 2:  # Enable Socket at Boot
            success = self.service_manager.enable_socket()
            self._show_status_popup("Socket", "enabled at boot", success)
        elif selected_action == 3:  # Disable Socket at Boot
            success = self.service_manager.disable_socket()
            self._show_status_popup("Socket", "disabled at boot", success)
    
    def _handle_template_action(self):
        """Handle template action selection."""
        selected_template_index = self.template_list.get_selected_item_index()
        selected_action = self.template_actions.get_selected_item_index()
        
        if selected_template_index is not None and 0 <= selected_template_index < len(self.status_data.get("templates", [])):
            template_id = self.status_data.get("templates", [])[selected_template_index]
            
            if selected_action == 0:  # Create Environment
                success = self.template_manager.create_environment(template_id)
                self._show_status_popup(f"{template_id} Environment", "created", success)
            elif selected_action == 1:  # Launch Environment
                success = self.template_manager.launch_environment(template_id)
                self._show_status_popup(f"{template_id} Environment", "launched", success)
    
    def _show_status_popup(self, subject: str, action: str, success: bool, custom_message: Optional[str] = None):
        """Show status popup with emoji indicator.
        
        Args:
            subject: Subject of the action
            action: Action performed
            success: Whether action was successful
            custom_message: Optional custom message
        """
        status_emoji = EMOJI_STATUS['excellent'] if success else EMOJI_STATUS['error']
        
        if custom_message:
            message = custom_message
        else:
            message = f"{status_emoji} {subject} {action} {'successfully' if success else 'failed'}"
            
            if not success:
                if not self.is_admin:
                    message += "\n\nThis may be due to insufficient privileges."
                if self.demo_mode:
                    message += "\n\nNote: In demo mode, operations are simulated."
        
        # Create and show popup
        popup = self.root.show_message_popup(
            f"{subject} {action.capitalize()}", 
            message
        )
        
        # Close popup after a few seconds
        threading.Timer(3.0, lambda: self.root.stop_popup(popup)).start()
    
    def stop(self):
        """Stop the TUI gracefully."""
        self.stop_refresh = True
        if self.refresh_thread.is_alive():
            self.refresh_thread.join(timeout=1.0)


def run_tui(demo_mode: bool = False):
    """Run the Docker TUI application.
    
    Args:
        demo_mode: Whether to use demo mode with simulated responses
    """
    # Create the py_cui window with 5 rows and 6 columns
    # - Row 0: Navigation menu
    # - Rows 1-4: Content area
    root = py_cui.PyCUI(5, 6)
    
    # Set title
    root.set_title('Docker Service Manager TUI')
    
    # Create Docker TUI instance
    tui = DockerTUI(root, demo_mode=demo_mode)
    
    # Add keyboard shortcuts
    root.add_key_command(py_cui.keys.KEY_Q_LOWER, root.stop)
    root.add_key_command(py_cui.keys.KEY_H_LOWER, lambda: root.show_help_text("Help", 
                                                   "Docker Service Manager TUI\n\n"
                                                   "Navigation:\n"
                                                   "- Arrow keys: Move between widgets\n"
                                                   "- Tab: Next widget\n"
                                                   "- Enter: Select item or perform action\n"
                                                   "- H: Show this help\n"
                                                   "- Q: Quit application\n\n"
                                                   "Use the top menu to switch between different views:\n"
                                                   "- Overview: System and Docker status\n"
                                                   "- Containers: Manage Docker containers\n"
                                                   "- Services: Control Docker daemon services\n"
                                                   "- Health: View system resource usage\n"
                                                   "- Templates: Create and launch environments"))
    
    # Start the CUI
    try:
        # Make sure overview widgets are visible initially
        tui._show_current_view()
        
        # Set initial focus to the navigation menu
        root.move_focus(tui.main_menu)
        
        # Start the UI
        root.start()
    except KeyboardInterrupt:
        pass
    finally:
        tui.stop()


if __name__ == "__main__":
    # Default to no demo mode
    demo_mode = "--demo" in sys.argv
    run_tui(demo_mode=demo_mode)