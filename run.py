#!/usr/bin/env python3
"""
FileConverter Pro - Main application entry point

A modern, high-performance web application for bulk file conversion 
supporting 200+ file formats.

Author: Your Name
Version: 1.0.0
License: MIT
"""

import os
import sys
import logging
from app import create_app

# Get configuration from environment
config_name = os.getenv('FLASK_CONFIG') or 'default'

# Create Flask application
app = create_app(config_name)

def setup_directories():
    """Create necessary directories if they don't exist"""
    directories = [
        app.config['UPLOAD_FOLDER'],
        app.config['CONVERTED_FOLDER'],
        app.config['TEMP_FOLDER']
    ]
    
    for directory in directories:
        try:
            os.makedirs(directory, exist_ok=True)
            app.logger.info(f"Directory ensured: {directory}")
        except OSError as e:
            app.logger.error(f"Failed to create directory {directory}: {e}")
            sys.exit(1)

def setup_logging():
    """Configure application logging"""
    if not app.debug:
        # Production logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s %(levelname)s %(name)s %(message)s',
            handlers=[
                logging.FileHandler('app.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
    else:
        # Development logging
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s %(levelname)s %(name)s %(message)s'
        )

def check_system_dependencies():
    """Check if required system dependencies are available"""
    import subprocess
    
    dependencies = {
        'ffmpeg': ['ffmpeg', '-version'],
        'imagemagick': ['convert', '-version'],
        'pandoc': ['pandoc', '--version']
    }
    
    missing_deps = []
    
    for name, command in dependencies.items():
        try:
            subprocess.run(command, capture_output=True, check=True)
            app.logger.info(f"✓ {name} is available")
        except (subprocess.CalledProcessError, FileNotFoundError):
            app.logger.warning(f"✗ {name} is not available")
            missing_deps.append(name)
    
    if missing_deps:
        app.logger.warning(
            f"Missing system dependencies: {', '.join(missing_deps)}. "
            "Some conversion features may not work properly."
        )
    
    return len(missing_deps) == 0

if __name__ == '__main__':
    # Setup logging
    setup_logging()
    
    # Setup directories
    setup_directories()
    
    # Check system dependencies
    check_system_dependencies()
    
    # Log startup information
    app.logger.info("=" * 50)
    app.logger.info("FileConverter Pro Starting Up")
    app.logger.info("=" * 50)
    app.logger.info(f"Environment: {config_name}")
    app.logger.info(f"Debug mode: {app.debug}")
    app.logger.info(f"Upload folder: {app.config['UPLOAD_FOLDER']}")
    app.logger.info(f"Max file size: {app.config['MAX_FILE_SIZE_MB']}MB")
    app.logger.info(f"Max files per batch: {app.config['MAX_FILES_PER_BATCH']}")
    
    # Run the application
    try:
        app.run(
            debug=app.config['DEBUG'],
            host='0.0.0.0',
            port=int(os.environ.get('PORT', 5001)),
            threaded=True
        )
    except KeyboardInterrupt:
        app.logger.info("Application stopped by user")
    except Exception as e:
        app.logger.error(f"Application failed to start: {e}")
        sys.exit(1)