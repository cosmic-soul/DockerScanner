"""
Environment templates for quick launching common development stacks.

This module provides predefined templates for common development environments
that can be quickly launched using Docker Compose.
"""
import os
import sys
import tempfile
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

from ..utils.display import print_status, print_section, COLORS


class EnvironmentTemplate:
    """Base class for environment templates."""
    
    def __init__(self, name: str, description: str, demo_mode: bool = False):
        """Initialize environment template.
        
        Args:
            name: Template name
            description: Template description
            demo_mode: Whether to use demo mode with simulated responses
        """
        self.name = name
        self.description = description
        self.demo_mode = demo_mode
        self.files: Dict[str, str] = {}  # Filename: content
        
    def get_files(self) -> Dict[str, str]:
        """Get template files.
        
        Returns:
            Dictionary of filename: content mappings
        """
        return self.files
        
    def generate(self, target_dir: str) -> bool:
        """Generate template files in target directory.
        
        Args:
            target_dir: Directory to write template files
            
        Returns:
            True if successful, False otherwise
        """
        if self.demo_mode:
            print_status(f"DEMO MODE: Simulating template generation for {self.name}", "info", demo_mode=True)
            return True
            
        try:
            # Create target directory if it doesn't exist
            target_path = Path(target_dir)
            target_path.mkdir(parents=True, exist_ok=True)
            
            # Write template files
            for filename, content in self.files.items():
                file_path = target_path / filename
                with open(file_path, 'w') as f:
                    f.write(content)
                    
            return True
        except Exception as e:
            print_status(f"Error generating template: {str(e)}", "error", demo_mode=self.demo_mode)
            return False
            
    def launch(self, target_dir: str) -> bool:
        """Launch the environment using Docker Compose.
        
        Args:
            target_dir: Directory containing template files
            
        Returns:
            True if successful, False otherwise
        """
        if self.demo_mode:
            print_status(f"DEMO MODE: Simulating launch of {self.name} environment", "info", demo_mode=True)
            print(f"\n{COLORS['CYAN']}Starting containers...{COLORS['RESET']}")
            for i in range(3):
                print(f"Creating network... {'done' if i >= 1 else 'working'}")
                print(f"Creating volume... {'done' if i >= 2 else 'working'}")
                print(f"Starting services... {'done' if i >= 3 else 'working'}")
                if i < 2:
                    print("\033[3A", end="")
                    sys.stdout.flush()
                    import time
                    time.sleep(1)
            print(f"\n{COLORS['GREEN']}Environment started successfully!{COLORS['RESET']}")
            print(f"\n{COLORS['YELLOW']}Access your application at:{COLORS['RESET']} http://localhost:8080")
            return True
            
        try:
            # Check if docker-compose.yml exists
            compose_file = os.path.join(target_dir, "docker-compose.yml")
            if not os.path.exists(compose_file):
                print_status("docker-compose.yml not found in target directory", "error", demo_mode=self.demo_mode)
                return False
                
            # Launch environment using docker-compose up -d
            import subprocess
            result = subprocess.run(
                ["docker-compose", "up", "-d"], 
                cwd=target_dir,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print_status("Environment launched successfully", "ok", demo_mode=self.demo_mode)
                return True
            else:
                print_status(f"Failed to launch environment: {result.stderr}", "error", demo_mode=self.demo_mode)
                return False
        except Exception as e:
            print_status(f"Error launching environment: {str(e)}", "error", demo_mode=self.demo_mode)
            return False


class LAMPTemplate(EnvironmentTemplate):
    """LAMP (Linux, Apache, MySQL, PHP) stack template."""
    
    def __init__(self, demo_mode: bool = False):
        """Initialize LAMP template.
        
        Args:
            demo_mode: Whether to use demo mode with simulated responses
        """
        super().__init__(
            name="LAMP Stack",
            description="Linux, Apache, MySQL, PHP development environment",
            demo_mode=demo_mode
        )
        
        # Define template files
        self.files = {
            "docker-compose.yml": """version: '3'

services:
  web:
    image: php:7.4-apache
    ports:
      - "8080:80"
    volumes:
      - ./www:/var/www/html
    depends_on:
      - db
    environment:
      - MYSQL_HOST=db
      - MYSQL_USER=lamp_user
      - MYSQL_PASSWORD=lamp_password
      - MYSQL_DATABASE=lamp_db

  db:
    image: mysql:5.7
    ports:
      - "3306:3306"
    volumes:
      - db_data:/var/lib/mysql
    environment:
      - MYSQL_ROOT_PASSWORD=root_password
      - MYSQL_DATABASE=lamp_db
      - MYSQL_USER=lamp_user
      - MYSQL_PASSWORD=lamp_password

  phpmyadmin:
    image: phpmyadmin/phpmyadmin
    ports:
      - "8081:80"
    depends_on:
      - db
    environment:
      - PMA_HOST=db
      - PMA_USER=root
      - PMA_PASSWORD=root_password

volumes:
  db_data:
""",
            "www/index.php": """<!DOCTYPE html>
<html>
<head>
  <title>LAMP Stack - Docker Service Manager</title>
  <style>
    body {
      font-family: Arial, sans-serif;
      margin: 40px;
      line-height: 1.6;
    }
    h1 {
      color: #3366cc;
    }
    .info {
      background-color: #f5f5f5;
      padding: 15px;
      border-radius: 5px;
    }
    .success {
      color: green;
      font-weight: bold;
    }
  </style>
</head>
<body>
  <h1>LAMP Stack Environment</h1>
  <p>This is a Docker-based LAMP (Linux, Apache, MySQL, PHP) development environment.</p>
  
  <div class="info">
    <h2>Environment Information</h2>
    <ul>
      <li>PHP Version: <?php echo phpversion(); ?></li>
      <li>Web Server: <?php echo $_SERVER['SERVER_SOFTWARE']; ?></li>
      <li>Document Root: <?php echo $_SERVER['DOCUMENT_ROOT']; ?></li>
    </ul>

    <h2>Database Connection</h2>
    <?php
    $host = 'db';
    $user = 'lamp_user';
    $password = 'lamp_password';
    $db = 'lamp_db';

    $conn = new mysqli($host, $user, $password, $db);
    if ($conn->connect_error) {
      echo "<p>Database connection failed: " . $conn->connect_error . "</p>";
    } else {
      echo "<p class='success'>Database connection successful!</p>";
      $conn->close();
    }
    ?>
  </div>

  <h2>Resources</h2>
  <ul>
    <li>PHPMyAdmin: <a href="http://localhost:8081">http://localhost:8081</a></li>
    <li>MySQL Database: localhost:3306</li>
  </ul>
</body>
</html>
""",
            "README.md": """# LAMP Stack Environment

This is a Docker-based LAMP (Linux, Apache, MySQL, PHP) development environment.

## Services

- **Web Server**: Apache with PHP 7.4
- **Database**: MySQL 5.7
- **Admin Tool**: PHPMyAdmin

## Usage

1. Start the environment:
   ```
   docker-compose up -d
   ```

2. Access the application:
   - Website: http://localhost:8080
   - PHPMyAdmin: http://localhost:8081 (root/root_password)

3. Stop the environment:
   ```
   docker-compose down
   ```

## Database Credentials

- **Root Password**: root_password
- **Database**: lamp_db
- **User**: lamp_user
- **Password**: lamp_password

## Customization

- Website files are in the `www/` directory
- Database data is persisted in the `db_data` volume
"""
        }
        
    def generate(self, target_dir: str) -> bool:
        """Generate LAMP template files.
        
        Args:
            target_dir: Directory to write template files
            
        Returns:
            True if successful, False otherwise
        """
        success = super().generate(target_dir)
        
        if success and not self.demo_mode:
            # Create www directory
            www_dir = os.path.join(target_dir, "www")
            os.makedirs(www_dir, exist_ok=True)
            
        return success


class MEANTemplate(EnvironmentTemplate):
    """MEAN (MongoDB, Express, Angular, Node.js) stack template."""
    
    def __init__(self, demo_mode: bool = False):
        """Initialize MEAN template.
        
        Args:
            demo_mode: Whether to use demo mode with simulated responses
        """
        super().__init__(
            name="MEAN Stack",
            description="MongoDB, Express, Angular, Node.js development environment",
            demo_mode=demo_mode
        )
        
        # Define template files
        self.files = {
            "docker-compose.yml": """version: '3'

services:
  nodejs:
    image: node:14
    container_name: mean_nodejs
    restart: always
    working_dir: /app
    volumes:
      - ./backend:/app
    ports:
      - "3000:3000"
    command: bash -c "npm install && npm start"
    depends_on:
      - mongodb
    environment:
      - MONGO_URI=mongodb://mongodb:27017/mean_app

  angular:
    image: node:14
    container_name: mean_angular
    restart: always
    working_dir: /app
    volumes:
      - ./frontend:/app
    ports:
      - "4200:4200"
    command: bash -c "npm install && npm start"
    
  mongodb:
    image: mongo:4.4
    container_name: mean_mongodb
    restart: always
    ports:
      - "27017:27017"
    volumes:
      - mongodb_data:/data/db
    environment:
      - MONGO_INITDB_DATABASE=mean_app

volumes:
  mongodb_data:
""",
            "backend/package.json": """{
  "name": "mean-backend",
  "version": "1.0.0",
  "description": "MEAN Stack Backend",
  "main": "server.js",
  "scripts": {
    "start": "node server.js",
    "dev": "nodemon server.js"
  },
  "dependencies": {
    "express": "^4.17.1",
    "mongoose": "^5.13.5",
    "cors": "^2.8.5",
    "body-parser": "^1.19.0"
  },
  "devDependencies": {
    "nodemon": "^2.0.12"
  }
}
""",
            "backend/server.js": """const express = require('express');
const mongoose = require('mongoose');
const cors = require('cors');
const bodyParser = require('body-parser');

// Initialize Express
const app = express();
const port = process.env.PORT || 3000;

// Middleware
app.use(cors());
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: true }));

// MongoDB Connection
const mongoURI = process.env.MONGO_URI || 'mongodb://localhost:27017/mean_app';
mongoose.connect(mongoURI, {
  useNewUrlParser: true,
  useUnifiedTopology: true,
  useCreateIndex: true
})
  .then(() => console.log('MongoDB connection established'))
  .catch(err => console.error('MongoDB connection error:', err));

// Define a simple schema for demonstration
const ItemSchema = new mongoose.Schema({
  name: { type: String, required: true },
  description: String,
  created: { type: Date, default: Date.now }
});

const Item = mongoose.model('Item', ItemSchema);

// API Routes
app.get('/', (req, res) => {
  res.json({ message: 'Welcome to the MEAN Stack API' });
});

// Get all items
app.get('/api/items', async (req, res) => {
  try {
    const items = await Item.find();
    res.json(items);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Create a new item
app.post('/api/items', async (req, res) => {
  try {
    const newItem = new Item(req.body);
    const savedItem = await newItem.save();
    res.status(201).json(savedItem);
  } catch (err) {
    res.status(400).json({ error: err.message });
  }
});

// Start server
app.listen(port, () => {
  console.log(`Server running on http://localhost:${port}`);
});
""",
            "frontend/package.json": """{
  "name": "mean-frontend",
  "version": "1.0.0",
  "description": "MEAN Stack Frontend",
  "scripts": {
    "start": "ng serve --host 0.0.0.0",
    "build": "ng build"
  },
  "dependencies": {
    "@angular/common": "^12.0.0",
    "@angular/compiler": "^12.0.0",
    "@angular/core": "^12.0.0",
    "@angular/forms": "^12.0.0",
    "@angular/platform-browser": "^12.0.0",
    "@angular/platform-browser-dynamic": "^12.0.0",
    "@angular/router": "^12.0.0",
    "rxjs": "^7.0.0",
    "zone.js": "~0.11.4"
  },
  "devDependencies": {
    "@angular-devkit/build-angular": "^12.0.0",
    "@angular/cli": "^12.0.0",
    "@angular/compiler-cli": "^12.0.0",
    "typescript": "~4.3.5"
  }
}
""",
            "README.md": """# MEAN Stack Environment

This is a Docker-based MEAN (MongoDB, Express, Angular, Node.js) development environment.

## Services

- **Backend**: Node.js with Express
- **Frontend**: Angular
- **Database**: MongoDB

## Usage

1. Start the environment:
   ```
   docker-compose up -d
   ```

2. Access the application:
   - Angular Frontend: http://localhost:4200
   - Express API: http://localhost:3000
   - MongoDB: localhost:27017

3. Stop the environment:
   ```
   docker-compose down
   ```

## Development

- Backend code is in the `backend/` directory
- Frontend code is in the `frontend/` directory
- Database data is persisted in the `mongodb_data` volume

## API Endpoints

- GET `/api/items` - Get all items
- POST `/api/items` - Create a new item
"""
        }
        
    def generate(self, target_dir: str) -> bool:
        """Generate MEAN template files.
        
        Args:
            target_dir: Directory to write template files
            
        Returns:
            True if successful, False otherwise
        """
        success = super().generate(target_dir)
        
        if success and not self.demo_mode:
            # Create backend and frontend directories
            os.makedirs(os.path.join(target_dir, "backend"), exist_ok=True)
            os.makedirs(os.path.join(target_dir, "frontend"), exist_ok=True)
            
        return success


class WordPressTemplate(EnvironmentTemplate):
    """WordPress development environment template."""
    
    def __init__(self, demo_mode: bool = False):
        """Initialize WordPress template.
        
        Args:
            demo_mode: Whether to use demo mode with simulated responses
        """
        super().__init__(
            name="WordPress",
            description="WordPress development environment with MySQL",
            demo_mode=demo_mode
        )
        
        # Define template files
        self.files = {
            "docker-compose.yml": """version: '3'

services:
  wordpress:
    image: wordpress:latest
    ports:
      - "8080:80"
    volumes:
      - wordpress_data:/var/www/html
      - ./wp-content:/var/www/html/wp-content
    depends_on:
      - db
    environment:
      - WORDPRESS_DB_HOST=db
      - WORDPRESS_DB_USER=wordpress_user
      - WORDPRESS_DB_PASSWORD=wordpress_password
      - WORDPRESS_DB_NAME=wordpress
      - WORDPRESS_DEBUG=1

  db:
    image: mysql:5.7
    ports:
      - "3306:3306"
    volumes:
      - mysql_data:/var/lib/mysql
    environment:
      - MYSQL_ROOT_PASSWORD=root_password
      - MYSQL_DATABASE=wordpress
      - MYSQL_USER=wordpress_user
      - MYSQL_PASSWORD=wordpress_password

  phpmyadmin:
    image: phpmyadmin/phpmyadmin
    ports:
      - "8081:80"
    depends_on:
      - db
    environment:
      - PMA_HOST=db
      - PMA_USER=root
      - PMA_PASSWORD=root_password

volumes:
  wordpress_data:
  mysql_data:
""",
            "README.md": """# WordPress Development Environment

This is a Docker-based WordPress development environment.

## Services

- **WordPress**: Latest version
- **Database**: MySQL 5.7
- **Admin Tool**: PHPMyAdmin

## Usage

1. Start the environment:
   ```
   docker-compose up -d
   ```

2. Access the application:
   - WordPress: http://localhost:8080
   - PHPMyAdmin: http://localhost:8081 (root/root_password)

3. Stop the environment:
   ```
   docker-compose down
   ```

## Database Credentials

- **Root Password**: root_password
- **Database**: wordpress
- **User**: wordpress_user
- **Password**: wordpress_password

## Customization

- WordPress content is in the `wp-content/` directory
- WordPress data is persisted in the `wordpress_data` volume
- Database data is persisted in the `mysql_data` volume
"""
        }
        
    def generate(self, target_dir: str) -> bool:
        """Generate WordPress template files.
        
        Args:
            target_dir: Directory to write template files
            
        Returns:
            True if successful, False otherwise
        """
        success = super().generate(target_dir)
        
        if success and not self.demo_mode:
            # Create wp-content directory
            wp_content_dir = os.path.join(target_dir, "wp-content")
            os.makedirs(wp_content_dir, exist_ok=True)
            
            # Create subdirectories
            os.makedirs(os.path.join(wp_content_dir, "plugins"), exist_ok=True)
            os.makedirs(os.path.join(wp_content_dir, "themes"), exist_ok=True)
            
        return success


class TemplateManager:
    """Manage environment templates."""
    
    def __init__(self, demo_mode: bool = False):
        """Initialize template manager.
        
        Args:
            demo_mode: Whether to use demo mode with simulated responses
        """
        self.demo_mode = demo_mode
        self.templates = self._register_templates()
        
    def _register_templates(self) -> Dict[str, EnvironmentTemplate]:
        """Register available templates.
        
        Returns:
            Dictionary of template_id: template_instance mappings
        """
        return {
            "lamp": LAMPTemplate(demo_mode=self.demo_mode),
            "mean": MEANTemplate(demo_mode=self.demo_mode),
            "wordpress": WordPressTemplate(demo_mode=self.demo_mode)
        }
        
    def get_templates(self) -> Dict[str, EnvironmentTemplate]:
        """Get all available templates.
        
        Returns:
            Dictionary of template_id: template_instance mappings
        """
        return self.templates
        
    def list_templates(self) -> bool:
        """List all available templates.
        
        Returns:
            True (always succeeds)
        """
        print_section("Available Environment Templates")
        
        for template_id, template in self.templates.items():
            print(f"{COLORS['CYAN']}{template_id}{COLORS['RESET']}: {template.name}")
            print(f"  {template.description}")
            print()
            
        return True
        
    def create_environment(self, template_id: str, target_dir: Optional[str] = None) -> bool:
        """Create an environment from a template.
        
        Args:
            template_id: ID of the template to use
            target_dir: Directory to create environment in (default: current directory)
            
        Returns:
            True if successful, False otherwise
        """
        # Check if template exists
        if template_id not in self.templates:
            print_status(f"Template '{template_id}' not found", "error", demo_mode=self.demo_mode)
            return False
            
        template = self.templates[template_id]
        
        # Use current directory if target_dir not specified
        if target_dir is None:
            target_dir = os.getcwd()
            
        # Generate template files
        print_status(f"Generating {template.name} template in {target_dir}", "info", demo_mode=self.demo_mode)
        return template.generate(target_dir)
        
    def launch_environment(self, template_id: str, target_dir: Optional[str] = None) -> bool:
        """Launch an environment from a template.
        
        Args:
            template_id: ID of the template to use
            target_dir: Directory containing environment files (default: current directory)
            
        Returns:
            True if successful, False otherwise
        """
        # Check if template exists
        if template_id not in self.templates:
            print_status(f"Template '{template_id}' not found", "error", demo_mode=self.demo_mode)
            return False
            
        template = self.templates[template_id]
        
        # Use current directory if target_dir not specified
        if target_dir is None:
            target_dir = os.getcwd()
            
        # Launch environment
        print_status(f"Launching {template.name} environment in {target_dir}", "info", demo_mode=self.demo_mode)
        return template.launch(target_dir)