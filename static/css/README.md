# CSS Theme System Documentation

## Overview

The Namaskah frontend uses a unified, modular CSS theme system with support for light and dark modes. All styles are built on a single source of truth for design tokens.

## File Structure

### Core Files (Load in this order)

1. **theme-config.css** - Single source of truth for all design tokens
   - Color palette (primary, secondary, status colors)
   - Typography (fonts, sizes, weights)
   - Spacing scale
   - Border radius
   - Shadows
   - Transitions
   - Z-index scale
   - Light/Dark mode variables

2. **components-unified.css** - All component styles
   - Buttons (all variants and sizes)
   - Forms (inputs, selects, textareas)
   - Cards
   - Alerts
   - Badges
   - Tables
   - Icons
   - Layout utilities

3. **buttons.css** - Extended button styles (optional, for advanced features)
   - Button animations
   - Toggle buttons
   - Radio/Checkbox styles
   - Switch/Toggle switches

4. **landing.css** - Landing page specific styles
   - Navigation
   - Hero section
   - Features grid
   - Pricing cards
   - Testimonials
   - CTA section
   - Footer

5. **timeline.css** - Scroll timeline and progress indicators
   - Scroll progress bar
   - Timeline dots
   - Scroll to top button

## CSS Load Order in Templates

### Recommended Import Order

```html
<!-- 1. Core theme configuration (MUST be first) -->
<link rel="stylesheet" href="/static/css/theme-config.css">

<!-- 2. Component styles -->
<link rel="stylesheet" href="/static/css/components-unified.css">

<!-- 3. Optional extended styles -->
<link rel="stylesheet" href="/static/css/buttons.css">

<!-- 4. Page-specific styles -->
<link rel="stylesheet" href="/static/css/landing.css">
<link rel="stylesheet" href="/static/css/timeline.css">
```

## Design Tokens

All design tokens are CSS custom properties (variables) defined in `theme-config.css`.

### Color Variables

```css
/* Primary Colors */
--color-primary: #2563eb;
--color-primary-50 through --color-primary-900: /* Color scale */

/* Secondary Colors */
--color-secondary: #7c3aed;
--color-secondary-50 through --color-secondary-900: /* Color scale */

/* Status Colors */
--color-success: #10b981;
--color-warning: #f59e0b;
--color-error: #ef4444;
--color-info: #0ea5e9;

/* Semantic Colors (Light Mode) */
--color-background: #ffffff;
--color-surface: #f9fafb;
--color-text: #111827;
--color-text-secondary: #6b7280;
--color-border: #e5e7eb;
```

### Typography Variables

```css
--font-family-base: 'Inter', -apple-system, BlinkMacSystemFont, ...;
--font-family-mono: 'Fira Code', 'Courier New', monospace;

--font-size-xs through --font-size-6xl: /* Font size scale */
--font-weight-light through --font-weight-extrabold: /* Font weights */
--line-height-tight through --line-height-loose: /* Line heights */
```

### Spacing Variables

```css
--space-0 through --space-32: /* Spacing scale from 0 to 8rem */
```

### Other Variables

```css
--radius-sm through --radius-full: /* Border radius scale */
--shadow-xs through --shadow-2xl: /* Shadow scale */
--shadow-glow-primary, --shadow-glow-secondary, etc.: /* Glow effects */
--transition-fast through --transition-slowest: /* Transition durations */
--ease-linear, --ease-in, --ease-out, --ease-in-out: /* Easing functions */
--z-hide through --z-max: /* Z-index scale */
```

## Dark Mode Support

### Automatic (System Preference)

Dark mode is automatically applied based on system preference using `prefers-color-scheme: dark`.

### Manual Toggle

Use the theme toggle button to manually switch between light and dark modes. The preference is saved to localStorage.

### Implementation

```html
<!-- Add theme toggle button -->
<button data-theme-toggle class="btn btn-ghost btn-sm">
  <svg class="icon"><!-- sun/moon icon --></svg>
</button>

<!-- Include theme manager script -->
<script src="/static/js/theme-manager.js"></script>
```

### CSS Classes

```css
/* Automatic dark mode (system preference) */
@media (prefers-color-scheme: dark) {
  :root {
    --color-background: #0f172a;
    --color-surface: #1e293b;
    /* ... other dark mode variables ... */
  }
}

/* Manual dark mode toggle */
html.dark-mode {
  --color-background: #0f172a;
  --color-surface: #1e293b;
  /* ... other dark mode variables ... */
}

/* Manual light mode override */
html.light-mode {
  --color-background: #ffffff;
  --color-surface: #f9fafb;
  /* ... other light mode variables ... */
}
```

## Theme Manager JavaScript

The `theme-manager.js` file handles all theme switching logic.

### Features

- Automatic system preference detection
- Manual theme toggle
- localStorage persistence
- Custom event dispatching
- Button state management

### Usage

```javascript
// Access the global theme manager
window.themeManager

// Get current theme
const theme = window.themeManager.getCurrentTheme(); // 'light' or 'dark'

// Set theme explicitly
window.themeManager.setTheme('dark');

// Toggle theme
window.themeManager.toggle();

// Listen for theme changes
window.addEventListener('themechange', (e) => {
  console.log('Theme changed to:', e.detail.theme);
});
```

## Component Usage

### Buttons

```html
<!-- Primary button -->
<button class="btn btn-primary">Click me</button>

<!-- Secondary button -->
<button class="btn btn-secondary">Click me</button>

<!-- Outline button -->
<button class="btn btn-outline">Click me</button>

<!-- Ghost button -->
<button class="btn btn-ghost">Click me</button>

<!-- Button sizes -->
<button class="btn btn-primary btn-sm">Small</button>
<button class="btn btn-primary btn-lg">Large</button>

<!-- Full width button -->
<button class="btn btn-primary btn-block">Full Width</button>
```

### Forms

```html
<div class="form-group">
  <label for="email">Email</label>
  <input type="email" id="email" placeholder="you@example.com">
</div>

<div class="form-group">
  <label for="message">Message</label>
  <textarea id="message"></textarea>
</div>
```

### Cards

```html
<div class="card">
  <div class="card-header">
    <h3>Card Title</h3>
  </div>
  <div class="card-body">
    <p>Card content goes here</p>
  </div>
  <div class="card-footer">
    <button class="btn btn-primary">Action</button>
  </div>
</div>
```

### Alerts

```html
<div class="alert alert-success">Success message</div>
<div class="alert alert-warning">Warning message</div>
<div class="alert alert-error">Error message</div>
<div class="alert alert-info">Info message</div>
```

### Badges

```html
<span class="badge badge-primary">Primary</span>
<span class="badge badge-success">Success</span>
<span class="badge badge-warning">Warning</span>
<span class="badge badge-error">Error</span>
```

## Customization

### Changing Colors

Edit `theme-config.css` to change the primary color:

```css
:root {
  --color-primary: #your-color;
  --color-primary-50: #lighter-shade;
  --color-primary-900: #darker-shade;
  /* ... update all shades ... */
}
```

### Changing Fonts

```css
:root {
  --font-family-base: 'Your Font', sans-serif;
  --font-family-mono: 'Your Mono Font', monospace;
}
```

### Changing Spacing

```css
:root {
  --space-4: 1.2rem; /* Increase base spacing */
  /* All other spacing scales will adjust proportionally */
}
```

## Browser Support

- Chrome/Edge: Full support
- Firefox: Full support
- Safari: Full support (iOS 13+)
- IE11: Not supported (uses CSS custom properties)

## Performance

- All styles use CSS custom properties for efficient theme switching
- No JavaScript required for basic styling (only for theme toggle)
- Minimal CSS file sizes through modular architecture
- Optimized for production with minification

## Migration from Old System

If migrating from the old system:

1. Replace all old CSS imports with new unified imports
2. Update color variable names to use `--color-*` prefix
3. Update spacing variable names to use `--space-*` prefix
4. Add theme manager script for dark mode support
5. Test all pages in both light and dark modes

## Troubleshooting

### Dark mode not working

1. Ensure `theme-config.css` is loaded first
2. Check that `theme-manager.js` is included
3. Verify browser supports `prefers-color-scheme` or manual toggle

### Colors not updating

1. Check CSS load order (theme-config.css must be first)
2. Verify variable names match exactly
3. Clear browser cache

### Buttons not styled

1. Ensure `components-unified.css` is loaded
2. Check that button has correct class (e.g., `btn btn-primary`)
3. Verify no conflicting CSS rules

## Support

For issues or questions, refer to the main README.md or contact the development team.
