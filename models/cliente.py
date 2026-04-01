# models/cliente.py
from sqlalchemy import Column, Integer, String, DateTime, func
from db.database import Base


class Cliente(Base):
    __tablename__ = "clientes"

    id        = Column(Integer, primary_key=True, autoincrement=True)
    nombre    = Column(String(100), nullable=False)
    telefono  = Column(String(30), nullable=True)
    email     = Column(String(150), nullable=True)
    creado_en = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self):
        return f"<Cliente id={self.id} nombre={self.nombre}>"
