"""
Services package for FileConverter Pro

This package contains business logic services for file handling,
conversion operations, and related functionality.
"""

from .file_handler import FileHandler
from .converter import (
    ConversionEngine,
    ImageConverter,
    VideoConverter,
    AudioConverter,
    DocumentConverter,
    ConversionService
)

# Export all services for easy importing
__all__ = [
    'FileHandler',
    'ConversionEngine',
    'ImageConverter',
    'VideoConverter', 
    'AudioConverter',
    'DocumentConverter',
    'ConversionService'
]

# Service registry for programmatic access
SERVICES = {
    'file_handler': FileHandler,
    'conversion': ConversionService,
    'image_converter': ImageConverter,
    'video_converter': VideoConverter,
    'audio_converter': AudioConverter,
    'document_converter': DocumentConverter
}

def get_service(service_name: str, *args, **kwargs):
    """
    Factory function to get service instances
    
    Args:
        service_name: Name of the service to instantiate
        *args: Positional arguments for service constructor
        **kwargs: Keyword arguments for service constructor
        
    Returns:
        Service instance
        
    Raises:
        ValueError: If service_name is not found
    """
    if service_name not in SERVICES:
        raise ValueError(f"Unknown service: {service_name}")
    
    service_class = SERVICES[service_name]
    return service_class(*args, **kwargs)

# Version info
__version__ = '1.0.0'
__author__ = 'FileConverter Pro Team'