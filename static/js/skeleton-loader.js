/**
 * Skeleton loading state to prevent UI flashing
 * 
 * This loader displays a skeleton/placeholder UI while the tier is being loaded.
 * It prevents the "freemium flash" by showing a loading state instead of the
 * actual UI with wrong tier information.
 */

class SkeletonLoader {
    static SKELETON_HTML = `
        <div class="skeleton-container" style="
            width: 100%;
            height: 100vh;
            background: #f9fafb;
            display: flex;
            flex-direction: column;
            font-family: system-ui, -apple-system, sans-serif;
        ">
            <!-- Header Skeleton -->
            <div class="skeleton-header" style="
                height: 60px;
                background: #fff;
                border-bottom: 1px solid #e5e7eb;
                display: flex;
                align-items: center;
                padding: 0 20px;
                gap: 12px;
            ">
                <div class="skeleton-pulse" style="
                    width: 40px;
                    height: 40px;
                    border-radius: 50%;
                    background: #e5e7eb;
                "></div>
                <div class="skeleton-pulse" style="
                    width: 200px;
                    height: 20px;
                    background: #e5e7eb;
                "></div>
                <div style="flex: 1;"></div>
                <div class="skeleton-pulse" style="
                    width: 100px;
                    height: 20px;
                    background: #e5e7eb;
                "></div>
            </div>
            
            <!-- Main Content -->
            <div style="display: flex; flex: 1;">
                <!-- Sidebar Skeleton -->
                <div class="skeleton-sidebar" style="
                    width: 250px;
                    background: #fff;
                    border-right: 1px solid #e5e7eb;
                    padding: 20px;
                    display: flex;
                    flex-direction: column;
                    gap: 12px;
                ">
                    ${Array(5).fill(0).map(() => `
                        <div class="skeleton-pulse" style="
                            width: 100%;
                            height: 40px;
                            background: #e5e7eb;
                            border-radius: 6px;
                        "></div>
                    `).join('')}
                </div>
                
                <!-- Content Skeleton -->
                <div class="skeleton-content" style="
                    flex: 1;
                    padding: 20px;
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                    gap: 20px;
                    overflow-y: auto;
                ">
                    ${Array(4).fill(0).map(() => `
                        <div class="skeleton-card" style="
                            background: #fff;
                            border-radius: 8px;
                            padding: 20px;
                            display: flex;
                            flex-direction: column;
                            gap: 12px;
                            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                        ">
                            <div class="skeleton-pulse" style="
                                width: 100%;
                                height: 20px;
                                background: #e5e7eb;
                            "></div>
                            <div class="skeleton-pulse" style="
                                width: 80%;
                                height: 16px;
                                background: #e5e7eb;
                            "></div>
                            <div class="skeleton-pulse" style="
                                width: 60%;
                                height: 16px;
                                background: #e5e7eb;
                            "></div>
                            <div style="flex: 1;"></div>
                            <div class="skeleton-pulse" style="
                                width: 100%;
                                height: 40px;
                                background: #e5e7eb;
                                border-radius: 6px;
                            "></div>
                        </div>
                    `).join('')}
                </div>
            </div>
        </div>
        
        <style>
            @keyframes skeleton-pulse {
                0%, 100% { opacity: 1; }
                50% { opacity: 0.5; }
            }
            .skeleton-pulse {
                animation: skeleton-pulse 2s ease-in-out infinite;
            }
            @keyframes fadeOut {
                from { opacity: 1; }
                to { opacity: 0; }
            }
        </style>
    `;
    
    /**
     * Show skeleton loading state
     * 
     * Replaces the entire body with skeleton HTML to show loading state
     * while tier is being loaded.
     */
    static show() {
        try {
            const container = document.createElement('div');
            container.innerHTML = this.SKELETON_HTML;
            document.body.innerHTML = '';
            document.body.appendChild(container);
            console.log('[SkeletonLoader] Skeleton displayed');
        } catch (error) {
            console.error('[SkeletonLoader] Failed to show skeleton:', error);
        }
    }
    
    /**
     * Hide skeleton loading state
     * 
     * Fades out and removes the skeleton, revealing the actual UI
     * that was rendered behind it.
     */
    static hide() {
        try {
            const skeleton = document.querySelector('.skeleton-container');
            if (skeleton) {
                skeleton.style.animation = 'fadeOut 0.3s ease-out';
                setTimeout(() => {
                    skeleton.remove();
                    console.log('[SkeletonLoader] Skeleton hidden');
                }, 300);
            }
        } catch (error) {
            console.error('[SkeletonLoader] Failed to hide skeleton:', error);
        }
    }
    
    /**
     * Check if skeleton is currently visible
     * 
     * @returns {boolean} True if skeleton is visible
     */
    static isVisible() {
        return !!document.querySelector('.skeleton-container');
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SkeletonLoader;
}
