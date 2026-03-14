# Namaskah SMS Verification Platform

**Version**: 4.4.0 - Carrier & Area Code Alignment 🚀  
**Status**: Production Ready  
**Last Updated**: March 15, 2026

![Build Status](https://img.shields.io/github/actions/workflow/status/yourusername/namaskah-sms/ci.yml?branch=main)
![Coverage](https://img.shields.io/codecov/c/github/yourusername/namaskah-sms)
![Python Version](https://img.shields.io/badge/python-3.11-blue)

---

## 🏗️ Architecture Overview

Namaskah follows a **Modular Monolith** architecture pattern, providing the benefits of microservices organization while maintaining the simplicity of a monolithic deployment.

```mermaid
graph TB
    subgraph "Client Layer"
        WEB[Web Browser]
        API_CLIENT[API Clients]
    end
    
    subgraph "API Gateway"
        MAIN[main.py<br/>FastAPI Application]
    end
    
    subgraph "Domain Routers"
        AUTH[Auth Router<br/>Login, Register, OAuth]
        WALLET[Wallet Router<br/>Payments, Balance]
        SMS[SMS Router<br/>Verification, Messages]
        TIER[Tier Router<br/>Plans, Upgrades]
        ADMIN[Admin Router<br/>User Management]
    end
    
    subgraph "Business Services"
        AUTH_SVC[Auth Service]
        PAYMENT_SVC[Payment Service]
        SMS_SVC[SMS Service]
        TIER_SVC[Tier Service]
        WEBHOOK_SVC[Webhook Service]
    end
    
    subgraph "Data Layer"
        DB[(PostgreSQL<br/>Database)]
        CACHE[(Redis<br/>Cache)]
    end
    
    subgraph "External Services"
        TEXTVERIFIED[TextVerified<br/>SMS Provider]
        PAYSTACK[Paystack<br/>Payments]
    end
    
    WEB --> MAIN
    API_CLIENT --> MAIN
    
    MAIN --> AUTH
    MAIN --> WALLET
    MAIN --> SMS
    MAIN --> TIER
    MAIN --> ADMIN
    
    AUTH --> AUTH_SVC
    WALLET --> PAYMENT_SVC
    WALLET --> WEBHOOK_SVC
    SMS --> SMS_SVC
    TIER --> TIER_SVC
    
    AUTH_SVC --> DB
    PAYMENT_SVC --> DB
    SMS_SVC --> DB
    TIER_SVC --> DB
    
    AUTH_SVC --> CACHE
    SMS_SVC --> CACHE
    
    SMS_SVC --> TEXTVERIFIED
    PAYMENT_SVC --> PAYSTACK
    WEBHOOK_SVC --> PAYSTACK
    
    style MAIN fill:#4CAF50
    style DB fill:#2196F3
    style CACHE fill:#FF9800
```

---

## 🎯 Modular Monolith Benefits

### ✅ Advantages
- **Clear Boundaries**: Each domain has its own router and service layer
- **Easy Testing**: Modules can be tested independently
- **Simple Deployment**: Single application, no orchestration needed
- **Shared Resources**: Efficient database connection pooling
- **Gradual Migration**: Can extract to microservices later if needed

### 📦 Module Structure

```
app/
├── api/                    # API Layer (Routers)
│   ├── core/              # Core domain routers
│   │   ├── auth.py        # Authentication & Authorization
│   │   ├── wallet.py      # Wallet & Payments
│   │   ├── countries.py   # Country & Service listings
│   │   └── verification.py # SMS Verification
│   ├── admin/             # Admin domain
│   │   ├── admin.py       # User management
│   │   ├── kyc.py         # KYC verification
│   │   └── support.py     # Support tickets
│   └── billing/           # Billing domain
│       └── tiers.py       # Tier management
│
├── services/              # Business Logic Layer
│   ├── auth_service.py    # Auth business logic
│   ├── payment_service.py # Payment processing
│   ├── sms_service.py     # SMS verification logic
│   ├── tier_service.py    # Tier calculations
│   └── webhook_service.py # Webhook handling
│
├── models/                # Data Layer
│   ├── user.py           # User model
│   ├── transaction.py    # Transaction model
│   ├── verification.py   # Verification model
│   └── subscription_tier.py # Tier model
│
├── core/                  # Shared Infrastructure
│   ├── database.py       # Database connection
│   ├── cache.py          # Redis cache
│   ├── config.py         # Configuration
│   └── dependencies.py   # Shared dependencies
│
└── middleware/            # Cross-cutting Concerns
    ├── auth.py           # Auth middleware
    ├── rate_limiting.py  # Rate limiting
    └── logging.py        # Request logging
```

---

## 🔄 Request Flow

```mermaid
sequenceDiagram
    participant Client
    participant Router
    participant Service
    participant Database
    participant External
    
    Client->>Router: HTTP Request
    Router->>Router: Validate Input
    Router->>Service: Call Business Logic
    Service->>Database: Query/Update Data
    Database-->>Service: Return Data
    Service->>External: Call External API (if needed)
    External-->>Service: Return Response
    Service->>Service: Process Business Rules
    Service-->>Router: Return Result
    Router->>Router: Format Response
    Router-->>Client: HTTP Response
```

---

## 💳 Payment Flow

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant Wallet API
    participant Payment Service
    participant Paystack
    participant Webhook
    participant Database
    
    User->>Frontend: Click "Add Credits"
    Frontend->>Wallet API: POST /wallet/paystack/initialize
    Wallet API->>Payment Service: initialize_payment()
    Payment Service->>Paystack: Create Transaction
    Paystack-->>Payment Service: Authorization URL
    Payment Service-->>Wallet API: Return URL
    Wallet API-->>Frontend: Return URL
    Frontend->>User: Redirect to Paystack
    User->>Paystack: Complete Payment
    Paystack->>Webhook: POST /wallet/paystack/webhook
    Webhook->>Payment Service: process_webhook()
    Payment Service->>Database: Update User Credits
    Payment Service->>Database: Record Transaction
    Database-->>Payment Service: Success
    Payment Service-->>Webhook: Success
    Webhook-->>Paystack: 200 OK
    Paystack->>User: Redirect to Success Page
```

---

## 📱 SMS Verification Flow

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant SMS API
    participant SMS Service
    participant Database
    participant TextVerified
    participant Polling Service
    
    User->>Frontend: Request Verification
    Frontend->>SMS API: POST /verify/create
    SMS API->>SMS Service: create_verification()
    SMS Service->>Database: Check User Balance
    Database-->>SMS Service: Balance OK
    SMS Service->>TextVerified: Purchase Number
    TextVerified-->>SMS Service: Phone Number
    SMS Service->>Database: Save Verification
    SMS Service-->>SMS API: Return Details
    SMS API-->>Frontend: Show Phone Number
    Frontend-->>User: Display Number
    
    Note over Polling Service: Background Process
    Polling Service->>TextVerified: Check for Messages
    TextVerified-->>Polling Service: SMS Code
    Polling Service->>Database: Update Verification
    
    User->>Frontend: Check Status
    Frontend->>SMS API: GET /verify/status/{id}
    SMS API->>Database: Query Verification
    Database-->>SMS API: Return Status
    SMS API-->>Frontend: Return Messages
    Frontend-->>User: Display Code
```

---

## 🎯 Tier System

```mermaid
graph LR
    subgraph "Tier Hierarchy"
        FREEMIUM[Freemium<br/>$0/mo<br/>$2.22/SMS]
        PAYG[Pay-As-You-Go<br/>$0/mo<br/>$2.50/SMS]
        PRO[Pro<br/>$25/mo<br/>$15 quota]
        CUSTOM[Custom<br/>$35/mo<br/>$25 quota]
    end
    
    subgraph "Features"
        API[API Access]
        FILTERS[Location/ISP Filters]
        AFFILIATE[Affiliate Program]
        SUPPORT[Priority Support]
    end
    
    FREEMIUM -.->|Upgrade| PAYG
    PAYG -.->|Upgrade| PRO
    PRO -.->|Upgrade| CUSTOM
    
    PRO --> API
    CUSTOM --> API
    
    PAYG --> FILTERS
    PRO --> FILTERS
    CUSTOM --> FILTERS
    
    PRO --> AFFILIATE
    CUSTOM --> AFFILIATE
    
    PRO --> SUPPORT
    CUSTOM --> SUPPORT
    
    style FREEMIUM fill:#90CAF9
    style PAYG fill:#81C784
    style PRO fill:#FFB74D
    style CUSTOM fill:#E57373
```

### Tier Comparison

| Feature | Freemium | Pay-As-You-Go | Pro | Custom |
|---------|----------|---------------|-----|--------|
| **Price** | $0/mo | $0/mo | $25/mo | $35/mo |
| **SMS Rate** | $2.22/SMS | $2.50/SMS | $0.30 overage | $0.20 overage |
| **Monthly Quota** | None | None | $15 | $25 |
| **API Access** | ❌ | ❌ | ✅ 10 keys | ✅ Unlimited |
| **Location Filters** | ❌ | ✅ +$0.25 | ✅ Included | ✅ Included |
| **ISP Filters** | ❌ | ✅ +$0.50 | ✅ Included | ✅ Included |
| **Affiliate Program** | ❌ | ❌ | ✅ Standard | ✅ Enhanced |
| **Support** | Community | Community | Priority | Dedicated |

---

## 🚀 Quick Start

### Prerequisites
```bash
# Required
Python 3.9+
PostgreSQL 13+
Redis 6+

# Optional
Docker & Docker Compose
Node.js 18+ (for frontend build)
```

### Installation

```bash
# 1. Clone repository
git clone https://github.com/yourusername/namaskah-sms.git
cd namaskah-sms

# 2. Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Setup environment
cp .env.example .env
# Edit .env with your configuration

# 5. Initialize database
python scripts/fix_production_schema.py

# 6. Run application
./start.sh
# or
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

**Open**: `http://localhost:8000`

---

## 🔌 API Endpoints

### Authentication
```http
POST   /api/auth/register          # Create account
POST   /api/auth/login             # Login
POST   /api/auth/refresh           # Refresh token
POST   /api/auth/logout            # Logout
GET    /api/auth/me                # Get current user
POST   /api/auth/google            # Google OAuth
```

### Wallet & Payments
```http
GET    /api/wallet/balance         # Get balance
POST   /api/wallet/paystack/initialize  # Initialize payment
POST   /api/wallet/paystack/verify      # Verify payment
POST   /api/wallet/paystack/webhook     # Payment webhook
GET    /api/wallet/transactions    # Transaction history
GET    /api/wallet/transactions/export  # Export transactions
```

### SMS Verification
```http
POST   /api/verify/create          # Create verification
GET    /api/verify/status/{id}     # Check status
GET    /api/verify/{id}/messages   # Get messages
GET    /api/verify/history         # Verification history
```

### Tiers
```http
GET    /api/tiers                  # List tiers
GET    /api/tiers/current          # Current tier
POST   /api/tiers/upgrade          # Upgrade tier
POST   /api/tiers/downgrade        # Downgrade tier
```

### API Keys (Pro+)
```http
GET    /api/keys                   # List API keys
POST   /api/keys/generate          # Generate key
DELETE /api/keys/{id}              # Revoke key
GET    /api/keys/{id}/usage        # Usage stats
```

### Countries & Services
```http
GET    /api/countries              # List countries
GET    /api/countries/{code}/services  # Get services
GET    /api/services               # List all services
```

---

## 🧪 Testing

### Run Tests
```bash
# All tests
pytest

# With coverage
pytest --cov=app --cov-report=html

# Specific module
pytest tests/unit/test_wallet_service.py -v

# Frontend tests
npm run test:e2e
```

### Test Structure
```
tests/
├── unit/                  # Unit tests (95% coverage target)
│   ├── test_wallet_service.py
│   ├── test_payment_service.py
│   ├── test_sms_service.py
│   └── test_tier_calculations.py
├── integration/           # Integration tests (85% coverage)
│   ├── test_wallet_api.py
│   ├── test_payment_flow.py
│   └── test_verification_flow.py
├── frontend/              # Frontend tests (70% coverage)
│   ├── test_login_page.spec.js
│   ├── test_dashboard.spec.js
│   └── test_verification_flow.spec.js
└── e2e/                   # End-to-end tests
    └── test_user_journeys.py
```

### Coverage Report
```bash
# Generate HTML coverage report
pytest --cov=app --cov-report=html
open htmlcov/index.html

# Current coverage: 81.48%
# Target coverage: 90%+
```

---

## 📊 Monitoring & Observability

```mermaid
graph TB
    subgraph "Application"
        APP[Namaskah App]
    end
    
    subgraph "Logging"
        LOGS[Application Logs]
        AUDIT[Audit Logs]
    end
    
    subgraph "Monitoring"
        SENTRY[Sentry<br/>Error Tracking]
        METRICS[Prometheus<br/>Metrics]
    end
    
    subgraph "Alerting"
        ALERTS[Alert Manager]
        SLACK[Slack Notifications]
    end
    
    APP --> LOGS
    APP --> AUDIT
    APP --> SENTRY
    APP --> METRICS
    
    SENTRY --> ALERTS
    METRICS --> ALERTS
    
    ALERTS --> SLACK
    
    style APP fill:#4CAF50
    style SENTRY fill:#FF5722
    style METRICS fill:#2196F3
```

---

## 🔒 Security Features

### OWASP Top 10 Compliance
- ✅ **A01: Broken Access Control** - Role-based access control (RBAC)
- ✅ **A02: Cryptographic Failures** - Bcrypt password hashing, JWT tokens
- ✅ **A03: Injection** - SQLAlchemy ORM, parameterized queries
- ✅ **A04: Insecure Design** - Secure by design architecture
- ✅ **A05: Security Misconfiguration** - Environment-based config
- ✅ **A06: Vulnerable Components** - Regular dependency updates
- ✅ **A07: Authentication Failures** - JWT + OAuth2, rate limiting
- ✅ **A08: Software Integrity** - Code signing, dependency verification
- ✅ **A09: Logging Failures** - Comprehensive audit logging
- ✅ **A10: SSRF** - Input validation, URL whitelisting

### Security Layers
```mermaid
graph TB
    subgraph "Defense in Depth"
        WAF[Web Application Firewall]
        RATE[Rate Limiting]
        AUTH[Authentication]
        AUTHZ[Authorization]
        INPUT[Input Validation]
        OUTPUT[Output Encoding]
        AUDIT[Audit Logging]
    end
    
    REQUEST[HTTP Request] --> WAF
    WAF --> RATE
    RATE --> AUTH
    AUTH --> AUTHZ
    AUTHZ --> INPUT
    INPUT --> OUTPUT
    OUTPUT --> AUDIT
    AUDIT --> RESPONSE[HTTP Response]
    
    style WAF fill:#F44336
    style AUTH fill:#FF9800
    style AUTHZ fill:#FFC107
    style INPUT fill:#4CAF50
```

---

## 🚢 Deployment

### Docker Compose (Recommended)
```bash
# Development
docker-compose up

# Production
docker-compose -f docker-compose.production.yml up -d
```

### Kubernetes
```bash
# Apply configuration
kubectl apply -f k8s-deployment.yaml

# Check status
kubectl get pods -l app=namaskah-sms

# View logs
kubectl logs -f deployment/namaskah-sms
```

### Manual Deployment
```bash
# Install dependencies
pip install -r requirements.txt

# Run with Gunicorn
gunicorn main:app \
  -w 4 \
  -k uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile - \
  --error-logfile -
```

### Render.com (Current Production)
```yaml
# render.yaml
services:
  - type: web
    name: namaskah-sms
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn main:app --host 0.0.0.0 --port $PORT --workers 2
    envVars:
      - key: DATABASE_URL
      - key: SECRET_KEY
      - key: JWT_SECRET_KEY
```

---

## 📚 Documentation

### 🚀 Getting Started
- **[SETUP.md](./SETUP.md)** - Complete setup and deployment guide
- **[CHANGELOG.md](./CHANGELOG.md)** - Version history and releases

### 🎯 Carrier & Area Code Alignment
- **[docs/fixes/CARRIER_LOOKUP_IMPLEMENTATION.md](./docs/fixes/CARRIER_LOOKUP_IMPLEMENTATION.md)** - Carrier lookup system (Phase 1-4)
- **[docs/fixes/TEXTVERIFIED_CARRIER_IMPLEMENTATION.md](./docs/fixes/TEXTVERIFIED_CARRIER_IMPLEMENTATION.md)** - 7 issues fixed, 8 features, 10 manual tests
- **[docs/tasks/CARRIER_LOOKUP_STRATEGY.md](./docs/tasks/CARRIER_LOOKUP_STRATEGY.md)** - Google libphonenumber recommendation
- **[docs/tasks/TEXTVERIFIED_ALIGNMENT_ROADMAP.md](./docs/tasks/TEXTVERIFIED_ALIGNMENT_ROADMAP.md)** - 5 milestones, 15 tasks

### 📋 Reference
- **[DOCUMENTATION_ORGANIZATION.md](./DOCUMENTATION_ORGANIZATION.md)** - Documentation structure guide
- **[CLEANUP_COMPLETE.md](./CLEANUP_COMPLETE.md)** - Archive organization summary

---

## 🛣️ Roadmap

### Completed Phases ✅

See [CHANGELOG.md](./CHANGELOG.md) for detailed features of completed phases:

- **Phase 1** (Dec 2025): Foundation & Infrastructure
- **Phase 2** (Jan 2026): Core Platform Features  
- **Phase 2.5** (Jan 26, 2026): Notification System (300x faster delivery, 100+ test cases)
- **Phase 3** (Mar 9, 2026): Production Excellence
- **Milestone 1** (Mar 14, 2026): TextVerified Alignment - Stop the Bleeding
- **Milestone 2** (Mar 14, 2026): Data Integrity
- **Milestone 3** (Mar 15, 2026): Carrier & Area Code Alignment

### Current & Upcoming

### Q2 2026 - Carrier Enhancement 🔄
- 🔄 **Google libphonenumber** (Phase 2 - offline phone validation)
- 🔄 **Enhanced analytics** (carrier success rates, preferences)
- 🔄 **SDK libraries** (Python, JavaScript, Go)

### Q3 2026 - Carrier Guarantee 📋
- 📋 **Numverify API** (Phase 3 - real carrier lookup)
- 📋 **Premium tier** (Carrier Guarantee feature)
- 📋 **Multi-region deployment**

### Q4 2026 - Excellence 📋
- 📋 **Commercial APIs** (if volume justifies)
- 📋 **Enterprise tier**
- 📋 **Advanced reporting**

---

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md).

### Development Setup
```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Run linters
black app/
flake8 app/
mypy app/

# Run tests
pytest
```

---

## 📄 License

MIT License - See [LICENSE](./LICENSE) file

---

## 🙏 Acknowledgments

- **FastAPI** - Modern Python web framework
- **SQLAlchemy** - Python SQL toolkit
- **TextVerified** - SMS provider
- **Paystack** - Payment processing
- **Render.com** - Hosting platform

---

## 📞 Support

- **Community**: [GitHub Discussions](https://github.com/yourusername/namaskah-sms/discussions)
- **Email**: support@namaskah.app
- **Documentation**: https://docs.namaskah.app
- **Status Page**: https://status.namaskah.app

---

**Built with ❤️ by the Namaskah Team**

**Ready to verify? [Get Started →](https://namaskah.app)**
