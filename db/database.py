# db/database.py
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase

_USER     = "postgres.shvsdftzvzknftxnbkhs"
_PASSWORD = "VhqXwb7yHkpDv0wK"
_HOST     = "aws-1-sa-east-1.pooler.supabase.com"
_PORT     = "5432"
_DBNAME   = "postgres"

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
    pool_pre_ping=True,
    pool_timeout=10,
    connect_args={"connect_timeout": 10},
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
