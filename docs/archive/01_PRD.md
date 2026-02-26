# Product Requirements Document (PRD)
## inDigital Analytics Platform

**Document Owner:** Abstract Studio
**Version:** 1.0
**Date:** December 2025
**Status:** Draft

---

## 1. Overview

### 1.1 Problem Statement

inDigital is a CRM/customer engagement platform that lacks robust analytics capabilities. Their clients need insights from their data but currently have no way to:
- Ask questions about their data without SQL knowledge
- Visualize trends and patterns
- Create automated reports
- Access real-time dashboards

This gap is causing client churn, lost deals, and missed upsell opportunities for inDigital.

### 1.2 Solution Summary

Build a **multi-tenant, AI-powered analytics platform** that:
- Embeds seamlessly into inDigital's CRM as a white-labeled feature
- Allows end users to ask questions in natural language
- Generates visualizations and dashboards automatically
- Provides CSV exports and scheduled reports
- Ensures complete data isolation between tenants

### 1.3 Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Platform uptime | 99.5% | Monitoring |
| Query response time | < 5 seconds | P95 latency |
| User adoption | 60% of enabled clients active | Monthly active users |
| Client satisfaction | NPS > 40 | Quarterly survey |
| Time to first insight | < 2 minutes | User analytics |

---

## 2. User Personas

### 2.1 End User (inDigital's Client Employee)

**Name:** Maria - Marketing Manager at Retail Corp

**Profile:**
- Works at a company that uses inDigital CRM
- Non-technical, no SQL or data skills
- Needs insights to make marketing decisions
- Currently exports data to Excel for analysis

**Goals:**
- Quickly understand campaign performance
- Identify top customers and segments
- Create reports for leadership
- Save time on manual analysis

**Pain Points:**
- Can't write SQL queries
- Manual exports are tedious
- No visualization tools
- Reports are always outdated

### 2.2 inDigital Administrator

**Name:** Carlos - inDigital Customer Success Manager

**Profile:**
- Works at inDigital
- Manages multiple client accounts
- Needs to see aggregate metrics across clients
- Helps clients get value from the platform

**Goals:**
- Monitor client usage and health
- Identify at-risk clients
- Demonstrate value to clients
- Onboard new clients to analytics

**Pain Points:**
- No visibility into client analytics usage
- Can't show ROI to clients
- Manual onboarding process
- No aggregate reporting

### 2.3 Abstract Studio Platform Admin

**Name:** Tech Team - Abstract Studio Engineers

**Profile:**
- Manages the analytics platform
- Monitors system health
- Handles support escalations

**Goals:**
- Keep platform running smoothly
- Monitor costs and usage
- Deploy updates without downtime
- Resolve issues quickly

---

## 3. Features & Requirements

### 3.1 Core Features (MVP)

#### F1: AI Chat Interface

**Description:** Natural language interface where users ask questions and receive answers with data and visualizations.

**Requirements:**
| ID | Requirement | Priority | Notes |
|----|-------------|----------|-------|
| F1.1 | User can type questions in natural language | Must Have | |
| F1.2 | System generates SQL from natural language | Must Have | Using Claude or Cortex |
| F1.3 | System executes SQL and returns results | Must Have | Max 10,000 rows |
| F1.4 | Results displayed as table | Must Have | |
| F1.5 | System auto-generates appropriate chart | Must Have | Based on data shape |
| F1.6 | User can export results as CSV | Must Have | |
| F1.7 | User can save query as "Saved Analysis" | Should Have | |
| F1.8 | Chat history persisted per session | Should Have | |
| F1.9 | Suggested questions for new users | Could Have | |
| F1.10 | Voice input support | Won't Have (v1) | Future |

**User Story:**
> As a marketing manager, I want to ask "Show me top customers by revenue this month" and see a table and chart, so I can quickly identify VIP customers.

**Acceptance Criteria:**
- Query response time < 5 seconds (P95)
- Correct data returned (tenant-isolated)
- Chart type appropriate for data
- Export produces valid CSV file

---

#### F2: Dashboard UI

**Description:** Pre-built and custom dashboards with interactive visualizations.

**Requirements:**
| ID | Requirement | Priority | Notes |
|----|-------------|----------|-------|
| F2.1 | Display multiple charts on single page | Must Have | Grid layout |
| F2.2 | Pre-built dashboard templates | Must Have | 3-5 templates |
| F2.3 | Global date filter affects all charts | Must Have | |
| F2.4 | Individual chart filters | Should Have | |
| F2.5 | Full-screen chart view | Should Have | |
| F2.6 | Dashboard auto-refresh | Should Have | Configurable interval |
| F2.7 | User can create custom dashboards | Could Have | |
| F2.8 | Dashboard sharing via link | Could Have | |

**Chart Types Required:**
- Bar chart (horizontal & vertical)
- Line chart
- Pie/Donut chart
- Table with pagination
- KPI card with trend indicator
- Area chart
- Scatter plot (nice to have)
- Heatmap (nice to have)

---

#### F3: Data Export

**Description:** Allow users to export data in various formats.

**Requirements:**
| ID | Requirement | Priority | Notes |
|----|-------------|----------|-------|
| F3.1 | Export table data as CSV | Must Have | |
| F3.2 | Export chart as PNG image | Should Have | |
| F3.3 | Export dashboard as PDF | Could Have | |
| F3.4 | Scheduled export via email | Could Have | |
| F3.5 | Export up to 100,000 rows | Must Have | Async for large |

---

#### F4: Saved Analyses

**Description:** Users can save queries/analyses for later access and schedule periodic refresh.

**Requirements:**
| ID | Requirement | Priority | Notes |
|----|-------------|----------|-------|
| F4.1 | Save analysis with name and description | Must Have | |
| F4.2 | View list of saved analyses | Must Have | |
| F4.3 | Re-run saved analysis | Must Have | |
| F4.4 | Delete saved analysis | Must Have | |
| F4.5 | Schedule periodic refresh (daily/weekly) | Should Have | |
| F4.6 | Email notification when refresh completes | Could Have | |
| F4.7 | Share saved analysis with team members | Could Have | |

---

#### F5: Multi-Tenancy

**Description:** Complete data isolation between inDigital's clients.

**Requirements:**
| ID | Requirement | Priority | Notes |
|----|-------------|----------|-------|
| F5.1 | Each tenant sees only their data | Must Have | Non-negotiable |
| F5.2 | Tenant context from authentication token | Must Have | JWT claim |
| F5.3 | Row-level security in database | Must Have | Snowflake RLS |
| F5.4 | No cross-tenant data leakage | Must Have | Security critical |
| F5.5 | Tenant-specific branding (logo, colors) | Could Have | Premium feature |
| F5.6 | Tenant usage tracking | Should Have | For billing |

---

#### F6: White-Label & Embedding

**Description:** Platform appears as native inDigital feature.

**Requirements:**
| ID | Requirement | Priority | Notes |
|----|-------------|----------|-------|
| F6.1 | No Abstract Studio branding visible to end users | Must Have | |
| F6.2 | Customizable logo and colors | Must Have | inDigital branding |
| F6.3 | Embeddable via iframe | Must Have | |
| F6.4 | Responsive design (desktop/tablet/mobile) | Must Have | |
| F6.5 | Custom domain support | Could Have | analytics.indigital.com |
| F6.6 | Theme customization per partner | Could Have | |

---

### 3.2 Non-Functional Requirements

#### Performance

| Requirement | Target |
|-------------|--------|
| Page load time | < 3 seconds |
| Query response (simple) | < 3 seconds |
| Query response (complex) | < 10 seconds |
| Concurrent users per tenant | 50+ |
| Total concurrent users | 500+ |

#### Availability

| Requirement | Target |
|-------------|--------|
| Uptime | 99.5% |
| Planned maintenance window | Sunday 2-6 AM UTC |
| Recovery Time Objective (RTO) | 4 hours |
| Recovery Point Objective (RPO) | 1 hour |

#### Security

| Requirement | Implementation |
|-------------|----------------|
| Authentication | JWT tokens from inDigital |
| Authorization | Tenant-based, row-level security |
| Data encryption (transit) | TLS 1.3 |
| Data encryption (rest) | AES-256 (Snowflake default) |
| Audit logging | All queries logged with user/tenant |
| PII handling | Minimized, no full message content |

#### Scalability

| Requirement | Target |
|-------------|--------|
| Tenants supported | 500+ |
| Data volume per tenant | 10M+ rows |
| Total data volume | 1B+ rows |
| Horizontal scaling | Supported |

---

## 4. User Flows

### 4.1 First-Time User Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  1. User logs into inDigital CRM                               │
│                         │                                       │
│                         ▼                                       │
│  2. Clicks "Analytics" tab (new!)                              │
│                         │                                       │
│                         ▼                                       │
│  3. Sees welcome screen with:                                  │
│     - Brief intro to AI chat                                   │
│     - Suggested questions to try                               │
│     - Link to pre-built dashboards                             │
│                         │                                       │
│                         ▼                                       │
│  4. Tries suggested question:                                  │
│     "Show me my top 10 customers"                              │
│                         │                                       │
│                         ▼                                       │
│  5. Sees results + chart                                       │
│     "Wow, this is useful!"                                     │
│                         │                                       │
│                         ▼                                       │
│  6. Explores more questions or dashboards                      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 AI Chat Query Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  1. User types: "Which campaigns had best open rates?"         │
│                         │                                       │
│                         ▼                                       │
│  2. System extracts tenant_id from session                     │
│                         │                                       │
│                         ▼                                       │
│  3. System calls AI (Claude/Cortex) with:                      │
│     - User question                                            │
│     - Schema context (tables, columns)                         │
│     - Tenant filter requirement                                │
│                         │                                       │
│                         ▼                                       │
│  4. AI generates SQL:                                          │
│     SELECT campaign_name, open_rate                            │
│     FROM dim_campaigns                                         │
│     WHERE tenant_id = 'xxx'                                    │
│     ORDER BY open_rate DESC                                    │
│                         │                                       │
│                         ▼                                       │
│  5. System executes SQL against Snowflake                      │
│                         │                                       │
│                         ▼                                       │
│  6. System determines appropriate chart type                   │
│     (bar chart for ranked data)                                │
│                         │                                       │
│                         ▼                                       │
│  7. Display: summary text + table + chart                      │
│                         │                                       │
│                         ▼                                       │
│  8. Show action buttons: Export, Save, Ask follow-up           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 4.3 Saved Analysis Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  SAVING:                                                       │
│  1. User runs query and likes the results                      │
│  2. Clicks "Save Analysis"                                     │
│  3. Enters name: "Weekly Campaign Performance"                 │
│  4. Optionally sets schedule: "Every Monday 8 AM"              │
│  5. Analysis saved to their library                            │
│                                                                 │
│  ACCESSING:                                                    │
│  1. User opens "Saved Analyses" section                        │
│  2. Sees list of saved analyses with last run time             │
│  3. Clicks to view latest results                              │
│  4. Can re-run, edit schedule, or delete                       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 5. Data Model (Summary)

### 5.1 Core Entities

| Entity | Description | Source |
|--------|-------------|--------|
| `dim_contacts` | Customers/users from inDigital | inDigital API |
| `fct_activities` | Events, transactions, interactions | inDigital API |
| `fct_messages` | Communications (email, SMS, etc.) | inDigital API |
| `dim_campaigns` | Marketing campaigns | inDigital API |
| `saved_analyses` | User-saved queries | Platform |
| `tenants` | Tenant registry | Platform |

### 5.2 Tenant Isolation

All data tables include `tenant_id` column with row-level security policy:

```sql
CREATE ROW ACCESS POLICY tenant_isolation
AS (tenant_id VARCHAR) RETURNS BOOLEAN ->
    tenant_id = CURRENT_SESSION_CONTEXT('tenant_id');
```

---

## 6. Technical Constraints

### 6.1 Must Use

| Technology | Reason |
|------------|--------|
| Snowflake | Data warehouse - already decided |
| Streamlit | UI framework - Snowflake native |
| Claude or Cortex | AI for NL-to-SQL |
| n8n | Data ingestion workflows |

### 6.2 Constraints

| Constraint | Impact |
|------------|--------|
| iframe embedding | Limited deep integration with host app |
| Snowflake compute costs | Must optimize queries |
| API rate limits (inDigital) | Affects sync frequency |
| Claude API costs | Must cache/optimize prompts |

---

## 7. Out of Scope (v1)

The following are explicitly **not** included in v1:

| Feature | Reason | Future Version |
|---------|--------|----------------|
| Predictive analytics | Complexity | v2 |
| Custom ML models | Complexity | v2 |
| Real-time streaming | Cost/complexity | v2 |
| Mobile native app | Web-first approach | v3 |
| Multi-language UI | English first | v2 |
| On-premise deployment | Cloud only | Maybe never |
| Direct database connections | API-only approach | v2 |
| Anomaly detection | Requires more data | v2 |

---

## 8. Milestones & Timeline

### Phase 1: Foundation (Weeks 1-3)

| Milestone | Deliverables | Owner |
|-----------|--------------|-------|
| M1: Discovery Complete | Tech assessment, data mapping | Abstract Studio + inDigital |
| M2: Infrastructure Ready | Snowflake setup, tenant registry | Abstract Studio |
| M3: Data Pipeline | n8n workflows, initial sync | Abstract Studio |

### Phase 2: Core Features (Weeks 4-6)

| Milestone | Deliverables | Owner |
|-----------|--------------|-------|
| M4: AI Chat MVP | NL-to-SQL working, basic UI | Abstract Studio |
| M5: Visualizations | Chart generation, dashboard layout | Abstract Studio |
| M6: Export & Save | CSV export, saved analyses | Abstract Studio |

### Phase 3: Integration (Weeks 7-8)

| Milestone | Deliverables | Owner |
|-----------|--------------|-------|
| M7: Embedding | iframe integration, auth flow | Abstract Studio + inDigital |
| M8: White-Label | Branding, no Abstract Studio visibility | Abstract Studio |
| M9: Testing | End-to-end testing, security review | Both |

### Phase 4: Launch (Week 9)

| Milestone | Deliverables | Owner |
|-----------|--------------|-------|
| M10: Pilot | 3-5 clients live | Both |
| M11: Iterate | Feedback incorporation | Abstract Studio |
| M12: Full Launch | All clients enabled | inDigital |

---

## 9. Risks & Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| inDigital API limitations | Medium | High | Early API discovery, work with their team |
| AI generates incorrect SQL | Medium | Medium | Validation layer, human review option |
| Performance issues at scale | Low | High | Load testing, query optimization |
| Security vulnerability | Low | Critical | Security review, penetration testing |
| Low user adoption | Medium | Medium | Onboarding flow, suggested questions |
| Scope creep | High | Medium | Strict MVP definition, phase approach |

---

## 10. Open Questions

| # | Question | Owner | Status |
|---|----------|-------|--------|
| 1 | What are inDigital's exact API endpoints? | inDigital | Pending |
| 2 | What authentication method for embedding? | Both | Pending |
| 3 | Which 3-5 clients for pilot? | inDigital | Pending |
| 4 | Custom domain required for launch? | inDigital | Pending |
| 5 | Any compliance requirements (HIPAA, etc.)? | inDigital | Pending |

---

## 11. Appendix

### A. Glossary

| Term | Definition |
|------|------------|
| Tenant | An inDigital client (company using their CRM) |
| End User | Employee at a tenant company |
| Partner | inDigital (the company we're building for) |
| NL-to-SQL | Natural Language to SQL conversion |

### B. Related Documents

| Document | Location |
|----------|----------|
| Technical Architecture | `02_technical_architecture.md` |
| Business Proposal | `03_business_proposal.md` |
| Integration Guide | `04_integration_guide.md` |
| Tech Assessment | `05_tech_stack_assessment.md` |
| Data Mapping | `06_data_mapping_document.md` |

---

*Document maintained by Abstract Studio*
