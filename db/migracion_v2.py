# db/migracion_v2.py
"""
Migración v2: agrega columnas nuevas a 'reservas' y crea tablas 'clientes' y 'bloqueos_cancha'.
Se ejecuta automáticamente al iniciar la app (seguro de correr múltiples veces).
"""
from sqlalchemy import text
from db.database import engine, Base


def migrar():
    try:
        with engine.connect() as conn:
            conn.execute(text(
                "ALTER TABLE reservas "
                "ADD COLUMN IF NOT EXISTS estado_pago VARCHAR(20) NOT NULL DEFAULT 'pendiente'"
            ))
            conn.execute(text(
                "ALTER TABLE reservas "
                "ADD COLUMN IF NOT EXISTS grupo_recurrente_id INTEGER"
            ))
            conn.commit()

        # Crear tablas nuevas (clientes, bloqueos_cancha)
        import models.cliente       # noqa: F401
        import models.bloqueo_cancha  # noqa: F401
        Base.metadata.create_all(bind=engine)

    except Exception as e:
        print(f"[migracion_v2] {e}")
