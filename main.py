# main.py
if __name__ == "__main__":
    import tkinter as tk
    from tkinter import messagebox

    try:
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
