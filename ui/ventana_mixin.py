# ui/ventana_mixin.py
import time
import customtkinter as ctk


def _get_work_area(win):
    """
    Devuelve (work_w, work_h) en píxeles lógicos (los que usa Tkinter).
    Descuenta la barra de tareas de Windows sin importar el escalado DPI.
    """
    screen_w = win.winfo_screenwidth()
    screen_h = win.winfo_screenheight()
    try:
        import ctypes, ctypes.wintypes
        # GetSystemMetrics en píxeles físicos
        phys_screen = ctypes.windll.user32.GetSystemMetrics(1)   # SM_CYSCREEN
        phys_work   = ctypes.windll.user32.GetSystemMetrics(17)  # SM_CYFULLSCREEN (sin taskbar)
        if phys_screen > 0:
            taskbar_ratio = (phys_screen - phys_work) / phys_screen
            taskbar_logical = int(screen_h * taskbar_ratio)
            work_h = screen_h - taskbar_logical - 8
        else:
            work_h = screen_h - 60
    except Exception:
        work_h = screen_h - 60
    return screen_w, work_h


def centrar_ventana(win, width, height):
    """
    Centra la ventana en el área útil real (excluye barra de tareas).
    Funciona correctamente con cualquier escalado DPI de Windows.
    Retorna (width, height) final.
    """
    work_w, work_h = _get_work_area(win)
    width  = min(width,  work_w - 20)
    height = min(height, work_h - 20)
    x = (work_w // 2) - (width  // 2)
    y = (work_h // 2) - (height // 2)
    win.geometry(f"{width}x{height}+{x}+{y}")
    return width, height

# Timeout de inactividad: 30 minutos. Aviso: 2 minutos antes.
_INACTIVIDAD_TOTAL_S = 30 * 60
_INACTIVIDAD_AVISO_S = 2  * 60
_TICK_MS             = 10_000   # cada 10 segundos revisar


class VentanaMixin:
    """Asegura que la ventana aparezca al frente al abrirse."""

    def _mostrar_ventana(self):
        self.deiconify()
        self.lift()
        self.focus_force()
        self.attributes("-topmost", True)
        self.after(100, lambda: self.attributes("-topmost", False))


class InactividadMixin:
    """
    Timeout automático de sesión por inactividad.
    - A los 28 minutos sin actividad muestra un aviso con cuenta regresiva.
    - A los 30 minutos cierra sesión automáticamente.
    - Cualquier movimiento de mouse, tecla o clic resetea el contador.

    La clase que use este mixin debe implementar _cerrar_sesion().
    Llamar a _iniciar_monitor_inactividad() después de construir la UI.
    """

    def _iniciar_monitor_inactividad(self):
        self._t_ultimo_evento = time.monotonic()
        self._aviso_inactividad = None
        self._tick_id = None
        self.bind_all("<Motion>", self._resetear_inactividad, add="+")
        self.bind_all("<Key>",    self._resetear_inactividad, add="+")
        self.bind_all("<Button>", self._resetear_inactividad, add="+")
        self._tick_inactividad()

    def _resetear_inactividad(self, event=None):
        self._t_ultimo_evento = time.monotonic()
        if self._aviso_inactividad and self._aviso_inactividad.winfo_exists():
            self._aviso_inactividad.destroy()
        self._aviso_inactividad = None

    def _tick_inactividad(self):
        try:
            elapsed  = time.monotonic() - self._t_ultimo_evento
            restante = _INACTIVIDAD_TOTAL_S - elapsed

            if restante <= 0:
                self._cerrar_sesion_por_timeout()
                return

            if restante <= _INACTIVIDAD_AVISO_S:
                if not self._aviso_inactividad or not self._aviso_inactividad.winfo_exists():
                    self._aviso_inactividad = _AvisoInactividadDialog(self, int(restante))

            # Cancelar tick anterior antes de programar el siguiente
            if self._tick_id:
                try:
                    self.after_cancel(self._tick_id)
                except Exception:
                    pass
            self._tick_id = self.after(_TICK_MS, self._tick_inactividad)
        except Exception:
            pass

    def _cerrar_sesion_por_timeout(self):
        from models.logs_service import registrar_log
        from auth.session import SessionManager
        usuario = SessionManager.get_usuario_actual()
        if usuario:
            registrar_log("timeout", username=usuario.nombre, usuario_id=usuario.id,
                          detalle="cierre automático por inactividad (30 min)")
        self._cerrar_sesion()


class _AvisoInactividadDialog(ctk.CTkToplevel):
    """Diálogo de cuenta regresiva que aparece 2 minutos antes del cierre automático."""

    def __init__(self, parent, segundos_restantes: int):
        super().__init__(parent)
        self._padre    = parent
        self._segundos = max(segundos_restantes, 0)

        self.title("Sesión por expirar")
        self.resizable(False, False)
        self.configure(fg_color="#0D0D0D")
        self.attributes("-topmost", True)
        self.transient(parent)
        self.grab_set()

        self.update_idletasks()
        w, h = 360, 210
        x = parent.winfo_rootx() + (parent.winfo_width()  // 2) - w // 2
        y = parent.winfo_rooty() + (parent.winfo_height() // 2) - h // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

        ctk.CTkFrame(self, height=4, fg_color="#FFA500", corner_radius=0).pack(fill="x")

        ctk.CTkLabel(self, text="Sesión por expirar",
            font=("Arial Black", 15, "bold"), text_color="#FFA500").pack(pady=(20, 4))
        ctk.CTkLabel(self, text="Cerramos sesión automáticamente en:",
            font=("Arial", 11), text_color="#888888").pack()

        self._lbl_cuenta = ctk.CTkLabel(self, text="",
            font=("Arial Black", 36, "bold"), text_color="#FFFFFF")
        self._lbl_cuenta.pack(pady=8)

        ctk.CTkButton(
            self, text="Seguir conectado",
            command=self._continuar,
            fg_color="#7C5CFF", hover_color="#9D84FF",
            text_color="#FFFFFF", font=("Arial Black", 12, "bold"),
            corner_radius=8, width=220, height=38,
        ).pack(pady=(4, 0))

        self._tick()

    def _fmt(self, s: int) -> str:
        m, seg = divmod(max(s, 0), 60)
        return f"{m}:{seg:02d}"

    def _tick(self):
        if not self.winfo_exists():
            return
        self._lbl_cuenta.configure(text=self._fmt(self._segundos))
        if self._segundos <= 0:
            self.destroy()
            try:
                self._padre._cerrar_sesion_por_timeout()
            except Exception:
                pass
            return
        self._segundos -= 1
        self.after(1_000, self._tick)

    def _continuar(self):
        try:
            self._padre._resetear_inactividad()
        except Exception:
            pass
        if self.winfo_exists():
            self.destroy()
