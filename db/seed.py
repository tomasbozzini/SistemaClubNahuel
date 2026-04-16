# db/seed.py
# Inserta datos iniciales en Supabase.
# Ejecutar con: python db/seed.py

import bcrypt
from db.database import get_connection, get_usuario_password
from db.init_db import init
from models.usuario import Usuario
from models.cancha import Cancha

_ADMIN_PASSWORD      = get_usuario_password("admin_password")
_SUPERADMIN_PASSWORD = get_usuario_password("superadmin_password")


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


CLUB_ID = 1  # club principal

ADMIN = {
    "nombre":   "Administrador",
    "email":    "admin@sistema.local",
    "password": _ADMIN_PASSWORD,
    "rol":      "admin",
    "club_id":  CLUB_ID,
}

SUPERADMIN = {
    "nombre":   "Tomas",
    "email":    "admin@sistema.com",
    "password": _SUPERADMIN_PASSWORD,
    "rol":      "superadmin",
    "club_id":  None,
}

CANCHAS = [
    {"nombre": "Fútbol 8 vs 8",   "tipo": "futbol", "duracion_minutos": 60, "club_id": CLUB_ID},
    {"nombre": "Fútbol 6 vs 6",   "tipo": "futbol", "duracion_minutos": 60, "club_id": CLUB_ID},
    {"nombre": "Fútbol 5 vs 5",   "tipo": "futbol", "duracion_minutos": 60, "club_id": CLUB_ID},
    {"nombre": "Tenis 1",         "tipo": "tenis",  "duracion_minutos": 60, "club_id": CLUB_ID},
    {"nombre": "Tenis 2",         "tipo": "tenis",  "duracion_minutos": 60, "club_id": CLUB_ID},
    {"nombre": "Pádel Singles 1", "tipo": "padel",  "duracion_minutos": 90, "club_id": CLUB_ID},
    {"nombre": "Pádel Singles 2", "tipo": "padel",  "duracion_minutos": 90, "club_id": CLUB_ID},
    {"nombre": "Pádel 1",         "tipo": "padel",  "duracion_minutos": 90, "club_id": CLUB_ID},
    {"nombre": "Pádel 2",         "tipo": "padel",  "duracion_minutos": 90, "club_id": CLUB_ID},
    {"nombre": "Pádel 3",         "tipo": "padel",  "duracion_minutos": 90, "club_id": CLUB_ID},
    {"nombre": "Pádel 4",         "tipo": "padel",  "duracion_minutos": 90, "club_id": CLUB_ID},
    {"nombre": "Pádel 5",         "tipo": "padel",  "duracion_minutos": 90, "club_id": CLUB_ID},
    {"nombre": "Pádel 6",         "tipo": "padel",  "duracion_minutos": 90, "club_id": CLUB_ID},
]


def seed():
    init()
    from db.migracion_multitenant import migrar
    migrar()

    with get_connection() as session:
        # --- Superadmin ---
        if not session.query(Usuario).filter_by(email=SUPERADMIN["email"]).first():
            session.add(Usuario(
                nombre=SUPERADMIN["nombre"],
                email=SUPERADMIN["email"],
                password_hash=hash_password(SUPERADMIN["password"]),
                rol=SUPERADMIN["rol"],
                club_id=SUPERADMIN["club_id"],
            ))
            print(f"  Superadmin creado: {SUPERADMIN['email']}")
        else:
            print(f"  Superadmin ya existe: {SUPERADMIN['email']}")

        # --- Admin del club principal ---
        if not session.query(Usuario).filter_by(email=ADMIN["email"]).first():
            session.add(Usuario(
                nombre=ADMIN["nombre"],
                email=ADMIN["email"],
                password_hash=hash_password(ADMIN["password"]),
                rol=ADMIN["rol"],
                club_id=ADMIN["club_id"],
            ))
            print(f"  Admin creado: {ADMIN['email']} (club_id: {CLUB_ID})")
        else:
            print(f"  Admin ya existe: {ADMIN['email']}")

        # --- Canchas ---
        for datos in CANCHAS:
            if not session.query(Cancha).filter_by(nombre=datos["nombre"], club_id=datos["club_id"]).first():
                session.add(Cancha(**datos))
                print(f"  Cancha creada: {datos['nombre']}")
            else:
                print(f"  Cancha ya existe: {datos['nombre']}")

        session.commit()
        print("Seed completado.")


if __name__ == "__main__":
    seed()
