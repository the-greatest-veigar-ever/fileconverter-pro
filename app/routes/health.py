"""
Health Check Routes for FileConverter Pro

This module provides health check endpoints for monitoring
and dependency validation.
"""

import os
import subprocess
import time
from flask import Blueprint, jsonify, current_app

health_bp = Blueprint('health', __name__)

@health_bp.route('/health')
def health_check():
    """
    Comprehensive health check endpoint for monitoring and Docker
    
    Returns:
        JSON response with health status and system checks
    """
    start_time = time.time()
    
    try:
        # Perform all health checks
        checks = {
            'database': check_redis_connection(),
            'directories': check_directories(),
            'system_dependencies': check_system_dependencies(),
            'disk_space': check_disk_space(),
            'memory': check_memory_usage()
        }
        
        # Calculate response time
        response_time = round((time.time() - start_time) * 1000, 2)
        
        # Overall health status
        all_healthy = all(check['status'] == 'healthy' for check in checks.values())
        overall_status = 'healthy' if all_healthy else 'unhealthy'
        status_code = 200 if all_healthy else 503
        
        return jsonify({
            'status': overall_status,
            'timestamp': int(time.time()),
            'response_time_ms': response_time,
            'version': '1.0.0',
            'environment': current_app.config.get('ENV', 'development'),
            'checks': checks
        }), status_code
        
    except Exception as e:
        current_app.logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'error',
            'timestamp': int(time.time()),
            'error': str(e),
            'version': '1.0.0'
        }), 500

@health_bp.route('/health/quick')
def quick_health_check():
    """
    Quick health check for load balancers
    
    Returns:
        Simple OK response
    """
    return jsonify({
        'status': 'ok',
        'timestamp': int(time.time())
    }), 200

@health_bp.route('/health/dependencies')
def dependencies_check():
    """
    Detailed system dependencies check
    
    Returns:
        JSON response with detailed dependency status
    """
    dependencies = check_system_dependencies()
    status_code = 200 if dependencies['status'] == 'healthy' else 503
    
    return jsonify({
        'status': dependencies['status'],
        'dependencies': dependencies['details'],
        'timestamp': int(time.time())
    }), status_code

def check_redis_connection():
    """Check Redis connection for Celery"""
    try:
        import redis
        redis_url = current_app.config.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
        r = redis.from_url(redis_url)
        r.ping()
        return {
            'status': 'healthy',
            'message': 'Redis connection successful'
        }
    except Exception as e:
        return {
            'status': 'unhealthy',
            'message': f'Redis connection failed: {str(e)}'
        }

def check_directories():
    """Check if required directories exist and are writable"""
    required_dirs = [
        current_app.config['UPLOAD_FOLDER'],
        current_app.config['CONVERTED_FOLDER'],
        current_app.config['TEMP_FOLDER']
    ]
    
    status = 'healthy'
    details = {}
    
    for dir_path in required_dirs:
        try:
            # Check if directory exists
            if not os.path.exists(dir_path):
                os.makedirs(dir_path, exist_ok=True)
            
            # Check if writable
            test_file = os.path.join(dir_path, '.write_test')
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)
            
            details[dir_path] = 'accessible'
            
        except Exception as e:
            details[dir_path] = f'error: {str(e)}'
            status = 'unhealthy'
    
    return {
        'status': status,
        'details': details
    }

def check_system_dependencies():
    """Check if required system dependencies are available"""
    dependencies = {
        'ffmpeg': {
            'command': ['ffmpeg', '-version'],
            'description': 'Video and audio conversion'
        },
        'imagemagick': {
            'command': ['convert', '-version'],
            'description': 'Advanced image processing'
        },
        'libreoffice': {
            'command': ['libreoffice', '--version'],
            'description': 'Document conversion'
        },
        'pandoc': {
            'command': ['pandoc', '--version'],
            'description': 'Universal document converter'
        }
    }
    
    status = 'healthy'
    details = {}
    
    for name, config in dependencies.items():
        try:
            result = subprocess.run(
                config['command'], 
                capture_output=True, 
                check=True,
                timeout=5
            )
            
            # Extract version information
            version_line = result.stdout.decode().split('\n')[0]
            details[name] = {
                'status': 'available',
                'version': version_line,
                'description': config['description']
            }
            
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            details[name] = {
                'status': 'unavailable',
                'description': config['description'],
                'impact': 'Some conversion features may not work'
            }
            # Don't mark as unhealthy for optional dependencies
            # status = 'unhealthy'
    
    return {
        'status': status,
        'details': details
    }

def check_disk_space():
    """Check available disk space"""
    try:
        upload_folder = current_app.config['UPLOAD_FOLDER']
        statvfs = os.statvfs(upload_folder)
        
        # Calculate disk space in GB
        total_space = (statvfs.f_frsize * statvfs.f_blocks) / (1024**3)
        free_space = (statvfs.f_frsize * statvfs.f_available) / (1024**3)
        used_space = total_space - free_space
        usage_percent = (used_space / total_space) * 100
        
        # Determine status based on usage
        if usage_percent > 90:
            status = 'critical'
        elif usage_percent > 80:
            status = 'warning'
        else:
            status = 'healthy'
        
        return {
            'status': status,
            'total_gb': round(total_space, 2),
            'free_gb': round(free_space, 2),
            'used_gb': round(used_space, 2),
            'usage_percent': round(usage_percent, 2)
        }
        
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Could not check disk space: {str(e)}'
        }

def check_memory_usage():
    """Check system memory usage"""
    try:
        import psutil
        
        memory = psutil.virtual_memory()
        usage_percent = memory.percent
        
        # Determine status based on usage
        if usage_percent > 90:
            status = 'critical'
        elif usage_percent > 80:
            status = 'warning'
        else:
            status = 'healthy'
        
        return {
            'status': status,
            'total_gb': round(memory.total / (1024**3), 2),
            'available_gb': round(memory.available / (1024**3), 2),
            'used_gb': round(memory.used / (1024**3), 2),
            'usage_percent': round(usage_percent, 2)
        }
        
    except ImportError:
        return {
            'status': 'unavailable',
            'message': 'psutil not installed - memory monitoring disabled'
        }
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Could not check memory usage: {str(e)}'
        }