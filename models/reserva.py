# models/reserva.py
from sqlalchemy import Column, Integer, String, Date, Time, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from db.database import Base


class Reserva(Base):
    __tablename__ = "reservas"

    id              = Column(Integer, primary_key=True, autoincrement=True)
    cancha_id       = Column(Integer, ForeignKey("canchas.id", ondelete="RESTRICT"), nullable=False)
    fecha           = Column(Date, nullable=False)
    hora_inicio     = Column(Time, nullable=False)
    hora_fin        = Column(Time, nullable=False)
    nombre_cliente  = Column(String(100), nullable=False)
    telefono_cliente = Column(String(30), nullable=True)
    estado          = Column(String(30), nullable=False, default="confirmada")  # confirmada / cancelada / completada
    notas           = Column(String(500), nullable=True)
    creado_en       = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    creado_por      = Column(Integer, ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True)

    cancha  = relationship("Cancha", back_populates="reservas")
    usuario = relationship("Usuario")

    def __repr__(self):
        return f"<Reserva id={self.id} cancha_id={self.cancha_id} fecha={self.fecha} {self.hora_inicio}-{self.hora_fin}>"
