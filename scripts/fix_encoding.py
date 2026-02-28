"""
One-time script to fix double-encoded UTF-8 text in the database.

Fixes names like "JosÃ©" → "José" (UTF-8 bytes read as Latin-1).
Applies to: messages.contact_name, contacts.contact_name, chat_conversations.agent_email
"""

import logging
from sqlalchemy import create_engine, text

from app.config import settings

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

TABLES_COLUMNS = [
    ("messages", "contact_name"),
    ("messages", "message_body"),
    ("messages", "intent"),
    ("contacts", "contact_name"),
    ("chat_conversations", "agent_email"),
]


def fix_encoding():
    """Fix double-encoded UTF-8 text using PostgreSQL convert_from/convert_to."""
    engine = create_engine(settings.DATABASE_URL)

    with engine.begin() as conn:
        for table, column in TABLES_COLUMNS:
            count_stmt = text(
                f"SELECT COUNT(*) FROM {table} "  # noqa: S608
                f"WHERE {column} ~ 'Ã' OR {column} ~ 'â' OR {column} ~ 'ð'"
            )
            count = conn.execute(count_stmt).scalar()
            logger.info("%s.%s: %d rows with corrupted encoding", table, column, count)

            if count == 0:
                continue

            update_stmt = text(
                f"UPDATE {table} "  # noqa: S608
                f"SET {column} = convert_from(convert_to({column}, 'LATIN1'), 'UTF8') "
                f"WHERE {column} ~ 'Ã' OR {column} ~ 'â' OR {column} ~ 'ð'"
            )
            result = conn.execute(update_stmt)
            logger.info("  Fixed %d rows", result.rowcount)

    logger.info("Encoding fix complete.")


if __name__ == "__main__":
    fix_encoding()
