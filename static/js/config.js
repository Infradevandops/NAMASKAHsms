// Configuration for Enhanced Frontend
window.CONFIG = {
    // API Configuration
    API_BASE_URL: '',
    WEBSOCKET_URL: `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws`,
    
    // Security Configuration
    CSRF_ENABLED: true,
    RATE_LIMIT_ENABLED: true,
    
    // Feature Flags
    FEATURES: {
        WEBSOCKET_ENABLED: true,
        REAL_TIME_UPDATES: true,
        BULK_VERIFICATION: true,
        ENHANCED_SECURITY: true,
        AUTO_REFRESH: true,
        NOTIFICATION_SOUND: true,
        // Enable Claude Haiku 4.5 for all clients (2025-11-14)
        CLAUDE_HAIKU_4_5_ENABLED: true
    },
    
    // UI Configuration
    UI: {
        AUTO_REFRESH_INTERVAL: 10000, // 10 seconds
        WEBSOCKET_RECONNECT_DELAY: 5000, // 5 seconds
        NOTIFICATION_TIMEOUT: 5000, // 5 seconds
        MAX_RETRY_ATTEMPTS: 3
    },
    
    // Validation Rules
    VALIDATION: {
        MIN_PASSWORD_LENGTH: 6,
        MAX_MESSAGE_LENGTH: 1000,
        ALLOWED_FILE_TYPES: ['csv', 'json'],
        MAX_BULK_OPERATIONS: 50
    },
    
    // Security Headers
    SECURITY: {
        CONTENT_TYPE: 'application/json',
        CSRF_HEADER: 'X-CSRF-Token'
    }
};

// Google OAuth Configuration (loaded dynamically)
window.GOOGLE_CLIENT_ID = null;
window.googleConfigLoaded = false;

// Load Google OAuth config
fetch('/auth/google/config')
    .then(response => response.json())
    .then(data => {
        window.GOOGLE_CLIENT_ID = data.client_id;
        window.googleConfigLoaded = true;
        console.log('Google OAuth config loaded:', !!data.client_id);
        
        // If no valid client ID, ensure button is hidden
        if (!data.client_id || data.client_id.length < 20) {
            console.log('Google OAuth not configured - client ID missing or invalid');
        }
    })
    .catch(error => {
        console.error('Failed to load Google config:', error);
        window.GOOGLE_CLIENT_ID = null;
        window.googleConfigLoaded = true;
    });

// Export config
window.getConfig = () => window.CONFIG;