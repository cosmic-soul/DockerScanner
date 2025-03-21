"""
AI-powered container recommendation system for Docker Service Manager.

This module provides intelligent recommendations for container configuration,
resource allocation, and optimization based on usage patterns and system metrics.
"""

import os
import json
import time
import random
import logging
import docker
from typing import Dict, List, Any, Tuple, Optional

# Internal imports
from docker_manager.utils.system import get_system_info
from docker_manager.core.health_report import HealthReport

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ContainerRecommendationEngine:
    """AI-powered recommendation engine for Docker containers."""
    
    # Pre-defined templates for common application types
    APPLICATION_TEMPLATES = {
        "web_server": {
            "name": "Web Server",
            "base_image": "nginx:alpine",
            "resource_profile": "balanced",
            "ports": [80, 443],
            "volumes": ["/var/www", "/etc/nginx/conf.d"],
            "env_vars": ["NGINX_HOST", "NGINX_PORT"],
            "networks": ["frontend"],
            "tags": ["web", "http", "reverse-proxy"]
        },
        "database": {
            "name": "Database Server",
            "base_image": "postgres:13-alpine",
            "resource_profile": "memory-optimized",
            "ports": [5432],
            "volumes": ["/var/lib/postgresql/data"],
            "env_vars": ["POSTGRES_USER", "POSTGRES_PASSWORD", "POSTGRES_DB"],
            "networks": ["backend"],
            "tags": ["database", "persistence", "sql"]
        },
        "app_server": {
            "name": "Application Server",
            "base_image": "node:16-alpine",
            "resource_profile": "balanced",
            "ports": [3000],
            "volumes": ["/app", "/app/node_modules"],
            "env_vars": ["NODE_ENV", "PORT", "DATABASE_URL"],
            "networks": ["frontend", "backend"],
            "tags": ["application", "server", "api"]
        },
        "cache": {
            "name": "Cache Server",
            "base_image": "redis:alpine",
            "resource_profile": "memory-optimized",
            "ports": [6379],
            "volumes": ["/data"],
            "env_vars": ["REDIS_PASSWORD"],
            "networks": ["backend"],
            "tags": ["cache", "in-memory", "key-value"]
        },
        "message_queue": {
            "name": "Message Queue",
            "base_image": "rabbitmq:3-management-alpine",
            "resource_profile": "balanced",
            "ports": [5672, 15672],
            "volumes": ["/var/lib/rabbitmq"],
            "env_vars": ["RABBITMQ_DEFAULT_USER", "RABBITMQ_DEFAULT_PASS"],
            "networks": ["backend"],
            "tags": ["queue", "messaging", "pubsub"]
        }
    }
    
    # Resource profiles mapping
    RESOURCE_PROFILES = {
        "minimal": {
            "cpu": 0.5,
            "memory": "256m",
            "memory_reservation": "128m",
            "description": "Minimum resources for basic functionality"
        },
        "balanced": {
            "cpu": 1.0,
            "memory": "512m",
            "memory_reservation": "256m",
            "description": "Balanced resources for general-purpose workloads"
        },
        "performance": {
            "cpu": 2.0,
            "memory": "1g",
            "memory_reservation": "512m",
            "description": "Enhanced performance for demanding applications"
        },
        "memory-optimized": {
            "cpu": 1.0,
            "memory": "2g",
            "memory_reservation": "1g",
            "description": "Optimized for memory-intensive applications"
        },
        "cpu-optimized": {
            "cpu": 4.0,
            "memory": "1g",
            "memory_reservation": "512m",
            "description": "Optimized for CPU-intensive workloads"
        }
    }
    
    def __init__(self, demo_mode: bool = False):
        """Initialize recommendation engine.
        
        Args:
            demo_mode: Whether to use demo mode with simulated data
        """
        self.demo_mode = demo_mode
        self.health_report = HealthReport(demo_mode=demo_mode)
        self.container_history = []
        self.system_metrics_history = []
        self.recommendations_cache = {}
        self.last_analysis_time = 0
        
        # Create data directory if it doesn't exist
        self.data_dir = os.path.expanduser("~/.docker_manager/data")
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Load historical data if available
        self._load_historical_data()
    
    def _load_historical_data(self) -> bool:
        """Load historical container and system metrics data.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Load container history
            container_history_file = os.path.join(self.data_dir, "container_history.json")
            if os.path.exists(container_history_file):
                with open(container_history_file, "r") as f:
                    self.container_history = json.load(f)
            
            # Load system metrics history
            system_metrics_file = os.path.join(self.data_dir, "system_metrics.json")
            if os.path.exists(system_metrics_file):
                with open(system_metrics_file, "r") as f:
                    self.system_metrics_history = json.load(f)
            
            return True
        except Exception as e:
            logger.error(f"Error loading historical data: {e}")
            return False
    
    def _save_historical_data(self) -> bool:
        """Save historical container and system metrics data.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Save container history (limit to last 100 entries)
            container_history_file = os.path.join(self.data_dir, "container_history.json")
            with open(container_history_file, "w") as f:
                json.dump(self.container_history[-100:], f, indent=2)
            
            # Save system metrics history (limit to last 100 entries)
            system_metrics_file = os.path.join(self.data_dir, "system_metrics.json")
            with open(system_metrics_file, "w") as f:
                json.dump(self.system_metrics_history[-100:], f, indent=2)
            
            return True
        except Exception as e:
            logger.error(f"Error saving historical data: {e}")
            return False
    
    def _get_containers_data(self) -> List[Dict[str, Any]]:
        """Get current container data for analysis.
        
        Returns:
            List of container dictionaries with relevant information
        """
        if self.demo_mode:
            # Generate sample containers for demo mode
            return [
                {
                    "id": "abc123def456",
                    "name": "web-server",
                    "image": "nginx:latest",
                    "status": "running",
                    "created": time.time() - 86400 * 3,  # 3 days ago
                    "ports": ["80/tcp", "443/tcp"],
                    "size": 125.8,  # MB
                    "memory_usage": 128.5,  # MB
                    "cpu_usage": 5.2,  # %
                    "restart_count": 2
                },
                {
                    "id": "def456ghi789",
                    "name": "postgres-db",
                    "image": "postgres:13",
                    "status": "running",
                    "created": time.time() - 86400 * 10,  # 10 days ago
                    "ports": ["5432/tcp"],
                    "size": 421.3,  # MB
                    "memory_usage": 356.8,  # MB
                    "cpu_usage": 8.7,  # %
                    "restart_count": 0
                },
                {
                    "id": "ghi789jkl012",
                    "name": "redis-cache",
                    "image": "redis:alpine",
                    "status": "running",
                    "created": time.time() - 86400 * 5,  # 5 days ago
                    "ports": ["6379/tcp"],
                    "size": 32.1,  # MB
                    "memory_usage": 42.6,  # MB
                    "cpu_usage": 1.3,  # %
                    "restart_count": 1
                },
                {
                    "id": "jkl012mno345",
                    "name": "node-app",
                    "image": "node:14",
                    "status": "exited",
                    "created": time.time() - 86400 * 1,  # 1 day ago
                    "ports": ["3000/tcp"],
                    "size": 978.5,  # MB
                    "memory_usage": 0,  # MB (not running)
                    "cpu_usage": 0,  # % (not running)
                    "restart_count": 5
                }
            ]
        else:
            # In real mode, get actual container data from Docker
            try:
                import docker
                client = docker.from_env()
                containers = []
                
                for container in client.containers.list(all=True):
                    stats = container.stats(stream=False)
                    
                    # Extract and calculate metrics
                    memory_usage = stats.get("memory_stats", {}).get("usage", 0) / (1024 * 1024)  # Convert to MB
                    cpu_delta = stats.get("cpu_stats", {}).get("cpu_usage", {}).get("total_usage", 0) - \
                                stats.get("precpu_stats", {}).get("cpu_usage", {}).get("total_usage", 0)
                    system_delta = stats.get("cpu_stats", {}).get("system_cpu_usage", 0) - \
                                  stats.get("precpu_stats", {}).get("system_cpu_usage", 0)
                    cpu_usage = 0
                    if system_delta > 0:
                        num_cpus = len(stats.get("cpu_stats", {}).get("cpu_usage", {}).get("percpu_usage", []))
                        cpu_usage = (cpu_delta / system_delta) * num_cpus * 100
                    
                    containers.append({
                        "id": container.id,
                        "name": container.name,
                        "image": container.image.tags[0] if container.image.tags else "unknown",
                        "status": container.status,
                        "created": container.attrs.get("Created", 0),
                        "ports": [f"{host_port}/tcp" for host_port in container.ports.keys()],
                        "size": container.attrs.get("SizeRootFs", 0) / (1024 * 1024),  # Convert to MB
                        "memory_usage": memory_usage,
                        "cpu_usage": cpu_usage,
                        "restart_count": container.attrs.get("RestartCount", 0)
                    })
                
                return containers
            except Exception as e:
                logger.error(f"Error getting container data: {e}")
                return []
    
    def _get_system_metrics(self) -> Dict[str, Any]:
        """Get current system metrics for analysis.
        
        Returns:
            Dictionary of system metrics
        """
        # Get system info
        system_info = get_system_info()
        
        if self.demo_mode:
            # Generate sample metrics for demo mode
            total_memory = 16 * 1024  # 16 GB
            used_memory = random.uniform(4 * 1024, 12 * 1024)  # 4-12 GB
            
            return {
                "timestamp": time.time(),
                "cpu_usage": random.uniform(10, 70),  # %
                "total_memory": total_memory,  # MB
                "used_memory": used_memory,  # MB
                "memory_usage": (used_memory / total_memory) * 100,  # %
                "disk_usage": random.uniform(40, 80),  # %
                "network_rx": random.uniform(100, 1000),  # KB/s
                "network_tx": random.uniform(50, 500),  # KB/s
                "system_load": [random.uniform(0.1, 4.0), random.uniform(0.2, 3.0), random.uniform(0.1, 2.0)],
                "docker_containers_running": random.randint(3, 10),
                "docker_containers_total": random.randint(5, 15),
                "docker_images": random.randint(10, 30)
            }
        else:
            # In real mode, get actual system metrics
            try:
                import psutil
                
                # Get CPU usage
                cpu_percent = psutil.cpu_percent(interval=0.5)
                
                # Get memory information
                mem = psutil.virtual_memory()
                total_memory = mem.total / (1024 * 1024)  # MB
                used_memory = mem.used / (1024 * 1024)  # MB
                memory_percent = mem.percent
                
                # Get disk usage
                disk = psutil.disk_usage('/')
                disk_percent = disk.percent
                
                # Get network I/O
                net_io = psutil.net_io_counters()
                
                # Get system load
                load_avg = [x / psutil.cpu_count() * 100 for x in psutil.getloadavg()]
                
                # Get Docker information
                docker_info = {}
                try:
                    import docker
                    client = docker.from_env()
                    info = client.info()
                    docker_info = {
                        "docker_containers_running": info.get("ContainersRunning", 0),
                        "docker_containers_total": info.get("Containers", 0),
                        "docker_images": info.get("Images", 0)
                    }
                except Exception as e:
                    logger.warning(f"Could not get Docker info: {e}")
                    docker_info = {
                        "docker_containers_running": 0,
                        "docker_containers_total": 0,
                        "docker_images": 0
                    }
                
                return {
                    "timestamp": time.time(),
                    "cpu_usage": cpu_percent,
                    "total_memory": total_memory,
                    "used_memory": used_memory,
                    "memory_usage": memory_percent,
                    "disk_usage": disk_percent,
                    "network_rx": net_io.bytes_recv / 1024,  # KB
                    "network_tx": net_io.bytes_sent / 1024,  # KB
                    "system_load": load_avg,
                    **docker_info
                }
            except Exception as e:
                logger.error(f"Error getting system metrics: {e}")
                return {"timestamp": time.time()}
    
    def _analyze_container_usage(self, containers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze container usage patterns.
        
        Args:
            containers: List of container data dictionaries
            
        Returns:
            Analysis results dictionary
        """
        if not containers:
            return {"status": "no_containers"}
        
        # Initialize analysis results
        results = {
            "timestamp": time.time(),
            "total_containers": len(containers),
            "running_containers": sum(1 for c in containers if c.get("status") == "running"),
            "stopped_containers": sum(1 for c in containers if c.get("status") == "exited"),
            "container_types": {},
            "resource_usage": {
                "average_memory_usage": 0,
                "average_cpu_usage": 0,
                "high_memory_containers": [],
                "high_cpu_containers": [],
                "idle_containers": []
            },
            "reliability": {
                "high_restart_containers": [],
                "average_restart_count": 0
            },
            "optimization_opportunities": []
        }
        
        # Calculate resource usage metrics
        running_containers = [c for c in containers if c.get("status") == "running"]
        if running_containers:
            # Calculate memory metrics
            memory_usage_values = [c.get("memory_usage", 0) for c in running_containers]
            results["resource_usage"]["average_memory_usage"] = sum(memory_usage_values) / len(running_containers)
            
            # Calculate CPU metrics
            cpu_usage_values = [c.get("cpu_usage", 0) for c in running_containers]
            results["resource_usage"]["average_cpu_usage"] = sum(cpu_usage_values) / len(running_containers)
            
            # Identify high memory usage containers (>500MB or >2x average)
            high_memory_threshold = max(500, results["resource_usage"]["average_memory_usage"] * 2)
            results["resource_usage"]["high_memory_containers"] = [
                c.get("name", c.get("id", "unknown"))
                for c in running_containers
                if c.get("memory_usage", 0) > high_memory_threshold
            ]
            
            # Identify high CPU usage containers (>50% or >2x average)
            high_cpu_threshold = max(50, results["resource_usage"]["average_cpu_usage"] * 2)
            results["resource_usage"]["high_cpu_containers"] = [
                c.get("name", c.get("id", "unknown"))
                for c in running_containers
                if c.get("cpu_usage", 0) > high_cpu_threshold
            ]
            
            # Identify idle containers (<1% CPU and <10MB memory)
            results["resource_usage"]["idle_containers"] = [
                c.get("name", c.get("id", "unknown"))
                for c in running_containers
                if c.get("cpu_usage", 0) < 1 and c.get("memory_usage", 0) < 10
            ]
        
        # Calculate reliability metrics
        restart_counts = [c.get("restart_count", 0) for c in containers]
        if restart_counts:
            results["reliability"]["average_restart_count"] = sum(restart_counts) / len(containers)
            
            # Identify containers with high restart counts (>5 or >2x average)
            high_restart_threshold = max(5, results["reliability"]["average_restart_count"] * 2)
            results["reliability"]["high_restart_containers"] = [
                c.get("name", c.get("id", "unknown"))
                for c in containers
                if c.get("restart_count", 0) > high_restart_threshold
            ]
        
        # Identify optimization opportunities
        opportunities = []
        
        # Memory limit opportunities
        if results["resource_usage"]["high_memory_containers"]:
            opportunities.append({
                "type": "memory_limit",
                "containers": results["resource_usage"]["high_memory_containers"],
                "description": "Set appropriate memory limits for high memory usage containers"
            })
        
        # CPU limit opportunities
        if results["resource_usage"]["high_cpu_containers"]:
            opportunities.append({
                "type": "cpu_limit",
                "containers": results["resource_usage"]["high_cpu_containers"],
                "description": "Set CPU quotas for high CPU usage containers"
            })
        
        # Idle container opportunities
        if results["resource_usage"]["idle_containers"]:
            opportunities.append({
                "type": "idle_containers",
                "containers": results["resource_usage"]["idle_containers"],
                "description": "Remove or optimize idle containers"
            })
        
        # Reliability opportunities
        if results["reliability"]["high_restart_containers"]:
            opportunities.append({
                "type": "reliability",
                "containers": results["reliability"]["high_restart_containers"],
                "description": "Improve stability of containers with high restart counts"
            })
        
        # Add opportunities to results
        results["optimization_opportunities"] = opportunities
        
        # Categorize containers by image type
        for container in containers:
            image = container.get("image", "unknown")
            
            # Extract the base image type
            if ":" in image:
                image_type = image.split(":")[0]
            else:
                image_type = image
                
            if image_type not in results["container_types"]:
                results["container_types"][image_type] = 0
            results["container_types"][image_type] += 1
        
        # Calculate resource usage metrics
        memory_usages = [c.get("memory_usage", 0) for c in containers if c.get("status") == "running"]
        cpu_usages = [c.get("cpu_usage", 0) for c in containers if c.get("status") == "running"]
        
        if memory_usages:
            results["resource_usage"]["average_memory_usage"] = sum(memory_usages) / len(memory_usages)
        
        if cpu_usages:
            results["resource_usage"]["average_cpu_usage"] = sum(cpu_usages) / len(cpu_usages)
        
        # Identify containers with high resource usage
        for container in containers:
            if container.get("status") != "running":
                continue
                
            # Check for high memory usage (over 75% of average)
            if container.get("memory_usage", 0) > results["resource_usage"]["average_memory_usage"] * 1.75:
                results["resource_usage"]["high_memory_containers"].append({
                    "id": container.get("id", "unknown")[:12],
                    "name": container.get("name", "unknown"),
                    "memory_usage": container.get("memory_usage", 0)
                })
            
            # Check for high CPU usage (over 75% of average)
            if container.get("cpu_usage", 0) > results["resource_usage"]["average_cpu_usage"] * 1.75:
                results["resource_usage"]["high_cpu_containers"].append({
                    "id": container.get("id", "unknown")[:12],
                    "name": container.get("name", "unknown"),
                    "cpu_usage": container.get("cpu_usage", 0)
                })
            
            # Check for idle containers (under 10% of average resource usage)
            if (container.get("memory_usage", 0) < results["resource_usage"]["average_memory_usage"] * 0.1 and
                container.get("cpu_usage", 0) < results["resource_usage"]["average_cpu_usage"] * 0.1):
                results["resource_usage"]["idle_containers"].append({
                    "id": container.get("id", "unknown")[:12],
                    "name": container.get("name", "unknown"),
                    "memory_usage": container.get("memory_usage", 0),
                    "cpu_usage": container.get("cpu_usage", 0)
                })
        
        # Calculate reliability metrics
        restart_counts = [c.get("restart_count", 0) for c in containers]
        
        if restart_counts:
            results["reliability"]["average_restart_count"] = sum(restart_counts) / len(restart_counts)
        
        # Identify containers with high restart counts
        for container in containers:
            # Check for high restart count (over 3x average)
            if (container.get("restart_count", 0) > results["reliability"]["average_restart_count"] * 3 and
                container.get("restart_count", 0) > 3):
                results["reliability"]["high_restart_containers"].append({
                    "id": container.get("id", "unknown")[:12],
                    "name": container.get("name", "unknown"),
                    "restart_count": container.get("restart_count", 0)
                })
        
        # Identify optimization opportunities
        if results["resource_usage"]["high_memory_containers"]:
            results["optimization_opportunities"].append({
                "type": "memory_limit",
                "description": "Set memory limits for high memory containers",
                "containers": [c["name"] for c in results["resource_usage"]["high_memory_containers"]],
                "action": "increase_limits"
            })
        
        if results["resource_usage"]["idle_containers"]:
            results["optimization_opportunities"].append({
                "type": "idle_containers",
                "description": "Consider removing or optimizing idle containers",
                "containers": [c["name"] for c in results["resource_usage"]["idle_containers"]],
                "action": "reduce_resources"
            })
        
        if results["reliability"]["high_restart_containers"]:
            results["optimization_opportunities"].append({
                "type": "reliability",
                "description": "Investigate containers with high restart counts",
                "containers": [c["name"] for c in results["reliability"]["high_restart_containers"]],
                "action": "improve_reliability"
            })
        
        return results
    
    def _generate_recommendations(self, container_analysis: Dict[str, Any], system_metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate intelligent recommendations based on analysis.
        
        Args:
            container_analysis: Container usage analysis results
            system_metrics: Current system metrics
            
        Returns:
            List of recommendation dictionaries
        """
        recommendations = []
        
        # Check for system-level recommendations
        if system_metrics.get("memory_usage", 0) > 80:
            recommendations.append({
                "type": "system",
                "category": "memory",
                "priority": "high",
                "title": "High Memory Usage",
                "description": "System memory usage is over 80%. Consider adding more memory or reducing container memory limits.",
                "actions": [
                    "Add more system memory",
                    "Review and reduce memory limits for containers",
                    "Stop unnecessary containers"
                ]
            })
        
        if system_metrics.get("cpu_usage", 0) > 80:
            recommendations.append({
                "type": "system",
                "category": "cpu",
                "priority": "high",
                "title": "High CPU Usage",
                "description": "System CPU usage is over 80%. Consider adding more CPU resources or optimizing container CPU usage.",
                "actions": [
                    "Add more CPU resources",
                    "Set CPU quotas for high-usage containers",
                    "Optimize applications for better CPU efficiency"
                ]
            })
        
        if system_metrics.get("disk_usage", 0) > 85:
            recommendations.append({
                "type": "system",
                "category": "disk",
                "priority": "high",
                "title": "Disk Space Running Low",
                "description": "Disk usage is over 85%. Consider cleaning up unused images and volumes or adding more storage.",
                "actions": [
                    "Run 'docker system prune' to remove unused data",
                    "Remove unused images with 'docker image prune'",
                    "Clean up unused volumes",
                    "Add more storage space"
                ]
            })
        
        # Check for container-specific recommendations
        for opportunity in container_analysis.get("optimization_opportunities", []):
            if opportunity["type"] == "memory_limit":
                recommendations.append({
                    "type": "container",
                    "category": "resource_management",
                    "priority": "medium",
                    "title": "Memory Limit Optimization",
                    "description": f"Set appropriate memory limits for high memory containers: {', '.join(opportunity['containers'])}",
                    "actions": [
                        "Set memory limits in container configuration",
                        "Use --memory flag when running containers",
                        "Monitor memory usage patterns"
                    ],
                    "affected_containers": opportunity["containers"]
                })
            
            if opportunity["type"] == "idle_containers":
                recommendations.append({
                    "type": "container",
                    "category": "resource_efficiency",
                    "priority": "low",
                    "title": "Idle Container Optimization",
                    "description": f"Optimize or remove idle containers: {', '.join(opportunity['containers'])}",
                    "actions": [
                        "Stop containers when not in use",
                        "Consider using container orchestration for auto-scaling",
                        "Reduce resource allocation for underutilized containers"
                    ],
                    "affected_containers": opportunity["containers"]
                })
            
            if opportunity["type"] == "reliability":
                recommendations.append({
                    "type": "container",
                    "category": "reliability",
                    "priority": "high",
                    "title": "Container Reliability Issues",
                    "description": f"Investigate containers with high restart counts: {', '.join(opportunity['containers'])}",
                    "actions": [
                        "Review container logs for error patterns",
                        "Check for resource constraints causing crashes",
                        "Consider implementing healthchecks",
                        "Adjust restart policies"
                    ],
                    "affected_containers": opportunity["containers"]
                })
        
        # Check for image-specific recommendations
        image_counts = container_analysis.get("container_types", {})
        
        # Look for opportunities to use Alpine or slim images
        for image_type, count in image_counts.items():
            if count > 0 and "alpine" not in image_type and "slim" not in image_type:
                recommendations.append({
                    "type": "image",
                    "category": "optimization",
                    "priority": "medium",
                    "title": "Use Lightweight Images",
                    "description": f"Consider using Alpine or slim variants for {image_type} images to reduce size and improve performance",
                    "actions": [
                        f"Replace '{image_type}' with '{image_type}:alpine' or '{image_type}:slim'",
                        "Rebuild containers with optimized images",
                        "Create custom Dockerfiles with minimal dependencies"
                    ]
                })
        
        # Generate networking recommendations if we have multiple containers
        if container_analysis.get("total_containers", 0) > 2:
            recommendations.append({
                "type": "network",
                "category": "organization",
                "priority": "medium",
                "title": "Use Custom Networks",
                "description": "Create custom bridge networks for container groups to improve isolation and security",
                "actions": [
                    "Create networks with 'docker network create'",
                    "Group related containers on the same network",
                    "Use network aliases for service discovery"
                ]
            })
        
        # Generate compose recommendations for complex setups
        if container_analysis.get("total_containers", 0) > 3:
            recommendations.append({
                "type": "management",
                "category": "orchestration",
                "priority": "high",
                "title": "Use Docker Compose",
                "description": "Consider using Docker Compose to manage your multi-container application",
                "actions": [
                    "Create a docker-compose.yml file",
                    "Define all services, networks, and volumes",
                    "Use 'docker-compose up' to start all services together"
                ]
            })
        
        # Add intelligent container matching recommendations
        templates_to_suggest = self._match_containers_to_templates(container_analysis)
        if templates_to_suggest:
            recommendations.append({
                "type": "templates",
                "category": "best_practices",
                "priority": "medium",
                "title": "Recommended Container Templates",
                "description": "Consider using these pre-configured templates for your container workloads",
                "templates": templates_to_suggest
            })
        
        return recommendations
    
    def _generate_resource_recommendations(self, container_analysis: Dict[str, Any], 
                                         system_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Generate resource allocation recommendations.
        
        Args:
            container_analysis: Container usage analysis results
            system_metrics: Current system metrics
            
        Returns:
            Resource recommendations dictionary
        """
        # Calculate total system capacity and current usage
        total_memory = system_metrics.get("total_memory", 16384)  # Default 16GB if not available
        memory_usage_percent = system_metrics.get("memory_usage", 0)
        cpu_usage_percent = system_metrics.get("cpu_usage", 0)
        
        # Determine appropriate resource profile based on current usage
        resource_profile = "balanced"  # Default profile
        
        if memory_usage_percent > 80 or cpu_usage_percent > 80:
            # System is under high load, be more conservative
            resource_profile = "minimal"
        elif memory_usage_percent < 30 and cpu_usage_percent < 30:
            # System has plenty of resources available
            resource_profile = "performance"
        
        # Fine-tune profile based on specific usage patterns
        if memory_usage_percent > 60 and cpu_usage_percent < 40:
            # Memory constrained but CPU available
            resource_profile = "memory-optimized"
        elif cpu_usage_percent > 60 and memory_usage_percent < 40:
            # CPU constrained but memory available
            resource_profile = "cpu-optimized"
        
        # Get profile details
        profile_details = self.RESOURCE_PROFILES.get(resource_profile, self.RESOURCE_PROFILES["balanced"])
        
        # Calculate available memory
        used_memory = (memory_usage_percent / 100) * total_memory
        available_memory = total_memory - used_memory
        
        # Calculate recommended values
        recommended_cpu = profile_details["cpu"]
        recommended_memory = profile_details["memory"]
        recommended_memory_reservation = profile_details["memory_reservation"]
        
        # Adjust based on container analysis
        if container_analysis.get("resource_usage", {}).get("high_memory_containers", []):
            # Increase memory recommendations for high memory containers
            if resource_profile in ["minimal", "balanced"]:
                resource_profile = "memory-optimized"
                profile_details = self.RESOURCE_PROFILES[resource_profile]
                recommended_memory = profile_details["memory"]
                recommended_memory_reservation = profile_details["memory_reservation"]
        
        if container_analysis.get("resource_usage", {}).get("high_cpu_containers", []):
            # Increase CPU recommendations for high CPU containers
            if resource_profile in ["minimal", "balanced"]:
                resource_profile = "cpu-optimized"
                profile_details = self.RESOURCE_PROFILES[resource_profile]
                recommended_cpu = profile_details["cpu"]
        
        # Format available memory
        if available_memory > 1024:
            available_memory_str = f"{available_memory/1024:.1f}g"
        else:
            available_memory_str = f"{available_memory:.0f}m"
        
        # Return resource recommendations
        return {
            "resource_profile": resource_profile,
            "profile_details": profile_details,
            "recommended_cpu": recommended_cpu,
            "recommended_memory": recommended_memory,
            "recommended_memory_reservation": recommended_memory_reservation,
            "available_memory": available_memory_str,
            "system_metrics": {
                "memory_usage_percent": memory_usage_percent,
                "cpu_usage_percent": cpu_usage_percent,
                "total_memory": total_memory
            }
        }
    
    def _match_containers_to_templates(self, container_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Match current container setup with optimal templates.
        
        Args:
            container_analysis: Container usage analysis results
            
        Returns:
            List of matching templates with confidence scores
        """
        matches = []
        image_counts = container_analysis.get("container_types", {})
        
        # Check for web server patterns
        if any(image_type in ["nginx", "httpd", "apache"] for image_type in image_counts.keys()):
            template = self.APPLICATION_TEMPLATES["web_server"].copy()
            template["confidence"] = 0.9
            template["reason"] = "Detected web server containers"
            matches.append(template)
        
        # Check for database patterns
        if any(image_type in ["postgres", "mysql", "mariadb", "mongo"] for image_type in image_counts.keys()):
            template = self.APPLICATION_TEMPLATES["database"].copy()
            template["confidence"] = 0.9
            template["reason"] = "Detected database containers"
            matches.append(template)
        
        # Check for application server patterns
        if any(image_type in ["node", "python", "ruby", "php"] for image_type in image_counts.keys()):
            template = self.APPLICATION_TEMPLATES["app_server"].copy()
            template["confidence"] = 0.8
            template["reason"] = "Detected application server containers"
            matches.append(template)
        
        # Check for cache patterns
        if any(image_type in ["redis", "memcached"] for image_type in image_counts.keys()):
            template = self.APPLICATION_TEMPLATES["cache"].copy()
            template["confidence"] = 0.9
            template["reason"] = "Detected cache service containers"
            matches.append(template)
        
        # Check for message queue patterns
        if any(image_type in ["rabbitmq", "kafka", "activemq"] for image_type in image_counts.keys()):
            template = self.APPLICATION_TEMPLATES["message_queue"].copy()
            template["confidence"] = 0.9
            template["reason"] = "Detected message queue containers"
            matches.append(template)
        
        # If no matches found, suggest based on running container count
        if not matches and container_analysis.get("total_containers", 0) > 0:
            # Suggest web server by default for single container setups
            if container_analysis.get("total_containers", 0) <= 2:
                template = self.APPLICATION_TEMPLATES["web_server"].copy()
                template["confidence"] = 0.6
                template["reason"] = "Basic recommendation for simple setup"
                matches.append(template)
            else:
                # For multi-container setups, suggest a balanced set of services
                for template_id in ["web_server", "database", "app_server"]:
                    template = self.APPLICATION_TEMPLATES[template_id].copy()
                    template["confidence"] = 0.7
                    template["reason"] = "Recommended for multi-container setup"
                    matches.append(template)
        
        return matches
    

    
    def analyze_and_recommend(self) -> Dict[str, Any]:
        """Perform complete analysis and generate recommendations.
        
        Returns:
            Dictionary containing analysis results and recommendations
        """
        # Check if we have a cached recent analysis (less than 5 minutes old)
        current_time = time.time()
        if (self.recommendations_cache and 
            current_time - self.last_analysis_time < 300):
            return self.recommendations_cache
        
        # Get current container and system data
        containers = self._get_containers_data()
        system_metrics = self._get_system_metrics()
        
        # Perform analysis
        container_analysis = self._analyze_container_usage(containers)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(container_analysis, system_metrics)
        resource_recommendations = self._generate_resource_recommendations(container_analysis, system_metrics)
        
        # Store historical data
        self.container_history.append({
            "timestamp": current_time,
            "container_count": len(containers),
            "running_count": sum(1 for c in containers if c.get("status") == "running")
        })
        
        self.system_metrics_history.append({
            "timestamp": current_time,
            "cpu_usage": system_metrics.get("cpu_usage", 0),
            "memory_usage": system_metrics.get("memory_usage", 0),
            "disk_usage": system_metrics.get("disk_usage", 0)
        })
        
        # Save historical data
        self._save_historical_data()
        
        # Prepare complete results
        result = {
            "timestamp": current_time,
            "analysis": {
                "container_analysis": container_analysis,
                "system_metrics": system_metrics
            },
            "recommendations": recommendations,
            "resource_recommendations": resource_recommendations,
            "container_templates": list(self.APPLICATION_TEMPLATES.values()),
        }
        
        # Cache the results
        self.recommendations_cache = result
        self.last_analysis_time = current_time
        
        return result
    
    def get_template_details(self, template_id: str) -> Optional[Dict[str, Any]]:
        """Get details for a specific application template.
        
        Args:
            template_id: ID of the template to retrieve
            
        Returns:
            Template details dictionary or None if not found
        """
        if template_id in self.APPLICATION_TEMPLATES:
            return self.APPLICATION_TEMPLATES[template_id]
        return None
    
    def generate_template(self, template_id: str, target_dir: str, 
                      custom_params: Optional[Dict[str, Any]] = None) -> Tuple[bool, Optional[str]]:
        """Generate container configuration from a template.
        
        Args:
            template_id: ID of the template to use
            target_dir: Directory to create the template in
            custom_params: Optional custom parameters to override template defaults
            
        Returns:
            Tuple of (success, error_message)
        """
        if template_id not in self.APPLICATION_TEMPLATES:
            return False, f"Template '{template_id}' not found"
        
        template = self.APPLICATION_TEMPLATES[template_id].copy()
        
        # Override with custom parameters if provided
        if custom_params:
            for key, value in custom_params.items():
                if key in template:
                    template[key] = value
        
        # Ensure target directory exists
        try:
            os.makedirs(target_dir, exist_ok=True)
        except Exception as e:
            return False, f"Failed to create directory: {e}"
        
        # Create docker-compose.yml
        compose_file = os.path.join(target_dir, "docker-compose.yml")
        try:
            with open(compose_file, "w") as f:
                f.write(self._generate_compose_file(template))
        except Exception as e:
            return False, f"Failed to create docker-compose.yml: {e}"
        
        # Create .env file with default values
        env_file = os.path.join(target_dir, ".env")
        try:
            with open(env_file, "w") as f:
                f.write(self._generate_env_file(template))
        except Exception as e:
            return False, f"Failed to create .env file: {e}"
        
        # Create README.md with instructions
        readme_file = os.path.join(target_dir, "README.md")
        try:
            with open(readme_file, "w") as f:
                f.write(self._generate_readme(template))
        except Exception as e:
            return False, f"Failed to create README.md: {e}"
        
        return True, None
    
    def _generate_compose_file(self, template: Dict[str, Any]) -> str:
        """Generate a docker-compose.yml file based on template.
        
        Args:
            template: Template dictionary
            
        Returns:
            docker-compose.yml content as string
        """
        # Get resource profile
        resource_profile = self.RESOURCE_PROFILES[template.get("resource_profile", "balanced")]
        
        service_name = template.get("name", "service").lower().replace(" ", "_")
        
        compose = f"""version: '3.8'

services:
  {service_name}:
    image: {template.get("base_image", "alpine:latest")}
    container_name: {service_name}
    restart: unless-stopped
"""
        
        # Add ports
        if template.get("ports"):
            compose += "    ports:\n"
            for port in template.get("ports", []):
                compose += f"      - \"{port}:{port}\"\n"
        
        # Add volumes
        if template.get("volumes"):
            compose += "    volumes:\n"
            for volume in template.get("volumes", []):
                volume_name = volume.strip("/").replace("/", "_")
                compose += f"      - {service_name}_{volume_name}:{volume}\n"
        
        # Add environment variables
        if template.get("env_vars"):
            compose += "    environment:\n"
            for env_var in template.get("env_vars", []):
                compose += f"      - {env_var}=${{var:{env_var}}}\n"
        
        # Add resource limits
        compose += "    deploy:\n"
        compose += "      resources:\n"
        compose += "        limits:\n"
        compose += f"          cpus: '{resource_profile.get('cpu', 1.0)}'\n"
        compose += f"          memory: {resource_profile.get('memory', '512m')}\n"
        compose += "        reservations:\n"
        compose += f"          memory: {resource_profile.get('memory_reservation', '256m')}\n"
        
        # Add networks
        if template.get("networks"):
            compose += "    networks:\n"
            for network in template.get("networks", []):
                compose += f"      - {network}\n"
        
        # Add networks section
        if template.get("networks"):
            compose += "\nnetworks:\n"
            for network in template.get("networks", []):
                compose += f"  {network}:\n"
                compose += "    driver: bridge\n"
        
        # Add volumes section
        if template.get("volumes"):
            compose += "\nvolumes:\n"
            for volume in template.get("volumes", []):
                volume_name = volume.strip("/").replace("/", "_")
                compose += f"  {service_name}_{volume_name}:\n"
                compose += "    driver: local\n"
        
        return compose
    
    def _generate_env_file(self, template: Dict[str, Any]) -> str:
        """Generate a .env file with default values.
        
        Args:
            template: Template dictionary
            
        Returns:
            .env file content as string
        """
        env_content = "# Environment variables for docker-compose.yml\n"
        env_content += f"# Template: {template.get('name', 'Unknown')}\n\n"
        
        # Add environment variables with default values
        for env_var in template.get("env_vars", []):
            # Generate appropriate default values based on variable name
            if "PORT" in env_var:
                env_content += f"{env_var}=8080\n"
            elif "PASSWORD" in env_var:
                env_content += f"{env_var}=changeme123\n"
            elif "USER" in env_var:
                env_content += f"{env_var}=admin\n"
            elif "HOST" in env_var:
                env_content += f"{env_var}=localhost\n"
            elif "DB" in env_var or "DATABASE" in env_var:
                env_content += f"{env_var}=app_db\n"
            elif "URL" in env_var:
                env_content += f"{env_var}=http://localhost:8080\n"
            elif "ENV" in env_var:
                env_content += f"{env_var}=development\n"
            else:
                env_content += f"{env_var}=default_value\n"
        
        return env_content
    
    def _generate_readme(self, template: Dict[str, Any]) -> str:
        """Generate a README.md file with instructions.
        
        Args:
            template: Template dictionary
            
        Returns:
            README.md content as string
        """
        service_name = template.get("name", "service")
        
        readme = f"""# {service_name} Container

This is a Docker container configuration for {service_name} generated by Docker Service Manager's AI recommendation system.

## Resource Profile

This container uses the "{template.get('resource_profile', 'balanced')}" resource profile:

- CPU: {self.RESOURCE_PROFILES[template.get('resource_profile', 'balanced')]['cpu']} cores
- Memory: {self.RESOURCE_PROFILES[template.get('resource_profile', 'balanced')]['memory']}
- Memory Reservation: {self.RESOURCE_PROFILES[template.get('resource_profile', 'balanced')]['memory_reservation']}

## Usage

1. Make sure Docker and Docker Compose are installed on your system
2. Review and edit values in the `.env` file
3. Start the container:
   ```
   docker-compose up -d
   ```
4. Check container status:
   ```
   docker-compose ps
   ```
5. View logs:
   ```
   docker-compose logs -f
   ```

## Configuration

The container exposes the following ports:
"""
        
        # Add port information
        for port in template.get("ports", []):
            readme += f"- Port {port}\n"
        
        # Add volume information
        if template.get("volumes"):
            readme += "\nThe container uses the following volumes:\n"
            for volume in template.get("volumes", []):
                readme += f"- {volume}\n"
        
        # Add environment variable information
        if template.get("env_vars"):
            readme += "\nThe container requires the following environment variables:\n"
            for env_var in template.get("env_vars", []):
                readme += f"- {env_var}\n"
        
        # Add network information
        if template.get("networks"):
            readme += "\nThe container uses the following networks:\n"
            for network in template.get("networks", []):
                readme += f"- {network}\n"
        
        # Add tags
        if template.get("tags"):
            readme += "\nTags: " + ", ".join(template.get("tags", [])) + "\n"
        
        readme += """
## Customization

You can customize this container by editing the docker-compose.yml file and the .env file according to your needs.
"""
        
        return readme