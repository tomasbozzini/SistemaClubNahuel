# auth/auth_service.py
import time
import bcrypt
from db.database import get_connection
from models.usuario import Usuario

# --- Rate limiting (en memoria) ---
# { username: {"intentos": int, "bloqueado_hasta": float} }
_intentos: dict = {}

MAX_INTENTOS    = 5
BLOQUEO_SEGUNDOS = 60


def _registrar_fallo(username: str):
    estado = _intentos.get(username, {"intentos": 0, "bloqueado_hasta": 0.0})
    estado["intentos"] += 1
    if estado["intentos"] >= MAX_INTENTOS:
        estado["bloqueado_hasta"] = time.time() + BLOQUEO_SEGUNDOS
    _intentos[username] = estado


def _esta_bloqueado(username: str) -> tuple[bool, int]:
    """Retorna (bloqueado, segundos_restantes)."""
    estado = _intentos.get(username)
    if not estado:
        return False, 0
    restante = estado["bloqueado_hasta"] - time.time()
    if restante > 0:
        return True, int(restante) + 1
    return False, 0


def _limpiar_intentos(username: str):
    _intentos.pop(username, None)


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
        raise ValueError(f"Demasiados intentos fallidos. Esperá {segundos} segundos.")

    with get_connection() as session:
        usuario = session.query(Usuario).filter_by(nombre=username, activo=True).first()

    if not usuario:
        _registrar_fallo(username)
        return None

    if not bcrypt.checkpw(password.encode(), usuario.password_hash.encode()):
        _registrar_fallo(username)
        return None

    _limpiar_intentos(username)
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
