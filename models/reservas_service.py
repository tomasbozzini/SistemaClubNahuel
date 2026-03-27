# models/reservas_service.py

from datetime import datetime, timedelta, date, time

from sqlalchemy import and_

from auth.session import SessionManager
from db.database import get_connection
from models.cancha import Cancha
from models.reserva import Reserva


# ── Duración ──────────────────────────────────────────────────────────────────

def _duracion_cancha(cancha: Cancha) -> timedelta:
    """Usa duracion_minutos de la cancha si está seteado, sino deriva del tipo."""
    minutos = getattr(cancha, "duracion_minutos", None) or 0
    if minutos > 0:
        return timedelta(minutes=minutos)
    tipo = (cancha.tipo or "").lower().replace("á", "a").replace("ú", "u")
    return timedelta(minutes=90) if tipo == "padel" else timedelta(hours=1)


# ── Lectura (solo reservas activas/futuras) ───────────────────────────────────

def listar_reservas() -> list[tuple]:
    """
    Retorna [(id, nombre_cliente, cancha_nombre, tipo, fecha_str, hora_inicio, notas), ...]
    Solo reservas con estado != 'completada'.
    """
    with get_connection() as session:
        filas = (
            session.query(Reserva, Cancha)
            .join(Cancha, Reserva.cancha_id == Cancha.id)
            .filter(Reserva.estado != "completada")
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


# ── Historial financiero ──────────────────────────────────────────────────────

def listar_historial_financiero(
    fecha_desde=None,
    fecha_hasta=None,
    cancha_id: int = None,
) -> list[tuple]:
    """
    Retorna todas las reservas (todos los estados) que coincidan con los filtros.
    Orden: fecha desc, hora_inicio desc.
    Columnas: (id, cliente, cancha_nombre, tipo, fecha, hora_inicio, hora_fin,
               duracion_minutos, estado, precio_total)
    """
    with get_connection() as session:
        q = (
            session.query(Reserva, Cancha)
            .join(Cancha, Reserva.cancha_id == Cancha.id)
        )
        if fecha_desde:
            q = q.filter(Reserva.fecha >= fecha_desde)
        if fecha_hasta:
            q = q.filter(Reserva.fecha <= fecha_hasta)
        if cancha_id:
            q = q.filter(Reserva.cancha_id == cancha_id)

        filas = q.order_by(Reserva.fecha.desc(), Reserva.hora_inicio.desc()).all()

        return [
            (
                r.id,
                r.nombre_cliente,
                c.nombre,
                c.tipo,
                str(r.fecha),
                str(r.hora_inicio)[:5],
                str(r.hora_fin)[:5],
                c.duracion_minutos,
                r.estado,
                r.precio_total or 0.0,
            )
            for r, c in filas
        ]


def totales_financieros() -> dict:
    """
    Retorna totales de reservas con estado='completada'.
    {'hoy': X, 'mes': X, 'anio': X, 'total': X}
    """
    hoy    = date.today()
    with get_connection() as session:
        completadas = (
            session.query(Reserva)
            .filter(Reserva.estado == "completada")
            .all()
        )
        total_hoy  = sum(r.precio_total or 0 for r in completadas if r.fecha == hoy)
        total_mes  = sum(r.precio_total or 0 for r in completadas
                         if r.fecha.year == hoy.year and r.fecha.month == hoy.month)
        total_anio = sum(r.precio_total or 0 for r in completadas if r.fecha.year == hoy.year)
        total_all  = sum(r.precio_total or 0 for r in completadas)
    return {"hoy": total_hoy, "mes": total_mes, "anio": total_anio, "total": total_all}


# ── Escritura ─────────────────────────────────────────────────────────────────

def insertar_reserva(
    cliente: str,
    cancha_id: int,
    fecha: str,
    hora: str,
    observaciones: str = "",
) -> int:
    """
    Inserta una reserva. Calcula hora_fin y precio_total automáticamente.
    Retorna el ID de la reserva creada.
    """
    hora_inicio = datetime.strptime(hora, "%H:%M").time()
    usuario     = SessionManager.get_usuario_actual()
    creado_por  = usuario.id if usuario else None

    with get_connection() as session:
        cancha    = session.query(Cancha).filter_by(id=cancha_id).first()
        duracion  = _duracion_cancha(cancha)
        hora_fin  = (datetime.combine(date.today(), hora_inicio) + duracion).time()
        precio    = (cancha.precio or 0.0) if cancha else 0.0

        reserva = Reserva(
            cancha_id=cancha_id,
            fecha=datetime.strptime(fecha, "%Y-%m-%d").date(),
            hora_inicio=hora_inicio,
            hora_fin=hora_fin,
            nombre_cliente=cliente,
            notas=observaciones,
            estado="confirmada",
            precio_total=precio,
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


# ── Overlap ───────────────────────────────────────────────────────────────────

def hay_superposicion(cancha_id: int, fecha: str, hora: str) -> bool:
    """
    Verifica superposición con reservas activas (excluye completadas).
    """
    try:
        hora_inicio = datetime.strptime(hora, "%H:%M").time()
    except ValueError:
        return False

    fecha_date = datetime.strptime(fecha, "%Y-%m-%d").date()

    with get_connection() as session:
        cancha   = session.query(Cancha).filter_by(id=cancha_id).first()
        duracion = _duracion_cancha(cancha)
        hora_fin = (datetime.combine(date.today(), hora_inicio) + duracion).time()

        conflicto = (
            session.query(Reserva)
            .filter(
                and_(
                    Reserva.cancha_id == cancha_id,
                    Reserva.fecha == fecha_date,
                    Reserva.estado != "completada",
                    Reserva.hora_inicio < hora_fin,
                    Reserva.hora_fin > hora_inicio,
                )
            )
            .first()
        )
    return conflicto is not None


# ── Limpieza periódica ────────────────────────────────────────────────────────

def eliminar_reservas_expiradas():
    """
    Marca como 'completada' las reservas cuyo hora_fin ya pasó.
    Al completar, fija precio_total desde el precio actual de la cancha
    (cubre el caso en que el precio fue configurado después de crear la reserva).
    No las elimina — quedan en el historial financiero.
    """
    ahora = datetime.now()
    with get_connection() as session:
        filas = (
            session.query(Reserva, Cancha)
            .join(Cancha, Reserva.cancha_id == Cancha.id)
            .filter(Reserva.estado == "confirmada")
            .all()
        )
        actualizadas = 0
        for r, c in filas:
            fin_dt = datetime.combine(r.fecha, r.hora_fin)
            if ahora >= fin_dt:
                r.estado = "completada"
                if not r.precio_total:
                    r.precio_total = c.precio or 0.0
                actualizadas += 1
        if actualizadas:
            session.commit()
