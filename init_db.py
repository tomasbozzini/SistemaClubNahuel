# init_db.py
from models.models import crear_tablas, insertar_cancha, listar_canchas

if __name__ == "__main__":
    crear_tablas()
    # Insertar algunas canchas iniciales (si no querés duplicados, podés comprobar antes)
    insertar_cancha("Pádel 1", "Pádel")
    insertar_cancha("Pádel 2", "Pádel")
    insertar_cancha("Tenis 1", "Tenis")
    insertar_cancha("Fútbol 1", "Fútbol")
    print("Canchas actuales:", listar_canchas())
