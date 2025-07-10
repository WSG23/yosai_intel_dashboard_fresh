// Fixed upload enhancement - more robust error checking
console.log('🚀 Upload enhancement JavaScript ready');

// Wait for DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('🎯 Upload enhancement JavaScript loaded');
    
    // Robust element checking
    function findUploadElement() {
        const selectors = [
            '#upload-area',
            '#drag-drop-upload', 
            '[id*="upload"]',
            '.upload-container'
        ];
        
        for (let selector of selectors) {
            const element = document.querySelector(selector);
            if (element) {
                console.log('✅ Found upload element:', selector);
                return element;
            }
        }
        
        console.log('⚠️ No upload element found, will retry...');
        return null;
    }
    
    // Try to find upload element, retry if not found
    let attempts = 0;
    const maxAttempts = 10;
    
    function initializeUpload() {
        const uploadElement = findUploadElement();
        
        if (uploadElement) {
            console.log('🎉 Upload enhancement initialized successfully');
            // Add your upload enhancements here
        } else {
            attempts++;
            if (attempts < maxAttempts) {
                setTimeout(initializeUpload, 500); // Retry in 500ms
            } else {
                console.log('❌ Could not find upload element after', maxAttempts, 'attempts');
            }
        }
    }
    
    // Start initialization
    initializeUpload();
});

// Export for debugging
window.uploadEnhancement = { findUploadElement };
