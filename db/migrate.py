# db/migrate.py
# Agrega las columnas nuevas a las tablas existentes.
# Ejecutar UNA sola vez: python db/migrate.py

from sqlalchemy import text
from db.database import engine


def migrate():
    print("Ejecutando migraciones...")
    with engine.connect() as conn:
        ops = [
            ("canchas",  "precio",           "ALTER TABLE canchas ADD COLUMN precio FLOAT NOT NULL DEFAULT 0.0"),
            ("canchas",  "duracion_minutos",  "ALTER TABLE canchas ADD COLUMN duracion_minutos INTEGER NOT NULL DEFAULT 60"),
            ("reservas", "precio_total",      "ALTER TABLE reservas ADD COLUMN precio_total FLOAT DEFAULT 0.0"),
        ]
        for tabla, col, sql in ops:
            try:
                conn.execute(text(sql))
                conn.commit()
                print(f"  OK  {tabla}.{col} agregado")
            except Exception:
                conn.rollback()
                print(f"  --  {tabla}.{col} ya existe, se omite")

        # Padel = 90 min por defecto
        try:
            conn.execute(text(
                "UPDATE canchas SET duracion_minutos = 90 WHERE tipo = 'padel' AND duracion_minutos = 60"
            ))
            conn.commit()
            print("  OK  duracion_minutos de pádel actualizada a 90")
        except Exception as e:
            conn.rollback()
            print(f"  Error actualizando duraciones: {e}")

    print("Migraciones completadas.")


if __name__ == "__main__":
    migrate()
