"""
Container logs functionality for Docker service manager.
"""
import sys
import time
from typing import List, Dict, Optional, Any, Tuple

try:
    import docker
    from docker.errors import DockerException
    DOCKER_AVAILABLE = True
except ImportError:
    DOCKER_AVAILABLE = False


class ContainerLogs:
    """Container logs functionality for Docker."""
    
    def __init__(self, demo_mode: bool = False):
        """Initialize container logs handler.
        
        Args:
            demo_mode: Whether to use demo mode with simulated responses
        """
        self.demo_mode = demo_mode
        
    def get_container_logs(self, container_id: str, tail: int = 100, follow: bool = False) -> bool:
        """Get logs for a specific container.
        
        Args:
            container_id: Container ID or name
            tail: Number of lines to show from end of logs
            follow: Whether to follow log output (similar to tail -f)
            
        Returns:
            True if successful, False otherwise
        """
        # If in demo mode, show simulated container logs
        if self.demo_mode:
            print(f"DEMO MODE: Simulating logs for container '{container_id}'")
            timestamp = int(time.time())
            
            # Simulate different log types based on container ID prefix
            if container_id.startswith('abc'):
                # Web server logs
                log_entries = [
                    f"[{timestamp-10}] [info] Server started on port 8080",
                    f"[{timestamp-8}] [info] Connected to database",
                    f"[{timestamp-5}] [info] GET /api/users 200 5ms",
                    f"[{timestamp-3}] [warning] Slow query detected: SELECT * FROM users WHERE last_login > '2023-01-01'",
                    f"[{timestamp-2}] [info] POST /api/auth 201 15ms",
                    f"[{timestamp-1}] [info] GET /api/products 200 3ms"
                ]
            elif container_id.startswith('def'):
                # Database logs
                log_entries = [
                    f"[{timestamp-10}] [info] Database initialized",
                    f"[{timestamp-8}] [info] Connection established from 172.17.0.3:53402",
                    f"[{timestamp-5}] [warning] Query took 1.5s to execute",
                    f"[{timestamp-3}] [info] Checkpoint started",
                    f"[{timestamp-2}] [info] Checkpoint completed",
                    f"[{timestamp-1}] [info] Slow query log enabled"
                ]
            else:
                # Generic logs
                log_entries = [
                    f"[{timestamp-10}] [info] Container started",
                    f"[{timestamp-8}] [info] Application initialized",
                    f"[{timestamp-5}] [info] Processing task #1234",
                    f"[{timestamp-3}] [info] Task completed successfully",
                    f"[{timestamp-2}] [info] Memory usage: 234MB",
                    f"[{timestamp-1}] [info] Idle"
                ]
                
            # Display simulated logs
            logs_to_show = log_entries[-tail:] if tail > 0 else log_entries
            for entry in logs_to_show:
                print(entry)
                
            # If follow mode is enabled, simulate ongoing logs
            if follow:
                try:
                    print("\nPress Ctrl+C to stop following logs...\n")
                    follow_count = 0
                    while follow_count < 10:  # Limit to 10 entries in demo mode
                        time.sleep(2)
                        current_time = int(time.time())
                        print(f"[{current_time}] [info] New activity at {time.strftime('%H:%M:%S')}")
                        follow_count += 1
                except KeyboardInterrupt:
                    print("\nStopped following logs")
                    
            return True
                
        # Normal mode - try to connect to real Docker
        if not DOCKER_AVAILABLE:
            print("Error: Docker Python SDK not installed.")
            print("Install with: pip install docker")
            print("Or run with --demo mode to see simulated output")
            return False
            
        try:
            print(f"Connecting to Docker to get logs for container '{container_id}'...")
            client = docker.from_env()
            container = client.containers.get(container_id)
            
            # Get container logs
            logs = container.logs(tail=tail, stream=follow, timestamps=True).decode('utf-8')
            
            if not follow:
                # Print logs directly
                print(logs)
            else:
                # Stream logs in follow mode
                print("\nPress Ctrl+C to stop following logs...\n")
                try:
                    for line in logs:
                        print(line, end='')
                except KeyboardInterrupt:
                    print("\nStopped following logs")
            
            return True
        except DockerException as e:
            print(f"Error connecting to Docker: {e}")
            print("Make sure Docker service is running.")
            print("Or try running with --demo mode for demonstration")
            return False
        except Exception as e:
            print(f"Error getting container logs: {e}")
            return False