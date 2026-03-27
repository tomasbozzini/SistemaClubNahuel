# ui/reservas_window.py
import customtkinter as ctk
from ui.ventana_mixin import VentanaMixin
from tkcalendar import DateEntry
from tkinter import messagebox
from datetime import datetime
from auth.session import SessionManager
from utils.validaciones import validar_horario
from models.canchas_service import listar_canchas_activas
from models.reservas_service import insertar_reserva, hay_superposicion


_DURACION_LABEL = {"padel": "1 h 30 min", "futbol": "1 hora", "tenis": "1 hora"}
_COLOR_TIPO = {"padel": "#00C4FF", "futbol": "#A3F843", "tenis": "#FF8C42"}


class ReservasWindow(VentanaMixin, ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.withdraw()

        if not SessionManager.esta_logueado():
            self.after(0, self.destroy)
            return

        self.title("Nueva Reserva")
        width, height = 520, 570
        self.geometry(f"{width}x{height}")
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (width  // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")
        self.resizable(False, False)
        self.transient(parent)
        self.configure(fg_color="#0D0D0D")

        # Barra de acento
        ctk.CTkFrame(self, height=4, fg_color="#A3F843", corner_radius=0).pack(fill="x")

        # Header
        hdr = ctk.CTkFrame(self, fg_color="#111111", corner_radius=0)
        hdr.pack(fill="x")
        ctk.CTkLabel(hdr, text="NUEVA RESERVA",
            font=("Arial Black", 20, "bold"), text_color="#FFFFFF").pack(
            anchor="w", padx=28, pady=(16, 2))
        ctk.CTkLabel(hdr, text="Completá los datos del turno",
            font=("Arial", 11), text_color="#A3F843").pack(anchor="w", padx=28, pady=(0, 14))

        ctk.CTkFrame(self, height=1, fg_color="#1C1C1C", corner_radius=0).pack(fill="x")

        # Card formulario
        card = ctk.CTkFrame(self, fg_color="#141414", corner_radius=0)
        card.pack(padx=0, pady=0, fill="both", expand=True)

        lbl_kw  = {"font": ("Arial", 10, "bold"), "text_color": "#555555", "anchor": "w"}
        ent_kw  = {"width": 432, "fg_color": "#1A1A1A", "border_color": "#252525",
                   "border_width": 1, "text_color": "#FFFFFF", "corner_radius": 10, "height": 40}

        # Cliente
        ctk.CTkLabel(card, text="CLIENTE", **lbl_kw).pack(anchor="w", padx=28, pady=(22, 4))
        self.entry_cliente = ctk.CTkEntry(card, placeholder_text="Nombre del cliente", **ent_kw)
        self.entry_cliente.pack(padx=28)

        # Cancha
        ctk.CTkLabel(card, text="CANCHA", **lbl_kw).pack(anchor="w", padx=28, pady=(16, 4))
        self.canchas = listar_canchas_activas()
        opciones = [f"{r[1]} ({r[2]})" for r in self.canchas]

        self.combo_cancha = ctk.CTkComboBox(card, values=opciones, width=432, height=40,
            fg_color="#1A1A1A", border_color="#252525", border_width=1,
            text_color="#FFFFFF", button_color="#252525", button_hover_color="#A3F843",
            dropdown_fg_color="#1A1A1A", dropdown_text_color="#FFFFFF", corner_radius=10,
            command=self._actualizar_hint)
        if opciones:
            self.combo_cancha.set(opciones[0])
        self.combo_cancha.pack(padx=28)

        # Hint de duración
        self.lbl_hint = ctk.CTkLabel(card, text="",
            font=("Arial", 10, "bold"), text_color="#444444", anchor="w")
        self.lbl_hint.pack(anchor="w", padx=28, pady=(4, 0))
        self._actualizar_hint()

        # Fila fecha / hora
        fila = ctk.CTkFrame(card, fg_color="transparent")
        fila.pack(padx=28, fill="x", pady=(14, 0))

        col_fecha = ctk.CTkFrame(fila, fg_color="transparent")
        col_fecha.pack(side="left", expand=True, fill="x", padx=(0, 14))
        ctk.CTkLabel(col_fecha, text="FECHA", **lbl_kw).pack(anchor="w", pady=(0, 4))
        self.date_entry = DateEntry(col_fecha, date_pattern="yyyy-mm-dd",
            background="#1A1A1A", foreground="white", borderwidth=0,
            headersbackground="#0D0D0D", headersforeground="#A3F843",
            selectbackground="#A3F843", selectforeground="black",
            normalbackground="#1A1A1A", normalforeground="white",
            weekendbackground="#1A1A1A", weekendforeground="#A3F843",
            font=("Arial", 11))
        self.date_entry.pack(anchor="w", ipady=6)

        col_hora = ctk.CTkFrame(fila, fg_color="transparent")
        col_hora.pack(side="left", expand=True, fill="x")
        ctk.CTkLabel(col_hora, text="HORA  (HH:MM)", **lbl_kw).pack(anchor="w", pady=(0, 4))
        self.entry_hora = ctk.CTkEntry(col_hora, placeholder_text="14:30",
            height=40, fg_color="#1A1A1A", border_color="#252525", border_width=1,
            text_color="#FFFFFF", corner_radius=10)
        self.entry_hora.pack(fill="x")

        # Observaciones
        ctk.CTkLabel(card, text="OBSERVACIONES", **lbl_kw).pack(anchor="w", padx=28, pady=(16, 4))
        self.entry_obs = ctk.CTkEntry(card, placeholder_text="Opcional", **ent_kw)
        self.entry_obs.pack(padx=28)

        # Botón guardar
        ctk.CTkFrame(card, height=1, fg_color="#1C1C1C", corner_radius=0).pack(
            fill="x", pady=(20, 0))
        ctk.CTkButton(card, text="GUARDAR RESERVA  →", command=self.guardar,
            fg_color="#A3F843", hover_color="#C5FF6B", text_color="#0D0D0D",
            font=("Arial Black", 13, "bold"), corner_radius=0, width=520, height=46
        ).pack(fill="x")

        self.after(150, self._mostrar_ventana)

    def _actualizar_hint(self, *_):
        seleccion = self.combo_cancha.get()
        cancha = next((r for r in self.canchas if f"{r[1]} ({r[2]})" == seleccion), None)
        if not cancha:
            self.lbl_hint.configure(text="")
            return
        tipo = cancha[2].lower().replace("á", "a").replace("ú", "u")
        duracion = _DURACION_LABEL.get(tipo, "1 hora")
        color    = _COLOR_TIPO.get(tipo, "#666666")
        self.lbl_hint.configure(
            text=f"Duración del turno:  {duracion}",
            text_color=color
        )

    def guardar(self):
        cliente   = self.entry_cliente.get().strip()
        seleccion = self.combo_cancha.get()
        fecha     = self.date_entry.get_date().isoformat()
        hora      = self.entry_hora.get().strip()
        obs       = self.entry_obs.get().strip()

        if not cliente:
            messagebox.showerror("Error", "Ingresá el nombre del cliente.")
            return
        if not seleccion:
            messagebox.showerror("Error", "Seleccioná una cancha.")
            return
        if not hora:
            messagebox.showwarning("Error", "Ingresá un horario.")
            return
        if not validar_horario(hora):
            messagebox.showerror("Error", "Formato de hora inválido. Use HH:MM (ej: 14:30).")
            return

        try:
            reserva_dt = datetime.strptime(f"{fecha} {hora}", "%Y-%m-%d %H:%M")
        except ValueError:
            messagebox.showerror("Error", "Fecha u hora inválida.")
            return
        if reserva_dt <= datetime.now():
            messagebox.showerror(
                "Horario inválido",
                "No se puede reservar en una fecha y hora pasada."
            )
            return

        cancha_id = next((r[0] for r in self.canchas if f"{r[1]} ({r[2]})" == seleccion), None)
        if cancha_id is None:
            messagebox.showerror("Error", "No se pudo identificar la cancha seleccionada.")
            return
        if hay_superposicion(cancha_id, fecha, hora):
            messagebox.showerror("Error", "Esa cancha ya está ocupada en ese horario.")
            return

        reserva_id = insertar_reserva(cliente, cancha_id, fecha, hora, obs)
        messagebox.showinfo("Reserva guardada", f"Reserva #{reserva_id} registrada correctamente.")
        self.event_generate("<<ReservaGuardada>>", when="tail")
        self.destroy()
