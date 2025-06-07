"""
File Validation Utilities for FileConverter Pro

This module provides comprehensive file validation including:
- File type detection and validation
- Size limits checking
- Security validation
- Format support verification
"""

import os
import magic
import filetype
from typing import Dict, List, Optional, Tuple
from flask import current_app
from werkzeug.datastructures import FileStorage


class FileValidator:
    """Comprehensive file validation service"""
    
    def __init__(self):
        self.allowed_extensions = current_app.config['ALLOWED_EXTENSIONS']
        self.max_file_size = current_app.config['MAX_FILE_SIZE_MB'] * 1024 * 1024  # Convert to bytes
        self.max_files_per_batch = current_app.config['MAX_FILES_PER_BATCH']
        
        # Security: Define dangerous file extensions
        self.dangerous_extensions = {
            'exe', 'bat', 'cmd', 'com', 'pif', 'scr', 'vbs', 'js', 'jar',
            'msi', 'dll', 'sys', 'sh', 'bash', 'php', 'jsp', 'asp', 'aspx'
        }
        
        # MIME type mappings for additional validation
        self.safe_mime_types = {
            # Images
            'image/jpeg', 'image/png', 'image/gif', 'image/webp', 'image/bmp',
            'image/tiff', 'image/svg+xml', 'image/x-icon', 'image/heic', 'image/heif',
            
            # Videos
            'video/mp4', 'video/avi', 'video/quicktime', 'video/x-msvideo',
            'video/x-ms-wmv', 'video/webm', 'video/x-flv', 'video/3gpp',
            
            # Audio
            'audio/mpeg', 'audio/wav', 'audio/flac', 'audio/aac', 'audio/ogg',
            'audio/x-ms-wma', 'audio/mp4', 'audio/opus',
            
            # Documents
            'application/pdf', 'application/msword', 'text/plain', 'text/rtf',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/vnd.oasis.opendocument.text',
            
            # Spreadsheets
            'application/vnd.ms-excel', 'text/csv',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'application/vnd.oasis.opendocument.spreadsheet',
            
            # Presentations
            'application/vnd.ms-powerpoint',
            'application/vnd.openxmlformats-officedocument.presentationml.presentation',
            'application/vnd.oasis.opendocument.presentation',
            
            # Archives
            'application/zip', 'application/x-rar-compressed', 'application/x-7z-compressed',
            'application/x-tar', 'application/gzip'
        }
    
    def validate_file(self, file: FileStorage) -> Dict:
        """
        Comprehensive file validation
        
        Args:
            file: Werkzeug FileStorage object
            
        Returns:
            Dictionary with validation result and details
        """
        if not file or not file.filename:
            return {
                'valid': False,
                'error': 'No file provided',
                'error_code': 'NO_FILE'
            }
        
        try:
            # Check filename
            filename_check = self._validate_filename(file.filename)
            if not filename_check['valid']:
                return filename_check
            
            # Check file size
            size_check = self._validate_file_size(file)
            if not size_check['valid']:
                return size_check
            
            # Check file extension
            extension_check = self._validate_file_extension(file.filename)
            if not extension_check['valid']:
                return extension_check
            
            # Check file content (magic bytes)
            content_check = self._validate_file_content(file)
            if not content_check['valid']:
                return content_check
            
            # Security checks
            security_check = self._validate_file_security(file)
            if not security_check['valid']:
                return security_check
            
            return {
                'valid': True,
                'message': 'File validation passed',
                'file_info': {
                    'filename': file.filename,
                    'size': self._get_file_size(file),
                    'extension': extension_check['extension'],
                    'file_type': extension_check['file_type'],
                    'mime_type': content_check.get('mime_type'),
                    'detected_type': content_check.get('detected_type')
                }
            }
            
        except Exception as e:
            current_app.logger.error(f"File validation error: {e}")
            return {
                'valid': False,
                'error': f'Validation failed: {str(e)}',
                'error_code': 'VALIDATION_ERROR'
            }
    
    def validate_batch(self, files: List[FileStorage]) -> Dict:
        """
        Validate a batch of files
        
        Args:
            files: List of FileStorage objects
            
        Returns:
            Dictionary with batch validation result
        """
        if not files:
            return {
                'valid': False,
                'error': 'No files provided',
                'error_code': 'NO_FILES'
            }
        
        # Check batch size
        if len(files) > self.max_files_per_batch:
            return {
                'valid': False,
                'error': f'Too many files. Maximum {self.max_files_per_batch} files allowed per batch',
                'error_code': 'TOO_MANY_FILES'
            }
        
        # Validate each file
        results = []
        total_size = 0
        valid_count = 0
        
        for i, file in enumerate(files):
            result = self.validate_file(file)
            results.append({
                'index': i,
                'filename': file.filename if file else 'unknown',
                'result': result
            })
            
            if result['valid']:
                valid_count += 1
                total_size += result['file_info']['size']
        
        # Check total batch size (optional limit)
        max_batch_size = self.max_file_size * len(files)  # Per-file limit * number of files
        if total_size > max_batch_size:
            return {
                'valid': False,
                'error': f'Total batch size too large: {self._format_size(total_size)} exceeds limit',
                'error_code': 'BATCH_SIZE_EXCEEDED',
                'batch_info': {
                    'total_files': len(files),
                    'valid_files': valid_count,
                    'total_size': total_size,
                    'results': results
                }
            }
        
        return {
            'valid': valid_count > 0,
            'message': f'{valid_count}/{len(files)} files passed validation',
            'batch_info': {
                'total_files': len(files),
                'valid_files': valid_count,
                'invalid_files': len(files) - valid_count,
                'total_size': total_size,
                'results': results
            }
        }
    
    def _validate_filename(self, filename: str) -> Dict:
        """Validate filename format and characters"""
        if not filename or filename.strip() == '':
            return {
                'valid': False,
                'error': 'Empty filename',
                'error_code': 'EMPTY_FILENAME'
            }
        
        # Check for dangerous characters
        dangerous_chars = ['<', '>', ':', '"', '|', '?', '*', '\0']
        if any(char in filename for char in dangerous_chars):
            return {
                'valid': False,
                'error': 'Filename contains invalid characters',
                'error_code': 'INVALID_FILENAME_CHARS'
            }
        
        # Check filename length
        if len(filename) > 255:
            return {
                'valid': False,
                'error': 'Filename too long (maximum 255 characters)',
                'error_code': 'FILENAME_TOO_LONG'
            }
        
        # Check for double extensions (potential security risk)
        parts = filename.lower().split('.')
        if len(parts) > 2:
            # Check if any part before the last is a dangerous extension
            for part in parts[1:-1]:  # Skip filename and final extension
                if part in self.dangerous_extensions:
                    return {
                        'valid': False,
                        'error': 'Suspicious filename with multiple extensions',
                        'error_code': 'SUSPICIOUS_FILENAME'
                    }
        
        return {'valid': True}
    
    def _validate_file_size(self, file: FileStorage) -> Dict:
        """Validate file size"""
        try:
            file_size = self._get_file_size(file)
            
            if file_size == 0:
                return {
                    'valid': False,
                    'error': 'Empty file',
                    'error_code': 'EMPTY_FILE'
                }
            
            if file_size > self.max_file_size:
                return {
                    'valid': False,
                    'error': f'File too large: {self._format_size(file_size)} exceeds {self._format_size(self.max_file_size)} limit',
                    'error_code': 'FILE_TOO_LARGE'
                }
            
            return {'valid': True, 'size': file_size}
            
        except Exception as e:
            return {
                'valid': False,
                'error': f'Could not determine file size: {str(e)}',
                'error_code': 'SIZE_CHECK_FAILED'
            }
    
    def _validate_file_extension(self, filename: str) -> Dict:
        """Validate file extension against supported formats"""
        if '.' not in filename:
            return {
                'valid': False,
                'error': 'File has no extension',
                'error_code': 'NO_EXTENSION'
            }
        
        extension = filename.rsplit('.', 1)[1].lower()
        
        # Check if extension is dangerous
        if extension in self.dangerous_extensions:
            return {
                'valid': False,
                'error': f'Dangerous file type: .{extension}',
                'error_code': 'DANGEROUS_EXTENSION'
            }
        
        # Find which category this extension belongs to
        file_type = None
        for category, extensions in self.allowed_extensions.items():
            if extension in extensions:
                file_type = category
                break
        
        if not file_type:
            return {
                'valid': False,
                'error': f'Unsupported file type: .{extension}',
                'error_code': 'UNSUPPORTED_EXTENSION',
                'supported_formats': self._get_supported_formats_summary()
            }
        
        return {
            'valid': True,
            'extension': extension,
            'file_type': file_type
        }
    
    def _validate_file_content(self, file: FileStorage) -> Dict:
        """Validate file content using magic bytes"""
        try:
            # Read first chunk for analysis
            file.seek(0)
            file_content = file.read(2048)  # Read first 2KB
            file.seek(0)  # Reset for later use
            
            if not file_content:
                return {
                    'valid': False,
                    'error': 'Could not read file content',
                    'error_code': 'CONTENT_READ_FAILED'
                }
            
            # Detect MIME type
            try:
                mime_type = magic.from_buffer(file_content, mime=True)
            except Exception:
                mime_type = 'application/octet-stream'
            
            # Detect file type using filetype library
            detected_type = None
            try:
                kind = filetype.guess(file_content)
                if kind:
                    detected_type = kind.extension
            except Exception:
                pass
            
            # Check if MIME type is in our safe list
            if mime_type not in self.safe_mime_types and not mime_type.startswith('text/'):
                current_app.logger.warning(f"Unknown MIME type detected: {mime_type} for file {file.filename}")
                # Don't reject, but log for monitoring
            
            # Check for executable signatures (security)
            if self._is_executable_content(file_content):
                return {
                    'valid': False,
                    'error': 'File appears to be executable',
                    'error_code': 'EXECUTABLE_CONTENT'
                }
            
            return {
                'valid': True,
                'mime_type': mime_type,
                'detected_type': detected_type
            }
            
        except Exception as e:
            current_app.logger.error(f"Content validation error: {e}")
            return {
                'valid': False,
                'error': f'Content validation failed: {str(e)}',
                'error_code': 'CONTENT_VALIDATION_ERROR'
            }
    
    def _validate_file_security(self, file: FileStorage) -> Dict:
        """Additional security validations"""
        try:
            # Check for suspicious patterns in filename
            filename_lower = file.filename.lower()
            
            # Check for script injection attempts
            script_patterns = ['<script', 'javascript:', 'vbscript:', 'onload=', 'onerror=']
            if any(pattern in filename_lower for pattern in script_patterns):
                return {
                    'valid': False,
                    'error': 'Filename contains suspicious script patterns',
                    'error_code': 'SCRIPT_INJECTION'
                }
            
            # Check for path traversal attempts
            if '..' in file.filename or '/' in file.filename or '\\' in file.filename:
                return {
                    'valid': False,
                    'error': 'Filename contains path traversal characters',
                    'error_code': 'PATH_TRAVERSAL'
                }
            
            return {'valid': True}
            
        except Exception as e:
            current_app.logger.error(f"Security validation error: {e}")
            return {
                'valid': False,
                'error': f'Security validation failed: {str(e)}',
                'error_code': 'SECURITY_CHECK_FAILED'
            }
    
    def _get_file_size(self, file: FileStorage) -> int:
        """Get file size in bytes"""
        # Save current position
        current_pos = file.tell()
        
        # Seek to end to get size
        file.seek(0, 2)  # Seek to end
        size = file.tell()
        
        # Restore original position
        file.seek(current_pos)
        
        return size
    
    def _is_executable_content(self, content: bytes) -> bool:
        """Check if content appears to be executable"""
        # Check for common executable signatures
        executable_signatures = [
            b'MZ',  # Windows PE
            b'\x7fELF',  # Linux ELF
            b'\xca\xfe\xba\xbe',  # Mach-O (macOS)
            b'\xfe\xed\xfa\xce',  # Mach-O (macOS)
            b'PK\x03\x04',  # ZIP (could contain executables, but also documents)
        ]
        
        # Only flag Windows PE and ELF as definitely executable
        dangerous_signatures = [b'MZ', b'\x7fELF']
        
        for sig in dangerous_signatures:
            if content.startswith(sig):
                return True
        
        return False
    
    def _format_size(self, size_bytes: int) -> str:
        """Format file size in human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"
    
    def _get_supported_formats_summary(self) -> Dict:
        """Get summary of supported formats"""
        summary = {}
        for category, extensions in self.allowed_extensions.items():
            summary[category] = {
                'count': len(extensions),
                'examples': list(extensions)[:5]  # First 5 as examples
            }
        return summary
    
    def is_format_supported(self, format_name: str) -> bool:
        """
        Check if a format is supported
        
        Args:
            format_name: File format/extension to check
            
        Returns:
            True if format is supported
        """
        format_lower = format_name.lower().strip()
        
        for extensions in self.allowed_extensions.values():
            if format_lower in extensions:
                return True
        
        return False
    
    def get_format_category(self, format_name: str) -> Optional[str]:
        """
        Get the category for a given format
        
        Args:
            format_name: File format/extension
            
        Returns:
            Category name or None if not found
        """
        format_lower = format_name.lower().strip()
        
        for category, extensions in self.allowed_extensions.items():
            if format_lower in extensions:
                return category
        
        return None
    
    def get_conversion_targets(self, source_format: str) -> List[str]:
        """
        Get possible conversion targets for a source format
        
        Args:
            source_format: Source file format
            
        Returns:
            List of possible target formats
        """
        source_category = self.get_format_category(source_format)
        if not source_category:
            return []
        
        # Return all formats in the same category except the source format
        targets = []
        for format_name in self.allowed_extensions[source_category]:
            if format_name.lower() != source_format.lower():
                targets.append(format_name)
        
        return sorted(targets)