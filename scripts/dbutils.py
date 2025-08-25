#!/usr/bin/env python3
# scripts/dbutils.py
# Utility for safe Postgres/SQLite database reset.
# Created according to the user's permanent Copilot Base Instructions.

from __future__ import annotations

import os
import sys
import subprocess
import traceback
from pathlib import Path

# --- Ensure Django project root is on sys.path ---
BASE_DIR = Path(__file__).resolve().parent.parent
print(f"BASE_DIR: {BASE_DIR}")
sys.path.insert(0, str(BASE_DIR))

# --- Setup Django ---
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django
from django.conf import settings

django.setup()


def run_cmd(cmd: list[str], password: str | None = None) -> None:
    """Run a shell command, optionally injecting PGPASSWORD."""
    env = os.environ.copy()
    if password:
        env["PGPASSWORD"] = password
    print(" ".join(cmd))
    subprocess.run(cmd, check=True, env=env)


def check_safety() -> None:
    """Abort if we are not in a safe environment."""
    db_conf = settings.DATABASES["default"]

    if db_conf["ENGINE"] == "django.db.backends.sqlite3":
        return  # SQLite is always safe (local file)

    if not settings.DEBUG and not os.getenv("ENABLE_REMOTE_DROP_DB"):
        raise RuntimeError("Refusing to reset DB when DEBUG=False and no override enabled")

    host = db_conf.get("HOST", "")
    if host not in {"localhost", "127.0.0.1"} and not os.getenv("ENABLE_REMOTE_DROP_DB"):
        raise RuntimeError(f"Refusing to reset remote DB host={host}")


def delete_db() -> None:
    """Drop database (Postgres or SQLite)."""
    db_conf = settings.DATABASES["default"]
    engine = db_conf["ENGINE"]

    if engine == "django.db.backends.sqlite3":
        path = db_conf["NAME"]
        if os.path.exists(path):
            print(f"Deleting SQLite DB {path}...")
            os.remove(path)
        else:
            print("SQLite DB does not exist, nothing to delete.")
        return

    if engine == "django.db.backends.postgresql":
        name = db_conf["NAME"]
        user = db_conf["USER"]
        host = db_conf.get("HOST", "localhost")
        port = db_conf.get("PORT", "5432")
        password = db_conf.get("PASSWORD")

        print(f"Terminating connections to {name}...")
        run_cmd(
            [
                "psql",
                "-d",
                "postgres",
                "-h",
                host,
                "-p",
                str(port),
                "-U",
                user,
                "-c",
                f"""
                SELECT pg_terminate_backend(pid)
                FROM pg_stat_activity
                WHERE datname = '{name}'
                  AND pid <> pg_backend_pid();
                """,
            ],
            password,
        )

        print(f"Dropping database {name}...")
        run_cmd(["dropdb", "--if-exists", name, "-h", host, "-p", str(port), "-U", user], password)
        print(f"Dropped PostgreSQL DB {name}")
        return

    raise RuntimeError(f"Unsupported DB engine: {engine}")


def create_db() -> None:
    """Create database (Postgres or SQLite)."""
    db_conf = settings.DATABASES["default"]
    engine = db_conf["ENGINE"]

    if engine == "django.db.backends.sqlite3":
        path = db_conf["NAME"]
        print(f"Creating SQLite DB {path}...")
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        open(path, "a").close()
        return

    if engine == "django.db.backends.postgresql":
        name = db_conf["NAME"]
        user = db_conf["USER"]
        host = db_conf.get("HOST", "localhost")
        port = db_conf.get("PORT", "5432")
        password = db_conf.get("PASSWORD")

        print(f"Creating database {name}...")
        run_cmd(["createdb", name, "-h", host, "-p", str(port), "-U", user], password)
        print(f"Created PostgreSQL DB {name}")
        return

    raise RuntimeError(f"Unsupported DB engine: {engine}")


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: dbutils.py [delete|create|reset]")
        sys.exit(1)

    try:
        check_safety()
        cmd = sys.argv[1]

        if cmd == "delete":
            delete_db()
        elif cmd == "create":
            create_db()
        elif cmd == "reset":
            delete_db()
            create_db()
            run_cmd([sys.executable, "manage.py", "migrate"])
            print("Database reset complete.")
        else:
            print(f"Unknown command: {cmd}")
            sys.exit(1)

    except Exception as e:
        tb = traceback.format_exc()
        print(f"❌ Error: {e}\n{tb}")
        sys.exit(1)


if __name__ == "__main__":
    main()
