# db/migracion_multitenant.py
"""
Migración multi-tenant v3:
  - Crea la tabla 'clubs' e inserta el club inicial (id=1)
  - Agrega club_id a todas las tablas existentes
  - Asigna club_id=1 a todos los registros existentes
  - Crea índices de performance
  - Agrega restricción CHECK en usuarios para superadmin
  - Se ejecuta automáticamente al iniciar la app (seguro de correr múltiples veces).
"""
from sqlalchemy import text
from db.database import engine


def migrar():
    try:
        with engine.connect() as conn:

            # ── 1. Crear tabla clubs ──────────────────────────────────────────
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS clubs (
                    id        SERIAL PRIMARY KEY,
                    nombre    VARCHAR(100) NOT NULL,
                    ciudad    VARCHAR(100),
                    plan      VARCHAR(20) DEFAULT 'basic',
                    activo    BOOLEAN DEFAULT TRUE,
                    creado_en TIMESTAMP DEFAULT NOW()
                )
            """))
            conn.commit()

            # ── 2. Insertar club inicial si no existe ─────────────────────────
            from db.database import get_club_nombre
            _nombre_inicial = get_club_nombre()
            conn.execute(text("""
                INSERT INTO clubs (id, nombre, ciudad)
                SELECT 1, :nombre, ''
                WHERE NOT EXISTS (SELECT 1 FROM clubs WHERE id = 1)
            """), {"nombre": _nombre_inicial})
            # Avanzar la secuencia SERIAL para que el próximo INSERT auto-incremente correctamente
            conn.execute(text(
                "SELECT setval('clubs_id_seq', COALESCE((SELECT MAX(id) FROM clubs), 1), true)"
            ))
            conn.commit()

            # ── 3. Agregar club_id a cada tabla (IF NOT EXISTS) ───────────────
            tablas = [
                "usuarios",
                "canchas",
                "reservas",
                "clientes",
                "bloqueos_cancha",
                "configuracion",
            ]
            for tabla in tablas:
                conn.execute(text(
                    f"ALTER TABLE {tabla} "
                    f"ADD COLUMN IF NOT EXISTS club_id INTEGER REFERENCES clubs(id)"
                ))
            # logs_acceso sin FK (puede haber logs sin club asociado)
            conn.execute(text(
                "ALTER TABLE logs_acceso "
                "ADD COLUMN IF NOT EXISTS club_id INTEGER"
            ))
            conn.commit()

            # ── 4. Asignar club_id=1 a todos los registros existentes ─────────
            for tabla in tablas + ["logs_acceso"]:
                conn.execute(text(
                    f"UPDATE {tabla} SET club_id = 1 WHERE club_id IS NULL"
                ))
            conn.commit()

            # ── 5. NOT NULL en tablas de datos (excepto usuarios y logs) ──────
            # usuarios: superadmin tiene club_id=NULL → usamos CHECK constraint
            # logs_acceso: nullable por diseño (logs de login sin sesión activa)
            # configuracion: nullable (algunos configs son globales)
            for tabla in ("canchas", "reservas", "clientes", "bloqueos_cancha"):
                try:
                    conn.execute(text(
                        f"ALTER TABLE {tabla} ALTER COLUMN club_id SET NOT NULL"
                    ))
                    conn.commit()
                except Exception:
                    conn.rollback()

            # CHECK constraint en usuarios: solo superadmin puede tener club_id NULL
            conn.execute(text("""
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM pg_constraint
                        WHERE conname = 'chk_usuarios_club_id_rol'
                    ) THEN
                        ALTER TABLE usuarios
                        ADD CONSTRAINT chk_usuarios_club_id_rol
                        CHECK (rol = 'superadmin' OR club_id IS NOT NULL);
                    END IF;
                END $$
            """))
            conn.commit()

            # ── 6. Unique constraint en canchas: (nombre, club_id) ───────────
            # Primero eliminar el unique en nombre solo (si existe)
            conn.execute(text("""
                DO $$
                BEGIN
                    ALTER TABLE canchas DROP CONSTRAINT IF EXISTS canchas_nombre_key;
                EXCEPTION WHEN OTHERS THEN NULL;
                END $$
            """))
            conn.execute(text("""
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM pg_constraint
                        WHERE conname = 'canchas_nombre_club_unique'
                    ) THEN
                        ALTER TABLE canchas
                        ADD CONSTRAINT canchas_nombre_club_unique
                        UNIQUE (nombre, club_id);
                    END IF;
                END $$
            """))
            conn.commit()

            # ── 7. Índices de performance ─────────────────────────────────────
            indices = [
                "CREATE INDEX IF NOT EXISTS idx_canchas_club        ON canchas(club_id)",
                "CREATE INDEX IF NOT EXISTS idx_reservas_club       ON reservas(club_id)",
                "CREATE INDEX IF NOT EXISTS idx_clientes_club       ON clientes(club_id)",
                "CREATE INDEX IF NOT EXISTS idx_reservas_club_fecha ON reservas(club_id, fecha)",
                "CREATE INDEX IF NOT EXISTS idx_usuarios_club       ON usuarios(club_id)",
                "CREATE INDEX IF NOT EXISTS idx_logs_club           ON logs_acceso(club_id)",
            ]
            for idx_sql in indices:
                conn.execute(text(idx_sql))
            conn.commit()

        print("[migracion_multitenant] OK — esquema multi-tenant aplicado.")

    except Exception as e:
        print(f"[migracion_multitenant] Error: {e}")
