# Data Mapping Document
## inDigital → Analytics Platform

**Prepared by:** Abstract Studio
**Date:** December 2025
**Status:** Draft - Pending inDigital API Review

---

## Purpose

This document maps inDigital's data entities and fields to the Analytics Platform's unified data model. It serves as the blueprint for data ingestion, transformation, and storage.

---

## 1. Source System Overview

### 1.1 inDigital API Summary

| Attribute | Value |
|-----------|-------|
| Base URL | `https://api.indigital.com` (TBD) |
| API Version | v1 (TBD) |
| Authentication | OAuth 2.0 / API Key (TBD) |
| Rate Limits | TBD |
| Documentation | TBD |

### 1.2 Available Entities

| Entity | API Endpoint | Sync Mode | Priority |
|--------|--------------|-----------|----------|
| Users/Contacts | `/api/v1/users` | Incremental | High |
| Events | `/api/v1/events` | Incremental | High |
| Transactions | `/api/v1/transactions` | Incremental | High |
| Campaigns | `/api/v1/campaigns` | Full Refresh | Medium |
| Messages | `/api/v1/messages` | Incremental | High |
| Segments | `/api/v1/segments` | Full Refresh | Low |

---

## 2. Entity Mappings

### 2.1 Users/Contacts → dim_contacts

#### Source: inDigital Users

```
Endpoint: GET /api/v1/users
Pagination: Cursor-based
Incremental Field: updated_at
```

#### Field Mapping

| inDigital Field | Type | Target Field | Target Type | Transform | Notes |
|-----------------|------|--------------|-------------|-----------|-------|
| `user_id` | string | `contact_id` | VARCHAR(100) | None | Primary key |
| `tenant_id` | string | `tenant_id` | VARCHAR(50) | None | From API context |
| `email` | string | `email` | VARCHAR(255) | LOWER() | Normalize |
| `phone` | string | `phone` | VARCHAR(50) | Normalize phone | E.164 format |
| `first_name` | string | `first_name` | VARCHAR(100) | None | |
| `last_name` | string | `last_name` | VARCHAR(100) | None | |
| `full_name` | string | `full_name` | VARCHAR(255) | Concat if null | first + last |
| `created_at` | timestamp | `created_at` | TIMESTAMP_NTZ | Parse ISO8601 | |
| `updated_at` | timestamp | `updated_at` | TIMESTAMP_NTZ | Parse ISO8601 | |
| `status` | string | `status` | VARCHAR(50) | Map values | See mapping below |
| `tags` | array | `source_attributes.tags` | VARIANT | JSON | |
| `custom_fields` | object | `source_attributes.custom` | VARIANT | JSON | |
| `lifetime_value` | number | `lifetime_value` | DECIMAL(15,2) | None | If available |
| `total_purchases` | number | `total_interactions` | INTEGER | None | Or calculate |

#### Status Mapping

| inDigital Status | Analytics Platform Status |
|------------------|---------------------------|
| `active` | `active` |
| `inactive` | `inactive` |
| `unsubscribed` | `churned` |
| `deleted` | (exclude) |

#### Target Table: MARTS.dim_contacts

```sql
CREATE TABLE MARTS.dim_contacts (
    contact_key         INTEGER AUTOINCREMENT PRIMARY KEY,
    tenant_id           VARCHAR(50) NOT NULL,
    source_id           VARCHAR(50) NOT NULL DEFAULT 'indigital',
    contact_id          VARCHAR(100) NOT NULL,
    email               VARCHAR(255),
    phone               VARCHAR(50),
    first_name          VARCHAR(100),
    last_name           VARCHAR(100),
    full_name           VARCHAR(255),
    created_at          TIMESTAMP_NTZ,
    updated_at          TIMESTAMP_NTZ,
    first_interaction_date  DATE,
    last_interaction_date   DATE,
    total_interactions      INTEGER,
    lifetime_value          DECIMAL(15,2),
    status              VARCHAR(50),
    segment             VARCHAR(100),
    source_attributes   VARIANT,
    _loaded_at          TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),

    UNIQUE (tenant_id, source_id, contact_id)
);
```

---

### 2.2 Events → fct_activities

#### Source: inDigital Events

```
Endpoint: GET /api/v1/events
Pagination: Cursor-based
Incremental Field: event_timestamp
```

#### Field Mapping

| inDigital Field | Type | Target Field | Target Type | Transform | Notes |
|-----------------|------|--------------|-------------|-----------|-------|
| `event_id` | string | `activity_id` | VARCHAR(100) | None | Primary key |
| `tenant_id` | string | `tenant_id` | VARCHAR(50) | None | From API context |
| `user_id` | string | `contact_key` | INTEGER | Lookup | FK to dim_contacts |
| `event_type` | string | `activity_type` | VARCHAR(100) | None | |
| `event_category` | string | `activity_category` | VARCHAR(50) | Map values | See mapping |
| `event_timestamp` | timestamp | `activity_timestamp` | TIMESTAMP_NTZ | Parse ISO8601 | |
| `properties` | object | `source_attributes` | VARIANT | JSON | |
| `campaign_id` | string | `campaign_key` | INTEGER | Lookup | FK to dim_campaigns |
| `channel` | string | `channel` | VARCHAR(50) | None | |
| `revenue` | number | `activity_value` | DECIMAL(15,2) | None | If applicable |
| `currency` | string | `currency` | VARCHAR(3) | None | |

#### Category Mapping

| inDigital Event Type | Activity Category |
|----------------------|-------------------|
| `email_sent`, `email_opened`, `email_clicked` | `engagement` |
| `purchase`, `refund`, `subscription` | `transaction` |
| `page_view`, `app_open`, `feature_used` | `engagement` |
| `support_ticket`, `chat_started` | `support` |
| `campaign_entered`, `campaign_converted` | `campaign` |

#### Target Table: MARTS.fct_activities

```sql
CREATE TABLE MARTS.fct_activities (
    activity_key        INTEGER AUTOINCREMENT PRIMARY KEY,
    tenant_id           VARCHAR(50) NOT NULL,
    source_id           VARCHAR(50) NOT NULL DEFAULT 'indigital',
    contact_key         INTEGER REFERENCES MARTS.dim_contacts(contact_key),
    activity_id         VARCHAR(100) NOT NULL,
    activity_timestamp  TIMESTAMP_NTZ NOT NULL,
    activity_category   VARCHAR(50),
    activity_type       VARCHAR(100),
    activity_value      DECIMAL(15,2),
    currency            VARCHAR(3),
    channel             VARCHAR(50),
    campaign_key        INTEGER,
    source_attributes   VARIANT,
    _loaded_at          TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);
```

---

### 2.3 Transactions → fct_activities (activity_category = 'transaction')

#### Source: inDigital Transactions

```
Endpoint: GET /api/v1/transactions
Pagination: Offset-based
Incremental Field: created_at
```

#### Field Mapping

| inDigital Field | Type | Target Field | Target Type | Transform | Notes |
|-----------------|------|--------------|-------------|-----------|-------|
| `transaction_id` | string | `activity_id` | VARCHAR(100) | Prefix 'txn_' | Avoid collision |
| `tenant_id` | string | `tenant_id` | VARCHAR(50) | None | |
| `user_id` | string | `contact_key` | INTEGER | Lookup | |
| `amount` | number | `activity_value` | DECIMAL(15,2) | None | |
| `currency` | string | `currency` | VARCHAR(3) | None | |
| `type` | string | `activity_type` | VARCHAR(100) | Map | 'purchase', 'refund' |
| `created_at` | timestamp | `activity_timestamp` | TIMESTAMP_NTZ | Parse | |
| `status` | string | `source_attributes.status` | VARIANT | JSON | |
| `items` | array | `source_attributes.items` | VARIANT | JSON | |
| `payment_method` | string | `source_attributes.payment` | VARIANT | JSON | |

#### Notes
- Transactions are stored in `fct_activities` with `activity_category = 'transaction'`
- This allows unified querying across all activity types

---

### 2.4 Campaigns → dim_campaigns

#### Source: inDigital Campaigns

```
Endpoint: GET /api/v1/campaigns
Pagination: Page-based
Sync Mode: Full Refresh (small dataset)
```

#### Field Mapping

| inDigital Field | Type | Target Field | Target Type | Transform | Notes |
|-----------------|------|--------------|-------------|-----------|-------|
| `campaign_id` | string | `campaign_id` | VARCHAR(100) | None | |
| `tenant_id` | string | `tenant_id` | VARCHAR(50) | None | |
| `name` | string | `campaign_name` | VARCHAR(255) | None | |
| `type` | string | `campaign_type` | VARCHAR(100) | Map | |
| `status` | string | `status` | VARCHAR(50) | Map | |
| `start_date` | date | `start_date` | DATE | Parse | |
| `end_date` | date | `end_date` | DATE | Parse | |
| `stats.sent` | integer | `total_sent` | INTEGER | None | |
| `stats.delivered` | integer | `total_delivered` | INTEGER | None | |
| `stats.opened` | integer | `total_opened` | INTEGER | None | |
| `stats.clicked` | integer | `total_clicked` | INTEGER | None | |
| `stats.converted` | integer | `total_converted` | INTEGER | None | |

#### Target Table: MARTS.dim_campaigns

```sql
CREATE TABLE MARTS.dim_campaigns (
    campaign_key        INTEGER AUTOINCREMENT PRIMARY KEY,
    tenant_id           VARCHAR(50) NOT NULL,
    source_id           VARCHAR(50) NOT NULL DEFAULT 'indigital',
    campaign_id         VARCHAR(100) NOT NULL,
    campaign_name       VARCHAR(255),
    campaign_type       VARCHAR(100),
    status              VARCHAR(50),
    start_date          DATE,
    end_date            DATE,
    total_sent          INTEGER,
    total_delivered     INTEGER,
    total_opened        INTEGER,
    total_clicked       INTEGER,
    total_converted     INTEGER,
    source_attributes   VARIANT,
    _loaded_at          TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);
```

---

### 2.5 Messages → fct_messages

#### Source: inDigital Messages

```
Endpoint: GET /api/v1/messages
Pagination: Cursor-based
Incremental Field: created_at
```

#### Field Mapping

| inDigital Field | Type | Target Field | Target Type | Transform | Notes |
|-----------------|------|--------------|-------------|-----------|-------|
| `message_id` | string | `message_id` | VARCHAR(100) | None | |
| `tenant_id` | string | `tenant_id` | VARCHAR(50) | None | |
| `user_id` | string | `contact_key` | INTEGER | Lookup | |
| `campaign_id` | string | `campaign_key` | INTEGER | Lookup | Optional |
| `direction` | string | `direction` | VARCHAR(10) | Map | 'inbound'/'outbound' |
| `channel` | string | `channel` | VARCHAR(50) | Map | See mapping |
| `type` | string | `message_type` | VARCHAR(50) | None | |
| `content` | string | `content_preview` | VARCHAR(500) | Truncate | First 500 chars |
| `has_attachment` | boolean | `has_media` | BOOLEAN | None | |
| `status` | string | `status` | VARCHAR(50) | Map | |
| `created_at` | timestamp | `message_timestamp` | TIMESTAMP_NTZ | Parse | |

#### Channel Mapping

| inDigital Channel | Analytics Channel |
|-------------------|-------------------|
| `email` | `email` |
| `sms` | `sms` |
| `whatsapp` | `whatsapp` |
| `push` | `push` |
| `in_app` | `in_app` |
| `web` | `web` |

#### Target Table: MARTS.fct_messages

```sql
CREATE TABLE MARTS.fct_messages (
    message_key         INTEGER AUTOINCREMENT PRIMARY KEY,
    tenant_id           VARCHAR(50) NOT NULL,
    source_id           VARCHAR(50) NOT NULL DEFAULT 'indigital',
    contact_key         INTEGER REFERENCES MARTS.dim_contacts(contact_key),
    campaign_key        INTEGER,
    message_id          VARCHAR(100) NOT NULL,
    message_timestamp   TIMESTAMP_NTZ NOT NULL,
    direction           VARCHAR(10),
    channel             VARCHAR(50),
    message_type        VARCHAR(50),
    content_preview     VARCHAR(500),
    has_media           BOOLEAN,
    status              VARCHAR(50),
    source_attributes   VARIANT,
    _loaded_at          TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);
```

---

## 3. Sync Configuration

### 3.1 Sync Schedule

| Entity | Frequency | Mode | Priority | Est. Volume/Day |
|--------|-----------|------|----------|-----------------|
| Users | Every 15 min | Incremental | High | 1,000 |
| Events | Every 15 min | Incremental | High | 50,000 |
| Transactions | Every 15 min | Incremental | High | 5,000 |
| Messages | Every 15 min | Incremental | High | 20,000 |
| Campaigns | Every 1 hour | Full Refresh | Medium | 100 |

### 3.2 Incremental Sync Strategy

```
┌─────────────────────────────────────────────────────────────────────┐
│                    INCREMENTAL SYNC FLOW                             │
│                                                                      │
│   1. Read last sync cursor from ADMIN.sync_state                    │
│                                                                      │
│   2. Call API with cursor:                                          │
│      GET /api/v1/users?updated_since={cursor}                       │
│                                                                      │
│   3. Transform and load to RAW tables                               │
│                                                                      │
│   4. Run dbt transformation (RAW → STAGING → MARTS)                 │
│                                                                      │
│   5. Update cursor in ADMIN.sync_state                              │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.3 Sync State Table

```sql
CREATE TABLE ADMIN.sync_state (
    sync_id         INTEGER AUTOINCREMENT PRIMARY KEY,
    source_id       VARCHAR(50) NOT NULL,
    tenant_id       VARCHAR(50) NOT NULL,
    entity          VARCHAR(100) NOT NULL,
    last_cursor     VARCHAR(500),
    last_sync_at    TIMESTAMP_NTZ,
    records_synced  INTEGER,
    status          VARCHAR(20),
    error_message   TEXT,

    UNIQUE (source_id, tenant_id, entity)
);
```

---

## 4. Data Quality Rules

### 4.1 Validation Rules

| Entity | Field | Rule | Action |
|--------|-------|------|--------|
| Users | email | Valid email format | Warn, allow |
| Users | phone | E.164 format | Normalize |
| Users | user_id | Not null | Reject |
| Events | event_timestamp | Not future | Warn, allow |
| Events | user_id | Exists in users | Orphan table |
| Transactions | amount | Positive number | Reject if negative |
| Messages | content | Max 10,000 chars | Truncate |

### 4.2 Deduplication Strategy

| Entity | Dedup Key | Strategy |
|--------|-----------|----------|
| Users | tenant_id + user_id | Upsert (latest wins) |
| Events | tenant_id + event_id | Insert only (immutable) |
| Transactions | tenant_id + transaction_id | Upsert (status updates) |
| Messages | tenant_id + message_id | Insert only |
| Campaigns | tenant_id + campaign_id | Upsert (stats update) |

---

## 5. Calculated Fields

### 5.1 Contact Metrics (dim_contacts)

| Field | Calculation | Update Frequency |
|-------|-------------|------------------|
| `first_interaction_date` | MIN(activity_timestamp) from fct_activities | Daily |
| `last_interaction_date` | MAX(activity_timestamp) from fct_activities | Every sync |
| `total_interactions` | COUNT(*) from fct_activities | Every sync |
| `lifetime_value` | SUM(activity_value) where category='transaction' | Every sync |

### 5.2 SQL for Calculated Fields

```sql
-- Update contact metrics after sync
MERGE INTO MARTS.dim_contacts t
USING (
    SELECT
        contact_key,
        MIN(activity_timestamp) as first_interaction,
        MAX(activity_timestamp) as last_interaction,
        COUNT(*) as total_interactions,
        SUM(CASE WHEN activity_category = 'transaction' THEN activity_value ELSE 0 END) as ltv
    FROM MARTS.fct_activities
    GROUP BY contact_key
) s
ON t.contact_key = s.contact_key
WHEN MATCHED THEN UPDATE SET
    first_interaction_date = s.first_interaction::DATE,
    last_interaction_date = s.last_interaction::DATE,
    total_interactions = s.total_interactions,
    lifetime_value = s.ltv;
```

---

## 6. PII & Sensitive Data

### 6.1 PII Fields

| Entity | Field | PII Type | Handling |
|--------|-------|----------|----------|
| Users | email | Direct PII | Store, mask in logs |
| Users | phone | Direct PII | Store, mask in logs |
| Users | first_name | Direct PII | Store |
| Users | last_name | Direct PII | Store |
| Messages | content | Potential PII | Truncate, no full storage |

### 6.2 Data Retention

| Data Type | Retention Period | Action After |
|-----------|------------------|--------------|
| Raw data | 90 days | Delete |
| Transformed data | 2 years | Archive to cold storage |
| Aggregated metrics | Indefinite | Keep |

---

## 7. Sample API Responses

### 7.1 Users Endpoint

```json
// GET /api/v1/users?updated_since=2025-01-01T00:00:00Z&limit=100
{
  "data": [
    {
      "user_id": "usr_123456",
      "email": "maria.garcia@example.com",
      "phone": "+5215512345678",
      "first_name": "Maria",
      "last_name": "Garcia",
      "full_name": "Maria Garcia",
      "status": "active",
      "tags": ["vip", "newsletter"],
      "custom_fields": {
        "company": "Acme Corp",
        "plan": "premium"
      },
      "created_at": "2024-06-15T10:30:00Z",
      "updated_at": "2025-01-15T14:22:00Z"
    }
  ],
  "pagination": {
    "cursor": "eyJsYXN0X2lkIjoiMTIzNDU2In0=",
    "has_more": true
  }
}
```

### 7.2 Events Endpoint

```json
// GET /api/v1/events?since=2025-01-01T00:00:00Z&limit=100
{
  "data": [
    {
      "event_id": "evt_789012",
      "user_id": "usr_123456",
      "event_type": "email_opened",
      "event_category": "engagement",
      "event_timestamp": "2025-01-15T09:45:00Z",
      "campaign_id": "cmp_456",
      "channel": "email",
      "properties": {
        "email_subject": "Your weekly update",
        "device": "mobile"
      }
    }
  ],
  "pagination": {
    "cursor": "...",
    "has_more": true
  }
}
```

---

## 8. Open Questions

| # | Question | Owner | Status |
|---|----------|-------|--------|
| 1 | What is the exact API base URL? | inDigital | Pending |
| 2 | What authentication method is used? | inDigital | Pending |
| 3 | Are there rate limits? What are they? | inDigital | Pending |
| 4 | Can we get historical data on first sync? | inDigital | Pending |
| 5 | How are deleted users handled in API? | inDigital | Pending |
| 6 | Is there a sandbox/staging API? | inDigital | Pending |
| 7 | What timezone are timestamps in? | inDigital | Pending |

---

## 9. Appendix: Raw Table Definitions

### RAW.indigital_users

```sql
CREATE TABLE RAW.indigital_users (
    _raw_id         INTEGER AUTOINCREMENT PRIMARY KEY,
    _tenant_id      VARCHAR(50) NOT NULL,
    _loaded_at      TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    _source_data    VARIANT NOT NULL  -- Raw JSON from API
);
```

### RAW.indigital_events

```sql
CREATE TABLE RAW.indigital_events (
    _raw_id         INTEGER AUTOINCREMENT PRIMARY KEY,
    _tenant_id      VARCHAR(50) NOT NULL,
    _loaded_at      TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    _source_data    VARIANT NOT NULL
);
```

*Similar pattern for other entities*

---

*Document will be updated as inDigital API details are confirmed.*
