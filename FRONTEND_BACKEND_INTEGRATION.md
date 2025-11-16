# 🔗 Frontend-Backend Integration Tasks

## Overview
Current frontend features are not fully responsive to backend/API. This document lists all integration tasks needed.

---

## 🎯 Phase 1: Core Verification Flow (CRITICAL)

### 1.1 SMS Verification Page (`/verify`)
- [ ] **Load countries from API**
  - Endpoint: `GET /api/countries/`
  - Current: Hardcoded list
  - Task: Fetch from backend, handle loading state

- [ ] **Load services by country**
  - Endpoint: `GET /api/countries/{country}/services`
  - Current: Hardcoded list
  - Task: Dynamic loading based on selected country

- [ ] **Create verification with real data**
  - Endpoint: `POST /api/verify/create`
  - Current: Mock implementation
  - Task: Send actual request, handle response

- [ ] **Poll for SMS code**
  - Endpoint: `GET /api/verify/{id}`
  - Current: Mock polling
  - Task: Real polling with actual API

- [ ] **Cancel verification**
  - Endpoint: `DELETE /api/verify/{id}`
  - Current: Mock cancel
  - Task: Real cancellation with refund

- [ ] **Get SMS messages**
  - Endpoint: `GET /api/verify/{id}/messages`
  - Current: Not implemented
  - Task: Fetch and display messages

---

## 🎯 Phase 2: Dashboard Integration (HIGH)

### 2.1 App Dashboard (`/app`)
- [ ] **Load account balance**
  - Endpoint: `GET /api/analytics/summary`
  - Current: Hardcoded $0.00
  - Task: Fetch real balance, update top bar

- [ ] **Load verification stats**
  - Endpoint: `GET /api/analytics/summary`
  - Current: Hardcoded 0 values
  - Task: Display real stats (total, success rate, rentals)

- [ ] **Load recent activity**
  - Endpoint: `GET /api/verify/history` (new endpoint needed)
  - Current: Hardcoded activities
  - Task: Fetch and display real activities

- [ ] **Quick action buttons**
  - Add Credits: `POST /api/wallet/add-credits` (new endpoint)
  - Notifications: `GET /api/notifications` (new endpoint)
  - Profile: `GET /api/user/profile` (new endpoint)

---

## 🎯 Phase 3: SMS History Page (HIGH)

### 3.1 SMS History (`/sms-history`)
- [ ] **Load SMS history**
  - Endpoint: `GET /api/verify/history`
  - Current: Mock data
  - Task: Fetch real SMS history

- [ ] **Filter by type**
  - Endpoint: `GET /api/verify/history?type=verification`
  - Current: Frontend filtering only
  - Task: Backend filtering

- [ ] **Pagination**
  - Endpoint: `GET /api/verify/history?skip=0&limit=10`
  - Current: Frontend pagination
  - Task: Backend pagination

- [ ] **Copy SMS code**
  - Current: Works with mock data
  - Task: Ensure works with real data

---

## 🎯 Phase 4: Authentication (CRITICAL)

### 4.1 Login Flow
- [ ] **Login endpoint**
  - Endpoint: `POST /api/auth/login`
  - Current: Mock login
  - Task: Real authentication

- [ ] **Token storage**
  - Current: localStorage
  - Task: Secure token handling

- [ ] **Token refresh**
  - Endpoint: `POST /api/auth/refresh`
  - Current: Not implemented
  - Task: Auto-refresh tokens

- [ ] **Logout**
  - Endpoint: `POST /api/auth/logout`
  - Current: localStorage.removeItem
  - Task: Backend logout

- [ ] **Protected routes**
  - Current: No protection
  - Task: Check token before rendering

---

## 🎯 Phase 5: Error Handling (HIGH)

### 5.1 API Error Responses
- [ ] **Handle 401 Unauthorized**
  - Current: Not handled
  - Task: Redirect to login

- [ ] **Handle 402 Payment Required**
  - Current: Not handled
  - Task: Show "Add Credits" prompt

- [ ] **Handle 429 Rate Limited**
  - Current: Not handled
  - Task: Show retry message

- [ ] **Handle 503 Service Unavailable**
  - Current: Not handled
  - Task: Show provider error

- [ ] **Handle network errors**
  - Current: Basic handling
  - Task: Retry logic, offline detection

---

## 🎯 Phase 6: Real-time Updates (MEDIUM)

### 6.1 WebSocket Integration
- [ ] **SMS code received notification**
  - Endpoint: `WS /ws/verify/{id}`
  - Current: Polling every 5 seconds
  - Task: Real-time WebSocket updates

- [ ] **Notification updates**
  - Endpoint: `WS /ws/notifications`
  - Current: Not implemented
  - Task: Real-time notifications

- [ ] **Balance updates**
  - Endpoint: `WS /ws/wallet`
  - Current: Not implemented
  - Task: Real-time balance updates

---

## 🎯 Phase 7: Analytics Integration (MEDIUM)

### 7.1 Analytics Dashboard
- [ ] **Load dashboard data**
  - Endpoint: `GET /api/analytics/dashboard`
  - Current: Not implemented
  - Task: Fetch and display

- [ ] **Load summary stats**
  - Endpoint: `GET /api/analytics/summary`
  - Current: Partial implementation
  - Task: Complete integration

- [ ] **Load trends**
  - Endpoint: `GET /api/analytics/trends`
  - Current: Not implemented
  - Task: Display trend charts

- [ ] **Load top services**
  - Endpoint: `GET /api/analytics/top-services`
  - Current: Not implemented
  - Task: Display service rankings

- [ ] **Load top countries**
  - Endpoint: `GET /api/analytics/top-countries`
  - Current: Not implemented
  - Task: Display country rankings

---

## 🎯 Phase 8: User Management (MEDIUM)

### 8.1 Profile Management
- [ ] **Load user profile**
  - Endpoint: `GET /api/user/profile`
  - Current: Not implemented
  - Task: Display user info

- [ ] **Update profile**
  - Endpoint: `PUT /api/user/profile`
  - Current: Not implemented
  - Task: Allow profile updates

- [ ] **Change password**
  - Endpoint: `POST /api/user/change-password`
  - Current: Not implemented
  - Task: Password change form

- [ ] **Two-factor authentication**
  - Endpoint: `POST /api/user/2fa/enable`
  - Current: Not implemented
  - Task: 2FA setup

---

## 🎯 Phase 9: Wallet/Credits (MEDIUM)

### 9.1 Credit Management
- [ ] **Add credits**
  - Endpoint: `POST /api/wallet/add-credits`
  - Current: Mock button
  - Task: Real payment integration

- [ ] **View credit history**
  - Endpoint: `GET /api/wallet/history`
  - Current: Not implemented
  - Task: Display transactions

- [ ] **View billing**
  - Endpoint: `GET /api/wallet/billing`
  - Current: Not implemented
  - Task: Display invoices

- [ ] **Download invoice**
  - Endpoint: `GET /api/wallet/invoice/{id}`
  - Current: Not implemented
  - Task: PDF download

---

## 🎯 Phase 10: Settings (LOW)

### 10.1 User Settings
- [ ] **Notification preferences**
  - Endpoint: `PUT /api/user/preferences`
  - Current: Not implemented
  - Task: Save preferences

- [ ] **API key management**
  - Endpoint: `GET/POST/DELETE /api/user/api-keys`
  - Current: Not implemented
  - Task: Manage API keys

- [ ] **Webhook configuration**
  - Endpoint: `GET/POST/PUT/DELETE /api/user/webhooks`
  - Current: Not implemented
  - Task: Configure webhooks

---

## 📋 Backend Endpoints Needed

### New Endpoints to Create
```
POST   /api/auth/login                 User login
POST   /api/auth/logout                User logout
POST   /api/auth/refresh               Refresh token
GET    /api/user/profile               Get user profile
PUT    /api/user/profile               Update profile
POST   /api/user/change-password       Change password
POST   /api/user/2fa/enable            Enable 2FA
GET    /api/verify/history             Get SMS history
POST   /api/wallet/add-credits         Add credits
GET    /api/wallet/history             Get transaction history
GET    /api/wallet/billing             Get billing info
GET    /api/wallet/invoice/{id}        Download invoice
GET    /api/notifications              Get notifications
POST   /api/user/preferences           Save preferences
GET    /api/user/api-keys              List API keys
POST   /api/user/api-keys              Create API key
DELETE /api/user/api-keys/{id}         Delete API key
GET    /api/user/webhooks              List webhooks
POST   /api/user/webhooks              Create webhook
PUT    /api/user/webhooks/{id}         Update webhook
DELETE /api/user/webhooks/{id}         Delete webhook
WS     /ws/verify/{id}                 WebSocket SMS updates
WS     /ws/notifications               WebSocket notifications
WS     /ws/wallet                      WebSocket wallet updates
```

---

## 🔄 Integration Checklist

### For Each Feature:
- [ ] API endpoint exists
- [ ] Frontend calls endpoint
- [ ] Loading state shown
- [ ] Error handling implemented
- [ ] Success response handled
- [ ] Data displayed correctly
- [ ] Mobile responsive
- [ ] Tested with real data

---

## 📊 Priority Order

1. **CRITICAL (Week 1)**
   - Authentication (login/logout)
   - SMS verification flow
   - Error handling

2. **HIGH (Week 2)**
   - Dashboard stats
   - SMS history
   - Cancel verification

3. **MEDIUM (Week 3)**
   - Analytics
   - WebSocket updates
   - Wallet/credits

4. **LOW (Week 4)**
   - Settings
   - API keys
   - Webhooks

---

## 🧪 Testing Requirements

For each integration:
- [ ] Unit test for API call
- [ ] Integration test with backend
- [ ] Error case testing
- [ ] Loading state testing
- [ ] Mobile testing
- [ ] Performance testing

---

## 📝 Notes

- All API calls should include error handling
- All forms should validate before submission
- All lists should support pagination
- All data should be cached appropriately
- All sensitive data should be encrypted
- All requests should include auth token

---

**Status:** 🔴 NOT STARTED  
**Estimated Time:** 4-6 weeks  
**Priority:** CRITICAL
