// Searchable Dropdown Component
class SearchableDropdown {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        this.options = {
            placeholder: 'Search...',
            maxHeight: '300px',
            showFlags: true,
            ...options
        };
        this.data = [];
        this.filteredData = [];
        this.selectedValue = null;
        this.isOpen = false;
        
        this.init();
    }
    
    init() {
        this.createHTML();
        this.bindEvents();
    }
    
    createHTML() {
        this.container.innerHTML = `
            <div class="searchable-dropdown">
                <div class="dropdown-input" id="${this.container.id}-input">
                    <input type="text" 
                           class="search-input" 
                           placeholder="${this.options.placeholder}"
                           id="${this.container.id}-search">
                    <span class="dropdown-arrow">▼</span>
                </div>
                <div class="dropdown-list" 
                     id="${this.container.id}-list" 
                     style="max-height: ${this.options.maxHeight}">
                    <!-- Options will be populated here -->
                </div>
            </div>
        `;
        
        this.searchInput = document.getElementById(`${this.container.id}-search`);
        this.dropdownList = document.getElementById(`${this.container.id}-list`);
        this.dropdownInput = document.getElementById(`${this.container.id}-input`);
    }
    
    bindEvents() {
        // Toggle dropdown
        this.dropdownInput.addEventListener('click', () => this.toggle());
        
        // Search functionality
        this.searchInput.addEventListener('input', (e) => this.handleSearch(e.target.value));
        
        // Keyboard navigation
        this.searchInput.addEventListener('keydown', (e) => this.handleKeydown(e));
        
        // Close on outside click
        document.addEventListener('click', (e) => {
            if (!this.container.contains(e.target)) {
                this.close();
            }
        });
    }
    
    setData(data) {
        this.data = data;
        this.filteredData = [...data];
        this.renderOptions();
    }
    
    handleSearch(query) {
        if (!query.trim()) {
            this.filteredData = [...this.data];
        } else {
            this.filteredData = this.data.filter(item => 
                item.name.toLowerCase().includes(query.toLowerCase()) ||
                item.code.toLowerCase().includes(query.toLowerCase())
            );
        }
        this.renderOptions();
        this.open();
    }
    
    renderOptions() {
        if (this.filteredData.length === 0) {
            this.dropdownList.innerHTML = '<div class="no-results">No results found</div>';
            return;
        }
        
        const html = this.filteredData.map(item => `
            <div class="dropdown-option" data-value="${item.code}" data-name="${item.name}">
                ${this.options.showFlags ? `<span class="flag">${item.flag || '🏳️'}</span>` : ''}
                <span class="name">${item.name}</span>
                ${item.count ? `<span class="count">(${item.count})</span>` : ''}
            </div>
        `).join('');
        
        this.dropdownList.innerHTML = html;
        
        // Bind click events to options
        this.dropdownList.querySelectorAll('.dropdown-option').forEach(option => {
            option.addEventListener('click', () => {
                this.selectOption(option.dataset.value, option.dataset.name);
            });
        });
    }
    
    selectOption(value, name) {
        this.selectedValue = value;
        this.searchInput.value = name;
        this.close();
        
        // Trigger change event
        this.container.dispatchEvent(new CustomEvent('change', {
            detail: { value, name }
        }));
    }
    
    open() {
        this.isOpen = true;
        this.dropdownList.style.display = 'block';
        this.container.classList.add('open');
    }
    
    close() {
        this.isOpen = false;
        this.dropdownList.style.display = 'none';
        this.container.classList.remove('open');
    }
    
    toggle() {
        if (this.isOpen) {
            this.close();
        } else {
            this.open();
        }
    }
    
    handleKeydown(e) {
        const options = this.dropdownList.querySelectorAll('.dropdown-option');
        const currentActive = this.dropdownList.querySelector('.dropdown-option.active');
        let activeIndex = Array.from(options).indexOf(currentActive);
        
        switch (e.key) {
            case 'ArrowDown':
                e.preventDefault();
                activeIndex = Math.min(activeIndex + 1, options.length - 1);
                this.setActiveOption(options[activeIndex]);
                break;
                
            case 'ArrowUp':
                e.preventDefault();
                activeIndex = Math.max(activeIndex - 1, 0);
                this.setActiveOption(options[activeIndex]);
                break;
                
            case 'Enter':
                e.preventDefault();
                if (currentActive) {
                    this.selectOption(currentActive.dataset.value, currentActive.dataset.name);
                }
                break;
                
            case 'Escape':
                this.close();
                break;
        }
    }
    
    setActiveOption(option) {
        // Remove active class from all options
        this.dropdownList.querySelectorAll('.dropdown-option').forEach(opt => {
            opt.classList.remove('active');
        });
        
        // Add active class to selected option
        if (option) {
            option.classList.add('active');
            option.scrollIntoView({ block: 'nearest' });
        }
    }
    
    getValue() {
        return this.selectedValue;
    }
    
    setValue(value) {
        const item = this.data.find(d => d.code === value);
        if (item) {
            this.selectOption(value, item.name);
        }
    }
}

// CSS Styles for Searchable Dropdown
const dropdownStyles = `
<style>
.searchable-dropdown {
    position: relative;
    width: 100%;
}

.dropdown-input {
    position: relative;
    border: 2px solid var(--border, #e5e7eb);
    border-radius: 12px;
    background: var(--bg-primary, white);
    cursor: pointer;
    transition: border-color 0.2s;
}

.dropdown-input:hover {
    border-color: var(--primary, #667eea);
}

.searchable-dropdown.open .dropdown-input {
    border-color: var(--primary, #667eea);
    border-bottom-left-radius: 0;
    border-bottom-right-radius: 0;
}

.search-input {
    width: 100%;
    padding: 16px;
    border: none;
    background: transparent;
    font-size: 16px;
    outline: none;
    cursor: pointer;
}

.search-input:focus {
    cursor: text;
}

.dropdown-arrow {
    position: absolute;
    right: 16px;
    top: 50%;
    transform: translateY(-50%);
    color: var(--text-secondary, #6b7280);
    pointer-events: none;
    transition: transform 0.2s;
}

.searchable-dropdown.open .dropdown-arrow {
    transform: translateY(-50%) rotate(180deg);
}

.dropdown-list {
    position: absolute;
    top: 100%;
    left: 0;
    right: 0;
    background: var(--bg-primary, white);
    border: 2px solid var(--primary, #667eea);
    border-top: none;
    border-bottom-left-radius: 12px;
    border-bottom-right-radius: 12px;
    max-height: 300px;
    overflow-y: auto;
    z-index: 1000;
    display: none;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.dropdown-option {
    display: flex;
    align-items: center;
    padding: 12px 16px;
    cursor: pointer;
    transition: background-color 0.2s;
    border-bottom: 1px solid var(--border, #e5e7eb);
}

.dropdown-option:last-child {
    border-bottom: none;
}

.dropdown-option:hover,
.dropdown-option.active {
    background: var(--bg-secondary, #f8fafc);
}

.dropdown-option .flag {
    margin-right: 12px;
    font-size: 18px;
}

.dropdown-option .name {
    flex: 1;
    font-weight: 500;
}

.dropdown-option .count {
    color: var(--text-secondary, #6b7280);
    font-size: 14px;
}

.no-results {
    padding: 20px;
    text-align: center;
    color: var(--text-secondary, #6b7280);
    font-style: italic;
}

/* Mobile optimizations */
@media (max-width: 768px) {
    .dropdown-list {
        max-height: 250px;
    }
    
    .dropdown-option {
        padding: 16px;
        font-size: 16px;
    }
    
    .dropdown-option .flag {
        font-size: 20px;
    }
}
</style>
`;

// Inject styles
if (!document.getElementById('searchable-dropdown-styles')) {
    const styleElement = document.createElement('div');
    styleElement.id = 'searchable-dropdown-styles';
    styleElement.innerHTML = dropdownStyles;
    document.head.appendChild(styleElement);
}

// Export for use
window.SearchableDropdown = SearchableDropdown;