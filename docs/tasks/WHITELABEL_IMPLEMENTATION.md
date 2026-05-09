# Whitelabel System Implementation Guide

**Task**: WL-01 through WL-08
**Status**: In Progress
**Started**: May 7, 2026
**Target**: 2-3 weeks

---

## Implementation Checklist

### Phase 1: Database & Models (WL-02)
- [ ] Create whitelabel tables migration
- [ ] Create WhitelabelDomain model
- [ ] Create WhitelabelBranding model
- [ ] Create WhitelabelEmailTemplate model

### Phase 2: Service Layer (WL-01)
- [ ] Implement WhitelabelService
- [ ] Domain validation
- [ ] DNS verification
- [ ] SSL certificate handling
- [ ] Branding storage

### Phase 3: API Layer (WL-03)
- [ ] Setup endpoint
- [ ] Config endpoint
- [ ] Branding update endpoint
- [ ] Domain verification endpoint

### Phase 4: Middleware (WL-04)
- [ ] Domain detection middleware
- [ ] Tenant resolution
- [ ] Branding injection
- [ ] CSS variable application

### Phase 5: Frontend (WL-05)
- [ ] Setup wizard UI
- [ ] Domain configuration
- [ ] Branding customization
- [ ] DNS verification instructions

### Phase 6: Email Templates (WL-06)
- [ ] Custom SMTP support
- [ ] Template variable system
- [ ] Fallback to platform SMTP

### Phase 7: Tier Gating (WL-07)
- [ ] Add whitelabel_enabled to tier config
- [ ] Enforce tier checks
- [ ] Upgrade prompts

### Phase 8: Testing (WL-08)
- [ ] E2E whitelabel flow
- [ ] Multi-tenant isolation
- [ ] SSL provisioning
- [ ] Load testing

---

## Architecture

```
Custom Domain Request (custom.example.com)
    ↓
Middleware: Detect Domain
    ↓
Query WhitelabelDomain by domain
    ↓
Load WhitelabelBranding for partner
    ↓
Inject CSS variables + logo
    ↓
Render with custom branding
```

---

## Database Schema

```sql
-- whitelabel_domains
CREATE TABLE whitelabel_domains (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    domain VARCHAR(255) NOT NULL UNIQUE,
    verified BOOLEAN DEFAULT FALSE,
    verification_token VARCHAR(255),
    verification_method VARCHAR(50), -- txt_record, meta_tag, file_upload
    ssl_status VARCHAR(50) DEFAULT 'pending', -- pending, active, failed
    ssl_expires_at TIMESTAMP,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- whitelabel_branding
CREATE TABLE whitelabel_branding (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) UNIQUE,
    logo_url VARCHAR(500),
    favicon_url VARCHAR(500),
    primary_color VARCHAR(7) DEFAULT '#667eea',
    secondary_color VARCHAR(7) DEFAULT '#764ba2',
    accent_color VARCHAR(7) DEFAULT '#f093fb',
    font_family VARCHAR(100) DEFAULT 'Inter',
    company_name VARCHAR(255),
    support_email VARCHAR(255),
    support_url VARCHAR(500),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- whitelabel_email_templates
CREATE TABLE whitelabel_email_templates (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    template_name VARCHAR(100) NOT NULL, -- welcome, verification, payment, etc.
    subject VARCHAR(255),
    html_content TEXT,
    text_content TEXT,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, template_name)
);

CREATE INDEX idx_whitelabel_domains_domain ON whitelabel_domains(domain);
CREATE INDEX idx_whitelabel_domains_user_id ON whitelabel_domains(user_id);
CREATE INDEX idx_whitelabel_branding_user_id ON whitelabel_branding(user_id);
```

---

## Domain Verification Methods

### Method 1: TXT Record (Recommended)
```
User adds TXT record to DNS:
_namaskah-verify.example.com TXT "verification_token_here"

We query DNS and verify token matches
```

### Method 2: Meta Tag
```html
User adds to their website:
<meta name="namaskah-verification" content="verification_token_here">

We fetch the page and check for meta tag
```

### Method 3: File Upload
```
User uploads file to:
https://example.com/.well-known/namaskah-verification.txt

We fetch the file and verify content
```

---

## SSL Certificate Provisioning

### Option A: Let's Encrypt (Automated)
```python
# Use certbot or acme.sh
# Requires DNS-01 or HTTP-01 challenge
# Auto-renew every 90 days
```

### Option B: Cloudflare Proxy (Recommended)
```
1. User adds domain to Cloudflare
2. Points CNAME to our server
3. Cloudflare handles SSL automatically
4. We verify via DNS TXT record
```

### Option C: User-Provided Certificate
```
User uploads:
- certificate.crt
- private.key
- ca_bundle.crt (optional)

We store securely and configure nginx
```

---

## Middleware Flow

```python
@app.middleware("http")
async def whitelabel_middleware(request: Request, call_next):
    # 1. Extract domain from request
    host = request.headers.get("host", "").split(":")[0]

    # 2. Check if custom domain
    if host != settings.base_domain:
        # 3. Query whitelabel_domains
        domain = db.query(WhitelabelDomain).filter(
            WhitelabelDomain.domain == host,
            WhitelabelDomain.verified == True,
            WhitelabelDomain.active == True
        ).first()

        if domain:
            # 4. Load branding
            branding = db.query(WhitelabelBranding).filter(
                WhitelabelBranding.user_id == domain.user_id
            ).first()

            # 5. Inject into request state
            request.state.whitelabel = {
                "enabled": True,
                "partner_id": domain.user_id,
                "branding": branding
            }

    # 6. Continue request
    response = await call_next(request)

    # 7. Inject CSS variables if whitelabel
    if hasattr(request.state, "whitelabel"):
        # Modify response to include custom CSS
        pass

    return response
```

---

## CSS Variable Injection

```html
<style>
:root {
    --primary-color: {{ branding.primary_color }};
    --secondary-color: {{ branding.secondary_color }};
    --accent-color: {{ branding.accent_color }};
    --font-family: {{ branding.font_family }};
}

.logo {
    background-image: url('{{ branding.logo_url }}');
}
</style>
```

---

## API Endpoints

```python
POST   /api/whitelabel/setup          # Initialize whitelabel
GET    /api/whitelabel/config         # Get current config
PUT    /api/whitelabel/branding       # Update branding
POST   /api/whitelabel/verify-domain  # Trigger DNS verification
DELETE /api/whitelabel/domain/{id}    # Remove domain
GET    /api/whitelabel/domains        # List domains
POST   /api/whitelabel/email-template # Create/update email template
GET    /api/whitelabel/email-templates # List email templates
```

---

## Security Considerations

1. **Tenant Isolation**: Ensure queries filter by partner_id
2. **Domain Validation**: Prevent subdomain takeover
3. **SSL Verification**: Validate certificates before use
4. **Rate Limiting**: Prevent abuse of verification endpoints
5. **Data Privacy**: Isolate partner data completely

---

## Testing Plan

1. **Unit Tests** (Target: 90%)
   - Domain validation
   - DNS verification
   - Branding injection
   - Tenant isolation

2. **Integration Tests**
   - Setup flow
   - Domain verification
   - Branding application
   - Email templates

3. **E2E Tests**
   - User sets up whitelabel
   - Domain verified
   - Custom branding applied
   - Multi-tenant isolation verified

4. **Load Testing**
   - Multiple tenants simultaneously
   - DNS verification under load
   - Branding injection performance

---

## Rollback Plan

If issues arise:
1. Disable whitelabel middleware
2. Return 404 on custom domains
3. Users revert to main domain
4. No data loss (tables remain)

---

## Cost Estimates

**Infrastructure:**
- SSL certificates: $0 (Let's Encrypt free)
- DNS queries: ~$0.01/month per domain
- Storage: Negligible

**Expected Costs:**
- 10 whitelabel users: ~$0.10/month
- 100 whitelabel users: ~$1/month

---

## Revenue Potential

**Pricing:**
- Pro tier ($25/mo): 1 custom domain included
- Custom tier ($35/mo): Unlimited domains

**Expected Revenue:**
- 5 Pro users with whitelabel: $125/month
- 10 Custom users: $350/month
- Total: $475/month additional revenue

---

## Next Actions

1. Create database migration
2. Implement WhitelabelService
3. Create API endpoints
4. Build middleware
5. Create setup wizard UI
6. Test multi-tenant isolation

**Estimated Time**: 12-16 hours of development
