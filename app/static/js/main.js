/**
 * FileConverter Pro - Main JavaScript
 * Core functionality and utilities for the application
 */

'use strict';

// Global App Object
window.FileConverterPro = {
    version: '1.0.0',
    debug: false,
    
    // Application state
    state: {
        theme: 'light',
        files: [],
        selectedFormat: null,
        conversionOptions: {},
        currentJob: null
    },
    
    // Configuration
    config: {
        maxFileSize: 100 * 1024 * 1024, // 100MB
        maxFiles: 50,
        allowedTypes: [
            'image', 'video', 'audio', 'document', 
            'presentation', 'spreadsheet', 'archive', 'font'
        ],
        apiEndpoints: {
            upload: '/api/upload',
            convert: '/api/convert',
            status: '/api/status',
            download: '/api/download',
            formats: '/api/formats'
        }
    },
    
    // Utility functions
    utils: {},
    
    // Components
    components: {},
    
    // Event handlers
    events: {},
    
    // API methods
    api: {}
};

const App = window.FileConverterPro;

/**
 * =============================================================================
 * UTILITY FUNCTIONS
 * =============================================================================
 */

App.utils = {
    /**
     * Format file size in human readable format
     */
    formatFileSize(bytes) {
        if (bytes === 0) return '0 B';
        
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
    },
    
    /**
     * Format duration in human readable format
     */
    formatDuration(seconds) {
        if (seconds < 1) return `${Math.round(seconds * 1000)}ms`;
        if (seconds < 60) return `${Math.round(seconds)}s`;
        
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = Math.round(seconds % 60);
        
        if (minutes < 60) {
            return `${minutes}m ${remainingSeconds}s`;
        }
        
        const hours = Math.floor(minutes / 60);
        const remainingMinutes = minutes % 60;
        return `${hours}h ${remainingMinutes}m`;
    },
    
    /**
     * Get file extension from filename
     */
    getFileExtension(filename) {
        return filename.toLowerCase().split('.').pop();
    },
    
    /**
     * Get file type category from extension
     */
    getFileType(extension) {
        const typeMap = {
            // Images
            'jpg': 'image', 'jpeg': 'image', 'png': 'image', 'gif': 'image',
            'bmp': 'image', 'tiff': 'image', 'webp': 'image', 'svg': 'image',
            'jfif': 'image', 'ico': 'image', 'heic': 'image', 'avif': 'image',
            
            // Videos
            'mp4': 'video', 'avi': 'video', 'mov': 'video', 'wmv': 'video',
            'flv': 'video', 'webm': 'video', 'mkv': 'video', '3gp': 'video',
            'm4v': 'video', 'f4v': 'video', 'asf': 'video', 'rm': 'video',
            
            // Audio
            'mp3': 'audio', 'wav': 'audio', 'flac': 'audio', 'aac': 'audio',
            'ogg': 'audio', 'wma': 'audio', 'm4a': 'audio', 'opus': 'audio',
            'aiff': 'audio', 'mid': 'audio', 'midi': 'audio',
            
            // Documents
            'pdf': 'document', 'doc': 'document', 'docx': 'document', 'txt': 'document',
            'rtf': 'document', 'odt': 'document', 'epub': 'document', 'mobi': 'document',
            
            // Presentations
            'ppt': 'presentation', 'pptx': 'presentation', 'odp': 'presentation', 'key': 'presentation',
            
            // Spreadsheets
            'xlsx': 'spreadsheet', 'xls': 'spreadsheet', 'csv': 'spreadsheet', 'ods': 'spreadsheet',
            'tsv': 'spreadsheet', 'numbers': 'spreadsheet',
            
            // Archives
            'zip': 'archive', 'rar': 'archive', '7z': 'archive', 'tar': 'archive',
            'gz': 'archive', 'bz2': 'archive',
            
            // Fonts
            'ttf': 'font', 'otf': 'font', 'woff': 'font', 'woff2': 'font', 'eot': 'font'
        };
        
        return typeMap[extension] || 'unknown';
    },
    
    /**
     * Generate unique ID
     */
    generateId() {
        return Date.now().toString(36) + Math.random().toString(36).substr(2);
    },
    
    /**
     * Debounce function
     */
    debounce(func, wait, immediate = false) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                timeout = null;
                if (!immediate) func(...args);
            };
            const callNow = immediate && !timeout;
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
            if (callNow) func(...args);
        };
    },
    
    /**
     * Throttle function
     */
    throttle(func, limit) {
        let inThrottle;
        return function() {
            const args = arguments;
            const context = this;
            if (!inThrottle) {
                func.apply(context, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    },
    
    /**
     * Deep clone object
     */
    deepClone(obj) {
        return JSON.parse(JSON.stringify(obj));
    },
    
    /**
     * Check if element is in viewport
     */
    isInViewport(element) {
        const rect = element.getBoundingClientRect();
        return (
            rect.top >= 0 &&
            rect.left >= 0 &&
            rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
            rect.right <= (window.innerWidth || document.documentElement.clientWidth)
        );
    },
    
    /**
     * Smooth scroll to element
     */
    scrollToElement(element, offset = 0) {
        const elementPosition = element.offsetTop - offset;
        window.scrollTo({
            top: elementPosition,
            behavior: 'smooth'
        });
    },
    
    /**
     * Copy text to clipboard
     */
    async copyToClipboard(text) {
        try {
            await navigator.clipboard.writeText(text);
            return true;
        } catch (err) {
            // Fallback for older browsers
            const textArea = document.createElement('textarea');
            textArea.value = text;
            document.body.appendChild(textArea);
            textArea.focus();
            textArea.select();
            try {
                document.execCommand('copy');
                document.body.removeChild(textArea);
                return true;
            } catch (err) {
                document.body.removeChild(textArea);
                return false;
            }
        }
    }
};

/**
 * =============================================================================
 * TOAST NOTIFICATIONS
 * =============================================================================
 */

App.utils.showToast = function(message, type = 'info', duration = 5000) {
    const container = document.getElementById('toast-container');
    if (!container) return;
    
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
        <div class="toast-content">
            <div class="toast-icon">
                <i data-feather="${getToastIcon(type)}"></i>
            </div>
            <div class="toast-message">${message}</div>
            <button class="toast-close" onclick="this.parentElement.parentElement.remove()">
                <i data-feather="x"></i>
            </button>
        </div>
    `;
    
    container.appendChild(toast);
    
    // Initialize feather icons
    if (window.feather) {
        feather.replace();
    }
    
    // Auto remove after duration
    if (duration > 0) {
        setTimeout(() => {
            if (toast.parentElement) {
                toast.style.animation = 'slideOutRight 0.3s ease-in';
                setTimeout(() => toast.remove(), 300);
            }
        }, duration);
    }
    
    function getToastIcon(type) {
        const icons = {
            success: 'check-circle',
            error: 'x-circle',
            warning: 'alert-triangle',
            info: 'info'
        };
        return icons[type] || 'info';
    }
};

/**
 * =============================================================================
 * THEME MANAGEMENT
 * =============================================================================
 */

App.components.theme = {
    init() {
        this.loadTheme();
        this.bindEvents();
    },
    
    loadTheme() {
        const savedTheme = localStorage.getItem('theme') || 'light';
        this.setTheme(savedTheme);
    },
    
    setTheme(theme) {
        App.state.theme = theme;
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('theme', theme);
        
        // Update theme toggle button
        const themeToggle = document.getElementById('theme-toggle');
        if (themeToggle) {
            themeToggle.setAttribute('aria-label', `Switch to ${theme === 'light' ? 'dark' : 'light'} theme`);
        }
    },
    
    toggleTheme() {
        const newTheme = App.state.theme === 'light' ? 'dark' : 'light';
        this.setTheme(newTheme);
        
        // Add transition class for smooth theme switching
        document.body.classList.add('theme-transitioning');
        setTimeout(() => {
            document.body.classList.remove('theme-transitioning');
        }, 300);
    },
    
    bindEvents() {
        const themeToggle = document.getElementById('theme-toggle');
        if (themeToggle) {
            themeToggle.addEventListener('click', () => this.toggleTheme());
        }
    }
};

/**
 * =============================================================================
 * NAVIGATION
 * =============================================================================
 */

App.components.navigation = {
    init() {
        this.bindEvents();
        this.handleScroll();
    },
    
    bindEvents() {
        // Mobile menu toggle
        const navToggle = document.getElementById('nav-toggle');
        const navMenu = document.getElementById('nav-menu');
        
        if (navToggle && navMenu) {
            navToggle.addEventListener('click', () => {
                navMenu.classList.toggle('active');
                navToggle.classList.toggle('active');
            });
        }
        
        // Close mobile menu when clicking outside
        document.addEventListener('click', (e) => {
            if (navMenu && !navMenu.contains(e.target) && !navToggle.contains(e.target)) {
                navMenu.classList.remove('active');
                navToggle.classList.remove('active');
            }
        });
        
        // Close mobile menu when clicking on links
        const navLinks = document.querySelectorAll('.nav-link');
        navLinks.forEach(link => {
            link.addEventListener('click', () => {
                if (navMenu) navMenu.classList.remove('active');
                if (navToggle) navToggle.classList.remove('active');
            });
        });
        
        // Header scroll effect
        window.addEventListener('scroll', App.utils.throttle(() => {
            this.handleScroll();
        }, 100));
    },
    
    handleScroll() {
        const header = document.getElementById('main-header');
        if (header) {
            if (window.scrollY > 100) {
                header.classList.add('scrolled');
            } else {
                header.classList.remove('scrolled');
            }
        }
    }
};

/**
 * =============================================================================
 * BACK TO TOP
 * =============================================================================
 */

App.components.backToTop = {
    init() {
        this.createButton();
        this.bindEvents();
    },
    
    createButton() {
        let backToTop = document.getElementById('back-to-top');
        if (!backToTop) {
            backToTop = document.createElement('button');
            backToTop.id = 'back-to-top';
            backToTop.className = 'back-to-top';
            backToTop.setAttribute('aria-label', 'Back to top');
            backToTop.innerHTML = '<i data-feather="arrow-up"></i>';
            document.body.appendChild(backToTop);
            
            if (window.feather) {
                feather.replace();
            }
        }
    },
    
    bindEvents() {
        const backToTop = document.getElementById('back-to-top');
        if (!backToTop) return;
        
        // Show/hide on scroll
        window.addEventListener('scroll', App.utils.throttle(() => {
            if (window.scrollY > 500) {
                backToTop.classList.add('visible');
            } else {
                backToTop.classList.remove('visible');
            }
        }, 100));
        
        // Scroll to top on click
        backToTop.addEventListener('click', () => {
            window.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
        });
    }
};

/**
 * =============================================================================
 * MODAL MANAGEMENT
 * =============================================================================
 */

App.components.modal = {
    stack: [],
    
    open(content, options = {}) {
        const modal = document.createElement('div');
        modal.className = 'modal-overlay';
        modal.innerHTML = `
            <div class="modal-container">
                <div class="modal-header">
                    <h3 class="modal-title">${options.title || ''}</h3>
                    <button class="modal-close" aria-label="Close modal">
                        <i data-feather="x"></i>
                    </button>
                </div>
                <div class="modal-body">
                    ${content}
                </div>
                ${options.footer ? `<div class="modal-footer">${options.footer}</div>` : ''}
            </div>
        `;
        
        // Add to modals container
        const container = document.getElementById('modals-container');
        if (container) {
            container.appendChild(modal);
        } else {
            document.body.appendChild(modal);
        }
        
        // Initialize feather icons
        if (window.feather) {
            feather.replace();
        }
        
        // Bind close events
        const closeBtn = modal.querySelector('.modal-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => this.close(modal));
        }
        
        // Close on backdrop click
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                this.close(modal);
            }
        });
        
        // Close on Escape key
        const escapeHandler = (e) => {
            if (e.key === 'Escape') {
                this.close(modal);
                document.removeEventListener('keydown', escapeHandler);
            }
        };
        document.addEventListener('keydown', escapeHandler);
        
        // Add to stack
        this.stack.push(modal);
        
        // Animate in
        requestAnimationFrame(() => {
            modal.style.opacity = '1';
            modal.querySelector('.modal-container').style.transform = 'scale(1)';
        });
        
        return modal;
    },
    
    close(modal) {
        if (!modal) {
            modal = this.stack.pop();
        }
        
        if (!modal) return;
        
        // Animate out
        modal.style.opacity = '0';
        modal.querySelector('.modal-container').style.transform = 'scale(0.95)';
        
        setTimeout(() => {
            if (modal.parentElement) {
                modal.remove();
            }
        }, 200);
        
        // Remove from stack
        const index = this.stack.indexOf(modal);
        if (index > -1) {
            this.stack.splice(index, 1);
        }
    },
    
    closeAll() {
        this.stack.forEach(modal => this.close(modal));
        this.stack = [];
    }
};

/**
 * =============================================================================
 * API METHODS
 * =============================================================================
 */

App.api = {
    /**
     * Base fetch wrapper with error handling
     */
    async request(url, options = {}) {
        try {
            const defaultOptions = {
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                }
            };
            
            const response = await fetch(url, { ...defaultOptions, ...options });
            
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.message || `HTTP ${response.status}: ${response.statusText}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('API Request failed:', error);
            throw error;
        }
    },
    
    /**
     * Upload files
     */
    async uploadFiles(files, targetFormat = null) {
        const formData = new FormData();
        
        files.forEach(file => {
            formData.append('files', file);
        });
        
        if (targetFormat) {
            formData.append('target_format', targetFormat);
        }
        
        return this.request(App.config.apiEndpoints.upload, {
            method: 'POST',
            body: formData,
            headers: {} // Let browser set Content-Type for FormData
        });
    },
    
    /**
     * Start conversion
     */
    async convertFiles(files, targetFormat, options = {}) {
        return this.request(App.config.apiEndpoints.convert, {
            method: 'POST',
            body: JSON.stringify({
                files,
                target_format: targetFormat,
                options
            })
        });
    },
    
    /**
     * Check conversion status
     */
    async getConversionStatus(jobId) {
        return this.request(`${App.config.apiEndpoints.status}/${jobId}`);
    },
    
    /**
     * Get supported formats
     */
    async getSupportedFormats() {
        return this.request(App.config.apiEndpoints.formats);
    },
    
    /**
     * Download file
     */
    downloadFile(jobId, filename = null) {
        const url = filename 
            ? `${App.config.apiEndpoints.download}/${jobId}/${filename}`
            : `${App.config.apiEndpoints.download}/${jobId}`;
        
        // Create temporary link and trigger download
        const link = document.createElement('a');
        link.href = url;
        link.download = filename || `converted_files_${jobId.slice(0, 8)}.zip`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }
};

/**
 * =============================================================================
 * INITIALIZATION
 * =============================================================================
 */

// DOM Content Loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize core components
    App.components.theme.init();
    App.components.navigation.init();
    App.components.backToTop.init();
    
    // Initialize feather icons
    if (window.feather) {
        feather.replace();
    }
    
    // Debug mode
    if (App.debug) {
        console.log('FileConverter Pro initialized', App);
        window.App = App; // Make available in console
    }
    
    // Custom initialization event
    document.dispatchEvent(new CustomEvent('fileconverter:ready', { detail: App }));
});

// Handle page visibility changes
document.addEventListener('visibilitychange', function() {
    if (document.hidden) {
        // Page is hidden - pause any ongoing operations if needed
        console.log('Page hidden');
    } else {
        // Page is visible - resume operations if needed
        console.log('Page visible');
    }
});

// Handle online/offline status
window.addEventListener('online', function() {
    App.utils.showToast('Connection restored', 'success');
});

window.addEventListener('offline', function() {
    App.utils.showToast('Connection lost. Please check your internet connection.', 'warning', 0);
});

// Global error handler
window.addEventListener('error', function(event) {
    console.error('Global error:', event.error);
    if (App.debug) {
        App.utils.showToast(`Error: ${event.error.message}`, 'error');
    }
});

// Unhandled promise rejection handler
window.addEventListener('unhandledrejection', function(event) {
    console.error('Unhandled promise rejection:', event.reason);
    if (App.debug) {
        App.utils.showToast(`Promise rejection: ${event.reason}`, 'error');
    }
});

// Export for module use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = App;
}

// Add CSS for smooth theme transitions
const themeTransitionStyle = document.createElement('style');
themeTransitionStyle.textContent = `
    .theme-transitioning * {
        transition: background-color 300ms ease, color 300ms ease, border-color 300ms ease !important;
    }
`;
document.head.appendChild(themeTransitionStyle);