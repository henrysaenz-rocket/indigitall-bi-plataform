#!/usr/bin/env python3
"""
generate_mock_data.py — Generate mock API responses for dev testing.

Creates JSON files in scripts/mock_data/ that mimic indigitall API responses.
These are used by `ingest_api.py --demo` when real API credentials are not available.

Usage:
    python scripts/generate_mock_data.py
"""

import json
import random
from datetime import datetime, timedelta
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent / "mock_data"

# Constants for realistic data generation
CHANNELS = ["SMS", "WhatsApp", "Email", "Push", "InApp"]
PROJECTS = ["visionamos", "locatel", "bosi", "demo"]
DIRECTIONS = ["Inbound", "Bot", "Agent", "Outbound", "System"]
INTENTS = [
    "saludo", "consulta_saldo", "pagos", "horarios", "soporte",
    "productos", "reclamos", "transferencias", "default_fallback",
    "despedida", "agente_humano", "estado_cuenta",
]
AGENTS = [f"agent_{i:03d}" for i in range(1, 11)]
CONTACTS = [
    {"id": f"contact_{i:04d}", "name": f"Usuario {i}"}
    for i in range(1, 201)
]
CAMPAIGN_NAMES = [
    "Bienvenida Nuevos Clientes", "Reactivacion Q1 2026",
    "Promo Navidad 2025", "Encuesta Satisfaccion",
    "Lanzamiento App v3", "Recordatorio Pago",
    "Black Friday 2025", "Dia sin IVA",
    "Cross-sell Seguros", "Referidos Premium",
]


def random_date(start_days_ago=90) -> datetime:
    return datetime.now() - timedelta(
        days=random.randint(0, start_days_ago),
        hours=random.randint(0, 23),
        minutes=random.randint(0, 59),
    )


def generate_messages(n=500) -> list:
    """Generate mock message records."""
    records = []
    for i in range(n):
        ts = random_date()
        contact = random.choice(CONTACTS)
        direction = random.choices(DIRECTIONS, weights=[30, 35, 20, 10, 5])[0]
        is_fallback = direction == "Bot" and random.random() < 0.12

        records.append({
            "message_id": f"msg_{i:06d}",
            "timestamp": ts.isoformat(),
            "date": ts.strftime("%Y-%m-%d"),
            "hour": ts.hour,
            "day_of_week": ts.strftime("%A"),
            "send_type": random.choice(["input", "output", "dialogflow", "operator"]),
            "direction": direction,
            "content_type": random.choice(["text", "interactive", "quickReplyEvent"]),
            "status": random.choice(["delivered", "read", "sent"]),
            "contact_name": contact["name"],
            "contact_id": contact["id"],
            "conversation_id": f"conv_{random.randint(1, 150):04d}",
            "agent_id": random.choice(AGENTS) if direction == "Agent" else None,
            "close_reason": random.choice(["resolved", "timeout", None]),
            "intent": random.choice(INTENTS) if direction == "Bot" else None,
            "is_fallback": is_fallback,
            "message_body": f"Mock message content #{i}",
            "is_bot": direction == "Bot",
            "is_human": direction in ("Agent", "Inbound"),
            "wait_time_seconds": random.randint(5, 120) if direction == "Agent" else None,
            "handle_time_seconds": random.randint(60, 600) if direction == "Agent" else None,
        })
    return records


def generate_contacts() -> list:
    """Generate mock contact records."""
    records = []
    for c in CONTACTS:
        first = random_date(180)
        last = random_date(10)
        records.append({
            "contact_id": c["id"],
            "contact_name": c["name"],
            "total_messages": random.randint(5, 200),
            "first_contact": first.strftime("%Y-%m-%d"),
            "last_contact": last.strftime("%Y-%m-%d"),
            "total_conversations": random.randint(1, 30),
        })
    return records


def generate_campaigns() -> list:
    """Generate mock campaign summary records."""
    records = []
    for i, name in enumerate(CAMPAIGN_NAMES):
        start = random_date(60)
        end = start + timedelta(days=random.randint(1, 30))
        total_sent = random.randint(1000, 50000)
        delivered = int(total_sent * random.uniform(0.85, 0.99))
        clicks = int(delivered * random.uniform(0.02, 0.25))
        opened = int(delivered * random.uniform(0.15, 0.45))

        records.append({
            "campana_id": f"camp_{i:03d}",
            "campana_nombre": name,
            "canal": random.choice(CHANNELS),
            "proyecto_cuenta": random.choice(PROJECTS),
            "tipo_campana": random.choice(["marketing", "transaccional", "servicio"]),
            "total_enviados": total_sent,
            "total_entregados": delivered,
            "total_clicks": clicks,
            "total_chunks": random.randint(1, 5),
            "fecha_inicio": start.strftime("%Y-%m-%d"),
            "fecha_fin": end.strftime("%Y-%m-%d"),
            "total_abiertos": opened,
            "total_rebotes": int(total_sent * random.uniform(0.01, 0.05)),
            "total_bloqueados": random.randint(0, 50),
            "total_spam": random.randint(0, 10),
            "total_desuscritos": random.randint(0, 30),
            "total_conversiones": int(clicks * random.uniform(0.05, 0.3)),
            "ctr": round(clicks / delivered * 100, 2) if delivered else 0,
            "tasa_entrega": round(delivered / total_sent * 100, 2) if total_sent else 0,
            "open_rate": round(opened / delivered * 100, 2) if delivered else 0,
            "conversion_rate": round(int(clicks * 0.15) / clicks * 100, 2) if clicks else 0,
        })
    return records


def generate_toques(n=300) -> list:
    """Generate mock toques_daily records."""
    records = []
    for i in range(n):
        dt = random_date(60)
        canal = random.choice(CHANNELS)
        enviados = random.randint(100, 5000)
        entregados = int(enviados * random.uniform(0.85, 0.99))
        clicks = int(entregados * random.uniform(0.02, 0.20))

        records.append({
            "date": dt.strftime("%Y-%m-%d"),
            "canal": canal,
            "proyecto_cuenta": random.choice(PROJECTS),
            "enviados": enviados,
            "entregados": entregados,
            "clicks": clicks,
            "chunks": random.randint(1, 3),
            "usuarios_unicos": random.randint(50, enviados),
            "abiertos": int(entregados * random.uniform(0.1, 0.4)) if canal == "Email" else None,
            "rebotes": random.randint(0, int(enviados * 0.05)),
            "bloqueados": random.randint(0, 20),
            "spam": random.randint(0, 5),
            "desuscritos": random.randint(0, 10),
            "conversiones": int(clicks * random.uniform(0.05, 0.25)),
            "ctr": round(clicks / entregados * 100, 2) if entregados else 0,
            "tasa_entrega": round(entregados / enviados * 100, 2) if enviados else 0,
            "open_rate": None,
            "conversion_rate": None,
        })
    return records


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    datasets = {
        "messages": generate_messages(500),
        "contacts": generate_contacts(),
        "campaigns": generate_campaigns(),
        "toques_daily": generate_toques(300),
    }

    for name, data in datasets.items():
        path = OUTPUT_DIR / f"{name}.json"
        with open(path, "w") as f:
            json.dump({"data": data, "count": len(data)}, f, indent=2, default=str)
        print(f"[OK] Generated {len(data)} records -> {path}")

    print(f"\nDone. Mock data written to {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
