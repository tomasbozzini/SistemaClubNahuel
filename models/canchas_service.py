# models/canchas_service.py
# Capa de servicio para canchas usando PostgreSQL (SQLAlchemy).
# Devuelve los mismos formatos de tupla que models.models para compatibilidad con la UI.

from db.database import get_connection
from models.cancha import Cancha


def listar_canchas() -> list[tuple]:
    """Retorna [(id, nombre, tipo, estado), ...] donde estado = 'disponible'|'inactiva'."""
    with get_connection() as session:
        canchas = session.query(Cancha).order_by(Cancha.id).all()
        return [(c.id, c.nombre, c.tipo, "disponible" if c.activa else "inactiva") for c in canchas]


def listar_canchas_activas() -> list[tuple]:
    """Retorna [(id, nombre, tipo), ...] — solo canchas activas."""
    with get_connection() as session:
        canchas = session.query(Cancha).filter_by(activa=True).order_by(Cancha.id).all()
        return [(c.id, c.nombre, c.tipo) for c in canchas]


def insertar_cancha(nombre: str, tipo: str):
    tipo_norm = tipo.lower().replace("á", "a").replace("ú", "u")
    with get_connection() as session:
        session.add(Cancha(nombre=nombre, tipo=tipo_norm))
        session.commit()


def eliminar_cancha(cancha_id: int):
    with get_connection() as session:
        c = session.query(Cancha).filter_by(id=cancha_id).first()
        if c:
            session.delete(c)
            session.commit()


def existe_cancha(nombre: str) -> bool:
    with get_connection() as session:
        return session.query(Cancha).filter_by(nombre=nombre).first() is not None
