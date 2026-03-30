# models/usuarios_service.py
# CRUD de usuarios para el panel del Supervisor.

from db.database import get_connection
from models.usuario import Usuario
from auth.auth_service import hashear_password


def listar_admins() -> list[tuple]:
    """Retorna [(id, nombre, email, activo), ...] de usuarios con rol 'admin'."""
    with get_connection() as session:
        usuarios = (
            session.query(Usuario)
            .filter_by(rol="admin")
            .order_by(Usuario.nombre)
            .all()
        )
        return [(u.id, u.nombre, u.email, u.activo) for u in usuarios]


def crear_admin(nombre: str, email: str, password: str) -> Usuario:
    """Crea un usuario con rol 'admin'. Lanza ValueError si el nombre ya existe."""
    nombre = nombre.strip()
    email  = email.strip().lower()
    with get_connection() as session:
        if session.query(Usuario).filter_by(nombre=nombre).first():
            raise ValueError(f"Ya existe un usuario con el nombre '{nombre}'.")
        if session.query(Usuario).filter_by(email=email).first():
            raise ValueError(f"Ya existe un usuario con ese email.")
        nuevo = Usuario(
            nombre=nombre,
            email=email,
            password_hash=hashear_password(password),
            rol="admin",
        )
        session.add(nuevo)
        session.commit()
        session.refresh(nuevo)
        return nuevo


def actualizar_admin(usuario_id: int, nombre: str, email: str, nueva_password: str = ""):
    """Actualiza nombre, email y opcionalmente la contraseña de un admin."""
    nombre = nombre.strip()
    email  = email.strip().lower()
    with get_connection() as session:
        u = session.query(Usuario).filter_by(id=usuario_id).first()
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


def eliminar_admin(usuario_id: int):
    """Elimina un usuario admin."""
    with get_connection() as session:
        u = session.query(Usuario).filter_by(id=usuario_id, rol="admin").first()
        if u:
            session.delete(u)
            session.commit()


def restablecer_password(usuario_id: int) -> str:
    """Genera una contraseña temporal, la guarda hasheada y retorna el texto plano."""
    import secrets
    import string
    nueva = "".join(secrets.choice(string.ascii_letters + string.digits) for _ in range(10))
    with get_connection() as session:
        u = session.query(Usuario).filter_by(id=usuario_id, rol="admin").first()
        if not u:
            raise ValueError("Usuario no encontrado.")
        u.password_hash = hashear_password(nueva)
        session.commit()
    return nueva
