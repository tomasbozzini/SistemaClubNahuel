# models/models.py
import os
import sqlite3
import sys
from typing import List, Tuple
from datetime import datetime, timedelta

# 📁 Ruta donde se guarda la base de datos
BASE_DIR = os.path.dirname(os.path.abspath(sys.argv[0]))
DB_PATH = os.path.join(BASE_DIR, "data", "reservas.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)


def conectar():
    """Conecta con la base de datos SQLite."""
    return sqlite3.connect(DB_PATH)


# 🧱 Crear tablas
def crear_tablas():
    """Crea las tablas necesarias si no existen."""
    conn = conectar()
    cur = conn.cursor()

    # Tabla de canchas
    cur.execute("""
    CREATE TABLE IF NOT EXISTS canchas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        tipo TEXT NOT NULL,
        estado TEXT DEFAULT 'disponible'
    )
    """)

    # Tabla de reservas
    cur.execute("""
    CREATE TABLE IF NOT EXISTS reservas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cliente TEXT NOT NULL,
        cancha_id INTEGER NOT NULL,
        fecha TEXT NOT NULL,  -- formato YYYY-MM-DD
        hora TEXT NOT NULL,   -- formato HH:MM
        observaciones TEXT,
        FOREIGN KEY (cancha_id) REFERENCES canchas(id)
    )
    """)

    conn.commit()
    conn.close()


# 🟢 Insertar una nueva cancha
def insertar_cancha(nombre: str, tipo: str):
    conn = conectar()
    cur = conn.cursor()
    cur.execute("INSERT INTO canchas (nombre, tipo) VALUES (?, ?)", (nombre, tipo))
    conn.commit()
    conn.close()


# 🔍 Listar todas las canchas (con su estado)
def listar_canchas() -> List[Tuple]:
    conn = conectar()
    cur = conn.cursor()
    cur.execute("SELECT id, nombre, tipo, estado FROM canchas ORDER BY id")
    filas = cur.fetchall()
    conn.close()
    return filas


# 🟢 Listar solo canchas disponibles
def listar_canchas_disponibles() -> List[Tuple]:
    conn = conectar()
    cur = conn.cursor()
    cur.execute("SELECT id, nombre, tipo FROM canchas WHERE estado='disponible' ORDER BY id")
    filas = cur.fetchall()
    conn.close()
    return filas


# 📅 Insertar una reserva (y marcar cancha como alquilada)
def insertar_reserva(cliente: str, cancha_id: int, fecha: str, hora: str, observaciones: str = "") -> int:
    conn = conectar()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO reservas (cliente, cancha_id, fecha, hora, observaciones)
        VALUES (?, ?, ?, ?, ?)
    """, (cliente, cancha_id, fecha, hora, observaciones))

    # Marcar cancha como alquilada
    cur.execute("UPDATE canchas SET estado='alquilada' WHERE id=?", (cancha_id,))
    conn.commit()
    reserva_id = cur.lastrowid
    conn.close()
    return reserva_id


# 📋 Listar todas las reservas
def listar_reservas() -> List[Tuple]:
    conn = conectar()
    cur = conn.cursor()
    cur.execute("""
    SELECT r.id, r.cliente, c.nombre, c.tipo, r.fecha, r.hora, r.observaciones
    FROM reservas r
    JOIN canchas c ON r.cancha_id = c.id
    ORDER BY r.fecha, r.hora
    """)
    filas = cur.fetchall()
    conn.close()
    return filas


# ⚠️ Verificar superposición de horarios
def hay_superposicion(cancha_id: int, fecha: str, hora: str) -> bool:
    """
    Verifica si ya hay una reserva que se superpone en la misma fecha
    dentro de un rango de 1 hora.
    """
    conn = conectar()
    cur = conn.cursor()

    try:
        hora_dt = datetime.strptime(hora, "%H:%M")
    except ValueError:
        conn.close()
        return False

    hora_inicio_nueva = hora_dt
    hora_fin_nueva = hora_dt + timedelta(hours=1)

    cur.execute("SELECT hora FROM reservas WHERE cancha_id = ? AND fecha = ?", (cancha_id, fecha))
    horas_reservadas = [row[0] for row in cur.fetchall()]
    conn.close()

    for h in horas_reservadas:
        try:
            h_dt = datetime.strptime(h, "%H:%M")
        except ValueError:
            continue

        hora_inicio_existente = h_dt
        hora_fin_existente = h_dt + timedelta(hours=1)

        # Si los intervalos se superponen
        if hora_inicio_nueva < hora_fin_existente and hora_fin_nueva > hora_inicio_existente:
            return True

    return False


# ❌ Eliminar una reserva (y liberar cancha)
def eliminar_reserva(reserva_id: int):
    """Elimina una reserva y vuelve la cancha a 'disponible'."""
    conn = conectar()
    cur = conn.cursor()

    # Buscar cancha asociada
    cur.execute("SELECT cancha_id FROM reservas WHERE id=?", (reserva_id,))
    fila = cur.fetchone()

    if fila:
        cancha_id = fila[0]
        # Eliminar reserva
        cur.execute("DELETE FROM reservas WHERE id=?", (reserva_id,))
        # Liberar cancha
        cur.execute("UPDATE canchas SET estado='disponible' WHERE id=?", (cancha_id,))

    conn.commit()
    conn.close()


# ⏰ Eliminar reservas vencidas automáticamente
def eliminar_reservas_expiradas():
    """
    Elimina reservas cuyo turno (hora + 1 hora) ya terminó,
    y libera automáticamente las canchas.
    """
    conn = conectar()
    cur = conn.cursor()

    ahora = datetime.now()
    cur.execute("SELECT id, cancha_id, fecha, hora FROM reservas")
    reservas = cur.fetchall()

    for reserva_id, cancha_id, fecha, hora in reservas:
        try:
            reserva_dt = datetime.strptime(f"{fecha} {hora}", "%Y-%m-%d %H:%M")
            if ahora >= reserva_dt + timedelta(hours=1):
                # Eliminar reserva vencida
                cur.execute("DELETE FROM reservas WHERE id=?", (reserva_id,))
                # Liberar cancha
                cur.execute("UPDATE canchas SET estado='disponible' WHERE id=?", (cancha_id,))
        except ValueError:
            continue

    conn.commit()
    conn.close()


# 🧹 Eliminar cancha (por su ID)
def eliminar_cancha(cancha_id: int):
    conn = conectar()
    cur = conn.cursor()
    cur.execute("DELETE FROM canchas WHERE id = ?", (cancha_id,))
    conn.commit()
    conn.close()


# 🔎 Verificar si ya existe una cancha con ese nombre
def existe_cancha(nombre: str) -> bool:
    conn = conectar()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM canchas WHERE nombre = ?", (nombre,))
    existe = cur.fetchone()[0] > 0
    conn.close()
    return existe
