# Namaskah SMS Verification Platform

**Version**: 3.0.0 - Tiered SaaS Platform 🚀  
**Status**: Production Ready with Versioning  
**Last Updated**: 2025-12-07

---

## 🎯 Choose Your Plan

Namaskah offers **4 tiers** designed for different use cases:

| Feature | Pay-As-You-Go (Trial) | Starter | Pro | Custom |
|---------|----------------------|---------|-----|--------|
| **Price** | $0/mo | $8.99/mo | $25/mo | $35/mo |
| **Included Quota** | None | $10 (~4 SMS) | $30 (~12 SMS) | $50 (~20 SMS) |
| **Per SMS** | $2.50 | Included, then +$0.50 | Included, then +$0.30 | Included, then +$0.20 |
| **API Access** | ❌ | ✅ 5 keys | ✅ 10 keys | ✅ Unlimited |
| **Area Code Selection** | ❌ | ✅ | ✅ | ✅ |
| **ISP/Carrier Filter** | ❌ | ❌ | ✅ | ✅ |
| **Countries** | All 50+ | All 50+ | All 50+ | All 50+ |
| **Support** | Community | Email | Priority | Dedicated |

**Subscription Benefits**: 
- ✅ **Included quota** resets monthly
- ✅ **Lower overage rates** - Fixed increase ($0.20-$0.50) vs $2.50 per SMS
- ✅ **API access** for automation
- ✅ **No interruption** when quota exhausted

---

## 🚀 Quick Start

```bash
# Clone and setup
git clone https://github.com/yourusername/namaskah-sms.git
cd namaskah-sms

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Run the application
./start.sh
# or
uvicorn main:app --host 127.0.0.1 --port 8000
```

**Open**: `http://localhost:8000`

---

## ✨ Key Features

### 🔐 Multi-Tier Access
- **Pay-As-You-Go (Trial)**: Test unlimited at $2.50/SMS, no commitment
- **Starter**: $8.99/mo with quota, then +$0.50/SMS overage
- **Pro**: $25/mo with larger quota, then +$0.30/SMS overage
- **Custom**: $35/mo with premium quota, then +$0.20/SMS overage

### 📱 SMS Verification
- Instant SMS verification codes
- 50+ countries supported
- Multiple services (Telegram, WhatsApp, etc.)
- Real-time status tracking

### 🔑 API Key Management
- Generate secure API keys
- Usage tracking and analytics
- Tier-based rate limiting
- Easy key rotation

### 💳 Flexible Billing
- Credit-based system
- Bonus credits on purchases
- Multiple payment methods
- Transparent pricing

### 🛡️ Enterprise Security
- OWASP Top 10 compliant
- JWT authentication
- CSRF protection
- Rate limiting
- Secure logging

---

## 🔌 API Endpoints

### Authentication
- `POST /api/auth/register` - Create account
- `POST /api/auth/login` - Login
- `POST /api/auth/refresh` - Refresh token
- `POST /api/auth/logout` - Logout

### SMS Verification
- `POST /api/verify/create` - Purchase verification
- `GET /api/verify/status/{id}` - Check SMS status
- `GET /api/verify/{id}/messages` - Get messages

### API Keys 🆕
- `GET /api/keys` - List your API keys
- `POST /api/keys/generate` - Generate new key
- `DELETE /api/keys/{id}` - Revoke key
- `GET /api/keys/{id}/usage` - Usage stats

### Countries & Services
- `GET /api/countries/` - List countries
- `GET /api/countries/{country}/services` - Get services

### Billing
- `POST /api/billing/add-credits` - Add credits
- `GET /api/billing/balance` - Get balance
- `GET /api/billing/history` - Payment history

### Tiers 🆕
- `GET /api/tiers` - List available tiers
- `GET /api/user/tier` - Get current tier
- `POST /api/user/tier/upgrade` - Upgrade tier

---

## 📊 Configuration

```bash
# .env file required
SECRET_KEY=your-32-char-secret-key
JWT_SECRET_KEY=your-32-char-jwt-secret
DATABASE_URL=postgresql://user:pass@host:port/db
SMS_PROVIDER_API_KEY=your-textverified-api-key

# Optional: Payment integration
STRIPE_SECRET_KEY=your-stripe-key
PAYPAL_CLIENT_ID=your-paypal-id
```

---

## 🗂️ Project Structure

```
app/
├── api/              # API endpoints by domain
│   ├── admin/        # Admin dashboard
│   ├── billing/      # Payment & tiers
│   ├── core/         # Auth, countries, services
│   ├── verification/ # SMS verification
│   └── ...
├── core/             # Core functionality
│   ├── config.py     # Configuration
│   ├── database.py   # Database setup
│   └── ...
├── middleware/       # Security middleware
├── models/           # Database models
├── schemas/          # API schemas
└── services/         # Business logic

templates/            # HTML templates
static/               # CSS, JS, images
docs/                 # Documentation
scripts/              # Utility scripts
```

---

## 🗄️ Database Setup

```bash
# Create tables
python3 fix_missing_tables.py

# Run migrations
alembic upgrade head

# Migrate users to tiers (for existing installations)
python3 scripts/migrate_users_to_tiers.py
```

---

## 🧪 Testing

```bash
# Run all tests
pytest

# With coverage
pytest --cov=app --cov-report=html

# Specific test file
pytest tests/test_api/test_tier_endpoints.py -v

# Health check
curl http://localhost:8000/api/system/health
```

---

## 📚 Enterprise Documentation

- [Enterprise Roadmap](docs/ENTERPRISE_ROADMAP.md) - Strategic phases for scaling.
- [Implementation Guide](docs/NEXT_PHASES_IMPLEMENTATION.md) - Immediate next steps for developers.
- [API Documentation](docs/TIER_API_DOCUMENTATION.md)
- [Tier Deployment Guide](docs/TIER_DEPLOYMENT_GUIDE.md)
- **[Security](./docs/SECURITY_AND_COMPLIANCE.md)** - Security details

---

## 🔒 Security Features

- ✅ OWASP Top 10 compliant
- ✅ Input sanitization (XSS prevention)
- ✅ SQL injection protection
- ✅ CSRF token protection
- ✅ Rate limiting (tier-based)
- ✅ JWT authentication
- ✅ API key security (hashed storage)
- ✅ Secure logging (no sensitive data)

---

## 🚢 Deployment

### Docker
```bash
# Development
docker-compose up

# Production
docker-compose -f docker-compose.prod.yml up -d
```

### Kubernetes
```bash
kubectl apply -f k8s-deployment.yaml
```

### Manual
```bash
# Install dependencies
pip install -r requirements.txt

# Run with gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker
```

---

## 🤝 Support

- **Community**: GitHub Discussions
- **Email**: support@namaskah.com (Starter+)
- **Priority**: Dedicated Slack (Turbo)
- **Documentation**: https://docs.namaskah.com

---

## 📈 Roadmap

### Q1 2026
- ✅ Tier system launch
- ✅ API key management
- 🔄 SDK libraries (Python, JS, Go)
- 🔄 Webhook builder

### Q2 2026
- Geographic targeting
- Device type filtering
- Referral program
- Volume discounts

### Q3 2026
- Enterprise tier
- Team management
- SSO integration
- White-label options

[**Full Roadmap →**](./docs/ROADMAP.md)

---

## 🛠️ Built With

- **FastAPI** - Modern Python web framework
- **SQLAlchemy** - Python SQL toolkit
- **PostgreSQL** - Primary database
- **Redis** - Caching layer
- **TextVerified** - SMS provider
- **JWT** - Authentication
- **Docker** - Containerization
- **Kubernetes** - Orchestration

---

## 📝 License

MIT License - See [LICENSE](./LICENSE) file

---

## 🙏 Acknowledgments

- TextVerified for SMS services
- FastAPI community
- All contributors

---

**Ready to verify? Sign up for free at [namaskah.com](https://namaskah.com)** 🚀

