# auth/auth_service.py
import time
import bcrypt
from db.database import get_connection
from models.usuario import Usuario

# --- Rate limiting (en memoria) ---
# { email: {"intentos": int, "bloqueado_hasta": float} }
_intentos: dict = {}

MAX_INTENTOS    = 5
BLOQUEO_SEGUNDOS = 60


def _registrar_fallo(email: str):
    estado = _intentos.get(email, {"intentos": 0, "bloqueado_hasta": 0.0})
    estado["intentos"] += 1
    if estado["intentos"] >= MAX_INTENTOS:
        estado["bloqueado_hasta"] = time.time() + BLOQUEO_SEGUNDOS
    _intentos[email] = estado


def _esta_bloqueado(email: str) -> tuple[bool, int]:
    """Retorna (bloqueado, segundos_restantes)."""
    estado = _intentos.get(email)
    if not estado:
        return False, 0
    restante = estado["bloqueado_hasta"] - time.time()
    if restante > 0:
        return True, int(restante) + 1
    return False, 0


def _limpiar_intentos(email: str):
    _intentos.pop(email, None)


def hashear_password(password: str) -> str:
    """Hashea una contraseña con bcrypt (work factor 12)."""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12)).decode()


def verificar_login(email: str, password: str):
    """
    Verifica credenciales contra la base de datos.
    Retorna el objeto Usuario si son correctas, o None si no.
    Lanza ValueError si la cuenta está bloqueada por rate limiting.
    """
    email = email.strip().lower()

    bloqueado, segundos = _esta_bloqueado(email)
    if bloqueado:
        raise ValueError(f"Demasiados intentos fallidos. Esperá {segundos} segundos.")

    with get_connection() as session:
        usuario = session.query(Usuario).filter_by(email=email, activo=True).first()

    if not usuario:
        _registrar_fallo(email)
        return None

    if not bcrypt.checkpw(password.encode(), usuario.password_hash.encode()):
        _registrar_fallo(email)
        return None

    _limpiar_intentos(email)
    return usuario


def crear_usuario(nombre: str, email: str, password: str, rol: str, usuario_actual) -> Usuario:
    """
    Crea un nuevo usuario. Solo puede ser llamado por un admin.
    Lanza PermissionError si usuario_actual no es admin.
    Lanza ValueError si el email ya existe.
    """
    if not usuario_actual or usuario_actual.rol != "admin":
        raise PermissionError("Solo un administrador puede crear usuarios.")

    email = email.strip().lower()

    with get_connection() as session:
        if session.query(Usuario).filter_by(email=email).first():
            raise ValueError(f"Ya existe un usuario con el email '{email}'.")

        nuevo = Usuario(
            nombre=nombre,
            email=email,
            password_hash=hashear_password(password),
            rol=rol,
        )
        session.add(nuevo)
        session.commit()
        session.refresh(nuevo)
        return nuevo
