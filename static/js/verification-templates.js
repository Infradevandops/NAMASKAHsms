/**
 * Verification Templates Module
 * Save and reuse country/service combinations
 */

class VerificationTemplates {
    constructor() {
        this.templates = this.loadTemplates();
        this.init();
    }

    init() {
        this.renderTemplates();
        this.setupEventListeners();
    }

    setupEventListeners() {
        // Save template button
        document.getElementById('save-template-btn')?.addEventListener('click', () => this.showSaveDialog());
        
        // Template actions
        document.addEventListener('click', (e) => {
            if (e.target.closest('.use-template-btn')) {
                const id = e.target.closest('.use-template-btn').dataset.templateId;
                this.useTemplate(id);
            }
            if (e.target.closest('.delete-template-btn')) {
                const id = e.target.closest('.delete-template-btn').dataset.templateId;
                this.deleteTemplate(id);
            }
        });
    }

    loadTemplates() {
        const stored = localStorage.getItem('verification_templates');
        return stored ? JSON.parse(stored) : [];
    }

    saveTemplates() {
        localStorage.setItem('verification_templates', JSON.stringify(this.templates));
    }

    showSaveDialog() {
        const service = document.getElementById('service-select').value;
        const country = document.getElementById('country-select').value;

        if (!service || !country) {
            this.showToast('Please select a service and country first', 'warning');
            return;
        }

        const name = prompt('Enter a name for this template:', `${service} - ${country}`);
        if (!name) return;

        this.saveTemplate(name, service, country);
    }

    saveTemplate(name, service, country) {
        const template = {
            id: Date.now().toString(),
            name,
            service,
            country,
            createdAt: new Date().toISOString()
        };

        this.templates.push(template);
        this.saveTemplates();
        this.renderTemplates();
        this.showToast('Template saved successfully!', 'success');
    }

    useTemplate(id) {
        const template = this.templates.find(t => t.id === id);
        if (!template) return;

        document.getElementById('service-select').value = template.service;
        document.getElementById('country-select').value = template.country;
        
        // Trigger change events
        document.getElementById('service-select').dispatchEvent(new Event('change'));
        document.getElementById('country-select').dispatchEvent(new Event('change'));

        this.showToast(`Applied template: ${template.name}`, 'success');
    }

    deleteTemplate(id) {
        if (!confirm('Delete this template?')) return;

        this.templates = this.templates.filter(t => t.id !== id);
        this.saveTemplates();
        this.renderTemplates();
        this.showToast('Template deleted', 'info');
    }

    renderTemplates() {
        const container = document.getElementById('templates-list');
        if (!container) return;

        if (this.templates.length === 0) {
            container.innerHTML = '<p class="text-muted small">No saved templates</p>';
            return;
        }

        container.innerHTML = this.templates.map(t => `
            <div class="template-item d-flex align-items-center justify-content-between mb-2 p-2 border rounded">
                <div class="flex-grow-1">
                    <strong>${t.name}</strong>
                    <small class="text-muted d-block">${t.service} • ${t.country}</small>
                </div>
                <div class="btn-group btn-group-sm">
                    <button class="btn btn-outline-primary use-template-btn" data-template-id="${t.id}">
                        <i class="fas fa-check"></i>
                    </button>
                    <button class="btn btn-outline-danger delete-template-btn" data-template-id="${t.id}">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
        `).join('');
    }

    showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `alert alert-${type} position-fixed top-0 end-0 m-3`;
        toast.style.zIndex = '9999';
        toast.textContent = message;
        document.body.appendChild(toast);
        setTimeout(() => toast.remove(), 3000);
    }
}

// Initialize
let verificationTemplates;
document.addEventListener('DOMContentLoaded', () => {
    verificationTemplates = new VerificationTemplates();
});
