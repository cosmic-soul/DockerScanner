"""
System health report functionality for Docker service manager.

This module provides a one-click health report system with visual
performance metrics to diagnose Docker and system performance.
"""

import os
import sys
import time
import platform
import datetime
import tempfile
from typing import Dict, List, Any, Tuple, Optional, Union
import json
import subprocess
import psutil

try:
    import matplotlib
    matplotlib.use('Agg')  # Use non-interactive backend
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

from docker_manager.utils.display import (
    print_status, 
    print_section,
    print_table,
    get_terminal_size
)


class HealthReport:
    """System health report generator with visual metrics."""

    def __init__(self, demo_mode: bool = False):
        """Initialize health report generator.
        
        Args:
            demo_mode: Whether to use demo mode with simulated responses
        """
        self.demo_mode = demo_mode
        self.report_data = {}
        self.chart_files = []
        self.temp_dir = tempfile.mkdtemp(prefix='docker_manager_report_')
    
    def _run_command(self, command: List[str]) -> Tuple[bool, str]:
        """Run system command and return result.
        
        Args:
            command: Command to run as list of arguments
        
        Returns:
            Tuple of (success, output)
        """
        if self.demo_mode:
            if "docker" in command:
                if "info" in command:
                    return True, "Demo Docker Info Output"
                elif "stats" in command:
                    return True, "CONTAINER ID,NAME,CPU %,MEM USAGE/LIMIT,MEM %,NET I/O,BLOCK I/O,PIDS\ndemo1,web-server,1.5%,10MiB/1GiB,1%,10MB/20MB,5MB/10MB,10\ndemo2,database,3.2%,200MiB/1GiB,20%,5MB/2MB,15MB/5MB,5"
                elif "ps" in command:
                    return True, "CONTAINER ID,IMAGE,COMMAND,CREATED,STATUS,PORTS,NAMES\ndemo1,nginx,\"/docker-entrypoint.sh\",5 hours ago,Up 5 hours,80/tcp,web-server\ndemo2,postgres,\"postgres\",2 days ago,Up 2 days,5432/tcp,database"
                else:
                    return True, "Demo Docker Command Output"
            return True, "Demo Command Output"
        
        try:
            result = subprocess.run(
                command, 
                capture_output=True, 
                text=True, 
                check=False
            )
            return result.returncode == 0, result.stdout
        except Exception as e:
            return False, str(e)
    
    def _get_system_metrics(self) -> Dict[str, Any]:
        """Collect system performance metrics.
        
        Returns:
            Dictionary of system metrics
        """
        if self.demo_mode:
            # Generate realistic demo data
            return {
                "cpu": {
                    "percent": 45.2,
                    "count": 8,
                    "per_cpu": [35.1, 62.3, 41.8, 50.2, 38.7, 52.1, 47.5, 33.9]
                },
                "memory": {
                    "total": 16.0,  # GB
                    "available": 8.5,  # GB
                    "percent": 46.9,
                    "used": 7.5,  # GB
                    "cached": 4.2  # GB
                },
                "disk": {
                    "total": 512.0,  # GB
                    "used": 256.0,  # GB
                    "free": 256.0,  # GB
                    "percent": 50.0
                },
                "network": {
                    "bytes_sent": 2500000,
                    "bytes_recv": 8500000,
                    "packets_sent": 25000,
                    "packets_recv": 42000
                }
            }
        
        try:
            # Get real system metrics
            metrics = {}
            
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            cpu_per_cpu = psutil.cpu_percent(interval=0.5, percpu=True)
            
            metrics["cpu"] = {
                "percent": cpu_percent,
                "count": cpu_count,
                "per_cpu": cpu_per_cpu
            }
            
            # Memory metrics
            mem = psutil.virtual_memory()
            metrics["memory"] = {
                "total": round(mem.total / (1024 ** 3), 2),  # GB
                "available": round(mem.available / (1024 ** 3), 2),  # GB
                "percent": mem.percent,
                "used": round(mem.used / (1024 ** 3), 2),  # GB
                "cached": round(getattr(mem, 'cached', 0) / (1024 ** 3), 2)  # GB
            }
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            metrics["disk"] = {
                "total": round(disk.total / (1024 ** 3), 2),  # GB
                "used": round(disk.used / (1024 ** 3), 2),  # GB
                "free": round(disk.free / (1024 ** 3), 2),  # GB
                "percent": disk.percent
            }
            
            # Network metrics
            net_io = psutil.net_io_counters()
            metrics["network"] = {
                "bytes_sent": net_io.bytes_sent,
                "bytes_recv": net_io.bytes_recv,
                "packets_sent": net_io.packets_sent,
                "packets_recv": net_io.packets_recv
            }
            
            return metrics
        except Exception as e:
            print_status(f"Error collecting system metrics: {e}", "error")
            return {
                "error": str(e)
            }
    
    def _get_docker_metrics(self) -> Dict[str, Any]:
        """Collect Docker-specific metrics.
        
        Returns:
            Dictionary of Docker metrics
        """
        if self.demo_mode:
            # Generate realistic demo data
            return {
                "status": "running",
                "version": "24.0.5",
                "containers": {
                    "total": 5,
                    "running": 3,
                    "paused": 0,
                    "stopped": 2,
                    "containers": [
                        {
                            "id": "demo1",
                            "name": "web-server",
                            "image": "nginx",
                            "status": "running",
                            "cpu_percent": 1.5,
                            "memory_usage": "10MiB",
                            "memory_percent": 1.0,
                            "network_io": "10MB/20MB",
                            "block_io": "5MB/10MB",
                            "pids": 10
                        },
                        {
                            "id": "demo2",
                            "name": "database",
                            "image": "postgres",
                            "status": "running",
                            "cpu_percent": 3.2,
                            "memory_usage": "200MiB",
                            "memory_percent": 20.0,
                            "network_io": "5MB/2MB",
                            "block_io": "15MB/5MB",
                            "pids": 5
                        },
                        {
                            "id": "demo3",
                            "name": "cache",
                            "image": "redis",
                            "status": "running",
                            "cpu_percent": 0.8,
                            "memory_usage": "50MiB",
                            "memory_percent": 5.0,
                            "network_io": "2MB/1MB",
                            "block_io": "1MB/5MB",
                            "pids": 3
                        }
                    ]
                },
                "errors": None
            }
        
        try:
            metrics = {
                "status": "unknown",
                "version": "unknown",
                "containers": {
                    "total": 0,
                    "running": 0,
                    "paused": 0,
                    "stopped": 0,
                    "containers": []
                },
                "errors": None
            }
            
            # Get Docker version
            success, output = self._run_command(["docker", "version", "--format", "{{.Server.Version}}"])
            if success:
                metrics["status"] = "running"
                metrics["version"] = output.strip()
            else:
                metrics["status"] = "not running"
                metrics["errors"] = "Docker daemon is not running"
                return metrics
            
            # Get container info
            success, output = self._run_command(["docker", "ps", "-a", "--format", "{{.ID}},{{.Image}},{{.Status}},{{.Names}}"])
            if success:
                containers = []
                running = 0
                paused = 0
                stopped = 0
                
                for line in output.strip().split('\n'):
                    if line:
                        parts = line.split(',')
                        if len(parts) >= 4:
                            container_id, image, status, name = parts[0], parts[1], parts[2], parts[3]
                            
                            status_lower = status.lower()
                            if "running" in status_lower:
                                running += 1
                                status = "running"
                            elif "paused" in status_lower:
                                paused += 1
                                status = "paused"
                            else:
                                stopped += 1
                                status = "stopped"
                            
                            containers.append({
                                "id": container_id,
                                "name": name,
                                "image": image,
                                "status": status
                            })
                
                metrics["containers"]["total"] = len(containers)
                metrics["containers"]["running"] = running
                metrics["containers"]["paused"] = paused
                metrics["containers"]["stopped"] = stopped
                
                # Get detailed stats for running containers
                for container in containers:
                    if container["status"] == "running":
                        success, stats = self._run_command(
                            ["docker", "stats", container["id"], "--no-stream", "--format", 
                             "{{.CPUPerc}},{{.MemUsage}},{{.MemPerc}},{{.NetIO}},{{.BlockIO}},{{.PIDs}}"]
                        )
                        
                        if success and stats.strip():
                            parts = stats.strip().split(',')
                            if len(parts) >= 6:
                                cpu, mem_usage, mem_perc, net_io, block_io, pids = parts
                                
                                container.update({
                                    "cpu_percent": float(cpu.replace('%', '')) if '%' in cpu else 0.0,
                                    "memory_usage": mem_usage.split('/')[0].strip(),
                                    "memory_percent": float(mem_perc.replace('%', '')) if '%' in mem_perc else 0.0,
                                    "network_io": net_io,
                                    "block_io": block_io,
                                    "pids": int(pids) if pids.isdigit() else 0
                                })
                
                metrics["containers"]["containers"] = containers
            
            return metrics
        except Exception as e:
            metrics["errors"] = str(e)
            return metrics
    
    def _generate_cpu_chart(self) -> Optional[str]:
        """Generate CPU usage chart.
        
        Returns:
            Path to generated chart file, or None if chart generation failed
        """
        if not MATPLOTLIB_AVAILABLE:
            return None
        
        try:
            cpu_data = self.report_data.get("system", {}).get("cpu", {})
            if not cpu_data or "per_cpu" not in cpu_data:
                return None
            
            plt.figure(figsize=(10, 6))
            
            # Create bar chart for CPU usage per core
            cores = [f"Core {i+1}" for i in range(len(cpu_data["per_cpu"]))]
            plt.bar(cores, cpu_data["per_cpu"], color='#4a7abc')
            
            plt.title('CPU Usage per Core')
            plt.xlabel('CPU Cores')
            plt.ylabel('Usage (%)')
            plt.ylim(0, 100)
            plt.grid(axis='y', linestyle='--', alpha=0.7)
            
            # Add overall CPU percentage on the chart
            plt.axhline(y=cpu_data.get("percent", 0), color='r', linestyle='-', alpha=0.8, 
                        label=f'Overall: {cpu_data.get("percent", 0)}%')
            plt.legend()
            
            # Save chart to temp file
            filename = os.path.join(self.temp_dir, "cpu_usage.png")
            plt.savefig(filename, bbox_inches='tight')
            plt.close()
            
            self.chart_files.append(filename)
            return filename
        except Exception as e:
            print_status(f"Error generating CPU chart: {e}", "error")
            return None
    
    def _generate_memory_chart(self) -> Optional[str]:
        """Generate memory usage chart.
        
        Returns:
            Path to generated chart file, or None if chart generation failed
        """
        if not MATPLOTLIB_AVAILABLE:
            return None
        
        try:
            mem_data = self.report_data.get("system", {}).get("memory", {})
            if not mem_data:
                return None
            
            plt.figure(figsize=(8, 8))
            
            # Create pie chart for memory usage
            used = mem_data.get("used", 0)
            cached = mem_data.get("cached", 0)
            free = mem_data.get("available", 0)
            
            # Handle edge cases to ensure non-negative values
            if used < 0: used = 0
            if cached < 0: cached = 0
            if free < 0: free = 0
            
            # If all are zero, use dummy data for demo
            if used == 0 and cached == 0 and free == 0:
                if self.demo_mode:
                    used, cached, free = 7.5, 4.2, 8.5
                else:
                    return None
            
            labels = ['Used', 'Cached', 'Free']
            sizes = [used, cached, free]
            colors = ['#e64c4c', '#4ca6e6', '#5fe64c']
            explode = (0.1, 0, 0)  # explode the 1st slice (Used)
            
            plt.pie(sizes, explode=explode, labels=labels, colors=colors,
                    autopct='%1.1f%%', startangle=90, shadow=True)
            
            title = f'Memory Usage (Total: {mem_data.get("total", 0)} GB)'
            plt.title(title)
            plt.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle
            
            # Save chart to temp file
            filename = os.path.join(self.temp_dir, "memory_usage.png")
            plt.savefig(filename, bbox_inches='tight')
            plt.close()
            
            self.chart_files.append(filename)
            return filename
        except Exception as e:
            print_status(f"Error generating memory chart: {e}", "error")
            return None
    
    def _generate_disk_chart(self) -> Optional[str]:
        """Generate disk usage chart.
        
        Returns:
            Path to generated chart file, or None if chart generation failed
        """
        if not MATPLOTLIB_AVAILABLE:
            return None
        
        try:
            disk_data = self.report_data.get("system", {}).get("disk", {})
            if not disk_data:
                return None
            
            plt.figure(figsize=(8, 8))
            
            # Create a simple pie chart for disk usage
            used = disk_data.get("used", 0)
            free = disk_data.get("free", 0)
            
            if used == 0 and free == 0:
                if self.demo_mode:
                    used, free = 256.0, 256.0
                else:
                    return None
            
            labels = ['Used', 'Free']
            sizes = [used, free]
            colors = ['#e67c4c', '#4ce67c']
            explode = (0.1, 0)  # explode the 1st slice
            
            plt.pie(sizes, explode=explode, labels=labels, colors=colors,
                    autopct='%1.1f%%', startangle=90, shadow=True)
            
            title = f'Disk Usage (Total: {disk_data.get("total", 0)} GB)'
            plt.title(title)
            plt.axis('equal')
            
            # Save chart to temp file
            filename = os.path.join(self.temp_dir, "disk_usage.png")
            plt.savefig(filename, bbox_inches='tight')
            plt.close()
            
            self.chart_files.append(filename)
            return filename
        except Exception as e:
            print_status(f"Error generating disk chart: {e}", "error")
            return None
    
    def _generate_container_chart(self) -> Optional[str]:
        """Generate container resources chart.
        
        Returns:
            Path to generated chart file, or None if chart generation failed
        """
        if not MATPLOTLIB_AVAILABLE:
            return None
        
        try:
            docker_data = self.report_data.get("docker", {})
            containers = docker_data.get("containers", {}).get("containers", [])
            
            running_containers = [c for c in containers if c.get("status") == "running" 
                                 and "cpu_percent" in c and "memory_percent" in c]
            
            if not running_containers:
                if self.demo_mode:
                    # Create demo containers for visualization
                    running_containers = [
                        {"name": "web-server", "cpu_percent": 1.5, "memory_percent": 1.0},
                        {"name": "database", "cpu_percent": 3.2, "memory_percent": 20.0},
                        {"name": "cache", "cpu_percent": 0.8, "memory_percent": 5.0}
                    ]
                else:
                    return None
            
            # Create figure with two subplots
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 7))
            
            # Container names
            names = [c.get("name", f"Container {i}") for i, c in enumerate(running_containers)]
            cpu_values = [c.get("cpu_percent", 0) for c in running_containers]
            mem_values = [c.get("memory_percent", 0) for c in running_containers]
            
            # CPU Usage subplot
            ax1.barh(names, cpu_values, color='#4a7abc')
            ax1.set_title('Container CPU Usage')
            ax1.set_xlabel('CPU (%)')
            ax1.grid(axis='x', linestyle='--', alpha=0.7)
            
            # Memory Usage subplot
            ax2.barh(names, mem_values, color='#e64c4c')
            ax2.set_title('Container Memory Usage')
            ax2.set_xlabel('Memory (%)')
            ax2.grid(axis='x', linestyle='--', alpha=0.7)
            
            # Adjust layout
            plt.tight_layout()
            
            # Save chart to temp file
            filename = os.path.join(self.temp_dir, "container_resources.png")
            plt.savefig(filename, bbox_inches='tight')
            plt.close()
            
            self.chart_files.append(filename)
            return filename
        except Exception as e:
            print_status(f"Error generating container chart: {e}", "error")
            return None
    
    def _generate_ascii_chart(self, data: List[float], max_value: float = 100.0, 
                            width: int = 40, title: str = "", labels: List[str] = None) -> str:
        """Generate an ASCII bar chart with improved visualization.
        
        Args:
            data: List of values to chart
            max_value: Maximum value for scaling
            width: Width of the chart in characters
            title: Chart title
            labels: Optional list of labels for each data point
            
        Returns:
            String containing ASCII chart
        """
        if not data:
            return "No data to display"
        
        result = []
        if title:
            result.append(title)
            result.append("=" * len(title))
        
        for i, value in enumerate(data):
            # Calculate bar length
            bar_len = int((value / max_value) * width)
            bar_len = max(0, min(width, bar_len))  # Clamp to valid range
            
            # Create color-coded bar based on value (in terminal visualization)
            # We use the same character but conceptually it would be colored
            bar_char = '█'
            
            # Get label or default to index number
            if labels and i < len(labels):
                label = labels[i]
            else:
                label = f"Item {i+1}"
                
            # Create the bar with color indication by using different spacing
            if value / max_value > 0.8:  # High usage - would be red
                bar = bar_char * bar_len
            elif value / max_value > 0.6:  # Medium usage - would be yellow
                bar = bar_char * bar_len
            else:  # Low usage - would be green
                bar = bar_char * bar_len
            
            # Format the label with fixed width
            label_width = 15
            padded_label = f"{label:<{label_width}}"
            
            # Add the label and value with formatted bar
            result.append(f"{padded_label} [{bar:<{width}}] {value:.1f}%")
        
        return "\n".join(result)
    
    def _cleanup_temp_files(self) -> None:
        """Clean up temporary files created for the report."""
        for file in self.chart_files:
            try:
                if os.path.exists(file):
                    os.remove(file)
            except Exception:
                pass
        
        try:
            if os.path.exists(self.temp_dir):
                os.rmdir(self.temp_dir)
        except Exception:
            pass
    
    def generate_report(self) -> bool:
        """Generate a complete system health report.
        
        Returns:
            True if report was generated successfully, False otherwise
        """
        print_section("System Health Report")
        print_status("Collecting system information...", "info")
        
        # Collect data
        self.report_data = {
            "timestamp": datetime.datetime.now().isoformat(),
            "system": {
                "os": platform.system(),
                "platform": platform.platform(),
                "python": sys.version.split()[0],
                "hostname": platform.node()
            },
            "recommendations": [],  # Will hold recommendation objects
            "status": {
                "overall": "excellent",  # Can be excellent, good, warning, critical
                "issues_count": 0
            }
        }
        
        # Add system metrics
        print_status("Collecting system metrics...", "info")
        system_metrics = self._get_system_metrics()
        self.report_data["system"].update(system_metrics)
        
        # Add Docker metrics
        print_status("Collecting Docker metrics...", "info")
        self.report_data["docker"] = self._get_docker_metrics()
        
        # Generate recommendations based on collected data
        print_status("Generating recommendations...", "info")
        self._generate_recommendations()
        
        # Generate visual charts (if matplotlib is available)
        has_charts = False
        if MATPLOTLIB_AVAILABLE:
            print_status("Generating performance charts...", "info")
            cpu_chart = self._generate_cpu_chart()
            memory_chart = self._generate_memory_chart()
            disk_chart = self._generate_disk_chart()
            container_chart = self._generate_container_chart()
            has_charts = any([cpu_chart, memory_chart, disk_chart, container_chart])
        
        # Display the report
        self._display_report(has_charts)
        
        return True
    
    def _display_report(self, has_charts: bool = False) -> None:
        """Display the health report in the terminal.
        
        Args:
            has_charts: Whether charts were generated
        """
        term_width, _ = get_terminal_size()
        divider = "=" * term_width
        
        # Report Header
        print()
        print_section("Docker Service Manager - System Health Report")
        print(f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"System: {self.report_data['system']['os']} ({self.report_data['system']['platform']})")
        print(f"Hostname: {self.report_data['system']['hostname']}")
        print(divider)
        
        # System Metrics
        print_section("System Resources")
        
        # CPU
        cpu_data = self.report_data["system"].get("cpu", {})
        if cpu_data:
            print(f"CPU Usage: {cpu_data.get('percent', 0)}% ({cpu_data.get('count', 0)} cores)")
            
            # Show per-CPU usage with ASCII chart if no matplotlib
            if not has_charts and cpu_data.get("per_cpu"):
                per_cpu = cpu_data.get("per_cpu", [])
                cpu_labels = [f"Core {i+1}" for i in range(len(per_cpu))]
                cpu_chart = self._generate_ascii_chart(
                    per_cpu, 
                    max_value=100.0, 
                    width=40, 
                    title="Per-Core CPU Usage (%)",
                    labels=cpu_labels
                )
                print("\n" + cpu_chart + "\n")
        
        # Memory
        mem_data = self.report_data["system"].get("memory", {})
        if mem_data:
            total = mem_data.get("total", 0)
            used = mem_data.get("used", 0)
            print(f"Memory Usage: {mem_data.get('percent', 0)}% ({used:.1f} GB of {total:.1f} GB)")
            
            if not has_charts:
                # Show memory breakdown with ASCII chart
                mem_values = [
                    mem_data.get("used", 0),
                    mem_data.get("cached", 0),
                    mem_data.get("available", 0)
                ]
                
                headers = ["Component", "Size (GB)", "Percentage"]
                rows = [
                    ["Used", f"{mem_data.get('used', 0):.1f}", f"{mem_data.get('percent', 0):.1f}%"],
                    ["Cached", f"{mem_data.get('cached', 0):.1f}", f"{(mem_data.get('cached', 0) / total * 100) if total else 0:.1f}%"],
                    ["Available", f"{mem_data.get('available', 0):.1f}", f"{(mem_data.get('available', 0) / total * 100) if total else 0:.1f}%"]
                ]
                print()
                print_table(headers, rows)
        
        # Disk
        disk_data = self.report_data["system"].get("disk", {})
        if disk_data:
            total = disk_data.get("total", 0)
            used = disk_data.get("used", 0)
            print(f"Disk Usage: {disk_data.get('percent', 0)}% ({used:.1f} GB of {total:.1f} GB)")
        
        # Network
        net_data = self.report_data["system"].get("network", {})
        if net_data:
            recv_mb = net_data.get("bytes_recv", 0) / (1024 * 1024)
            sent_mb = net_data.get("bytes_sent", 0) / (1024 * 1024)
            print(f"Network I/O: {recv_mb:.1f} MB received, {sent_mb:.1f} MB sent")
        
        print(divider)
        
        # Docker Information
        print_section("Docker Status")
        
        docker_data = self.report_data.get("docker", {})
        docker_status = docker_data.get("status", "unknown")
        
        if docker_status == "running":
            print_status("Docker daemon is running", "ok")
            print(f"Docker version: {docker_data.get('version', 'unknown')}")
            
            # Container statistics
            containers = docker_data.get("containers", {})
            total = containers.get("total", 0)
            running = containers.get("running", 0)
            stopped = containers.get("stopped", 0)
            
            print(f"Containers: {total} total, {running} running, {stopped} stopped")
            
            if running > 0:
                print()
                print_section("Running Containers")
                
                # Create table of running containers
                running_containers = [c for c in containers.get("containers", []) 
                                     if c.get("status") == "running"]
                
                if running_containers:
                    headers = ["Name", "Image", "CPU %", "Memory Usage", "Memory %"]
                    rows = []
                    
                    for container in running_containers:
                        rows.append([
                            container.get("name", "Unknown"),
                            container.get("image", "Unknown"),
                            f"{container.get('cpu_percent', 0):.1f}%",
                            container.get("memory_usage", "Unknown"),
                            f"{container.get('memory_percent', 0):.1f}%"
                        ])
                    
                    print_table(headers, rows)
                    
                    if not has_charts:
                        # Generate ASCII chart of container resource usage
                        print()
                        cpu_values = [c.get("cpu_percent", 0) for c in running_containers]
                        names = [c.get("name", f"Container {i}") for i, c in enumerate(running_containers)]
                        
                        # Use our enhanced chart function for container visualization
                        max_cpu = max(cpu_values) if cpu_values else 5.0
                        max_cpu = max(5.0, max_cpu)  # Ensure a reasonable minimum
                        
                        container_cpu_chart = self._generate_ascii_chart(
                            cpu_values,
                            max_value=max_cpu,
                            width=30,
                            title="Container CPU Usage",
                            labels=names
                        )
                        print("\n" + container_cpu_chart)
        else:
            print_status("Docker daemon is not running", "error")
            if docker_data.get("errors"):
                print(f"Error: {docker_data.get('errors')}")
        
        print(divider)
        
        # Information about Charts
        if has_charts:
            print_section("Performance Charts")
            print("Charts have been generated and saved to:")
            for chart_file in self.chart_files:
                if os.path.exists(chart_file):
                    print(f" - {chart_file}")
            print()
            print("To view these charts, open them with an image viewer.")
            print("In terminal environments, you can use tools like 'display', 'xdg-open',")
            print("or transfer them to a system with graphical capabilities.")
        elif MATPLOTLIB_AVAILABLE:
            print_status("No charts were generated. This may be due to insufficient data.", "warning")
        else:
            print_status("Charts could not be generated because matplotlib is not available.", "info")
            print("Install matplotlib to enable visual charts: pip install matplotlib")
        
        # Recommendations
        self._display_recommendations()
        
        print(divider)
        print("Report completed.\n")
    
    def _generate_recommendations(self) -> None:
        """Generate structured recommendations based on collected data."""
        system = self.report_data.get("system", {})
        docker = self.report_data.get("docker", {})
        
        # Reset recommendations
        self.report_data["recommendations"] = []
        
        # Track issues count for status
        issues_count = 0
        
        # CPU recommendations
        cpu_data = system.get("cpu", {})
        cpu_percent = cpu_data.get("percent", 0)
        if cpu_percent > 80:
            self.report_data["recommendations"].append({
                "type": "critical",
                "component": "cpu",
                "title": "High CPU Usage",
                "description": "CPU usage is high. Consider limiting container CPU usage or scaling services.",
                "metrics": {"current": cpu_percent, "threshold": 80},
                "action": "docker update --cpus=X container_name"
            })
            issues_count += 1
        elif cpu_percent > 70:
            self.report_data["recommendations"].append({
                "type": "warning",
                "component": "cpu",
                "title": "Elevated CPU Usage",
                "description": "CPU usage is elevated. Monitor for potential performance issues.",
                "metrics": {"current": cpu_percent, "threshold": 70},
                "action": "Monitor CPU trends with Docker stats"
            })
            issues_count += 1
        
        # Memory recommendations
        mem_data = system.get("memory", {})
        mem_percent = mem_data.get("percent", 0)
        if mem_percent > 85:
            self.report_data["recommendations"].append({
                "type": "critical",
                "component": "memory",
                "title": "High Memory Usage",
                "description": "Memory usage is high. Consider increasing swap space or limiting container memory.",
                "metrics": {"current": mem_percent, "threshold": 85},
                "action": "docker update --memory=X container_name"
            })
            issues_count += 1
        elif mem_percent > 75:
            self.report_data["recommendations"].append({
                "type": "warning",
                "component": "memory",
                "title": "Elevated Memory Usage",
                "description": "Memory usage is elevated. Monitor for potential resource constraints.",
                "metrics": {"current": mem_percent, "threshold": 75},
                "action": "Monitor memory usage with Docker stats"
            })
            issues_count += 1
        
        # Disk recommendations
        disk_data = system.get("disk", {})
        disk_percent = disk_data.get("percent", 0)
        if disk_percent > 85:
            self.report_data["recommendations"].append({
                "type": "critical",
                "component": "disk",
                "title": "High Disk Usage",
                "description": "Disk usage is high. Consider cleaning up unused images and volumes.",
                "metrics": {"current": disk_percent, "threshold": 85},
                "action": "docker system prune -a"
            })
            issues_count += 1
        elif disk_percent > 75:
            self.report_data["recommendations"].append({
                "type": "warning",
                "component": "disk",
                "title": "Elevated Disk Usage",
                "description": "Disk usage is elevated. Consider cleaning up unused resources.",
                "metrics": {"current": disk_percent, "threshold": 75},
                "action": "docker system prune"
            })
            issues_count += 1
        
        # Docker status recommendations
        if docker.get("status") != "running":
            self.report_data["recommendations"].append({
                "type": "critical",
                "component": "docker",
                "title": "Docker Daemon Not Running",
                "description": "Docker daemon is not running.",
                "metrics": {"current": "stopped", "expected": "running"},
                "action": "systemctl start docker (or appropriate command for your system)"
            })
            issues_count += 1
        else:
            # Container recommendations
            containers = docker.get("containers", {})
            stopped_count = containers.get("stopped", 0)
            if stopped_count > 5:
                self.report_data["recommendations"].append({
                    "type": "warning",
                    "component": "containers",
                    "title": "Stopped Containers",
                    "description": f"You have {stopped_count} stopped containers that could be cleaned up.",
                    "metrics": {"current": stopped_count, "threshold": 5},
                    "action": "docker container prune"
                })
                issues_count += 1
            
            # Performance recommendations for running containers
            running_containers = [c for c in containers.get("containers", []) if c.get("status") == "running"]
            high_cpu_containers = [c for c in running_containers if c.get("cpu_percent", 0) > 80]
            
            if high_cpu_containers:
                container_names = ", ".join([c.get("name", "Unknown") for c in high_cpu_containers])
                self.report_data["recommendations"].append({
                    "type": "critical",
                    "component": "container_cpu",
                    "title": "High Container CPU Usage",
                    "description": f"High CPU usage detected in containers: {container_names}",
                    "metrics": {"containers": len(high_cpu_containers), "threshold": 80},
                    "action": "docker update --cpus=X container_name"
                })
                issues_count += 1
            
            high_mem_containers = [c for c in running_containers if c.get("memory_percent", 0) > 80]
            if high_mem_containers:
                container_names = ", ".join([c.get("name", "Unknown") for c in high_mem_containers])
                self.report_data["recommendations"].append({
                    "type": "critical",
                    "component": "container_memory",
                    "title": "High Container Memory Usage",
                    "description": f"High memory usage detected in containers: {container_names}",
                    "metrics": {"containers": len(high_mem_containers), "threshold": 80},
                    "action": "docker update --memory=X container_name"
                })
                issues_count += 1
        
        # Update overall status based on recommendations
        if issues_count == 0:
            self.report_data["status"]["overall"] = "excellent"
        elif issues_count <= 2 and not any(r.get("type") == "critical" for r in self.report_data["recommendations"]):
            self.report_data["status"]["overall"] = "good"
        elif issues_count <= 4:
            self.report_data["status"]["overall"] = "warning"
        else:
            self.report_data["status"]["overall"] = "critical"
        
        self.report_data["status"]["issues_count"] = issues_count
    
    def _display_recommendations(self) -> None:
        """Display system and Docker health recommendations."""
        print_section("Recommendations")
        
        recommendations = self.report_data.get("recommendations", [])
        
        # Display recommendations
        if recommendations:
            for i, recommendation in enumerate(recommendations, 1):
                rec_type = recommendation.get("type", "info").upper()
                title = recommendation.get("title", "Recommendation")
                description = recommendation.get("description", "")
                action = recommendation.get("action", "")
                
                print(f"{i}. [{rec_type}] {title}: {description}")
                if action:
                    print(f"   - Suggested action: {action}")
        else:
            print("No specific recommendations at this time. System appears to be healthy.")
    
    def save_report(self, filename: str) -> Optional[str]:
        """Save the health report to a file.
        
        Args:
            filename: Name of the file to save the report to
            
        Returns:
            Path to the saved file on success, None on failure
        """
        try:
            # Create a serializable version of the report data
            serializable_data = {
                "timestamp": self.report_data.get("timestamp", datetime.datetime.now().isoformat()),
                "system": self.report_data.get("system", {}),
                "docker": self.report_data.get("docker", {}),
                "recommendations": self.report_data.get("recommendations", []),
                "status": self.report_data.get("status", {"overall": "unknown", "issues_count": 0})
            }
            
            # Create the file
            with open(filename, 'w') as f:
                json.dump(serializable_data, f, indent=2)
            
            print_status(f"Health report saved to {os.path.abspath(filename)}", "ok")
            return os.path.abspath(filename)
        except Exception as e:
            print_status(f"Error saving health report: {e}", "error")
            return None