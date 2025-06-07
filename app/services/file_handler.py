"""
File Handler Service for FileConverter Pro

This service manages file operations including upload, storage,
organization, ZIP creation, and cleanup.
"""

import os
import uuid
import zipfile
import shutil
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from werkzeug.utils import secure_filename
from flask import current_app
import magic
import filetype

class FileHandler:
    """Handles all file operations for the conversion service"""
    
    def __init__(self):
        self.upload_folder = current_app.config['UPLOAD_FOLDER']
        self.converted_folder = current_app.config['CONVERTED_FOLDER']
        self.temp_folder = current_app.config['TEMP_FOLDER']
        
        # Ensure directories exist
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Ensure all required directories exist"""
        for folder in [self.upload_folder, self.converted_folder, self.temp_folder]:
            os.makedirs(folder, exist_ok=True)
    
    def save_uploaded_file(self, file) -> Dict:
        """
        Save an uploaded file to the upload directory
        
        Args:
            file: Werkzeug FileStorage object
            
        Returns:
            Dictionary with file information
            
        Raises:
            Exception: If file save fails
        """
        try:
            # Generate unique filename
            original_filename = secure_filename(file.filename)
            file_id = str(uuid.uuid4())
            timestamp = int(time.time())
            
            # Get file extension
            filename_parts = original_filename.rsplit('.', 1)
            if len(filename_parts) == 2:
                name, extension = filename_parts
                extension = extension.lower()
            else:
                name = original_filename
                extension = self._detect_extension_from_content(file)
            
            # Create unique filename
            unique_filename = f"{file_id}_{timestamp}_{name}.{extension}"
            file_path = os.path.join(self.upload_folder, unique_filename)
            
            # Save file
            file.save(file_path)
            
            # Get file information
            file_stats = os.stat(file_path)
            file_info = {
                'id': file_id,
                'original_filename': original_filename,
                'filename': unique_filename,
                'path': file_path,
                'size': file_stats.st_size,
                'extension': extension,
                'mime_type': self._get_mime_type(file_path),
                'uploaded_at': datetime.utcnow().isoformat(),
                'checksum': self._calculate_checksum(file_path)
            }
            
            current_app.logger.info(f"File saved successfully: {original_filename} -> {unique_filename}")
            return file_info
            
        except Exception as e:
            current_app.logger.error(f"Failed to save file {file.filename}: {e}")
            # Cleanup if file was partially saved
            if 'file_path' in locals() and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except:
                    pass
            raise Exception(f"File save failed: {str(e)}")
    
    def _detect_extension_from_content(self, file) -> str:
        """
        Detect file extension from content when not provided in filename
        
        Args:
            file: File object
            
        Returns:
            Detected extension or 'bin' as fallback
        """
        try:
            # Reset file pointer
            file.seek(0)
            file_content = file.read(1024)  # Read first 1KB
            file.seek(0)  # Reset for actual save
            
            # Try filetype library first
            kind = filetype.guess(file_content)
            if kind:
                return kind.extension
            
            # Fallback to python-magic
            mime_type = magic.from_buffer(file_content, mime=True)
            extension_map = {
                'image/jpeg': 'jpg',
                'image/png': 'png',
                'image/gif': 'gif',
                'image/webp': 'webp',
                'video/mp4': 'mp4',
                'video/avi': 'avi',
                'audio/mpeg': 'mp3',
                'audio/wav': 'wav',
                'application/pdf': 'pdf',
                'text/plain': 'txt'
            }
            
            return extension_map.get(mime_type, 'bin')
            
        except Exception as e:
            current_app.logger.warning(f"Could not detect file extension: {e}")
            return 'bin'
    
    def _get_mime_type(self, file_path: str) -> str:
        """
        Get MIME type of a file
        
        Args:
            file_path: Path to the file
            
        Returns:
            MIME type string
        """
        try:
            return magic.from_file(file_path, mime=True)
        except Exception as e:
            current_app.logger.warning(f"Could not determine MIME type for {file_path}: {e}")
            return 'application/octet-stream'
    
    def _calculate_checksum(self, file_path: str) -> str:
        """
        Calculate MD5 checksum of a file
        
        Args:
            file_path: Path to the file
            
        Returns:
            MD5 checksum as hex string
        """
        try:
            import hashlib
            
            hash_md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
            
        except Exception as e:
            current_app.logger.warning(f"Could not calculate checksum for {file_path}: {e}")
            return ""
    
    def create_conversion_path(self, original_file_info: Dict, target_format: str) -> str:
        """
        Create path for converted file
        
        Args:
            original_file_info: Information about the original file
            target_format: Target format extension
            
        Returns:
            Path for the converted file
        """
        try:
            # Extract name without extension
            original_name = original_file_info['original_filename']
            if '.' in original_name:
                name_without_ext = original_name.rsplit('.', 1)[0]
            else:
                name_without_ext = original_name
            
            # Create converted filename
            file_id = original_file_info['id']
            timestamp = int(time.time())
            converted_filename = f"{file_id}_{timestamp}_{secure_filename(name_without_ext)}.{target_format}"
            
            return os.path.join(self.converted_folder, converted_filename)
            
        except Exception as e:
            current_app.logger.error(f"Failed to create conversion path: {e}")
            # Fallback path
            fallback_name = f"{uuid.uuid4()}_{int(time.time())}.{target_format}"
            return os.path.join(self.converted_folder, fallback_name)
    
    def create_temp_path(self, extension: str = 'tmp') -> str:
        """
        Create a temporary file path
        
        Args:
            extension: File extension for temp file
            
        Returns:
            Temporary file path
        """
        temp_filename = f"{uuid.uuid4()}_{int(time.time())}.{extension}"
        return os.path.join(self.temp_folder, temp_filename)
    
    def create_download_zip(self, job_id: str, converted_files: List[Dict]) -> Optional[str]:
        """
        Create a ZIP file containing all converted files
        
        Args:
            job_id: Conversion job ID
            converted_files: List of converted file information
            
        Returns:
            Path to created ZIP file or None if failed
        """
        try:
            if not converted_files:
                return None
            
            # Create ZIP filename
            zip_filename = f"converted_{job_id}_{int(time.time())}.zip"
            zip_path = os.path.join(self.temp_folder, zip_filename)
            
            # Create ZIP file
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_info in converted_files:
                    file_path = file_info['path']
                    if os.path.exists(file_path):
                        # Use original filename in ZIP
                        archive_name = file_info.get('original_filename', file_info['filename'])
                        zipf.write(file_path, archive_name)
                        current_app.logger.debug(f"Added to ZIP: {archive_name}")
                    else:
                        current_app.logger.warning(f"File not found for ZIP: {file_path}")
            
            # Verify ZIP was created and has content
            if os.path.exists(zip_path) and os.path.getsize(zip_path) > 0:
                current_app.logger.info(f"ZIP created successfully: {zip_path}")
                return zip_path
            else:
                current_app.logger.error("ZIP file was not created or is empty")
                return None
                
        except Exception as e:
            current_app.logger.error(f"Failed to create ZIP file: {e}")
            # Cleanup partial ZIP file
            if 'zip_path' in locals() and os.path.exists(zip_path):
                try:
                    os.remove(zip_path)
                except:
                    pass
            return None
    
    def cleanup_old_files(self, max_age_hours: int = 24) -> Dict:
        """
        Clean up old files from upload, converted, and temp directories
        
        Args:
            max_age_hours: Maximum age of files to keep (in hours)
            
        Returns:
            Dictionary with cleanup statistics
        """
        try:
            cutoff_time = time.time() - (max_age_hours * 3600)
            cleanup_stats = {
                'files_removed': 0,
                'space_freed_bytes': 0,
                'directories_cleaned': []
            }
            
            # Directories to clean
            directories = [
                self.upload_folder,
                self.converted_folder,
                self.temp_folder
            ]
            
            for directory in directories:
                if not os.path.exists(directory):
                    continue
                
                dir_stats = self._cleanup_directory(directory, cutoff_time)
                cleanup_stats['files_removed'] += dir_stats['files_removed']
                cleanup_stats['space_freed_bytes'] += dir_stats['space_freed']
                
                if dir_stats['files_removed'] > 0:
                    cleanup_stats['directories_cleaned'].append({
                        'directory': directory,
                        'files_removed': dir_stats['files_removed'],
                        'space_freed_bytes': dir_stats['space_freed']
                    })
            
            # Convert bytes to MB for easier reading
            cleanup_stats['space_freed_mb'] = round(cleanup_stats['space_freed_bytes'] / (1024 * 1024), 2)
            
            current_app.logger.info(
                f"Cleanup completed: {cleanup_stats['files_removed']} files removed, "
                f"{cleanup_stats['space_freed_mb']} MB freed"
            )
            
            return cleanup_stats
            
        except Exception as e:
            current_app.logger.error(f"Cleanup failed: {e}")
            return {'files_removed': 0, 'space_freed_bytes': 0, 'space_freed_mb': 0, 'error': str(e)}
    
    def _cleanup_directory(self, directory: str, cutoff_time: float) -> Dict:
        """
        Clean up files in a specific directory
        
        Args:
            directory: Directory path to clean
            cutoff_time: Cutoff timestamp for file age
            
        Returns:
            Dictionary with cleanup statistics for this directory
        """
        stats = {'files_removed': 0, 'space_freed': 0}
        
        try:
            for filename in os.listdir(directory):
                file_path = os.path.join(directory, filename)
                
                # Skip directories and .gitkeep files
                if os.path.isdir(file_path) or filename == '.gitkeep':
                    continue
                
                try:
                    # Check file age
                    file_mtime = os.path.getmtime(file_path)
                    if file_mtime < cutoff_time:
                        # Get file size before deletion
                        file_size = os.path.getsize(file_path)
                        
                        # Remove file
                        os.remove(file_path)
                        
                        stats['files_removed'] += 1
                        stats['space_freed'] += file_size
                        
                        current_app.logger.debug(f"Removed old file: {file_path}")
                        
                except Exception as e:
                    current_app.logger.warning(f"Could not remove file {file_path}: {e}")
                    continue
                    
        except Exception as e:
            current_app.logger.error(f"Error cleaning directory {directory}: {e}")
        
        return stats
    
    def get_file_info(self, file_path: str) -> Optional[Dict]:
        """
        Get information about a file
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dictionary with file information or None if file doesn't exist
        """
        try:
            if not os.path.exists(file_path):
                return None
            
            file_stats = os.stat(file_path)
            filename = os.path.basename(file_path)
            
            # Extract extension
            if '.' in filename:
                extension = filename.rsplit('.', 1)[1].lower()
            else:
                extension = ''
            
            return {
                'filename': filename,
                'path': file_path,
                'size': file_stats.st_size,
                'extension': extension,
                'mime_type': self._get_mime_type(file_path),
                'modified_at': datetime.fromtimestamp(file_stats.st_mtime).isoformat(),
                'checksum': self._calculate_checksum(file_path)
            }
            
        except Exception as e:
            current_app.logger.error(f"Error getting file info for {file_path}: {e}")
            return None
    
    def move_file(self, source_path: str, destination_path: str) -> bool:
        """
        Move a file from source to destination
        
        Args:
            source_path: Source file path
            destination_path: Destination file path
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure destination directory exists
            os.makedirs(os.path.dirname(destination_path), exist_ok=True)
            
            # Move file
            shutil.move(source_path, destination_path)
            
            current_app.logger.debug(f"File moved: {source_path} -> {destination_path}")
            return True
            
        except Exception as e:
            current_app.logger.error(f"Failed to move file {source_path} to {destination_path}: {e}")
            return False
    
    def copy_file(self, source_path: str, destination_path: str) -> bool:
        """
        Copy a file from source to destination
        
        Args:
            source_path: Source file path
            destination_path: Destination file path
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure destination directory exists
            os.makedirs(os.path.dirname(destination_path), exist_ok=True)
            
            # Copy file
            shutil.copy2(source_path, destination_path)
            
            current_app.logger.debug(f"File copied: {source_path} -> {destination_path}")
            return True
            
        except Exception as e:
            current_app.logger.error(f"Failed to copy file {source_path} to {destination_path}: {e}")
            return False
    
    def delete_file(self, file_path: str) -> bool:
        """
        Delete a file
        
        Args:
            file_path: Path to file to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                current_app.logger.debug(f"File deleted: {file_path}")
                return True
            else:
                current_app.logger.warning(f"File not found for deletion: {file_path}")
                return False
                
        except Exception as e:
            current_app.logger.error(f"Failed to delete file {file_path}: {e}")
            return False
    
    def get_directory_size(self, directory: str) -> int:
        """
        Get total size of all files in a directory
        
        Args:
            directory: Directory path
            
        Returns:
            Total size in bytes
        """
        try:
            total_size = 0
            for dirpath, dirnames, filenames in os.walk(directory):
                for filename in filenames:
                    file_path = os.path.join(dirpath, filename)
                    try:
                        total_size += os.path.getsize(file_path)
                    except (OSError, IOError):
                        continue
            return total_size
            
        except Exception as e:
            current_app.logger.error(f"Error calculating directory size for {directory}: {e}")
            return 0