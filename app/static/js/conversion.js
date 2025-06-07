/**
 * FileConverter Pro - Conversion Module
 * Handles format selection, conversion options, progress tracking, and conversion workflow
 */

'use strict';

// Conversion module
window.FileConverterPro = window.FileConverterPro || {};
window.FileConverterPro.Conversion = (function() {
    
    // Private variables
    let selectedFormat = null;
    let conversionOptions = {};
    let currentJob = null;
    let pollingInterval = null;
    let convertButton = null;
    
    // Format categories and their supported conversions
    const formatCategories = {
        image: {
            icon: 'image',
            formats: ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff', 'webp', 'svg', 'ico', 'heic', 'heif', 'avif'],
            commonTargets: ['jpg', 'png', 'webp', 'pdf'],
            qualitySupported: true,
            resolutionSupported: true
        },
        video: {
            icon: 'video',
            formats: ['mp4', 'avi', 'mov', 'wmv', 'flv', 'webm', 'mkv', '3gp', 'm4v'],
            commonTargets: ['mp4', 'webm', 'avi'],
            qualitySupported: true,
            resolutionSupported: true,
            fpsSupported: true
        },
        audio: {
            icon: 'music',
            formats: ['mp3', 'wav', 'flac', 'aac', 'ogg', 'wma', 'm4a', 'opus'],
            commonTargets: ['mp3', 'wav', 'flac'],
            qualitySupported: true,
            bitrateSupported: true
        },
        document: {
            icon: 'file-text',
            formats: ['pdf', 'doc', 'docx', 'txt', 'rtf', 'odt', 'epub'],
            commonTargets: ['pdf', 'docx', 'txt'],
            qualitySupported: false
        },
        presentation: {
            icon: 'monitor',
            formats: ['ppt', 'pptx', 'odp', 'key'],
            commonTargets: ['pdf', 'pptx'],
            qualitySupported: false
        },
        spreadsheet: {
            icon: 'grid',
            formats: ['xlsx', 'xls', 'csv', 'ods'],
            commonTargets: ['xlsx', 'csv', 'pdf'],
            qualitySupported: false
        },
        archive: {
            icon: 'archive',
            formats: ['zip', 'rar', '7z', 'tar', 'gz'],
            commonTargets: ['zip', '7z'],
            qualitySupported: false
        },
        font: {
            icon: 'type',
            formats: ['ttf', 'otf', 'woff', 'woff2', 'eot'],
            commonTargets: ['woff2', 'ttf'],
            qualitySupported: false
        }
    };
    
    // Quality presets
    const qualityPresets = {
        high: { quality: 95, description: 'Best quality, larger file size' },
        medium: { quality: 85, description: 'Good quality, balanced file size' },
        low: { quality: 70, description: 'Smaller file size, reduced quality' }
    };
    
    // Format selection functions
    function showFormatSelection() {
        const formatSelection = document.getElementById('format-selection');
        if (formatSelection) {
            formatSelection.style.display = 'block';
            generateFormatOptions();
        }
    }
    
    function generateFormatOptions() {
        const uploadedFiles = getUploadedFiles();
        if (!uploadedFiles || uploadedFiles.length === 0) return;
        
        // Determine which categories are relevant
        const fileTypes = new Set(uploadedFiles.map(file => file.file_type || file.fileType));
        const relevantCategories = Array.from(fileTypes).filter(type => formatCategories[type]);
        
        // Create format categories
        const formatCategoriesContainer = document.getElementById('format-categories');
        if (!formatCategoriesContainer) return;
        
        formatCategoriesContainer.innerHTML = '';
        
        relevantCategories.forEach(categoryName => {
            const category = formatCategories[categoryName];
            const categoryElement = createFormatCategory(categoryName, category);
            formatCategoriesContainer.appendChild(categoryElement);
        });
        
        // Initialize feather icons
        if (window.feather) {
            feather.replace();
        }
    }
    
    function createFormatCategory(categoryName, category) {
        const categoryDiv = document.createElement('div');
        categoryDiv.className = 'format-category';
        categoryDiv.innerHTML = `
            <div class="format-category-btn" onclick="FileConverterPro.Conversion.toggleCategory('${categoryName}')">
                <div class="format-category-icon">
                    <i data-feather="${category.icon}"></i>
                </div>
                <div class="format-category-info">
                    <span class="format-category-name">${categoryName.charAt(0).toUpperCase() + categoryName.slice(1)}</span>
                    <span class="format-category-count">${category.formats.length} formats</span>
                </div>
                <i data-feather="chevron-down" class="category-toggle-icon"></i>
            </div>
            <div class="format-options" id="formats-${categoryName}">
                ${createFormatOptions(category)}
            </div>
        `;
        
        return categoryDiv;
    }
    
    function createFormatOptions(category) {
        let html = '<div class="format-grid">';
        
        // Show common targets first
        category.commonTargets.forEach(format => {
            html += `
                <button class="format-option common" onclick="FileConverterPro.Conversion.selectFormat('${format}')" data-format="${format}">
                    <span class="format-name">.${format.toUpperCase()}</span>
                    <span class="format-badge">Popular</span>
                </button>
            `;
        });
        
        // Show all other formats
        category.formats.filter(format => !category.commonTargets.includes(format)).forEach(format => {
            html += `
                <button class="format-option" onclick="FileConverterPro.Conversion.selectFormat('${format}')" data-format="${format}">
                    <span class="format-name">.${format.toUpperCase()}</span>
                </button>
            `;
        });
        
        html += '</div>';
        return html;
    }
    
    function toggleCategory(categoryName) {
        const category = document.querySelector(`.format-category:has(#formats-${categoryName})`);
        const formatOptions = document.getElementById(`formats-${categoryName}`);
        
        if (!category || !formatOptions) return;
        
        const isActive = category.classList.contains('active');
        
        // Close all categories
        document.querySelectorAll('.format-category').forEach(cat => {
            cat.classList.remove('active');
        });
        
        // Open this category if it wasn't active
        if (!isActive) {
            category.classList.add('active');
        }
    }
    
    function selectFormat(format) {
        selectedFormat = format;
        
        // Update UI
        document.querySelectorAll('.format-option').forEach(option => {
            option.classList.remove('selected');
        });
        
        const selectedOption = document.querySelector(`[data-format="${format}"]`);
        if (selectedOption) {
            selectedOption.classList.add('selected');
        }
        
        // Show conversion options
        showConversionOptions(format);
        
        // Enable convert button
        updateConvertButton();
        
        // Show quick formats for easy switching
        showQuickFormats(format);
    }
    
    // Conversion options functions
    function showConversionOptions(format) {
        const optionsContainer = document.getElementById('conversion-options');
        if (!optionsContainer) return;
        
        // Determine which category this format belongs to
        let category = null;
        for (const [catName, catData] of Object.entries(formatCategories)) {
            if (catData.formats.includes(format)) {
                category = catData;
                break;
            }
        }
        
        if (!category) return;
        
        optionsContainer.style.display = 'block';
        generateConversionOptions(format, category);
    }
    
    function generateConversionOptions(format, category) {
        const optionsGrid = document.getElementById('options-grid');
        if (!optionsGrid) return;
        
        optionsGrid.innerHTML = '';
        
        // Quality options
        if (category.qualitySupported) {
            optionsGrid.appendChild(createQualityOption());
        }
        
        // Resolution options for images and videos
        if (category.resolutionSupported) {
            optionsGrid.appendChild(createResolutionOption());
        }
        
        // FPS options for videos
        if (category.fpsSupported) {
            optionsGrid.appendChild(createFpsOption());
        }
        
        // Bitrate options for audio
        if (category.bitrateSupported) {
            optionsGrid.appendChild(createBitrateOption());
        }
        
        // Format-specific options
        createFormatSpecificOptions(format, optionsGrid);
    }
    
    function createQualityOption() {
        const div = document.createElement('div');
        div.className = 'option-group';
        div.innerHTML = `
            <label class="option-label">Quality:</label>
            <div class="option-control">
                <select class="option-select" id="quality-select" onchange="FileConverterPro.Conversion.updateOption('quality', this.value)">
                    <option value="high">High (95%)</option>
                    <option value="medium" selected>Medium (85%)</option>
                    <option value="low">Low (70%)</option>
                    <option value="custom">Custom</option>
                </select>
            </div>
            <div class="custom-quality" id="custom-quality" style="display: none;">
                <input type="range" min="1" max="100" value="85" class="slider" id="quality-slider" 
                       oninput="FileConverterPro.Conversion.updateCustomQuality(this.value)">
                <span class="option-value" id="quality-value">85%</span>
            </div>
        `;
        return div;
    }
    
    function createResolutionOption() {
        const div = document.createElement('div');
        div.className = 'option-group';
        div.innerHTML = `
            <label class="option-label">Resolution:</label>
            <div class="option-control">
                <select class="option-select" id="resolution-select" onchange="FileConverterPro.Conversion.updateResolution(this.value)">
                    <option value="original" selected>Keep Original</option>
                    <option value="4k">4K (3840×2160)</option>
                    <option value="1080p">1080p (1920×1080)</option>
                    <option value="720p">720p (1280×720)</option>
                    <option value="480p">480p (854×480)</option>
                    <option value="custom">Custom</option>
                </select>
            </div>
            <div class="custom-resolution" id="custom-resolution" style="display: none;">
                <input type="number" placeholder="Width" class="option-input" id="width-input" 
                       onchange="FileConverterPro.Conversion.updateCustomResolution()">
                <span>×</span>
                <input type="number" placeholder="Height" class="option-input" id="height-input" 
                       onchange="FileConverterPro.Conversion.updateCustomResolution()">
            </div>
        `;
        return div;
    }
    
    function createFpsOption() {
        const div = document.createElement('div');
        div.className = 'option-group';
        div.innerHTML = `
            <label class="option-label">Frame Rate:</label>
            <div class="option-control">
                <select class="option-select" id="fps-select" onchange="FileConverterPro.Conversion.updateOption('fps', this.value)">
                    <option value="original" selected>Keep Original</option>
                    <option value="60">60 FPS</option>
                    <option value="30">30 FPS</option>
                    <option value="24">24 FPS</option>
                    <option value="15">15 FPS</option>
                </select>
            </div>
        `;
        return div;
    }
    
    function createBitrateOption() {
        const div = document.createElement('div');
        div.className = 'option-group';
        div.innerHTML = `
            <label class="option-label">Audio Bitrate:</label>
            <div class="option-control">
                <select class="option-select" id="bitrate-select" onchange="FileConverterPro.Conversion.updateOption('bitrate', this.value)">
                    <option value="320k">320 kbps (High)</option>
                    <option value="192k" selected>192 kbps (Medium)</option>
                    <option value="128k">128 kbps (Standard)</option>
                    <option value="96k">96 kbps (Low)</option>
                </select>
            </div>
        `;
        return div;
    }
    
    function createFormatSpecificOptions(format, container) {
        // Add format-specific options based on the target format
        switch (format) {
            case 'pdf':
                container.appendChild(createPdfOptions());
                break;
            case 'webp':
                container.appendChild(createWebpOptions());
                break;
            // Add more format-specific options as needed
        }
    }
    
    function createPdfOptions() {
        const div = document.createElement('div');
        div.className = 'option-group';
        div.innerHTML = `
            <label class="option-label">PDF Options:</label>
            <div class="option-control">
                <label class="checkbox-option">
                    <input type="checkbox" id="pdf-optimize" onchange="FileConverterPro.Conversion.updateOption('optimize', this.checked)">
                    <span>Optimize for web</span>
                </label>
            </div>
        `;
        return div;
    }
    
    function createWebpOptions() {
        const div = document.createElement('div');
        div.className = 'option-group';
        div.innerHTML = `
            <label class="option-label">WebP Method:</label>
            <div class="option-control">
                <select class="option-select" id="webp-method" onchange="FileConverterPro.Conversion.updateOption('method', this.value)">
                    <option value="6" selected>6 (Best compression)</option>
                    <option value="4">4 (Balanced)</option>
                    <option value="2">2 (Faster)</option>
                    <option value="0">0 (Fastest)</option>
                </select>
            </div>
        `;
        return div;
    }
    
    // Option update functions
    function updateOption(key, value) {
        conversionOptions[key] = value;
        console.log('Updated option:', key, '=', value);
    }
    
    function updateCustomQuality(value) {
        const qualityValue = document.getElementById('quality-value');
        if (qualityValue) {
            qualityValue.textContent = value + '%';
        }
        updateOption('custom_quality', parseInt(value));
    }
    
    function updateResolution(value) {
        const customResolution = document.getElementById('custom-resolution');
        if (customResolution) {
            customResolution.style.display = value === 'custom' ? 'block' : 'none';
        }
        
        if (value !== 'custom' && value !== 'original') {
            const resolutions = {
                '4k': [3840, 2160],
                '1080p': [1920, 1080],
                '720p': [1280, 720],
                '480p': [854, 480]
            };
            
            if (resolutions[value]) {
                updateOption('resolution', resolutions[value]);
            }
        } else if (value === 'original') {
            delete conversionOptions.resolution;
        }
    }
    
    function updateCustomResolution() {
        const widthInput = document.getElementById('width-input');
        const heightInput = document.getElementById('height-input');
        
        if (widthInput && heightInput && widthInput.value && heightInput.value) {
            updateOption('resolution', [parseInt(widthInput.value), parseInt(heightInput.value)]);
        }
    }
    
    // Quick formats
    function showQuickFormats(selectedFormat) {
        const quickFormats = document.getElementById('quick-formats');
        if (!quickFormats) return;
        
        // Determine category of selected format
        let category = null;
        for (const [catName, catData] of Object.entries(formatCategories)) {
            if (catData.formats.includes(selectedFormat)) {
                category = catData;
                break;
            }
        }
        
        if (!category) return;
        
        quickFormats.style.display = 'block';
        const quickGrid = quickFormats.querySelector('.quick-formats-grid');
        if (quickGrid) {
            quickGrid.innerHTML = '';
            
            category.commonTargets.forEach(format => {
                const btn = document.createElement('button');
                btn.className = 'quick-format';
                btn.setAttribute('data-format', format);
                btn.onclick = () => selectFormat(format);
                btn.innerHTML = `.${format.toUpperCase()}`;
                
                if (format === selectedFormat) {
                    btn.classList.add('selected');
                }
                
                quickGrid.appendChild(btn);
            });
        }
    }
    
    // Conversion functions
    function updateConvertButton() {
        if (!convertButton) {
            convertButton = document.getElementById('convert-button');
        }
        
        if (convertButton) {
            const hasFiles = getUploadedFiles().length > 0;
            const hasFormat = selectedFormat !== null;
            
            convertButton.disabled = !(hasFiles && hasFormat);
            
            if (hasFiles && hasFormat) {
                convertButton.textContent = `Convert to ${selectedFormat.toUpperCase()}`;
            } else if (!hasFiles) {
                convertButton.textContent = 'Select files first';
            } else {
                convertButton.textContent = 'Choose format';
            }
        }
    }
    
    async function startConversion() {
        const uploadedFiles = getUploadedFiles();
        if (!uploadedFiles || uploadedFiles.length === 0) {
            showError('No files to convert');
            return;
        }
        
        if (!selectedFormat) {
            showError('Please select a target format');
            return;
        }
        
        try {
            // Prepare conversion request
            const conversionData = {
                files: uploadedFiles.map(file => ({
                    id: file.id,
                    original_filename: file.original_filename,
                    filename: file.filename,
                    path: file.path,
                    size: file.size,
                    extension: file.extension
                })),
                target_format: selectedFormat,
                options: conversionOptions
            };
            
            // Start conversion
            const response = await fetch('/api/convert', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(conversionData)
            });
            
            const result = await response.json();
            
            if (response.ok) {
                currentJob = result.job_id;
                
                // Redirect to conversion status page
                window.location.href = `/convert?job_id=${result.job_id}`;
                
            } else {
                showError(result.message || 'Conversion failed to start');
            }
            
        } catch (error) {
            console.error('Conversion error:', error);
            showError('Failed to start conversion. Please try again.');
        }
    }
    
    // Status tracking
    function startStatusTracking(jobId) {
        if (pollingInterval) {
            clearInterval(pollingInterval);
        }
        
        pollingInterval = setInterval(async () => {
            try {
                const response = await fetch(`/api/status/${jobId}`);
                const status = await response.json();
                
                if (response.ok) {
                    updateConversionStatus(status);
                    
                    // Stop polling if conversion is complete
                    if (['completed', 'failed', 'cancelled'].includes(status.status)) {
                        clearInterval(pollingInterval);
                        pollingInterval = null;
                    }
                }
            } catch (error) {
                console.error('Status check error:', error);
            }
        }, 2000);
    }
    
    function updateConversionStatus(status) {
        // This would be used on the conversion status page
        console.log('Conversion status:', status);
    }
    
    // Utility functions
    function getUploadedFiles() {
        if (window.FileConverterPro.uploadedFiles) {
            return window.FileConverterPro.uploadedFiles;
        }
        
        if (window.FileConverterPro.Upload) {
            return window.FileConverterPro.Upload.getValidFiles();
        }
        
        return [];
    }
    
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
    
    // Event handlers
    function handleUploadComplete(uploadResult) {
        // Show format selection when upload is complete
        showFormatSelection();
        updateConvertButton();
    }
    
    // Initialization
    function init() {
        convertButton = document.getElementById('convert-button');
        
        if (convertButton) {
            convertButton.addEventListener('click', startConversion);
        }
        
        // Initialize quality select change handler
        const qualitySelect = document.getElementById('quality-select');
        if (qualitySelect) {
            qualitySelect.addEventListener('change', function() {
                const customQuality = document.getElementById('custom-quality');
                if (customQuality) {
                    customQuality.style.display = this.value === 'custom' ? 'block' : 'none';
                }
                
                if (this.value !== 'custom') {
                    const presets = { high: 95, medium: 85, low: 70 };
                    updateOption('quality', presets[this.value]);
                }
            });
        }
        
        console.log('Conversion module initialized');
    }
    
    // Public API
    return {
        init: init,
        selectFormat: selectFormat,
        toggleCategory: toggleCategory,
        updateOption: updateOption,
        updateCustomQuality: updateCustomQuality,
        updateResolution: updateResolution,
        updateCustomResolution: updateCustomResolution,
        startConversion: startConversion,
        startStatusTracking: startStatusTracking,
        handleUploadComplete: handleUploadComplete,
        getSelectedFormat: () => selectedFormat,
        getConversionOptions: () => conversionOptions
    };
    
})();

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    if (window.FileConverterPro && window.FileConverterPro.Conversion) {
        window.FileConverterPro.Conversion.init();
    }
});

// Global initialization function for manual initialization
window.initializeConversion = function() {
    if (window.FileConverterPro && window.FileConverterPro.Conversion) {
        window.FileConverterPro.Conversion.init();
    }
};