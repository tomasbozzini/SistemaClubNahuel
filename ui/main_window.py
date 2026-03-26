# ui/main_window.py
import customtkinter as ctk
from customtkinter import CTkImage
from PIL import Image
from ui.reservas_window import ReservasWindow
from ui.ver_reservas_window import VerReservasWindow
from ui.gestionar_canchas_window import GestionarCanchasWindow
from ui.calendario_reservas_window import CalendarioWindow


class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Sistema de Reservas - Club Nahuel")
        width = 900
        height = 740
        self.geometry(f"{width}x{height}")

        # Centrar ventana
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")
        self.resizable(False, False)
        self.configure(fg_color="#121212")

        # Limpieza periódica
        self.limpiar_reservas_periodicamente()

        # === Barra de acento superior ===
        ctk.CTkFrame(self, height=5, fg_color="#A3F843", corner_radius=0).pack(fill="x")

        # === Header ===
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(pady=(28, 8))

        logo_path = "assets/logoclubnahuel.png"
        logo_img = CTkImage(
            light_image=Image.open(logo_path),
            dark_image=Image.open(logo_path),
            size=(100, 82)
        )
        ctk.CTkLabel(header_frame, image=logo_img, text="").pack()

        ctk.CTkLabel(
            header_frame,
            text="CLUB NAHUEL",
            font=("Arial Black", 34, "bold"),
            text_color="#FFFFFF"
        ).pack(pady=(10, 0))

        ctk.CTkLabel(
            header_frame,
            text="S I S T E M A   D E   R E S E R V A S",
            font=("Arial", 11),
            text_color="#A3F843"
        ).pack(pady=(4, 0))

        # Separador
        ctk.CTkFrame(self, height=1, fg_color="#2A2A2A", corner_radius=0).pack(fill="x", padx=50, pady=(18, 0))

        # === Grid de cards ===
        cards_frame = ctk.CTkFrame(self, fg_color="transparent")
        cards_frame.pack(pady=28)

        self._crear_card(cards_frame, "NUEVA RESERVA",   "Registrá un turno en la cancha",  self.abrir_registrar,         0, 0)
        self._crear_card(cards_frame, "VER RESERVAS",    "Listado completo de turnos",       self.abrir_ver,               0, 1)
        self._crear_card(cards_frame, "CALENDARIO",      "Vista mensual de reservas",        self.abrir_calendario,        1, 0)
        self._crear_card(cards_frame, "CANCHAS",         "Gestioná las canchas del club",    self.abrir_gestionar_canchas, 1, 1)

        # Separador
        ctk.CTkFrame(self, height=1, fg_color="#2A2A2A", corner_radius=0).pack(fill="x", padx=50, pady=(10, 0))

        # === Botón Salir ===
        ctk.CTkButton(
            self,
            text="SALIR",
            command=self.destroy,
            fg_color="transparent",
            hover_color="#1E1E1E",
            text_color="#FF5C5C",
            border_color="#FF5C5C",
            border_width=2,
            corner_radius=8,
            width=150,
            height=38,
            font=("Arial", 12, "bold")
        ).pack(pady=18)

        # === Footer ===
        ctk.CTkFrame(self, height=1, fg_color="#1E1E1E", corner_radius=0).pack(fill="x")
        ctk.CTkLabel(
            self,
            text="Club Nahuel  •  Sistema de Reservas",
            font=("Arial", 9),
            text_color="#333333"
        ).pack(pady=6)

    def _crear_card(self, parent, titulo, subtitulo, comando, row, col):
        card = ctk.CTkFrame(
            parent,
            width=370,
            height=125,
            fg_color="#1A1A1A",
            corner_radius=14,
            border_width=1,
            border_color="#2A2A2A"
        )
        card.grid(row=row, column=col, padx=14, pady=14)
        card.grid_propagate(False)

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.place(relx=0.5, rely=0.5, anchor="center")

        lbl_titulo = ctk.CTkLabel(
            inner,
            text=titulo,
            font=("Arial Black", 18, "bold"),
            text_color="#A3F843"
        )
        lbl_titulo.pack()

        lbl_sub = ctk.CTkLabel(
            inner,
            text=subtitulo,
            font=("Arial", 12),
            text_color="#666666"
        )
        lbl_sub.pack(pady=(4, 0))

        def set_hover(active):
            if active:
                card.configure(fg_color="#212121", border_color="#A3F843")
            else:
                card.configure(fg_color="#1A1A1A", border_color="#2A2A2A")

        def check_hover():
            cx, cy = card.winfo_rootx(), card.winfo_rooty()
            cw, ch = card.winfo_width(), card.winfo_height()
            mx, my = card.winfo_pointerx(), card.winfo_pointery()
            if not (cx <= mx <= cx + cw and cy <= my <= cy + ch):
                set_hover(False)

        def on_enter(e):
            set_hover(True)

        def on_leave(e):
            # Diferir el chequeo para que la posición del puntero esté actualizada
            card.after(10, check_hover)

        def on_click(e):
            comando()

        for w in (card, inner, lbl_titulo, lbl_sub):
            w.bind("<Enter>", on_enter)
            w.bind("<Leave>", on_leave)
            w.bind("<Button-1>", on_click)

    def limpiar_reservas_periodicamente(self):
        from models.models import eliminar_reservas_expiradas
        eliminar_reservas_expiradas()
        self.after(60000, self.limpiar_reservas_periodicamente)

    def abrir_registrar(self):
        ReservasWindow(self)

    def abrir_ver(self):
        VerReservasWindow(self)

    def abrir_gestionar_canchas(self):
        GestionarCanchasWindow(self)

    def abrir_calendario(self):
        CalendarioWindow(self)


