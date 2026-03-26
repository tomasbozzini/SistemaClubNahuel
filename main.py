# main.py
import os
from models.models import crear_tablas

# Crear carpeta data si no existe (SQLite local)
if not os.path.exists("data"):
    os.makedirs("data")

# Crear tablas SQLite si no existen
crear_tablas()

if __name__ == "__main__":
    from ui.login_window import LoginWindow
    app = LoginWindow()
    app.mainloop()
