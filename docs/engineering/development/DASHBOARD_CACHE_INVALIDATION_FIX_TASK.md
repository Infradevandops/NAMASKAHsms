# Task: Fix Dashboard Cache Invalidation Script

**Status:** ✅ CLOSED — pre-existing fix confirmed
**Area:** Dashboard / service-worker cache invalidation
**Affected file:** `templates/dashboard_base.html`

## Problem

The inline cache-version script has an extra closing brace immediately before
the IIFE invocation. Once Jinja renders the template, the browser rejects the
entire script with `SyntaxError: Unexpected token '}'`.

As a result, the script does not compare or update `i18n_version` in
`localStorage` and does not delete the old `vrenum` Cache Storage entries.
Users can continue receiving stale cached static assets after a deployment.

## Required fix

Remove the unmatched closing brace from the inline script in
`templates/dashboard_base.html`. Keep the existing behavior:

- Compare the stored `i18n_version` with the server-rendered `app_version`.
- On version change, delete Cache Storage entries whose names contain
  `vrenum`.
- Record the current version in `localStorage`.
- Load the versioned i18n script as before.

Do not broaden cache deletion or change service-worker cache policy as part of
this task.

## Acceptance criteria

- The rendered inline script parses as valid JavaScript.
- When the stored version differs, the script requests deletion of matching
  `vrenum` caches and stores the new version.
- When the stored version matches, it does not delete caches.
- The versioned i18n script and unrelated dashboard behavior remain unchanged.

## Verification

1. Render or extract the inline script with a representative `app_version` and
   check its syntax with Node.js or the project's browser test tooling.
2. Exercise both version-changed and version-unchanged branches with mocked
   `localStorage` and Cache Storage, or verify those behaviors in a browser.
3. Run any focused frontend/template tests available in the repository.
