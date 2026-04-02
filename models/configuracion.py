# models/configuracion.py
from sqlalchemy import Column, String
from db.database import Base


class Configuracion(Base):
    __tablename__ = "configuracion"

    clave = Column(String, primary_key=True)
    valor = Column(String, nullable=False)
