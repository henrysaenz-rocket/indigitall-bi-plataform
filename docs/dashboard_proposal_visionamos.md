# Propuesta de Dashboard — Visionamos (Red Coopcentral)

## Contexto de Negocio

Visionamos es la plataforma tecnologica de la Red Coopcentral, una red de cooperativas financieras en Colombia. Su operacion de atencion al cliente se realiza **exclusivamente por WhatsApp Cloud API**, combinando:

- **Chatbot (Dialogflow)**: Atiende el primer contacto, clasifica intenciones, resuelve consultas simples
- **Agentes Humanos**: Atienden casos escalados (Mesa de Servicios, VirtualCoop, Red Coopcentral)
- **Notificaciones del Sistema**: Mensajes automaticos de asignacion y cierre

### Perfil de Datos (85 dias: Nov 2025 — Feb 2026)

| Metrica | Valor |
|---------|-------|
| Total Mensajes | 122,385 |
| Conversaciones | ~5,300 |
| Contactos Unicos | ~680 |
| Agentes Activos | 15 |
| Canal | WhatsApp Cloud API (unico) |
| Promedio Diario | 1,440 mensajes / 63 conversaciones / 44 contactos |
| Horario Pico | 13:00 — 22:00 (bi-modal: 15-16h y 19-21h) |
| Dias Activos | Lunes a Viernes (sabado minimo, domingo casi nulo) |
| Fallback Rate | 3.08% (excelente, meta < 15%) |

---

## Principios de Diseno

### Storytelling con Datos

El dashboard cuenta una **historia en 5 actos**, de lo general a lo especifico:

1. **Resumen Ejecutivo** (KPIs) — "Como vamos en general?"
2. **Tendencia Temporal** — "Estamos creciendo o disminuyendo?"
3. **Composicion del Servicio** — "Quien atiende: bot, agente o usuario?"
4. **Patrones de Comportamiento** — "Cuando nos contactan y que necesitan?"
5. **Rendimiento Individual** — "Como rinden nuestros agentes?"

### Principios Estadisticos

- **Comparacion temporal**: Cada KPI muestra tendencia vs periodo anterior (delta %)
- **Distribucion**: Graficos de distribucion horaria y semanal revelan patrones operativos
- **Pareto**: Top intenciones muestran el 80/20 de las necesidades del usuario
- **Proporcion**: Donut de direction muestra el ratio bot/humano/usuario
- **Ranking**: Tabla de agentes permite identificar top performers y carga desbalanceada

---

## Estructura del Dashboard

### Seccion 1: KPIs con Tendencia (Row 1)

5 tarjetas KPI, cada una con valor actual + badge de tendencia (verde/rojo):

| KPI | Icono | Descripcion | Meta |
|-----|-------|-------------|------|
| Total Mensajes | `bi-chat-left-text` | Volumen total en el periodo | Contexto |
| Contactos Unicos | `bi-people` | Personas distintas atendidas | Crecimiento |
| Conversaciones | `bi-chat-square-dots` | Sesiones de atencion | Capacidad |
| T. Espera Promedio | `bi-clock` | Segundos promedio hasta asignacion | < 60s |
| Fallback Rate | `bi-exclamation-triangle` | % de mensajes sin intencion detectada | < 15% |

**Interpretacion de tendencia**:
- Para Mensajes, Contactos, Conversaciones: subida = verde (mas demanda atendida)
- Para T. Espera y Fallback: subida = rojo (empeoramiento), bajada = verde (mejora)

### Seccion 2: Tendencia de Volumen (Row 2)

**Mensajes por Dia** — Area chart, ancho completo (md=8)
- Linea azul primaria con fill semitransparente
- Muestra la tendencia diaria de volumen
- Permite identificar picos, caidas, y patrones semanales

**Distribucion por Tipo** — Donut chart (md=4)
- Segmentos: Inbound (usuario), Agent (humano), Bot (Dialogflow), System
- Centro del donut: total de mensajes
- Muestra la proporcion de automatizacion vs atencion humana

### Seccion 3: Patrones de Comportamiento (Row 3)

**Distribucion Horaria** — Bar chart (md=6)
- Eje X: horas 0-23, Eje Y: cantidad de mensajes
- Revela los dos picos: laboral (15-16h) y nocturno (19-21h)
- Util para planificar turnos de agentes

**Actividad por Dia de Semana** — Bar chart (md=6)
- Eje X: Lun-Dom, Eje Y: cantidad de mensajes
- Muestra concentracion L-V y caida el fin de semana
- Confirma que el servicio es predominantemente laboral

### Seccion 4: Intenciones y Automatizacion (Row 4)

**Top Intenciones** — Horizontal bar chart (md=7)
- Top 10 intents por volumen
- Revela que necesitan los usuarios: Menu, Mesa Servicios, Redirect a agente
- Fallback Intent visible para monitorear problemas de comprension

**Resolucion Bot vs Humano** — Donut chart (md=5)
- Segmentos: Bot (Dialogflow), Agente Humano, Usuario (inbound), Sistema
- Indicador clave de automatizacion
- Meta: incrementar % bot sin afectar satisfaccion

### Seccion 5: Rendimiento de Agentes (Row 5)

**Tabla de Agentes** — DataTable sortable, paginada (md=12)
- Columnas: Agente, Mensajes, Conversaciones, Contactos, T.Manejo(s), T.Espera(s), Dias Activos
- Sortable por cualquier columna
- Identifica: top performers, agentes sobrecargados, tiempos de respuesta

---

## Filtros

- **Rango de Fecha**: Botones rapidos (7D, 30D, 90D) + selector personalizado
- **Tenant**: Selector global en navbar (para futuro multi-tenant)

---

## Paleta de Colores (InDigitall)

| Uso | Color |
|-----|-------|
| Area chart / lineas primarias | `#1E88E5` |
| Barras positivas / secondary | `#76C043` |
| Donut segmentos | Secuencia: `#1E88E5`, `#76C043`, `#A0A3BD`, `#42A5F5` |
| Trend badge positivo | `#76C043` (success) |
| Trend badge negativo | `#EF4444` (error) |
| Fondo de cards | `#FFFFFF` |
| Fondo de pagina | `#F5F7FA` |
| Texto principal | `#1A1A2E` |
| Texto secundario | `#6E7191` |
