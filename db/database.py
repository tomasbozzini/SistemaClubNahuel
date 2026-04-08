# db/database.py
import configparser
import os
from contextlib import contextmanager

from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
_cfg = configparser.ConfigParser()
_cfg_path = os.path.join(os.path.dirname(__file__), "..", "config.ini")
_cfg.read(_cfg_path, encoding="utf-8")

_db = _cfg["database"]
_url = (
    f"postgresql+psycopg2://{_db['user']}:{_db['password']}"
    f"@{_db['host']}:{_db['port']}/{_db['dbname']}"
)

# ---------------------------------------------------------------------------
# Engine & session factory
# ---------------------------------------------------------------------------
engine = create_engine(
    _url,
    connect_args={"sslmode": "require"},
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

Base = declarative_base()

# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------

@contextmanager
def get_connection():
    """Context manager that yields a SQLAlchemy session."""
    session = SessionLocal()
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def probar_conexion() -> bool:
    """Returns True if the database is reachable, False otherwise."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
