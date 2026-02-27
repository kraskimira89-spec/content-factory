# db: общая БД для цепочки агентов (Content Factory)
# Использование: from db import get_connection; conn = get_connection()

from pathlib import Path

# Корень проекта (родитель папки db)
PROJECT_ROOT = Path(__file__).resolve().parent.parent


def get_connection():
    """
    Возвращает подключение к PostgreSQL.
    Переменная окружения: DATABASE_URL (postgresql://user:pass@host:port/dbname)
    или POSTGRES_HOST, POSTGRES_PORT, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB.
    """
    try:
        import psycopg2
        from psycopg2.extras import RealDictCursor
    except ImportError:
        raise ImportError("Установите psycopg2-binary: pip install psycopg2-binary")

    import os
    from dotenv import load_dotenv

    env_path = PROJECT_ROOT / "config" / ".env"
    if env_path.exists():
        load_dotenv(env_path)
    load_dotenv(PROJECT_ROOT / ".env")

    url = os.getenv("DATABASE_URL")
    if url:
        return psycopg2.connect(url, cursor_factory=RealDictCursor)

    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    user = os.getenv("POSTGRES_USER", "postgres")
    password = os.getenv("POSTGRES_PASSWORD", "")
    dbname = os.getenv("POSTGRES_DB", "content_factory")
    return psycopg2.connect(
        host=host, port=port, user=user, password=password, dbname=dbname,
        cursor_factory=RealDictCursor,
    )


def is_available() -> bool:
    """Проверяет, настроена ли БД и доступна ли она."""
    try:
        conn = get_connection()
        conn.close()
        return True
    except Exception:
        return False
