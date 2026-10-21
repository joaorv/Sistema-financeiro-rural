from typing import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings

_url = settings.DATABASE_URL
_connect_args = {"check_same_thread": False} if _url.startswith("sqlite") else {}

engine = create_engine(_url, connect_args=_connect_args, pool_pre_ping=True)

if _url.startswith("sqlite"):
    # O lower() nativo do SQLite ignora acentos (Ç, Á...); usa o do Python para buscas corretas
    @event.listens_for(engine, "connect")
    def _sqlite_lower_unicode(dbapi_conn, _record):
        dbapi_conn.create_function("lower", 1, lambda s: s.lower() if isinstance(s, str) else s, deterministic=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    """Dependência do FastAPI: abre uma sessão por requisição e garante o fechamento."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """
    Cria as tabelas que ainda não existem (não altera tabelas existentes).
    Só roda no SQLite local; no PostgreSQL (Neon) o banco é criado por db/schema.sql.
    """
    if not _url.startswith("sqlite"):
        return
    from app.db import models  # noqa: F401  (registra os models no metadata)

    Base.metadata.create_all(bind=engine)
