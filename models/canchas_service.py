# models/canchas_service.py
import models.reserva  # noqa: F401 — necesario para que SQLAlchemy resuelva Cancha.reservas
from db.database import get_connection
from models.cancha import Cancha


def _duracion_por_tipo(tipo: str) -> int:
    """Retorna los minutos de duración según el tipo de cancha."""
    normalizado = tipo.lower().replace("á", "a").replace("ú", "u") if tipo else ""
    return 90 if normalizado == "padel" else 60


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


def listar_canchas_con_precio() -> list[tuple]:
    """Retorna [(id, nombre, tipo, precio, duracion_minutos), ...] — solo activas."""
    with get_connection() as session:
        canchas = session.query(Cancha).filter_by(activa=True).order_by(Cancha.id).all()
        return [(c.id, c.nombre, c.tipo, c.precio, c.duracion_minutos) for c in canchas]


def insertar_cancha(nombre: str, tipo: str):
    tipo_norm = tipo.lower().replace("á", "a").replace("ú", "u")
    duracion  = _duracion_por_tipo(tipo_norm)
    with get_connection() as session:
        session.add(Cancha(nombre=nombre, tipo=tipo_norm, duracion_minutos=duracion))
        session.commit()


def actualizar_precio_cancha(cancha_id: int, precio: float):
    """Actualiza el precio de una cancha."""
    with get_connection() as session:
        c = session.query(Cancha).filter_by(id=cancha_id).first()
        if c:
            c.precio = precio
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
