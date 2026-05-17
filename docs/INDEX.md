# Namaskah Documentation Index

**Version**: 4.7.1
**Last Updated**: May 17, 2026
**Total Documents**: ~40 (consolidated from 104)

---

## 📚 Quick Navigation

### 🎯 Start Here
- **[Platform Assessment](./PLATFORM_ASSESSMENT.md)** - System overview and status
- **[Platform Assessment (Detailed)](./PLATFORM_ASSESSMENT_DETAILED.md)** - Deep technical analysis
- **[Strict Refund Policy](./STRICT_REFUND_POLICY.md)** - Business policy

### 🚀 Recent Implementations
- **[Error Tracking Complete](./ERROR_TRACKING_COMPLETE.md)** - Error tracking system (v4.7.2)
- **[Voice UI Complete](./VOICE_UI_COMPLETE.md)** - Voice verification system
- **[Whitelabel Complete](./WHITELABEL_COMPLETE.md)** - Partner whitelabel system
- **[Area Code Implementation](./tasks/AREA_CODE_IMPLEMENTATION.md)** - Tier-gated area code selection

### 🧪 Testing & Verification
- **[TextVerified Area Code Test Guide](./TEXTVERIFIED_AREA_CODE_TEST_GUIDE.md)** - Provider testing
- **[UI/UX Assessment](./UI_UX_ASSESSMENT.md)** - Interface evaluation

---

## 📂 Documentation by Category

### Business & Strategy
**Location**: `/docs/business/`
- [Essential Startup Brief](./business/ESSENTIAL_STARTUP_BRIEF.md) - Business overview
- [Pricing & ROI](./business/PRICING_INVENTORY_ROI.md) - Revenue model
- [Project Vision](./business/PROJECT_VISION.md) - Long-term goals

### Engineering

#### API Documentation
**Location**: `/docs/engineering/api/`
- [API Guide](./engineering/api/API_GUIDE.md) - Complete API reference
- [API v2 Spec](./engineering/api/api_v2_spec.yaml) - OpenAPI specification
- [Tier Management API](./engineering/api/TIER_MANAGEMENT_API.md) - Subscription tiers
- [Voice vs SMS](./engineering/api/VOICE_VS_SMS_VERIFICATION.md) - Capability comparison

#### Development
**Location**: `/docs/engineering/development/`
- [Accessibility Checklist](./engineering/development/ACCESSIBILITY_CHECKLIST.md) - WCAG compliance
- [I18N Guide](./engineering/development/I18N_GUIDE.md) - Internationalization

### Features
**Location**: `/docs/features/`
- [Advanced Analytics](./features/ADVANCED_ANALYTICS_CUSTOM_REPORTS.md) - Custom reports
- [Billing History](./features/BILLING_HISTORY.md) - Transaction history
- [GDPR Compliance](./features/COMPLIANCE_GDPR_CHECKER.md) - Data privacy
- [Disputes](./features/DISPUTES_COMMENTS_ATTACHMENTS.md) - Dispute management
- [KYC Viewer](./features/KYC_DOCUMENT_VIEWER.md) - Document verification
- [Usage Quotas](./features/USAGE_QUOTAS.md) - Rate limiting
- [Activity Timeline](./features/USER_MANAGEMENT_ACTIVITY_TIMELINE.md) - User activity

### Knowledge Base
**Location**: `/docs/knowledge/`
- [Business Logic](./knowledge/BUSINESS_LOGIC.md) - Core business rules
- [Refund Logic](./knowledge/REFUND_LOGIC_VERIFIED.md) - Refund processing
- [SMS Logic](./knowledge/SMS_LOGIC.md) - SMS verification flow

### Operations

#### Deployment & Infrastructure
**Location**: `/docs/operations/`
- [DigitalOcean Deployment](./operations/DIGITALOCEAN_DEPLOYMENT.md) - Cloud deployment
- [Monitoring](./operations/MONITORING.md) - System monitoring
- [Production Migration](./operations/PRODUCTION_MIGRATION_GUIDE.md) - Migration guide
- [Runbook](./operations/RUNBOOK.md) - Operational procedures

#### Security
**Location**: `/docs/operations/security/`
- [Security & Compliance](./operations/security/SECURITY_AND_COMPLIANCE.md) - Security practices

### Tasks & Roadmap
**Location**: `/docs/tasks/`
- [Area Code Implementation](./tasks/AREA_CODE_IMPLEMENTATION.md) - ✅ Complete
- [Phase 5: Admin Intelligence](./tasks/PHASE_5_ADMIN_INTELLIGENCE.md) - ✅ Complete
- [Phase 6: Platform Hardening](./tasks/PHASE_6_PLATFORM_HARDENING.md) - ✅ Complete
- [Push Notifications](./tasks/PUSH_NOTIFICATIONS_IMPLEMENTATION.md) - 📋 Planned
- [Telegram Integration](./tasks/TELEGRAM_IMPLEMENTATION.md) - 📋 Planned
- [Whitelabel](./tasks/WHITELABEL_IMPLEMENTATION.md) - ✅ Complete

---

## 📦 Archive

Historical implementation documents are archived for reference:

**Location**: `/docs/archive/`
- `area-code-implementation/` - Area code feature history
- `error-tracking-implementation/` - Error tracking implementation
- `voice-ui-implementation/` - Voice UI development
- `whitelabel-implementation/` - Whitelabel system development
- `changes/` - Historical change logs
- `milestones/` - Project milestones
- `sessions/` - Development session notes
- `misc/` - Miscellaneous archived docs

---

## 🔍 Finding Documentation

### By Topic
- **Authentication**: See [API Guide](./engineering/api/API_GUIDE.md)
- **Payments**: See [Business Logic](./knowledge/BUSINESS_LOGIC.md)
- **Refunds**: See [Refund Logic](./knowledge/REFUND_LOGIC_VERIFIED.md) + [Strict Policy](./STRICT_REFUND_POLICY.md)
- **SMS/Voice**: See [SMS Logic](./knowledge/SMS_LOGIC.md) + [Voice vs SMS](./engineering/api/VOICE_VS_SMS_VERIFICATION.md)
- **Tiers**: See [Tier Management API](./engineering/api/TIER_MANAGEMENT_API.md)
- **Monitoring**: See [Monitoring](./operations/MONITORING.md) + [Runbook](./operations/RUNBOOK.md)
- **Security**: See [Security & Compliance](./operations/security/SECURITY_AND_COMPLIANCE.md)

### By Status
- **✅ Complete**: Error Tracking, Voice UI, Whitelabel, Area Code, Phase 5, Phase 6
- **📋 Planned**: Push Notifications, Telegram Integration
- **🔄 Ongoing**: Monitoring, Security, Documentation

---

## 📝 Documentation Standards

### File Naming
- Use SCREAMING_SNAKE_CASE for docs
- Be descriptive: `FEATURE_NAME_COMPLETE.md`
- Avoid version numbers in filenames

### Document Structure
```markdown
# Title

**Version**: X.X.X
**Status**: ✅/📋/🔄
**Last Updated**: Date

## Overview
Brief description

## Implementation
Technical details

## Testing
Test results

## Reference
Links and resources
```

### Status Indicators
- ✅ Complete and deployed
- 📋 Planned/In progress
- 🔄 Ongoing/Maintenance
- ⚠️ Needs attention
- ❌ Deprecated/Archived

---

## 🤝 Contributing

### Adding New Documentation
1. Create doc in appropriate folder
2. Follow naming conventions
3. Use standard structure
4. Update this INDEX
5. Link from related docs

### Updating Existing Documentation
1. Update "Last Updated" date
2. Maintain version history
3. Archive old versions if major changes
4. Update cross-references

### Archiving Documentation
1. Move to `/docs/archive/[category]/`
2. Create summary doc if consolidating
3. Update INDEX to remove entry
4. Add redirect note in old location

---

## 📞 Support

**Questions about documentation?**
- Check this INDEX first
- Search in relevant category folder
- Check archive for historical context
- Create GitHub issue if doc is missing

---

**Last Consolidated**: May 17, 2026
**Consolidation**: Reduced from 104 to ~40 documents (60% reduction)
