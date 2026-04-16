# ui/main_window.py
import logging
import customtkinter as ctk

_log = logging.getLogger(__name__)
from auth.session import SessionManager
from ui.reservas_window import ReservasWindow
from ui.ver_reservas_window import VerReservasWindow
from ui.calendario_reservas_window import CalendarioWindow
from ui.ventana_mixin import InactividadMixin
from ui.gestionar_canchas_window import GestionarCanchasWindow
from ui.clientes_window import ClientesWindow
from sync.poller import ReservasPoller, EventoActualizacion, EventoError, EventoReconexion

POLL_CHECK_MS = 500

# Acento por sección
_COLOR = {
    "reserva":        "#7C5CFF",
    "ver":            "#00C4FF",
    "calendario":     "#9D6EFF",
    "canchas":        "#FF8C42",
    "finanzas":       "#FFD700",
    "disponibilidad": "#00D4FF",
    "clientes":       "#9D6EFF",
}


class MainWindow(InactividadMixin, ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.withdraw()

        if not SessionManager.esta_logueado():
            self.after(0, self._volver_login)
            return

        from db.database import get_club_nombre
        self.title(f"Sistema de Reservas - {get_club_nombre()}")
        self.update_idletasks()
        from ui.ventana_mixin import _get_work_area
        work_w, work_h = _get_work_area(self)

        # "full" ≥ 850 | "compact" 750-849 | "mini" < 750
        if work_h >= 850:
            self._size = "full"
            width, height = 900, min(920, work_h - 20)
        elif work_h >= 750:
            self._size = "compact"
            width, height = 860, min(760, work_h - 20)
        else:
            self._size = "mini"
            width, height = 820, min(680, work_h - 20)

        x = (work_w // 2) - (width  // 2)
        y = (work_h // 2) - (height // 2)
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

        self._iniciar_monitor_inactividad()
        self.after(2000, self._verificar_actualizacion)

        self.protocol("WM_DELETE_WINDOW", self._cerrar)
        self.deiconify()

    # ── UI ───────────────────────────────────────────────────────────────────

    def _build_ui(self):
        usuario = SessionManager.get_usuario_actual()

        # Barra superior de acento
        ctk.CTkFrame(self, height=4, fg_color="#7C5CFF", corner_radius=0).pack(fill="x")

        # Header
        header_frame = ctk.CTkFrame(self, fg_color="#111111", corner_radius=0)
        header_frame.pack(fill="x")

        size = self._size  # "full" | "compact" | "mini"
        inner_header = ctk.CTkFrame(header_frame, fg_color="transparent")
        hpad = {"full": (22, 18), "compact": (12, 10), "mini": (6, 6)}[size]
        inner_header.pack(pady=hpad)

        icon_sz = {"full": 48, "compact": 38, "mini": 30}[size]
        ctk.CTkLabel(inner_header, text="◈",
            font=("Arial Black", icon_sz), text_color="#7C5CFF").pack()
        title_font = {"full": 32, "compact": 24, "mini": 20}[size]
        title_pady = {"full": (8, 0), "compact": (6, 0), "mini": (4, 0)}[size]
        from db.database import get_club_nombre
        ctk.CTkLabel(
            inner_header, text=get_club_nombre().upper(),
            font=("Arial Black", title_font, "bold"), text_color="#FFFFFF"
        ).pack(pady=title_pady)
        if size != "mini":
            ctk.CTkLabel(
                inner_header, text="S I S T E M A   D E   R E S E R V A S",
                font=("Arial", 10), text_color="#7C5CFF"
            ).pack(pady=(2, 0))

        # Chip de usuario
        rol_color = "#7C5CFF" if usuario.rol == "admin" else "#00C4FF"
        chip = ctk.CTkFrame(inner_header, fg_color="#1A1A1A", corner_radius=20,
            border_width=1, border_color="#2A2A2A")
        chip_pady = {"full": (12, 0), "compact": (8, 0), "mini": (5, 0)}[size]
        chip.pack(pady=chip_pady)
        ctk.CTkLabel(
            chip,
            text=f"  {usuario.nombre}  ·  {usuario.rol.upper()}  ",
            font=("Arial", 11, "bold"), text_color=rol_color
        ).pack(padx=10, pady=4)

        ctk.CTkFrame(self, height=1, fg_color="#1C1C1C", corner_radius=0).pack(fill="x")

        # ── Cards ────────────────────────────────────────────────────────────
        cards_frame = ctk.CTkFrame(self, fg_color="transparent")
        cards_pady = {"full": 26, "compact": 14, "mini": 8}[size]
        cards_frame.pack(pady=cards_pady)

        self._crear_card(cards_frame, "NUEVA RESERVA",       "Registrá un nuevo turno",        "✦", _COLOR["reserva"],    self.abrir_registrar,   0, 0)
        self._crear_card(cards_frame, "VER RESERVAS",        "Listado completo de turnos",     "≡", _COLOR["ver"],        self.abrir_ver,         0, 1)
        self._crear_card(cards_frame, "CALENDARIO",          "Vista mensual de reservas",      "◉", _COLOR["calendario"], self.abrir_calendario,  1, 0)
        self._crear_card(cards_frame, "HISTORIAL FINANCIERO","Registros y totales recaudados", "$", _COLOR["finanzas"],   self.abrir_finanzas,    1, 1)
        self._crear_card(cards_frame, "GESTIONAR CANCHAS",   "Alta, baja y bloqueos",          "⬡", _COLOR["canchas"],    self.abrir_canchas,     2, 0)
        self._crear_card(cards_frame, "CLIENTES",            "Agenda de clientes frecuentes",  "✎", _COLOR["clientes"],   self.abrir_clientes,    2, 1)

        # Card DISPONIBILIDAD — ancho completo
        dispon_wrap = ctk.CTkFrame(cards_frame, fg_color="transparent")
        dispon_wrap.grid(row=3, column=0, columnspan=2, padx=11, pady=(0, 4))
        self._crear_card_wide(dispon_wrap, "DISPONIBILIDAD",
            "Vista en tiempo real de canchas y horarios", "◎",
            _COLOR["disponibilidad"], self.abrir_disponibilidad)

        ctk.CTkFrame(self, height=1, fg_color="#1C1C1C", corner_radius=0).pack(fill="x", padx=0)

        # ── Botones ───────────────────────────────────────────────────────────
        botones_wrap = ctk.CTkFrame(self, fg_color="transparent")
        btn_pady = {"full": 16, "compact": 10, "mini": 6}[size]
        botones_wrap.pack(pady=btn_pady)

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
        size   = self._size
        card_h = {"full": 128, "compact": 108, "mini": 92}[size]
        card_w = {"full": 376, "compact": 356, "mini": 336}[size]
        pady   = {"full": 11,  "compact": 7,   "mini": 4}[size]
        icon_y = {"full": 42,  "compact": 32,  "mini": 24}[size]
        txt_y  = {"full": 44,  "compact": 34,  "mini": 26}[size]
        sub_y  = {"full": 72,  "compact": 58,  "mini": 50}[size]

        card = ctk.CTkFrame(
            parent, width=card_w, height=card_h,
            fg_color="#141414", corner_radius=14,
            border_width=1, border_color="#222222"
        )
        card.grid(row=row, column=col, padx=11, pady=pady)
        card.grid_propagate(False)

        # Barra de acento superior
        accent = ctk.CTkFrame(card, height=3, fg_color=color, corner_radius=0)
        accent.place(x=0, y=0, relwidth=1.0)

        # Ícono
        icon_bg = ctk.CTkFrame(card, width=46, height=46,
            fg_color="#1C1C1C", corner_radius=12)
        icon_bg.place(x=18, y=icon_y)
        icon_bg.pack_propagate(False)
        lbl_icon = ctk.CTkLabel(icon_bg, text=icono,
            font=("Arial Black", 20), text_color=color)
        lbl_icon.place(relx=0.5, rely=0.5, anchor="center")

        # Textos
        title_font = {"full": 15, "compact": 13, "mini": 12}[size]
        lbl_titulo = ctk.CTkLabel(card, text=titulo,
            font=("Arial Black", title_font, "bold"), text_color="#FFFFFF")
        lbl_titulo.place(x=76, y=txt_y)
        lbl_sub = ctk.CTkLabel(card, text=subtitulo,
            font=("Arial", 10), text_color="#444444")
        lbl_sub.place(x=76, y=sub_y)

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

        def _ejecutar(cmd):
            try:
                cmd()
            except Exception as ex:
                _log.exception("Error al abrir ventana")
                from tkinter import messagebox
                messagebox.showerror("Error al abrir ventana", str(ex))

        for w in (card, icon_bg, lbl_icon, lbl_titulo, lbl_sub, arrow, accent):
            w.bind("<Enter>",    lambda e: set_hover(True))
            w.bind("<Leave>",    lambda e: card.after(10, check_hover))
            w.bind("<Button-1>", lambda e, c=comando: _ejecutar(c))

    def _crear_card_wide(self, parent, titulo, subtitulo, icono, color, comando):
        """Card de ancho completo (ocupa las dos columnas)."""
        size = self._size
        card_w = {"full": 774, "compact": 734, "mini": 694}[size]
        card_h = {"full": 80,  "compact": 68,  "mini": 58}[size]
        card = ctk.CTkFrame(
            parent, width=card_w, height=card_h,
            fg_color="#141414", corner_radius=14,
            border_width=1, border_color="#222222",
        )
        card.pack()
        card.pack_propagate(False)

        accent = ctk.CTkFrame(card, height=3, fg_color=color, corner_radius=0)
        accent.place(x=0, y=0, relwidth=1.0)

        icon_bg = ctk.CTkFrame(card, width=46, height=46,
            fg_color="#1C1C1C", corner_radius=12)
        icon_bg.place(x=18, y=17)
        icon_bg.pack_propagate(False)
        lbl_icon = ctk.CTkLabel(icon_bg, text=icono,
            font=("Arial Black", 20), text_color=color)
        lbl_icon.place(relx=0.5, rely=0.5, anchor="center")

        lbl_titulo = ctk.CTkLabel(card, text=titulo,
            font=("Arial Black", 15, "bold"), text_color="#FFFFFF")
        lbl_titulo.place(x=76, y=18)
        lbl_sub = ctk.CTkLabel(card, text=subtitulo,
            font=("Arial", 11), text_color="#444444")
        lbl_sub.place(x=76, y=44)

        arrow = ctk.CTkLabel(card, text="›", font=("Arial Black", 26), text_color="#2A2A2A")
        arrow.place(relx=0.97, rely=0.55, anchor="center")

        def set_hover(active):
            card.configure(
                fg_color="#1C1C1C" if active else "#141414",
                border_color=color if active else "#222222",
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
        self._sync_bar_ref = barra
        barra.pack_propagate(False)

        self._dot_sync = ctk.CTkLabel(barra, text="●",
            font=("Arial", 9), text_color="#333333")
        self._dot_sync.pack(side="right", padx=(0, 4))

        self._lbl_sync = ctk.CTkLabel(barra, text="Conectando...",
            font=("Arial", 9), text_color="#333333")
        self._lbl_sync.pack(side="right", padx=(0, 2))

    def _set_sync_ok(self, timestamp):
        self._dot_sync.configure(text_color="#7C5CFF")
        self._lbl_sync.configure(
            text=f"Sincronizado  {timestamp.strftime('%H:%M:%S')}",
            text_color="#3A4A2A"
        )

    def _set_sync_error(self):
        self._dot_sync.configure(text_color="#FFA500")
        self._lbl_sync.configure(text="Sin conexión — reintentando", text_color="#4A3A00")

    def _set_sync_reconectado(self, timestamp):
        self._dot_sync.configure(text_color="#7C5CFF")
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

    def abrir_calendario(self):
        CalendarioWindow(self)

    def abrir_finanzas(self):
        from ui.financiero_window import FinancieroWindow
        FinancieroWindow(self)

    def abrir_canchas(self):
        GestionarCanchasWindow(self)

    def abrir_clientes(self):
        ClientesWindow(self)

    def abrir_disponibilidad(self):
        from ui.disponibilidad_window import DisponibilidadWindow
        DisponibilidadWindow(self)

    # ── Actualización ────────────────────────────────────────────────────────

    def _verificar_actualizacion(self):
        import threading
        def _check():
            from models.actualizacion_service import verificar_actualizacion
            hay_update, version, url = verificar_actualizacion()
            if hay_update:
                self.after(0, lambda: self._mostrar_banner_update(version, url))
        threading.Thread(target=_check, daemon=True).start()

    def _mostrar_banner_update(self, version, url):
        try:
            banner = ctk.CTkFrame(self, fg_color="#2A1F00", corner_radius=0,
                                  border_width=2, border_color="#FFD700")
            banner.pack(fill="x", before=self._sync_bar_ref)

            ctk.CTkLabel(
                banner,
                text=f"  🔔  Nueva versión disponible: v{version}",
                font=("Arial", 13, "bold"), text_color="#FFD700"
            ).pack(side="left", padx=(16, 8), pady=10)

            btn_update = ctk.CTkButton(
                banner, text="Actualizar ahora",
                command=lambda: self._iniciar_descarga_update(url, banner),
                fg_color="#FFD700", hover_color="#FFC000",
                text_color="#1A1200", border_width=0,
                corner_radius=6, width=160, height=30, font=("Arial", 11, "bold")
            )
            btn_update.pack(side="left", padx=8, pady=10)

            ctk.CTkButton(
                banner, text="✕", command=banner.destroy,
                fg_color="transparent", hover_color="#3A2800",
                text_color="#FFD700", width=32, height=30, font=("Arial", 13, "bold")
            ).pack(side="right", padx=12, pady=10)
        except Exception:
            pass

    def _iniciar_descarga_update(self, url, banner):
        if not url:
            return
        from utils.updater import descargar_actualizacion, aplicar_actualizacion

        # Ventana de progreso
        dlg = ctk.CTkToplevel(self)
        dlg.title("Actualizando")
        dlg.resizable(False, False)
        dlg.configure(fg_color="#0D0D0D")
        dlg.transient(self)
        dlg.grab_set()
        dlg.protocol("WM_DELETE_WINDOW", lambda: None)  # no se puede cerrar

        w, h = 380, 160
        dlg.geometry(f"{w}x{h}+{self.winfo_rootx() + self.winfo_width()//2 - w//2}"
                     f"+{self.winfo_rooty() + self.winfo_height()//2 - h//2}")

        ctk.CTkFrame(dlg, height=4, fg_color="#FFD700", corner_radius=0).pack(fill="x")
        ctk.CTkLabel(dlg, text="Descargando actualización...",
                     font=("Arial Black", 13, "bold"), text_color="#FFFFFF").pack(pady=(18, 6))

        lbl_pct = ctk.CTkLabel(dlg, text="0%", font=("Arial", 11), text_color="#FFD700")
        lbl_pct.pack()

        barra = ctk.CTkProgressBar(dlg, width=320, height=12,
                                   fg_color="#1A1A1A", progress_color="#FFD700")
        barra.set(0)
        barra.pack(pady=(8, 0))

        def _progress(desc, total):
            pct = (desc / total) if total else 0
            self.after(0, lambda: barra.set(pct))
            self.after(0, lambda: lbl_pct.configure(
                text=f"{int(pct * 100)}%  ({desc // 1024 // 1024:.1f} MB)"
            ))

        def _done(ruta):
            self.after(0, lambda: barra.set(1))
            self.after(0, lambda: lbl_pct.configure(
                text="Actualización lista. Reabrí el programa."))
            self.after(800, lambda: aplicar_actualizacion(ruta))

        def _error(exc):
            self.after(0, dlg.destroy)
            self.after(0, lambda: __import__("tkinter.messagebox",
                fromlist=["showerror"]).showerror(
                    "Error al actualizar",
                    f"No se pudo descargar la actualización.\n{exc}"
            ))

        banner.destroy()
        descargar_actualizacion(url, on_progress=_progress, on_done=_done, on_error=_error)

    # ── Ciclos periódicos ─────────────────────────────────────────────────────

    def limpiar_reservas_periodicamente(self):
        import threading
        from models.reservas_service import eliminar_reservas_expiradas
        def _worker():
            try:
                eliminar_reservas_expiradas()
            except Exception as e:
                _log.warning("limpiar_reservas: %s", e)
        threading.Thread(target=_worker, daemon=True).start()
        self.after(60_000, self.limpiar_reservas_periodicamente)

    # ── Cierre y logout ───────────────────────────────────────────────────────

    def _cerrar_sesion(self):
        import threading
        from models.logs_service import registrar_log
        usuario = SessionManager.get_usuario_actual()
        if usuario:
            threading.Thread(
                target=registrar_log,
                args=("logout",),
                kwargs={"username": usuario.nombre, "usuario_id": usuario.id},
                daemon=True,
            ).start()
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
