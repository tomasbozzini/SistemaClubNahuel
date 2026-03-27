# auth/auth_service.py
import json
import time
import bcrypt
from pathlib import Path

from db.database import get_connection
from models.usuario import Usuario
from models.logs_service import registrar_log

# --- Persistencia de intentos fallidos ---
_DATA_DIR = Path(__file__).resolve().parent.parent / "data"
_ATTEMPTS_FILE = _DATA_DIR / "login_attempts.json"

MAX_INTENTOS     = 5
BLOQUEO_SEGUNDOS = 60


def _cargar_intentos() -> dict:
    try:
        if _ATTEMPTS_FILE.exists():
            with open(_ATTEMPTS_FILE, "r") as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def _guardar_intentos(intentos: dict):
    try:
        _DATA_DIR.mkdir(exist_ok=True)
        with open(_ATTEMPTS_FILE, "w") as f:
            json.dump(intentos, f)
    except Exception:
        pass


def _registrar_fallo(username: str):
    intentos = _cargar_intentos()
    estado = intentos.get(username, {"intentos": 0, "bloqueado_hasta": 0.0})
    estado["intentos"] += 1
    if estado["intentos"] >= MAX_INTENTOS:
        estado["bloqueado_hasta"] = time.time() + BLOQUEO_SEGUNDOS
    intentos[username] = estado
    _guardar_intentos(intentos)


def _esta_bloqueado(username: str) -> tuple[bool, int]:
    """Retorna (bloqueado, segundos_restantes)."""
    intentos = _cargar_intentos()
    estado = intentos.get(username)
    if not estado:
        return False, 0
    restante = estado["bloqueado_hasta"] - time.time()
    if restante > 0:
        return True, int(restante) + 1
    return False, 0


def _limpiar_intentos(username: str):
    intentos = _cargar_intentos()
    if username in intentos:
        del intentos[username]
        _guardar_intentos(intentos)


def hashear_password(password: str) -> str:
    """Hashea una contraseña con bcrypt (work factor 12)."""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12)).decode()


def verificar_login(username: str, password: str):
    """
    Verifica credenciales contra la base de datos usando nombre de usuario.
    Retorna el objeto Usuario si son correctas, o None si no.
    Lanza ValueError si la cuenta está bloqueada por rate limiting.
    """
    username = username.strip()

    bloqueado, segundos = _esta_bloqueado(username)
    if bloqueado:
        registrar_log("bloqueado", username=username,
                      detalle=f"cuenta bloqueada, {segundos}s restantes")
        raise ValueError(f"Demasiados intentos fallidos. Esperá {segundos} segundos.")

    with get_connection() as session:
        usuario = session.query(Usuario).filter_by(nombre=username, activo=True).first()

    if not usuario:
        _registrar_fallo(username)
        registrar_log("login_fallo", username=username, detalle="usuario no encontrado")
        return None

    if not bcrypt.checkpw(password.encode(), usuario.password_hash.encode()):
        _registrar_fallo(username)
        registrar_log("login_fallo", username=username,
                      usuario_id=usuario.id, detalle="contraseña incorrecta")
        return None

    _limpiar_intentos(username)
    registrar_log("login_ok", username=username, usuario_id=usuario.id)
    return usuario


def crear_usuario(nombre: str, email: str, password: str, rol: str, usuario_actual) -> Usuario:
    """
    Crea un nuevo usuario. Solo puede ser llamado por un admin.
    Lanza PermissionError si usuario_actual no es admin.
    Lanza ValueError si el nombre ya existe.
    """
    if not usuario_actual or usuario_actual.rol != "admin":
        raise PermissionError("Solo un administrador puede crear usuarios.")

    nombre = nombre.strip()

    with get_connection() as session:
        if session.query(Usuario).filter_by(nombre=nombre).first():
            raise ValueError(f"Ya existe un usuario con el nombre '{nombre}'.")

        nuevo = Usuario(
            nombre=nombre,
            email=email.strip().lower() if email else "",
            password_hash=hashear_password(password),
            rol=rol,
        )
        session.add(nuevo)
        session.commit()
        session.refresh(nuevo)
        return nuevo
