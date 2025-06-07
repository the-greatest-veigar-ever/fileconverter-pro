import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Base configuration class"""
    
    # Flask Configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # File Upload Configuration
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 100)) * 1024 * 1024  # MB to bytes
    MAX_FILES_PER_BATCH = int(os.environ.get('MAX_FILES_PER_BATCH', 50))
    MAX_FILE_SIZE_MB = int(os.environ.get('MAX_FILE_SIZE_MB', 100))
    
    # Directory Configuration
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', 'uploads')
    CONVERTED_FOLDER = os.environ.get('CONVERTED_FOLDER', 'converted')
    TEMP_FOLDER = os.environ.get('TEMP_FOLDER', 'temp')
    
    # Celery Configuration
    CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
    CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
    
    # External API Configuration
    CONVERTIO_API_KEY = os.environ.get('CONVERTIO_API_KEY')
    ENABLE_API_FALLBACK = os.environ.get('ENABLE_API_FALLBACK', 'false').lower() == 'true'
    
    # Security
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', 'http://localhost:5000').split(',')
    
    # Performance
    CONVERSION_TIMEOUT = int(os.environ.get('CONVERSION_TIMEOUT', 300))
    CLEANUP_INTERVAL = int(os.environ.get('CLEANUP_INTERVAL', 3600))
    
    # Comprehensive file type configurations
    ALLOWED_EXTENSIONS = {
        'image': [
            # Standard formats
            'jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff', 'tif', 'webp', 'svg',
            # Additional formats
            'jfif', 'ico', 'psd', 'raw', 'cr2', 'nef', 'dng', 'heic', 'heif', 'avif',
            # Less common but supported
            'pbm', 'pgm', 'ppm', 'xbm', 'xpm', 'tga', 'pcx'
        ],
        'video': [
            # Common formats
            'mp4', 'avi', 'mov', 'wmv', 'flv', 'webm', 'mkv', '3gp', 'm4v',
            # Professional formats
            'f4v', 'asf', 'rm', 'rmvb', 'vob', 'ts', 'mts', 'm2ts',
            # Additional formats
            'divx', 'xvid', 'ogv', 'dv', 'mxf'
        ],
        'audio': [
            # Standard formats
            'mp3', 'wav', 'flac', 'aac', 'ogg', 'wma', 'm4a',
            # Additional formats
            'mid', 'midi', 'ra', 'amr', 'opus', 'ape', 'ac3', 'dts',
            # Professional formats
            'aiff', 'au', 'snd', 'gsm', 'voc'
        ],
        'document': [
            # Text documents
            'pdf', 'doc', 'docx', 'txt', 'rtf', 'odt', 'pages',
            # E-books
            'epub', 'mobi', 'azw', 'azw3', 'fb2',
            # Other document formats
            'djvu', 'ps', 'eps', 'tex', 'md', 'html', 'htm'
        ],
        'presentation': [
            # Presentation formats
            'ppt', 'pptx', 'odp', 'key'
        ],
        'spreadsheet': [
            # Spreadsheet formats
            'xlsx', 'xls', 'csv', 'ods', 'tsv', 'dbf', 'xlsm', 'xlsb', 'numbers'
        ],
        'archive': [
            # Archive formats
            'zip', 'rar', '7z', 'tar', 'gz', 'bz2', 'xz', 'z', 'lzma'
        ],
        'font': [
            # Font formats
            'ttf', 'otf', 'woff', 'woff2', 'eot'
        ]
    }
    
    # Conversion engine configurations
    CONVERSION_ENGINES = {
        'image': ['pillow', 'wand'],  # Pillow for basic, Wand (ImageMagick) for advanced
        'video': ['ffmpeg'],          # FFmpeg for all video conversions
        'audio': ['ffmpeg'],          # FFmpeg for all audio conversions
        'document': ['pandoc', 'libreoffice'],  # Pandoc + LibreOffice for documents
        'presentation': ['libreoffice'],
        'spreadsheet': ['openpyxl', 'pandas'],
        'archive': ['patoolib', 'py7zr'],
        'font': ['fonttools']
    }
    
    # Quality settings for different formats
    QUALITY_SETTINGS = {
        'image': {
            'jpeg': {'quality': 85, 'optimize': True},
            'png': {'optimize': True},
            'webp': {'quality': 85, 'method': 6}
        },
        'video': {
            'mp4': {'crf': 23, 'preset': 'medium'},
            'webm': {'crf': 30, 'preset': 'medium'}
        },
        'audio': {
            'mp3': {'bitrate': '192k'},
            'aac': {'bitrate': '128k'},
            'ogg': {'bitrate': '192k'}
        }
    }

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False

class TestingConfig(Config):
    """Testing configuration"""
    DEBUG = True
    TESTING = True
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10MB for testing
    MAX_FILES_PER_BATCH = 5

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}