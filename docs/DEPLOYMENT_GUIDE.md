# Deployment Guide

**Version**: 2.5.0  
**Last Updated**: 2025-11-23

---

## Prerequisites

- Python 3.11+
- PostgreSQL 12+
- Redis 6+ (optional, for caching)
- Docker (optional)

---

## Environment Setup

### 1. Create .env file

```bash
# Security
SECRET_KEY=<generate-with-secrets.token_urlsafe(32)>
JWT_SECRET_KEY=<generate-with-secrets.token_urlsafe(32)>

# Database
DATABASE_URL=postgresql://<user>:<password>@localhost:5432/namaskah

# Redis (optional)
REDIS_URL=redis://localhost:6379/0

# API Keys
SMS_PROVIDER_API_KEY=<your-api-key>
SMS_PROVIDER_EMAIL=<your-email>

# Environment
ENVIRONMENT=production
DEBUG=false

# Server
HOST=0.0.0.0
PORT=8000
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Database Setup

```bash
# Create database
createdb namaskah

# Run migrations
alembic upgrade head

# Create tables
python3 scripts/create_tables.py
```

---

## Local Development

### Start Application

```bash
./start.sh
# or
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

### Run Tests

```bash
pytest tests/ -v
```

### Code Quality

```bash
# Format code
black app/

# Sort imports
isort app/

# Lint
flake8 app/
```

---

## Docker Deployment

### Build Image

```bash
docker build -t namaskah-sms:2.5.0 .
```

### Run Container

```bash
docker run -d \
  --name namaskah-sms \
  -p 8000:8000 \
  -e DATABASE_URL=postgresql://<user>:<password>@db:5432/namaskah \
  -e SECRET_KEY=<your-secret-key> \
  -e JWT_SECRET_KEY=<your-jwt-secret> \
  namaskah-sms:2.5.0
```

---

## Production Deployment

### 1. Security Checklist

- [ ] Generate strong SECRET_KEY and JWT_SECRET_KEY
- [ ] Use HTTPS only
- [ ] Set DEBUG=false
- [ ] Configure CORS origins
- [ ] Enable CSRF protection
- [ ] Set secure cookie flags
- [ ] Configure rate limiting
- [ ] Enable logging

### 2. Database

- [ ] Use PostgreSQL (not SQLite)
- [ ] Enable SSL connections
- [ ] Configure connection pooling
- [ ] Set up backups
- [ ] Monitor performance

### 3. Caching

- [ ] Set up Redis
- [ ] Configure cache expiry
- [ ] Monitor memory usage

### 4. Monitoring

- [ ] Set up logging
- [ ] Configure error tracking (Sentry)
- [ ] Monitor performance
- [ ] Set up alerts

### 5. Deployment

```bash
# Pull latest code
git pull origin main

# Install dependencies
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Restart application
systemctl restart namaskah-sms
```

---

## Health Checks

### Application Health

```bash
curl http://localhost:8000/api/system/health
```

### Database Health

```bash
curl http://localhost:8000/api/system/health
```

---

## Troubleshooting

### Application Won't Start

1. Check logs: `tail -f app.log`
2. Verify environment variables
3. Check database connection
4. Verify port availability

### Database Connection Issues

1. Check PostgreSQL is running
2. Verify DATABASE_URL
3. Check network connectivity
4. Verify credentials

### Performance Issues

1. Check database queries
2. Monitor Redis cache
3. Check rate limiting
4. Profile application

---

## Rollback

```bash
# Revert to previous version
git checkout <previous-commit>

# Reinstall dependencies
pip install -r requirements.txt

# Run migrations (if needed)
alembic downgrade -1

# Restart application
systemctl restart namaskah-sms
```

---

## Monitoring

### Logs

```bash
# View logs
tail -f app.log

# Search logs
grep "ERROR" app.log
```

### Metrics

- Request count
- Response time
- Error rate
- Database connections
- Cache hit rate

---

## Support

For deployment issues, contact devops@namaskah.app
