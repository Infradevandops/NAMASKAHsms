# CSS Architecture

## Overview

The Namaskah frontend uses a consolidated CSS architecture with a single source of truth for design tokens. The CSS has been refactored to eliminate duplicates and improve maintainability.

## File Structure

### Core Files (Required - Load in Order)

| File | Purpose | Import Order |
|------|---------|--------------|
| `core.css` | Design tokens, reset, base components | 1 |
| `tier-colors.css` | Tier-specific colors and badges | 2 |
| `dashboard.css` | Dashboard layout and components | 3 |

### Feature-Specific Files

| File | Purpose | When to Include |
|------|---------|-----------------|
| `landing.css` | Landing page styles | Landing page only |
| `pricing-cards.css` | Pricing page cards | Pricing page only |
| `verification.css` | Verification flow | Verification pages |
| `admin-dashboard.css` | Admin panel | Admin pages |
| `design-system.css` | Extended design system | Optional |

### Deprecated Files (Do Not Use in New Code)

These files have been consolidated into `core.css`:

| File | Replaced By | Status |
|------|-------------|--------|
| `buttons.css` | `core.css` | Keep for backward compat |
| `components-unified.css` | `core.css` | Keep for backward compat |
| `tier-components.css` | `tier-colors.css` | Keep for backward compat |
| `theme-config.css` | `core.css` | Keep for backward compat |

## Usage

### Basic Page Template

```html
<head>
    <!-- Core styles (always include) -->
    <link rel="stylesheet" href="/static/css/core.css">
    <link rel="stylesheet" href="/static/css/tier-colors.css">
    
    <!-- Page-specific styles -->
    <link rel="stylesheet" href="/static/css/dashboard.css">
</head>
```

### Design Tokens

All design tokens are CSS variables in `core.css`:

```css
/* Colors */
var(--color-primary)      /* #667eea */
var(--color-success)      /* #10b981 */
var(--color-warning)      /* #f59e0b */
var(--color-error)        /* #ef4444 */

/* Spacing */
var(--space-sm)           /* 0.5rem */
var(--space-md)           /* 1rem */
var(--space-lg)           /* 1.5rem */

/* Typography */
var(--font-size-sm)       /* 0.875rem */
var(--font-size-base)     /* 1rem */
var(--font-size-lg)       /* 1.125rem */

/* Borders */
var(--radius-md)          /* 0.375rem */
var(--radius-lg)          /* 0.5rem */

/* Shadows */
var(--shadow-sm)
var(--shadow-md)
var(--shadow-lg)
```

## Component Classes

### Buttons

```html
<button class="btn btn-primary">Primary</button>
<button class="btn btn-secondary">Secondary</button>
<button class="btn btn-success">Success</button>
<button class="btn btn-error">Error</button>
<button class="btn btn-outline">Outline</button>
<button class="btn btn-ghost">Ghost</button>

<!-- Sizes -->
<button class="btn btn-primary btn-sm">Small</button>
<button class="btn btn-primary btn-lg">Large</button>

<!-- States -->
<button class="btn btn-primary btn-loading">Loading...</button>
<button class="btn btn-primary" disabled>Disabled</button>
```

### Cards

```html
<div class="card">
    <div class="card-header">
        <h3 class="card-title">Title</h3>
    </div>
    <div class="card-body">Content here</div>
    <div class="card-footer">Footer actions</div>
</div>
```

### Alerts

```html
<div class="alert alert-success">Success message</div>
<div class="alert alert-warning">Warning message</div>
<div class="alert alert-error">Error message</div>
<div class="alert alert-info">Info message</div>
```

### Tier Badges

```html
<span class="tier-badge tier-badge-freemium">Freemium</span>
<span class="tier-badge tier-badge-payg">Pay-As-You-Go</span>
<span class="tier-badge tier-badge-pro">Pro</span>
<span class="tier-badge tier-badge-custom">Custom</span>
```

## Jinja2 Macros

For consistent component rendering, use the Jinja2 macros in `templates/macros/ui_components.html`:

```jinja2
{% from "macros/ui_components.html" import tier_badge, button, card, alert, loading_spinner %}

{{ tier_badge('pro') }}
{{ button('Submit', variant='primary', type='submit') }}
{{ alert('Success!', type='success') }}
{{ loading_spinner(size='lg', text='Loading...') }}

{% call card(title='User Profile') %}
    <p>Card content</p>
{% endcall %}
```

### Available Macros

| Macro | Purpose |
|-------|---------|
| `tier_badge(tier, size, solid)` | Tier badge with styling |
| `button(text, variant, size, ...)` | Button with all variants |
| `card(title, id, class, ...)` | Card container |
| `alert(message, type, dismissible)` | Alert/notification |
| `loading_spinner(size, text)` | Loading indicator |
| `skeleton(type, lines)` | Skeleton loader |
| `form_input(name, label, ...)` | Form input with label |
| `progress_bar(value, max, ...)` | Progress bar |
| `empty_state(title, message, ...)` | Empty state placeholder |
| `tier_card_full(tier, name, ...)` | Full tier card |

## Migration Guide

If updating existing templates:

1. Replace `buttons.css` import with `core.css`
2. Replace `components-unified.css` import with `core.css`
3. Replace `theme-config.css` import with `core.css`
4. Use CSS variables instead of hardcoded colors
5. Use Jinja2 macros for consistent components

## Dark Mode

Dark mode is supported via `[data-theme="dark"]` on `<html>`:

```html
<html data-theme="dark">
```

Override variables for dark mode:

```css
[data-theme="dark"] {
    --color-background: #1a1a2e;
    --color-surface: #252540;
    --color-text: #ffffff;
}
```

## Browser Support

- Chrome/Edge: Full support
- Firefox: Full support
- Safari: Full support (iOS 13+)
- IE11: Not supported (uses CSS custom properties)
