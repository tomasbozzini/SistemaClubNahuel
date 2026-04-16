# models/log_acceso.py
from sqlalchemy import Column, Integer, String, DateTime, func
from db.database import Base


class LogAcceso(Base):
    __tablename__ = "logs_acceso"

    id         = Column(Integer, primary_key=True, autoincrement=True)
    usuario_id = Column(Integer, nullable=True)   # None si el usuario no existe en la BD
    username   = Column(String(100), nullable=True)
    accion     = Column(String(50),  nullable=False)  # login_ok | login_fallo | bloqueado | logout
    detalle    = Column(String(255), nullable=True)
    hostname   = Column(String(100), nullable=True)   # equipo desde el que se conecta
    timestamp  = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    club_id    = Column(Integer, nullable=True)   # nullable: logs de login ocurren antes de establecer sesión

    def __repr__(self):
        return f"<LogAcceso id={self.id} accion={self.accion} username={self.username} club_id={self.club_id}>"
