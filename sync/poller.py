# sync/poller.py
import queue
import threading
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Optional

from db.database import get_connection
from models.reserva import Reserva


# ---------------------------------------------------------------------------
# Eventos que el poller pone en la cola
# ---------------------------------------------------------------------------

@dataclass
class EventoActualizacion:
    reservas: list          # lista de objetos Reserva (detached)
    timestamp: datetime     # momento en que se obtuvo el dato

@dataclass
class EventoError:
    mensaje: str
    timestamp: datetime

@dataclass
class EventoReconexion:
    timestamp: datetime


# ---------------------------------------------------------------------------
# Poller
# ---------------------------------------------------------------------------

class ReservasPoller:
    """
    Consulta Supabase en un hilo de fondo cada `intervalo_normal` segundos.
    Los resultados se ponen en una `queue.Queue` thread-safe; la UI la drena
    con `.after()` y nunca toca Tkinter desde este hilo.

    Flujo:
      1. iniciar()   → arranca el hilo daemon
      2. detener()   → señala al hilo que pare (graceful)
      3. forzar_actualizacion() → dispara una consulta inmediata sin esperar
    """

    INTERVALO_NORMAL = 30   # segundos entre polls normales
    INTERVALO_ERROR  = 60   # segundos entre reintentos tras error

    def __init__(self):
        self.cola: queue.Queue = queue.Queue()
        self._stop_event   = threading.Event()
        self._forzar_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._ultima_actualizacion: Optional[datetime] = None
        self._con_error = False

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    def iniciar(self):
        """Arranca el hilo de polling (idempotente)."""
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._ciclo, daemon=True, name="ReservasPoller"
        )
        self._thread.start()

    def detener(self):
        """Señala al hilo que pare. No bloquea."""
        self._stop_event.set()
        self._forzar_event.set()   # desbloquear wait si está dormido

    def forzar_actualizacion(self):
        """Dispara una consulta inmediata (ej: después de crear una reserva)."""
        self._forzar_event.set()

    # ------------------------------------------------------------------
    # Hilo de fondo
    # ------------------------------------------------------------------

    def _ciclo(self):
        # Primera consulta inmediata al arrancar
        self._consultar()

        while not self._stop_event.is_set():
            intervalo = self.INTERVALO_ERROR if self._con_error else self.INTERVALO_NORMAL
            # Espera `intervalo` segundos O hasta que se fuerce una actualización
            disparado_por_forzar = self._forzar_event.wait(timeout=intervalo)
            self._forzar_event.clear()

            if self._stop_event.is_set():
                break

            self._consultar()

    def _consultar(self):
        try:
            with get_connection() as session:
                todas = session.query(Reserva).order_by(
                    Reserva.fecha, Reserva.hora_inicio
                ).all()

                reservas_serializadas = [_serializar(r) for r in todas]

            ahora = datetime.now()
            self._ultima_actualizacion = ahora

            if self._con_error:
                self._con_error = False
                self.cola.put(EventoReconexion(timestamp=ahora))

            self.cola.put(EventoActualizacion(
                reservas=reservas_serializadas,
                timestamp=ahora,
            ))

        except Exception as exc:
            self._con_error = True
            self.cola.put(EventoError(
                mensaje=str(exc),
                timestamp=datetime.now(),
            ))


def _serializar(r: Reserva) -> dict:
    """Convierte un objeto Reserva ORM en dict para pasar entre hilos."""
    return {
        "id":               r.id,
        "cancha_id":        r.cancha_id,
        "fecha":            str(r.fecha),
        "hora_inicio":      str(r.hora_inicio)[:5],
        "hora_fin":         str(r.hora_fin)[:5],
        "nombre_cliente":   r.nombre_cliente,
        "telefono_cliente": r.telefono_cliente or "",
        "estado":           r.estado,
        "notas":            r.notas or "",
        "creado_en":        str(r.creado_en),
        "creado_por":       r.creado_por,
    }
