/**
 * Working Upload Enhancement JavaScript
 */
window.uploadProgressLog = [];

document.addEventListener('DOMContentLoaded', function() {
    console.log('🎯 Upload enhancement JavaScript loaded');
    
    // Wait for Dash to render, then enhance upload areas
    setTimeout(function() {
        enhanceUploadAreas();
    }, 1000);
});

function enhanceUploadAreas() {
    // Find the upload component by ID
    const uploadElement = document.getElementById('drag-drop-upload');
    if (!uploadElement) {
        console.warn('Upload element not found');
        return;
    }
    
    console.log('✅ Found upload element, adding enhancements');
    
    // Find the actual upload area (the styled div)
    const uploadArea = uploadElement.querySelector('div[style*="border-style: dashed"]');
    if (!uploadArea) {
        console.warn('Upload area not found');
        return;
    }
    
    setupDragAndDrop(uploadArea);
    setupKeyboardAccessibility(uploadArea);
    setupFileValidation(uploadElement);
}

function setupDragAndDrop(uploadArea) {
    let dragCounter = 0;
    
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        uploadArea.addEventListener(eventName, preventDefaults, false);
        document.body.addEventListener(eventName, preventDefaults, false);
    });
    
    ['dragenter', 'dragover'].forEach(eventName => {
        uploadArea.addEventListener(eventName, function(e) {
            dragCounter++;
            uploadArea.style.backgroundColor = '#e3f2fd';
            uploadArea.style.borderColor = '#2196f3';
            uploadArea.style.transform = 'scale(1.02)';
            console.log('Drag highlight active');
        }, false);
    });
    
    ['dragleave', 'drop'].forEach(eventName => {
        uploadArea.addEventListener(eventName, function(e) {
            dragCounter--;
            if (dragCounter === 0) {
                uploadArea.style.backgroundColor = '#f8f9fa';
                uploadArea.style.borderColor = '#007bff';
                uploadArea.style.transform = 'scale(1)';
                console.log('Drag highlight removed');
            }
        }, false);
    });
    
    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }
}

function setupKeyboardAccessibility(uploadArea) {
    uploadArea.setAttribute('tabindex', '0');
    uploadArea.setAttribute('role', 'button');
    uploadArea.setAttribute('aria-label', 'Click or press Enter to upload files');
    
    uploadArea.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            const fileInput = uploadArea.closest('[id="drag-drop-upload"]').querySelector('input[type="file"]');
            if (fileInput) {
                fileInput.click();
                console.log('File input triggered via keyboard');
            }
        }
    });
}

function setupFileValidation(uploadElement) {
    const fileInput = uploadElement.querySelector('input[type="file"]');
    if (!fileInput) return;
    
    fileInput.addEventListener('change', function(e) {
        const files = e.target.files;
        console.log(`Files selected: ${files.length}`);
        validateFiles(files);
    });
}

function validateFiles(files) {
    const maxSize = 50 * 1024 * 1024; // 50MB
    const allowedExtensions = ['.csv', '.xls', '.xlsx', '.json'];
    
    Array.from(files).forEach(file => {
        if (file.size > maxSize) {
            console.error(`File "${file.name}" is too large`);
            return;
        }
        
        const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
        if (!allowedExtensions.includes(fileExtension)) {
            console.error(`File "${file.name}" has unsupported format`);
            return;
        }
        
        console.log(`✅ File "${file.name}" passed validation`);
        window.uploadProgressLog.push(`Validated: ${file.name}`);
    });
}

console.log('🚀 Upload enhancement JavaScript ready');
