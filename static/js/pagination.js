/**
 * Pagination Component
 * Handles client-side and server-side pagination with loading states
 */

class Pagination {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        this.currentPage = 1;
        this.totalPages = 1;
        this.pageSize = options.pageSize || 10;
        this.onPageChange = options.onPageChange || (() => {});
        this.maxButtons = options.maxButtons || 5;
    }

    render(currentPage, totalPages, totalItems) {
        this.currentPage = currentPage;
        this.totalPages = totalPages;

        if (!this.container || totalPages <= 1) {
            if (this.container) this.container.innerHTML = '';
            return;
        }

        const start = (currentPage - 1) * this.pageSize + 1;
        const end = Math.min(currentPage * this.pageSize, totalItems);

        this.container.innerHTML = `
            <div class="d-flex justify-content-between align-items-center">
                <div class="text-muted small" role="status" aria-live="polite">
                    Showing ${start}-${end} of ${totalItems}
                </div>
                <nav aria-label="Pagination navigation">
                    <ul class="pagination pagination-sm mb-0" role="navigation">
                        ${this.renderButtons()}
                    </ul>
                </nav>
            </div>
        `;

        this.attachEventListeners();
    }

    renderButtons() {
        let buttons = [];
        
        // Previous button
        buttons.push(`
            <li class="page-item ${this.currentPage === 1 ? 'disabled' : ''}">
                <a class="page-link" href="#" data-page="${this.currentPage - 1}" 
                   aria-label="Previous page" ${this.currentPage === 1 ? 'aria-disabled="true" tabindex="-1"' : ''}>Previous</a>
            </li>
        `);

        // Page numbers
        const range = this.getPageRange();
        
        if (range[0] > 1) {
            buttons.push(`<li class="page-item"><a class="page-link" href="#" data-page="1" aria-label="Go to page 1">1</a></li>`);
            if (range[0] > 2) buttons.push(`<li class="page-item disabled"><span class="page-link" aria-hidden="true">...</span></li>`);
        }

        range.forEach(page => {
            buttons.push(`
                <li class="page-item ${page === this.currentPage ? 'active' : ''}">
                    <a class="page-link" href="#" data-page="${page}" 
                       aria-label="${page === this.currentPage ? 'Current page, page ' + page : 'Go to page ' + page}"
                       ${page === this.currentPage ? 'aria-current="page"' : ''}>${page}</a>
                </li>
            `);
        });

        if (range[range.length - 1] < this.totalPages) {
            if (range[range.length - 1] < this.totalPages - 1) {
                buttons.push(`<li class="page-item disabled"><span class="page-link" aria-hidden="true">...</span></li>`);
            }
            buttons.push(`<li class="page-item"><a class="page-link" href="#" data-page="${this.totalPages}" aria-label="Go to page ${this.totalPages}">${this.totalPages}</a></li>`);
        }

        // Next button
        buttons.push(`
            <li class="page-item ${this.currentPage === this.totalPages ? 'disabled' : ''}">
                <a class="page-link" href="#" data-page="${this.currentPage + 1}" 
                   aria-label="Next page" ${this.currentPage === this.totalPages ? 'aria-disabled="true" tabindex="-1"' : ''}>Next</a>
            </li>
        `);

        return buttons.join('');
    }

    getPageRange() {
        const half = Math.floor(this.maxButtons / 2);
        let start = Math.max(1, this.currentPage - half);
        let end = Math.min(this.totalPages, start + this.maxButtons - 1);
        
        if (end - start < this.maxButtons - 1) {
            start = Math.max(1, end - this.maxButtons + 1);
        }

        return Array.from({ length: end - start + 1 }, (_, i) => start + i);
    }

    attachEventListeners() {
        this.container.querySelectorAll('.page-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const page = parseInt(e.target.dataset.page);
                if (page && page !== this.currentPage && page >= 1 && page <= this.totalPages) {
                    this.onPageChange(page);
                }
            });
            
            // Keyboard navigation
            link.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    link.click();
                }
            });
        });
        
        // Arrow key navigation
        this.container.addEventListener('keydown', (e) => {
            if (e.key === 'ArrowLeft' && this.currentPage > 1) {
                e.preventDefault();
                this.onPageChange(this.currentPage - 1);
            } else if (e.key === 'ArrowRight' && this.currentPage < this.totalPages) {
                e.preventDefault();
                this.onPageChange(this.currentPage + 1);
            }
        });
    }

    showLoading() {
        if (this.container) {
            this.container.style.opacity = '0.5';
            this.container.style.pointerEvents = 'none';
            this.container.setAttribute('aria-busy', 'true');
        }
    }

    hideLoading() {
        if (this.container) {
            this.container.style.opacity = '1';
            this.container.style.pointerEvents = 'auto';
            this.container.setAttribute('aria-busy', 'false');
        }
    }
}

// Export for use in other scripts
window.Pagination = Pagination;
