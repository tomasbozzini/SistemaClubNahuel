# main.py
if __name__ == "__main__":
    import tkinter as tk
    import threading
    from tkinter import messagebox

    try:
        def _migrar_bg():
            """Ejecuta todas las migraciones en background al iniciar."""
            try:
                from db.migracion_v2 import migrar as migrar_v2
                migrar_v2()
            except Exception:
                pass
            try:
                from db.migracion_multitenant import migrar as migrar_mt
                migrar_mt()
            except Exception:
                pass
            try:
                from db.migracion_v3 import migrar as migrar_v3
                migrar_v3()
            except Exception:
                pass

        threading.Thread(target=_migrar_bg, daemon=True).start()

        from ui.login_window import LoginWindow
        app = LoginWindow()
        app.mainloop()
    except EnvironmentError as e:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "Error de configuración",
            f"{e}\n\nVerificá que el archivo .env exista y tenga las credenciales correctas."
        )
        root.destroy()
    except Exception as e:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "Error al iniciar",
            f"No se pudo iniciar la aplicación:\n\n{e}"
        )
        root.destroy()
