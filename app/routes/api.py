"""
API Routes for FileConverter Pro

This module contains all REST API endpoints for file conversion,
upload handling, status checking, and file downloads.
"""

import os
import uuid
import json
import time
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, current_app, send_file, abort
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge

# Import our services (we'll create these next)
from app.services.file_handler import FileHandler
from app.services.converter import ConversionService
from app.utils.validators import FileValidator
from app.utils.helpers import format_file_size, get_file_type

api_bp = Blueprint("api", __name__)

# In-memory storage for conversion jobs (in production, use Redis or database)
conversion_jobs = {}


@api_bp.route("/upload", methods=["POST"])
def upload_files():
    """
    Upload files for conversion

    Expected form data:
        files: List of files to upload
        target_format: Target format for conversion (optional)

    Returns:
        JSON response with upload status and file information
    """
    try:
        # Check if files are present
        if "files" not in request.files:
            return (
                jsonify(
                    {
                        "error": "No files provided",
                        "message": "Please select files to upload",
                    }
                ),
                400,
            )

        files = request.files.getlist("files")
        target_format = request.form.get("target_format", "").lower()

        # Validate number of files
        if len(files) == 0:
            return (
                jsonify(
                    {
                        "error": "No files selected",
                        "message": "Please select at least one file",
                    }
                ),
                400,
            )

        if len(files) > current_app.config["MAX_FILES_PER_BATCH"]:
            return (
                jsonify(
                    {
                        "error": "Too many files",
                        "message": f'Maximum {current_app.config["MAX_FILES_PER_BATCH"]} files allowed per batch',
                    }
                ),
                400,
            )

        # Process each file
        uploaded_files = []
        file_handler = FileHandler()
        validator = FileValidator()

        for file in files:
            if file.filename == "":
                continue

            try:
                # Validate file
                validation_result = validator.validate_file(file)
                if not validation_result["valid"]:
                    uploaded_files.append(
                        {
                            "filename": file.filename,
                            "status": "error",
                            "error": validation_result["error"],
                        }
                    )
                    continue

                # Save file
                file_info = file_handler.save_uploaded_file(file)
                file_info.update(
                    {
                        "status": "uploaded",
                        "file_type": get_file_type(file_info["extension"]),
                        "size_formatted": format_file_size(file_info["size"]),
                    }
                )

                uploaded_files.append(file_info)

            except Exception as e:
                current_app.logger.error(f"Error processing file {file.filename}: {e}")
                uploaded_files.append(
                    {
                        "filename": file.filename,
                        "status": "error",
                        "error": f"Upload failed: {str(e)}",
                    }
                )

        # Check if any files were successfully uploaded
        successful_uploads = [f for f in uploaded_files if f["status"] == "uploaded"]
        if not successful_uploads:
            return (
                jsonify(
                    {"error": "No files uploaded successfully", "files": uploaded_files}
                ),
                400,
            )

        return (
            jsonify(
                {
                    "message": f"Successfully uploaded {len(successful_uploads)} file(s)",
                    "files": uploaded_files,
                    "total_files": len(uploaded_files),
                    "successful_uploads": len(successful_uploads),
                    "target_format": target_format if target_format else None,
                }
            ),
            200,
        )

    except RequestEntityTooLarge:
        return (
            jsonify(
                {
                    "error": "File too large",
                    "message": f'File size exceeds the maximum limit of {current_app.config["MAX_FILE_SIZE_MB"]}MB',
                }
            ),
            413,
        )

    except Exception as e:
        current_app.logger.error(f"Upload error: {e}")
        return (
            jsonify(
                {
                    "error": "Upload failed",
                    "message": "An unexpected error occurred during upload",
                }
            ),
            500,
        )


@api_bp.route("/convert", methods=["POST"])
def convert_files():
    """
    Convert uploaded files to target format

    Expected JSON data:
        files: List of file information from upload
        target_format: Target format for conversion
        options: Conversion options (quality, resolution, etc.)

    Returns:
        JSON response with conversion job ID and status
    """
    try:
        data = request.get_json()

        if not data:
            return (
                jsonify(
                    {
                        "error": "No data provided",
                        "message": "Please provide conversion parameters",
                    }
                ),
                400,
            )

        files = data.get("files", [])
        target_format = data.get("target_format", "").lower().strip()
        options = data.get("options", {})

        # Validate input
        if not files:
            return (
                jsonify(
                    {
                        "error": "No files provided",
                        "message": "Please provide files to convert",
                    }
                ),
                400,
            )

        validator = FileValidator()

        if not target_format:
            target_format = None

        if target_format and not validator.is_format_supported(target_format):
            return (
                jsonify(
                    {
                        "error": "Unsupported target format",
                        "message": f'Format "{target_format}" is not supported',
                    }
                ),
                400,
            )

        # Validate each file target format
        for file in files:
            file_ext = file.get("extension", "").lower()
            file_target = (
                (file.get("target_format") or target_format or "").lower().strip()
            )
            if not file_target:
                return (
                    jsonify(
                        {
                            "error": "No target format specified",
                            "message": f'Missing target format for file {file.get("filename")}',
                        }
                    ),
                    400,
                )
            if not validator.is_format_supported(file_target):
                return (
                    jsonify(
                        {
                            "error": "Unsupported target format",
                            "message": f'Format "{file_target}" is not supported',
                        }
                    ),
                    400,
                )

            source_cat = validator.get_format_category(file_ext)
            target_cat = validator.get_format_category(file_target)
            if source_cat != target_cat:
                return (
                    jsonify(
                        {
                            "error": "Invalid target format",
                            "message": f"{file_target} not allowed for {file_ext}",
                        }
                    ),
                    400,
                )

            file["target_format"] = file_target

        # Create conversion job
        job_id = str(uuid.uuid4())
        job_data = {
            "id": job_id,
            "status": "queued",
            "files": files,
            "target_format": target_format,
            "options": options,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "progress": 0,
            "total_files": len(files),
            "completed_files": 0,
            "converted_files": [],
            "errors": [],
        }

        # Store job in memory (in production, use Redis or database)
        conversion_jobs[job_id] = job_data

        # Start conversion process (this would typically be a Celery task)
        try:
            conversion_service = ConversionService()
            # For now, we'll simulate async processing
            # In production, this would be: conversion_service.convert_batch.delay(job_id)
            result = conversion_service.convert_batch(
                job_id, files, target_format, options
            )

            # Update job status
            conversion_jobs[job_id].update(
                {
                    "status": "completed" if result["success"] else "failed",
                    "updated_at": datetime.utcnow().isoformat(),
                    "progress": 100,
                    "completed_files": result.get("completed_count", 0),
                    "converted_files": result.get("converted_files", []),
                    "errors": result.get("errors", []),
                }
            )

        except Exception as e:
            current_app.logger.error(f"Conversion failed for job {job_id}: {e}")
            conversion_jobs[job_id].update(
                {
                    "status": "failed",
                    "updated_at": datetime.utcnow().isoformat(),
                    "errors": [f"Conversion failed: {str(e)}"],
                }
            )

        return (
            jsonify(
                {
                    "message": "Conversion job created successfully",
                    "job_id": job_id,
                    "status": conversion_jobs[job_id]["status"],
                    "estimated_time": len(files) * 2,  # 2 seconds per file estimate
                }
            ),
            202,
        )

    except Exception as e:
        current_app.logger.error(f"Convert error: {e}")
        return (
            jsonify(
                {
                    "error": "Conversion failed",
                    "message": "An unexpected error occurred during conversion setup",
                }
            ),
            500,
        )


@api_bp.route("/status/<job_id>", methods=["GET"])
def get_conversion_status(job_id):
    """
    Get conversion job status and progress

    Args:
        job_id: Conversion job ID

    Returns:
        JSON response with job status and progress
    """
    try:
        if job_id not in conversion_jobs:
            return (
                jsonify(
                    {
                        "error": "Job not found",
                        "message": f"Conversion job {job_id} does not exist",
                    }
                ),
                404,
            )

        job = conversion_jobs[job_id]

        # Calculate progress details
        progress_details = {
            "percentage": job["progress"],
            "completed_files": job["completed_files"],
            "total_files": job["total_files"],
            "remaining_files": job["total_files"] - job["completed_files"],
        }

        # Calculate estimated time remaining
        if job["status"] == "processing" and job["progress"] > 0:
            elapsed_time = (
                datetime.utcnow() - datetime.fromisoformat(job["created_at"])
            ).total_seconds()
            estimated_total = elapsed_time / (job["progress"] / 100)
            estimated_remaining = max(0, estimated_total - elapsed_time)
        else:
            estimated_remaining = 0

        response_data = {
            "job_id": job_id,
            "status": job["status"],
            "progress": progress_details,
            "created_at": job["created_at"],
            "updated_at": job["updated_at"],
            "estimated_remaining_seconds": int(estimated_remaining),
            "target_format": job["target_format"],
        }

        # Include results if completed
        if job["status"] in ["completed", "failed"]:
            response_data.update(
                {"converted_files": job["converted_files"], "errors": job["errors"]}
            )

        return jsonify(response_data), 200

    except Exception as e:
        current_app.logger.error(f"Status check error for job {job_id}: {e}")
        return (
            jsonify(
                {
                    "error": "Status check failed",
                    "message": "Unable to retrieve job status",
                }
            ),
            500,
        )


@api_bp.route("/download/<job_id>", methods=["GET"])
def download_converted_files(job_id):
    """
    Download converted files as a ZIP archive

    Args:
        job_id: Conversion job ID

    Returns:
        ZIP file with converted files or JSON error
    """
    try:
        if job_id not in conversion_jobs:
            return (
                jsonify(
                    {
                        "error": "Job not found",
                        "message": f"Conversion job {job_id} does not exist",
                    }
                ),
                404,
            )

        job = conversion_jobs[job_id]

        if job["status"] != "completed":
            return (
                jsonify(
                    {
                        "error": "Job not completed",
                        "message": f'Job status is "{job["status"]}", not ready for download',
                    }
                ),
                400,
            )

        if not job["converted_files"]:
            return (
                jsonify(
                    {
                        "error": "No files available",
                        "message": "No converted files available for download",
                    }
                ),
                404,
            )

        # Create ZIP file with converted files
        file_handler = FileHandler()
        zip_path = file_handler.create_download_zip(job_id, job["converted_files"])

        if not zip_path or not os.path.exists(zip_path):
            return (
                jsonify(
                    {
                        "error": "Download preparation failed",
                        "message": "Unable to prepare files for download",
                    }
                ),
                500,
            )

        # Send ZIP file
        return send_file(
            zip_path,
            as_attachment=True,
            download_name=f"converted_files_{job_id[:8]}.zip",
            mimetype="application/zip",
        )

    except Exception as e:
        current_app.logger.error(f"Download error for job {job_id}: {e}")
        return (
            jsonify(
                {
                    "error": "Download failed",
                    "message": "Unable to download converted files",
                }
            ),
            500,
        )


@api_bp.route("/download/<job_id>/<filename>", methods=["GET"])
def download_single_file(job_id, filename):
    """
    Download a single converted file

    Args:
        job_id: Conversion job ID
        filename: Name of the file to download

    Returns:
        File download or JSON error
    """
    try:
        if job_id not in conversion_jobs:
            return (
                jsonify(
                    {
                        "error": "Job not found",
                        "message": f"Conversion job {job_id} does not exist",
                    }
                ),
                404,
            )

        job = conversion_jobs[job_id]

        if job["status"] != "completed":
            return (
                jsonify(
                    {
                        "error": "Job not completed",
                        "message": f'Job status is "{job["status"]}", not ready for download',
                    }
                ),
                400,
            )

        # Find the requested file
        target_file = None
        for file_info in job["converted_files"]:
            if file_info["filename"] == filename:
                target_file = file_info
                break

        if not target_file:
            return (
                jsonify(
                    {
                        "error": "File not found",
                        "message": f'File "{filename}" not found in conversion results',
                    }
                ),
                404,
            )

        file_path = target_file["path"]
        if not os.path.exists(file_path):
            return (
                jsonify(
                    {
                        "error": "File not available",
                        "message": "The requested file is no longer available",
                    }
                ),
                404,
            )

        return send_file(file_path, as_attachment=True, download_name=filename)

    except Exception as e:
        current_app.logger.error(f"Single file download error: {e}")
        return (
            jsonify(
                {
                    "error": "Download failed",
                    "message": "Unable to download the requested file",
                }
            ),
            500,
        )


@api_bp.route("/formats", methods=["GET"])
def get_supported_formats():
    """
    Get list of supported file formats

    Returns:
        JSON response with supported formats by category
    """
    try:
        supported_formats = current_app.config["ALLOWED_EXTENSIONS"]
        conversion_engines = current_app.config["CONVERSION_ENGINES"]

        # Add engine information to each category
        formats_with_engines = {}
        for category, formats in supported_formats.items():
            formats_with_engines[category] = {
                "formats": sorted(formats),
                "count": len(formats),
                "engines": conversion_engines.get(category, []),
            }

        return (
            jsonify(
                {
                    "supported_formats": formats_with_engines,
                    "total_formats": sum(
                        len(formats) for formats in supported_formats.values()
                    ),
                    "categories": list(supported_formats.keys()),
                    "last_updated": datetime.utcnow().isoformat(),
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Formats endpoint error: {e}")
        return (
            jsonify(
                {
                    "error": "Unable to retrieve supported formats",
                    "message": "An error occurred while fetching format information",
                }
            ),
            500,
        )


@api_bp.route("/jobs", methods=["GET"])
def list_conversion_jobs():
    """
    List recent conversion jobs (for debugging/monitoring)

    Returns:
        JSON response with job list
    """
    try:
        # Get recent jobs (last 24 hours)
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        recent_jobs = []

        for job_id, job in conversion_jobs.items():
            job_time = datetime.fromisoformat(job["created_at"])
            if job_time > cutoff_time:
                recent_jobs.append(
                    {
                        "job_id": job_id,
                        "status": job["status"],
                        "created_at": job["created_at"],
                        "total_files": job["total_files"],
                        "completed_files": job["completed_files"],
                        "target_format": job["target_format"],
                    }
                )

        # Sort by creation time (newest first)
        recent_jobs.sort(key=lambda x: x["created_at"], reverse=True)

        return (
            jsonify(
                {
                    "jobs": recent_jobs[:50],  # Limit to 50 most recent
                    "total_count": len(recent_jobs),
                    "cutoff_time": cutoff_time.isoformat(),
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Jobs list error: {e}")
        return (
            jsonify(
                {
                    "error": "Unable to retrieve job list",
                    "message": "An error occurred while fetching job information",
                }
            ),
            500,
        )


@api_bp.route("/cleanup", methods=["POST"])
def cleanup_old_files():
    """
    Cleanup old files and completed jobs (admin endpoint)

    Returns:
        JSON response with cleanup results
    """
    try:
        file_handler = FileHandler()
        cleanup_result = file_handler.cleanup_old_files()

        # Also cleanup old job records (older than 24 hours)
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        jobs_cleaned = 0

        jobs_to_remove = []
        for job_id, job in conversion_jobs.items():
            job_time = datetime.fromisoformat(job["created_at"])
            if job_time < cutoff_time:
                jobs_to_remove.append(job_id)

        for job_id in jobs_to_remove:
            del conversion_jobs[job_id]
            jobs_cleaned += 1

        return (
            jsonify(
                {
                    "message": "Cleanup completed successfully",
                    "files_removed": cleanup_result.get("files_removed", 0),
                    "space_freed_mb": cleanup_result.get("space_freed_mb", 0),
                    "jobs_cleaned": jobs_cleaned,
                    "cleanup_time": datetime.utcnow().isoformat(),
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Cleanup error: {e}")
        return (
            jsonify(
                {
                    "error": "Cleanup failed",
                    "message": "An error occurred during cleanup",
                }
            ),
            500,
        )


# Error handlers for API routes
@api_bp.errorhandler(413)
def handle_file_too_large(error):
    """Handle file too large errors"""
    return (
        jsonify(
            {
                "error": "File too large",
                "message": f'File size exceeds the maximum limit of {current_app.config["MAX_FILE_SIZE_MB"]}MB',
            }
        ),
        413,
    )


@api_bp.errorhandler(404)
def handle_api_not_found(error):
    """Handle API endpoint not found"""
    return (
        jsonify(
            {
                "error": "Endpoint not found",
                "message": "The requested API endpoint does not exist",
            }
        ),
        404,
    )


@api_bp.errorhandler(500)
def handle_api_internal_error(error):
    """Handle internal server errors in API"""
    current_app.logger.error(f"API internal error: {error}")
    return (
        jsonify(
            {
                "error": "Internal server error",
                "message": "An unexpected error occurred",
            }
        ),
        500,
    )
