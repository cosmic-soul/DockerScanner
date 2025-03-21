# Docker Service Manager

A cross-platform Python CLI tool for managing Docker daemon services on Linux, macOS, and Windows systems.

## Features

- Cross-platform Docker service management (Linux, macOS, Windows)
- Start, stop, restart Docker services
- Enable/disable Docker services at boot
- Check service and socket status
- Comprehensive system information
- Docker container listing
- Administrative privilege validation
- Clear console output with status messages
- Demo mode for testing in environments without Docker
- Interactive menu-based interface for easier use
- Quick launch templates for common development environments
- Modular, extensible architecture
- Contextual onboarding for new users
- One-click system health reports with detailed metrics
- Visual performance and resource monitoring with ASCII graphs
- Health report recommendations based on system status

## Requirements

- Python 3.x
- docker-py (Python Docker SDK)
- tabulate library

## Installation

### Easy Installation

#### Windows
1. Download the latest release from the [Releases page](https://github.com/your-username/docker-service-manager/releases)
2. Run the `Docker_Service_Manager_Setup.exe` installer
3. Follow the on-screen instructions

Alternatively, if you have Python installed:
```bash
# Run the Windows installer batch file
install_windows.bat
```

#### Linux/macOS
```bash
# Make the installer script executable
chmod +x install_unix.sh

# Run the installer
./install_unix.sh
```

### Manual Installation

If you prefer to install manually:

```bash
# Install from PyPI
pip install docker-service-manager

# Or install from source
pip install .
```

### Development Installation

For development, you can install in editable mode:

```bash
pip install -e .
```

## Usage

### Basic Usage

```bash
python docker_service_manager.py [command] [action]
```

### Commands

- `service`: Manage Docker service (start, stop, restart, status, enable, disable)
- `socket`: Manage Docker socket (start, stop, status, enable, disable)
- `containers`: List Docker containers
- `template`: Manage development environment templates (list, create, launch)
- `info`: Display Docker system information
- `version`: Show tool version
- `health`: Generate a comprehensive system health report

### Demo Mode

Run in demo mode to simulate Docker responses without an actual Docker installation:

```bash
python docker_service_manager.py --demo [command] [action]
```

This is useful for:
- Testing the tool in environments where Docker isn't available
- Training or demonstration purposes
- Development testing without affecting a real Docker installation

### Interactive Mode

Run the tool in interactive mode for a menu-based interface:

```bash
python docker_service_manager.py --interactive
# or
python docker_service_manager.py -i
```

You can also use demo mode with interactive mode:

```bash
python docker_service_manager.py --interactive --demo
```

#### Contextual Onboarding

The interactive mode includes an enhanced contextual onboarding system for new users:

- **Welcome Screen**: First-time users see a detailed welcome message with key features, navigation tips, and demo mode information
- **First-Time Section Guidance**: When you navigate to a new section for the first time, you'll receive a brief explanation of what that section does and recommended first steps
- **Contextual Help**: Press `?` at any menu to get detailed context-specific help about available commands and options
- **Complete Help Directory**: Press `h` to browse all available help topics through an interactive menu
- **Adaptive Contextual Tips**: Smart suggestions appear based on your current menu and actions - these suggestions evolve as you gain experience
- **Action-Specific Guidance**: Specific tips appear after taking actions to suggest logical next steps
- **Progress Tracking**: The system remembers which help topics you've already explored so you don't see redundant information

The onboarding system stores a minimal user profile in ~/.docker_manager/config.json to track your progress, ensuring help is available when needed without becoming intrusive as you gain familiarity with the tool.

### Examples

Check Docker service status:
```bash
python docker_service_manager.py service status
```

List containers in demo mode:
```bash
python docker_service_manager.py --demo containers
```

View system information in demo mode:
```bash
python docker_service_manager.py --demo info
```

List available templates in demo mode:
```bash
python docker_service_manager.py --demo template list
```

Create a LAMP stack environment:
```bash
python docker_service_manager.py --demo template create lamp --directory ~/docker-environments/lamp
```

Launch a WordPress environment:
```bash
python docker_service_manager.py --demo template launch wordpress --directory ~/docker-environments/wordpress
```

### Development Templates

The tool includes predefined templates for common development environments:

- **LAMP Stack**: Linux, Apache, MySQL, PHP
  - Web server (PHP 7.4 with Apache)
  - MySQL 5.7 database
  - PHPMyAdmin for database management

- **MEAN Stack**: MongoDB, Express, Angular, Node.js
  - Node.js backend (Express.js)
  - Angular frontend
  - MongoDB database

- **WordPress**: Complete WordPress development environment
  - WordPress latest version
  - MySQL 5.7 database
  - PHPMyAdmin for database management

All templates include:
- Docker Compose configuration
- Persistent volumes for data
- Demo index pages and README files
- Port mappings for easy local access

## Project Structure

The project has been refactored into a modular structure:

```
docker_manager/
├── __init__.py             # Package initialization
├── core/                   # Core functionality
│   ├── __init__.py
│   ├── service_manager.py  # Main service manager class
│   └── container_logs.py   # Container logs functionality
├── ui/                     # User interface components
│   ├── __init__.py
│   ├── cli.py              # Command-line interface
│   ├── interactive.py      # Interactive console UI
│   ├── onboarding.py       # Contextual help and onboarding system
│   └── tui/                # Terminal User Interface components
│       ├── __init__.py
│       └── main.py         # TUI implementation (future)
├── utils/                  # Utility functions
│   ├── __init__.py
│   ├── display.py          # Display and formatting utilities
│   └── system.py           # System-related utilities
└── templates/              # Templates and extensions
    ├── __init__.py
    ├── command_template.py # Template for adding new commands
    └── environment_templates.py # Development environment templates
```

## Extending the Tool

### Adding New Commands

You can extend the tool with new commands by:

1. Creating a new command module based on the template in `docker_manager/templates/command_template.py`
2. Adding the command to the CLI parser in `docker_manager/ui/cli.py`
3. Adding a menu entry in the interactive console in `docker_manager/ui/interactive.py`

### Adding Custom Development Templates

You can add your own development environment templates:

1. Create a new template class in `docker_manager/templates/environment_templates.py` by extending the `EnvironmentTemplate` base class
2. Define your Docker Compose configuration and any additional files needed
3. Register your template in the `TemplateManager._register_templates()` method
4. Your template will automatically be available in both CLI and interactive modes

### Customizing the Onboarding System

You can extend or modify the onboarding system to add custom help topics or contextual tips:

1. Add new help topics by creating appropriate methods (like `_show_new_feature_help()`) in the `OnboardingManager` class 
2. Add entries to the `topics` dictionary in the `show_topic()` method to make them accessible
3. Add new section-specific first-time help in the `section_help` dictionary in `show_first_time_section_help()`
4. Add new contextual suggestions in the `suggestions` dictionary in the `maybe_show_suggestion()` method
5. The onboarding system will automatically track which topics users have seen and which sections they've visited
6. All help content is organized by menu/section and action for easy contextual navigation

Example for creating a new template:

```python
class RubyOnRailsTemplate(EnvironmentTemplate):
    """Ruby on Rails development environment template."""
    
    def __init__(self, demo_mode: bool = False):
        """Initialize Rails template."""
        super().__init__(
            name="Ruby on Rails",
            description="Ruby on Rails with PostgreSQL",
            demo_mode=demo_mode
        )
        
        # Define template files
        self.files = {
            "docker-compose.yml": """version: '3'
# Your Docker Compose configuration here
""",
            "README.md": """# Ruby on Rails Environment
# Documentation for your template
"""
        }
```
