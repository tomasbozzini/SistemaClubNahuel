# models/reservas_service.py
# Capa de servicio para reservas usando PostgreSQL (SQLAlchemy).
# Mantiene las mismas firmas que models.models para compatibilidad con la UI.

from datetime import datetime, timedelta, date, time

from sqlalchemy import and_

from auth.session import SessionManager
from db.database import get_connection
from models.cancha import Cancha
from models.reserva import Reserva


def listar_reservas() -> list[tuple]:
    """
    Retorna [(id, nombre_cliente, cancha_nombre, tipo, fecha_str, hora_inicio, notas), ...]
    ordenado por fecha y hora — mismo formato que el SQLite original.
    """
    with get_connection() as session:
        filas = (
            session.query(Reserva, Cancha)
            .join(Cancha, Reserva.cancha_id == Cancha.id)
            .order_by(Reserva.fecha, Reserva.hora_inicio)
            .all()
        )
        return [
            (
                r.id,
                r.nombre_cliente,
                c.nombre,
                c.tipo,
                str(r.fecha),
                str(r.hora_inicio)[:5],
                r.notas or "",
            )
            for r, c in filas
        ]


def insertar_reserva(
    cliente: str,
    cancha_id: int,
    fecha: str,
    hora: str,
    observaciones: str = "",
) -> int:
    """
    Inserta una reserva. hora_fin = hora_inicio + 1 hora.
    Retorna el ID de la reserva creada.
    """
    hora_inicio = datetime.strptime(hora, "%H:%M").time()
    hora_fin = (
        datetime.combine(date.today(), hora_inicio) + timedelta(hours=1)
    ).time()

    usuario = SessionManager.get_usuario_actual()
    creado_por = usuario.id if usuario else None

    with get_connection() as session:
        reserva = Reserva(
            cancha_id=cancha_id,
            fecha=datetime.strptime(fecha, "%Y-%m-%d").date(),
            hora_inicio=hora_inicio,
            hora_fin=hora_fin,
            nombre_cliente=cliente,
            notas=observaciones,
            estado="confirmada",
            creado_por=creado_por,
        )
        session.add(reserva)
        session.commit()
        return reserva.id


def eliminar_reserva(reserva_id: int):
    with get_connection() as session:
        r = session.query(Reserva).filter_by(id=reserva_id).first()
        if r:
            session.delete(r)
            session.commit()


def hay_superposicion(cancha_id: int, fecha: str, hora: str) -> bool:
    """Verifica si ya hay una reserva que se superpone en el rango [hora, hora+1h)."""
    try:
        hora_inicio = datetime.strptime(hora, "%H:%M").time()
    except ValueError:
        return False

    hora_fin = (
        datetime.combine(date.today(), hora_inicio) + timedelta(hours=1)
    ).time()
    fecha_date = datetime.strptime(fecha, "%Y-%m-%d").date()

    with get_connection() as session:
        conflicto = (
            session.query(Reserva)
            .filter(
                and_(
                    Reserva.cancha_id == cancha_id,
                    Reserva.fecha == fecha_date,
                    Reserva.hora_inicio < hora_fin,
                    Reserva.hora_fin > hora_inicio,
                )
            )
            .first()
        )
    return conflicto is not None


def eliminar_reservas_expiradas():
    """Elimina reservas cuyo hora_fin ya pasó."""
    ahora = datetime.now()
    with get_connection() as session:
        reservas = session.query(Reserva).all()
        eliminadas = 0
        for r in reservas:
            fin_dt = datetime.combine(r.fecha, r.hora_fin)
            if ahora >= fin_dt:
                session.delete(r)
                eliminadas += 1
        if eliminadas:
            session.commit()
