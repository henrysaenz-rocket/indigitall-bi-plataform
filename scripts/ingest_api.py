#!/usr/bin/env python3
"""
ingest_api.py — CLI tool to ingest data from REST APIs into the BI platform.

Usage:
    # Demo mode (uses local mock JSON files)
    python scripts/ingest_api.py --demo --table messages --tenant demo

    # Real API ingestion
    python scripts/ingest_api.py \
        --api-url https://api.indigitall.com/v1/stats/send/count \
        --api-key YOUR_KEY --table messages --tenant visionamos \
        --mapping scripts/mappings/messages.json

    # Dry run (shows what would be inserted)
    python scripts/ingest_api.py --demo --table messages --tenant demo --dry-run
"""

import argparse
import json
import sys
import os
from datetime import datetime, timezone
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
from sqlalchemy import text

from app.models.database import engine
from app.config import settings


def load_mapping(mapping_path: str) -> dict:
    """Load a JSON mapping file that defines API field -> DB column transforms."""
    with open(mapping_path) as f:
        return json.load(f)


def load_mock_data(table_name: str) -> list:
    """Load mock JSON data from scripts/mock_data/{table}.json."""
    mock_path = Path(__file__).parent / "mock_data" / f"{table_name}.json"
    if not mock_path.exists():
        print(f"[WARN] Mock data not found: {mock_path}")
        print(f"       Run: python scripts/generate_mock_data.py")
        return []
    with open(mock_path) as f:
        data = json.load(f)
    return data.get("data", data) if isinstance(data, dict) else data


def fetch_api_page(api_url: str, api_key: str, project_id: str,
                   cursor: str = None, page: int = 0, limit: int = 1000) -> dict:
    """Fetch one page of data from the API."""
    import requests

    headers = {
        "X-Api-Key": api_key,
        "X-Project-Id": project_id,
        "Content-Type": "application/json",
    }
    params = {"limit": limit}
    if cursor:
        params["since"] = cursor
    if page > 0:
        params["offset"] = page * limit

    resp = requests.get(api_url, headers=headers, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()


def get_sync_cursor(tenant_id: str, entity: str) -> str | None:
    """Read the last sync cursor from sync_state."""
    query = text(
        "SELECT last_cursor FROM sync_state "
        "WHERE tenant_id = :tid AND entity = :entity"
    )
    with engine.connect() as conn:
        row = conn.execute(query, {"tid": tenant_id, "entity": entity}).first()
    return row.last_cursor if row else None


def update_sync_state(tenant_id: str, entity: str, cursor: str, count: int, status: str):
    """Upsert the sync_state row."""
    query = text("""
        INSERT INTO sync_state (tenant_id, entity, last_cursor, last_sync_at, records_synced, status)
        VALUES (:tid, :entity, :cursor, NOW(), :count, :status)
        ON CONFLICT (tenant_id, entity) DO UPDATE SET
            last_cursor = EXCLUDED.last_cursor,
            last_sync_at = NOW(),
            records_synced = EXCLUDED.records_synced,
            status = EXCLUDED.status
    """)
    with engine.begin() as conn:
        conn.execute(query, {
            "tid": tenant_id, "entity": entity,
            "cursor": cursor, "count": count, "status": status,
        })


def apply_mapping(records: list, mapping: dict, tenant_id: str) -> list:
    """Transform API records using mapping config."""
    field_map = mapping.get("fields", {})
    defaults = mapping.get("defaults", {})
    transforms = mapping.get("transforms", {})

    mapped = []
    for rec in records:
        row = {"tenant_id": tenant_id}
        # Apply field mapping
        for api_field, db_col in field_map.items():
            row[db_col] = rec.get(api_field)

        # Apply defaults for missing fields
        for col, default_val in defaults.items():
            if col not in row or row[col] is None:
                row[col] = default_val

        # Apply transforms
        for col, transform in transforms.items():
            if col in row and row[col] is not None:
                if transform == "lowercase":
                    row[col] = str(row[col]).lower()
                elif transform == "date_only":
                    row[col] = str(row[col])[:10]
                elif transform == "bool":
                    row[col] = bool(row[col])
                elif transform == "int":
                    try:
                        row[col] = int(row[col])
                    except (ValueError, TypeError):
                        row[col] = 0

        mapped.append(row)
    return mapped


def insert_records(table_name: str, records: list, dry_run: bool = False):
    """Insert records into the target table."""
    if not records:
        print("[INFO] No records to insert.")
        return 0

    df = pd.DataFrame(records)
    print(f"[INFO] {'DRY RUN - ' if dry_run else ''}Inserting {len(df)} records into '{table_name}'")
    print(f"       Columns: {list(df.columns)}")

    if dry_run:
        print(df.head(5).to_string(index=False))
        return len(df)

    # Use pandas to_sql with 'append' for simple insertion
    with engine.begin() as conn:
        df.to_sql(table_name, conn, if_exists="append", index=False, method="multi")

    print(f"[OK] Inserted {len(df)} records into '{table_name}'")
    return len(df)


def main():
    parser = argparse.ArgumentParser(description="Ingest data from REST APIs into the BI platform")
    parser.add_argument("--api-url", help="API endpoint URL")
    parser.add_argument("--api-key", help="API key for authentication")
    parser.add_argument("--table", required=True, help="Target database table name")
    parser.add_argument("--tenant", required=True, help="Tenant ID for multi-tenant isolation")
    parser.add_argument("--mapping", help="Path to JSON mapping file")
    parser.add_argument("--demo", action="store_true", help="Use mock data instead of real API")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be inserted without writing")
    parser.add_argument("--limit", type=int, default=1000, help="Records per page (default: 1000)")
    parser.add_argument("--max-pages", type=int, default=100, help="Max pages to fetch (default: 100)")
    args = parser.parse_args()

    table = args.table
    tenant = args.tenant
    print(f"\n{'='*60}")
    print(f"ingest_api.py — {table} for tenant '{tenant}'")
    print(f"Mode: {'DEMO' if args.demo else 'LIVE API'} {'(DRY RUN)' if args.dry_run else ''}")
    print(f"{'='*60}\n")

    # Load mapping
    mapping = {}
    if args.mapping:
        mapping = load_mapping(args.mapping)
        print(f"[INFO] Loaded mapping: {args.mapping}")
    elif not args.demo:
        # Try default mapping path
        default_path = Path(__file__).parent / "mappings" / f"{table}.json"
        if default_path.exists():
            mapping = load_mapping(str(default_path))
            print(f"[INFO] Loaded default mapping: {default_path}")

    # Set sync state to running
    if not args.dry_run:
        update_sync_state(tenant, table, "", 0, "running")

    total_inserted = 0

    try:
        if args.demo:
            # Demo mode: load mock data
            records = load_mock_data(table)
            if mapping:
                records = apply_mapping(records, mapping, tenant)
            else:
                # Add tenant_id to each record
                for r in records:
                    r["tenant_id"] = tenant
            total_inserted = insert_records(table, records, dry_run=args.dry_run)

        else:
            # Live API mode: paginated fetch
            if not args.api_url or not args.api_key:
                print("[ERROR] --api-url and --api-key are required for live mode")
                sys.exit(1)

            cursor = get_sync_cursor(tenant, table)
            print(f"[INFO] Starting from cursor: {cursor or '(beginning)'}")

            for page in range(args.max_pages):
                print(f"[INFO] Fetching page {page + 1}...")
                response = fetch_api_page(
                    args.api_url, args.api_key, tenant,
                    cursor=cursor, page=page, limit=args.limit,
                )

                # Extract data (handle both list and {data: [...]} formats)
                if isinstance(response, list):
                    page_records = response
                else:
                    page_records = response.get("data", response.get("results", []))

                if not page_records:
                    print(f"[INFO] No more records at page {page + 1}. Done.")
                    break

                if mapping:
                    page_records = apply_mapping(page_records, mapping, tenant)
                else:
                    for r in page_records:
                        r["tenant_id"] = tenant

                count = insert_records(table, page_records, dry_run=args.dry_run)
                total_inserted += count

                # Update cursor for next page
                if isinstance(response, dict):
                    cursor = response.get("next_cursor", response.get("cursor"))
                    if not cursor:
                        break
                else:
                    break

        # Update sync state
        if not args.dry_run:
            new_cursor = datetime.now(timezone.utc).isoformat()
            update_sync_state(tenant, table, new_cursor, total_inserted, "completed")

        print(f"\n[DONE] Total records processed: {total_inserted}")

    except Exception as e:
        print(f"\n[ERROR] {e}")
        if not args.dry_run:
            update_sync_state(tenant, table, "", 0, "error")
        raise


if __name__ == "__main__":
    main()
