"""
Routes package for FileConverter Pro

This package contains all Flask blueprints and routing logic
for the web application and API endpoints.
"""

from .main import main_bp
from .api import api_bp
from .health import health_bp

# Export all blueprints for easy importing
__all__ = [
    'main_bp',
    'api_bp', 
    'health_bp'
]

# Blueprint registry for programmatic access
BLUEPRINTS = {
    'main': main_bp,
    'api': api_bp,
    'health': health_bp
}

def register_all_blueprints(app):
    """
    Convenience function to register all blueprints with a Flask app
    
    Args:
        app: Flask application instance
    """
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(health_bp)

# Version info
__version__ = '1.0.0'
__author__ = 'FileConverter Pro Team'