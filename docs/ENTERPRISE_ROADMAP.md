# Enterprise Readiness Roadmap

## Executive Summary
This document outlines the strategic phases to transition Namaskah SMS from a functional MVP to a scalable, secure, and compliance-ready enterprise platform.

## Current State Assessment
- **Core Functionality**: ✅ SMS Verification, Rentals, Tiered Subscriptions, Basic Auth.
- **Database**: ⚠️ SQLite (Dev) - Needs migration to PostgreSQL (Prod).
- **Security**: ⚠️ Basic JWT. Missing 2FA, detailed Audit Logs, and WAF.
- **Observability**: ❌ Missing Metrics (`/metrics`), centralized logging, and tracing.
- **Scalability**: ⚠️ Synchronous SMS sending (partially polled). Needs robust Celery queues.

## Phase 1: Infrastructure Hardening (Weeks 1-2)
**Goal**: Establish a robust, production-grade foundation.
1.  **Database Migration**:
    -   Migrate from SQLite to PostgreSQL 15+.
    -   Implement Alembic migration scripts for all schema changes.
    -   Set up connection pooling (PgBouncer).
2.  **Background Workers**:
    -   Fully integrate Celery + Redis for asynchronous tasks (SMS sending, Webhook processing).
    -   Replace `run_in_executor` patterns with robust queues.
3.  **Containerization**:
    -   Finalize `Dockerfile` for production (multi-stage builds).
    -   Create `docker-compose.prod.yml` (App, DB, Redis, Nginx).

## Phase 2: Observability & Security (Weeks 3-4)
**Goal**: gain visibility and secure user data.
1.  **Metrics & Monitoring**:
    -   Integrate `prometheus-fastapi-instrumentator`.
    -   Expose `/metrics` endpoint.
    -   Set up Grafana dashboards for API latency, error rates, and credit usage.
2.  **Audit Logging**:
    -   Implement `AuditMiddleware` to record sensitive actions (billing, settings changes) to `audit_logs` table.
3.  **Security Upgrades**:
    -   Implement Two-Factor Authentication (TOTP) backend.
    -   Rate Limiting (Redis-backed) per user tier.

## Phase 3: Advanced Billing & Compliance (Weeks 5-6)
**Goal**: Automate financial flows and meet regulatory standards.
1.  **Billing Automation**:
    -   Robust Stripe/Paystack Webhook handling (idempotency, signature verification).
    -   PDF Invoice generation (utilizing `xhtml2pdf` or similar).
    -   Tax calculation integrations.
2.  **Compliance**:
    -   KYC (Know Your Customer) flow implementation.
    -   Data retention policies (auto-archive old verifications).

## Phase 4: High Availability (Weeks 7+)
**Goal**: Scale to millions of requests.
1.  **Horizontal Scaling**: K8s or Swarm deployment.
2.  **Database Replication**: Read replicas for analytics.
3.  **Global Edge**: CDN caching for static assets.
