// Favorite Services Manager
class FavoriteServices {
    constructor() {
        this.favorites = [];
        this.load();
    }

    load() {
        const stored = localStorage.getItem('favorite_services');
        this.favorites = stored ? JSON.parse(stored) : [];
    }

    save() {
        localStorage.setItem('favorite_services', JSON.stringify(this.favorites));
    }

    add(serviceId, serviceName, cost) {
        if (!this.isFavorite(serviceId)) {
            this.favorites.push({ id: serviceId, name: serviceName, cost, addedAt: Date.now() });
            this.save();
            return true;
        }
        return false;
    }

    remove(serviceId) {
        this.favorites = this.favorites.filter(f => f.id !== serviceId);
        this.save();
    }

    isFavorite(serviceId) {
        return this.favorites.some(f => f.id === serviceId);
    }

    getAll() {
        return this.favorites;
    }

    renderUI(containerId) {
        const container = document.getElementById(containerId);
        if (!container) return;

        if (this.favorites.length === 0) {
            container.innerHTML = '<div style="font-size: 13px; color: #9ca3af; text-align: center; padding: 20px;">No favorites yet. Click ⭐ on any service to add.</div>';
            return;
        }

        container.innerHTML = this.favorites.map(f => `
            <div onclick="selectService('${f.id}', '${f.name.replace(/'/g, "\\'")}', ${f.cost})" 
                 style="padding: 10px; cursor: pointer; border-bottom: 1px solid #f3f4f6; transition: background 0.15s; display: flex; justify-content: space-between; align-items: center;"
                 onmouseover="this.style.background='#f9fafb'"
                 onmouseout="this.style.background='white'">
                <div>
                    <div style="font-weight: 600; color: #1f2937; font-size: 13px;">${f.name}</div>
                    <div style="font-size: 11px; color: #6b7280;">$${f.cost.toFixed(2)}</div>
                </div>
                <button onclick="event.stopPropagation(); favoriteServices.remove('${f.id}'); favoriteServices.renderUI('favorites-list')" 
                        style="background: none; border: none; cursor: pointer; font-size: 16px; color: #f59e0b;">⭐</button>
            </div>
        `).join('');
    }
}

window.favoriteServices = new FavoriteServices();
