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

if not _cfg.has_section("database"):
    raise EnvironmentError(
        f"No se encontró la sección [database] en config.ini ({_cfg_path}). "
        "Verificá que el archivo exista y tenga el formato correcto."
    )

_db = _cfg["database"]
_CAMPOS_REQUERIDOS = ["host", "user", "password", "port", "dbname"]
_faltantes = [c for c in _CAMPOS_REQUERIDOS if c not in _db]
if _faltantes:
    raise EnvironmentError(
        f"config.ini: faltan campos requeridos en [database]: {', '.join(_faltantes)}"
    )

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
