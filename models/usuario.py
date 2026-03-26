# models/usuario.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, func
from db.database import Base


class Usuario(Base):
    __tablename__ = "usuarios"

    id         = Column(Integer, primary_key=True, autoincrement=True)
    nombre     = Column(String(100), nullable=False)
    email      = Column(String(150), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    rol        = Column(String(50), nullable=False, default="operador")  # admin / operador
    activo     = Column(Boolean, nullable=False, default=True)
    creado_en  = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self):
        return f"<Usuario id={self.id} email={self.email} rol={self.rol}>"
