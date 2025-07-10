// Override broken Dash navigation with simple JavaScript
document.addEventListener('DOMContentLoaded', function() {
    console.log('🔧 Navbar override loading...');
    
    // Wait for navbar to load
    setTimeout(function() {
        const navLinks = document.querySelectorAll('[id*="nav-"][id*="-link"]');
        
        navLinks.forEach(function(link) {
            // Remove any existing click handlers
            link.onclick = null;
            
            // Add simple navigation
            link.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                
                const href = this.getAttribute('href');
                if (href) {
                    console.log('🚀 Navigating to:', href);
                    window.location.href = href;
                }
            });
        });
        
        console.log('✅ Navbar override installed for', navLinks.length, 'links');
    }, 1000);
});
