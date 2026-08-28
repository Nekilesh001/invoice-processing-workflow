from contextlib import contextmanager
from typing import Generator, Optional
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker, Session

from app.config import settings

Base = declarative_base()

_engine = None
_SessionLocal = None


def get_engine(db_url: Optional[str] = None):
    """Creates or returns the active SQLAlchemy engine."""
    global _engine, _SessionLocal
    url = db_url or settings.database_url

    if _engine is None or db_url is not None:
        # SQLite vs MySQL engine configurations
        if url.startswith("sqlite"):
            engine = create_engine(url, connect_args={"check_same_thread": False})
        else:
            engine = create_engine(
                url,
                pool_pre_ping=True,
                pool_recycle=3600,
                echo=False
            )

        if db_url is None:
            _engine = engine
            _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)
        return engine

    return _engine


def get_session_factory(engine=None):
    """Returns session factory for the given or default engine."""
    global _SessionLocal
    eng = engine or get_engine()
    return sessionmaker(autocommit=False, autoflush=False, bind=eng)


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=get_engine())


def get_db(db_url: Optional[str] = None) -> Generator[Session, None, None]:
    """Generator function managing database session lifecycle for FastAPI dependency injection."""
    eng = get_engine(db_url)
    session_factory = get_session_factory(eng)
    session = session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@contextmanager
def get_db_context(db_url: Optional[str] = None) -> Generator[Session, None, None]:
    """Context manager wrapper for non-FastAPI block code."""
    generator = get_db(db_url)
    session = next(generator)
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db(engine=None):
    """Initializes all database tables created via Base metadata."""
    import app.database.models  # Ensures all ORM models are registered with Base metadata
    eng = engine or get_engine()
    Base.metadata.create_all(bind=eng)
    _run_lightweight_migrations(eng)


def _run_lightweight_migrations(eng):
    """
    Best-effort, idempotent ALTER TABLE for columns added after initial deployment.
    create_all() only creates missing tables, not missing columns on existing tables,
    so pre-existing MySQL databases need this to pick up new columns without a full
    migration framework. Safe no-op if the column already exists.
    """
    statements = [
        "ALTER TABLE invoices ADD COLUMN procurement_assessment_json TEXT",
        "ALTER TABLE invoices ADD COLUMN risk_assessment_json TEXT",
    ]
    with eng.connect() as conn:
        for stmt in statements:
            try:
                conn.execute(text(stmt))
                conn.commit()
            except Exception:
                # Column already exists (or dialect doesn't need this, e.g. fresh create_all) - ignore.
                conn.rollback()
