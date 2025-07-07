/**
 * Client-side JavaScript for enhanced file upload functionality
 * Save as: assets/js/upload_enhancement.js
 */

// Upload progress tracking and visual feedback
window.uploadProgressLog = [];

/**
 * Enhanced drag and drop functionality with visual feedback
 */
document.addEventListener('DOMContentLoaded', function() {
    // Find all upload components
    const uploadComponents = document.querySelectorAll('[data-dash-is-loading="true"]');
    
    uploadComponents.forEach(component => {
        const uploadArea = component.querySelector('div[style*="border-style: dashed"]');
        if (!uploadArea) return;
        
        // Add enhanced drag and drop events
        setupDragAndDrop(uploadArea);
        
        // Add keyboard accessibility
        setupKeyboardAccessibility(uploadArea);
        
        // Add file validation
        setupFileValidation(uploadArea);
    });
});

/**
 * Setup drag and drop with visual feedback
 */
function setupDragAndDrop(uploadArea) {
    let dragCounter = 0;
    
    // Prevent default drag behaviors
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        uploadArea.addEventListener(eventName, preventDefaults, false);
        document.body.addEventListener(eventName, preventDefaults, false);
    });
    
    // Highlight drop area when item is dragged over it
    ['dragenter', 'dragover'].forEach(eventName => {
        uploadArea.addEventListener(eventName, highlight, false);
    });
    
    ['dragleave', 'drop'].forEach(eventName => {
        uploadArea.addEventListener(eventName, unhighlight, false);
    });
    
    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }
    
    function highlight(e) {
        dragCounter++;
        uploadArea.style.backgroundColor = '#e3f2fd';
        uploadArea.style.borderColor = '#2196f3';
        uploadArea.style.transform = 'scale(1.02)';
        uploadArea.style.boxShadow = '0 4px 20px rgba(33, 150, 243, 0.3)';
    }
    
    function unhighlight(e) {
        dragCounter--;
        if (dragCounter === 0) {
            uploadArea.style.backgroundColor = '#f8f9fa';
            uploadArea.style.borderColor = '#007bff';
            uploadArea.style.transform = 'scale(1)';
            uploadArea.style.boxShadow = 'none';
        }
    }
}

/**
 * Setup keyboard accessibility
 */
function setupKeyboardAccessibility(uploadArea) {
    uploadArea.setAttribute('tabindex', '0');
    uploadArea.setAttribute('role', 'button');
    uploadArea.setAttribute('aria-label', 'Click or press Enter to upload files');
    
    uploadArea.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            const fileInput = uploadArea.querySelector('input[type="file"]');
            if (fileInput) {
                fileInput.click();
            }
        }
    });
    
    // Focus styles
    uploadArea.addEventListener('focus', function() {
        uploadArea.style.outline = '2px solid #007bff';
        uploadArea.style.outlineOffset = '2px';
    });
    
    uploadArea.addEventListener('blur', function() {
        uploadArea.style.outline = 'none';
    });
}

/**
 * Setup client-side file validation
 */
function setupFileValidation(uploadArea) {
    const fileInput = uploadArea.querySelector('input[type="file"]');
    if (!fileInput) return;
    
    fileInput.addEventListener('change', function(e) {
        const files = e.target.files;
        validateFiles(files);
    });
}

/**
 * Validate files before upload
 */
function validateFiles(files) {
    const maxSize = 50 * 1024 * 1024; // 50MB
    const allowedTypes = [
        'text/csv',
        'application/vnd.ms-excel',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'application/json'
    ];
    
    const allowedExtensions = ['.csv', '.xls', '.xlsx', '.json'];
    
    Array.from(files).forEach(file => {
        // Size validation
        if (file.size > maxSize) {
            showValidationError(`File "${file.name}" is too large. Maximum size is 50MB.`);
            return;
        }
        
        // Type validation
        const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
        if (!allowedExtensions.includes(fileExtension)) {
            showValidationError(`File "${file.name}" has an unsupported format. Supported: CSV, Excel, JSON.`);
            return;
        }
        
        // Unicode filename validation
        try {
            encodeURIComponent(file.name);
        } catch (e) {
            showValidationError(`File "${file.name}" has an invalid filename. Please rename and try again.`);
            return;
        }
        
        console.log(`✅ File "${file.name}" passed validation`);
        window.uploadProgressLog.push(`Validated: ${file.name}`);
    });
}

/**
 * Show validation error to user
 */
function showValidationError(message) {
    console.error(message);
    
    // Create toast notification
    const toastContainer = document.getElementById('toast-container');
    if (toastContainer) {
        const toast = document.createElement('div');
        toast.className = 'alert alert-danger alert-dismissible fade show';
        toast.innerHTML = `
            <strong>Upload Error:</strong> ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        toastContainer.appendChild(toast);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 5000);
    }
}

console.log('🎯 Upload enhancement JavaScript loaded successfully');
