# ui/main_window.py
import customtkinter as ctk
from customtkinter import CTkImage
from PIL import Image
from auth.session import SessionManager
from ui.reservas_window import ReservasWindow
from ui.ver_reservas_window import VerReservasWindow
from ui.gestionar_canchas_window import GestionarCanchasWindow
from ui.calendario_reservas_window import CalendarioWindow
from sync.poller import ReservasPoller, EventoActualizacion, EventoError, EventoReconexion

POLL_CHECK_MS = 500


class MainWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.withdraw()

        if not SessionManager.esta_logueado():
            self.after(0, self._volver_login)
            return

        self.title("Sistema de Reservas - Club Nahuel")
        width, height = 900, 780
        self.geometry(f"{width}x{height}")
        self.update_idletasks()
        x = (self.winfo_screenwidth()  // 2) - (width  // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")
        self.resizable(False, False)
        self.configure(fg_color="#121212")

        self._ventana_ver: VerReservasWindow | None = None

        self.limpiar_reservas_periodicamente()
        self._build_ui()
        self._build_sync_bar()

        self._poller = ReservasPoller()
        self._poller.iniciar()
        self._procesar_cola_sync()

        self.protocol("WM_DELETE_WINDOW", self._cerrar)
        self.deiconify()

    # ── UI ───────────────────────────────────────────────────────────────────

    def _build_ui(self):
        usuario = SessionManager.get_usuario_actual()

        ctk.CTkFrame(self, height=5, fg_color="#A3F843", corner_radius=0).pack(fill="x")

        # Header
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(pady=(20, 8))

        logo_path = "assets/logoclubnahuel.png"
        logo_img = CTkImage(
            light_image=Image.open(logo_path),
            dark_image=Image.open(logo_path),
            size=(100, 82)
        )
        ctk.CTkLabel(header_frame, image=logo_img, text="").pack()
        ctk.CTkLabel(
            header_frame, text="CLUB NAHUEL",
            font=("Arial Black", 34, "bold"), text_color="#FFFFFF"
        ).pack(pady=(10, 0))
        ctk.CTkLabel(
            header_frame, text="S I S T E M A   D E   R E S E R V A S",
            font=("Arial", 11), text_color="#A3F843"
        ).pack(pady=(4, 0))

        # Chip de usuario logueado
        rol_color = "#A3F843" if usuario.rol == "admin" else "#5599FF"
        chip = ctk.CTkFrame(header_frame, fg_color="#1A1A1A", corner_radius=20)
        chip.pack(pady=(10, 0))
        ctk.CTkLabel(
            chip,
            text=f"  {usuario.nombre}  ·  {usuario.rol.upper()}  ",
            font=("Arial", 11, "bold"), text_color=rol_color
        ).pack(padx=8, pady=4)

        ctk.CTkFrame(self, height=1, fg_color="#2A2A2A", corner_radius=0).pack(
            fill="x", padx=50, pady=(16, 0))

        # Cards
        cards_frame = ctk.CTkFrame(self, fg_color="transparent")
        cards_frame.pack(pady=22)
        self._crear_card(cards_frame, "NUEVA RESERVA",  "Registrá un turno en la cancha", self.abrir_registrar,         0, 0)
        self._crear_card(cards_frame, "VER RESERVAS",   "Listado completo de turnos",      self.abrir_ver,               0, 1)
        self._crear_card(cards_frame, "CALENDARIO",     "Vista mensual de reservas",        self.abrir_calendario,        1, 0)
        self._crear_card(cards_frame, "CANCHAS",        "Gestioná las canchas del club",    self.abrir_gestionar_canchas, 1, 1)

        ctk.CTkFrame(self, height=1, fg_color="#2A2A2A", corner_radius=0).pack(
            fill="x", padx=50, pady=(8, 0))

        # Botones de acción
        botones = ctk.CTkFrame(self, fg_color="transparent")
        botones.pack(pady=12)

        ctk.CTkButton(
            botones, text="CERRAR SESIÓN", command=self._cerrar_sesion,
            fg_color="transparent", hover_color="#1E1E1E",
            text_color="#FFA500", border_color="#FFA500", border_width=2,
            corner_radius=8, width=160, height=38, font=("Arial", 12, "bold")
        ).pack(side="left", padx=8)

        ctk.CTkButton(
            botones, text="SALIR", command=self._cerrar,
            fg_color="transparent", hover_color="#1E1E1E",
            text_color="#FF5C5C", border_color="#FF5C5C", border_width=2,
            corner_radius=8, width=130, height=38, font=("Arial", 12, "bold")
        ).pack(side="left", padx=8)

    # ── Barra de sync ────────────────────────────────────────────────────────

    def _build_sync_bar(self):
        barra = ctk.CTkFrame(self, fg_color="#0E0E0E", corner_radius=0, height=28)
        barra.pack(fill="x", side="bottom")
        barra.pack_propagate(False)
        self._lbl_sync = ctk.CTkLabel(
            barra, text="● Conectando...",
            font=("Arial", 10), text_color="#555555"
        )
        self._lbl_sync.pack(side="right", padx=14)

    def _set_sync_ok(self, timestamp):
        self._lbl_sync.configure(
            text=f"● Sincronizado  {timestamp.strftime('%H:%M:%S')}",
            text_color="#A3F843"
        )

    def _set_sync_error(self):
        self._lbl_sync.configure(
            text="⚠  Sin conexión — reintentando en 60s",
            text_color="#FFA500"
        )

    def _set_sync_reconectado(self, timestamp):
        self._lbl_sync.configure(
            text=f"● Reconectado  {timestamp.strftime('%H:%M:%S')}",
            text_color="#A3F843"
        )

    # ── Loop de drenado de cola ──────────────────────────────────────────────

    def _procesar_cola_sync(self):
        try:
            while True:
                evento = self._poller.cola.get_nowait()
                if isinstance(evento, EventoActualizacion):
                    self._set_sync_ok(evento.timestamp)
                    self._refrescar_ventana_ver()
                elif isinstance(evento, EventoError):
                    self._set_sync_error()
                elif isinstance(evento, EventoReconexion):
                    self._set_sync_reconectado(evento.timestamp)
        except Exception:
            pass
        try:
            self.after(POLL_CHECK_MS, self._procesar_cola_sync)
        except Exception:
            pass

    def _refrescar_ventana_ver(self):
        if self._ventana_ver and self._ventana_ver.winfo_exists():
            self._ventana_ver.cargar_reservas()

    # ── Apertura de sub-ventanas ─────────────────────────────────────────────

    def abrir_registrar(self):
        win = ReservasWindow(self)
        win.bind("<<ReservaGuardada>>", lambda e: self._poller.forzar_actualizacion())

    def abrir_ver(self):
        if self._ventana_ver and self._ventana_ver.winfo_exists():
            self._ventana_ver.lift()
            return
        self._ventana_ver = VerReservasWindow(self)

    def abrir_gestionar_canchas(self):
        GestionarCanchasWindow(self)

    def abrir_calendario(self):
        CalendarioWindow(self)

    # ── Ciclos periódicos ────────────────────────────────────────────────────

    def limpiar_reservas_periodicamente(self):
        from models.reservas_service import eliminar_reservas_expiradas
        try:
            eliminar_reservas_expiradas()
        except Exception:
            pass
        self.after(60000, self.limpiar_reservas_periodicamente)

    # ── Cierre y logout ──────────────────────────────────────────────────────

    def _cerrar_sesion(self):
        self._poller.detener()
        SessionManager.cerrar_sesion()
        self._volver_login()

    def _volver_login(self):
        self.master.deiconify()
        self.destroy()

    def _cerrar(self):
        self._poller.detener()
        SessionManager.cerrar_sesion()
        self.master.quit()

    # ── Cards ────────────────────────────────────────────────────────────────

    def _crear_card(self, parent, titulo, subtitulo, comando, row, col):
        card = ctk.CTkFrame(
            parent, width=370, height=125,
            fg_color="#1A1A1A", corner_radius=14,
            border_width=1, border_color="#2A2A2A"
        )
        card.grid(row=row, column=col, padx=14, pady=14)
        card.grid_propagate(False)

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.place(relx=0.5, rely=0.5, anchor="center")

        lbl_titulo = ctk.CTkLabel(
            inner, text=titulo,
            font=("Arial Black", 18, "bold"), text_color="#A3F843"
        )
        lbl_titulo.pack()
        lbl_sub = ctk.CTkLabel(
            inner, text=subtitulo,
            font=("Arial", 12), text_color="#666666"
        )
        lbl_sub.pack(pady=(4, 0))

        def set_hover(active):
            card.configure(
                fg_color="#212121" if active else "#1A1A1A",
                border_color="#A3F843" if active else "#2A2A2A"
            )

        def check_hover():
            cx, cy = card.winfo_rootx(), card.winfo_rooty()
            cw, ch = card.winfo_width(), card.winfo_height()
            mx, my = card.winfo_pointerx(), card.winfo_pointery()
            if not (cx <= mx <= cx + cw and cy <= my <= cy + ch):
                set_hover(False)

        for w in (card, inner, lbl_titulo, lbl_sub):
            w.bind("<Enter>",    lambda e: set_hover(True))
            w.bind("<Leave>",    lambda e: card.after(10, check_hover))
            w.bind("<Button-1>", lambda e, c=comando: c())
