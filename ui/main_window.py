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

# Acento por sección
_COLOR = {
    "reserva":   "#A3F843",
    "ver":       "#00C4FF",
    "calendario":"#9D6EFF",
    "canchas":   "#FF8C42",
}


class MainWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.withdraw()

        if not SessionManager.esta_logueado():
            self.after(0, self._volver_login)
            return

        self.title("Sistema de Reservas - Club Nahuel")
        width, height = 900, 740
        self.geometry(f"{width}x{height}")
        self.update_idletasks()
        x = (self.winfo_screenwidth()  // 2) - (width  // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")
        self.resizable(False, False)
        self.configure(fg_color="#0D0D0D")

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

        # Barra superior de acento
        ctk.CTkFrame(self, height=4, fg_color="#A3F843", corner_radius=0).pack(fill="x")

        # Header
        header_frame = ctk.CTkFrame(self, fg_color="#111111", corner_radius=0)
        header_frame.pack(fill="x")

        inner_header = ctk.CTkFrame(header_frame, fg_color="transparent")
        inner_header.pack(pady=(22, 18))

        logo_path = "assets/logoclubnahuel.png"
        logo_img = CTkImage(
            light_image=Image.open(logo_path),
            dark_image=Image.open(logo_path),
            size=(88, 72)
        )
        ctk.CTkLabel(inner_header, image=logo_img, text="").pack()
        ctk.CTkLabel(
            inner_header, text="CLUB NAHUEL",
            font=("Arial Black", 32, "bold"), text_color="#FFFFFF"
        ).pack(pady=(8, 0))
        ctk.CTkLabel(
            inner_header, text="S I S T E M A   D E   R E S E R V A S",
            font=("Arial", 10), text_color="#A3F843"
        ).pack(pady=(3, 0))

        # Chip de usuario
        rol_color = "#A3F843" if usuario.rol == "admin" else "#00C4FF"
        chip = ctk.CTkFrame(inner_header, fg_color="#1A1A1A", corner_radius=20,
            border_width=1, border_color="#2A2A2A")
        chip.pack(pady=(12, 0))
        ctk.CTkLabel(
            chip,
            text=f"  {usuario.nombre}  ·  {usuario.rol.upper()}  ",
            font=("Arial", 11, "bold"), text_color=rol_color
        ).pack(padx=10, pady=5)

        ctk.CTkFrame(self, height=1, fg_color="#1C1C1C", corner_radius=0).pack(fill="x")

        # ── Cards ────────────────────────────────────────────────────────────
        cards_frame = ctk.CTkFrame(self, fg_color="transparent")
        cards_frame.pack(pady=26)

        self._crear_card(cards_frame, "NUEVA RESERVA",  "Registrá un nuevo turno",  "✦", _COLOR["reserva"],    self.abrir_registrar,         0, 0)
        self._crear_card(cards_frame, "VER RESERVAS",   "Listado completo de turnos","≡", _COLOR["ver"],        self.abrir_ver,               0, 1)
        self._crear_card(cards_frame, "CALENDARIO",     "Vista mensual de reservas", "◉", _COLOR["calendario"], self.abrir_calendario,        1, 0)
        self._crear_card(cards_frame, "CANCHAS",        "Gestioná las canchas",      "◈", _COLOR["canchas"],    self.abrir_gestionar_canchas, 1, 1)

        ctk.CTkFrame(self, height=1, fg_color="#1C1C1C", corner_radius=0).pack(fill="x", padx=0)

        # ── Botones ───────────────────────────────────────────────────────────
        botones_wrap = ctk.CTkFrame(self, fg_color="transparent")
        botones_wrap.pack(pady=16)

        ctk.CTkButton(
            botones_wrap, text="CERRAR SESIÓN", command=self._cerrar_sesion,
            fg_color="transparent", hover_color="#161616",
            text_color="#FFA500", border_color="#2A2000", border_width=1,
            corner_radius=8, width=160, height=36, font=("Arial", 11, "bold")
        ).pack(side="left", padx=8)

        ctk.CTkButton(
            botones_wrap, text="SALIR", command=self._cerrar,
            fg_color="transparent", hover_color="#161616",
            text_color="#FF5C5C", border_color="#2A0000", border_width=1,
            corner_radius=8, width=120, height=36, font=("Arial", 11, "bold")
        ).pack(side="left", padx=8)

    # ── Cards ────────────────────────────────────────────────────────────────

    def _crear_card(self, parent, titulo, subtitulo, icono, color, comando, row, col):
        card = ctk.CTkFrame(
            parent, width=376, height=128,
            fg_color="#141414", corner_radius=14,
            border_width=1, border_color="#222222"
        )
        card.grid(row=row, column=col, padx=11, pady=11)
        card.grid_propagate(False)

        # Barra de acento superior
        accent = ctk.CTkFrame(card, height=3, fg_color=color, corner_radius=0)
        accent.place(x=0, y=0, relwidth=1.0)

        # Ícono
        icon_bg = ctk.CTkFrame(card, width=46, height=46,
            fg_color="#1C1C1C", corner_radius=12)
        icon_bg.place(x=18, y=42)
        icon_bg.pack_propagate(False)
        lbl_icon = ctk.CTkLabel(icon_bg, text=icono,
            font=("Arial Black", 20), text_color=color)
        lbl_icon.place(relx=0.5, rely=0.5, anchor="center")

        # Textos
        lbl_titulo = ctk.CTkLabel(card, text=titulo,
            font=("Arial Black", 15, "bold"), text_color="#FFFFFF")
        lbl_titulo.place(x=76, y=44)
        lbl_sub = ctk.CTkLabel(card, text=subtitulo,
            font=("Arial", 11), text_color="#444444")
        lbl_sub.place(x=76, y=72)

        # Flecha
        arrow = ctk.CTkLabel(card, text="›", font=("Arial Black", 26), text_color="#2A2A2A")
        arrow.place(relx=0.92, rely=0.62, anchor="center")

        def set_hover(active):
            card.configure(
                fg_color="#1C1C1C" if active else "#141414",
                border_color=color if active else "#222222"
            )
            arrow.configure(text_color=color if active else "#2A2A2A")
            lbl_titulo.configure(text_color=color if active else "#FFFFFF")

        def check_hover():
            try:
                cx, cy = card.winfo_rootx(), card.winfo_rooty()
                cw, ch = card.winfo_width(), card.winfo_height()
                mx, my = card.winfo_pointerx(), card.winfo_pointery()
                if not (cx <= mx <= cx + cw and cy <= my <= cy + ch):
                    set_hover(False)
            except Exception:
                pass

        for w in (card, icon_bg, lbl_icon, lbl_titulo, lbl_sub, arrow, accent):
            w.bind("<Enter>",    lambda e: set_hover(True))
            w.bind("<Leave>",    lambda e: card.after(10, check_hover))
            w.bind("<Button-1>", lambda e, c=comando: c())

    # ── Barra de sync ────────────────────────────────────────────────────────

    def _build_sync_bar(self):
        barra = ctk.CTkFrame(self, fg_color="#0A0A0A", corner_radius=0, height=26)
        barra.pack(fill="x", side="bottom")
        barra.pack_propagate(False)

        self._dot_sync = ctk.CTkLabel(barra, text="●",
            font=("Arial", 9), text_color="#333333")
        self._dot_sync.pack(side="right", padx=(0, 4))

        self._lbl_sync = ctk.CTkLabel(barra, text="Conectando...",
            font=("Arial", 9), text_color="#333333")
        self._lbl_sync.pack(side="right", padx=(0, 2))

    def _set_sync_ok(self, timestamp):
        self._dot_sync.configure(text_color="#A3F843")
        self._lbl_sync.configure(
            text=f"Sincronizado  {timestamp.strftime('%H:%M:%S')}",
            text_color="#3A4A2A"
        )

    def _set_sync_error(self):
        self._dot_sync.configure(text_color="#FFA500")
        self._lbl_sync.configure(text="Sin conexión — reintentando", text_color="#4A3A00")

    def _set_sync_reconectado(self, timestamp):
        self._dot_sync.configure(text_color="#A3F843")
        self._lbl_sync.configure(
            text=f"Reconectado  {timestamp.strftime('%H:%M:%S')}",
            text_color="#3A4A2A"
        )

    # ── Cola de sync ─────────────────────────────────────────────────────────

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

    # ── Apertura de sub-ventanas ──────────────────────────────────────────────

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

    # ── Ciclos periódicos ─────────────────────────────────────────────────────

    def limpiar_reservas_periodicamente(self):
        from models.reservas_service import eliminar_reservas_expiradas
        try:
            eliminar_reservas_expiradas()
        except Exception:
            pass
        self.after(60000, self.limpiar_reservas_periodicamente)

    # ── Cierre y logout ───────────────────────────────────────────────────────

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
