# models/bloqueos_service.py
from datetime import date as date_type, datetime
from auth.session import SessionManager
from db.database import get_connection
import models.club    # noqa: F401 — necesario para que SQLAlchemy resuelva la FK bloqueos_cancha.club_id → clubs.id
from models.bloqueo_cancha import BloqueoCancha
from models.cancha import Cancha


def listar_bloqueos_futuros() -> list[tuple]:
    """
    Retorna bloqueos cuya fecha_hasta >= hoy del club activo.
    [(id, cancha_nombre, cancha_id, fecha_desde_str, fecha_hasta_str, motivo), ...]
    """
    hoy = date_type.today()
    club_id = SessionManager.get_club_id()
    with get_connection() as session:
        q = (
            session.query(BloqueoCancha, Cancha)
            .join(Cancha, BloqueoCancha.cancha_id == Cancha.id)
            .filter(BloqueoCancha.fecha_hasta >= hoy)
        )
        if club_id is not None:
            q = q.filter(BloqueoCancha.club_id == club_id)
        filas = q.order_by(BloqueoCancha.fecha_desde).all()
        return [
            (b.id, c.nombre, c.id, str(b.fecha_desde), str(b.fecha_hasta), b.motivo or "")
            for b, c in filas
        ]


def insertar_bloqueo(cancha_id: int, fecha_desde, fecha_hasta, motivo: str = "") -> int:
    if isinstance(fecha_desde, str):
        fecha_desde = datetime.strptime(fecha_desde, "%Y-%m-%d").date()
    if isinstance(fecha_hasta, str):
        fecha_hasta = datetime.strptime(fecha_hasta, "%Y-%m-%d").date()
    club_id = SessionManager.get_club_id()
    with get_connection() as session:
        b = BloqueoCancha(
            cancha_id=cancha_id,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            motivo=motivo.strip() or None,
            club_id=club_id,
        )
        session.add(b)
        session.commit()
        session.refresh(b)
        return b.id


def finalizar_bloqueo_hoy(bloqueo_id: int):
    """Adelanta fecha_hasta al día de hoy, liberando la cancha inmediatamente."""
    hoy = date_type.today()
    club_id = SessionManager.get_club_id()
    with get_connection() as session:
        q = session.query(BloqueoCancha).filter(BloqueoCancha.id == bloqueo_id)
        if club_id is not None:
            q = q.filter(BloqueoCancha.club_id == club_id)
        b = q.first()
        if b:
            b.fecha_hasta = hoy
            session.commit()


def eliminar_bloqueo(bloqueo_id: int):
    club_id = SessionManager.get_club_id()
    with get_connection() as session:
        q = session.query(BloqueoCancha).filter(BloqueoCancha.id == bloqueo_id)
        if club_id is not None:
            q = q.filter(BloqueoCancha.club_id == club_id)
        b = q.first()
        if b:
            session.delete(b)
            session.commit()


def cancha_bloqueada(cancha_id: int, fecha) -> bool:
    """Devuelve True si la cancha tiene un bloqueo activo en esa fecha."""
    if isinstance(fecha, str):
        fecha = datetime.strptime(fecha, "%Y-%m-%d").date()
    club_id = SessionManager.get_club_id()
    with get_connection() as session:
        q = session.query(BloqueoCancha).filter(
            BloqueoCancha.cancha_id == cancha_id,
            BloqueoCancha.fecha_desde <= fecha,
            BloqueoCancha.fecha_hasta >= fecha,
        )
        if club_id is not None:
            q = q.filter(BloqueoCancha.club_id == club_id)
        return q.first() is not None


def reservas_afectadas_por_bloqueo(cancha_id: int, fecha_desde, fecha_hasta) -> list:
    """Retorna reservas confirmadas que quedan dentro del rango de bloqueo."""
    from models.reserva import Reserva
    if isinstance(fecha_desde, str):
        fecha_desde = datetime.strptime(fecha_desde, "%Y-%m-%d").date()
    if isinstance(fecha_hasta, str):
        fecha_hasta = datetime.strptime(fecha_hasta, "%Y-%m-%d").date()
    club_id = SessionManager.get_club_id()
    with get_connection() as session:
        q = session.query(Reserva).filter(
            Reserva.cancha_id == cancha_id,
            Reserva.estado == "confirmada",
            Reserva.fecha >= fecha_desde,
            Reserva.fecha <= fecha_hasta,
        )
        if club_id is not None:
            q = q.filter(Reserva.club_id == club_id)
        return q.order_by(Reserva.fecha, Reserva.hora_inicio).all()
