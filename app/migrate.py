"""Applies migrations/*.sql in lexical order, once each.

Used by the init container of the orbitly-backend deployment. Each file runs in
its own transaction and is recorded in schema_migrations. orbitly-cloud keeps a
copy of the same files under db/migrations/ for DBA review and local compose.
"""

import logging
import sys
from pathlib import Path

import psycopg

from app.config import get_settings

log = logging.getLogger("orbitly.migrate")
MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "migrations"


def _dsn() -> str:
    # SQLAlchemy URLs carry a driver suffix that libpq does not understand.
    return get_settings().database_url.replace("postgresql+psycopg://", "postgresql://", 1)


def run() -> int:
    files = sorted(MIGRATIONS_DIR.glob("*.sql"))
    with psycopg.connect(_dsn(), autocommit=True) as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS schema_migrations ("
            " version text PRIMARY KEY, applied_at timestamptz NOT NULL DEFAULT now())"
        )
        # Serialise concurrent pods: only one init container migrates at a time.
        conn.execute("SELECT pg_advisory_lock(7262001)")
        try:
            done = {r[0] for r in conn.execute("SELECT version FROM schema_migrations")}
            applied = 0
            for path in files:
                version = path.stem
                if version in done:
                    continue
                log.info("applying %s", path.name)
                with conn.transaction():
                    conn.execute(path.read_text())
                    conn.execute("INSERT INTO schema_migrations (version) VALUES (%s)", (version,))
                applied += 1
            log.info("%d migration(s) applied, %d already present", applied, len(done))
        finally:
            conn.execute("SELECT pg_advisory_unlock(7262001)")
    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    sys.exit(run())
