"""
Create the 'raw' schema and landing tables for Indigitall API extraction.

Usage:
    docker compose exec app python scripts/create_raw_schema.py
"""

import sys
from pathlib import Path

from sqlalchemy import text

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.models.database import engine

# ---------------------------------------------------------------------------
# DDL statements
# ---------------------------------------------------------------------------

CREATE_SCHEMA = "CREATE SCHEMA IF NOT EXISTS raw"

RAW_TABLES = {
    "extraction_log": """
        CREATE TABLE IF NOT EXISTS raw.extraction_log (
            id              SERIAL PRIMARY KEY,
            application_id  VARCHAR(100),
            tenant_id       VARCHAR(50),
            endpoint        VARCHAR(500) NOT NULL,
            http_status     INTEGER,
            duration_ms     INTEGER,
            error_message   TEXT,
            started_at      TIMESTAMPTZ DEFAULT NOW(),
            finished_at     TIMESTAMPTZ
        )
    """,
    "raw_applications": """
        CREATE TABLE IF NOT EXISTS raw.raw_applications (
            id              SERIAL PRIMARY KEY,
            application_id  VARCHAR(100),
            tenant_id       VARCHAR(50),
            endpoint        VARCHAR(200),
            loaded_at       TIMESTAMPTZ DEFAULT NOW(),
            date_from       DATE,
            date_to         DATE,
            source_data     JSONB NOT NULL
        )
    """,
    "raw_push_stats": """
        CREATE TABLE IF NOT EXISTS raw.raw_push_stats (
            id              SERIAL PRIMARY KEY,
            application_id  VARCHAR(100),
            tenant_id       VARCHAR(50),
            endpoint        VARCHAR(200),
            loaded_at       TIMESTAMPTZ DEFAULT NOW(),
            date_from       DATE,
            date_to         DATE,
            source_data     JSONB NOT NULL
        )
    """,
    "raw_chat_stats": """
        CREATE TABLE IF NOT EXISTS raw.raw_chat_stats (
            id              SERIAL PRIMARY KEY,
            application_id  VARCHAR(100),
            tenant_id       VARCHAR(50),
            endpoint        VARCHAR(200),
            loaded_at       TIMESTAMPTZ DEFAULT NOW(),
            date_from       DATE,
            date_to         DATE,
            source_data     JSONB NOT NULL
        )
    """,
    "raw_sms_stats": """
        CREATE TABLE IF NOT EXISTS raw.raw_sms_stats (
            id              SERIAL PRIMARY KEY,
            application_id  VARCHAR(100),
            tenant_id       VARCHAR(50),
            endpoint        VARCHAR(200),
            loaded_at       TIMESTAMPTZ DEFAULT NOW(),
            date_from       DATE,
            date_to         DATE,
            source_data     JSONB NOT NULL
        )
    """,
    "raw_email_stats": """
        CREATE TABLE IF NOT EXISTS raw.raw_email_stats (
            id              SERIAL PRIMARY KEY,
            application_id  VARCHAR(100),
            tenant_id       VARCHAR(50),
            endpoint        VARCHAR(200),
            loaded_at       TIMESTAMPTZ DEFAULT NOW(),
            date_from       DATE,
            date_to         DATE,
            source_data     JSONB NOT NULL
        )
    """,
    "raw_inapp_stats": """
        CREATE TABLE IF NOT EXISTS raw.raw_inapp_stats (
            id              SERIAL PRIMARY KEY,
            application_id  VARCHAR(100),
            tenant_id       VARCHAR(50),
            endpoint        VARCHAR(200),
            loaded_at       TIMESTAMPTZ DEFAULT NOW(),
            date_from       DATE,
            date_to         DATE,
            source_data     JSONB NOT NULL
        )
    """,
    "raw_campaigns_api": """
        CREATE TABLE IF NOT EXISTS raw.raw_campaigns_api (
            id              SERIAL PRIMARY KEY,
            application_id  VARCHAR(100),
            tenant_id       VARCHAR(50),
            endpoint        VARCHAR(200),
            loaded_at       TIMESTAMPTZ DEFAULT NOW(),
            date_from       DATE,
            date_to         DATE,
            source_data     JSONB NOT NULL
        )
    """,
    "raw_contacts_api": """
        CREATE TABLE IF NOT EXISTS raw.raw_contacts_api (
            id              SERIAL PRIMARY KEY,
            application_id  VARCHAR(100),
            tenant_id       VARCHAR(50),
            endpoint        VARCHAR(200),
            loaded_at       TIMESTAMPTZ DEFAULT NOW(),
            date_from       DATE,
            date_to         DATE,
            source_data     JSONB NOT NULL
        )
    """,
}

INDICES = [
    "CREATE INDEX IF NOT EXISTS idx_extraction_log_endpoint ON raw.extraction_log (endpoint)",
    "CREATE INDEX IF NOT EXISTS idx_extraction_log_started ON raw.extraction_log (started_at DESC)",
    "CREATE INDEX IF NOT EXISTS idx_raw_applications_app ON raw.raw_applications (application_id)",
    "CREATE INDEX IF NOT EXISTS idx_raw_push_stats_app ON raw.raw_push_stats (application_id)",
    "CREATE INDEX IF NOT EXISTS idx_raw_chat_stats_app ON raw.raw_chat_stats (application_id)",
    "CREATE INDEX IF NOT EXISTS idx_raw_sms_stats_app ON raw.raw_sms_stats (application_id)",
    "CREATE INDEX IF NOT EXISTS idx_raw_email_stats_app ON raw.raw_email_stats (application_id)",
    "CREATE INDEX IF NOT EXISTS idx_raw_inapp_stats_app ON raw.raw_inapp_stats (application_id)",
    "CREATE INDEX IF NOT EXISTS idx_raw_campaigns_api_app ON raw.raw_campaigns_api (application_id)",
    "CREATE INDEX IF NOT EXISTS idx_raw_contacts_api_app ON raw.raw_contacts_api (application_id)",
]


def main():
    print("=== Creating raw schema and tables ===\n")

    with engine.begin() as conn:
        # Schema
        conn.execute(text(CREATE_SCHEMA))
        print("  Schema 'raw' created (or already exists)")

        # Tables
        for table_name, ddl in RAW_TABLES.items():
            conn.execute(text(ddl))
            print(f"  Table raw.{table_name} created")

        # Indices
        for idx_sql in INDICES:
            conn.execute(text(idx_sql))
        print(f"\n  {len(INDICES)} indices created")

    print("\n=== Raw schema setup complete ===")


if __name__ == "__main__":
    main()
