"""
FileConverter Pro - Flask Application Factory

This module contains the Flask application factory and configuration.
"""

from flask import Flask
from flask_cors import CORS
from flask_moment import Moment
from config import config
from datetime import datetime

def create_app(config_name='default'):
    """
    Create and configure Flask application
    
    Args:
        config_name (str): Configuration environment name
        
    Returns:
        Flask: Configured Flask application instance
    """
    
    # Create Flask instance
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    init_extensions(app)
    
    # Register Jinja2 filters
    @app.template_filter('strftime')
    def _jinja2_filter_datetime(date, fmt=None):
        if fmt is None:
            fmt = '%Y'
        if isinstance(date, str):
            date = datetime.now()
        return date.strftime(fmt)
    
    # Register blueprints
    register_blueprints(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Setup logging
    setup_logging(app)
    
    return app

def init_extensions(app):
    """Initialize Flask extensions"""
    
    # CORS configuration
    CORS(app, origins=app.config.get('CORS_ORIGINS', ['http://localhost:5000']))
    
    # Initialize Flask-Moment for datetime handling
    Moment(app)

def register_blueprints(app):
    """Register application blueprints"""
    
    # Import blueprints
    from app.routes.main import main_bp
    from app.routes.api import api_bp
    from app.routes.health import health_bp
    
    # Register blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(health_bp)

def register_error_handlers(app):
    """Register custom error handlers"""
    
    @app.errorhandler(404)
    def not_found_error(error):
        return {'error': 'Not found', 'message': 'The requested resource was not found'}, 404
    
    @app.errorhandler(413)
    def request_entity_too_large(error):
        return {
            'error': 'File too large',
            'message': f'File size exceeds the maximum limit of {app.config["MAX_FILE_SIZE_MB"]}MB'
        }, 413
    
    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f'Internal server error: {error}')
        return {
            'error': 'Internal server error',
            'message': 'An unexpected error occurred. Please try again later.'
        }, 500

def setup_logging(app):
    """Setup application logging"""
    
    if not app.debug and not app.testing:
        import logging
        from logging.handlers import RotatingFileHandler
        
        # Create file handler
        file_handler = RotatingFileHandler(
            'app.log', 
            maxBytes=10240000, 
            backupCount=10
        )
        
        # Set logging format
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        
        # Set log level
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        
        app.logger.setLevel(logging.INFO)
        app.logger.info('FileConverter Pro startup')