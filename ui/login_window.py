# ui/login_window.py
import threading
import customtkinter as ctk
from auth.auth_service import verificar_login
from auth.session import SessionManager


class LoginWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Club Nahuel — Iniciar sesión")
        self.resizable(False, False)
        self.configure(fg_color="#0D0D0D")
        self._set_centered(420, 300)
        self._build_splash()
        self.after(300, self._verificar_conexion)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _set_centered(self, width: int, height: int):
        from ui.ventana_mixin import centrar_ventana
        self.update_idletasks()
        centrar_ventana(self, width, height)

    # ── Splash / conexión ─────────────────────────────────────────────────────

    def _build_splash(self):
        self._splash = ctk.CTkFrame(self, fg_color="transparent")
        self._splash.place(relx=0.5, rely=0.42, anchor="center")

        ctk.CTkLabel(self._splash, text="◈",
            font=("Arial Black", 52), text_color="#A3F843").pack()
        ctk.CTkLabel(self._splash, text="CLUB NAHUEL",
            font=("Arial Black", 22, "bold"), text_color="#FFFFFF").pack(pady=(4, 0))
        ctk.CTkFrame(self._splash, height=2, width=80, fg_color="#A3F843",
            corner_radius=1).pack(pady=14)

        self._lbl_estado = ctk.CTkLabel(
            self._splash, text="Conectando al servidor...",
            font=("Arial", 11), text_color="#555555",
        )
        self._lbl_estado.pack()

        self._btn_reintentar = ctk.CTkButton(
            self._splash, text="REINTENTAR",
            command=self._verificar_conexion,
            fg_color="#A3F843", hover_color="#C5FF6B",
            text_color="#0D0D0D", font=("Arial Black", 11, "bold"),
            corner_radius=10, height=40, width=160,
        )
        self._btn_salir = ctk.CTkButton(
            self._splash, text="SALIR",
            command=self.destroy,
            fg_color="transparent", hover_color="#1A0000",
            text_color="#FF5C5C", border_color="#2A0000", border_width=1,
            corner_radius=10, height=40, width=160,
        )

        ctk.CTkLabel(self, text="v 1.2",
            font=("Arial", 9), text_color="#2A2A2A").place(relx=0.5, rely=0.93, anchor="center")

    def _verificar_conexion(self):
        self._btn_reintentar.pack_forget()
        self._btn_salir.pack_forget()
        self._lbl_estado.configure(text="Conectando al servidor...", text_color="#555555")
        threading.Thread(target=self._chequear_en_hilo, daemon=True).start()

    def _chequear_en_hilo(self):
        from db.database import probar_conexion
        ok = probar_conexion()
        self.after(0, self._on_resultado, ok)

    def _on_resultado(self, ok: bool):
        if ok:
            self._splash.destroy()
            self._set_centered(720, 460)
            self._build_ui()
            self.bind("<Return>", lambda e: self._intentar_login())
        else:
            self._lbl_estado.configure(
                text="No se pudo conectar al servidor.\nVerificá tu conexión a internet.",
                text_color="#FF5C5C",
            )
            self._btn_reintentar.pack(pady=(16, 6))
            self._btn_salir.pack()

    # ── Login form ────────────────────────────────────────────────────────────

    def _build_ui(self):
        # Panel izquierdo — marca
        left = ctk.CTkFrame(self, fg_color="#A3F843", corner_radius=0, width=265)
        left.pack(side="left", fill="y")
        left.pack_propagate(False)

        brand = ctk.CTkFrame(left, fg_color="transparent")
        brand.place(relx=0.5, rely=0.44, anchor="center")

        ctk.CTkLabel(brand, text="◈",
            font=("Arial Black", 54), text_color="#0D0D0D").pack()
        ctk.CTkLabel(brand, text="CLUB\nNAHUEL",
            font=("Arial Black", 26, "bold"), text_color="#0D0D0D",
            justify="center").pack(pady=(2, 0))
        ctk.CTkFrame(brand, height=2, width=90, fg_color="#0D0D0D",
            corner_radius=1).pack(pady=(16, 16))
        ctk.CTkLabel(brand, text="S I S T E M A  D E  R E S E R V A S",
            font=("Arial", 8, "bold"), text_color="#1E1E1E").pack()

        ctk.CTkLabel(left, text="v 1.2",
            font=("Arial", 9), text_color="#2C2C1A").place(relx=0.5, rely=0.93, anchor="center")

        # Panel derecho — formulario
        right = ctk.CTkFrame(self, fg_color="#0D0D0D", corner_radius=0)
        right.pack(side="left", fill="both", expand=True)

        form_wrap = ctk.CTkFrame(right, fg_color="transparent")
        form_wrap.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(form_wrap, text="Hola, bienvenido",
            font=("Arial", 12), text_color="#3A3A3A").pack(anchor="w")
        ctk.CTkLabel(form_wrap, text="Iniciar sesión",
            font=("Arial Black", 24, "bold"), text_color="#FFFFFF").pack(anchor="w", pady=(2, 28))

        lbl_kw = {"font": ("Arial", 10, "bold"), "text_color": "#555555", "anchor": "w"}
        ent_kw = {
            "fg_color": "#141414", "border_color": "#252525", "border_width": 1,
            "text_color": "#FFFFFF", "corner_radius": 10,
            "height": 46, "width": 310,
            "placeholder_text_color": "#333333",
        }

        ctk.CTkLabel(form_wrap, text="USUARIO", **lbl_kw).pack(anchor="w")
        self.entry_email = ctk.CTkEntry(form_wrap, placeholder_text="Nombre de usuario", **ent_kw)
        self.entry_email.pack(pady=(4, 18))

        ctk.CTkLabel(form_wrap, text="CONTRASEÑA", **lbl_kw).pack(anchor="w")
        self.entry_password = ctk.CTkEntry(
            form_wrap, placeholder_text="••••••••", show="•", **ent_kw
        )
        self.entry_password.pack(pady=(4, 0))

        self.lbl_error = ctk.CTkLabel(
            form_wrap, text="", font=("Arial", 11),
            text_color="#FF5C5C", wraplength=310, anchor="w"
        )
        self.lbl_error.pack(pady=(8, 0), anchor="w")

        self.btn_login = ctk.CTkButton(
            form_wrap, text="INGRESAR  →",
            command=self._intentar_login,
            fg_color="#A3F843", hover_color="#C5FF6B",
            text_color="#0D0D0D", font=("Arial Black", 13, "bold"),
            corner_radius=10, height=48, width=310,
        )
        self.btn_login.pack(pady=(20, 0))

        self.entry_email.focus()

    # ── Auth ──────────────────────────────────────────────────────────────────

    def _intentar_login(self):
        email    = self.entry_email.get().strip()
        password = self.entry_password.get()

        if not email or not password:
            self._mostrar_error("Completá usuario y contraseña.")
            return

        self.btn_login.configure(state="disabled", text="Verificando...")
        self.update()

        try:
            usuario = verificar_login(email, password)
        except ValueError as e:
            self._mostrar_error(str(e))
            self.btn_login.configure(state="normal", text="INGRESAR  →")
            return

        self.btn_login.configure(state="normal", text="INGRESAR  →")

        if usuario is None:
            self._mostrar_error("Usuario o contraseña incorrectos.")
            self.entry_password.delete(0, "end")
            return

        SessionManager.iniciar_sesion(usuario)
        self.entry_email.delete(0, "end")
        self.entry_password.delete(0, "end")
        self._abrir_principal()

    def _mostrar_error(self, mensaje: str):
        self.lbl_error.configure(text=mensaje)

    def _abrir_principal(self):
        usuario = SessionManager.get_usuario_actual()
        self.withdraw()
        if usuario and usuario.rol == "supervisor":
            from ui.supervisor_window import SupervisorWindow
            SupervisorWindow(self)
        else:
            from ui.main_window import MainWindow
            MainWindow(self)
