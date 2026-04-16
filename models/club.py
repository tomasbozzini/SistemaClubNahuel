# models/club.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Date, Numeric, Text, func
from db.database import Base


class Club(Base):
    __tablename__ = "clubs"

    id                   = Column(Integer, primary_key=True, autoincrement=True)
    nombre               = Column(String(100), nullable=False)
    ciudad               = Column(String(100), nullable=True)
    plan                 = Column(String(20), nullable=False, default="basic")
    activo               = Column(Boolean, nullable=False, default=True)
    creado_en            = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    fecha_instalacion    = Column(Date, nullable=True)
    monto_implementacion = Column(Numeric(10, 2), nullable=True)
    precio_mensual       = Column(Numeric(10, 2), nullable=True)
    dia_vencimiento      = Column(Integer, default=5)
    fecha_ultimo_pago    = Column(Date, nullable=True)
    estado_pago          = Column(String(20), default="al_dia")
    notas                = Column(Text, nullable=True)
    modo_mantenimiento   = Column(Boolean, default=False)

    def __repr__(self):
        return f"<Club id={self.id} nombre={self.nombre}>"
