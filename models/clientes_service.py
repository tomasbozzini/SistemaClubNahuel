# models/clientes_service.py
from auth.session import SessionManager
from db.database import get_connection
from models.cliente import Cliente


def listar_clientes() -> list[tuple]:
    """Retorna [(id, nombre, telefono, email), ...] ordenado por nombre."""
    club_id = SessionManager.get_club_id()
    with get_connection() as session:
        q = session.query(Cliente).order_by(Cliente.nombre)
        if club_id is not None:
            q = q.filter(Cliente.club_id == club_id)
        clientes = q.all()
        return [(c.id, c.nombre, c.telefono or "", c.email or "") for c in clientes]


def buscar_clientes(texto: str) -> list[tuple]:
    """Retorna hasta 8 clientes cuyo nombre contenga el texto (case-insensitive)."""
    if not texto or not texto.strip():
        return []
    club_id = SessionManager.get_club_id()
    with get_connection() as session:
        q = session.query(Cliente).filter(Cliente.nombre.ilike(f"%{texto.strip()}%"))
        if club_id is not None:
            q = q.filter(Cliente.club_id == club_id)
        clientes = q.order_by(Cliente.nombre).limit(8).all()
        return [(c.id, c.nombre, c.telefono or "", c.email or "") for c in clientes]


def insertar_cliente(nombre: str, telefono: str = "", email: str = "") -> int:
    club_id = SessionManager.get_club_id()
    with get_connection() as session:
        c = Cliente(
            nombre=nombre.strip(),
            telefono=telefono.strip() or None,
            email=email.strip().lower() or None,
            club_id=club_id,
        )
        session.add(c)
        session.commit()
        session.refresh(c)
        return c.id


def actualizar_cliente(cliente_id: int, nombre: str, telefono: str = "", email: str = ""):
    club_id = SessionManager.get_club_id()
    with get_connection() as session:
        q = session.query(Cliente).filter(Cliente.id == cliente_id)
        if club_id is not None:
            q = q.filter(Cliente.club_id == club_id)
        c = q.first()
        if c:
            c.nombre   = nombre.strip()
            c.telefono = telefono.strip() or None
            c.email    = email.strip().lower() or None
            session.commit()


def eliminar_cliente(cliente_id: int):
    club_id = SessionManager.get_club_id()
    with get_connection() as session:
        q = session.query(Cliente).filter(Cliente.id == cliente_id)
        if club_id is not None:
            q = q.filter(Cliente.club_id == club_id)
        c = q.first()
        if c:
            session.delete(c)
            session.commit()
