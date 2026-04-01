# models/clientes_service.py
from db.database import get_connection
from models.cliente import Cliente


def listar_clientes() -> list[tuple]:
    """Retorna [(id, nombre, telefono, email), ...] ordenado por nombre."""
    with get_connection() as session:
        clientes = session.query(Cliente).order_by(Cliente.nombre).all()
        return [(c.id, c.nombre, c.telefono or "", c.email or "") for c in clientes]


def buscar_clientes(texto: str) -> list[tuple]:
    """Retorna hasta 8 clientes cuyo nombre contenga el texto (case-insensitive)."""
    with get_connection() as session:
        clientes = (
            session.query(Cliente)
            .filter(Cliente.nombre.ilike(f"%{texto}%"))
            .order_by(Cliente.nombre)
            .limit(8)
            .all()
        )
        return [(c.id, c.nombre, c.telefono or "", c.email or "") for c in clientes]


def insertar_cliente(nombre: str, telefono: str = "", email: str = "") -> int:
    with get_connection() as session:
        c = Cliente(
            nombre=nombre.strip(),
            telefono=telefono.strip() or None,
            email=email.strip().lower() or None,
        )
        session.add(c)
        session.commit()
        session.refresh(c)
        return c.id


def actualizar_cliente(cliente_id: int, nombre: str, telefono: str = "", email: str = ""):
    with get_connection() as session:
        c = session.query(Cliente).filter_by(id=cliente_id).first()
        if c:
            c.nombre   = nombre.strip()
            c.telefono = telefono.strip() or None
            c.email    = email.strip().lower() or None
            session.commit()


def eliminar_cliente(cliente_id: int):
    with get_connection() as session:
        c = session.query(Cliente).filter_by(id=cliente_id).first()
        if c:
            session.delete(c)
            session.commit()
