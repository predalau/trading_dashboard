"""Apply ordered .sql files in backend/migrations exactly once.

Tracked in a schema_migrations table. Safe to run repeatedly (idempotent):
each file is applied in its own transaction and recorded; already-applied
files are skipped. The baseline schema still comes from database/schema.sql
on fresh database volumes -- migrations carry forward changes to a running DB.
"""
import os

from sqlalchemy import text

from app.database import engine

MIGRATIONS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "migrations")


def run() -> list[str]:
    """Apply any pending migrations. Returns the filenames applied this run."""
    applied: list[str] = []
    with engine.begin() as conn:
        conn.execute(
            text(
                "CREATE TABLE IF NOT EXISTS schema_migrations ("
                "filename VARCHAR(255) PRIMARY KEY, "
                "applied_at TIMESTAMP WITH TIME ZONE DEFAULT now())"
            )
        )
        done = {row[0] for row in conn.execute(text("SELECT filename FROM schema_migrations"))}

    for filename in sorted(os.listdir(MIGRATIONS_DIR)):
        if not filename.endswith(".sql") or filename in done:
            continue
        sql = open(os.path.join(MIGRATIONS_DIR, filename)).read()
        with engine.begin() as conn:
            conn.execute(text(sql))
            conn.execute(
                text("INSERT INTO schema_migrations (filename) VALUES (:f)"),
                {"f": filename},
            )
        applied.append(filename)
    return applied


if __name__ == "__main__":
    print("applied:", run())
