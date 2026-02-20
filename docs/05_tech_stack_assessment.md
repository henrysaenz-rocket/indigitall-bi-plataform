# inDigital Tech Stack Assessment
## Discovery Questionnaire & Findings

**Prepared by:** Abstract Studio
**Date:** December 2025
**Status:** Draft - Pending inDigital Input

---

## Purpose

This document captures the technical landscape of inDigital's platform to inform the design and implementation of the Analytics Platform integration. Complete answers are required before development begins.

---

## Section 1: Company & Product Overview

### 1.1 General Information

| Question | Answer |
|----------|--------|
| Company name | inDigital |
| Primary product | CRM / Customer Engagement Platform |
| Target market | |
| Number of active clients (tenants) | |
| Typical client size (users per client) | |
| Geographic regions served | |

### 1.2 Current Analytics Capabilities

| Question | Answer |
|----------|--------|
| Do you offer any analytics today? | |
| If yes, what tools/features? | |
| What are clients asking for that you can't provide? | |
| Have clients churned due to lack of analytics? | |
| What's the #1 analytics request from clients? | |

---

## Section 2: Technical Architecture

### 2.1 Platform Stack

| Component | Technology | Version | Notes |
|-----------|------------|---------|-------|
| Frontend framework | (React, Vue, Angular, etc.) | | |
| Backend language | (Node.js, Python, Java, etc.) | | |
| Backend framework | (Express, Django, Spring, etc.) | | |
| Primary database | (PostgreSQL, MySQL, MongoDB, etc.) | | |
| Secondary databases | | | |
| Hosting provider | (AWS, GCP, Azure, on-prem) | | |
| CDN | | | |
| Cache layer | (Redis, Memcached, etc.) | | |

### 2.2 Architecture Diagram

Please provide or describe your current architecture:

```
[Space for architecture diagram or description]
```

### 2.3 Infrastructure

| Question | Answer |
|----------|--------|
| Is infrastructure containerized? (Docker, K8s) | |
| Do you use infrastructure-as-code? (Terraform, etc.) | |
| CI/CD pipeline tools | |
| Monitoring/observability tools | |
| Log management | |

---

## Section 3: Authentication & Authorization

### 3.1 Authentication System

| Question | Answer |
|----------|--------|
| Authentication method | (Username/password, OAuth, SSO, etc.) |
| Identity provider | (Auth0, Okta, Cognito, custom, etc.) |
| Do you support SSO for enterprise clients? | |
| Multi-factor authentication available? | |
| Session management approach | (JWT, sessions, etc.) |
| Token expiration time | |

### 3.2 Authorization Model

| Question | Answer |
|----------|--------|
| How is tenant isolation implemented? | |
| Role-based access control (RBAC)? | |
| What roles exist? | (Admin, User, Viewer, etc.) |
| Can clients have custom roles? | |
| How are permissions enforced? | |

### 3.3 Integration Requirements

| Question | Answer |
|----------|--------|
| Can you generate signed JWT tokens for external services? | |
| What claims can be included in tokens? | |
| Can you expose a token endpoint for our service? | |
| Preferred authentication flow for embedded apps | |

---

## Section 4: API & Data Access

### 4.1 API Overview

| Question | Answer |
|----------|--------|
| Do you have a REST API? | |
| Do you have a GraphQL API? | |
| Is the API documented? (Link) | |
| API versioning strategy | |
| API authentication method | (API key, OAuth, JWT) |

### 4.2 API Rate Limits

| Endpoint Category | Requests/Minute | Requests/Day | Notes |
|-------------------|-----------------|--------------|-------|
| General | | | |
| Bulk/Export | | | |
| Webhooks | | | |

### 4.3 Available Endpoints

Please list the main API endpoints and what data they expose:

| Endpoint | Method | Description | Pagination | Filters |
|----------|--------|-------------|------------|---------|
| /api/v1/users | GET | List users | | |
| /api/v1/events | GET | List events | | |
| /api/v1/campaigns | GET | List campaigns | | |
| | | | | |
| | | | | |

### 4.4 Webhooks

| Question | Answer |
|----------|--------|
| Do you support webhooks? | |
| What events trigger webhooks? | |
| Webhook payload format | |
| Retry policy on failure | |
| Can webhooks be configured per-tenant? | |

### 4.5 Bulk Data Export

| Question | Answer |
|----------|--------|
| Is bulk data export available? | |
| Export formats supported | (CSV, JSON, etc.) |
| Size limits | |
| Async export (for large datasets)? | |

---

## Section 5: Data Model

### 5.1 Core Entities

List the main data entities in your system:

| Entity | Description | Approx. Records (Total) | Records per Tenant (Avg) |
|--------|-------------|-------------------------|--------------------------|
| Users/Contacts | | | |
| Events/Activities | | | |
| Transactions | | | |
| Campaigns | | | |
| Messages | | | |
| | | | |

### 5.2 Entity Relationships

Please describe or diagram the relationships between entities:

```
[Space for ER diagram or description]

Example:
- User has many Events
- User has many Transactions
- Campaign has many Messages
- Message belongs to User
```

### 5.3 Key Fields per Entity

#### Users/Contacts

| Field | Type | Description | Always Present? |
|-------|------|-------------|-----------------|
| user_id | | | |
| email | | | |
| phone | | | |
| name | | | |
| created_at | | | |
| | | | |

#### Events/Activities

| Field | Type | Description | Always Present? |
|-------|------|-------------|-----------------|
| event_id | | | |
| user_id | | | |
| event_type | | | |
| timestamp | | | |
| | | | |

#### Transactions

| Field | Type | Description | Always Present? |
|-------|------|-------------|-----------------|
| transaction_id | | | |
| user_id | | | |
| amount | | | |
| currency | | | |
| | | | |

#### Campaigns

| Field | Type | Description | Always Present? |
|-------|------|-------------|-----------------|
| campaign_id | | | |
| name | | | |
| type | | | |
| status | | | |
| | | | |

### 5.4 Custom Fields

| Question | Answer |
|----------|--------|
| Do tenants have custom fields? | |
| How are custom fields stored? | (JSON column, separate table, etc.) |
| Can custom fields be queried via API? | |
| Max number of custom fields per entity | |

---

## Section 6: Multi-Tenancy

### 6.1 Tenant Structure

| Question | Answer |
|----------|--------|
| How are tenants identified? | (tenant_id, subdomain, etc.) |
| Single database or database-per-tenant? | |
| How is tenant data isolated? | |
| Can one user belong to multiple tenants? | |
| Tenant hierarchy | (Simple or nested organizations?) |

### 6.2 Tenant Provisioning

| Question | Answer |
|----------|--------|
| How are new tenants created? | |
| Average time to provision new tenant | |
| Is there a tenant management API? | |
| Can we programmatically create tenants? | |

### 6.3 Tenant Identification in API

| Question | Answer |
|----------|--------|
| How is tenant context passed to API? | (Header, URL, token claim) |
| Header name (if applicable) | |
| Can API access data across tenants? | (Admin only?) |

---

## Section 7: Security & Compliance

### 7.1 Data Security

| Question | Answer |
|----------|--------|
| Data encryption at rest? | |
| Data encryption in transit? | |
| PII handling policies | |
| Data retention policy | |
| Right to deletion (GDPR) supported? | |

### 7.2 Compliance

| Certification | Status | Notes |
|---------------|--------|-------|
| SOC 2 | | |
| GDPR | | |
| HIPAA | | |
| ISO 27001 | | |
| Other | | |

### 7.3 Security Requirements for Partners

| Question | Answer |
|----------|--------|
| Security review required? | |
| Penetration testing required? | |
| Data processing agreement (DPA) needed? | |
| Specific security certifications required? | |

---

## Section 8: Current Integrations

### 8.1 Existing Third-Party Integrations

| Integration | Purpose | How Connected |
|-------------|---------|---------------|
| | | |
| | | |
| | | |

### 8.2 Embedded Applications

| Question | Answer |
|----------|--------|
| Do you currently embed third-party apps? | |
| If yes, how? (iframe, SDK, etc.) | |
| Any issues with current embedding approach? | |
| CSP (Content Security Policy) restrictions? | |

---

## Section 9: Team & Process

### 9.1 Technical Contacts

| Role | Name | Email | Notes |
|------|------|-------|-------|
| Technical Lead | | | |
| Backend Developer | | | |
| Frontend Developer | | | |
| DevOps/Infrastructure | | | |
| Product Manager | | | |

### 9.2 Development Process

| Question | Answer |
|----------|--------|
| Sprint length | |
| Release frequency | |
| Staging/QA environment available? | |
| Can we get API access to staging? | |

---

## Section 10: Timeline & Priorities

### 10.1 Business Priorities

| Question | Answer |
|----------|--------|
| Target launch date | |
| Pilot clients identified? | |
| Must-have features for launch | |
| Nice-to-have features | |
| Biggest concern/risk | |

### 10.2 Resource Availability

| Question | Answer |
|----------|--------|
| Developer hours available for integration | |
| When can integration work begin? | |
| Any blackout periods? (holidays, freezes) | |

---

## Findings Summary

*To be completed after questionnaire is filled*

### Architecture Compatibility

| Aspect | Status | Notes |
|--------|--------|-------|
| API availability | | |
| Authentication integration | | |
| Multi-tenancy alignment | | |
| Data model completeness | | |
| Embedding feasibility | | |

### Identified Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| | | |
| | | |

### Recommended Approach

*Summary of technical approach based on findings*

---

## Next Steps

1. [ ] Schedule discovery call to walk through questionnaire
2. [ ] Obtain API documentation and access
3. [ ] Get access to staging environment
4. [ ] Identify pilot tenant for testing
5. [ ] Sign data processing agreement if required

---

*Please return completed questionnaire to: [contact@abstractstudio.ai]*
