# db/seed.py
# Inserta datos iniciales en Supabase.
# Ejecutar con: python db/seed.py

import os
import bcrypt
from dotenv import load_dotenv
from db.database import get_connection
from db.init_db import init
from models.usuario import Usuario
from models.cancha import Cancha

load_dotenv()

_ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
if not _ADMIN_PASSWORD:
    raise EnvironmentError(
        "Falta ADMIN_PASSWORD en el archivo .env. "
        "Agregá la variable antes de ejecutar seed.py."
    )


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


ADMIN = {
    "nombre": "Administrador",
    "email": "admin@clubnahuel.com",
    "password": _ADMIN_PASSWORD,
    "rol": "admin",
}

CANCHAS = [
    {"nombre": "Pádel 1",  "tipo": "padel",  "descripcion": "Cancha de pádel cubierta"},
    {"nombre": "Pádel 2",  "tipo": "padel",  "descripcion": "Cancha de pádel descubierta"},
    {"nombre": "Fútbol 1", "tipo": "futbol", "descripcion": "Cancha de fútbol 5"},
    {"nombre": "Tenis 1",  "tipo": "tenis",  "descripcion": "Cancha de tenis con polvo de ladrillo"},
    {"nombre": "Tenis 2",  "tipo": "tenis",  "descripcion": "Cancha de tenis rápida"},
]


def seed():
    # Asegurar que las tablas existen
    init()

    with get_connection() as session:
        # --- Usuario admin ---
        existe = session.query(Usuario).filter_by(email=ADMIN["email"]).first()
        if not existe:
            admin = Usuario(
                nombre=ADMIN["nombre"],
                email=ADMIN["email"],
                password_hash=hash_password(ADMIN["password"]),
                rol=ADMIN["rol"],
            )
            session.add(admin)
            print(f"  Usuario creado: {ADMIN['email']} (rol: {ADMIN['rol']})")
        else:
            print(f"  Usuario ya existe: {ADMIN['email']}")

        # --- Canchas ---
        for datos in CANCHAS:
            existe = session.query(Cancha).filter_by(nombre=datos["nombre"]).first()
            if not existe:
                session.add(Cancha(**datos))
                print(f"  Cancha creada: {datos['nombre']} ({datos['tipo']})")
            else:
                print(f"  Cancha ya existe: {datos['nombre']}")

        session.commit()
        print("Seed completado.")


if __name__ == "__main__":
    seed()
