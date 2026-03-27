# models/logs_service.py
import socket
from db.database import get_connection
from models.log_acceso import LogAcceso


def _get_hostname() -> str:
    try:
        return socket.gethostname()
    except Exception:
        return "desconocido"


def registrar_log(
    accion: str,
    username: str = None,
    usuario_id: int = None,
    detalle: str = None,
):
    """
    Registra un evento de acceso en la tabla logs_acceso.
    Falla silenciosamente para no interrumpir el flujo de autenticación.

    Acciones esperadas:
        login_ok      — login exitoso
        login_fallo   — contraseña o usuario incorrectos
        bloqueado     — cuenta bloqueada por rate limiting
        logout        — cierre de sesión
        timeout       — cierre automático por inactividad
    """
    try:
        with get_connection() as session:
            log = LogAcceso(
                usuario_id=usuario_id,
                username=username,
                accion=accion,
                detalle=detalle,
                hostname=_get_hostname(),
            )
            session.add(log)
            session.commit()
    except Exception as e:
        print(f"[warn] logs_service: no se pudo registrar log '{accion}': {e}")
