"""
Helper Utilities for FileConverter Pro

This module provides utility functions used throughout the application
including file operations, formatting, validation helpers, and more.
"""

import os
import re
import time
import hashlib
import mimetypes
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Any
from urllib.parse import quote, unquote
from flask import current_app


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human readable format
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted size string (e.g., "1.5 MB")
    """
    if size_bytes == 0:
        return "0 B"
    
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if abs(size_bytes) < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    
    return f"{size_bytes:.1f} PB"


def format_duration(seconds: float) -> str:
    """
    Format duration in human readable format
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted duration string
    """
    if seconds < 1:
        return f"{int(seconds * 1000)}ms"
    elif seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        remaining_seconds = int(seconds % 60)
        return f"{minutes}m {remaining_seconds}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"


def get_file_type(extension: str) -> Optional[str]:
    """
    Get file type category from extension
    
    Args:
        extension: File extension (without dot)
        
    Returns:
        File type category or None if not found
    """
    extension_lower = extension.lower().strip()
    allowed_extensions = current_app.config['ALLOWED_EXTENSIONS']
    
    for file_type, extensions in allowed_extensions.items():
        if extension_lower in extensions:
            return file_type
    
    return None


def get_mime_type(filename: str) -> str:
    """
    Get MIME type from filename
    
    Args:
        filename: Name of the file
        
    Returns:
        MIME type string
    """
    mime_type, _ = mimetypes.guess_type(filename)
    return mime_type or 'application/octet-stream'


def safe_filename(filename: str) -> str:
    """
    Create a safe filename by removing/replacing dangerous characters
    
    Args:
        filename: Original filename
        
    Returns:
        Safe filename
    """
    # Remove or replace dangerous characters
    filename = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '', filename)
    
    # Replace spaces with underscores
    filename = re.sub(r'\s+', '_', filename)
    
    # Remove multiple dots (except the last one for extension)
    name_parts = filename.rsplit('.', 1)
    if len(name_parts) == 2:
        name, ext = name_parts
        name = re.sub(r'\.+', '.', name).strip('.')
        filename = f"{name}.{ext}"
    else:
        filename = re.sub(r'\.+', '.', filename).strip('.')
    
    # Ensure filename is not empty
    if not filename or filename == '.':
        filename = f"file_{int(time.time())}"
    
    # Limit length
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        max_name_length = 255 - len(ext)
        filename = name[:max_name_length] + ext
    
    return filename


def generate_unique_filename(base_filename: str, directory: str) -> str:
    """
    Generate a unique filename in the given directory
    
    Args:
        base_filename: Base filename
        directory: Target directory
        
    Returns:
        Unique filename
    """
    safe_name = safe_filename(base_filename)
    full_path = os.path.join(directory, safe_name)
    
    if not os.path.exists(full_path):
        return safe_name
    
    name, ext = os.path.splitext(safe_name)
    counter = 1
    
    while True:
        new_filename = f"{name}_{counter}{ext}"
        full_path = os.path.join(directory, new_filename)
        
        if not os.path.exists(full_path):
            return new_filename
        
        counter += 1


def calculate_file_hash(file_path: str, algorithm: str = 'md5') -> str:
    """
    Calculate hash of a file
    
    Args:
        file_path: Path to the file
        algorithm: Hash algorithm ('md5', 'sha1', 'sha256')
        
    Returns:
        Hash string in hexadecimal format
    """
    try:
        hash_obj = hashlib.new(algorithm)
        
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_obj.update(chunk)
        
        return hash_obj.hexdigest()
        
    except Exception as e:
        current_app.logger.error(f"Error calculating hash for {file_path}: {e}")
        return ""


def is_valid_uuid(uuid_string: str) -> bool:
    """
    Check if string is a valid UUID
    
    Args:
        uuid_string: String to validate
        
    Returns:
        True if valid UUID
    """
    import uuid
    try:
        uuid.UUID(uuid_string)
        return True
    except ValueError:
        return False


def timestamp_to_datetime(timestamp: Union[int, float]) -> datetime:
    """
    Convert timestamp to datetime object
    
    Args:
        timestamp: Unix timestamp
        
    Returns:
        datetime object
    """
    return datetime.fromtimestamp(timestamp)


def datetime_to_timestamp(dt: datetime) -> int:
    """
    Convert datetime to Unix timestamp
    
    Args:
        dt: datetime object
        
    Returns:
        Unix timestamp
    """
    return int(dt.timestamp())


def format_datetime(dt: datetime, format_string: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    Format datetime object as string
    
    Args:
        dt: datetime object
        format_string: Format string
        
    Returns:
        Formatted datetime string
    """
    return dt.strftime(format_string)


def parse_datetime(date_string: str, format_string: str = "%Y-%m-%d %H:%M:%S") -> Optional[datetime]:
    """
    Parse datetime string
    
    Args:
        date_string: Date string
        format_string: Expected format
        
    Returns:
        datetime object or None if parsing fails
    """
    try:
        return datetime.strptime(date_string, format_string)
    except ValueError:
        return None


def time_ago(dt: datetime) -> str:
    """
    Get human readable time ago string
    
    Args:
        dt: datetime object
        
    Returns:
        Time ago string (e.g., "2 hours ago")
    """
    now = datetime.utcnow()
    if dt.tzinfo is None:
        # Assume UTC if no timezone info
        pass
    else:
        now = now.replace(tzinfo=dt.tzinfo)
    
    diff = now - dt
    seconds = int(diff.total_seconds())
    
    if seconds < 60:
        return "just now"
    elif seconds < 3600:
        minutes = seconds // 60
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    elif seconds < 86400:
        hours = seconds // 3600
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif seconds < 2592000:  # 30 days
        days = seconds // 86400
        return f"{days} day{'s' if days != 1 else ''} ago"
    elif seconds < 31536000:  # 365 days
        months = seconds // 2592000
        return f"{months} month{'s' if months != 1 else ''} ago"
    else:
        years = seconds // 31536000
        return f"{years} year{'s' if years != 1 else ''} ago"


def clean_string(text: str, max_length: Optional[int] = None) -> str:
    """
    Clean and sanitize text string
    
    Args:
        text: Input text
        max_length: Maximum length (optional)
        
    Returns:
        Cleaned text
    """
    if not text:
        return ""
    
    # Remove control characters
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)
    
    # Strip whitespace
    text = text.strip()
    
    # Limit length if specified
    if max_length and len(text) > max_length:
        text = text[:max_length].strip()
    
    return text


def slugify(text: str, max_length: int = 50) -> str:
    """
    Convert text to URL-friendly slug
    
    Args:
        text: Input text
        max_length: Maximum slug length
        
    Returns:
        URL-friendly slug
    """
    # Convert to lowercase
    text = text.lower()
    
    # Replace spaces and special characters with hyphens
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    
    # Remove leading/trailing hyphens
    text = text.strip('-')
    
    # Limit length
    if len(text) > max_length:
        text = text[:max_length].rstrip('-')
    
    return text


def validate_email(email: str) -> bool:
    """
    Validate email address format
    
    Args:
        email: Email address to validate
        
    Returns:
        True if valid email format
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_url(url: str) -> bool:
    """
    Validate URL format
    
    Args:
        url: URL to validate
        
    Returns:
        True if valid URL format
    """
    pattern = r'^https?://[^\s/$.?#].[^\s]*$'
    return re.match(pattern, url) is not None


def extract_extension(filename: str) -> str:
    """
    Extract file extension from filename
    
    Args:
        filename: Name of the file
        
    Returns:
        File extension without dot (lowercase)
    """
    if '.' not in filename:
        return ''
    
    return filename.rsplit('.', 1)[1].lower()


def get_file_info_summary(file_path: str) -> Dict:
    """
    Get comprehensive file information
    
    Args:
        file_path: Path to the file
        
    Returns:
        Dictionary with file information
    """
    try:
        if not os.path.exists(file_path):
            return {'error': 'File not found'}
        
        stat = os.stat(file_path)
        filename = os.path.basename(file_path)
        extension = extract_extension(filename)
        
        return {
            'filename': filename,
            'size': stat.st_size,
            'size_formatted': format_file_size(stat.st_size),
            'extension': extension,
            'file_type': get_file_type(extension),
            'mime_type': get_mime_type(filename),
            'created': datetime.fromtimestamp(stat.st_ctime),
            'modified': datetime.fromtimestamp(stat.st_mtime),
            'accessed': datetime.fromtimestamp(stat.st_atime),
            'is_readable': os.access(file_path, os.R_OK),
            'is_writable': os.access(file_path, os.W_OK)
        }
        
    except Exception as e:
        current_app.logger.error(f"Error getting file info for {file_path}: {e}")
        return {'error': str(e)}


def create_progress_data(current: int, total: int, start_time: float) -> Dict:
    """
    Create progress data dictionary
    
    Args:
        current: Current progress count
        total: Total count
        start_time: Start timestamp
        
    Returns:
        Progress data dictionary
    """
    if total == 0:
        percentage = 100
    else:
        percentage = min(100, int((current / total) * 100))
    
    elapsed_time = time.time() - start_time
    
    if current > 0 and percentage > 0:
        estimated_total_time = elapsed_time / (percentage / 100)
        estimated_remaining = max(0, estimated_total_time - elapsed_time)
    else:
        estimated_remaining = 0
    
    return {
        'current': current,
        'total': total,
        'percentage': percentage,
        'elapsed_seconds': round(elapsed_time, 2),
        'estimated_remaining_seconds': round(estimated_remaining, 2),
        'elapsed_formatted': format_duration(elapsed_time),
        'estimated_remaining_formatted': format_duration(estimated_remaining)
    }


def chunked_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """
    Split list into chunks of specified size
    
    Args:
        lst: List to chunk
        chunk_size: Size of each chunk
        
    Returns:
        List of chunks
    """
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def deep_merge_dicts(dict1: Dict, dict2: Dict) -> Dict:
    """
    Deep merge two dictionaries
    
    Args:
        dict1: First dictionary
        dict2: Second dictionary
        
    Returns:
        Merged dictionary
    """
    result = dict1.copy()
    
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge_dicts(result[key], value)
        else:
            result[key] = value
    
    return result


def sanitize_dict_for_json(data: Any) -> Any:
    """
    Sanitize data for JSON serialization
    
    Args:
        data: Data to sanitize
        
    Returns:
        JSON-serializable data
    """
    if isinstance(data, dict):
        return {key: sanitize_dict_for_json(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [sanitize_dict_for_json(item) for item in data]
    elif isinstance(data, datetime):
        return data.isoformat()
    elif isinstance(data, (bytes, bytearray)):
        return data.decode('utf-8', errors='ignore')
    elif hasattr(data, '__dict__'):
        return sanitize_dict_for_json(data.__dict__)
    else:
        return data


def get_available_formats_for_type(file_type: str) -> List[str]:
    """
    Get available formats for a given file type
    
    Args:
        file_type: File type category
        
    Returns:
        List of available formats
    """
    allowed_extensions = current_app.config['ALLOWED_EXTENSIONS']
    return sorted(allowed_extensions.get(file_type, []))


def estimate_conversion_time(file_size: int, file_type: str, target_format: str) -> float:
    """
    Estimate conversion time based on file size and type
    
    Args:
        file_size: File size in bytes
        file_type: Source file type
        target_format: Target format
        
    Returns:
        Estimated time in seconds
    """
    # Base processing rates (bytes per second) for different operations
    base_rates = {
        'image': 10 * 1024 * 1024,    # 10 MB/s
        'audio': 5 * 1024 * 1024,     # 5 MB/s
        'video': 1024 * 1024,         # 1 MB/s (slower due to complexity)
        'document': 50 * 1024 * 1024, # 50 MB/s (fast for text)
        'archive': 20 * 1024 * 1024   # 20 MB/s
    }
    
    # Complexity multipliers for certain conversions
    complexity_multipliers = {
        ('video', 'mp4'): 1.5,
        ('video', 'webm'): 2.0,
        ('image', 'webp'): 1.2,
        ('document', 'pdf'): 1.3
    }
    
    base_rate = base_rates.get(file_type, 2 * 1024 * 1024)  # Default 2 MB/s
    multiplier = complexity_multipliers.get((file_type, target_format), 1.0)
    
    estimated_seconds = (file_size / base_rate) * multiplier
    
    # Minimum 1 second, maximum 300 seconds for estimation
    return max(1, min(300, estimated_seconds))


def url_safe_filename(filename: str) -> str:
    """
    Create URL-safe version of filename
    
    Args:
        filename: Original filename
        
    Returns:
        URL-safe filename
    """
    return quote(filename, safe='')


def url_unsafe_filename(encoded_filename: str) -> str:
    """
    Decode URL-safe filename
    
    Args:
        encoded_filename: URL-encoded filename
        
    Returns:
        Original filename
    """
    return unquote(encoded_filename)