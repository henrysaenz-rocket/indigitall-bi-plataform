"""Dashboard AI Service — AI-powered suggestions for dashboard construction."""

import json
import logging
from typing import Dict, Any, List, Optional

from app.config import settings

logger = logging.getLogger(__name__)

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

SYSTEM_PROMPT = """Eres un asistente experto en Business Intelligence y dashboards.
Tu trabajo es ayudar a los usuarios a construir tableros analiticos efectivos.

El usuario tiene acceso a consultas guardadas que puede agregar como widgets a su tablero.
Cada consulta tiene: nombre, tipo de grafica (bar, line, pie, table), y datos.

Cuando el usuario describe que quiere ver en su tablero, debes:
1. Sugerir cuales de sus consultas disponibles son mas relevantes
2. Recomendar tipos de graficas apropiados
3. Sugerir disposicion (ancho de widgets: 4=tercio, 6=mitad, 12=completo)
4. Si no hay consultas relevantes, sugerir que consultas crear primero

Responde SIEMPRE en JSON valido con este formato:
{
    "response": "Tu explicacion en español",
    "suggestions": [
        {
            "query_id": 123,
            "title": "Nombre de la consulta",
            "description": "Por que es relevante",
            "recommended_width": 6,
            "recommended_chart": "bar"
        }
    ]
}

Si no hay consultas disponibles que coincidan, suggestions puede estar vacio
y en response explica que consultas deberian crear primero.

Responde en español colombiano, profesional pero accesible.
"""


class DashboardAIService:
    """AI service for dashboard building suggestions."""

    def __init__(self):
        self.openai_client = None
        self.anthropic_client = None

        if OPENAI_AVAILABLE and settings.has_openai_key:
            self.openai_client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)

        if ANTHROPIC_AVAILABLE and settings.has_ai_key:
            self.anthropic_client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    def suggest_dashboard(
        self,
        message: str,
        available_queries: List[Dict],
        current_widgets: List[Dict],
    ) -> Dict[str, Any]:
        """Generate dashboard suggestions based on user request."""
        queries_desc = "\n".join(
            f"- ID:{q['id']} \"{q['name']}\" ({q.get('ai_function', 'SQL')}, "
            f"{q.get('result_row_count', 0)} filas)"
            for q in available_queries
        ) if available_queries else "No hay consultas guardadas."

        current_desc = ""
        if current_widgets:
            current_desc = "\nWidgets actuales en el tablero:\n" + "\n".join(
                f"- \"{w.get('title', 'Widget')}\" (ancho={w.get('width', 6)})"
                for w in current_widgets
            )

        user_msg = (
            f"Consultas disponibles:\n{queries_desc}\n"
            f"{current_desc}\n\n"
            f"Solicitud del usuario: {message}"
        )

        # Try Anthropic first
        if self.anthropic_client:
            result = self._anthropic_suggest(user_msg)
            if result:
                return result

        # Try OpenAI
        if self.openai_client:
            result = self._openai_suggest(user_msg)
            if result:
                return result

        return {
            "response": (
                "No tengo acceso al servicio de IA en este momento. "
                "Puedes agregar consultas manualmente desde el panel lateral."
            ),
            "suggestions": [],
        }

    def _anthropic_suggest(self, user_msg: str) -> Optional[Dict[str, Any]]:
        try:
            response = self.anthropic_client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=1024,
                temperature=0.3,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_msg}],
            )
            return self._parse_response(response.content[0].text)
        except Exception as e:
            logger.warning("Anthropic dashboard AI failed: %s", e)
            return None

    def _openai_suggest(self, user_msg: str) -> Optional[Dict[str, Any]]:
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_msg},
                ],
                max_tokens=1024,
                temperature=0.3,
            )
            return self._parse_response(response.choices[0].message.content)
        except Exception as e:
            logger.warning("OpenAI dashboard AI failed: %s", e)
            return None

    @staticmethod
    def _parse_response(text: str) -> Optional[Dict[str, Any]]:
        """Parse JSON response from AI."""
        import re
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group())
                except json.JSONDecodeError:
                    pass
        return None

    def propose_additional_queries(self, message: str) -> Dict[str, Any]:
        """Suggest new queries the user could create for their dashboard."""
        user_msg = (
            f"El usuario quiere crear un tablero con este enfoque: {message}\n\n"
            "Sugiere 3-5 consultas de datos que serian utiles para este tablero. "
            "Para cada consulta sugiere: titulo, descripcion breve, y tipo de grafica ideal. "
            "Responde en JSON: {{\"suggestions\": [{{\"title\": ..., \"description\": ..., "
            "\"chart_type\": ...}}]}}"
        )

        if self.openai_client:
            try:
                response = self.openai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_msg},
                    ],
                    max_tokens=512,
                    temperature=0.5,
                )
                result = self._parse_response(response.choices[0].message.content)
                if result:
                    return result
            except Exception as e:
                logger.warning("OpenAI propose queries failed: %s", e)

        return {"suggestions": []}
