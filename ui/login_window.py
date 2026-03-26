# ui/login_window.py
import customtkinter as ctk
from tkinter import messagebox
from auth.auth_service import verificar_login
from auth.session import SessionManager


class LoginWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Club Nahuel — Iniciar sesión")
        width, height = 420, 520
        self.resizable(False, False)
        self.configure(fg_color="#121212")

        self.update_idletasks()
        x = (self.winfo_screenwidth()  // 2) - (width  // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

        self._build_ui()
        self.bind("<Return>", lambda e: self._intentar_login())

    def _build_ui(self):
        # Barra de acento
        ctk.CTkFrame(self, height=5, fg_color="#A3F843", corner_radius=0).pack(fill="x")

        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(pady=(36, 0))

        ctk.CTkLabel(
            header, text="CLUB NAHUEL",
            font=("Arial Black", 28, "bold"), text_color="#FFFFFF"
        ).pack()
        ctk.CTkLabel(
            header, text="S I S T E M A   D E   R E S E R V A S",
            font=("Arial", 10), text_color="#A3F843"
        ).pack(pady=(4, 0))

        ctk.CTkFrame(self, height=1, fg_color="#2A2A2A", corner_radius=0).pack(
            fill="x", padx=40, pady=(24, 0)
        )

        # Card formulario
        card = ctk.CTkFrame(self, fg_color="#1A1A1A", corner_radius=14)
        card.pack(padx=36, pady=20, fill="both", expand=True)

        ctk.CTkLabel(
            card, text="Iniciar sesión",
            font=("Arial Black", 16, "bold"), text_color="#FFFFFF"
        ).pack(anchor="w", padx=24, pady=(22, 0))
        ctk.CTkLabel(
            card, text="Ingresá tus credenciales para continuar",
            font=("Arial", 11), text_color="#555555"
        ).pack(anchor="w", padx=24, pady=(2, 16))

        lbl_kw = {"font": ("Arial", 10, "bold"), "text_color": "#777777", "anchor": "w"}
        ent_kw = {
            "fg_color": "#212121", "border_color": "#333333",
            "text_color": "#FFFFFF", "corner_radius": 8,
            "height": 42, "width": 340,
        }

        ctk.CTkLabel(card, text="EMAIL", **lbl_kw).pack(anchor="w", padx=24)
        self.entry_email = ctk.CTkEntry(card, placeholder_text="admin@clubnahuel.com", **ent_kw)
        self.entry_email.pack(padx=24, pady=(4, 12))

        ctk.CTkLabel(card, text="CONTRASEÑA", **lbl_kw).pack(anchor="w", padx=24)
        self.entry_password = ctk.CTkEntry(
            card, placeholder_text="••••••••", show="•", **ent_kw
        )
        self.entry_password.pack(padx=24, pady=(4, 0))

        # Mensaje de error (oculto hasta que haya error)
        self.lbl_error = ctk.CTkLabel(
            card, text="", font=("Arial", 11),
            text_color="#FF5C5C", wraplength=340
        )
        self.lbl_error.pack(padx=24, pady=(8, 0))

        self.btn_login = ctk.CTkButton(
            card, text="INGRESAR",
            command=self._intentar_login,
            fg_color="#A3F843", hover_color="#91E03A",
            text_color="#000000", font=("Arial", 13, "bold"),
            corner_radius=10, height=44, width=340,
        )
        self.btn_login.pack(padx=24, pady=(16, 24))

        # Footer
        ctk.CTkLabel(
            self, text="Club Nahuel  •  Sistema de Reservas",
            font=("Arial", 9), text_color="#2A2A2A"
        ).pack(pady=(0, 10))

        self.entry_email.focus()

    def _intentar_login(self):
        email    = self.entry_email.get().strip()
        password = self.entry_password.get()

        if not email or not password:
            self._mostrar_error("Completá email y contraseña.")
            return

        self.btn_login.configure(state="disabled", text="Verificando...")
        self.update()

        try:
            usuario = verificar_login(email, password)
        except ValueError as e:
            self._mostrar_error(str(e))
            self.btn_login.configure(state="normal", text="INGRESAR")
            return

        self.btn_login.configure(state="normal", text="INGRESAR")

        if usuario is None:
            self._mostrar_error("Email o contraseña incorrectos.")
            self.entry_password.delete(0, "end")
            return

        SessionManager.iniciar_sesion(usuario)
        self._abrir_principal()

    def _mostrar_error(self, mensaje: str):
        self.lbl_error.configure(text=mensaje)

    def _abrir_principal(self):
        from ui.main_window import MainWindow
        self.withdraw()
        MainWindow(self)
