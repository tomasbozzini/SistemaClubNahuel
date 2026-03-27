# db/database.py
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase

load_dotenv()

_USER     = os.getenv("user")
_PASSWORD = os.getenv("password")
_HOST     = os.getenv("host")
_PORT     = os.getenv("port", "5432")
_DBNAME   = os.getenv("dbname", "postgres")

if not _HOST or not _PASSWORD:
    raise EnvironmentError(
        "Faltan variables de entorno. Asegurate de tener 'host' y 'password' en el archivo .env"
    )

DATABASE_URL = (
    f"postgresql+psycopg2://{_USER}:{_PASSWORD}"
    f"@{_HOST}:{_PORT}/{_DBNAME}"
    f"?sslmode=require"
)

engine = create_engine(
    DATABASE_URL,
    pool_size=5,
    max_overflow=10,
    pool_recycle=300,
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


class Base(DeclarativeBase):
    pass


def get_connection():
    """
    Devuelve una sesión SQLAlchemy lista para usar.

        with get_connection() as session:
            session.execute(...)
    """
    return SessionLocal()


def probar_conexion():
    """Verifica que la conexión a Supabase sea exitosa."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("Conexión exitosa a Supabase.")
        return True
    except Exception as e:
        print(f"Error al conectar con Supabase: {e}")
        return False
