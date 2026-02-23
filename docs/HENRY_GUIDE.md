# Henry's Guide — inDigitall BI Platform

This guide covers two workflows you'll need regularly:
1. **Making changes to the web app** (UI, visuals, auth, new pages)
2. **Adding new data tables and building dashboards on top of them**

Read this from top to bottom the first time. After that, use it as a reference.

---

## Prerequisites

Make sure you have:
- SSH access to the GCP VM (`gcloud compute ssh indigitall-analytics --project=trax-report-automation --zone=southamerica-east1-a`)
- The repo cloned locally at `Indigital/platform/`
- Docker Desktop running locally for dev testing
- Python 3.11+ (for running scripts outside Docker)

Start local dev with:
```bash
cd Indigital/platform
docker compose up -d
# First time only:
docker compose exec app python scripts/seed_data.py
```

Your local app runs at `http://localhost:8050`.

---

# PART 1: Deploying Web App Changes

## How the app is structured

The platform is a **Plotly Dash** app. Dash is a Python framework where you build UIs in Python (not HTML/JS). Every UI element is a Python object.

```
app/
├── main.py              ← Entry point. Navbar, global layout, callback imports.
├── config.py            ← Settings. Reads from .env file.
├── layouts/             ← Pages. Each file = one page (URL route).
│   ├── home.py          ← /           (KPI cards, favorites, quick actions)
│   ├── query.py         ← /consultas/nueva  (AI chat)
│   ├── query_list.py    ← /consultas  (saved queries list)
│   ├── dashboard_list.py← /tableros   (dashboard list)
│   ├── dashboard_view.py← /tableros/<id>  (single dashboard)
│   └── data_explorer.py ← /datos      (table browser)
├── callbacks/           ← Logic. Each file matches a layout file.
│   ├── home_cb.py
│   ├── query_cb.py
│   ├── query_list_cb.py
│   ├── dashboard_list_cb.py
│   ├── dashboard_view_cb.py
│   └── data_explorer_cb.py
├── services/            ← Business logic (database queries, AI, etc.)
├── middleware/           ← Auth (JWT or dev mode)
├── models/              ← SQLAlchemy table definitions
└── assets/              ← CSS, images (auto-served by Dash)
```

**Key concept:** Dash separates _layout_ (what the page looks like) from _callbacks_ (what happens when the user interacts). A layout file defines the HTML structure. A callback file defines the Python functions that run when someone clicks a button, loads a page, etc.

---

## Example A: Changing a button

Say you want to change the "Nueva Consulta" quick-action card on the home page to have different text.

### Step 1 — Find the layout

The home page is `app/layouts/home.py`. Open it and find the card:

```python
html.H5("Nueva Consulta", className="mt-2 mb-1"),
html.P("Pregunta al asistente IA sobre tus datos",
       className="text-muted small mb-0"),
```

### Step 2 — Make the change

Change the text:

```python
html.H5("Hacer Pregunta", className="mt-2 mb-1"),
html.P("Usa inteligencia artificial para analizar tus datos",
       className="text-muted small mb-0"),
```

### Step 3 — Test locally

```bash
docker compose up -d
```

Open `http://localhost:8050` and verify the change. Dash in debug mode auto-reloads when files change.

### Step 4 — Deploy to production

```bash
# Commit your change
git add app/layouts/home.py
git commit -m "Update home page card text"
git push

# Deploy to GCP VM
gcloud compute ssh indigitall-analytics \
  --project=trax-report-automation \
  --zone=southamerica-east1-a \
  --command="cd /opt/indigitall-analytics && bash scripts/deploy/deploy.sh"
```

`deploy.sh` does 4 things automatically:
1. `git pull` — pulls your latest commit
2. `docker compose build --no-cache app` — rebuilds only the Dash container
3. `docker compose up -d` — restarts services
4. Runs `create_tables()` — creates any new DB tables if you added models

After ~30 seconds, check the production URL to verify.

---

## Example B: Creating a new page with a visual (chart)

Say you want to add a `/reportes` page that shows a bar chart of messages per day.

### Step 1 — Create the layout file

Create `app/layouts/reports.py`:

```python
"""Reports page — Custom visualizations."""

import dash
from dash import html, dcc
import dash_bootstrap_components as dbc

dash.register_page(__name__, path="/reportes", name="Reportes", order=4)

layout = dbc.Container([
    html.H2("Reportes", className="page-title"),
    html.P("Visualizaciones personalizadas.", className="page-subtitle"),

    # The chart — empty initially, filled by callback
    dcc.Graph(id="report-messages-bar", style={"height": "400px"}),
], fluid=True, className="py-4")
```

Important: `dash.register_page(...)` is what registers this file as a page with a URL.

### Step 2 — Create the callback file

Create `app/callbacks/reports_cb.py`:

```python
"""Reports callbacks — load chart data."""

from dash import Input, Output, callback
import plotly.express as px
from sqlalchemy import text

from app.models.database import engine


@callback(
    Output("report-messages-bar", "figure"),
    Input("tenant-context", "data"),
)
def load_messages_chart(tenant):
    query = text("""
        SELECT date, COUNT(*) as count
        FROM messages
        WHERE tenant_id = :tid
        GROUP BY date
        ORDER BY date
    """)
    with engine.connect() as conn:
        rows = conn.execute(query, {"tid": tenant or "demo"}).fetchall()

    dates = [r.date for r in rows]
    counts = [r.count for r in rows]

    fig = px.bar(x=dates, y=counts, labels={"x": "Fecha", "y": "Mensajes"})
    fig.update_layout(template="plotly_white", margin=dict(t=20))
    return fig
```

Every `@callback` connects an **Output** (something on the page to update) to **Inputs** (things that trigger the update). Here, when `tenant-context` changes (on page load), the chart loads.

### Step 3 — Register the callback in main.py

Open `app/main.py` and add this import at the bottom with the other callback imports:

```python
import app.callbacks.reports_cb  # noqa: F401
```

### Step 4 — Add a nav link (optional)

In `app/main.py`, inside the `create_navbar()` function, add a NavItem in the nav list:

```python
dbc.NavItem(dbc.NavLink(
    [html.I(className="bi bi-bar-chart me-1"), "Reportes"],
    href="/reportes", active="exact",
)),
```

### Step 5 — Test and deploy

```bash
# Test locally
docker compose up -d
# Visit http://localhost:8050/reportes

# Deploy
git add app/layouts/reports.py app/callbacks/reports_cb.py app/main.py
git commit -m "Add reports page with messages bar chart"
git push
gcloud compute ssh indigitall-analytics \
  --project=trax-report-automation \
  --zone=southamerica-east1-a \
  --command="cd /opt/indigitall-analytics && bash scripts/deploy/deploy.sh"
```

---

## Example C: Changing authentication

The app has two auth modes, controlled by `AUTH_MODE` in `.env`:

| Mode | What it does | When to use |
|------|-------------|-------------|
| `dev` | No login required. Anyone can access. Tenant set via `?tenant=` query param or defaults to `demo`. | Local development, demos |
| `jwt` | Validates a JWT token from a cookie or `Authorization: Bearer` header. Extracts `project_id` from the token as the tenant. | Production with indigitall SSO |

### To switch to JWT mode in production:

1. SSH into the VM:
   ```bash
   gcloud compute ssh indigitall-analytics --project=trax-report-automation --zone=southamerica-east1-a
   ```

2. Edit the `.env` file:
   ```bash
   cd /opt/indigitall-analytics
   nano .env
   ```

3. Change these values:
   ```
   AUTH_MODE=jwt
   JWT_SECRET_KEY=the-secret-key-from-indigitall
   JWT_COOKIE_NAME=indigitall_token
   ```

4. Restart the app:
   ```bash
   docker compose restart app
   ```

The JWT secret must match whatever indigitall uses to sign their tokens. The cookie name must match the cookie their system sets in the browser.

### How JWT auth works in the code

The auth logic lives in `app/middleware/auth.py`. On every HTTP request:

1. Flask `before_request` hook runs
2. If `AUTH_MODE=jwt`: reads the JWT from the cookie or Authorization header
3. Validates the signature using `JWT_SECRET_KEY`
4. Extracts `project_id` from the JWT claims → sets it as `tenant_id`
5. Extracts `email`, `name`, `role` from claims → sets as `user`
6. All of this goes into Flask's `g` object, accessible from any callback

If you need to customize which JWT claim maps to the tenant, edit this section in `app/middleware/auth.py`:

```python
tenant = (
    claims.get("project_id")
    or claims.get("tenant_id")
    or claims.get("org_id")
    or settings.DEFAULT_TENANT
)
```

### Adding a login page (if needed)

The current JWT mode assumes the token already exists (set by indigitall's login system). If you need a standalone login page:

1. Create `app/layouts/login.py` with a form (email + password fields)
2. Create `app/callbacks/login_cb.py` that posts credentials to an auth API and sets the cookie
3. In `app/middleware/auth.py`, redirect to `/login` when no valid JWT is found (instead of allowing access with default tenant)

---

## CSS and Styling

All styles are in `app/assets/styles.css`. Dash auto-serves everything in the `assets/` folder.

The design system uses CSS variables:
```css
--id-primary: #1E88E5;    /* Blue — primary buttons, links */
--id-secondary: #76C043;  /* Green — success states */
--id-bg-page: #F5F7FA;    /* Light gray background */
--id-bg-card: #FFFFFF;    /* Card backgrounds */
```

To style a component, add a `className` in your Python layout code and define the class in `styles.css`:

```python
# In your layout:
html.Div("Hello", className="my-custom-card")
```

```css
/* In assets/styles.css: */
.my-custom-card {
    background: var(--id-bg-card);
    border-radius: 12px;
    padding: 1.5rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}
```

You also have full access to Bootstrap 5 utility classes (`text-muted`, `mb-3`, `d-flex`, etc.) and Bootstrap Icons (`bi bi-house-door`, `bi bi-search`, etc.).

---

## Deployment checklist

Every time you deploy a change:

- [ ] Test locally first (`docker compose up -d`, check `localhost:8050`)
- [ ] Commit with a descriptive message
- [ ] Push to git
- [ ] Run `deploy.sh` on the VM
- [ ] Check the production URL to verify
- [ ] If something breaks, check logs: `docker compose logs app --tail 50`

---

# PART 2: Adding New Tables + Data Pipeline + Dashboards

This is a 5-step process. Every step builds on the previous one.

```
Step 1          Step 2          Step 3          Step 4          Step 5
Define the  →  Create the   →  Create the   →  Ingest the   →  Build the
table model    mapping file    mock data       data            dashboard
(schemas.py)   (mappings/)     (mock_data/)    (ingest_api)    (layouts/)
```

---

## Step 1: Define the table model

Open `app/models/schemas.py`. This file defines every table in the database. Add your new model following the existing pattern.

Example — adding a `surveys` table:

```python
class Survey(Base):
    __tablename__ = "surveys"

    id = Column(Integer, primary_key=True)
    tenant_id = Column(Text, nullable=False)           # REQUIRED on every table
    survey_id = Column(String(100), nullable=False)
    contact_id = Column(String(100))
    question = Column(Text)
    answer = Column(Text)
    score = Column(SmallInteger)
    submitted_at = Column(TIMESTAMP(timezone=True))
    canal = Column(String(30))

    __table_args__ = (
        UniqueConstraint("tenant_id", "survey_id", name="uq_surveys_tenant_sid"),
        Index("idx_surveys_tenant_date", "tenant_id", "submitted_at"),
    )
```

Rules:
- **Always include `tenant_id`** — every table is multi-tenant
- **Always add a `UniqueConstraint`** — this prevents duplicate records on re-ingestion
- Use the same column types you see in the existing models (`String`, `Integer`, `Date`, `TIMESTAMP`, `Numeric`, `Boolean`, `Text`)

### Register it in `database.py`

Open `app/models/database.py` and add the import in `create_tables()`:

```python
def create_tables():
    from app.models.schemas import (
        Message, Contact, Agent, DailyStat,
        ToquesDaily, Campaign, ToquesHeatmap, ToquesUsuario,
        SavedQuery, Dashboard, SyncState,
        Survey,  # ← add here
    )
    Base.metadata.create_all(bind=engine)
```

### Make it visible in the Data Explorer

Open `app/services/schema_service.py` and add the table name to the whitelist:

```python
ALLOWED_TABLES = {
    "messages", "contacts", "agents", "daily_stats",
    "toques_daily", "campaigns", "toques_heatmap", "toques_usuario",
    "saved_queries", "dashboards", "sync_state",
    "surveys",  # ← add here
}
```

### Make it queryable by the AI Agent

Open `app/services/ai_agent.py` and add it to the allowed tables:

```python
ALLOWED_TABLES = frozenset({
    "messages", "contacts", "agents", "daily_stats",
    "toques_daily", "campaigns", "toques_heatmap", "toques_usuario",
    "surveys",  # ← add here
})
```

### Create the table

Locally:
```bash
docker compose exec app python -c "from app.models.database import create_tables; create_tables()"
```

This is idempotent — it creates new tables without touching existing ones.

---

## Step 2: Create the mapping file

The mapping file tells the ingestion script how to translate API field names into your database column names.

Create `scripts/mappings/surveys.json`:

```json
{
  "description": "Mapping for indigitall Surveys API -> surveys table",
  "api_endpoint": "/v1/surveys",
  "fields": {
    "id": "survey_id",
    "contact": "contact_id",
    "question_text": "question",
    "answer_text": "answer",
    "rating": "score",
    "created_at": "submitted_at",
    "channel": "canal"
  },
  "defaults": {
    "score": 0
  },
  "transforms": {
    "score": "int",
    "canal": "lowercase"
  },
  "notes": "Field names are placeholders — update when API docs arrive"
}
```

The three sections:
- **`fields`**: `"api_field_name": "database_column_name"` — renames fields
- **`defaults`**: fills in values when the API returns null
- **`transforms`**: type conversions applied after mapping
  - `"bool"` — cast to Python bool
  - `"int"` — cast to int (0 on failure)
  - `"date_only"` — take first 10 characters (turns datetime into date)
  - `"lowercase"` — lowercase the string

You don't need to map `tenant_id` — the ingestion script adds it automatically.

---

## Step 3: Create mock data

Until real API credentials arrive, you test with mock data.

Open `scripts/generate_mock_data.py` and add a function for your table:

```python
def generate_surveys(count=100):
    """Generate mock survey responses."""
    records = []
    for i in range(count):
        contact = random.choice(CONTACTS)
        records.append({
            "id": f"survey_{i:04d}",
            "contact": contact["id"],
            "question_text": random.choice([
                "Como califica nuestro servicio?",
                "Recomendaria nuestro producto?",
                "Que tan facil fue usar la app?",
            ]),
            "answer_text": random.choice([
                "Muy bueno", "Bueno", "Regular", "Malo", "Excelente"
            ]),
            "rating": random.randint(1, 5),
            "created_at": (datetime.now() - timedelta(days=random.randint(0, 90))).isoformat(),
            "channel": random.choice(CHANNELS),
        })
    return records
```

Then in the `main()` function at the bottom, add:

```python
save("surveys", generate_surveys())
```

Run it:
```bash
docker compose exec app python scripts/generate_mock_data.py
```

This creates `scripts/mock_data/surveys.json`.

---

## Step 4: Ingest the data

Now load the mock data into your database:

```bash
# Dry run first — see what would be inserted without writing
docker compose exec app python scripts/ingest_api.py \
  --demo --table surveys --tenant demo --dry-run

# If it looks right, run for real
docker compose exec app python scripts/ingest_api.py \
  --demo --table surveys --tenant demo
```

Verify in the Data Explorer: go to `http://localhost:8050/datos` and click the `surveys` table card. You should see the schema, a preview of rows, and profiling stats.

### What happens under the hood

1. `ingest_api.py` loads `scripts/mock_data/surveys.json` (because `--demo`)
2. Loads `scripts/mappings/surveys.json` (auto-detected by table name)
3. Runs `apply_mapping()` — renames fields, applies defaults, runs transforms, adds `tenant_id`
4. Runs `insert_records()` — uses pandas `to_sql()` to bulk insert into PostgreSQL
5. Updates the `sync_state` table — sets status to `completed`, stores timestamp and record count

### When real API credentials arrive

Replace `--demo` with real API parameters:

```bash
docker compose exec app python scripts/ingest_api.py \
  --api-url https://api.indigitall.com/v1/surveys \
  --api-key $INDIGITALL_API_KEY \
  --table surveys \
  --tenant visionamos \
  --dry-run
```

The script handles pagination automatically. It also reads the `sync_state` table for the last cursor, so subsequent runs only fetch new records (incremental sync).

### Automating with n8n

For tables that need regular updates, add them to the n8n workflows:

1. Open n8n at `http://localhost:5678` (or the production URL)
2. Open the `indigitall-data-sync` workflow
3. Duplicate the Messages branch (HTTP Request → Postgres Insert nodes)
4. Update the API URL, field mappings, and target table name
5. Connect it to the same Schedule Trigger (runs every 15 minutes)

---

## Step 5: Build a dashboard

Now that data is in the database, build a visualization.

### Option A: Add a chart to an existing page

The simplest approach. Open any layout file and add a `dcc.Graph`:

```python
dcc.Graph(id="surveys-score-chart")
```

Then in the corresponding callback file:

```python
@callback(
    Output("surveys-score-chart", "figure"),
    Input("tenant-context", "data"),
)
def load_survey_scores(tenant):
    query = text("""
        SELECT score, COUNT(*) as count
        FROM surveys
        WHERE tenant_id = :tid
        GROUP BY score
        ORDER BY score
    """)
    with engine.connect() as conn:
        rows = conn.execute(query, {"tid": tenant or "demo"}).fetchall()

    fig = px.bar(
        x=[r.score for r in rows],
        y=[r.count for r in rows],
        labels={"x": "Puntuación", "y": "Respuestas"},
    )
    fig.update_layout(template="plotly_white")
    return fig
```

### Option B: Create a dedicated page

Follow Example B from Part 1 above. Create `app/layouts/surveys.py` + `app/callbacks/surveys_cb.py`. Register the callback import in `main.py`.

### Option C: Use the AI Chat

Once you add the table to `ALLOWED_TABLES` in `ai_agent.py`, users can ask the AI natural language questions about the data:

- "Cual es el promedio de score en las encuestas?"
- "Cuantas encuestas se recibieron por WhatsApp este mes?"
- "Muestra las encuestas con score menor a 3"

The AI Agent generates SQL queries, validates them against the blocklist, and returns results as tables or charts. No coding needed for this — it works automatically.

---

## Available chart types (Plotly)

Dash uses Plotly for charts. The most common types:

```python
import plotly.express as px

# Bar chart
fig = px.bar(df, x="date", y="count")

# Line chart
fig = px.line(df, x="date", y="value")

# Pie chart
fig = px.pie(df, names="category", values="count")

# Heatmap
fig = px.imshow(pivot_table)

# Scatter plot
fig = px.scatter(df, x="handle_time", y="score", color="canal")

# Table (use Dash DataTable instead of Plotly)
from dash import dash_table
dash_table.DataTable(data=df.to_dict("records"), columns=[...])
```

Always use `fig.update_layout(template="plotly_white")` for consistent styling.

---

## Full example: from zero to dashboard

Here's the complete file-by-file summary for adding a `surveys` entity:

| Step | File | Action |
|------|------|--------|
| 1 | `app/models/schemas.py` | Add `Survey` class |
| 2 | `app/models/database.py` | Add `Survey` to `create_tables()` imports |
| 3 | `app/services/schema_service.py` | Add `"surveys"` to `ALLOWED_TABLES` |
| 4 | `app/services/ai_agent.py` | Add `"surveys"` to `ALLOWED_TABLES` |
| 5 | `scripts/mappings/surveys.json` | Create mapping file |
| 6 | `scripts/generate_mock_data.py` | Add `generate_surveys()` function |
| 7 | Run `generate_mock_data.py` | Creates `scripts/mock_data/surveys.json` |
| 8 | Run `ingest_api.py --demo` | Loads data into PostgreSQL |
| 9 | `app/layouts/surveys.py` | Create page with charts |
| 10 | `app/callbacks/surveys_cb.py` | Create callbacks to load data |
| 11 | `app/main.py` | Import callbacks + add nav link |
| 12 | Deploy | `git push` + `deploy.sh` |

---

## Common commands reference

```bash
# --- Local development ---
docker compose up -d                    # Start all services
docker compose logs app --tail 50       # Check app logs
docker compose restart app              # Restart after .env changes
docker compose exec app python -c \
  "from app.models.database import create_tables; create_tables()"
                                        # Create new tables

# --- Data ---
docker compose exec app python scripts/generate_mock_data.py
docker compose exec app python scripts/ingest_api.py --demo --table TABLE --tenant demo
docker compose exec app python scripts/ingest_api.py --demo --table TABLE --tenant demo --dry-run

# --- Production deployment ---
gcloud compute ssh indigitall-analytics \
  --project=trax-report-automation \
  --zone=southamerica-east1-a \
  --command="cd /opt/indigitall-analytics && bash scripts/deploy/deploy.sh"

# --- Production logs ---
gcloud compute ssh indigitall-analytics \
  --project=trax-report-automation \
  --zone=southamerica-east1-a \
  --command="cd /opt/indigitall-analytics && docker compose logs app --tail 50"

# --- Check what's running in production ---
gcloud compute ssh indigitall-analytics \
  --project=trax-report-automation \
  --zone=southamerica-east1-a \
  --command="cd /opt/indigitall-analytics && docker compose ps"
```

---

## Troubleshooting

### "ImportError: No module named..."
You probably forgot to add a file or import. Check:
- Did you `import app.callbacks.your_file_cb` in `main.py`?
- Is your layout file inside `app/layouts/`?

### "Callback ID not found"
The `id` in your `Output(...)` or `Input(...)` must match exactly an element `id` in your layout. Check for typos.

### "Table not found in Data Explorer"
Add the table name to `ALLOWED_TABLES` in `app/services/schema_service.py`.

### "Duplicate key violates unique constraint" during ingestion
Your mock data has duplicate records. Either:
- Make the generated IDs truly unique (use a counter, not random)
- Or clear the table before re-ingesting: `docker compose exec db psql -U postgres -c "DELETE FROM your_table WHERE tenant_id = 'demo';"`

### Changes not showing in production
- Did you `git push`?
- Did you run `deploy.sh`?
- Check if the container restarted: `docker compose ps` — look at the STATUS column
- Check logs: `docker compose logs app --tail 50`

### "Port already in use" when starting Docker
Stop any conflicting services: `docker compose down` then `docker compose up -d`.
