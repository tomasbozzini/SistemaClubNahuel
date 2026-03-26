# main.py
import os
from models.models import crear_tablas
from ui.main_window import MainWindow

# Crear carpeta data si no existe
if not os.path.exists("data"):
    os.makedirs("data")

# Crear tablas si no existen
crear_tablas()

# Iniciar app
if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()

