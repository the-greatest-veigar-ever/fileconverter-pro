/**
 * FileConverter Pro - Upload Module
 * Handles file uploads, drag & drop, validation, and file management
 */

'use strict';

// Upload module
window.FileConverterPro = window.FileConverterPro || {};
window.FileConverterPro.Upload = (function() {
    
    // Private variables
    let uploadZone = null;
    let fileInput = null;
    let selectedFiles = [];
    let isDragging = false;
    let uploadInProgress = false;
    
    // Configuration
    const config = {
        maxFileSize: 100 * 1024 * 1024, // 100MB
        maxFiles: 50,
        allowedTypes: {
            image: ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff', 'webp', 'svg', 'ico', 'heic', 'heif', 'avif'],
            video: ['mp4', 'avi', 'mov', 'wmv', 'flv', 'webm', 'mkv', '3gp', 'm4v', 'f4v', 'asf', 'rm'],
            audio: ['mp3', 'wav', 'flac', 'aac', 'ogg', 'wma', 'm4a', 'opus', 'ape', 'ac3', 'aiff', 'au'],
            document: ['pdf', 'doc', 'docx', 'txt', 'rtf', 'odt', 'pages', 'epub', 'mobi', 'azw', 'azw3', 'fb2'],
            presentation: ['ppt', 'pptx', 'odp', 'key'],
            spreadsheet: ['xlsx', 'xls', 'csv', 'ods', 'tsv', 'dbf', 'xlsm', 'xlsb', 'numbers'],
            archive: ['zip', 'rar', '7z', 'tar', 'gz', 'bz2', 'xz', 'z', 'lzma'],
            font: ['ttf', 'otf', 'woff', 'woff2', 'eot']
        }
    };
    
    // File validation functions
    function validateFile(file) {
        const errors = [];
        
        // Check file size
        if (file.size > config.maxFileSize) {
            errors.push(`File too large. Maximum size is ${formatFileSize(config.maxFileSize)}`);
        }
        
        // Check file type
        const extension = getFileExtension(file.name);
        const fileType = getFileType(extension);
        
        if (!fileType) {
            errors.push(`Unsupported file type: .${extension}`);
        }
        
        // Check for empty files
        if (file.size === 0) {
            errors.push('File is empty');
        }
        
        return {
            valid: errors.length === 0,
            errors: errors,
            fileType: fileType,
            extension: extension
        };
    }
    
    function getFileExtension(filename) {
        return filename.toLowerCase().split('.').pop();
    }
    
    function getFileType(extension) {
        for (const [type, extensions] of Object.entries(config.allowedTypes)) {
            if (extensions.includes(extension)) {
                return type;
            }
        }
        return null;
    }

    function getConversionTargets(extension) {
        const type = getFileType(extension);
        if (!type) return [];
        return config.allowedTypes[type].filter(ext => ext !== extension);
    }
    
    function formatFileSize(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
    }
    
    // File management functions
    function addFiles(files) {
        const fileArray = Array.from(files);
        
        // Check total file count
        if (selectedFiles.length + fileArray.length > config.maxFiles) {
            showError(`Maximum ${config.maxFiles} files allowed`);
            return;
        }
        
        fileArray.forEach(file => {
            // Generate unique ID for file
            const fileId = generateFileId();
            
            // Validate file
            const validation = validateFile(file);
            
            // Create file object
        const fileObj = {
            id: fileId,
            file: file,
            name: file.name,
            size: file.size,
            type: file.type,
            extension: getFileExtension(file.name),
            fileType: validation.fileType,
            valid: validation.valid,
            errors: validation.errors,
            preview: null,
            uploaded: false,
            targetExtension: getFileExtension(file.name)
        };
            
            // Generate preview for images
            if (validation.fileType === 'image') {
                generateImagePreview(fileObj);
            }
            
            selectedFiles.push(fileObj);
        });
        
        updateFileList();
        updateUploadZone();
    }
    
    function removeFile(fileId) {
        selectedFiles = selectedFiles.filter(file => file.id !== fileId);
        updateFileList();
        updateUploadZone();
    }
    
    function clearAllFiles() {
        selectedFiles = [];
        updateFileList();
        updateUploadZone();
    }
    
    function generateFileId() {
        return Date.now().toString(36) + Math.random().toString(36).substr(2);
    }
    
    function generateImagePreview(fileObj) {
        const reader = new FileReader();
        reader.onload = function(e) {
            fileObj.preview = e.target.result;
            updateFileItem(fileObj.id);
        };
        reader.readAsDataURL(fileObj.file);
    }
    
    // UI update functions
    function updateUploadZone() {
        if (!uploadZone) return;
        
        const hasFiles = selectedFiles.length > 0;
        const fileListContainer = document.getElementById('file-list-container');
        const formatSelection = document.getElementById('format-selection');
        
        if (hasFiles) {
            uploadZone.classList.add('has-files');
            if (fileListContainer) fileListContainer.style.display = 'block';
            if (formatSelection) formatSelection.style.display = 'block';
            
            // Update upload zone text
            const uploadTitle = uploadZone.querySelector('.upload-title');
            const uploadSubtitle = uploadZone.querySelector('.upload-subtitle');
            
            if (uploadTitle) {
                uploadTitle.textContent = `${selectedFiles.length} file(s) selected`;
            }
            if (uploadSubtitle) {
                const totalSize = selectedFiles.reduce((sum, file) => sum + file.size, 0);
                uploadSubtitle.textContent = `Total size: ${formatFileSize(totalSize)}`;
            }
        } else {
            uploadZone.classList.remove('has-files');
            if (fileListContainer) fileListContainer.style.display = 'none';
            if (formatSelection) formatSelection.style.display = 'none';
            
            // Reset upload zone text
            const uploadTitle = uploadZone.querySelector('.upload-title');
            const uploadSubtitle = uploadZone.querySelector('.upload-subtitle');
            
            if (uploadTitle) {
                uploadTitle.textContent = 'Drop files here or click to browse';
            }
            if (uploadSubtitle) {
                uploadSubtitle.textContent = 'Support for 200+ formats • Max 100MB per file • Up to 50 files';
            }
        }
    }
    
    function updateFileList() {
        const fileList = document.getElementById('file-list');
        const fileCount = document.getElementById('file-count');
        const totalFiles = document.getElementById('total-files-count');
        const totalSize = document.getElementById('total-size');
        
        if (!fileList) return;
        
        // Update counters
        if (fileCount) fileCount.textContent = `${selectedFiles.length} files`;
        if (totalFiles) totalFiles.textContent = selectedFiles.length;
        
        const totalBytes = selectedFiles.reduce((sum, file) => sum + file.size, 0);
        if (totalSize) totalSize.textContent = formatFileSize(totalBytes);
        
        // Clear existing list
        fileList.innerHTML = '';
        
        // Add each file
        selectedFiles.forEach(fileObj => {
            const fileItem = createFileItem(fileObj);
            fileList.appendChild(fileItem);
        });
        
        // Initialize feather icons for new items
        if (window.feather) {
            feather.replace();
        }
    }
    
    function createFileItem(fileObj) {
        const template = document.getElementById('file-item-template');
        if (!template) {
            // Fallback if template doesn't exist
            const div = document.createElement('div');
            div.className = 'file-item';
            div.innerHTML = `
                <div class="file-info">
                    <span class="file-name">${fileObj.name}</span>
                    <span class="file-size">${formatFileSize(fileObj.size)}</span>
                </div>
                <button class="remove-file-btn" onclick="FileConverterPro.Upload.removeFile('${fileObj.id}')">
                    Remove
                </button>
            `;
            return div;
        }
        
        const clone = template.content.cloneNode(true);
        const fileItem = clone.querySelector('.file-item');
        
        // Set file ID
        fileItem.setAttribute('data-file-id', fileObj.id);
        
        // Update file details
        const fileName = clone.querySelector('.file-name');
        const fileSize = clone.querySelector('.file-size');
        const fileType = clone.querySelector('.file-type');
        const formatBadge = clone.querySelector('.format-text');
        
        if (fileName) fileName.textContent = fileObj.name;
        if (fileSize) fileSize.textContent = formatFileSize(fileObj.size);
        if (fileType) fileType.textContent = fileObj.fileType || 'unknown';
        if (formatBadge) formatBadge.textContent = fileObj.extension.toUpperCase();

        // Populate extension select
        const extSelect = clone.querySelector('.extension-select');
        if (extSelect) {
            const targets = getConversionTargets(fileObj.extension);
            // include current extension
            const options = [fileObj.extension, ...targets];
            extSelect.innerHTML = options
                .map(ext => `<option value="${ext}">${ext.toUpperCase()}</option>`) 
                .join('');
            extSelect.value = fileObj.extension;
            fileObj.targetExtension = fileObj.extension;
            extSelect.addEventListener('change', () => {
                fileObj.targetExtension = extSelect.value;
            });
        }
        
        // Set file type icon
        const fileIcon = clone.querySelector('.file-type-icon');
        if (fileIcon && fileObj.fileType) {
            fileIcon.setAttribute('data-feather', getFileTypeIcon(fileObj.fileType));
        }
        
        // Show preview if available
        if (fileObj.preview) {
            const thumbnail = clone.querySelector('.file-thumbnail');
            const thumbnailImage = clone.querySelector('.thumbnail-image');
            const iconContainer = clone.querySelector('.file-icon-container');
            
            if (thumbnail && thumbnailImage && iconContainer) {
                thumbnailImage.src = fileObj.preview;
                thumbnail.style.display = 'block';
                iconContainer.style.display = 'none';
            }
        }
        
        // Set validation status
        const statusIcon = clone.querySelector('.status-icon');
        const statusText = clone.querySelector('.status-text');
        
        if (!fileObj.valid) {
            if (statusIcon) {
                statusIcon.classList.remove('status-valid');
                statusIcon.classList.add('status-error');
                statusIcon.setAttribute('data-feather', 'x-circle');
            }
            if (statusText) statusText.textContent = 'Invalid';
            
            // Show validation errors
            const validation = clone.querySelector('.file-validation');
            const validationMessage = clone.querySelector('.validation-message');
            if (validation && validationMessage) {
                validation.style.display = 'block';
                validationMessage.textContent = fileObj.errors.join(', ');
            }
        }
        
        // Bind remove button
        const removeBtn = clone.querySelector('.remove-btn');
        if (removeBtn) {
            removeBtn.addEventListener('click', () => removeFile(fileObj.id));
        }
        
        return clone;
    }
    
    function updateFileItem(fileId) {
        const fileItem = document.querySelector(`[data-file-id="${fileId}"]`);
        const fileObj = selectedFiles.find(f => f.id === fileId);
        
        if (!fileItem || !fileObj) return;
        
        // Update preview if available
        if (fileObj.preview) {
            const thumbnail = fileItem.querySelector('.file-thumbnail');
            const thumbnailImage = fileItem.querySelector('.thumbnail-image');
            const iconContainer = fileItem.querySelector('.file-icon-container');

            if (thumbnail && thumbnailImage && iconContainer) {
                thumbnailImage.src = fileObj.preview;
                thumbnail.style.display = 'block';
                iconContainer.style.display = 'none';
            }
        }

        const extSelect = fileItem.querySelector('.extension-select');
        if (extSelect) {
            const targets = getConversionTargets(fileObj.extension);
            const options = [fileObj.extension, ...targets];
            extSelect.innerHTML = options
                .map(ext => `<option value="${ext}">${ext.toUpperCase()}</option>`)
                .join('');
            extSelect.value = fileObj.targetExtension || fileObj.extension;
        }
    }
    
    function getFileTypeIcon(fileType) {
        const icons = {
            image: 'image',
            video: 'video',
            audio: 'music',
            document: 'file-text',
            presentation: 'monitor',
            spreadsheet: 'grid',
            archive: 'archive',
            font: 'type'
        };
        return icons[fileType] || 'file';
    }
    
    // Event handlers
    function handleDragEnter(e) {
        e.preventDefault();
        e.stopPropagation();
        
        if (!isDragging) {
            isDragging = true;
            uploadZone.classList.add('drag-over');
        }
    }
    
    function handleDragOver(e) {
        e.preventDefault();
        e.stopPropagation();
    }
    
    function handleDragLeave(e) {
        e.preventDefault();
        e.stopPropagation();
        
        // Only remove drag-over class if we're leaving the upload zone entirely
        if (!uploadZone.contains(e.relatedTarget)) {
            isDragging = false;
            uploadZone.classList.remove('drag-over');
        }
    }
    
    function handleDrop(e) {
        e.preventDefault();
        e.stopPropagation();
        
        isDragging = false;
        uploadZone.classList.remove('drag-over');
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            addFiles(files);
        }
    }
    
    function handleFileSelect(e) {
        const files = e.target.files;
        if (files.length > 0) {
            addFiles(files);
        }
        
        // Reset file input
        e.target.value = '';
    }
    
    function handleBrowseClick() {
        if (fileInput) {
            fileInput.click();
        }
    }
    
    // Upload functionality
    async function uploadFiles() {
        if (uploadInProgress || selectedFiles.length === 0) return;
        
        const validFiles = selectedFiles.filter(file => file.valid);
        if (validFiles.length === 0) {
            showError('No valid files to upload');
            return;
        }
        
        uploadInProgress = true;
        showUploadProgress(true);
        
        try {
            const formData = new FormData();
            validFiles.forEach(fileObj => {
                formData.append('files', fileObj.file);
            });
            
            const response = await fetch('/api/upload', {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();

            if (response.ok) {
                showSuccess('Files uploaded successfully');

                // Store uploaded files info for conversion including target extension
                window.FileConverterPro.uploadedFiles = result.files.map((info, idx) => {
                    const localFile = validFiles[idx];
                    return Object.assign({}, info, {
                        target_extension: localFile.targetExtension
                    });
                });
                
                // Trigger next step in conversion process
                if (window.FileConverterPro.Conversion && window.FileConverterPro.Conversion.handleUploadComplete) {
                    window.FileConverterPro.Conversion.handleUploadComplete(result);
                }
                
            } else {
                showError(result.message || 'Upload failed');
            }
            
        } catch (error) {
            console.error('Upload error:', error);
            showError('Upload failed. Please try again.');
        } finally {
            uploadInProgress = false;
            showUploadProgress(false);
        }
    }
    
    function showUploadProgress(show) {
        const progressSection = document.getElementById('upload-progress');
        if (progressSection) {
            progressSection.style.display = show ? 'block' : 'none';
        }
    }
    
    // Utility functions
    function showError(message) {
        if (window.FileConverterPro.utils && window.FileConverterPro.utils.showToast) {
            window.FileConverterPro.utils.showToast(message, 'error');
        } else {
            alert('Error: ' + message);
        }
    }
    
    function showSuccess(message) {
        if (window.FileConverterPro.utils && window.FileConverterPro.utils.showToast) {
            window.FileConverterPro.utils.showToast(message, 'success');
        } else {
            console.log('Success: ' + message);
        }
    }
    
    // Initialization
    function init() {
        uploadZone = document.getElementById('upload-area');
        fileInput = document.getElementById('file-input');
        
        if (!uploadZone || !fileInput) {
            console.warn('Upload elements not found');
            return;
        }
        
        // Bind drag and drop events
        uploadZone.addEventListener('dragenter', handleDragEnter);
        uploadZone.addEventListener('dragover', handleDragOver);
        uploadZone.addEventListener('dragleave', handleDragLeave);
        uploadZone.addEventListener('drop', handleDrop);
        uploadZone.addEventListener('click', handleBrowseClick);
        
        // Bind file input change
        fileInput.addEventListener('change', handleFileSelect);
        
        // Bind clear all button
        const clearAllBtn = document.getElementById('clear-all-btn');
        if (clearAllBtn) {
            clearAllBtn.addEventListener('click', clearAllFiles);
        }
        
        // Bind add more button
        const addMoreBtn = document.getElementById('add-more-btn');
        if (addMoreBtn) {
            addMoreBtn.addEventListener('click', handleBrowseClick);
        }
        
        // Bind quick upload buttons
        const quickUploadBtns = document.querySelectorAll('.quick-upload-btn');
        quickUploadBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                const accept = btn.getAttribute('data-accept');
                if (accept && fileInput) {
                    fileInput.setAttribute('accept', accept);
                    fileInput.click();
                }
            });
        });
        
        console.log('Upload module initialized');
    }
    
    // Public API
    return {
        init: init,
        addFiles: addFiles,
        removeFile: removeFile,
        clearAllFiles: clearAllFiles,
        uploadFiles: uploadFiles,
        getSelectedFiles: () => selectedFiles,
        getValidFiles: () => selectedFiles.filter(file => file.valid),
        isUploadInProgress: () => uploadInProgress
    };
    
})();

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    if (window.FileConverterPro && window.FileConverterPro.Upload) {
        window.FileConverterPro.Upload.init();
    }
});

// Global initialization function for manual initialization
window.initializeUpload = function() {
    if (window.FileConverterPro && window.FileConverterPro.Upload) {
        window.FileConverterPro.Upload.init();
    }
};