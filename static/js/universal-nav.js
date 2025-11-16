/**
 * Universal Navigation Component
 * Adds consistent Namaskah logo with wave animation and theme toggle to all pages
 */

(function() {
    'use strict';
    
    // Check if nav already exists or if page has its own top-nav
    if (document.querySelector('.universal-nav') || document.querySelector('.top-nav')) return;
    
    // Create navigation
    const nav = document.createElement('div');
    nav.className = 'universal-nav';
    nav.innerHTML = `
        <div class="universal-logo" onclick="window.location.href='/'" style="cursor: pointer; position: relative;">
            Namaskah
            <svg width="80" height="8" style="position: absolute; bottom: -5px; left: 0;">
                <path d="M 0 4 Q 20 0, 40 4 T 80 4" stroke="#667eea" stroke-width="2" fill="none" stroke-linecap="round">
                    <animate attributeName="d" 
                        values="M 0 4 Q 20 0, 40 4 T 80 4; M 0 4 Q 20 8, 40 4 T 80 4; M 0 4 Q 20 0, 40 4 T 80 4" 
                        dur="2s" repeatCount="indefinite"/>
                </path>
            </svg>
        </div>
        <div class="universal-theme-toggle" onclick="toggleUniversalTheme()"></div>
    `;
    
    // Add styles
    const style = document.createElement('style');
    style.textContent = `
        .universal-nav {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 15px 20px;
            background: var(--bg-secondary);
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            z-index: 500;
        }
        
        .universal-logo {
            font-size: 1.2rem;
            font-weight: bold;
            color: var(--text-primary);
            transition: transform 0.3s ease;
            user-select: none;
        }
        
        .universal-logo:hover {
            transform: scale(1.05);
        }
        
        .universal-theme-toggle {
            width: 50px;
            height: 26px;
            background: var(--border);
            border-radius: 13px;
            position: relative;
            cursor: pointer;
            transition: background 0.3s;
        }
        
        .universal-theme-toggle::after {
            content: '🌙';
            position: absolute;
            top: 2px;
            left: 2px;
            width: 22px;
            height: 22px;
            background: white;
            border-radius: 50%;
            transition: transform 0.3s;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 12px;
        }
        
        [data-theme="light"] .universal-theme-toggle::after {
            content: '☀️';
            transform: translateX(24px);
        }
        
        body {
            padding-top: 60px;
        }
        
        @media (max-width: 768px) {
            .universal-nav {
                padding: 12px 15px;
            }
            .universal-logo {
                font-size: 1rem;
            }
            body {
                padding-top: 55px;
            }
        }
    `;
    
    // Theme toggle function
    window.toggleUniversalTheme = function() {
        const current = document.documentElement.getAttribute('data-theme') || 'dark';
        const next = current === 'dark' ? 'light' : 'dark';
        document.documentElement.setAttribute('data-theme', next);
        localStorage.setItem('theme', next);
    };
    
    // Apply saved theme
    const savedTheme = localStorage.getItem('theme') || 'dark';
    document.documentElement.setAttribute('data-theme', savedTheme);
    
    // Add to page with fade-in
    document.head.appendChild(style);
    nav.style.opacity = '0';
    nav.style.transition = 'opacity 0.3s ease-in';
    document.body.insertBefore(nav, document.body.firstChild);
    
    // Fade in after DOM insertion
    requestAnimationFrame(() => {
        setTimeout(() => {
            nav.style.opacity = '1';
        }, 50);
    });
    
    console.log('✅ Universal navigation loaded');
})();
