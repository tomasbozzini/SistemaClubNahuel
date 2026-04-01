# db/init_db.py
# Crea todas las tablas en Supabase si no existen.
# Ejecutar con: python db/init_db.py

from db.database import engine, Base

# Importar todos los modelos para que Base los registre
import models.usuario       # noqa: F401
import models.cancha        # noqa: F401
import models.reserva       # noqa: F401
import models.log_acceso    # noqa: F401
import models.cliente       # noqa: F401
import models.bloqueo_cancha  # noqa: F401


def init():
    print("Creando tablas en Supabase...")
    Base.metadata.create_all(bind=engine)
    tablas = list(Base.metadata.tables.keys())
    print(f"Tablas creadas/verificadas: {tablas}")


if __name__ == "__main__":
    init()
