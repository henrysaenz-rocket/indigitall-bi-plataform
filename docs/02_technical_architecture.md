# Technical Architecture Document
## inDigital Analytics Platform

**Document Owner:** Abstract Studio
**Version:** 1.0
**Date:** December 2025
**Status:** Draft

---

## 1. Architecture Overview

### 1.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           END USERS                                      │
│                  (inDigital's Client Employees)                          │
└─────────────────────────────────────────────────────────────────────────┘
                                   │
                                   │ HTTPS
                                   ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        INDIGITAL CRM                                     │
│                                                                          │
│   ┌──────────────────────────────────────────────────────────────────┐  │
│   │  iframe: https://analytics.abstractstudio.co/?token={jwt}       │  │
│   └──────────────────────────────────────────────────────────────────┘  │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
                                   │
                                   │ HTTPS (iframe)
                                   ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     PRESENTATION LAYER                                   │
│                     (Streamlit Application)                              │
│                                                                          │
│   Host: analytics.abstractstudio.co                                    │
│   Runtime: Docker on AWS ECS / GCP Cloud Run                            │
│                                                                          │
│   ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐        │
│   │   AI Chat       │  │   Dashboards    │  │  Saved Analyses │        │
│   │   Interface     │  │   & Charts      │  │  & Exports      │        │
│   └─────────────────┘  └─────────────────┘  └─────────────────┘        │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
                                   │
                    ┌──────────────┼──────────────┐
                    │              │              │
                    ▼              ▼              ▼
┌─────────────────────┐ ┌─────────────────┐ ┌─────────────────────────────┐
│    AI SERVICE       │ │   SNOWFLAKE     │ │    DATA INGESTION           │
│                     │ │                 │ │    (n8n)                    │
│  ┌───────────────┐  │ │  ┌───────────┐  │ │                             │
│  │ Claude API    │  │ │  │ Query     │  │ │  ┌─────────────────────┐   │
│  │ (Anthropic)   │  │ │  │ Engine    │  │ │  │  Scheduled Syncs    │   │
│  └───────────────┘  │ │  └───────────┘  │ │  │  (every 15 min)     │   │
│         OR          │ │                 │ │  └─────────────────────┘   │
│  ┌───────────────┐  │ │  ┌───────────┐  │ │             │              │
│  │ Snowflake     │  │ │  │ Data      │  │ │             ▼              │
│  │ Cortex        │  │ │  │ Storage   │  │ │  ┌─────────────────────┐   │
│  └───────────────┘  │ │  └───────────┘  │ │  │  inDigital API      │   │
│                     │ │                 │ │  └─────────────────────┘   │
└─────────────────────┘ └─────────────────┘ └─────────────────────────────┘
```

### 1.2 Component Summary

| Component | Technology | Purpose |
|-----------|------------|---------|
| Presentation Layer | Streamlit (Python) | User interface, charts, chat |
| AI Service | Claude API or Snowflake Cortex | Natural language to SQL |
| Data Warehouse | Snowflake | Data storage, querying, security |
| Data Ingestion | n8n | ETL from inDigital API |
| Hosting | AWS ECS or GCP Cloud Run | Container hosting |
| Secrets Management | AWS Secrets Manager / GCP Secret Manager | API keys, credentials |

---

## 2. Component Details

### 2.1 Presentation Layer (Streamlit)

#### Technology Stack

| Component | Choice | Rationale |
|-----------|--------|-----------|
| Framework | Streamlit 1.x | Fast development, Python native, good charts |
| Charts | Plotly | Interactive, professional quality |
| State Management | Streamlit session state | Simple, sufficient for use case |
| Styling | Custom CSS | White-label requirements |

#### Application Structure

```
streamlit_app/
├── app.py                    # Main entry point
├── config/
│   ├── settings.py           # Configuration management
│   └── branding.py           # White-label settings
├── components/
│   ├── chat.py               # AI chat interface
│   ├── dashboard.py          # Dashboard layouts
│   ├── charts.py             # Chart generation
│   └── export.py             # Export functionality
├── services/
│   ├── auth.py               # JWT validation
│   ├── ai_agent.py           # NL-to-SQL logic
│   ├── snowflake.py          # Database connection
│   └── saved_analyses.py     # CRUD for saved analyses
├── utils/
│   ├── sql_validator.py      # SQL safety checks
│   └── chart_selector.py     # Auto chart type selection
├── static/
│   └── styles.css            # Custom styling
├── Dockerfile
└── requirements.txt
```

#### Key Code Patterns

**Authentication (services/auth.py):**

```python
import jwt
from functools import wraps
import streamlit as st

class AuthService:
    def __init__(self, secret_key: str):
        self.secret_key = secret_key

    def validate_token(self, token: str) -> dict:
        """Validate JWT and extract tenant context."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return {
                'tenant_id': payload['tenant_id'],
                'user_id': payload['user_id'],
                'user_name': payload.get('user_name', 'User'),
                'partner_id': payload.get('partner_id', 'indigital'),
            }
        except jwt.ExpiredSignatureError:
            raise AuthError("Token expired")
        except jwt.InvalidTokenError:
            raise AuthError("Invalid token")

    def get_current_tenant(self) -> str:
        """Get tenant_id from session."""
        return st.session_state.get('tenant_id')
```

**AI Agent (services/ai_agent.py):**

```python
from anthropic import Anthropic
from snowflake.connector import connect

class AIAgent:
    def __init__(self, anthropic_key: str, snowflake_conn):
        self.client = Anthropic(api_key=anthropic_key)
        self.db = snowflake_conn

    def generate_sql(self, question: str, tenant_id: str) -> str:
        """Convert natural language to SQL."""
        schema_context = self._get_schema_context(tenant_id)

        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            system=f"""You are a SQL expert. Generate Snowflake SQL queries.

SCHEMA:
{schema_context}

RULES:
1. ALWAYS include: WHERE tenant_id = '{tenant_id}'
2. LIMIT results to 10000 rows max
3. Use clear column aliases
4. Only SELECT queries allowed
5. Never use DELETE, UPDATE, INSERT, DROP""",
            messages=[{"role": "user", "content": question}]
        )

        sql = self._extract_sql(response.content[0].text)
        self._validate_sql(sql, tenant_id)
        return sql

    def _validate_sql(self, sql: str, tenant_id: str):
        """Security validation of generated SQL."""
        sql_upper = sql.upper()

        # Block dangerous operations
        forbidden = ['DELETE', 'UPDATE', 'INSERT', 'DROP', 'TRUNCATE', 'ALTER']
        for keyword in forbidden:
            if keyword in sql_upper:
                raise SecurityError(f"Forbidden operation: {keyword}")

        # Ensure tenant filter present
        if f"tenant_id = '{tenant_id}'" not in sql.lower():
            raise SecurityError("Missing tenant filter")
```

#### Deployment Configuration

**Dockerfile:**

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 8501

# Health check
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

# Run Streamlit
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

**requirements.txt:**

```
streamlit>=1.28.0
snowflake-connector-python>=3.0.0
anthropic>=0.18.0
plotly>=5.18.0
pandas>=2.0.0
PyJWT>=2.8.0
python-dotenv>=1.0.0
```

---

### 2.2 Snowflake Data Warehouse

#### Database Structure

```
ANALYTICS_PLATFORM (Account)
│
├── INDIGITAL_DB (Database)
│   │
│   ├── RAW (Schema)
│   │   ├── indigital_users
│   │   ├── indigital_events
│   │   ├── indigital_transactions
│   │   ├── indigital_campaigns
│   │   └── indigital_messages
│   │
│   ├── STAGING (Schema)
│   │   ├── stg_contacts
│   │   ├── stg_activities
│   │   ├── stg_messages
│   │   └── stg_campaigns
│   │
│   ├── MARTS (Schema)
│   │   ├── dim_contacts
│   │   ├── dim_campaigns
│   │   ├── fct_activities
│   │   └── fct_messages
│   │
│   └── ADMIN (Schema)
│       ├── tenants
│       ├── partners
│       ├── saved_analyses
│       ├── analysis_executions
│       ├── sync_state
│       └── audit_log
│
├── WAREHOUSE: ANALYTICS_WH (X-Small)
│
└── ROLES
    ├── PLATFORM_ADMIN
    ├── PARTNER_INDIGITAL
    └── (Dynamic tenant roles)
```

#### Row-Level Security Implementation

```sql
-- 1. Create row access policy
CREATE OR REPLACE ROW ACCESS POLICY ADMIN.tenant_data_policy
AS (tenant_id VARCHAR) RETURNS BOOLEAN ->
    -- Check if tenant matches session context
    tenant_id = CURRENT_SESSION_CONTEXT('tenant_id')::VARCHAR
    -- Or if user is platform admin
    OR IS_ROLE_IN_SESSION('PLATFORM_ADMIN')
    -- Or if user is partner admin for this tenant
    OR EXISTS (
        SELECT 1 FROM ADMIN.tenants t
        WHERE t.tenant_id = tenant_id
        AND t.partner_id = CURRENT_SESSION_CONTEXT('partner_id')::VARCHAR
        AND IS_ROLE_IN_SESSION('PARTNER_ADMIN')
    );

-- 2. Apply to all data tables
ALTER TABLE MARTS.dim_contacts
    ADD ROW ACCESS POLICY ADMIN.tenant_data_policy ON (tenant_id);
ALTER TABLE MARTS.fct_activities
    ADD ROW ACCESS POLICY ADMIN.tenant_data_policy ON (tenant_id);
ALTER TABLE MARTS.fct_messages
    ADD ROW ACCESS POLICY ADMIN.tenant_data_policy ON (tenant_id);
ALTER TABLE MARTS.dim_campaigns
    ADD ROW ACCESS POLICY ADMIN.tenant_data_policy ON (tenant_id);

-- 3. Set session context when user connects
-- (Called by application before queries)
ALTER SESSION SET SESSION_CONTEXT = '{
    "tenant_id": "acme_corp",
    "partner_id": "indigital",
    "user_id": "user@acme.com"
}';
```

#### Key Tables

**ADMIN.tenants:**

```sql
CREATE TABLE ADMIN.tenants (
    tenant_id           VARCHAR(50) PRIMARY KEY,
    tenant_name         VARCHAR(255) NOT NULL,
    partner_id          VARCHAR(50) NOT NULL,
    source_tenant_id    VARCHAR(100),          -- ID in inDigital system
    is_active           BOOLEAN DEFAULT TRUE,
    created_at          TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    config              VARIANT,               -- Custom settings

    CONSTRAINT fk_partner FOREIGN KEY (partner_id)
        REFERENCES ADMIN.partners(partner_id)
);
```

**ADMIN.saved_analyses:**

```sql
CREATE TABLE ADMIN.saved_analyses (
    analysis_id         VARCHAR(50) PRIMARY KEY DEFAULT UUID_STRING(),
    tenant_id           VARCHAR(50) NOT NULL,
    created_by          VARCHAR(100) NOT NULL,

    -- Analysis definition
    name                VARCHAR(255) NOT NULL,
    description         TEXT,
    natural_language_query VARCHAR(2000),
    generated_sql       TEXT NOT NULL,

    -- Visualization
    chart_type          VARCHAR(50),
    chart_config        VARIANT,

    -- Scheduling
    refresh_schedule    VARCHAR(50),           -- Cron expression
    last_refresh_at     TIMESTAMP_NTZ,
    next_refresh_at     TIMESTAMP_NTZ,
    is_active           BOOLEAN DEFAULT TRUE,

    -- Results
    latest_result_url   VARCHAR(500),

    -- Metadata
    created_at          TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    updated_at          TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),

    CONSTRAINT fk_tenant FOREIGN KEY (tenant_id)
        REFERENCES ADMIN.tenants(tenant_id)
);
```

**ADMIN.audit_log:**

```sql
CREATE TABLE ADMIN.audit_log (
    log_id              VARCHAR(50) PRIMARY KEY DEFAULT UUID_STRING(),
    tenant_id           VARCHAR(50),
    user_id             VARCHAR(100),
    action              VARCHAR(50),           -- 'query', 'export', 'save', 'login'
    details             VARIANT,               -- Query text, parameters, etc.
    ip_address          VARCHAR(50),
    user_agent          VARCHAR(500),
    created_at          TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);
```

#### Scheduled Tasks

```sql
-- Task to refresh saved analyses
CREATE OR REPLACE TASK ADMIN.refresh_saved_analyses
    WAREHOUSE = ANALYTICS_WH
    SCHEDULE = 'USING CRON */15 * * * * UTC'  -- Every 15 minutes
AS
CALL ADMIN.sp_refresh_due_analyses();

-- Stored procedure for refresh logic
CREATE OR REPLACE PROCEDURE ADMIN.sp_refresh_due_analyses()
RETURNS VARCHAR
LANGUAGE SQL
AS
$$
DECLARE
    analysis RECORD;
    result_count INTEGER;
BEGIN
    -- Find analyses due for refresh
    FOR analysis IN (
        SELECT analysis_id, tenant_id, generated_sql, name
        FROM ADMIN.saved_analyses
        WHERE is_active = TRUE
          AND refresh_schedule IS NOT NULL
          AND next_refresh_at <= CURRENT_TIMESTAMP()
    ) DO
        BEGIN
            -- Set tenant context
            ALTER SESSION SET SESSION_CONTEXT =
                '{"tenant_id": "' || analysis.tenant_id || '"}';

            -- Execute and count results
            EXECUTE IMMEDIATE 'SELECT COUNT(*) FROM (' || analysis.generated_sql || ')';

            -- Update last refresh
            UPDATE ADMIN.saved_analyses
            SET last_refresh_at = CURRENT_TIMESTAMP(),
                next_refresh_at = -- Calculate next based on cron
            WHERE analysis_id = analysis.analysis_id;

        EXCEPTION WHEN OTHER THEN
            -- Log error but continue
            INSERT INTO ADMIN.audit_log (tenant_id, action, details)
            VALUES (analysis.tenant_id, 'refresh_error',
                    OBJECT_CONSTRUCT('analysis_id', analysis.analysis_id,
                                     'error', SQLERRM));
        END;
    END FOR;

    RETURN 'Completed';
END;
$$;

-- Enable the task
ALTER TASK ADMIN.refresh_saved_analyses RESUME;
```

---

### 2.3 Data Ingestion (n8n)

#### Workflow Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           n8n WORKFLOWS                                  │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  WORKFLOW: indigital_users_sync                                 │    │
│  │                                                                 │    │
│  │  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐     │    │
│  │  │ Schedule │ → │ Get Sync │ → │ Fetch    │ → │Transform │     │    │
│  │  │ Trigger  │   │ State    │   │ API Data │   │ Data     │     │    │
│  │  │ (15 min) │   │          │   │          │   │          │     │    │
│  │  └──────────┘   └──────────┘   └──────────┘   └──────────┘     │    │
│  │                                                     │           │    │
│  │                                                     ▼           │    │
│  │                 ┌──────────┐   ┌──────────┐   ┌──────────┐     │    │
│  │                 │ Update   │ ← │ Load to  │ ← │ Validate │     │    │
│  │                 │ Sync     │   │ Snowflake│   │ Records  │     │    │
│  │                 │ State    │   │          │   │          │     │    │
│  │                 └──────────┘   └──────────┘   └──────────┘     │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  Similar workflows for: events, transactions, campaigns, messages       │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

#### Workflow Configuration

```json
{
  "name": "indigital_users_sync",
  "nodes": [
    {
      "name": "Schedule Trigger",
      "type": "n8n-nodes-base.scheduleTrigger",
      "parameters": {
        "rule": {
          "interval": [{"field": "minutes", "minutesInterval": 15}]
        }
      }
    },
    {
      "name": "Get Sync State",
      "type": "n8n-nodes-base.snowflake",
      "parameters": {
        "operation": "executeQuery",
        "query": "SELECT last_cursor FROM ADMIN.sync_state WHERE source_id = 'indigital' AND entity = 'users' AND tenant_id = '{{$json.tenant_id}}'"
      }
    },
    {
      "name": "Fetch inDigital Users",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "url": "https://api.indigital.com/v1/users",
        "method": "GET",
        "authentication": "predefinedCredentialType",
        "queryParameters": {
          "updated_since": "={{$node['Get Sync State'].json.last_cursor}}",
          "limit": 1000
        },
        "options": {
          "pagination": {
            "paginationMode": "cursor",
            "cursorProperty": "pagination.cursor",
            "stopCondition": "={{!$json.pagination.has_more}}"
          }
        }
      }
    },
    {
      "name": "Transform Data",
      "type": "n8n-nodes-base.code",
      "parameters": {
        "jsCode": `
          return items.map(item => ({
            json: {
              _tenant_id: $env.CURRENT_TENANT_ID,
              _loaded_at: new Date().toISOString(),
              _source_data: item.json
            }
          }));
        `
      }
    },
    {
      "name": "Load to Snowflake",
      "type": "n8n-nodes-base.snowflake",
      "parameters": {
        "operation": "insert",
        "table": "RAW.indigital_users",
        "columns": "_tenant_id, _loaded_at, _source_data"
      }
    },
    {
      "name": "Update Sync State",
      "type": "n8n-nodes-base.snowflake",
      "parameters": {
        "operation": "executeQuery",
        "query": "MERGE INTO ADMIN.sync_state..."
      }
    }
  ]
}
```

#### Multi-Tenant Sync Strategy

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     TENANT SYNC ORCHESTRATION                            │
│                                                                          │
│  Master Workflow (runs every 15 min):                                   │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  1. Query ADMIN.tenants WHERE is_active = TRUE                  │    │
│  │  2. For each tenant:                                            │    │
│  │     - Get tenant API credentials from secrets                   │    │
│  │     - Trigger entity sync workflows with tenant context         │    │
│  │  3. Log completion to ADMIN.audit_log                           │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  Entity Workflows (triggered per tenant):                               │
│  • indigital_users_sync                                                 │
│  • indigital_events_sync                                                │
│  • indigital_transactions_sync                                          │
│  • indigital_messages_sync                                              │
│  • indigital_campaigns_sync (full refresh, hourly)                      │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

### 2.4 AI Service Options

#### Option A: Claude API (Anthropic)

**Pros:**
- Most capable for complex NL understanding
- Best at following complex instructions
- Consistent output quality

**Cons:**
- External API dependency
- Cost per request (~$0.01-0.05 per query)
- Latency (~1-3 seconds)

**Implementation:**

```python
from anthropic import Anthropic

class ClaudeAIService:
    def __init__(self, api_key: str):
        self.client = Anthropic(api_key=api_key)

    def generate_sql(self, question: str, schema: str, tenant_id: str) -> str:
        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            system=self._build_system_prompt(schema, tenant_id),
            messages=[{"role": "user", "content": question}]
        )
        return self._extract_sql(response.content[0].text)
```

#### Option B: Snowflake Cortex

**Pros:**
- No external dependency
- Data never leaves Snowflake
- Lower latency for simple queries
- Cost included in Snowflake compute

**Cons:**
- Less capable than Claude for complex queries
- Limited model options
- Newer, less battle-tested

**Implementation:**

```python
class CortexAIService:
    def __init__(self, snowflake_conn):
        self.conn = snowflake_conn

    def generate_sql(self, question: str, schema: str, tenant_id: str) -> str:
        prompt = self._build_prompt(question, schema, tenant_id)

        result = self.conn.cursor().execute(f"""
            SELECT SNOWFLAKE.CORTEX.COMPLETE(
                'mistral-large',
                '{prompt.replace("'", "''")}'
            )
        """).fetchone()

        return self._extract_sql(result[0])
```

#### Recommendation: Hybrid Approach

```python
class HybridAIService:
    """Use Cortex for simple queries, Claude for complex ones."""

    def __init__(self, cortex_service, claude_service):
        self.cortex = cortex_service
        self.claude = claude_service

    def generate_sql(self, question: str, schema: str, tenant_id: str) -> str:
        complexity = self._assess_complexity(question)

        if complexity == 'simple':
            # Use Cortex (faster, cheaper)
            return self.cortex.generate_sql(question, schema, tenant_id)
        else:
            # Use Claude (more capable)
            return self.claude.generate_sql(question, schema, tenant_id)

    def _assess_complexity(self, question: str) -> str:
        """Assess query complexity based on keywords."""
        complex_indicators = [
            'compare', 'trend', 'correlation', 'predict',
            'cohort', 'segment', 'between', 'versus'
        ]
        if any(ind in question.lower() for ind in complex_indicators):
            return 'complex'
        return 'simple'
```

---

## 3. Authentication Flow

### 3.1 JWT Token Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        AUTHENTICATION FLOW                               │
│                                                                          │
│  1. User logs into inDigital CRM                                        │
│     └─► inDigital authenticates user against their system               │
│                                                                          │
│  2. User navigates to Analytics tab                                     │
│     └─► inDigital frontend calls: GET /api/analytics-token              │
│                                                                          │
│  3. inDigital backend generates JWT:                                    │
│     ┌─────────────────────────────────────────────────────────────┐     │
│     │  {                                                          │     │
│     │    "tenant_id": "acme_corp",                                │     │
│     │    "user_id": "maria@acmecorp.com",                         │     │
│     │    "user_name": "Maria Garcia",                             │     │
│     │    "partner_id": "indigital",                               │     │
│     │    "roles": ["analyst"],                                    │     │
│     │    "iat": 1704067200,                                       │     │
│     │    "exp": 1704070800  // 1 hour                             │     │
│     │  }                                                          │     │
│     │  Signed with: SHARED_SECRET (known to both parties)         │     │
│     └─────────────────────────────────────────────────────────────┘     │
│                                                                          │
│  4. inDigital loads iframe:                                             │
│     <iframe src="https://analytics.abstractstudio.co/?token=eyJ...">           │
│                                                                          │
│  5. Streamlit app validates token:                                      │
│     └─► Extracts tenant_id, sets session context                        │
│     └─► Sets Snowflake session: tenant_id = 'acme_corp'                 │
│                                                                          │
│  6. All queries automatically filtered by tenant_id                     │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Token Specification

| Claim | Type | Required | Description |
|-------|------|----------|-------------|
| `tenant_id` | string | Yes | Unique tenant identifier |
| `user_id` | string | Yes | User's email or ID |
| `user_name` | string | No | Display name |
| `partner_id` | string | Yes | Partner identifier (e.g., 'indigital') |
| `roles` | array | No | User roles for authorization |
| `iat` | integer | Yes | Issued at timestamp |
| `exp` | integer | Yes | Expiration timestamp |

### 3.3 Token Refresh Strategy

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        TOKEN REFRESH                                     │
│                                                                          │
│  Token lifetime: 1 hour                                                 │
│                                                                          │
│  Refresh approach:                                                      │
│  • Streamlit app checks token expiration on each request                │
│  • If < 10 minutes remaining, notify parent frame                       │
│  • Parent frame (inDigital) generates new token                         │
│  • Parent posts new token to iframe via postMessage                     │
│  • Streamlit app updates session with new token                         │
│                                                                          │
│  // In Streamlit (JavaScript component)                                 │
│  window.addEventListener('message', (event) => {                        │
│    if (event.data.type === 'TOKEN_REFRESH') {                           │
│      updateToken(event.data.token);                                     │
│    }                                                                    │
│  });                                                                    │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Security Architecture

### 4.1 Security Layers

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        SECURITY LAYERS                                   │
│                                                                          │
│  Layer 1: Network Security                                              │
│  ├── HTTPS only (TLS 1.3)                                               │
│  ├── WAF (AWS WAF / Cloudflare)                                         │
│  └── DDoS protection                                                    │
│                                                                          │
│  Layer 2: Authentication                                                │
│  ├── JWT validation                                                     │
│  ├── Token expiration enforcement                                       │
│  └── Signature verification                                             │
│                                                                          │
│  Layer 3: Authorization                                                 │
│  ├── Tenant context extraction                                          │
│  ├── Role-based access control                                          │
│  └── Row-level security in Snowflake                                    │
│                                                                          │
│  Layer 4: Data Security                                                 │
│  ├── Encryption at rest (AES-256)                                       │
│  ├── Encryption in transit (TLS)                                        │
│  └── PII minimization                                                   │
│                                                                          │
│  Layer 5: Application Security                                          │
│  ├── SQL injection prevention                                           │
│  ├── Input validation                                                   │
│  └── Output encoding                                                    │
│                                                                          │
│  Layer 6: Audit & Monitoring                                            │
│  ├── All queries logged                                                 │
│  ├── Anomaly detection                                                  │
│  └── Access alerts                                                      │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 4.2 SQL Injection Prevention

```python
class SQLValidator:
    """Validate AI-generated SQL for security."""

    FORBIDDEN_KEYWORDS = [
        'DELETE', 'UPDATE', 'INSERT', 'DROP', 'TRUNCATE',
        'ALTER', 'CREATE', 'GRANT', 'REVOKE', 'EXECUTE'
    ]

    REQUIRED_PATTERNS = [
        r"tenant_id\s*=\s*'[^']+'"  # Must have tenant filter
    ]

    def validate(self, sql: str, tenant_id: str) -> bool:
        sql_upper = sql.upper()

        # Check forbidden keywords
        for keyword in self.FORBIDDEN_KEYWORDS:
            if keyword in sql_upper:
                raise SecurityError(f"Forbidden keyword: {keyword}")

        # Check required patterns
        for pattern in self.REQUIRED_PATTERNS:
            if not re.search(pattern, sql, re.IGNORECASE):
                raise SecurityError("Missing required filter")

        # Verify tenant_id matches
        if f"'{tenant_id}'" not in sql:
            raise SecurityError("Tenant ID mismatch")

        return True
```

### 4.3 Audit Logging

```python
class AuditLogger:
    """Log all user actions for security and compliance."""

    def log_query(self, tenant_id: str, user_id: str, query: str,
                  result_count: int, duration_ms: int):
        self.db.execute("""
            INSERT INTO ADMIN.audit_log
            (tenant_id, user_id, action, details, created_at)
            VALUES (%s, %s, 'query', %s, CURRENT_TIMESTAMP())
        """, [
            tenant_id,
            user_id,
            json.dumps({
                'query': query[:1000],  # Truncate long queries
                'result_count': result_count,
                'duration_ms': duration_ms
            })
        ])

    def log_export(self, tenant_id: str, user_id: str,
                   format: str, row_count: int):
        # Similar logging for exports
        pass

    def log_login(self, tenant_id: str, user_id: str,
                  ip_address: str, user_agent: str):
        # Log authentication events
        pass
```

---

## 5. Infrastructure

### 5.1 Deployment Architecture (AWS)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        AWS INFRASTRUCTURE                                │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                         VPC                                     │    │
│  │                                                                 │    │
│  │  ┌─────────────────┐    ┌─────────────────┐                    │    │
│  │  │ Public Subnet   │    │ Public Subnet   │                    │    │
│  │  │ (AZ-a)          │    │ (AZ-b)          │                    │    │
│  │  │                 │    │                 │                    │    │
│  │  │ ┌─────────────┐ │    │ ┌─────────────┐ │                    │    │
│  │  │ │     ALB     │ │    │ │     ALB     │ │                    │    │
│  │  │ └─────────────┘ │    │ └─────────────┘ │                    │    │
│  │  └────────┬────────┘    └────────┬────────┘                    │    │
│  │           │                      │                              │    │
│  │  ┌────────┴──────────────────────┴────────┐                    │    │
│  │  │           Private Subnet                │                    │    │
│  │  │                                         │                    │    │
│  │  │  ┌─────────────────────────────────┐   │                    │    │
│  │  │  │          ECS Cluster            │   │                    │    │
│  │  │  │                                 │   │                    │    │
│  │  │  │  ┌─────────┐    ┌─────────┐    │   │                    │    │
│  │  │  │  │Streamlit│    │Streamlit│    │   │                    │    │
│  │  │  │  │Container│    │Container│    │   │                    │    │
│  │  │  │  │  (x2)   │    │  (x2)   │    │   │                    │    │
│  │  │  │  └─────────┘    └─────────┘    │   │                    │    │
│  │  │  └─────────────────────────────────┘   │                    │    │
│  │  │                                         │                    │    │
│  │  │  ┌─────────────────────────────────┐   │                    │    │
│  │  │  │         n8n (ECS)               │   │                    │    │
│  │  │  └─────────────────────────────────┘   │                    │    │
│  │  └─────────────────────────────────────────┘                    │    │
│  │                                                                 │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  External Services:                                                     │
│  ├── Snowflake (Managed)                                                │
│  ├── Claude API (Anthropic)                                             │
│  ├── Secrets Manager                                                    │
│  └── CloudWatch (Monitoring)                                            │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 5.2 Environment Configuration

| Environment | Purpose | Snowflake DB | URL |
|-------------|---------|--------------|-----|
| Development | Engineering testing | INDIGITAL_DEV | dev.analytics.abstractstudio.co |
| Staging | QA and UAT | INDIGITAL_STAGING | staging.analytics.abstractstudio.co |
| Production | Live traffic | INDIGITAL_PROD | analytics.abstractstudio.co |

### 5.3 Scaling Strategy

| Component | Scaling Trigger | Target |
|-----------|-----------------|--------|
| Streamlit containers | CPU > 70% | 2-10 instances |
| Snowflake warehouse | Query queue > 5 | Auto-scale (X-Small → Medium) |
| n8n | Not scaled | Single instance (stateful) |

---

## 6. Monitoring & Observability

### 6.1 Key Metrics

| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| API response time (P95) | < 3s | > 5s |
| Query response time (P95) | < 5s | > 10s |
| Error rate | < 1% | > 5% |
| Availability | 99.5% | < 99% |
| Active users (daily) | - | < 50% of baseline |

### 6.2 Monitoring Stack

| Tool | Purpose |
|------|---------|
| CloudWatch | AWS infrastructure metrics |
| Snowflake Query History | Database performance |
| Application logs | Error tracking, debugging |
| Custom dashboard | Business metrics |

### 6.3 Alerting

| Alert | Condition | Notification |
|-------|-----------|--------------|
| High error rate | > 5% errors in 5 min | Slack + PagerDuty |
| Slow queries | P95 > 10s for 10 min | Slack |
| Service down | Health check failed | PagerDuty |
| Security anomaly | Unusual access pattern | Email + Slack |

---

## 7. Disaster Recovery

### 7.1 Backup Strategy

| Data | Backup Method | Frequency | Retention |
|------|---------------|-----------|-----------|
| Snowflake data | Time Travel | Continuous | 90 days |
| Snowflake schemas | Fail-safe | Continuous | 7 days beyond Time Travel |
| n8n workflows | Git repository | On change | Indefinite |
| Configuration | Infrastructure as Code | On change | Indefinite |

### 7.2 Recovery Procedures

| Scenario | RTO | RPO | Procedure |
|----------|-----|-----|-----------|
| Container failure | 5 min | 0 | Auto-restart by ECS |
| Database corruption | 1 hour | 1 hour | Restore from Time Travel |
| Region failure | 4 hours | 1 hour | Failover to DR region |
| Complete data loss | 24 hours | 1 hour | Restore from backup |

---

## 8. Cost Estimates

### 8.1 Monthly Infrastructure Costs

| Component | Configuration | Estimated Cost |
|-----------|---------------|----------------|
| Snowflake | X-Small warehouse, 1TB storage | $300-500 |
| AWS ECS | 2x t3.medium (Streamlit) | $60 |
| AWS ECS | 1x t3.small (n8n) | $15 |
| AWS ALB | Load balancer | $20 |
| Claude API | ~10,000 queries/month | $100-500 |
| AWS Secrets Manager | Secrets storage | $5 |
| CloudWatch | Monitoring | $20 |
| **Total** | | **$520-1,120/month** |

### 8.2 Cost Optimization

| Optimization | Savings |
|--------------|---------|
| Use Snowflake Cortex instead of Claude | $100-400/month |
| Auto-suspend warehouse after 1 min | 30-50% compute |
| Reserved capacity (1 year) | 30% on AWS |

---

## 9. Appendix

### A. API Reference (Internal)

See separate API documentation.

### B. Database Schema Diagrams

See Data Mapping Document.

### C. Sequence Diagrams

See separate technical diagrams.

---

*Document maintained by Abstract Studio Engineering Team*
