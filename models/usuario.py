# models/usuario.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, func
from db.database import Base


class Usuario(Base):
    __tablename__ = "usuarios"

    id            = Column(Integer, primary_key=True, autoincrement=True)
    nombre        = Column(String(100), nullable=False)
    email         = Column(String(150), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    rol           = Column(String(50), nullable=False, default="admin")  # superadmin / supervisor / admin
    activo        = Column(Boolean, nullable=False, default=True)
    creado_en     = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    # NULL solo para superadmin (acceso a todos los clubes)
    club_id       = Column(Integer, ForeignKey("clubs.id"), nullable=True)

    def __repr__(self):
        return f"<Usuario id={self.id} email={self.email} rol={self.rol} club_id={self.club_id}>"
