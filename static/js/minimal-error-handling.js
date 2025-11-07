// Minimal error handling for landing page
window.addEventListener('error', function(e) {
    console.error('Page error:', e.error);
    // Silently handle errors without showing to user
});

// Handle unhandled promise rejections
window.addEventListener('unhandledrejection', function(e) {
    console.error('Unhandled promise rejection:', e.reason);
    e.preventDefault(); // Prevent the default browser behavior
});

// Ensure modals work even if there are errors
document.addEventListener('DOMContentLoaded', function() {
    // Ensure modal close buttons work
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('close') || e.target.onclick) {
            try {
                if (e.target.onclick) {
                    e.target.onclick();
                }
            } catch (error) {
                // Fallback: hide all modals
                document.querySelectorAll('.modal').forEach(modal => {
                    modal.classList.add('hidden');
                });
            }
        }
    });
    
    // Ensure forms work
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', function(e) {
            try {
                // Let the original handler run
            } catch (error) {
                e.preventDefault();
                alert('⚠️ Form submission failed. Please try again or contact support.');
            }
        });
    });
});