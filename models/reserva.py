# models/reserva.py
from sqlalchemy import Column, Integer, String, Date, Time, DateTime, Float, ForeignKey, Index, func
from sqlalchemy.orm import relationship
from db.database import Base


class Reserva(Base):
    __tablename__ = "reservas"
    __table_args__ = (
        Index("idx_reservas_fecha",        "fecha"),
        Index("idx_reservas_cancha_fecha", "cancha_id", "fecha"),
        Index("idx_reservas_estado",       "estado"),
    )

    id               = Column(Integer, primary_key=True, autoincrement=True)
    cancha_id        = Column(Integer, ForeignKey("canchas.id", ondelete="RESTRICT"), nullable=False)
    fecha            = Column(Date, nullable=False)
    hora_inicio      = Column(Time, nullable=False)
    hora_fin         = Column(Time, nullable=False)
    nombre_cliente   = Column(String(100), nullable=False)
    telefono_cliente = Column(String(30), nullable=True)
    estado               = Column(String(30), nullable=False, default="confirmada")  # confirmada / cancelada / completada
    estado_pago          = Column(String(20), nullable=False, server_default="pendiente")  # pendiente / seña / pagado
    notas                = Column(String(500), nullable=True)
    precio_total         = Column(Float, nullable=True, default=0.0)
    grupo_recurrente_id  = Column(Integer, nullable=True)
    creado_en            = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    creado_por           = Column(Integer, ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True)
    club_id              = Column(Integer, ForeignKey("clubs.id"), nullable=False)

    cancha  = relationship("Cancha", back_populates="reservas")
    usuario = relationship("Usuario")

    def __repr__(self):
        return f"<Reserva id={self.id} cancha_id={self.cancha_id} fecha={self.fecha} {self.hora_inicio}-{self.hora_fin}>"
