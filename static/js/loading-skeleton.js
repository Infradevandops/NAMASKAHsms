/**
 * Loading Skeleton Component
 * Provides visual feedback while content loads
 */

class LoadingSkeleton {
    static create(type, options = {}) {
        const skeleton = document.createElement('div');
        skeleton.className = 'skeleton';
        skeleton.setAttribute('aria-busy', 'true');
        skeleton.setAttribute('aria-live', 'polite');

        switch (type) {
            case 'card':
                return this.createCard(options);
            case 'table':
                return this.createTable(options);
            case 'chart':
                return this.createChart(options);
            case 'text':
                return this.createText(options);
            case 'stat':
                return this.createStat(options);
            default:
                return skeleton;
        }
    }

    static createCard(options = {}) {
        const { height = '200px', padding = '24px' } = options;
        const card = document.createElement('div');
        card.className = 'skeleton-card';
        card.style.cssText = `
            background: white;
            border-radius: 12px;
            padding: ${padding};
            height: ${height};
            animation: pulse 1.5s ease-in-out infinite;
        `;
        card.innerHTML = `
            <div class="skeleton-line" style="width: 40%; height: 20px; margin-bottom: 16px;"></div>
            <div class="skeleton-line" style="width: 100%; height: 100px;"></div>
        `;
        return card;
    }

    static createTable(options = {}) {
        const { rows = 5, columns = 4 } = options;
        const table = document.createElement('div');
        table.className = 'skeleton-table';
        
        let html = '<div style="display: flex; gap: 12px; margin-bottom: 12px; padding: 12px; background: #f9fafb; border-radius: 8px;">';
        for (let i = 0; i < columns; i++) {
            html += '<div class="skeleton-line" style="flex: 1; height: 16px;"></div>';
        }
        html += '</div>';

        for (let i = 0; i < rows; i++) {
            html += '<div style="display: flex; gap: 12px; margin-bottom: 8px; padding: 12px; border-bottom: 1px solid #f3f4f6;">';
            for (let j = 0; j < columns; j++) {
                html += '<div class="skeleton-line" style="flex: 1; height: 14px;"></div>';
            }
            html += '</div>';
        }

        table.innerHTML = html;
        return table;
    }

    static createChart(options = {}) {
        const { height = '300px' } = options;
        const chart = document.createElement('div');
        chart.className = 'skeleton-chart';
        chart.style.cssText = `
            height: ${height};
            background: linear-gradient(135deg, #f3f4f6 0%, #e5e7eb 100%);
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            animation: pulse 1.5s ease-in-out infinite;
        `;
        chart.innerHTML = `
            <div style="text-align: center; color: #9ca3af;">
                <div style="font-size: 32px; margin-bottom: 8px;">📊</div>
                <div style="font-size: 14px;">Loading chart...</div>
            </div>
        `;
        return chart;
    }

    static createText(options = {}) {
        const { width = '100%', height = '16px' } = options;
        const text = document.createElement('div');
        text.className = 'skeleton-line';
        text.style.cssText = `
            width: ${width};
            height: ${height};
            background: #e5e7eb;
            border-radius: 4px;
            animation: pulse 1.5s ease-in-out infinite;
        `;
        return text;
    }

    static createStat(options = {}) {
        const stat = document.createElement('div');
        stat.className = 'skeleton-stat';
        stat.style.cssText = `
            background: white;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        `;
        stat.innerHTML = `
            <div class="skeleton-line" style="width: 60%; height: 12px; margin-bottom: 12px;"></div>
            <div class="skeleton-line" style="width: 40%; height: 32px;"></div>
        `;
        return stat;
    }

    static show(container, type, options = {}) {
        if (typeof container === 'string') {
            container = document.getElementById(container) || document.querySelector(container);
        }
        if (!container) return;

        const skeleton = this.create(type, options);
        container.innerHTML = '';
        container.appendChild(skeleton);
    }

    static hide(container) {
        if (typeof container === 'string') {
            container = document.getElementById(container) || document.querySelector(container);
        }
        if (!container) return;

        const skeletons = container.querySelectorAll('.skeleton, .skeleton-card, .skeleton-table, .skeleton-chart, .skeleton-stat');
        skeletons.forEach(s => s.remove());
    }
}

// Add CSS
const style = document.createElement('style');
style.textContent = `
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }

    .skeleton-line {
        background: linear-gradient(90deg, #e5e7eb 25%, #f3f4f6 50%, #e5e7eb 75%);
        background-size: 200% 100%;
        animation: shimmer 1.5s ease-in-out infinite;
        border-radius: 4px;
    }

    @keyframes shimmer {
        0% { background-position: 200% 0; }
        100% { background-position: -200% 0; }
    }

    .skeleton-card, .skeleton-table, .skeleton-chart, .skeleton-stat {
        animation: fadeIn 0.3s ease;
    }

    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }
`;
document.head.appendChild(style);

// Export
window.LoadingSkeleton = LoadingSkeleton;

console.log('✅ Loading skeleton component initialized');
