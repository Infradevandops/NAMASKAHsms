# Namaskah SMS Verification Platform

**Version**: 4.0.0 - Freemium SaaS Platform 🚀  
**Status**: Production Ready with Freemium Model  
**Last Updated**: 2025-12-25

---

## 🎯 Choose Your Plan

Namaskah offers **4 tiers** designed for different use cases:

| Feature | Freemium | Pay-As-You-Go | Pro | Custom |
|---------|----------|---------------|-----|--------|
| **Price** | $0/mo | $0/mo | $25/mo | $35/mo |
| **SMS Rate** | $2.22/SMS (9 per $20) | $2.50/SMS | $15 quota + $0.30 overage | $25 quota + $0.20 overage |
| **API Access** | ❌ | ❌ | ✅ 10 keys | ✅ Unlimited |
| **Location Filters** | ❌ Random only | ✅ +$0.25/SMS | ✅ Included | ✅ Included |
| **ISP/Carrier Filter** | ❌ | ✅ +$0.50/SMS | ✅ Included | ✅ Included |
| **Affiliate Program** | ❌ | ❌ | ✅ Standard | ✅ Enhanced |
| **Support** | Community | Community | Priority | Dedicated |

**Freemium Benefits**: 
- ✅ **11% discount** - $2.22/SMS vs $2.50/SMS
- ✅ **No monthly fees** - Pay only for what you use
- ✅ **Instant start** - All new users begin here
- ✅ **Easy upgrade** - Unlock filters and API anytime

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
- **Freemium**: Start free with 9 SMS per $20 deposit ($2.22/SMS)
- **Pay-As-You-Go**: Add location/ISP filtering (+$0.25-$0.75/SMS)
- **Pro**: $25/mo with API access and all filters included
- **Custom**: $35/mo with unlimited API keys and enhanced affiliate program

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

## 📚 Documentation

- [API Guide](docs/API_GUIDE.md) - Complete API reference
- [Tier Management API](docs/TIER_MANAGEMENT_API.md) - Tier system API
- [Tier CLI Reference](docs/TIER_CLI_REFERENCE.md) - Command-line tools
- [Security & Compliance](docs/SECURITY_AND_COMPLIANCE.md) - Security details
- [Server Management](docs/SERVER_MANAGEMENT.md) - Server operations
- [Voice vs SMS Verification](docs/VOICE_VS_SMS_VERIFICATION.md) - Verification methods

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

