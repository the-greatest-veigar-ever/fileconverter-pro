"""
Main Web Routes for FileConverter Pro

This module contains the main web routes that serve HTML pages
for the user interface.
"""

import os
from flask import Blueprint, render_template, current_app, jsonify, request

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """
    Main landing page with file conversion interface
    
    Returns:
        Rendered HTML template with conversion interface
    """
    try:
        # Get supported file types from config
        supported_formats = current_app.config['ALLOWED_EXTENSIONS']
        
        # Calculate total supported formats
        total_formats = sum(len(formats) for formats in supported_formats.values())
        
        # Get conversion engines info
        conversion_engines = current_app.config['CONVERSION_ENGINES']
        
        return render_template('index.html',
            supported_formats=supported_formats,
            total_formats=total_formats,
            conversion_engines=conversion_engines,
            max_file_size=current_app.config['MAX_FILE_SIZE_MB'],
            max_files=current_app.config['MAX_FILES_PER_BATCH']
        )
        
    except Exception as e:
        current_app.logger.error(f"Error rendering index page: {e}")
        return render_template('error.html', 
            error_title="Page Load Error",
            error_message="Unable to load the conversion interface. Please try again."
        ), 500

@main_bp.route('/convert')
def convert_page():
    """
    Conversion status and results page
    
    Returns:
        Rendered HTML template for conversion tracking
    """
    try:
        job_id = request.args.get('job_id')
        
        if not job_id:
            return render_template('convert.html', job_id=None)
        
        return render_template('convert.html', job_id=job_id)
        
    except Exception as e:
        current_app.logger.error(f"Error rendering convert page: {e}")
        return render_template('error.html',
            error_title="Conversion Page Error",
            error_message="Unable to load the conversion page. Please try again."
        ), 500

@main_bp.route('/about')
def about():
    """
    About page with application information
    
    Returns:
        Rendered HTML template with application details
    """
    try:
        # Application statistics
        app_stats = {
            'supported_formats': sum(len(formats) for formats in current_app.config['ALLOWED_EXTENSIONS'].values()),
            'format_categories': len(current_app.config['ALLOWED_EXTENSIONS']),
            'max_file_size': current_app.config['MAX_FILE_SIZE_MB'],
            'max_batch_size': current_app.config['MAX_FILES_PER_BATCH'],
            'conversion_engines': list(set(
                engine for engines in current_app.config['CONVERSION_ENGINES'].values()
                for engine in engines
            ))
        }
        
        return render_template('about.html', app_stats=app_stats)
        
    except Exception as e:
        current_app.logger.error(f"Error rendering about page: {e}")
        return render_template('error.html',
            error_title="About Page Error",
            error_message="Unable to load the about page. Please try again."
        ), 500

@main_bp.route('/privacy')
def privacy():
    """
    Privacy policy page
    
    Returns:
        Rendered HTML template with privacy policy
    """
    return render_template('privacy.html')

@main_bp.route('/terms')
def terms():
    """
    Terms of service page
    
    Returns:
        Rendered HTML template with terms of service
    """
    return render_template('terms.html')

@main_bp.route('/formats')
def formats():
    """
    Supported formats page with detailed format information
    
    Returns:
        JSON or HTML response with supported formats
    """
    try:
        supported_formats = current_app.config['ALLOWED_EXTENSIONS']
        
        # If request wants JSON (for API)
        if request.headers.get('Accept') == 'application/json':
            return jsonify({
                'supported_formats': supported_formats,
                'total_formats': sum(len(formats) for formats in supported_formats.values()),
                'categories': list(supported_formats.keys())
            })
        
        # Otherwise render HTML page
        return render_template('formats.html', supported_formats=supported_formats)
        
    except Exception as e:
        current_app.logger.error(f"Error in formats endpoint: {e}")
        
        if request.headers.get('Accept') == 'application/json':
            return jsonify({'error': 'Unable to retrieve supported formats'}), 500
        else:
            return render_template('error.html',
                error_title="Formats Page Error",
                error_message="Unable to load the supported formats page."
            ), 500

@main_bp.route('/help')
def help_page():
    """
    Help and documentation page
    
    Returns:
        Rendered HTML template with help content
    """
    try:
        # Help topics and FAQ
        help_topics = [
            {
                'title': 'Getting Started',
                'description': 'Learn how to convert your first file',
                'icon': 'play-circle'
            },
            {
                'title': 'Supported Formats',
                'description': 'View all supported file formats',
                'icon': 'file-text'
            },
            {
                'title': 'Batch Conversion',
                'description': 'Convert multiple files at once',
                'icon': 'layers'
            },
            {
                'title': 'Quality Settings',
                'description': 'Optimize output quality and size',
                'icon': 'settings'
            },
            {
                'title': 'Troubleshooting',
                'description': 'Common issues and solutions',
                'icon': 'help-circle'
            }
        ]
        
        faq = [
            {
                'question': 'What is the maximum file size I can upload?',
                'answer': f'You can upload files up to {current_app.config["MAX_FILE_SIZE_MB"]}MB in size.'
            },
            {
                'question': 'How many files can I convert at once?',
                'answer': f'You can convert up to {current_app.config["MAX_FILES_PER_BATCH"]} files in a single batch.'
            },
            {
                'question': 'Are my files stored on your servers?',
                'answer': 'No, all files are automatically deleted after conversion. We do not store your files permanently.'
            },
            {
                'question': 'Which formats are supported?',
                'answer': f'We support over {sum(len(formats) for formats in current_app.config["ALLOWED_EXTENSIONS"].values())} different file formats across images, videos, audio, documents, and more.'
            },
            {
                'question': 'Is the service free to use?',
                'answer': 'Yes, FileConverter Pro is completely free to use with no registration required.'
            }
        ]
        
        return render_template('help.html', 
            help_topics=help_topics,
            faq=faq
        )
        
    except Exception as e:
        current_app.logger.error(f"Error rendering help page: {e}")
        return render_template('error.html',
            error_title="Help Page Error",
            error_message="Unable to load the help page. Please try again."
        ), 500

@main_bp.errorhandler(404)
def page_not_found(error):
    """
    Custom 404 error handler
    
    Returns:
        Rendered 404 error page
    """
    return render_template('error.html',
        error_title="Page Not Found",
        error_message="The page you're looking for doesn't exist.",
        error_code=404
    ), 404

@main_bp.errorhandler(500)
def internal_server_error(error):
    """
    Custom 500 error handler
    
    Returns:
        Rendered 500 error page
    """
    current_app.logger.error(f"Internal server error: {error}")
    return render_template('error.html',
        error_title="Internal Server Error",
        error_message="Something went wrong on our end. Please try again later.",
        error_code=500
    ), 500

# Context processors for templates
@main_bp.app_context_processor
def inject_global_vars():
    """
    Inject global variables into all templates
    
    Returns:
        Dictionary of global template variables
    """
    return {
        'app_name': 'FileConverter Pro',
        'app_version': '1.0.0',
        'max_file_size_mb': current_app.config['MAX_FILE_SIZE_MB'],
        'max_files_per_batch': current_app.config['MAX_FILES_PER_BATCH'],
        'total_supported_formats': sum(
            len(formats) for formats in current_app.config['ALLOWED_EXTENSIONS'].values()
        )
    }