"""
Models package for FileConverter Pro

This package contains data models for file conversion operations,
job tracking, and related entities.
"""

from .conversion import (
    ConversionStatus,
    FileType,
    FileInfo,
    ConvertedFile,
    ConversionError,
    ConversionOptions,
    ConversionProgress,
    ConversionJob,
    ConversionJobManager,
    job_manager
)

__all__ = [
    'ConversionStatus',
    'FileType', 
    'FileInfo',
    'ConvertedFile',
    'ConversionError',
    'ConversionOptions',
    'ConversionProgress',
    'ConversionJob',
    'ConversionJobManager',
    'job_manager'
]

# Version info
__version__ = '1.0.0'
__author__ = 'FileConverter Pro Team'