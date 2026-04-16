# models/configuracion.py
from sqlalchemy import Column, Integer, String, ForeignKey
from db.database import Base


class Configuracion(Base):
    __tablename__ = "configuracion"

    # clave sigue siendo PK global para configs del sistema (ej: latest_version, download_url)
    clave   = Column(String, primary_key=True)
    valor   = Column(String, nullable=False)
    club_id = Column(Integer, ForeignKey("clubs.id"), nullable=True)  # NULL = config global del sistema
