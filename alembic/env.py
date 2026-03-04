from __future__ import annotations

import json
import os
import subprocess
from logging.config import fileConfig
from urllib.parse import quote

from alembic import context
from sqlalchemy import engine_from_config, pool

import soma_shared.db.models  # noqa: F401
from soma_shared.db.models.base import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def _parse_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _load_dotenv(path: str) -> None:
    if not os.path.exists(path):
        return

    with open(path, "r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip()
            if (
                len(value) >= 2
                and value[0] == value[-1]
                and value[0] in {"'", '"'}
            ):
                value = value[1:-1]
            if key and key not in os.environ:
                os.environ[key] = value


def _load_candidate_env_files() -> None:
    candidate_paths = [
        os.getenv("ALEMBIC_DOTENV"),
        os.path.join(ROOT_DIR, ".env"),
        os.path.join(ROOT_DIR, "mcp_platform", ".env"),
        os.path.join(os.path.dirname(ROOT_DIR), "SOMA", "mcp_platform", ".env"),
    ]
    for path in candidate_paths:
        if path:
            _load_dotenv(path)


def _read_rds_secret(secret_id: str) -> dict[str, object]:
    cmd = [
        "aws",
        "secretsmanager",
        "get-secret-value",
        "--secret-id",
        secret_id,
        "--query",
        "SecretString",
        "--output",
        "text",
    ]
    result = subprocess.run(
        cmd,
        check=True,
        capture_output=True,
        text=True,
    )
    secret_str = result.stdout.strip()
    try:
        return json.loads(secret_str)
    except json.JSONDecodeError as exc:
        raise RuntimeError("RDS secret is not valid JSON") from exc


def _resolve_rds_url() -> str:
    secret_id = os.getenv("RDS_SECRET_ID")
    if not secret_id:
        raise RuntimeError("RDS_SECRET_ID must be set when POSTGRES_DSN is missing")

    secret = _read_rds_secret(secret_id)
    use_reader = _parse_bool(os.getenv("RDS_USE_READER"), default=False)
    reader_host = os.getenv("RDS_READER_HOST")
    writer_host = os.getenv("RDS_WRITER_HOST")
    host = None
    if use_reader and reader_host:
        host = reader_host
    elif writer_host:
        host = writer_host
    else:
        host = secret.get("host") or secret.get("hostname")
    if not host:
        raise RuntimeError("RDS secret is missing host information")

    user = secret.get("username")
    password = secret.get("password")
    if not user or not password:
        raise RuntimeError("RDS secret is missing username or password")

    db_name = (
        os.getenv("RDS_DB_NAME")
        or secret.get("dbname")
        or secret.get("db_name")
        or secret.get("database")
    )
    if not db_name:
        raise RuntimeError("RDS secret is missing database name")

    port = os.getenv("RDS_PORT") or secret.get("port") or 5432
    return (
        f"postgresql+psycopg2://{quote(str(user))}:{quote(str(password))}"
        f"@{host}:{port}/{quote(str(db_name))}"
    )


def _get_url() -> str:
    _load_candidate_env_files()
    url = os.getenv("POSTGRES_DSN")
    if not url:
        url = _resolve_rds_url()
    return url.replace("postgresql+asyncpg", "postgresql+psycopg2")


target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = _get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    url = _get_url()
    config.set_main_option("sqlalchemy.url", url.replace("%", "%%"))
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
