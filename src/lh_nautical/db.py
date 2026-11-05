"""Configuração centralizada de conexão com o PostgreSQL via SQLAlchemy e psycopg."""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING
from urllib.parse import quote_plus

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover

    def load_dotenv(dotenv_path: Path | None = None) -> bool:
        """Fallback leve para leitura de arquivo .env caso python-dotenv não esteja ativo."""
        if dotenv_path is None or not dotenv_path.is_file():
            return False
        for raw_line in dotenv_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip().strip("'\""))
        return True


if TYPE_CHECKING:
    from sqlalchemy import Engine

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")


def get_database_url() -> str:
    """Constrói a URL de conexão SQLAlchemy (driver psycopg v3) a partir do ambiente."""
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    dbname = os.getenv("POSTGRES_DB", "challenge_db")
    user = quote_plus(os.getenv("POSTGRES_USER", "challenge"))
    password = quote_plus(os.getenv("POSTGRES_PASSWORD", "mysecret"))
    return f"postgresql+psycopg://{user}:{password}@{host}:{port}/{dbname}"


def get_engine() -> Engine:
    """Retorna uma instância de Engine do SQLAlchemy com pool_pre_ping habilitado."""
    from sqlalchemy import create_engine

    return create_engine(get_database_url(), pool_pre_ping=True, future=True)


def get_data_dir() -> Path:
    """Retorna o diretório de arquivos CSV brutos."""
    raw_dir = os.getenv("DATA_DIR", "data")
    path = Path(raw_dir)
    return path if path.is_absolute() else PROJECT_ROOT / path


def get_reports_dir() -> Path:
    """Retorna o diretório de saída dos relatórios e garante sua existência."""
    raw_dir = os.getenv("REPORTS_DIR", "reports")
    path = Path(raw_dir)
    resolved = path if path.is_absolute() else PROJECT_ROOT / path
    resolved.mkdir(parents=True, exist_ok=True)
    return resolved
