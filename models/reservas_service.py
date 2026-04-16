# models/reservas_service.py

from datetime import datetime, timedelta, date, time

from sqlalchemy import and_

from auth.session import SessionManager
from db.database import get_connection
from models.cancha import Cancha
from models.reserva import Reserva


# ── Helpers ──────────────────────────────────────────────────────────────────

def _t_mins(t: time) -> int:
    """
    Convierte un time a minutos desde medianoche.
    time(0, 0) se trata como 1440 (= 24 * 60) para representar el cierre del día,
    lo que evita el problema de que '00:00' < '22:00' en comparación directa.
    """
    v = t.hour * 60 + t.minute
    return 1440 if v == 0 else v


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
    Retorna reservas con estado != 'completada' del club activo.
    Para series recurrentes, muestra solo la próxima fecha (la más cercana).
    Tupla: (id[0], nombre_cliente[1], cancha_nombre[2], tipo[3], fecha[4],
             hora_inicio[5], notas[6], telefono_cliente[7],
             estado_pago[8], grupo_recurrente_id[9])
    """
    club_id = SessionManager.get_club_id()
    with get_connection() as session:
        q = (
            session.query(Reserva, Cancha)
            .join(Cancha, Reserva.cancha_id == Cancha.id)
            .filter(Reserva.estado != "completada")
        )
        if club_id is not None:
            q = q.filter(Reserva.club_id == club_id)
        filas = q.order_by(Reserva.fecha, Reserva.hora_inicio).all()

        # Contar cuántas ocurrencias quedan por grupo recurrente
        conteo_grupo: dict[int, int] = {}
        for r, c in filas:
            if r.grupo_recurrente_id:
                conteo_grupo[r.grupo_recurrente_id] = conteo_grupo.get(r.grupo_recurrente_id, 0) + 1

        # Para reservas recurrentes: mostrar solo la próxima ocurrencia por grupo
        grupos_vistos: set[int] = set()
        resultado = []
        for r, c in filas:
            if r.grupo_recurrente_id:
                if r.grupo_recurrente_id not in grupos_vistos:
                    grupos_vistos.add(r.grupo_recurrente_id)
                    resultado.append((r, c))
            else:
                resultado.append((r, c))

        return [
            (
                r.id,
                r.nombre_cliente,
                c.nombre,
                c.tipo,
                str(r.fecha),
                str(r.hora_inicio)[:5],
                r.notas or "",
                r.telefono_cliente or "",
                r.estado_pago or "pendiente",
                r.grupo_recurrente_id,
                conteo_grupo.get(r.grupo_recurrente_id, 0) if r.grupo_recurrente_id else 0,
            )
            for r, c in resultado
        ]


def listar_reservas_por_fecha(fecha_date) -> list[tuple]:
    """
    Retorna reservas confirmadas para una fecha específica del club activo.
    [(cancha_id, cancha_nombre, hora_inicio_str, hora_fin_str, nombre_cliente, tipo), ...]
    """
    club_id = SessionManager.get_club_id()
    with get_connection() as session:
        q = (
            session.query(Reserva, Cancha)
            .join(Cancha, Reserva.cancha_id == Cancha.id)
            .filter(Reserva.fecha == fecha_date, Reserva.estado == "confirmada")
        )
        if club_id is not None:
            q = q.filter(Reserva.club_id == club_id)
        filas = q.order_by(Reserva.hora_inicio).all()
        return [
            (
                r.cancha_id,
                c.nombre,
                str(r.hora_inicio)[:5],
                str(r.hora_fin)[:5],
                r.nombre_cliente,
                c.tipo,
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
    Retorna todas las reservas (todos los estados) del club activo que coincidan con los filtros.
    Columnas: (id, cliente, cancha_nombre, tipo, fecha, hora_inicio, hora_fin,
               duracion_minutos, estado, precio_total)
    """
    club_id = SessionManager.get_club_id()
    with get_connection() as session:
        q = (
            session.query(Reserva, Cancha)
            .join(Cancha, Reserva.cancha_id == Cancha.id)
        )
        if club_id is not None:
            q = q.filter(Reserva.club_id == club_id)
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
    """Retorna totales de reservas con estado='completada' del club activo."""
    hoy = date.today()
    club_id = SessionManager.get_club_id()
    with get_connection() as session:
        q = session.query(Reserva).filter(Reserva.estado == "completada")
        if club_id is not None:
            q = q.filter(Reserva.club_id == club_id)
        completadas = q.all()
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
    telefono: str = "",
    estado_pago: str = "pendiente",
) -> int:
    """Inserta una reserva. Retorna el ID creado."""
    hora_inicio = datetime.strptime(hora, "%H:%M").time()
    usuario     = SessionManager.get_usuario_actual()
    creado_por  = usuario.id if usuario else None
    club_id     = SessionManager.get_club_id()
    _PAGOS_VALIDOS = {"pendiente", "seña", "pagado"}
    if estado_pago not in _PAGOS_VALIDOS:
        estado_pago = "pendiente"

    with get_connection() as session:
        cancha   = session.query(Cancha).filter_by(id=cancha_id).first()
        duracion = _duracion_cancha(cancha)
        hora_fin = (datetime.combine(date.today(), hora_inicio) + duracion).time()
        precio   = (cancha.precio or 0.0) if cancha else 0.0

        reserva = Reserva(
            cancha_id=cancha_id,
            fecha=datetime.strptime(fecha, "%Y-%m-%d").date(),
            hora_inicio=hora_inicio,
            hora_fin=hora_fin,
            nombre_cliente=cliente,
            telefono_cliente=telefono or None,
            notas=observaciones,
            estado="confirmada",
            estado_pago=estado_pago,
            precio_total=precio,
            creado_por=creado_por,
            club_id=club_id,
        )
        session.add(reserva)
        session.commit()
        return reserva.id


def insertar_reservas_recurrentes(
    cliente: str,
    cancha_id: int,
    fecha_inicio_str: str,
    hora: str,
    observaciones: str,
    telefono: str,
    fecha_hasta_str: str,
    estado_pago: str = "pendiente",
) -> tuple[int, int, list[str]]:
    """
    Inserta reservas semanales (mismo día de semana) desde fecha_inicio hasta fecha_hasta.
    Retorna (exitosas, conflictos, lista_fechas_conflicto).
    """
    import random
    from models.bloqueos_service import cancha_bloqueada

    fecha_inicio = datetime.strptime(fecha_inicio_str, "%Y-%m-%d").date()
    fecha_hasta  = datetime.strptime(fecha_hasta_str,  "%Y-%m-%d").date()
    hora_inicio  = datetime.strptime(hora, "%H:%M").time()
    usuario      = SessionManager.get_usuario_actual()
    creado_por   = usuario.id if usuario else None
    club_id      = SessionManager.get_club_id()

    # Generar todas las fechas con el mismo día de semana
    fechas = []
    f = fecha_inicio
    while f <= fecha_hasta:
        fechas.append(f)
        f += timedelta(weeks=1)

    _PAGOS_VALIDOS = {"pendiente", "seña", "pagado"}
    if estado_pago not in _PAGOS_VALIDOS:
        estado_pago = "pendiente"
    exitosas         = 0
    conflictos       = 0
    fechas_conflicto = []
    grupo_id         = random.randint(100_000, 2_000_000_000)

    with get_connection() as session:
        cancha   = session.query(Cancha).filter_by(id=cancha_id).first()
        duracion = _duracion_cancha(cancha)
        hora_fin = (datetime.combine(date.today(), hora_inicio) + duracion).time()
        precio   = (cancha.precio or 0.0) if cancha else 0.0

        ini_mins = _t_mins(hora_inicio)
        fin_mins = _t_mins(hora_fin)

        for f in fechas:
            if cancha_bloqueada(cancha_id, f):
                conflictos += 1
                fechas_conflicto.append(str(f))
                continue

            q = session.query(Reserva).filter(
                Reserva.cancha_id == cancha_id,
                Reserva.fecha == f,
                Reserva.estado != "completada",
            )
            if club_id is not None:
                q = q.filter(Reserva.club_id == club_id)
            reservas_dia = q.all()

            conflicto = any(
                ini_mins < _t_mins(r.hora_fin) and fin_mins > _t_mins(r.hora_inicio)
                for r in reservas_dia
            )
            if conflicto:
                conflictos += 1
                fechas_conflicto.append(str(f))
                continue

            session.add(Reserva(
                cancha_id=cancha_id,
                fecha=f,
                hora_inicio=hora_inicio,
                hora_fin=hora_fin,
                nombre_cliente=cliente,
                telefono_cliente=telefono or None,
                notas=observaciones,
                estado="confirmada",
                estado_pago=estado_pago,
                precio_total=precio,
                grupo_recurrente_id=grupo_id,
                creado_por=creado_por,
                club_id=club_id,
            ))
            exitosas += 1

        if exitosas:
            session.commit()

    return exitosas, conflictos, fechas_conflicto


def eliminar_reserva(reserva_id: int):
    club_id = SessionManager.get_club_id()
    with get_connection() as session:
        q = session.query(Reserva).filter(Reserva.id == reserva_id)
        if club_id is not None:
            q = q.filter(Reserva.club_id == club_id)
        r = q.first()
        if r:
            session.delete(r)
            session.commit()


def eliminar_reservas_futuras_del_grupo(grupo_id: int, desde_fecha):
    """Elimina todas las reservas del grupo desde desde_fecha (inclusive)."""
    if isinstance(desde_fecha, str):
        desde_fecha = datetime.strptime(desde_fecha, "%Y-%m-%d").date()
    club_id = SessionManager.get_club_id()
    with get_connection() as session:
        q = session.query(Reserva).filter(
            Reserva.grupo_recurrente_id == grupo_id,
            Reserva.fecha >= desde_fecha,
            Reserva.estado == "confirmada",
        )
        if club_id is not None:
            q = q.filter(Reserva.club_id == club_id)
        q.delete()
        session.commit()


def actualizar_estado_pago(reserva_id: int, estado_pago: str):
    """Actualiza el estado de pago de una reserva: pendiente / seña / pagado."""
    club_id = SessionManager.get_club_id()
    with get_connection() as session:
        q = session.query(Reserva).filter(Reserva.id == reserva_id)
        if club_id is not None:
            q = q.filter(Reserva.club_id == club_id)
        r = q.first()
        if r:
            r.estado_pago = estado_pago
            session.commit()


# ── Verificación de disponibilidad ───────────────────────────────────────────

def verificar_slot(cancha_id: int, fecha: str, hora: str) -> str | None:
    """
    Verifica si el slot está disponible.
    Retorna None si está libre, o un mensaje de error si no.
    """
    from models.bloqueos_service import cancha_bloqueada
    if cancha_bloqueada(cancha_id, fecha):
        return "Esa cancha está bloqueada por mantenimiento en esa fecha."
    if hay_superposicion(cancha_id, fecha, hora):
        return "Esa cancha ya está ocupada en ese horario."
    return None


# ── Overlap ───────────────────────────────────────────────────────────────────

def hay_superposicion(cancha_id: int, fecha: str, hora: str) -> bool:
    """
    Verifica superposición con reservas activas (excluye completadas).
    Usa comparación en minutos para manejar correctamente slots que terminan a las 00:00.
    """
    try:
        hora_inicio = datetime.strptime(hora, "%H:%M").time()
    except ValueError:
        return False

    fecha_date = datetime.strptime(fecha, "%Y-%m-%d").date()
    club_id = SessionManager.get_club_id()

    with get_connection() as session:
        cancha   = session.query(Cancha).filter_by(id=cancha_id).first()
        duracion = _duracion_cancha(cancha)
        hora_fin = (datetime.combine(date.today(), hora_inicio) + duracion).time()

        q = session.query(Reserva).filter(
            Reserva.cancha_id == cancha_id,
            Reserva.fecha == fecha_date,
            Reserva.estado != "completada",
        )
        if club_id is not None:
            q = q.filter(Reserva.club_id == club_id)
        reservas = q.all()

    ini = _t_mins(hora_inicio)
    fin = _t_mins(hora_fin)
    return any(ini < _t_mins(r.hora_fin) and fin > _t_mins(r.hora_inicio) for r in reservas)


# ── Slots disponibles ────────────────────────────────────────────────────────

def listar_slots_disponibles(cancha_id: int, fecha: str) -> list[str]:
    """
    Retorna lista de horarios HH:MM disponibles para reservar.
    Genera candidatos cada 30 min desde 08:00 hasta que slot+duración <= 23:00.
    Descarta: cancha bloqueada, superposición parcial o total con reservas activas,
    horarios ya pasados (si la fecha es hoy).
    """
    from models.bloqueos_service import cancha_bloqueada

    fecha_date = datetime.strptime(fecha, "%Y-%m-%d").date() if isinstance(fecha, str) else fecha
    club_id = SessionManager.get_club_id()

    if cancha_bloqueada(cancha_id, fecha_date):
        return []

    with get_connection() as session:
        cancha = session.query(Cancha).filter_by(id=cancha_id).first()
        if not cancha:
            return []
        duracion = _duracion_cancha(cancha)

        q = session.query(Reserva).filter(
            Reserva.cancha_id == cancha_id,
            Reserva.fecha == fecha_date,
            Reserva.estado != "completada",
        )
        if club_id is not None:
            q = q.filter(Reserva.club_id == club_id)
        reservas_dia = q.all()
        ocupados = [(r.hora_inicio, r.hora_fin) for r in reservas_dia]

    # Cierre = medianoche: permite slots que terminan hasta las 00:00
    cierre_dt = datetime.combine(fecha_date, time(0, 0)) + timedelta(days=1)
    ahora = datetime.now()

    # Convertir ocupados a minutos para comparación robusta (00:00 = 1440)
    ocupados_mins = [(_t_mins(ini), _t_mins(fin)) for ini, fin in ocupados]

    disponibles = []
    slot_dt = datetime.combine(fecha_date, time(8, 0))

    while True:
        slot_fin_dt = slot_dt + duracion
        if slot_fin_dt > cierre_dt:
            break
        if slot_dt > ahora:
            s_min     = slot_dt.hour * 60 + slot_dt.minute
            s_fin_min = slot_fin_dt.hour * 60 + slot_fin_dt.minute
            if s_fin_min == 0:
                s_fin_min = 1440  # 00:00 = medianoche = 24*60
            overlap = any(s_min < fin and s_fin_min > ini for ini, fin in ocupados_mins)
            if not overlap:
                disponibles.append(slot_dt.strftime("%H:%M"))
        slot_dt += timedelta(minutes=30)

    return disponibles


# ── Limpieza periódica ────────────────────────────────────────────────────────

def eliminar_reservas_expiradas():
    """
    Marca como 'completada' las reservas cuyo hora_fin ya pasó.
    No las elimina — quedan en el historial financiero.
    hora_fin == time(0,0) representa medianoche del día siguiente (fin de turno 23:00–00:00).
    Aplica a todas las reservas de todos los clubes (tarea de mantenimiento global).
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
            # hora_fin 00:00 significa medianoche del día siguiente, no el inicio del mismo día
            if r.hora_fin == time(0, 0):
                fin_dt += timedelta(days=1)
            if ahora >= fin_dt:
                r.estado = "completada"
                if not r.precio_total:
                    r.precio_total = c.precio or 0.0
                actualizadas += 1
        if actualizadas:
            session.commit()
