"""
Container lifecycle visualization for Docker service manager.

This module provides animated visualization of Docker container
states and transitions using terminal-based animations.
"""
import os
import sys
import time
import threading
from typing import List, Dict, Any, Optional, Callable, Union, Tuple

try:
    import blessed
    BLESSED_AVAILABLE = True
except ImportError:
    BLESSED_AVAILABLE = False

try:
    import docker
    from docker.errors import DockerException
    DOCKER_AVAILABLE = True
except ImportError:
    DOCKER_AVAILABLE = False

from ..utils.display import COLORS, get_terminal_size, print_status, print_section

# Container states with their visual representation
CONTAINER_STATES = {
    'created': ('○', COLORS['CYAN']),   # Circle
    'running': ('●', COLORS['GREEN']),  # Filled circle
    'paused': ('◑', COLORS['YELLOW']),  # Half-filled circle
    'restarting': ('◎', COLORS['MAGENTA']), # Circle with dot
    'exited': ('◌', COLORS['RED']),     # Empty circle
    'dead': ('⊗', COLORS['RED']),       # Crossed circle
    'removing': ('⌛', COLORS['YELLOW']), # Hourglass
    'unknown': ('?', COLORS['YELLOW'])  # Question mark
}

# Animation frames for transitions
TRANSITION_FRAMES = {
    'start': ['○', '◔', '◑', '◕', '●'],  # Empty to full
    'stop': ['●', '◕', '◑', '◔', '○'],   # Full to empty
    'pause': ['●', '◕', '◑'],           # Full to half
    'unpause': ['◑', '◕', '●'],         # Half to full
    'restart': ['●', '◌', '◎', '○', '◔', '◑', '◕', '●'],  # Full cycle
    'remove': ['◌', '⊝', '⊘', '⊗']      # Empty to crossed
}

class ContainerVisualizer:
    """Visualize Docker container states and transitions with terminal animations."""
    
    def __init__(self, demo_mode: bool = False):
        """Initialize container visualizer.
        
        Args:
            demo_mode: Whether to use demo mode with simulated responses
        """
        self.demo_mode = demo_mode
        self.term = blessed.Terminal() if BLESSED_AVAILABLE else None
        self.running = False
        self.containers = []
        self.animation_thread = None
        self.lock = threading.Lock()
        
    def _check_requirements(self) -> bool:
        """Check if required dependencies are available.
        
        Returns:
            True if all dependencies are available, False otherwise
        """
        missing = []
        
        if not BLESSED_AVAILABLE:
            missing.append("blessed")
            
        if not DOCKER_AVAILABLE and not self.demo_mode:
            missing.append("docker")
            
        if missing:
            print_status(f"Missing required dependencies: {', '.join(missing)}", "error")
            print(f"Install with: pip install {' '.join(missing)}")
            return False
            
        return True
        
    def _get_containers(self) -> List[Dict[str, Any]]:
        """Get container data for visualization.
        
        Returns:
            List of container dictionaries with relevant information
        """
        if self.demo_mode:
            # Create sample containers for demonstration
            return [
                {'id': 'abc123', 'name': 'demo-webserver', 'state': 'running', 'image': 'nginx:latest'},
                {'id': 'def456', 'name': 'demo-database', 'state': 'running', 'image': 'mysql:8.0'},
                {'id': 'ghi789', 'name': 'demo-redis', 'state': 'restarting', 'image': 'redis:alpine'},
                {'id': 'jkl012', 'name': 'demo-backup', 'state': 'exited', 'image': 'alpine:latest'}
            ]
            
        # Connect to Docker for real container data
        try:
            client = docker.from_env()
            containers = client.containers.list(all=True)
            
            return [
                {
                    'id': container.short_id,
                    'name': container.name,
                    'state': container.status,
                    'image': container.image.tags[0] if container.image.tags else "none"
                }
                for container in containers
            ]
        except Exception as e:
            print_status(f"Error connecting to Docker: {e}", "error")
            return []
            
    def _draw_container(self, container: Dict[str, Any], x: int, y: int) -> None:
        """Draw a container with its state.
        
        Args:
            container: Container data dictionary
            x: X-coordinate for drawing
            y: Y-coordinate for drawing
        """
        if not self.term:
            return
            
        state = container['state']
        symbol, color = CONTAINER_STATES.get(state, CONTAINER_STATES['unknown'])
        
        # Draw the container with color based on its state
        name_display = container['name'][:20]  # Limit name length
        with self.lock:
            print(self.term.move(y, x) + 
                  color + symbol + COLORS['RESET'] + ' ' + 
                  name_display + ' ' + 
                  f"({state})")
            
    def _animate_transition(self, container_id: str, transition: str) -> None:
        """Animate container state transition.
        
        Args:
            container_id: ID of the container to animate
            transition: Type of transition ('start', 'stop', etc.)
        """
        if not self.term or not self.running:
            return
            
        # Find the container in our list
        container_index = None
        for i, container in enumerate(self.containers):
            if container['id'] == container_id:
                container_index = i
                break
                
        if container_index is None:
            return
            
        # Get position for animation
        width, _ = get_terminal_size()
        x = 3
        y = 5 + container_index
        
        # Get animation frames
        frames = TRANSITION_FRAMES.get(transition, [])
        
        # Animate the transition
        name_display = self.containers[container_index]['name'][:20]
        for frame in frames:
            if not self.running:
                break
                
            with self.lock:
                color = COLORS['YELLOW']  # Use yellow for transitions
                print(self.term.move(y, x) + 
                      color + frame + COLORS['RESET'] + ' ' + 
                      name_display + ' ' + 
                      f"({transition}...)")
                      
            time.sleep(0.2)
            
    def _update_containers_loop(self) -> None:
        """Background loop to update container states."""
        if not self.term:
            return
            
        previous_states = {}
        
        # Clear screen once when starting
        with self.lock:
            print(self.term.clear())
            print(self.term.move(1, 1) + f"{COLORS['BOLD']}Docker Container Lifecycle Visualization{COLORS['RESET']}")
            print(self.term.move(2, 1) + "Press 'q' to exit, 'r' to refresh")
            print(self.term.move(3, 1) + "=" * (get_terminal_size()[0] - 2))
        
        while self.running:
            # Get current containers
            self.containers = self._get_containers()
            
            # Check for state changes and animate transitions
            for i, container in enumerate(self.containers):
                container_id = container['id']
                current_state = container['state']
                
                # If we have a previous state and it changed, animate transition
                if container_id in previous_states and previous_states[container_id] != current_state:
                    old_state = previous_states[container_id]
                    
                    # Determine transition type based on state change
                    transition = None
                    if old_state == 'exited' and current_state == 'running':
                        transition = 'start'
                    elif old_state == 'running' and current_state == 'exited':
                        transition = 'stop'
                    elif old_state == 'running' and current_state == 'paused':
                        transition = 'pause'
                    elif old_state == 'paused' and current_state == 'running':
                        transition = 'unpause'
                    elif current_state == 'restarting':
                        transition = 'restart'
                    
                    if transition:
                        self._animate_transition(container_id, transition)
                
                # Draw the container in its current state
                self._draw_container(container, 3, 5 + i)
                
                # Save state for next comparison
                previous_states[container_id] = current_state
            
            # Display instructions at the bottom
            with self.lock:
                print(self.term.move(5 + len(self.containers) + 2, 1) + 
                      f"{COLORS['CYAN']}Legend:{COLORS['RESET']} " +
                      f"{COLORS['GREEN']}● Running{COLORS['RESET']} " +
                      f"{COLORS['YELLOW']}◑ Paused{COLORS['RESET']} " +
                      f"{COLORS['RED']}◌ Exited{COLORS['RESET']} " +
                      f"{COLORS['MAGENTA']}◎ Restarting{COLORS['RESET']} " +
                      f"{COLORS['RED']}⊗ Dead{COLORS['RESET']}")
            
            # In demo mode, randomly simulate state changes for demonstration
            if self.demo_mode and self.containers:
                time.sleep(1.5)  # Longer delay between state changes in demo mode
                
                # Occasionally simulate a state change in demo mode
                # (This is just for demonstration, in real mode we get actual changes from Docker)
                if len(self.containers) > 0 and self.running and self.demo_mode:
                    import random
                    # Choose a random container and simulate a state change every few cycles
                    if random.random() < 0.3:  # 30% chance of state change
                        container_idx = random.randint(0, len(self.containers) - 1)
                        container = self.containers[container_idx]
                        current_state = container['state']
                        
                        # Determine a random state transition
                        possible_transitions = []
                        if current_state == 'running':
                            possible_transitions = ['exited', 'paused', 'restarting']
                        elif current_state == 'exited':
                            possible_transitions = ['running']
                        elif current_state == 'paused':
                            possible_transitions = ['running']
                        elif current_state == 'restarting':
                            possible_transitions = ['running']
                            
                        if possible_transitions:
                            new_state = random.choice(possible_transitions)
                            
                            # Determine transition type
                            transition = None
                            if current_state == 'exited' and new_state == 'running':
                                transition = 'start'
                            elif current_state == 'running' and new_state == 'exited':
                                transition = 'stop'
                            elif current_state == 'running' and new_state == 'paused':
                                transition = 'pause'
                            elif current_state == 'paused' and new_state == 'running':
                                transition = 'unpause'
                            elif new_state == 'restarting':
                                transition = 'restart'
                            
                            # Animate the transition
                            if transition:
                                self._animate_transition(container['id'], transition)
                                
                            # Update the container state for next cycle
                            self.containers[container_idx]['state'] = new_state
                            previous_states[container['id']] = new_state
            else:
                # Normal mode - wait shorter time between updates
                time.sleep(1)
                
    def show_visualization(self) -> bool:
        """Show animated visualization of container states.
        
        Returns:
            True if visualization was displayed successfully, False otherwise
        """
        # Check dependencies
        if not self._check_requirements():
            return False
            
        if not self.term:
            print_status("Blessed library is required for visualization", "error")
            return False
            
        # Start visualization loop
        self.running = True
        
        try:
            # Start update loop in background thread
            self.animation_thread = threading.Thread(target=self._update_containers_loop)
            self.animation_thread.daemon = True
            self.animation_thread.start()
            
            # Main input loop
            with self.term.cbreak(), self.term.hidden_cursor():
                while self.running:
                    key = self.term.inkey(timeout=0.5)
                    
                    if key == 'q':  # Quit
                        self.running = False
                        break
                    elif key == 'r':  # Refresh
                        with self.lock:
                            print(self.term.clear())
                            print(self.term.move(1, 1) + f"{COLORS['BOLD']}Docker Container Lifecycle Visualization{COLORS['RESET']}")
                            print(self.term.move(2, 1) + "Press 'q' to exit, 'r' to refresh")
                            print(self.term.move(3, 1) + "=" * (get_terminal_size()[0] - 2))
        except KeyboardInterrupt:
            pass
        finally:
            # Clean up
            self.running = False
            if self.animation_thread:
                self.animation_thread.join(1.0)  # Wait for animation to stop
                
            # Ensure cursor is visible and screen is cleared
            if self.term:
                print(self.term.normal + self.term.clear())
                
        return True
        
    def show_simple_visualization(self) -> bool:
        """Show a simplified version of the visualization without animation.
        
        This is a fallback for systems without blessed or with limited terminal support.
        
        Returns:
            True if visualization was displayed successfully, False otherwise
        """
        # Get containers
        containers = self._get_containers()
        
        if not containers:
            print_status("No containers found", "warning", demo_mode=self.demo_mode)
            return True
            
        # Display containers with their states
        print_section("Container States")
        
        for container in containers:
            state = container['state']
            symbol, color = CONTAINER_STATES.get(state, CONTAINER_STATES['unknown'])
            
            # Display container with colored state symbol
            print(f"{color}{symbol}{COLORS['RESET']} {container['name']} ({state}) - {container['image']}")
            
        # Display legend
        print("\nLegend:")
        print(f"{COLORS['GREEN']}●{COLORS['RESET']} Running | " +
              f"{COLORS['YELLOW']}◑{COLORS['RESET']} Paused | " +
              f"{COLORS['RED']}◌{COLORS['RESET']} Exited | " +
              f"{COLORS['MAGENTA']}◎{COLORS['RESET']} Restarting | " +
              f"{COLORS['RED']}⊗{COLORS['RESET']} Dead")
              
        return True