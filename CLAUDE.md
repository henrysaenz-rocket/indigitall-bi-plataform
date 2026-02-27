# inDigitall BI Platform — Project Rules

## Clean Code Principles (Robert C. Martin)

### Naming
- Use **intention-revealing names**. If a name requires a comment, the name is wrong.
- Class names are **nouns** (`DataService`, `ChartService`), method names are **verbs** (`get_summary_stats`, `create_line_chart`).
- Avoid abbreviations except well-known ones (`df`, `conn`, `stmt`, `cfg`).
- Use snake_case for Python functions/variables, PascalCase for classes.
- Boolean variables/functions start with `is_`, `has_`, `can_`, `should_`.

### Functions
- Functions should do **one thing** and do it well.
- Keep functions **small** — prefer under 20 lines, never exceed 40.
- Limit function arguments to **3 or fewer**. Group related args into dicts or dataclasses.
- No side effects — a function named `get_*` must not modify state.
- Prefer **early returns** over nested conditionals.
- Extract helper functions rather than writing long procedural blocks.

### DRY (Don't Repeat Yourself)
- Every piece of knowledge must have a **single, unambiguous representation**.
- If you copy-paste code, extract it into a shared function or constant.
- SQL patterns are centralized in `data_service.py`; chart patterns in `chart_service.py`.

### Error Handling
- Use **exceptions**, not return codes.
- Catch specific exceptions, never bare `except:`.
- Log errors with context (what was being attempted, what input caused the failure).
- Fail fast at system boundaries; be resilient inside pipelines (log and continue).

### Comments
- Good code is **self-documenting**. Don't comment what the code does — make the code clearer.
- Use comments only for: **why** (not what), legal notices, TODOs with ticket references.
- Docstrings on public methods only — follow Google style: one-line summary, then Args/Returns.
- Delete commented-out code. Git has history.

### Code Organization
- **One class per file** for models; **one service per file** for services.
- Imports at the top, grouped: stdlib → third-party → local.
- Keep modules focused: `data_service.py` = queries, `chart_service.py` = visualizations, `*_cb.py` = callbacks.
- Avoid circular imports. Callbacks import services; services import models; models import nothing.

### Testing
- Every bug fix should include a test that reproduces the bug.
- Test names describe the scenario: `test_fallback_rate_with_zero_messages_returns_zero`.
- Tests are fast, independent, and repeatable.

### YAGNI (You Aren't Gonna Need It)
- Don't build features until they are actually needed.
- Don't add parameters "for future flexibility" — add them when there's a second use case.
- Prefer simple over clever.

---

## InDigitall Brand Guidelines

All UI, dashboards, charts, and visual elements MUST use the InDigitall design system.

### Color Palette (mandatory)

| Token | Hex | Usage |
|-------|-----|-------|
| `--id-primary` | `#1E88E5` | Primary actions, active states, main chart color |
| `--id-primary-dark` | `#1565C0` | Hover states, emphasis, gradients |
| `--id-primary-light` | `#42A5F5` | Backgrounds, secondary chart color |
| `--id-secondary` | `#76C043` | Success, CTA buttons, positive trends |
| `--id-secondary-dark` | `#5EA832` | Hover on secondary elements |
| `--id-success` | `#76C043` | Positive KPI badges, upward trends |
| `--id-warning` | `#FFC107` | Caution indicators, medium-priority alerts |
| `--id-error` | `#EF4444` | Error states, negative trends, downward KPIs |
| `--id-info` | `#1E88E5` | Informational badges, tooltips |

### Chart Color Sequence (ordered, use in this order)

```
#1E88E5, #76C043, #A0A3BD, #42A5F5, #1565C0, #FFC107, #9C27B0, #FF5722
```

### Typography
- **Font**: Inter (Google Fonts), fallback: system stack
- **Sizes**: xs=12px, sm=13px, base=15px, lg=18px, xl=24px, 2xl=32px
- **KPI values**: 28px, weight 600
- **KPI labels**: 13px, weight 500, uppercase, letter-spacing 0.05em
- **Section headers**: 18px, weight 600

### Spacing
- xs=4px, sm=8px, md=16px, lg=24px, xl=32px

### Border Radius
- Cards: 16px (`--id-radius-lg`)
- Buttons/Inputs: 8px (`--id-radius-sm`)
- Pills/Chips: 24px (`--id-radius-pill`)

### Shadows
- Cards: `0 4px 24px rgba(0, 0, 0, 0.06)`
- Hover: `0 8px 32px rgba(0, 0, 0, 0.1)`

### Plotly Charts (mandatory styling)
- Background: transparent (`rgba(0,0,0,0)`)
- Grid color: `#E4E4E7`
- Font: Inter, size 12, color `#6E7191`
- Hover label: dark bg (`#1A1A2E`), font 13px
- Area fills: `rgba(30, 136, 229, 0.1)` for primary
- Line width: 2-3px
- No display mode bar (`config={"displayModeBar": False}`)

### CSS Classes (use existing, don't create new ones)
- Page titles: `.page-title`, `.page-subtitle`
- Cards: `.kpi-card`, `.chart-widget`
- Labels: `.section-label`, `.kpi-label`, `.kpi-value`
- Navbar: `.navbar-indigitall`

### Language
- All user-facing text in **Spanish (Colombian)**.
- Labels: "Mensajes", "Contactos", "Conversaciones", "Agentes", "Tendencia", etc.
- Date format: `YYYY-MM-DD` in pickers, `DD MMM` in chart axes.

### Do NOT
- Use colors outside the defined palette.
- Use fonts other than Inter.
- Create new CSS classes when existing ones cover the need.
- Use English in user-facing labels (except technical terms like "Fallback", "Bot").
- Add external CSS frameworks beyond Bootstrap + Bootstrap Icons.

---

## Project Architecture

```
app/
  main.py              — Dash app + Flask server + pipeline API
  config.py            — Settings from .env
  models/
    database.py        — SQLAlchemy engine
    schemas.py         — ORM table definitions
  services/
    data_service.py    — All SQL queries (DataService class)
    chart_service.py   — All Plotly charts (ChartService class)
  layouts/             — Dash pages (registered with use_pages)
  callbacks/           — Dash callbacks (*_cb.py)
  assets/
    styles.css         — Design system (CSS variables)
    indigitall_logo.webp
scripts/
  extractors/          — API data extraction
  transform_bridge.py  — raw.* → public.* ETL
dbt/                   — dbt models and tests
```

### Conventions
- Callbacks go in `app/callbacks/<page>_cb.py`, one file per page.
- Layout IDs use page prefix: `ops-*`, `home-*`, `query-*`.
- DataService methods return `pd.DataFrame` or `Dict[str, Any]`.
- ChartService methods return `go.Figure`.
- All DB queries use SQLAlchemy Core (not raw SQL strings) except for complex CTEs.
- Tenant filtering via `_tenant_filter()` helper on every query.
