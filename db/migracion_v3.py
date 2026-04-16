# db/migracion_v3.py
"""
Migración v3 — multi-tenant extendido:
  - Agrega columnas de negocio a la tabla clubs
  - Crea tabla pagos_mantenimiento
  - Inicializa el club principal con datos del plan Pro
  - Seguro de correr múltiples veces (idempotente)
"""
from sqlalchemy import text
from db.database import engine


def migrar():
    try:
        with engine.connect() as conn:

            # ── 1. Nuevas columnas en clubs ───────────────────────────────────
            cols = [
                ("fecha_instalacion",    "DATE DEFAULT CURRENT_DATE"),
                ("monto_implementacion", "DECIMAL(10,2)"),
                ("precio_mensual",       "DECIMAL(10,2)"),
                ("dia_vencimiento",      "INTEGER DEFAULT 5"),
                ("fecha_ultimo_pago",    "DATE"),
                ("estado_pago",          "VARCHAR(20) DEFAULT 'al_dia'"),
                ("notas",                "TEXT"),
                ("modo_mantenimiento",   "BOOLEAN DEFAULT FALSE"),
            ]
            for col, tipo in cols:
                conn.execute(text(
                    f"ALTER TABLE clubs ADD COLUMN IF NOT EXISTS {col} {tipo}"
                ))
            conn.commit()

            # ── 2. Inicializar club principal con datos del plan Pro ──────────
            conn.execute(text("""
                UPDATE clubs SET
                    plan                 = 'pro',
                    monto_implementacion = 1200.00,
                    precio_mensual       = 60.00,
                    dia_vencimiento      = 5,
                    fecha_ultimo_pago    = CURRENT_DATE,
                    estado_pago          = 'al_dia',
                    modo_mantenimiento   = FALSE
                WHERE id = 1
                  AND precio_mensual IS NULL
            """))
            conn.commit()

            # ── 3. Tabla de pagos de mantenimiento ────────────────────────────
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS pagos_mantenimiento (
                    id         SERIAL PRIMARY KEY,
                    club_id    INTEGER NOT NULL REFERENCES clubs(id),
                    fecha_pago DATE    NOT NULL DEFAULT CURRENT_DATE,
                    monto      DECIMAL(10,2) NOT NULL,
                    periodo    VARCHAR(20),
                    notas      TEXT,
                    creado_en  TIMESTAMP DEFAULT NOW()
                )
            """))
            conn.execute(text(
                "CREATE INDEX IF NOT EXISTS idx_pagos_club "
                "ON pagos_mantenimiento(club_id)"
            ))
            conn.commit()

        print("[migracion_v3] OK — columnas de negocio aplicadas.")

    except Exception as e:
        print(f"[migracion_v3] Error: {e}")
