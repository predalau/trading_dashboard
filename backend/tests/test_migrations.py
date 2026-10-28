"""Integration test for the SQL migration runner (uses the real Postgres engine)."""
import app.run_migrations as rm
from sqlalchemy import text


def test_run_migrations_is_idempotent(monkeypatch, tmp_path):
    mig_dir = tmp_path / "m"
    mig_dir.mkdir()
    fname = "9999_test_demo.sql"
    (mig_dir / fname).write_text("CREATE TABLE IF NOT EXISTS t_demo_mig (id INTEGER);")
    monkeypatch.setattr(rm, "MIGRATIONS_DIR", str(mig_dir))

    try:
        assert rm.run() == [fname]      # first run applies the file
        assert rm.run() == []           # second run applies nothing (idempotent)
    finally:
        with rm.engine.begin() as conn:
            conn.execute(text("DROP TABLE IF EXISTS t_demo_mig"))
            conn.execute(
                text("DELETE FROM schema_migrations WHERE filename = :f"), {"f": fname}
            )
