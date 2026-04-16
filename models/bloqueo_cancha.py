# models/bloqueo_cancha.py
from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, func
from db.database import Base


class BloqueoCancha(Base):
    __tablename__ = "bloqueos_cancha"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    cancha_id   = Column(Integer, ForeignKey("canchas.id", ondelete="CASCADE"), nullable=False)
    fecha_desde = Column(Date, nullable=False)
    fecha_hasta = Column(Date, nullable=False)
    motivo      = Column(String(255), nullable=True)
    creado_en   = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    club_id     = Column(Integer, ForeignKey("clubs.id"), nullable=False)

    def __repr__(self):
        return f"<BloqueoCancha id={self.id} cancha_id={self.cancha_id} {self.fecha_desde}→{self.fecha_hasta} club_id={self.club_id}>"
