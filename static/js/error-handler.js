// Global Error Handler for Smooth UX
class ErrorHandler {
    static init() {
        // Handle network errors
        window.addEventListener('unhandledrejection', this.handlePromiseRejection);
        
        // Handle JS errors
        window.addEventListener('error', this.handleError);
        
        // Handle navigation errors
        this.setupNavigationErrorHandling();
    }
    
    // Network/Promise error handling
    static handlePromiseRejection(event) {
        console.error('Network error:', event.reason);
        
        if (event.reason?.message?.includes('fetch')) {
            NotificationManager.show('Connection issue. Please check your internet.', 'warning');
        }
        
        event.preventDefault();
    }
    
    // JavaScript error handling
    static handleError(event) {
        console.error('JS Error:', event.error);
        
        // Don't show notifications for minor errors
        if (!event.error?.message?.includes('ResizeObserver')) {
            NotificationManager.show('Something went wrong. Please refresh the page.', 'error');
        }
    }
    
    // Navigation error handling
    static setupNavigationErrorHandling() {
        // Intercept failed navigation
        const originalPushState = history.pushState;
        history.pushState = function(...args) {
            try {
                return originalPushState.apply(this, args);
            } catch (error) {
                console.error('Navigation error:', error);
                NotificationManager.show('Navigation failed', 'error');
            }
        };
    }
}

// Authentication Error Handler
class AuthHandler {
    static handleAuthError(response) {
        if (response.status === 401) {
            this.logout('Session expired. Please login again.');
            return true;
        }
        
        if (response.status === 403) {
            NotificationManager.show('Access denied', 'error');
            return true;
        }
        
        return false;
    }
    
    static logout(message = 'Logged out') {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        NotificationManager.show(message, 'info');
        
        // Smooth redirect
        setTimeout(() => {
            window.location.href = '/auth/login';
        }, 1000);
    }
    
    static validateToken() {
        const token = localStorage.getItem('token');
        if (!token) return false;
        
        try {
            const payload = JSON.parse(atob(token.split('.')[1]));
            return payload.exp * 1000 > Date.now();
        } catch {
            return false;
        }
    }
}

// Notification Manager
class NotificationManager {
    static show(message, type = 'info', duration = 5000) {
        // Remove existing notifications
        document.querySelectorAll('.notification').forEach(n => n.remove());
        
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 16px 20px;
            border-radius: 8px;
            color: white;
            font-weight: 600;
            z-index: 10000;
            max-width: 400px;
            animation: slideIn 0.3s ease;
        `;
        
        // Set background color based on type
        const colors = {
            success: '#10b981',
            error: '#ef4444',
            warning: '#f59e0b',
            info: '#3b82f6'
        };
        notification.style.background = colors[type] || colors.info;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => notification.remove(), 300);
        }, duration);
    }
}

// Loading Manager
class LoadingManager {
    static show(element, text = 'Loading...') {
        if (typeof element === 'string') {
            element = document.getElementById(element);
        }
        
        if (!element) return;
        
        element.innerHTML = `
            <div style="display: flex; align-items: center; justify-content: center; padding: 20px;">
                <div style="width: 20px; height: 20px; border: 2px solid #f3f3f3; border-top: 2px solid #667eea; border-radius: 50%; animation: spin 1s linear infinite; margin-right: 10px;"></div>
                <span>${text}</span>
            </div>
        `;
    }
    
    static hide(element, content = '') {
        if (typeof element === 'string') {
            element = document.getElementById(element);
        }
        
        if (!element) return;
        element.innerHTML = content;
    }
}

// Smooth Navigation
class NavigationManager {
    static smoothScrollTo(elementId) {
        const element = document.getElementById(elementId);
        if (element) {
            element.scrollIntoView({ 
                behavior: 'smooth', 
                block: 'start' 
            });
        }
    }
    
    static showSection(sectionName) {
        // Hide all sections with fade
        document.querySelectorAll('.section').forEach(section => {
            section.style.opacity = '0';
            setTimeout(() => section.classList.add('hidden'), 150);
        });
        
        // Show target section with fade
        setTimeout(() => {
            const targetSection = document.getElementById(`${sectionName}-section`);
            if (targetSection) {
                targetSection.classList.remove('hidden');
                targetSection.style.opacity = '1';
                this.smoothScrollTo(`${sectionName}-section`);
            }
        }, 200);
    }
}

// API Helper with Error Handling
class APIHelper {
    static async request(url, options = {}) {
        const token = localStorage.getItem('token');
        
        // Validate token before request
        if (token && !AuthHandler.validateToken()) {
            AuthHandler.logout('Session expired');
            throw new Error('Token expired');
        }
        
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
                ...(token && { 'Authorization': `Bearer ${token}` })
            }
        };
        
        const finalOptions = { ...defaultOptions, ...options };
        
        try {
            const response = await fetch(url, finalOptions);
            
            // Handle auth errors
            if (AuthHandler.handleAuthError(response)) {
                throw new Error('Authentication failed');
            }
            
            // Handle other HTTP errors
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.message || `HTTP ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('API Error:', error);
            
            if (error.message.includes('fetch')) {
                NotificationManager.show('Network error. Please check your connection.', 'error');
            } else if (!error.message.includes('Authentication')) {
                NotificationManager.show(error.message || 'Request failed', 'error');
            }
            
            throw error;
        }
    }
}

// Initialize error handling
document.addEventListener('DOMContentLoaded', () => {
    ErrorHandler.init();
    
    // Add CSS for animations
    const style = document.createElement('style');
    style.textContent = `
        @keyframes slideIn {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
        @keyframes slideOut {
            from { transform: translateX(0); opacity: 1; }
            to { transform: translateX(100%); opacity: 0; }
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        .section {
            transition: opacity 0.3s ease;
        }
    `;
    document.head.appendChild(style);
});

// Export for global use
window.ErrorHandler = ErrorHandler;
window.AuthHandler = AuthHandler;
window.NotificationManager = NotificationManager;
window.LoadingManager = LoadingManager;
window.NavigationManager = NavigationManager;
window.APIHelper = APIHelper;