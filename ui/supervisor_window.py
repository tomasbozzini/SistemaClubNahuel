# ui/supervisor_window.py
import customtkinter as ctk
from ui.ventana_mixin import VentanaMixin, InactividadMixin
from customtkinter import CTkImage
from PIL import Image
from auth.session import SessionManager

_COLOR = {
    "reservas":  "#A3F843",
    "precios":   "#00D68F",
    "usuarios":  "#9D6EFF",
    "finanzas":  "#FFD700",
    "canchas":   "#FF8C42",
}


class SupervisorWindow(VentanaMixin, InactividadMixin, ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.withdraw()

        if not SessionManager.esta_logueado():
            self.after(0, self._volver_login)
            return

        self.title("Panel Supervisor — Club Nahuel")
        self.update_idletasks()
        from ui.ventana_mixin import _get_work_area
        work_w, work_h = _get_work_area(self)

        if work_h >= 850:
            self._size = "full"
            width, height = 820, min(870, work_h - 20)
        elif work_h >= 750:
            self._size = "compact"
            width, height = 780, min(730, work_h - 20)
        else:
            self._size = "mini"
            width, height = 740, min(640, work_h - 20)

        x = (work_w // 2) - (width  // 2)
        y = (work_h // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")
        self.resizable(False, False)
        self.configure(fg_color="#0D0D0D")

        self._build_ui()
        self._iniciar_monitor_inactividad()
        self.protocol("WM_DELETE_WINDOW", self._cerrar)
        self.after(150, self._mostrar_ventana)

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        usuario = SessionManager.get_usuario_actual()

        ctk.CTkFrame(self, height=4, fg_color="#00D68F", corner_radius=0).pack(fill="x")

        # Header
        size = self._size
        header_frame = ctk.CTkFrame(self, fg_color="#111111", corner_radius=0)
        header_frame.pack(fill="x")
        inner_header = ctk.CTkFrame(header_frame, fg_color="transparent")
        hpad = {"full": (22, 18), "compact": (12, 10), "mini": (6, 6)}[size]
        inner_header.pack(pady=hpad)

        logo_path = "assets/logoclubnahuel.png"
        logo_size = {"full": (88, 72), "compact": (68, 56), "mini": (52, 42)}[size]
        try:
            logo_img = CTkImage(
                light_image=Image.open(logo_path),
                dark_image=Image.open(logo_path),
                size=logo_size,
            )
            ctk.CTkLabel(inner_header, image=logo_img, text="").pack()
        except Exception:
            pass

        title_font = {"full": 32, "compact": 24, "mini": 20}[size]
        title_pady = {"full": (8, 0), "compact": (6, 0), "mini": (4, 0)}[size]
        ctk.CTkLabel(inner_header, text="CLUB NAHUEL",
            font=("Arial Black", title_font, "bold"), text_color="#FFFFFF").pack(pady=title_pady)
        if size != "mini":
            ctk.CTkLabel(inner_header, text="P A N E L   S U P E R V I S O R",
                font=("Arial", 10), text_color="#00D68F").pack(pady=(2, 0))

        chip = ctk.CTkFrame(inner_header, fg_color="#1A1A1A", corner_radius=20,
            border_width=1, border_color="#2A2A2A")
        chip_pady = {"full": (12, 0), "compact": (8, 0), "mini": (5, 0)}[size]
        chip.pack(pady=chip_pady)
        ctk.CTkLabel(chip,
            text=f"  {usuario.nombre}  ·  SUPERVISOR  ",
            font=("Arial", 11, "bold"), text_color="#00D68F").pack(padx=10, pady=4)

        ctk.CTkFrame(self, height=1, fg_color="#1C1C1C", corner_radius=0).pack(fill="x")

        cards_pady = {"full": 16, "compact": 10, "mini": 6}[size]
        cards_frame = ctk.CTkFrame(self, fg_color="transparent")
        cards_frame.pack(pady=cards_pady)

        self._crear_card(cards_frame, "SISTEMA DE RESERVAS", "Gestioná turnos y reservas",
            "◉", _COLOR["reservas"], self._abrir_reservas, 0, 0)
        self._crear_card(cards_frame, "GESTIÓN DE PRECIOS",  "Configurá precios por cancha",
            "◈", _COLOR["precios"],  self._abrir_precios,   0, 1)
        self._crear_card(cards_frame, "GESTIÓN DE USUARIOS", "Administrá los usuarios ADMIN",
            "✦", _COLOR["usuarios"], self._abrir_usuarios,  1, 0)
        self._crear_card(cards_frame, "HISTORIAL FINANCIERO","Registros y totales recaudados",
            "$", _COLOR["finanzas"], self._abrir_finanzas,  1, 1)

        # Card CANCHAS — fila completa
        canchas_wrap = ctk.CTkFrame(cards_frame, fg_color="transparent")
        canchas_wrap.grid(row=2, column=0, columnspan=2, padx=11, pady=(0, 4))
        self._crear_card_wide(canchas_wrap, "GESTIÓN DE CANCHAS",
            "Agregá o eliminá canchas del club", "◈", _COLOR["canchas"],
            self._abrir_canchas)

        # Card DISPONIBILIDAD — fila completa
        dispon_wrap = ctk.CTkFrame(cards_frame, fg_color="transparent")
        dispon_wrap.grid(row=3, column=0, columnspan=2, padx=11, pady=(0, 4))
        self._crear_card_wide(dispon_wrap, "DISPONIBILIDAD",
            "Vista en tiempo real de canchas y horarios", "◎", "#00D68F",
            self._abrir_disponibilidad)

        ctk.CTkFrame(self, height=1, fg_color="#1C1C1C", corner_radius=0).pack(fill="x")

        # Botones
        botones_wrap = ctk.CTkFrame(self, fg_color="transparent")
        btn_pady = {"full": 18, "compact": 10, "mini": 6}[size]
        botones_wrap.pack(pady=btn_pady)

        ctk.CTkButton(
            botones_wrap, text="CERRAR SESIÓN", command=self._cerrar_sesion,
            fg_color="transparent", hover_color="#161616",
            text_color="#FFA500", border_color="#2A2000", border_width=1,
            corner_radius=8, width=160, height=36, font=("Arial", 11, "bold"),
        ).pack(side="left", padx=8)

        ctk.CTkButton(
            botones_wrap, text="SALIR", command=self._cerrar,
            fg_color="transparent", hover_color="#161616",
            text_color="#FF5C5C", border_color="#2A0000", border_width=1,
            corner_radius=8, width=120, height=36, font=("Arial", 11, "bold"),
        ).pack(side="left", padx=8)

    # ── Cards ─────────────────────────────────────────────────────────────────

    def _crear_card(self, parent, titulo, subtitulo, icono, color, comando, row, col):
        size   = self._size
        card_h = {"full": 126, "compact": 106, "mini": 90}[size]
        card_w = {"full": 352, "compact": 332, "mini": 312}[size]
        pady   = {"full": 11,  "compact": 7,   "mini": 4}[size]
        icon_y = {"full": 40,  "compact": 30,  "mini": 22}[size]
        txt_y  = {"full": 42,  "compact": 32,  "mini": 24}[size]
        sub_y  = {"full": 70,  "compact": 57,  "mini": 48}[size]

        card = ctk.CTkFrame(
            parent, width=card_w, height=card_h,
            fg_color="#141414", corner_radius=14,
            border_width=1, border_color="#222222",
        )
        card.grid(row=row, column=col, padx=11, pady=pady)
        card.grid_propagate(False)

        accent = ctk.CTkFrame(card, height=3, fg_color=color, corner_radius=0)
        accent.place(x=0, y=0, relwidth=1.0)

        icon_bg = ctk.CTkFrame(card, width=46, height=46,
            fg_color="#1C1C1C", corner_radius=12)
        icon_bg.place(x=18, y=icon_y)
        icon_bg.pack_propagate(False)
        lbl_icon = ctk.CTkLabel(icon_bg, text=icono,
            font=("Arial Black", 20), text_color=color)
        lbl_icon.place(relx=0.5, rely=0.5, anchor="center")

        title_font = {"full": 14, "compact": 13, "mini": 12}[size]
        lbl_titulo = ctk.CTkLabel(card, text=titulo,
            font=("Arial Black", title_font, "bold"), text_color="#FFFFFF")
        lbl_titulo.place(x=76, y=txt_y)
        lbl_sub = ctk.CTkLabel(card, text=subtitulo,
            font=("Arial", 10), text_color="#444444")
        lbl_sub.place(x=76, y=sub_y)

        arrow = ctk.CTkLabel(card, text="›", font=("Arial Black", 26), text_color="#2A2A2A")
        arrow.place(relx=0.92, rely=0.62, anchor="center")

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

    def _crear_card_wide(self, parent, titulo, subtitulo, icono, color, comando):
        size   = self._size
        card_w = {"full": 726, "compact": 686, "mini": 646}[size]
        card_h = {"full": 76,  "compact": 64,  "mini": 54}[size]
        card = ctk.CTkFrame(
            parent, width=card_w, height=card_h,
            fg_color="#141414", corner_radius=14,
            border_width=1, border_color="#222222",
        )
        card.pack()
        card.pack_propagate(False)

        accent = ctk.CTkFrame(card, height=3, fg_color=color, corner_radius=0)
        accent.place(x=0, y=0, relwidth=1.0)

        icon_bg = ctk.CTkFrame(card, width=42, height=42,
            fg_color="#1C1C1C", corner_radius=10)
        icon_bg.place(x=18, y=17)
        icon_bg.pack_propagate(False)
        lbl_icon = ctk.CTkLabel(icon_bg, text=icono,
            font=("Arial Black", 18), text_color=color)
        lbl_icon.place(relx=0.5, rely=0.5, anchor="center")

        lbl_titulo = ctk.CTkLabel(card, text=titulo,
            font=("Arial Black", 14, "bold"), text_color="#FFFFFF")
        lbl_titulo.place(x=74, y=16)
        lbl_sub = ctk.CTkLabel(card, text=subtitulo,
            font=("Arial", 11), text_color="#444444")
        lbl_sub.place(x=74, y=42)

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

    # ── Apertura de sub-ventanas ──────────────────────────────────────────────

    def _abrir_reservas(self):
        from ui.main_window import MainWindow
        win = MainWindow(self)

        def _cerrar_main():
            try:
                win._poller.detener()
            except Exception:
                pass
            win.destroy()
            self.lift()
            self.focus_force()

        win.protocol("WM_DELETE_WINDOW", _cerrar_main)

    def _abrir_precios(self):
        from ui.precios_window import PreciosWindow
        PreciosWindow(self)

    def _abrir_usuarios(self):
        from ui.gestion_usuarios_window import GestionUsuariosWindow
        GestionUsuariosWindow(self)

    def _abrir_finanzas(self):
        from ui.financiero_window import FinancieroWindow
        FinancieroWindow(self)

    def _abrir_canchas(self):
        from ui.gestionar_canchas_window import GestionarCanchasWindow
        GestionarCanchasWindow(self)

    def _abrir_disponibilidad(self):
        from ui.disponibilidad_window import DisponibilidadWindow
        DisponibilidadWindow(self)

    # ── Cierre ────────────────────────────────────────────────────────────────

    def _cerrar_sesion(self):
        from models.logs_service import registrar_log
        usuario = SessionManager.get_usuario_actual()
        if usuario:
            registrar_log("logout", username=usuario.nombre, usuario_id=usuario.id)
        SessionManager.cerrar_sesion()
        self._volver_login()

    def _volver_login(self):
        self.master.deiconify()
        self.destroy()

    def _cerrar(self):
        SessionManager.cerrar_sesion()
        self.master.quit()
