# 📚 Namaskah SMS API Documentation

**Version**: 2.4.0  
**Last Updated**: December 2024  
**Security Level**: Production Ready ✅

---

## 🔒 Security Features

### Authentication
- **JWT Token Authentication** - All endpoints require valid JWT tokens
- **Rate Limiting** - Multi-algorithm rate limiting with adaptive thresholds
- **Input Sanitization** - All inputs sanitized against XSS and injection attacks
- **SQL Injection Protection** - Parameterized queries and ORM usage
- **Path Traversal Protection** - Safe file path validation

### Data Protection
- **Sensitive Data Masking** - Automatic masking of credentials and PII
- **Secure Logging** - Log injection prevention and structured logging
- **Environment Secrets** - Secure secrets management with validation

---

## 🚀 Core Endpoints

### Verification API

#### Create Verification
```http
POST /api/verify/create
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "service_name": "telegram",
  "country": "US",
  "pricing_tier": "standard"
}
```

**Response:**
```json
{
  "id": "verification_id",
  "service_name": "telegram", 
  "phone_number": "+1234567890",
  "status": "pending",
  "cost": 0.50,
  "created_at": "2024-12-01T10:00:00Z"
}
```

#### Check Verification Status
```http
GET /api/verify/{verification_id}
Authorization: Bearer <jwt_token>
```

#### Get SMS Messages
```http
GET /api/verify/{verification_id}/messages
Authorization: Bearer <jwt_token>
```

### Countries & Services

#### Get Countries
```http
GET /api/countries/
```

#### Get Services for Country
```http
GET /api/countries/{country}/services
```

---

## 🔧 Configuration

### Environment Variables
```bash
# Required
SECRET_KEY=your-secret-key-32-chars-min
JWT_SECRET_KEY=your-jwt-secret-32-chars-min
DATABASE_URL=postgresql://user:pass@host:port/db

# SMS Providers
TEXTVERIFIED_API_KEY=your-textverified-key
FIVESIM_API_KEY=your-5sim-key

# Optional
REDIS_URL=redis://localhost:6379/0
SENTRY_DSN=your-sentry-dsn
```

### Security Configuration
```python
# Rate Limiting
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=3600

# JWT Settings  
JWT_EXPIRE_MINUTES=480  # 8 hours
JWT_ALGORITHM=HS256

# Timeouts
HTTP_TIMEOUT_SECONDS=30.0
ASYNC_TASK_TIMEOUT_SECONDS=1800
```

---

## 📊 Error Handling

### Standard Error Response
```json
{
  "detail": "Error message",
  "error_code": "SPECIFIC_ERROR_CODE",
  "timestamp": "2024-12-01T10:00:00Z"
}
```

### Error Codes
- `INSUFFICIENT_CREDITS` - User has insufficient credits
- `INVALID_INPUT` - Request validation failed
- `RESOURCE_NOT_FOUND` - Requested resource not found
- `EXTERNAL_SERVICE_ERROR` - SMS provider error
- `RATE_LIMIT_EXCEEDED` - Rate limit exceeded

---

## 🛡️ Security Best Practices

### For Developers
1. **Always validate input** - Use provided validation utilities
2. **Sanitize outputs** - Use data masking for sensitive information
3. **Use parameterized queries** - Never concatenate SQL strings
4. **Implement proper error handling** - Use specific exception types
5. **Log securely** - Use structured logging with sanitization

### For API Users
1. **Secure JWT tokens** - Store tokens securely, rotate regularly
2. **Use HTTPS only** - Never send requests over HTTP
3. **Implement retry logic** - Handle rate limits and temporary failures
4. **Validate responses** - Check response status and structure
5. **Monitor usage** - Track API usage and costs

---

## 📈 Performance & Monitoring

### Caching
- **Redis Primary** - High-performance caching with Redis
- **Memory Fallback** - In-memory cache when Redis unavailable
- **Dual-Layer Architecture** - Automatic failover between cache layers

### Rate Limiting
- **Token Bucket** - Smooth rate limiting for burst traffic
- **Sliding Window** - Precise rate limiting over time windows
- **Adaptive Limiting** - Dynamic limits based on system load

### Monitoring
- **Prometheus Metrics** - Comprehensive application metrics
- **Health Checks** - Automated health monitoring
- **Error Tracking** - Structured error logging and alerting

---

## 🔄 Migration Guide

### From Previous Versions

#### Breaking Changes in v2.4.0
- **Authentication Required** - All endpoints now require JWT authentication
- **Rate Limiting** - New rate limiting may affect high-volume usage
- **Error Format** - Standardized error response format

#### Migration Steps
1. **Update Authentication** - Implement JWT token handling
2. **Handle Rate Limits** - Add retry logic for rate limit responses
3. **Update Error Handling** - Handle new error response format
4. **Test Thoroughly** - Validate all integrations work correctly

---

## 📞 Support

### Documentation
- **API Reference** - Complete endpoint documentation
- **Security Guide** - Security implementation details
- **Migration Guide** - Version upgrade instructions

### Contact
- **Technical Support** - support@namaskah.app
- **Security Issues** - security@namaskah.app
- **General Inquiries** - hello@namaskah.app

---

**Built with FastAPI + Advanced Security Features**
