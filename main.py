# main.py
if __name__ == "__main__":
    import tkinter as tk
    import threading
    from tkinter import messagebox

    try:
        # Migración en background — la ventana de login aparece de inmediato
        def _migrar_bg():
            try:
                from db.migracion_v2 import migrar
                migrar()
            except Exception:
                pass  # Fallo silencioso — la migración no es bloqueante

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
