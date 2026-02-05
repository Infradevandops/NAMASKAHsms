/**
 * Toast Notification System
 * Displays temporary notifications to user
 */

class ToastNotification {
    constructor() {
        this.container = this.createContainer();
        this.toasts = [];
        this.addStyles();
    }
    
    createContainer() {
        const container = document.createElement('div');
        container.id = 'toast-container';
        container.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 9999;
            display: flex;
            flex-direction: column;
            gap: 10px;
            pointer-events: none;
        `;
        document.body.appendChild(container);
        return container;
    }
    
    addStyles() {
        const style = document.createElement('style');
        style.textContent = `
            @keyframes slideIn {
                from {
                    transform: translateX(400px);
                    opacity: 0;
                }
                to {
                    transform: translateX(0);
                    opacity: 1;
                }
            }
            
            @keyframes slideOut {
                from {
                    transform: translateX(0);
                    opacity: 1;
                }
                to {
                    transform: translateX(400px);
                    opacity: 0;
                }
            }
            
            .toast {
                animation: slideIn 0.3s ease-out;
            }
            
            .toast.removing {
                animation: slideOut 0.3s ease-in;
            }
        `;
        document.head.appendChild(style);
    }
    
    show(message, type = 'info', duration = 3000) {
        const toast = document.createElement('div');
        const icons = {
            'success': '✅',
            'error': '❌',
            'warning': '⚠️',
            'info': 'ℹ️'
        };
        
        const colors = {
            'success': '#10b981',
            'error': '#ef4444',
            'warning': '#f59e0b',
            'info': '#3b82f6'
        };
        
        toast.className = 'toast';
        toast.style.cssText = `
            background: white;
            border-radius: 8px;
            padding: 16px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            display: flex;
            align-items: center;
            gap: 12px;
            min-width: 300px;
            border-left: 4px solid ${colors[type] || colors['info']};
            pointer-events: auto;
        `;
        
        toast.innerHTML = `
            <span style="font-size: 18px; flex-shrink: 0;">${icons[type] || icons['info']}</span>
            <span style="flex: 1; font-size: 14px; color: #333;">${this.escapeHtml(message)}</span>
            <button onclick="this.parentElement.remove()" style="
                background: none;
                border: none;
                font-size: 18px;
                cursor: pointer;
                color: #999;
                padding: 0;
                width: 24px;
                height: 24px;
                display: flex;
                align-items: center;
                justify-content: center;
                flex-shrink: 0;
            ">×</button>
        `;
        
        this.container.appendChild(toast);
        this.toasts.push(toast);
        
        if (duration > 0) {
            setTimeout(() => {
                toast.classList.add('removing');
                setTimeout(() => {
                    toast.remove();
                    this.toasts = this.toasts.filter(t => t !== toast);
                }, 300);
            }, duration);
        }
    }
    
    success(message, duration = 3000) {
        this.show(message, 'success', duration);
    }
    
    error(message, duration = 5000) {
        this.show(message, 'error', duration);
    }
    
    warning(message, duration = 4000) {
        this.show(message, 'warning', duration);
    }
    
    info(message, duration = 3000) {
        this.show(message, 'info', duration);
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Create global instance
window.toast = new ToastNotification();

console.log('✅ Toast notification system loaded');
