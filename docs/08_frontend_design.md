# 08 — Frontend Design Document

**Version:** 1.0 — Draft for Review
**Date:** 2026-02-16
**Status:** PENDING REVIEW

---

## 1. Design Vision

### Concept: "Redash meets AI Assistant"

The platform follows Redash's proven information architecture — **Queries produce Visualizations; Visualizations compose Dashboards** — but replaces the SQL editor with an **AI chat interface**. The primary user (marketing manager, non-technical) never writes SQL; they ask questions in natural language and the AI generates data + charts they can save, organize, and compose into dashboards.

### Core Model

```
                    ┌──────────────┐
                    │   AI Chat    │  ← User asks question in Spanish
                    └──────┬───────┘
                           │ produces
                    ┌──────▼───────┐
                    │    Query     │  ← Named result: data + visualization
                    │  (Consulta)  │     Can be saved, tagged, shared
                    └──────┬───────┘
                           │ added to
                    ┌──────▼───────┐
                    │  Dashboard   │  ← Grid of query widgets
                    │  (Tablero)   │     Drag, resize, auto-refresh
                    └──────────────┘
```

### Key Differences from Redash

| Aspect | Redash | Our Platform |
|--------|--------|-------------|
| Query creation | SQL editor + schema browser | AI chat (natural language) |
| Data source selection | Multi-database dropdown | Single tenant, auto-selected |
| User profile | Data analyst / engineer | Marketing manager (non-technical) |
| Language | English UI | Spanish UI |
| Visualization creation | Manual config (type, axes, series) | AI auto-generates + user can edit |
| Tenant isolation | User groups + data source permissions | RLS + JWT per tenant |
| Pre-built analytics | None (all ad-hoc) | 13+ pre-built functions for common questions |
| SQL fallback | Primary interface | Hidden from user; AI uses internally |

---

## 2. Navigation Structure

### Top Navbar (Persistent, All Pages)

```
┌─────────────────────────────────────────────────────────────────────┐
│  [Logo]   Inicio   Consultas   Tableros   Alertas    [+ Crear ▾]  │
│                                                    [🔔] [Avatar ▾] │
└─────────────────────────────────────────────────────────────────────┘
```

**Left section:**
- **Logo**: inDigitall logo (clickable → home)
- **Inicio**: Home page (`/`)
- **Consultas**: Saved queries list (`/consultas`)
- **Tableros**: Dashboards list (`/tableros`)
- **Alertas**: Alerts list (`/alertas`) — Phase 2, placeholder for now

**Right section:**
- **+ Crear** dropdown button (green, CTA):
  - Nueva Consulta → opens AI chat in new query mode (`/consultas/nueva`)
  - Nuevo Tablero → creates empty dashboard (`/tableros/nuevo`)
  - Nueva Alerta → placeholder
- **Notification bell** (future)
- **User avatar dropdown**:
  - Tenant name / project name (display only)
  - Configuracion (future)
  - Cerrar sesion

### Mobile Responsive

On screens < 768px:
- Navbar collapses to hamburger menu
- Logo stays visible
- "+ Crear" becomes a floating action button (FAB)

### URL Routing

| Route | Page | Description |
|-------|------|-------------|
| `/` | Home | Favorites + recent items |
| `/consultas` | Query List | All saved queries |
| `/consultas/nueva` | New Query | AI chat + empty results |
| `/consultas/:id` | Query View | Saved query: results + visualization + AI chat |
| `/tableros` | Dashboard List | All dashboards |
| `/tableros/nuevo` | New Dashboard | Empty grid + add widget |
| `/tableros/:id` | Dashboard View | Widget grid, view mode |
| `/tableros/:id/editar` | Dashboard Edit | Widget grid, edit mode (drag/resize) |
| `/alertas` | Alerts List | Placeholder |

---

## 3. Home Page (`/`)

### Layout

```
┌─────────────────────────────────────────────────────────┐
│  NAVBAR                                                  │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Buenos dias, [Nombre]                                   │
│  Bienvenido a tu plataforma de analitica                │
│                                                          │
│  ┌──────────────────────┐  ┌──────────────────────┐     │
│  │  Tableros Favoritos  │  │  Consultas Favoritas  │     │
│  │                      │  │                       │     │
│  │  📊 Dashboard Princ. │  │  📈 Fallback Rate     │     │
│  │  📊 Email Campaign   │  │  📈 Mensajes por Hora │     │
│  │  📊 Weekly Report    │  │  📈 Top Contactos     │     │
│  │                      │  │                       │     │
│  │  [Ver todos →]       │  │  [Ver todas →]        │     │
│  └──────────────────────┘  └──────────────────────┘     │
│                                                          │
│  ┌──────────────────────┐  ┌──────────────────────┐     │
│  │  Tableros Recientes  │  │  Consultas Recientes  │     │
│  │                      │  │                       │     │
│  │  📊 ...              │  │  📈 ...               │     │
│  │  📊 ...              │  │  📈 ...               │     │
│  └──────────────────────┘  └──────────────────────┘     │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### Sections

1. **Greeting banner**: "Buenos dias/tardes/noches, [User Name]" + quick action: "Hacer una pregunta" button → `/consultas/nueva`
2. **Tableros Favoritos** (2-column card grid): Dashboard cards the user has starred. Each card shows: name, last updated, widget count. Click → dashboard view.
3. **Consultas Favoritas** (2-column card grid): Saved query cards the user has starred. Each card shows: name, visualization type icon, last run time. Click → query view.
4. **Tableros Recientes** (list): Last 5 dashboards viewed. Same card format.
5. **Consultas Recientes** (list): Last 5 queries viewed.

### Empty State (New User)

```
┌─────────────────────────────────────────────────────────┐
│                                                          │
│              Bienvenido a inDigitall Analytics            │
│                                                          │
│  Comienza haciendo una pregunta sobre tus datos:         │
│                                                          │
│  ┌────────────────────────────────────────────────┐      │
│  │  💬  "¿Como esta el fallback del bot?"         │      │
│  │  📊  "Muestra la tendencia de mensajes"         │      │
│  │  📈  "Top 10 contactos activos"                 │      │
│  └────────────────────────────────────────────────┘      │
│                                                          │
│         [ Hacer mi primera consulta → ]                  │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

## 4. Query Page — AI Chat + Results (`/consultas/nueva` and `/consultas/:id`)

This is the most critical page. It merges Redash's query editor concept with an AI assistant interface.

### Layout: Three-Panel Design

```
┌─────────────────────────────────────────────────────────────────────┐
│  NAVBAR                                                              │
├─────────────────────────────────────────────────────────────────────┤
│  [Query Name ✏️]     [⭐] [▷ Ejecutar] [💾 Guardar] [⋮ Mas]       │
├──────────────┬──────────────────────────────────────────────────────┤
│              │                                                       │
│   AI Chat    │              Results / Visualization                  │
│   Panel      │                                                       │
│   (Left)     │  ┌─────────────────────────────────────────────┐     │
│              │  │ [Tabla] [📊 Grafico 1] [+ Nueva Visual.]    │     │
│  ┌────────┐  │  ├─────────────────────────────────────────────┤     │
│  │Suggest.│  │  │                                             │     │
│  │ chips  │  │  │          Chart / Table / Data               │     │
│  └────────┘  │  │                                             │     │
│              │  │                                             │     │
│  💬 Chat    │  │                                             │     │
│  messages   │  │                                             │     │
│  ...        │  │                                             │     │
│  ...        │  │                                             │     │
│              │  │                                             │     │
│              │  └─────────────────────────────────────────────┘     │
│              │                                                       │
│  ┌────────┐  │  ┌─────────────────────────────────────────────┐     │
│  │ Input  │  │  │ Query Details (collapsible)                  │     │
│  │ area   │  │  │ Function: summary | Rows: 5 | Time: 0.2s   │     │
│  └────────┘  │  └─────────────────────────────────────────────┘     │
│              │                                                       │
├──────────────┴──────────────────────────────────────────────────────┤
│  [📥 Exportar CSV]  [📋 Copiar]  [📌 Agregar a Tablero]           │
└─────────────────────────────────────────────────────────────────────┘
```

### 4.1 Page Header Bar

| Element | Description |
|---------|-------------|
| **Query Name** | Editable inline text. Default: "Nueva Consulta". Click to rename. |
| **Star button** | Toggle favorite. Adds to home page favorites. |
| **Ejecutar** | Re-run the current query (refresh data). Blue primary button. |
| **Guardar** | Save query + visualization state. Disabled until first result. |
| **Mas (⋮)** dropdown | Fork (duplicate), Archivar (soft delete), Ver SQL (show generated SQL for advanced users). |

### 4.2 AI Chat Panel (Left, ~35% Width)

This replaces Redash's SQL editor + schema browser.

**State Machine:**

```
EMPTY → SUGGESTIONS_SHOWN → USER_TYPING → PROCESSING → RESULT_DISPLAYED
                                              ↑              │
                                              └──────────────┘
                                              (user asks follow-up)
```

**Empty State (new query):**
- Title: "Pregunta sobre tus datos"
- Subtitle: "Describe lo que quieres analizar en lenguaje natural"
- 6 suggestion chips in 2x3 grid:
  - "¿Como esta el fallback del bot?"
  - "Muestra mensajes por canal"
  - "¿Cual es el horario pico?"
  - "Top 10 contactos activos"
  - "Dame un resumen ejecutivo"
  - "Comparar cooperativas"

**Conversation Flow:**
- **User message**: Blue gradient bubble, right-aligned. Shows timestamp.
- **Assistant message**: Light gray bubble, left-aligned. Contains:
  - Text explanation (markdown)
  - "Ver en panel" link → scrolls/focuses the results panel
- **Processing state**: Typing indicator animation + "Analizando datos..."
- **Error state**: Red-tinted bubble with error message + retry button

**Chat Input:**
- Fixed at bottom of chat panel
- Placeholder: "Escribe tu pregunta..."
- Send button (blue arrow icon)
- Keyboard: Enter to send, Shift+Enter for new line

**Conversation Memory:**
- Last 10 messages visible in scrollable area
- Session-based (stored in browser, `dcc.Store`)
- Each analytics response links to the results panel

### 4.3 Results Panel (Right, ~65% Width)

Inspired by Redash's results area below the query editor.

**Visualization Tabs (top of panel):**
- **Tabla**: Default. Shows `dash_table.DataTable` with full results.
- **[Chart Name]**: Each saved visualization gets its own tab. Default auto-generated chart from AI response.
- **+ Nueva Visualizacion**: Opens visualization editor modal.

**Visualization Content:**
- `dcc.Graph(figure=...)` for charts
- `dash_table.DataTable` for tables
- Full width of the results panel
- Charts use the inDigitall color palette (#1E88E5, #76C043, etc.)

**Query Details (collapsible bar below results):**
- Function name or SQL query used
- Rows returned
- Execution time
- "Ver SQL" toggle for advanced users (shows the generated SQL)

**Action Bar (bottom of results panel):**
- **Exportar CSV**: Downloads current result as CSV
- **Copiar**: Copies data to clipboard
- **Agregar a Tablero**: Opens "Add to Dashboard" modal

### 4.4 Visualization Editor Modal

When user clicks "+ Nueva Visualizacion" or edits existing visualization:

```
┌─────────────────────────────────────────────────────────┐
│  Editar Visualizacion                            [✕]     │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Tipo: [Dropdown: Barras / Lineas / Pie / Tabla / ...]  │
│                                                          │
│  Nombre: [________________________]                      │
│                                                          │
│  ┌──────────────────────────────────────────────┐       │
│  │ [General] [Eje X] [Eje Y] [Series] [Colores] │       │
│  ├──────────────────────────────────────────────┤       │
│  │                                              │       │
│  │  Eje X: [Dropdown: column names]             │       │
│  │  Eje Y: [Dropdown: column names]             │       │
│  │  Agrupar por: [Dropdown: optional]           │       │
│  │                                              │       │
│  └──────────────────────────────────────────────┘       │
│                                                          │
│  Preview:                                                │
│  ┌──────────────────────────────────────────────┐       │
│  │          [Live chart preview]                 │       │
│  └──────────────────────────────────────────────┘       │
│                                                          │
│               [Cancelar]  [Guardar Visualizacion]        │
└─────────────────────────────────────────────────────────┘
```

**Supported Visualization Types:**
- Barras (bar chart — vertical/horizontal)
- Lineas (line chart)
- Pie / Dona (pie/donut)
- Combo (dual axis — bars + line)
- Area (area chart)
- Mapa de Calor (heatmap)
- Tabla (data table with formatting)
- Numero (single KPI value)
- Embudo (funnel)

### 4.5 "Add to Dashboard" Modal

```
┌───────────────────────────────────────┐
│  Agregar a Tablero               [✕]  │
├───────────────────────────────────────┤
│                                       │
│  Buscar tablero: [____________🔍]    │
│                                       │
│  Tableros recientes:                  │
│  ○ Dashboard Principal                │
│  ○ Reporte Semanal Email              │
│  ○ Rendimiento de Bot                 │
│                                       │
│  — o —                                │
│  [ + Crear nuevo tablero ]            │
│                                       │
│  Visualizacion a agregar:             │
│  [Dropdown: Tabla / Grafico 1 / ...]  │
│                                       │
│         [Cancelar]  [Agregar]         │
└───────────────────────────────────────┘
```

---

## 5. Query List Page (`/consultas`)

### Layout

```
┌─────────────────────────────────────────────────────────┐
│  NAVBAR                                                  │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Consultas                           [+ Nueva Consulta]  │
│                                                          │
│  [🔍 Buscar...]  [⭐ Favoritos ▾]  [🏷️ Tags ▾]         │
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │ ⭐  Fallback Rate         pie     hace 2 horas   │   │
│  │ ⭐  Mensajes por Hora     bar     hace 1 dia     │   │
│  │     Top Contactos         hbar    hace 3 dias    │   │
│  │     Resumen Ejecutivo     table   hace 1 semana  │   │
│  │     Tendencia Mensajes    line    hace 1 semana  │   │
│  └──────────────────────────────────────────────────┘   │
│                                                          │
│  Mostrando 5 de 23 consultas          [< 1 2 3 ... >]  │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### Table Columns

| Column | Description |
|--------|-------------|
| **Favorito** | Star toggle |
| **Nombre** | Query name (clickable → query view) |
| **Tipo** | Visualization icon (bar, line, pie, table) |
| **Creado por** | User name |
| **Ultimo resultado** | Relative timestamp ("hace 2 horas") |
| **Tags** | Optional tags/labels |

### Filters

- **Search**: Text search across query names
- **Favoritos**: Toggle to show only starred queries
- **Tags**: Multi-select dropdown for tag filtering
- **Mis consultas / Todas**: Toggle between own queries and all accessible queries

### Pagination

- 20 items per page
- Standard pagination component

---

## 6. Dashboard View Page (`/tableros/:id`)

### View Mode Layout

```
┌─────────────────────────────────────────────────────────────────────┐
│  NAVBAR                                                              │
├─────────────────────────────────────────────────────────────────────┤
│  [Dashboard Name ✏️]   [⭐] [🔄 Actualizar] [⏱️ Auto ▾] [✏️ Editar] [⋮] │
├─────────────────────────────────────────────────────────────────────┤
│  Filtros: [Periodo ▾] [Canal ▾] [Proyecto ▾]         [Aplicar]     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │
│  │ KPI Card │ │ KPI Card │ │ KPI Card │ │ KPI Card │ │ KPI Card │  │
│  │ Enviados │ │  Clicks  │ │   CTR    │ │  Open %  │ │ Campanas │  │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘  │
│                                                                      │
│  ┌────────────────────────┐  ┌────────────────────────┐             │
│  │                        │  │                        │             │
│  │  Line Chart            │  │  Combo Chart           │             │
│  │  Enviados vs Chunks    │  │  Envio vs Clicks+CTR   │             │
│  │                        │  │                        │             │
│  └────────────────────────┘  └────────────────────────┘             │
│                                                                      │
│  ┌────────────────────────┐  ┌────────────────────────┐             │
│  │                        │  │                        │             │
│  │  Horizontal Bar        │  │  Horizontal Bar        │             │
│  │  Campanas x Volumen    │  │  Campanas x CTR        │             │
│  │                        │  │                        │             │
│  └────────────────────────┘  └────────────────────────┘             │
│                                                                      │
│  ┌─────────────────────────────────────────────────────┐            │
│  │                    Heatmap                           │            │
│  │              Dia de Semana x Hora                    │            │
│  └─────────────────────────────────────────────────────┘            │
│                                                                      │
│  ┌─────────────────────────────────────────────────────┐            │
│  │                 Data Table                           │            │
│  │           Detalle de Campanas                        │            │
│  │           [📥 Exportar CSV]                         │            │
│  └─────────────────────────────────────────────────────┘            │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 6.1 Dashboard Header Bar

| Element | Description |
|---------|-------------|
| **Dashboard Name** | Editable inline. Click to rename. |
| **Star** | Toggle favorite |
| **Actualizar** | Refresh all widgets (re-run all queries) |
| **Auto** dropdown | Auto-refresh interval: Off, 1 min, 5 min, 10 min, 30 min, 1 hora |
| **Editar** | Enter edit mode (drag/resize/add widgets) |
| **Mas (⋮)** | Full screen, Compartir link, Duplicar, Archivar |

### 6.2 Dashboard Filters

Dashboard-level filters that apply to all widgets. Each widget query can declare which parameters it accepts.

| Filter | Type | Description |
|--------|------|-------------|
| Periodo | Dropdown | Diario / Semanal / Mensual |
| Canal | Multiselect | SMS, WhatsApp, Email, Push, In-App/Web |
| Proyecto | Dropdown | Todos, or specific project |
| Fecha | Date range picker | Custom date range |
| Telefono | Search input | Filter by phone number |

Filters are rendered in a collapsible bar below the navbar. "Aplicar" button triggers all widgets to re-query with new filter values.

### 6.3 Widget Grid

**Grid system:** 6-column grid (matching Redash). Uses CSS Grid (not react-grid-layout since we're in Dash).

**Widget sizes (in grid columns):**
- **Small**: 1 col (KPI number card)
- **Medium**: 2 cols (standard chart)
- **Large**: 3 cols (wide chart)
- **Full**: 6 cols (heatmap, data table)

**Each widget contains:**
- Title bar with query name
- Visualization (chart or table)
- Hover actions: "Ver consulta" (go to query), "Actualizar" (refresh single widget)

### 6.4 Dashboard AI Chat (Slide-Over Panel)

On any dashboard page, a floating "💬 Preguntar" button in bottom-right opens a slide-over chat panel (right side, ~400px wide). This allows the user to ask questions in context of the dashboard they're viewing.

```
┌────────────────────────────────────┐
│  Asistente IA                 [✕]  │
├────────────────────────────────────┤
│                                    │
│  Suggestion chips:                 │
│  "¿Como va el CTR esta semana?"    │
│  "Comparar con mes anterior"       │
│                                    │
│  [Chat messages...]                │
│                                    │
│  ┌──────────────────────────┐     │
│  │  Pregunta...         [→] │     │
│  └──────────────────────────┘     │
│                                    │
│  [Guardar como consulta]           │
│  [Agregar a este tablero]          │
│                                    │
└────────────────────────────────────┘
```

When the AI responds with data+chart, the user can:
1. **"Guardar como consulta"** → saves as a new named query
2. **"Agregar a este tablero"** → adds the result as a new widget directly

---

## 7. Dashboard Edit Mode (`/tableros/:id/editar`)

### Layout Changes in Edit Mode

```
┌─────────────────────────────────────────────────────────────────────┐
│  NAVBAR                                                              │
├─────────────────────────────────────────────────────────────────────┤
│  [Dashboard Name]   [+ Agregar Widget]  [Listo ✓]                   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─ ─ ─ ─ ─ ─ ─ ─ ┐  ┌─ ─ ─ ─ ─ ─ ─ ─ ┐  ┌─ ─ ─ ─ ─ ─ ┐       │
│  │  KPI Card  [✕]  │  │  KPI Card  [✕]  │  │ KPI    [✕]  │       │
│  │  (draggable)    │  │  (draggable)    │  │ (drag)      │       │
│  └─ ─ ─ ─ ─ ─ ─ ─ ┘  └─ ─ ─ ─ ─ ─ ─ ─ ┘  └─ ─ ─ ─ ─ ─ ┘       │
│                                                                      │
│  ┌─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┐  ┌─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┐     │
│  │  Chart Widget       [⋮][✕] │  │  Chart Widget      [⋮][✕] │     │
│  │  ↔ resize handle           │  │  ↔ resize handle          │     │
│  └─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┘  └─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┘     │
│                                                                      │
│  ┌ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─┐   │
│  │  + Agregar Widget (drop zone)                                │   │
│  └ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─┘   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Edit Mode Features

| Feature | Description |
|---------|-------------|
| **Drag** | Move widgets by dragging title bar |
| **Resize** | Drag bottom-right corner to resize (snap to column grid) |
| **Remove** | [✕] button on each widget |
| **Widget menu (⋮)** | Edit title, Change visualization, Go to query |
| **Add Widget** | Opens "Agregar Widget" modal |
| **Listo** | Exit edit mode, save layout |

### "Add Widget" Modal

```
┌─────────────────────────────────────────────┐
│  Agregar Widget                        [✕]   │
├─────────────────────────────────────────────┤
│                                              │
│  ○ Consulta existente                        │
│  ○ Texto / Markdown                          │
│                                              │
│  Buscar consulta: [_______________🔍]       │
│                                              │
│  Resultados:                                 │
│  ┌────────────────────────────────────┐     │
│  │  📈 Fallback Rate                  │     │
│  │     Visualizaciones: [Tabla] [Pie] │     │
│  ├────────────────────────────────────┤     │
│  │  📊 Mensajes por Hora              │     │
│  │     Visualizaciones: [Tabla] [Bar] │     │
│  ├────────────────────────────────────┤     │
│  │  📈 Top Contactos                  │     │
│  │     Visualizaciones: [Tabla][HBar] │     │
│  └────────────────────────────────────┘     │
│                                              │
│  Seleccionado: Fallback Rate → [Pie]        │
│                                              │
│            [Cancelar]  [Agregar al Tablero]  │
└─────────────────────────────────────────────┘
```

**Text/Markdown widget option:** For adding section headers, descriptions, or commentary to dashboards.

---

## 8. Dashboard List Page (`/tableros`)

> **Shared by default:** All dashboards and saved queries are **shared across the entire project/organization**. When one user creates or edits a dashboard, every other user in the same tenant sees it immediately. There is no private/published distinction — "Creado por" shows authorship for attribution, not access control. RLS isolates between tenants, but within a tenant everything is collaborative.

### Layout

```
┌─────────────────────────────────────────────────────────┐
│  NAVBAR                                                  │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Tableros                            [+ Nuevo Tablero]   │
│                                                          │
│  [🔍 Buscar...]  [⭐ Favoritos ▾]  [🏷️ Tags ▾]         │
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │ ⭐  Dashboard Principal    6 widgets  hace 1h    │   │
│  │ ⭐  Email Campaign Report  4 widgets  hace 2h    │   │
│  │     Weekly SMS Report      8 widgets  hace 1d    │   │
│  │     Bot Performance        3 widgets  hace 3d    │   │
│  └──────────────────────────────────────────────────┘   │
│                                                          │
│  Mostrando 4 de 12 tableros          [< 1 2 ... >]     │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### Table Columns

| Column | Description |
|--------|-------------|
| **Favorito** | Star toggle |
| **Nombre** | Dashboard name (clickable) |
| **Widgets** | Count of widgets in dashboard |
| **Creado por** | User name |
| **Ultima actualizacion** | Relative timestamp |
| **Tags** | Optional labels |

---

## 9. Default "Primary Dashboard"

When a new tenant is provisioned, the system auto-creates a **"Dashboard Principal"** with pre-configured widgets from the existing demo data. This ensures the marketing manager sees value immediately.

### Pre-Built Widgets (maps to existing demo Dashboard page)

**Row 1: KPI Cards (5 small widgets, 1 col each)**
1. Total Enviados
2. Total Clicks
3. Chunks Usados
4. CTR Promedio
5. Campanas Activas

**Row 2: Trend Charts (2 medium widgets, 3 cols each)**
6. Enviados vs Chunks (multi-line)
7. Enviados vs Clicks vs CTR (combo chart)

**Row 3: Rankings (2 medium widgets, 3 cols each)**
8. Campanas por Volumen (horizontal bar)
9. Campanas por CTR (horizontal bar)

**Row 4: Heatmap (1 full-width widget, 6 cols)**
10. Dia x Hora heatmap

**Row 5: Table (1 full-width widget, 6 cols)**
11. Detalle de Campanas (data table with CSV export)

### Channel-Specific Dashboards (Future)

Additional pre-built dashboards for each channel tab from the demo:
- **Email Analytics**: 11 KPIs + 4 charts + heatmap + table
- **In-App/Web Analytics**: 6 KPIs + 4 charts + heatmap + table
- **WhatsApp Conversations**: Summary stats + fallback rate + trends
- **Push** / **CC** / **Wallet**: Placeholder dashboards

---

## 10. AI Agent Interaction Design

### 10.1 The 13 Pre-Built Functions (Existing)

These remain from the demo. Each maps to a service method + default visualization.

| # | Function | Default Chart | Question Pattern |
|---|----------|--------------|-----------------|
| 1 | `summary` | table | "Dame un resumen", "cuantos mensajes" |
| 2 | `fallback_rate` | table + KPI | "Como esta el bot", "tasa de fallback" |
| 3 | `messages_by_direction` | pie | "Mensajes por canal", "distribucion" |
| 4 | `messages_by_hour` | bar | "Horario pico", "trafico por hora" |
| 5 | `messages_over_time` | line | "Tendencia", "historico" |
| 6 | `messages_by_day_of_week` | bar | "Dia de la semana", "lunes martes" |
| 7 | `top_contacts` | horizontal_bar | "Top contactos", "ranking" |
| 8 | `intent_distribution` | horizontal_bar | "Intenciones", "temas" |
| 9 | `agent_performance` | bar | "Rendimiento agentes", "operadores" |
| 10 | `entity_comparison` | horizontal_bar | "Comparar cooperativas" |
| 11 | `high_messages_day` | table | "Clientes con mas de 4 mensajes/dia" |
| 12 | `high_messages_week` | table | "Clientes con mas de 4 mensajes/semana" |
| 13 | `high_messages_month` | table | "Clientes con mas de 4 mensajes/mes" |

### 10.2 SQL Fallback (New)

When the user's question doesn't match any pre-built function, the AI generates a guarded SQL query.

**User experience:**
1. User asks: "Cuantos mensajes entraron el jueves pasado entre 2pm y 5pm?"
2. AI responds: "Encontre 342 mensajes inbound el jueves entre 14:00 y 17:00. Esto es 15% mas que el promedio de jueves."
3. Results panel shows data table + auto-generated bar chart
4. Query Details shows: "Consulta SQL generada" (collapsible, shows the SQL for transparency)

**Guardrails (enforced server-side):**
- SELECT only (no mutations)
- Allowed tables whitelist
- Auto-inject `tenant_id` filter (RLS enforces at DB level too)
- LIMIT 1000 max rows
- 10-second query timeout
- Keyword blocklist: DROP, DELETE, INSERT, UPDATE, ALTER, TRUNCATE, CREATE

### 10.3 Demo Mode

When no Anthropic API key is configured, the platform runs in **demo mode**:
- Pattern matching handles ~15 common question patterns (see `_demo_mode_query`)
- Response quality is lower but functional
- User sees a subtle banner: "Modo demo — respuestas limitadas"

### 10.4 AI System Prompt (Key Details)

- Personality: Senior data analyst, friendly, proactive
- Language: Spanish, professional but accessible
- Always provides business insights, not just data
- Knows inDigitall context: WhatsApp Business, chatbot, cooperativas
- Response format: JSON with type, function/SQL, explanation
- Conversation memory: last 4 messages for context

---

## 11. Component Library Mapping

### Dash Component Equivalents

| UI Element | Dash Component | CSS Class |
|-----------|---------------|-----------|
| Top navbar | `dbc.Navbar` + `dbc.NavItem` | `.navbar-indigitall` |
| Create dropdown | `dbc.DropdownMenu` + `dbc.DropdownMenuItem` | `.create-dropdown` |
| Page container | `dash.page_container` in `dbc.Container(fluid=True)` | `.page-content` |
| KPI card | `dbc.Card` + `html.Div` | `.kpi-card` |
| Chart widget | `dbc.Card` wrapping `dcc.Graph` | `.chart-widget` |
| Data table | `dash_table.DataTable` | `.data-table` |
| Filter dropdown | `dcc.Dropdown` | `.filter-dropdown` |
| Multi-select | `dcc.Dropdown(multi=True)` | `.filter-multiselect` |
| Date picker | `dcc.DatePickerRange` | `.date-range-picker` |
| Search input | `dbc.Input(type="search")` | `.search-input` |
| Chat message (user) | `html.Div` | `.chat-message.user-msg` |
| Chat message (AI) | `html.Div` | `.chat-message.assistant-msg` |
| Suggestion chip | `dbc.Button(outline=True, size="sm")` | `.suggestion-chip` |
| Chat input | `dbc.InputGroup` + `dbc.Input` + `dbc.Button` | `.chat-input` |
| Modal dialog | `dbc.Modal` | `.modal-dialog` |
| Tabs | `dbc.Tabs` + `dbc.Tab` | `.viz-tabs` |
| Accordion | `dbc.Accordion` | `.query-details` |
| Spinner | `dbc.Spinner` | `.loading-spinner` |
| Star/favorite | `dbc.Button` (toggle icon) | `.favorite-btn` |
| Pagination | `dbc.Pagination` | `.pagination` |
| Breadcrumb | `dbc.Breadcrumb` | — |
| Toast notification | `dbc.Toast` | `.toast-notification` |
| Slide-over panel | `dbc.Offcanvas` | `.ai-chat-panel` |
| Widget grid | `html.Div` with CSS Grid | `.dashboard-grid` |
| Download trigger | `dcc.Download` + `dbc.Button` | — |

### Client-Side State Stores

| Store | Type | Purpose |
|-------|------|---------|
| `chat-history` | `dcc.Store(storage_type="session")` | Current chat conversation |
| `query-result` | `dcc.Store(storage_type="memory")` | Active query result data (JSON) |
| `dashboard-layout` | `dcc.Store(storage_type="memory")` | Widget positions/sizes for edit mode |
| `user-preferences` | `dcc.Store(storage_type="local")` | Favorites, recent items, UI preferences |
| `active-filters` | `dcc.Store(storage_type="session")` | Dashboard filter state |
| `tenant-context` | `dcc.Store(storage_type="session")` | Current tenant from JWT |

---

## 12. Design Tokens (CSS Variables)

```css
:root {
  /* === Brand Colors === */
  --id-primary: #1E88E5;
  --id-primary-dark: #1565C0;
  --id-primary-light: #42A5F5;
  --id-secondary: #76C043;
  --id-secondary-dark: #5EA832;

  /* === Neutral Palette === */
  --id-text-primary: #1A1A2E;
  --id-text-secondary: #6E7191;
  --id-text-muted: #A0A3BD;
  --id-bg-page: #F5F7FA;
  --id-bg-card: #FFFFFF;
  --id-border: #E4E4E7;

  /* === Semantic Colors === */
  --id-success: #76C043;
  --id-warning: #FFC107;
  --id-error: #EF4444;
  --id-info: #1E88E5;

  /* === Typography === */
  --id-font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  --id-font-size-xs: 12px;
  --id-font-size-sm: 13px;
  --id-font-size-base: 15px;
  --id-font-size-lg: 18px;
  --id-font-size-xl: 24px;
  --id-font-size-2xl: 32px;
  --id-font-weight-normal: 400;
  --id-font-weight-medium: 500;
  --id-font-weight-semibold: 600;
  --id-font-weight-bold: 700;

  /* === Spacing === */
  --id-space-xs: 4px;
  --id-space-sm: 8px;
  --id-space-md: 16px;
  --id-space-lg: 24px;
  --id-space-xl: 32px;
  --id-space-2xl: 48px;

  /* === Border Radius === */
  --id-radius-sm: 8px;
  --id-radius-md: 12px;
  --id-radius-lg: 16px;
  --id-radius-pill: 24px;
  --id-radius-circle: 50%;

  /* === Shadows === */
  --id-shadow-sm: 0 2px 8px rgba(0, 0, 0, 0.06);
  --id-shadow-md: 0 4px 24px rgba(0, 0, 0, 0.06);
  --id-shadow-lg: 0 8px 32px rgba(0, 0, 0, 0.1);

  /* === Chat-Specific === */
  --id-chat-user-bg: linear-gradient(135deg, #1565C0 0%, #42A5F5 100%);
  --id-chat-user-text: #FFFFFF;
  --id-chat-assistant-bg: #F5F7FA;
  --id-chat-assistant-border: #E4E4E7;

  /* === Chart Colors (ordered sequence) === */
  --id-chart-1: #1E88E5;
  --id-chart-2: #76C043;
  --id-chart-3: #A0A3BD;
  --id-chart-4: #42A5F5;
  --id-chart-5: #1565C0;
  --id-chart-6: #FFC107;
  --id-chart-7: #9C27B0;
  --id-chart-8: #FF5722;

  /* === Grid (Dashboard) === */
  --id-grid-columns: 6;
  --id-grid-gap: 16px;
  --id-grid-row-height: 80px;

  /* === Z-Index Scale === */
  --id-z-navbar: 1000;
  --id-z-modal-backdrop: 1040;
  --id-z-modal: 1050;
  --id-z-offcanvas: 1045;
  --id-z-toast: 1090;
  --id-z-fab: 1030;

  /* === Transitions === */
  --id-transition-fast: 150ms ease-out;
  --id-transition-normal: 200ms ease-out;
  --id-transition-slow: 300ms ease-out;

  /* === Layout === */
  --id-navbar-height: 56px;
  --id-chat-panel-width: 35%;
  --id-offcanvas-width: 400px;
  --id-max-content-width: 1400px;
}
```

---

## 13. Page-by-Page Callback Inventory

### Home Page
| Callback | Trigger | Effect |
|----------|---------|--------|
| `load-favorites` | Page load | Fetch starred queries + dashboards from DB |
| `load-recents` | Page load | Fetch last 5 viewed from `user-preferences` store |
| `navigate-query` | Click query card | Navigate to `/consultas/:id` |
| `navigate-dashboard` | Click dashboard card | Navigate to `/tableros/:id` |

### Query Page (New + View)
| Callback | Trigger | Effect |
|----------|---------|--------|
| `send-message` | Send button / Enter key | Process via AI agent, update chat + results |
| `click-suggestion` | Click chip | Fill input + auto-send |
| `update-results` | AI response received | Render table + chart in results panel |
| `save-query` | Click Guardar | Write to `saved_queries` table (name, data, chart config) |
| `toggle-favorite` | Click star | Update `is_favorite` in DB |
| `rename-query` | Edit name field | Update query name in DB |
| `export-csv` | Click Exportar | Trigger `dcc.Download` |
| `add-to-dashboard` | Click Agregar | Open modal, save widget reference |
| `open-viz-editor` | Click + Nueva Vis. | Open visualization editor modal |
| `save-visualization` | Submit viz editor | Save new visualization config to query |
| `execute-query` | Click Ejecutar | Re-run current query, refresh results |

### Dashboard Page (View + Edit)
| Callback | Trigger | Effect |
|----------|---------|--------|
| `load-dashboard` | Page load | Fetch layout + all widget data |
| `apply-filters` | Click Aplicar | Re-query all widgets with new filters |
| `auto-refresh` | Interval timer | Re-query all widgets periodically |
| `toggle-edit-mode` | Click Editar / Listo | Switch between view/edit CSS modes |
| `update-layout` | Drag/resize widget | Update widget positions in `dashboard-layout` store |
| `add-widget` | Submit add widget modal | Insert new widget into grid |
| `remove-widget` | Click ✕ on widget | Remove widget from layout |
| `save-layout` | Click Listo (exit edit) | Persist layout to DB |
| `open-ai-chat` | Click "Preguntar" FAB | Open `dbc.Offcanvas` with AI chat |
| `ai-add-to-dashboard` | Click "Agregar a este tablero" | Save AI result as widget |
| `refresh-single` | Hover widget → refresh | Re-query single widget |
| `export-widget-csv` | Widget action → export | Download widget data as CSV |

### Query List / Dashboard List
| Callback | Trigger | Effect |
|----------|---------|--------|
| `load-list` | Page load | Fetch paginated items from DB |
| `search` | Type in search | Filter items client-side or re-query |
| `filter-favorites` | Toggle favorites | Filter to starred items only |
| `filter-tags` | Select tags | Filter by tag |
| `paginate` | Click page number | Load page N of results |
| `toggle-favorite` | Click star | Update in DB |

---

## 14. Error States

| State | UI Treatment |
|-------|-------------|
| **AI unavailable** | Chat shows: "El asistente no esta disponible. Intenta mas tarde." + retry button |
| **Query timeout** | Results panel: "La consulta tardo demasiado. Intenta una pregunta mas especifica." |
| **No results** | Results panel: "No se encontraron resultados para estos filtros." + suggestion to adjust filters |
| **Network error** | Toast notification: "Error de conexion. Verifica tu conexion a internet." |
| **Auth expired** | Redirect to login / indigitall portal with message |
| **Widget load failure** | Widget shows: "Error al cargar" + retry button (doesn't break other widgets) |
| **Demo mode** | Persistent banner below navbar: "Modo demo — funcionalidad limitada" (yellow, dismissible) |

---

## 15. Responsive Breakpoints

| Breakpoint | Width | Layout Changes |
|-----------|-------|----------------|
| **Desktop** | >= 1200px | Full layout: navbar, chat panel + results side-by-side |
| **Tablet** | 768-1199px | Chat panel collapses to offcanvas, results full-width |
| **Mobile** | < 768px | Hamburger nav, stacked layout, FAB for create/chat |

### Dashboard Grid Responsive

| Breakpoint | Grid Columns | Widget Behavior |
|-----------|-------------|-----------------|
| >= 1200px | 6 columns | Full grid |
| 768-1199px | 3 columns | Widgets reflow |
| < 768px | 1 column | Widgets stack vertically |

---

## 16. Implementation Priority

### Phase A (MVP — Build First)
1. Top navbar + routing
2. Query page (AI chat + results + save)
3. Query list page
4. Dashboard view page (static grid, no drag)
5. Dashboard list page
6. Home page (favorites + recents)
7. Default "Dashboard Principal" auto-creation

### Phase B (Enhanced — Build Second)
8. Dashboard edit mode (drag/resize widgets)
9. Add Widget modal
10. Visualization editor
11. Dashboard filters (parameter passing)
12. Dashboard AI slide-over chat
13. Auto-refresh for dashboards

### Phase C (Polish — Build Third)
14. Tags system
15. Responsive mobile layout
16. Text/Markdown widgets
17. Alerts page (placeholder → functional)
18. Full-screen dashboard mode
19. Share dashboard via public link
