// Verification Templates Manager
class VerificationTemplates {
    constructor() {
        this.templates = [];
        this.load();
    }

    load() {
        const stored = localStorage.getItem('verification_templates');
        this.templates = stored ? JSON.parse(stored) : [];
    }

    save() {
        localStorage.setItem('verification_templates', JSON.stringify(this.templates));
    }

    add(name, serviceId, serviceName, cost) {
        const template = {
            id: Date.now().toString(),
            name,
            serviceId,
            serviceName,
            cost,
            createdAt: Date.now()
        };
        this.templates.push(template);
        this.save();
        return template;
    }

    remove(id) {
        this.templates = this.templates.filter(t => t.id !== id);
        this.save();
    }

    getAll() {
        return this.templates;
    }

    renderUI(containerId) {
        const container = document.getElementById(containerId);
        if (!container) return;

        if (this.templates.length === 0) {
            container.innerHTML = '<div style="font-size: 13px; color: #9ca3af; text-align: center; padding: 20px;">No templates saved. Create one to speed up repeat verifications.</div>';
            return;
        }

        container.innerHTML = this.templates.map(t => `
            <div onclick="verificationTemplates.apply('${t.id}')" 
                 style="padding: 12px; cursor: pointer; border: 1px solid #e5e7eb; border-radius: 8px; margin-bottom: 8px; transition: all 0.2s; display: flex; justify-content: space-between; align-items: center;"
                 onmouseover="this.style.background='#f9fafb'; this.style.borderColor='#667eea'"
                 onmouseout="this.style.background='white'; this.style.borderColor='#e5e7eb'">
                <div>
                    <div style="font-weight: 600; color: #1f2937; font-size: 13px;">${t.name}</div>
                    <div style="font-size: 11px; color: #6b7280; margin-top: 2px;">${t.serviceName} • $${t.cost.toFixed(2)}</div>
                </div>
                <button onclick="event.stopPropagation(); verificationTemplates.remove('${t.id}'); verificationTemplates.renderUI('templates-list')" 
                        style="background: none; border: none; cursor: pointer; font-size: 16px; color: #ef4444; padding: 4px;">×</button>
            </div>
        `).join('');
    }

    apply(id) {
        const template = this.templates.find(t => t.id === id);
        if (!template) return;

        if (typeof selectService === 'function') {
            selectService(template.serviceId, template.serviceName, template.cost);
        }
    }

    showSaveModal() {
        if (!selectedService) {
            alert('Please select a service first');
            return;
        }

        const modal = document.createElement('div');
        modal.style.cssText = 'position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; z-index: 10000;';
        modal.onclick = (e) => { if (e.target === modal) modal.remove(); };

        modal.innerHTML = `
            <div style="background: white; border-radius: 12px; padding: 24px; max-width: 400px; width: 90%;" onclick="event.stopPropagation()">
                <h3 style="font-size: 18px; font-weight: 700; margin-bottom: 16px;">Save Template</h3>
                <input type="text" id="template-name-input" placeholder="Template name (e.g., WhatsApp US)" 
                       style="width: 100%; padding: 12px; border: 1px solid #d1d5db; border-radius: 8px; font-size: 14px; margin-bottom: 16px;">
                <div style="display: flex; gap: 8px;">
                    <button onclick="this.closest('[style*=fixed]').remove()" 
                            style="flex: 1; padding: 12px; background: #f3f4f6; border: none; border-radius: 8px; cursor: pointer; font-weight: 600;">Cancel</button>
                    <button onclick="verificationTemplates.saveFromModal()" 
                            style="flex: 1; padding: 12px; background: #667eea; color: white; border: none; border-radius: 8px; cursor: pointer; font-weight: 600;">Save</button>
                </div>
            </div>
        `;

        document.body.appendChild(modal);
        setTimeout(() => document.getElementById('template-name-input').focus(), 100);
    }

    saveFromModal() {
        const name = document.getElementById('template-name-input').value.trim();
        if (!name) {
            alert('Please enter a template name');
            return;
        }

        const service = allServices.find(s => s.id === selectedService);
        if (!service) return;

        this.add(name, service.id, service.name, service.cost);
        this.renderUI('templates-list');
        document.querySelector('[style*="position: fixed"]').remove();
    }
}

window.verificationTemplates = new VerificationTemplates();
