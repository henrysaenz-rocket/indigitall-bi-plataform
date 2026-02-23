# Henry's Guide — inDigitall BI Platform

## Overview

This comprehensive guide covers two primary workflows for the inDigitall BI Platform:
1. Modifying the web application (UI, visuals, authentication, pages)
2. Adding new database tables and constructing dashboards

## Part 1: Web App Deployment

### Architecture

The platform uses **Plotly Dash**, a Python-based UI framework. The structure separates layout files (defining page appearance) from callback files (containing interaction logic).

Key directories include:
- `app/layouts/` — Individual page definitions
- `app/callbacks/` — Event handlers and business logic
- `app/services/` — Database queries and external integrations
- `app/middleware/` — Authentication handling
- `app/models/` — Database table definitions

### Common Modification Examples

**Button/Text Changes:** Locate the element in the appropriate layout file under `app/layouts/`, modify the text properties, then test locally via Docker before deploying.

**New Pages:** Create paired files—a layout file defining the visual structure and a callback file containing data-loading logic. Register the callback import in `main.py`.

**Authentication:** The platform supports two modes—development (no login) and JWT token validation. Production implementations extract tenant information from JWT claims stored in cookies or Authorization headers.

### Deployment Process

Changes follow this sequence: commit locally, push to git, execute `deploy.sh` on the GCP VM. The script automatically pulls changes, rebuilds containers, and restarts services.

## Part 2: Data Pipeline (Tables to Dashboards)

A five-step process governs adding new data sources:

### Step 1: Schema Definition

Database tables are defined in `app/models/schemas.py` using SQLAlchemy. Every table requires a `tenant_id` column for multi-tenant support and a `UniqueConstraint` preventing duplicate records.

### Step 2: Field Mapping

Create a JSON mapping file in `scripts/mappings/` specifying how API field names translate to database columns. Support includes default values and type transformations.

### Step 3: Mock Data Generation

Developers create placeholder data via `scripts/generate_mock_data.py`, enabling feature development before actual API credentials arrive.

### Step 4: Data Ingestion

The `ingest_api.py` script loads data using the mapping file, applies transformations, and inserts records into PostgreSQL. It tracks synchronization state for incremental updates.

### Step 5: Visualization

Create dashboards either by adding charts to existing pages or building dedicated pages with Plotly visualizations. The AI Agent automatically queries new tables without additional configuration.

## Key Technologies

- **Framework:** Plotly Dash (Python)
- **Database:** PostgreSQL
- **Containerization:** Docker Compose
- **Deployment:** GCP VMs via gcloud SSH
- **Visualization:** Plotly Express

## Essential Commands Reference

Local development starts with `docker compose up -d`. Data ingestion uses `ingest_api.py` with flags specifying table names and tenant contexts. Production deployment triggers via `deploy.sh` on the remote VM.

## Prerequisites

SSH access to the GCP VM, local repository clone, Docker Desktop, and Python 3.11+ enable full development workflow.
