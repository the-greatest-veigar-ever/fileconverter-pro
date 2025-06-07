"""
Conversion Models for FileConverter Pro

This module defines data models for tracking conversion jobs,
file information, and conversion statistics.
"""

import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict, field
from enum import Enum
import json


class ConversionStatus(Enum):
    """Enumeration of conversion job statuses"""
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class FileType(Enum):
    """Enumeration of file types"""
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    DOCUMENT = "document"
    PRESENTATION = "presentation"
    SPREADSHEET = "spreadsheet"
    ARCHIVE = "archive"
    FONT = "font"
    UNKNOWN = "unknown"


@dataclass
class FileInfo:
    """Information about a file"""
    id: str
    original_filename: str
    filename: str
    path: str
    size: int
    extension: str
    file_type: str
    mime_type: Optional[str] = None
    checksum: Optional[str] = None
    uploaded_at: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'FileInfo':
        """Create FileInfo from dictionary"""
        return cls(**data)
    
    def to_dict(self) -> Dict:
        """Convert FileInfo to dictionary"""
        return asdict(self)
    
    @property
    def size_mb(self) -> float:
        """Get file size in MB"""
        return round(self.size / (1024 * 1024), 2)
    
    @property
    def name_without_extension(self) -> str:
        """Get filename without extension"""
        if '.' in self.original_filename:
            return self.original_filename.rsplit('.', 1)[0]
        return self.original_filename


@dataclass
class ConvertedFile:
    """Information about a converted file"""
    id: str
    original_filename: str
    filename: str
    path: str
    size: int
    extension: str
    file_type: str
    converted_at: str
    conversion_time: float
    engine: str
    original_size: Optional[int] = None
    compression_ratio: Optional[float] = None
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ConvertedFile':
        """Create ConvertedFile from dictionary"""
        return cls(**data)
    
    def to_dict(self) -> Dict:
        """Convert ConvertedFile to dictionary"""
        return asdict(self)
    
    @property
    def size_mb(self) -> float:
        """Get file size in MB"""
        return round(self.size / (1024 * 1024), 2)
    
    @property
    def original_size_mb(self) -> float:
        """Get original file size in MB"""
        if self.original_size:
            return round(self.original_size / (1024 * 1024), 2)
        return 0.0


@dataclass
class ConversionError:
    """Information about a conversion error"""
    filename: str
    error_message: str
    error_code: Optional[str] = None
    timestamp: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat()
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ConversionError':
        """Create ConversionError from dictionary"""
        return cls(**data)
    
    def to_dict(self) -> Dict:
        """Convert ConversionError to dictionary"""
        return asdict(self)


@dataclass
class ConversionOptions:
    """Options for file conversion"""
    quality: Optional[int] = None
    resolution: Optional[tuple] = None
    bitrate: Optional[str] = None
    fps: Optional[int] = None
    codec: Optional[str] = None
    format_specific: Optional[Dict] = None
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ConversionOptions':
        """Create ConversionOptions from dictionary"""
        return cls(**data)
    
    def to_dict(self) -> Dict:
        """Convert ConversionOptions to dictionary"""
        result = asdict(self)
        # Remove None values
        return {k: v for k, v in result.items() if v is not None}


@dataclass
class ConversionProgress:
    """Progress information for a conversion job"""
    current: int = 0
    total: int = 0
    percentage: float = 0.0
    estimated_remaining_seconds: float = 0.0
    current_file: Optional[str] = None
    
    def update(self, current: int, total: int, current_file: Optional[str] = None):
        """Update progress information"""
        self.current = current
        self.total = total
        self.percentage = (current / total * 100) if total > 0 else 0
        if current_file:
            self.current_file = current_file
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ConversionProgress':
        """Create ConversionProgress from dictionary"""
        return cls(**data)
    
    def to_dict(self) -> Dict:
        """Convert ConversionProgress to dictionary"""
        return asdict(self)


@dataclass
class ConversionJob:
    """Model for a conversion job"""
    id: str
    status: ConversionStatus
    target_format: str
    created_at: str
    updated_at: str
    files: List[FileInfo] = field(default_factory=list)
    converted_files: List[ConvertedFile] = field(default_factory=list)
    errors: List[ConversionError] = field(default_factory=list)
    options: Optional[ConversionOptions] = None
    progress: Optional[ConversionProgress] = None
    total_files: int = 0
    completed_files: int = 0
    failed_files: int = 0
    total_processing_time: float = 0.0
    zip_path: Optional[str] = None
    expires_at: Optional[str] = None
    
    def __post_init__(self):
        """Post-initialization processing"""
        if isinstance(self.status, str):
            self.status = ConversionStatus(self.status)
        
        if self.total_files == 0:
            self.total_files = len(self.files)
        
        if self.progress is None:
            self.progress = ConversionProgress(total=self.total_files)
        
        # Convert dict objects to dataclass objects
        self.files = [FileInfo.from_dict(f) if isinstance(f, dict) else f for f in self.files]
        self.converted_files = [ConvertedFile.from_dict(f) if isinstance(f, dict) else f for f in self.converted_files]
        self.errors = [ConversionError.from_dict(e) if isinstance(e, dict) else e for e in self.errors]
        
        if isinstance(self.options, dict):
            self.options = ConversionOptions.from_dict(self.options)
        
        if isinstance(self.progress, dict):
            self.progress = ConversionProgress.from_dict(self.progress)
    
    @classmethod
    def create_new(cls, target_format: str, files: List[FileInfo], options: Optional[ConversionOptions] = None) -> 'ConversionJob':
        """Create a new conversion job"""
        job_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        
        return cls(
            id=job_id,
            status=ConversionStatus.QUEUED,
            target_format=target_format.lower(),
            created_at=now,
            updated_at=now,
            files=files,
            options=options or ConversionOptions(),
            total_files=len(files),
            progress=ConversionProgress(total=len(files))
        )
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ConversionJob':
        """Create ConversionJob from dictionary"""
        return cls(**data)
    
    def to_dict(self) -> Dict:
        """Convert ConversionJob to dictionary"""
        result = asdict(self)
        # Convert enum to string
        result['status'] = self.status.value
        return result
    
    def to_json(self) -> str:
        """Convert ConversionJob to JSON string"""
        return json.dumps(self.to_dict(), default=str)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'ConversionJob':
        """Create ConversionJob from JSON string"""
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    def update_status(self, status: ConversionStatus):
        """Update job status"""
        self.status = status
        self.updated_at = datetime.utcnow().isoformat()
    
    def add_converted_file(self, converted_file: ConvertedFile):
        """Add a successfully converted file"""
        self.converted_files.append(converted_file)
        self.completed_files = len(self.converted_files)
        self.progress.update(self.completed_files, self.total_files)
        self.updated_at = datetime.utcnow().isoformat()
    
    def add_error(self, error: ConversionError):
        """Add a conversion error"""
        self.errors.append(error)
        self.failed_files = len(self.errors)
        self.updated_at = datetime.utcnow().isoformat()
    
    def update_progress(self, current: int, current_file: Optional[str] = None):
        """Update job progress"""
        self.progress.update(current, self.total_files, current_file)
        self.updated_at = datetime.utcnow().isoformat()
    
    def set_zip_path(self, zip_path: str):
        """Set the path to the ZIP file containing all converted files"""
        self.zip_path = zip_path
        self.updated_at = datetime.utcnow().isoformat()
    
    def is_completed(self) -> bool:
        """Check if job is completed (successfully or with errors)"""
        return self.status in [ConversionStatus.COMPLETED, ConversionStatus.FAILED]
    
    def is_successful(self) -> bool:
        """Check if job completed successfully"""
        return self.status == ConversionStatus.COMPLETED and len(self.converted_files) > 0
    
    def has_errors(self) -> bool:
        """Check if job has any errors"""
        return len(self.errors) > 0
    
    def get_success_rate(self) -> float:
        """Get success rate as percentage"""
        if self.total_files == 0:
            return 0.0
        return (self.completed_files / self.total_files) * 100
    
    def get_total_input_size(self) -> int:
        """Get total size of input files"""
        return sum(file.size for file in self.files)
    
    def get_total_output_size(self) -> int:
        """Get total size of converted files"""
        return sum(file.size for file in self.converted_files)
    
    def get_compression_ratio(self) -> float:
        """Get overall compression ratio"""
        input_size = self.get_total_input_size()
        output_size = self.get_total_output_size()
        
        if input_size == 0:
            return 0.0
        
        return round((1 - output_size / input_size) * 100, 2)
    
    def get_summary(self) -> Dict:
        """Get job summary for API responses"""
        return {
            'id': self.id,
            'status': self.status.value,
            'target_format': self.target_format,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'progress': {
                'percentage': self.progress.percentage,
                'completed_files': self.completed_files,
                'total_files': self.total_files,
                'failed_files': self.failed_files
            },
            'statistics': {
                'success_rate': self.get_success_rate(),
                'total_input_size': self.get_total_input_size(),
                'total_output_size': self.get_total_output_size(),
                'compression_ratio': self.get_compression_ratio(),
                'processing_time': self.total_processing_time
            },
            'has_errors': self.has_errors(),
            'has_results': len(self.converted_files) > 0,
            'download_available': self.zip_path is not None
        }


class ConversionJobManager:
    """Manager class for conversion jobs"""
    
    def __init__(self):
        # In production, this would be replaced with Redis or database storage
        self._jobs: Dict[str, ConversionJob] = {}
    
    def create_job(self, target_format: str, files: List[Dict], options: Optional[Dict] = None) -> ConversionJob:
        """Create a new conversion job"""
        # Convert file dicts to FileInfo objects
        file_infos = [FileInfo.from_dict(f) for f in files]
        
        # Convert options dict to ConversionOptions
        conversion_options = ConversionOptions.from_dict(options) if options else None
        
        # Create job
        job = ConversionJob.create_new(target_format, file_infos, conversion_options)
        
        # Store job
        self._jobs[job.id] = job
        
        return job
    
    def get_job(self, job_id: str) -> Optional[ConversionJob]:
        """Get a conversion job by ID"""
        return self._jobs.get(job_id)
    
    def update_job(self, job: ConversionJob):
        """Update a conversion job"""
        self._jobs[job.id] = job
    
    def delete_job(self, job_id: str) -> bool:
        """Delete a conversion job"""
        if job_id in self._jobs:
            del self._jobs[job_id]
            return True
        return False
    
    def list_jobs(self, limit: int = 50, status: Optional[ConversionStatus] = None) -> List[ConversionJob]:
        """List conversion jobs with optional filtering"""
        jobs = list(self._jobs.values())
        
        if status:
            jobs = [job for job in jobs if job.status == status]
        
        # Sort by creation time (newest first)
        jobs.sort(key=lambda j: j.created_at, reverse=True)
        
        return jobs[:limit]
    
    def cleanup_expired_jobs(self, max_age_hours: int = 24) -> int:
        """Clean up expired jobs"""
        from datetime import timedelta
        
        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
        expired_jobs = []
        
        for job_id, job in self._jobs.items():
            job_time = datetime.fromisoformat(job.created_at.replace('Z', '+00:00'))
            if job_time < cutoff_time:
                expired_jobs.append(job_id)
        
        for job_id in expired_jobs:
            del self._jobs[job_id]
        
        return len(expired_jobs)
    
    def get_statistics(self) -> Dict:
        """Get overall conversion statistics"""
        total_jobs = len(self._jobs)
        completed_jobs = sum(1 for job in self._jobs.values() if job.status == ConversionStatus.COMPLETED)
        failed_jobs = sum(1 for job in self._jobs.values() if job.status == ConversionStatus.FAILED)
        processing_jobs = sum(1 for job in self._jobs.values() if job.status == ConversionStatus.PROCESSING)
        
        total_files_processed = sum(job.total_files for job in self._jobs.values())
        total_files_converted = sum(job.completed_files for job in self._jobs.values())
        
        return {
            'total_jobs': total_jobs,
            'completed_jobs': completed_jobs,
            'failed_jobs': failed_jobs,
            'processing_jobs': processing_jobs,
            'success_rate': (completed_jobs / total_jobs * 100) if total_jobs > 0 else 0,
            'total_files_processed': total_files_processed,
            'total_files_converted': total_files_converted,
            'file_success_rate': (total_files_converted / total_files_processed * 100) if total_files_processed > 0 else 0
        }


# Global job manager instance
job_manager = ConversionJobManager()