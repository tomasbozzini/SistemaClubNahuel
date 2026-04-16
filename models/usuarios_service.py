# models/usuarios_service.py
# CRUD de usuarios para el panel del Supervisor.

from auth.session import SessionManager
from db.database import get_connection
from models.usuario import Usuario
from auth.auth_service import hashear_password


def listar_admins() -> list[tuple]:
    """Retorna [(id, nombre, email, activo), ...] de admins del club activo."""
    club_id = SessionManager.get_club_id()
    with get_connection() as session:
        q = session.query(Usuario).filter(Usuario.rol == "admin")
        if club_id is not None:
            q = q.filter(Usuario.club_id == club_id)
        usuarios = q.order_by(Usuario.nombre).all()
        return [(u.id, u.nombre, u.email, u.activo) for u in usuarios]


def crear_admin(nombre: str, email: str, password: str) -> Usuario:
    """Crea un usuario con rol 'admin' para el club activo. Lanza ValueError si el nombre ya existe."""
    club_id = SessionManager.get_club_id()
    nombre  = nombre.strip()
    email   = email.strip().lower()
    with get_connection() as session:
        if session.query(Usuario).filter_by(nombre=nombre).first():
            raise ValueError(f"Ya existe un usuario con el nombre '{nombre}'.")
        if session.query(Usuario).filter_by(email=email).first():
            raise ValueError("Ya existe un usuario con ese email.")
        nuevo = Usuario(
            nombre=nombre,
            email=email,
            password_hash=hashear_password(password),
            rol="admin",
            club_id=club_id,
        )
        session.add(nuevo)
        session.commit()
        session.refresh(nuevo)
        return nuevo


def actualizar_admin(usuario_id: int, nombre: str, email: str, nueva_password: str = ""):
    """Actualiza nombre, email y opcionalmente la contraseña de un admin del club activo."""
    club_id = SessionManager.get_club_id()
    nombre  = nombre.strip()
    email   = email.strip().lower()
    with get_connection() as session:
        q = session.query(Usuario).filter(Usuario.id == usuario_id, Usuario.rol == "admin")
        if club_id is not None:
            q = q.filter(Usuario.club_id == club_id)
        u = q.first()
        if not u:
            raise ValueError("Usuario no encontrado.")
        duplicado_nombre = session.query(Usuario).filter(
            Usuario.nombre == nombre, Usuario.id != usuario_id
        ).first()
        if duplicado_nombre:
            raise ValueError(f"Ya existe un usuario con el nombre '{nombre}'.")
        u.nombre = nombre
        u.email  = email
        if nueva_password.strip():
            u.password_hash = hashear_password(nueva_password)
        session.commit()


def crear_usuario(nombre: str, email: str, password: str,
                  rol: str = "admin", club_id: int = None) -> Usuario:
    """
    Crea un usuario con el rol e club_id indicados (uso superadmin).
    Lanza ValueError si el nombre o email ya existe.
    """
    nombre = nombre.strip()
    email  = email.strip().lower()
    with get_connection() as session:
        if session.query(Usuario).filter_by(nombre=nombre).first():
            raise ValueError(f"Ya existe un usuario con el nombre '{nombre}'.")
        if session.query(Usuario).filter_by(email=email).first():
            raise ValueError("Ya existe un usuario con ese email.")
        nuevo = Usuario(
            nombre=nombre,
            email=email,
            password_hash=hashear_password(password),
            rol=rol,
            club_id=club_id,
        )
        session.add(nuevo)
        session.commit()
        session.refresh(nuevo)
        return nuevo


def eliminar_admin(usuario_id: int):
    """Elimina un usuario admin del club activo."""
    club_id = SessionManager.get_club_id()
    with get_connection() as session:
        q = session.query(Usuario).filter(Usuario.id == usuario_id, Usuario.rol == "admin")
        if club_id is not None:
            q = q.filter(Usuario.club_id == club_id)
        u = q.first()
        if u:
            session.delete(u)
            session.commit()


def restablecer_password(usuario_id: int) -> str:
    """Genera una contraseña temporal, la guarda hasheada y retorna el texto plano."""
    import secrets
    import string
    club_id = SessionManager.get_club_id()
    nueva = "".join(secrets.choice(string.ascii_letters + string.digits) for _ in range(10))
    with get_connection() as session:
        q = session.query(Usuario).filter(Usuario.id == usuario_id, Usuario.rol == "admin")
        if club_id is not None:
            q = q.filter(Usuario.club_id == club_id)
        u = q.first()
        if not u:
            raise ValueError("Usuario no encontrado.")
        u.password_hash = hashear_password(nueva)
        session.commit()
    return nueva
