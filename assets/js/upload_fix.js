// Fixed upload enhancement with correct IDs
console.log('🔧 Upload fix loading...');

document.addEventListener('DOMContentLoaded', function() {
    // Look for the actual upload component ID
    const uploadElement = document.getElementById('drag-drop-upload');
    
    if (uploadElement) {
        console.log('✅ Found drag-drop-upload component');
        
        // Make sure it's visible and functional
        uploadElement.style.display = 'block';
        uploadElement.style.visibility = 'visible';
        uploadElement.style.opacity = '1';
        
        console.log('🎉 Upload component activated');
    } else {
        console.log('❌ drag-drop-upload component not found');
        
        // List all upload-related elements for debugging
        const allUploads = document.querySelectorAll('[id*="upload"], [class*="upload"]');
        console.log('Found upload elements:', allUploads.length);
        allUploads.forEach(el => console.log('  -', el.id || el.className));
    }
});
