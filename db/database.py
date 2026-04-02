# db/database.py
import os
import sys
import configparser
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase


def _get_db_url() -> str:
    cfg = configparser.ConfigParser()

    if getattr(sys, "frozen", False):
        # Ejecutable PyInstaller: config.ini está en sys._MEIPASS
        base = sys._MEIPASS
    else:
        # Desarrollo: config.ini está en la raíz del proyecto
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    path = os.path.join(base, "config.ini")
    cfg.read(path)

    db = cfg["database"]
    return (
        f"postgresql+psycopg2://{db['user']}:{db['password']}"
        f"@{db['host']}:{db['port']}/{db['dbname']}"
        f"?sslmode=require"
    )


DATABASE_URL = _get_db_url()

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
    return SessionLocal()


def probar_conexion():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        print(f"Error al conectar con Supabase: {e}")
        return False
