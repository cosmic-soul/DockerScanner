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

## Requirements

- Python 3.x
- docker-py (Python Docker SDK)
- tabulate library

## Installation

1. Install required Python packages:

```bash
pip install docker tabulate
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
- `info`: Display Docker system information
- `version`: Show tool version

### Demo Mode

Run in demo mode to simulate Docker responses without an actual Docker installation:

```bash
python docker_service_manager.py --demo [command] [action]
```

This is useful for:
- Testing the tool in environments where Docker isn't available
- Training or demonstration purposes
- Development testing without affecting a real Docker installation

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
