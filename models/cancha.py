# models/cancha.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, func
from sqlalchemy.orm import relationship
from db.database import Base


class Cancha(Base):
    __tablename__ = "canchas"

    id               = Column(Integer, primary_key=True, autoincrement=True)
    nombre           = Column(String(100), nullable=False, unique=True)
    tipo             = Column(String(50), nullable=False)   # padel / futbol / tenis
    descripcion      = Column(String(255), nullable=True)
    activa           = Column(Boolean, nullable=False, default=True)
    precio           = Column(Float, nullable=False, default=0.0)
    duracion_minutos = Column(Integer, nullable=False, default=60)
    creado_en        = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    reservas = relationship("Reserva", back_populates="cancha")

    def __repr__(self):
        return f"<Cancha id={self.id} nombre={self.nombre} tipo={self.tipo}>"
