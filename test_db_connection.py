# test_db_connection.py
# Ejecutar con: python test_db_connection.py
from db.database import probar_conexion, get_connection
from sqlalchemy import text

if probar_conexion():
    with get_connection() as session:
        resultado = session.execute(text("SELECT current_database(), current_user, version()"))
        db, user, version = resultado.fetchone()
        print(f"  Base de datos : {db}")
        print(f"  Usuario       : {user}")
        print(f"  PostgreSQL    : {version.split(',')[0]}")
