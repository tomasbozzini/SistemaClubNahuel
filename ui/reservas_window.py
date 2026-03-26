# ui/reservas_window.py
import customtkinter as ctk
from tkcalendar import DateEntry
from tkinter import messagebox
from utils.validaciones import validar_horario
from models.models import listar_canchas, insertar_reserva, hay_superposicion


class ReservasWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Nueva Reserva")
        width, height = 520, 550
        self.geometry(f"{width}x{height}")
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")
        self.resizable(False, False)
        self.transient(parent)
        self.configure(fg_color="#121212")

        # Barra superior
        ctk.CTkFrame(self, height=4, fg_color="#A3F843", corner_radius=0).pack(fill="x")

        # Header
        ctk.CTkLabel(self, text="NUEVA RESERVA",
            font=("Arial Black", 22, "bold"), text_color="#FFFFFF").pack(pady=(20, 0))
        ctk.CTkLabel(self, text="Completá los datos del turno",
            font=("Arial", 11), text_color="#A3F843").pack(pady=(2, 0))
        ctk.CTkFrame(self, height=1, fg_color="#2A2A2A", corner_radius=0).pack(fill="x", padx=40, pady=(14, 0))

        # Card formulario
        card = ctk.CTkFrame(self, fg_color="#1A1A1A", corner_radius=14)
        card.pack(padx=36, pady=18, fill="both", expand=True)

        lbl_kw = {"font": ("Arial", 10, "bold"), "text_color": "#777777", "anchor": "w"}
        ent_kw = {"width": 408, "fg_color": "#212121", "border_color": "#333333",
                  "text_color": "#FFFFFF", "corner_radius": 8, "height": 38}

        ctk.CTkLabel(card, text="CLIENTE", **lbl_kw).pack(anchor="w", padx=22, pady=(18, 3))
        self.entry_cliente = ctk.CTkEntry(card, placeholder_text="Nombre del cliente", **ent_kw)
        self.entry_cliente.pack(padx=22)

        ctk.CTkLabel(card, text="CANCHA", **lbl_kw).pack(anchor="w", padx=22, pady=(12, 3))
        self.canchas = listar_canchas()
        opciones = [f"{r[1]} ({r[2]})" for r in self.canchas]
        self.combo_cancha = ctk.CTkComboBox(card, values=opciones, width=408, height=38,
            fg_color="#212121", border_color="#333333", text_color="#FFFFFF",
            button_color="#333333", button_hover_color="#A3F843",
            dropdown_fg_color="#1E1E1E", dropdown_text_color="#FFFFFF", corner_radius=8)
        if opciones:
            self.combo_cancha.set(opciones[0])
        self.combo_cancha.pack(padx=22)

        # Fecha y hora en la misma fila
        fila = ctk.CTkFrame(card, fg_color="transparent")
        fila.pack(padx=22, fill="x", pady=(12, 0))

        col_fecha = ctk.CTkFrame(fila, fg_color="transparent")
        col_fecha.pack(side="left", expand=True, fill="x", padx=(0, 12))
        ctk.CTkLabel(col_fecha, text="FECHA", **lbl_kw).pack(anchor="w", pady=(0, 4))
        self.date_entry = DateEntry(col_fecha, date_pattern="yyyy-mm-dd",
            background="#1A1A1A", foreground="white", borderwidth=0,
            headersbackground="#121212", headersforeground="#A3F843",
            selectbackground="#A3F843", selectforeground="black",
            normalbackground="#1A1A1A", normalforeground="white",
            weekendbackground="#1A1A1A", weekendforeground="#A3F843",
            font=("Arial", 11))
        self.date_entry.pack(anchor="w", ipady=5)

        col_hora = ctk.CTkFrame(fila, fg_color="transparent")
        col_hora.pack(side="left", expand=True, fill="x")
        ctk.CTkLabel(col_hora, text="HORA  (HH:MM)", **lbl_kw).pack(anchor="w", pady=(0, 4))
        self.entry_hora = ctk.CTkEntry(col_hora, placeholder_text="14:30",
            height=38, fg_color="#212121", border_color="#333333",
            text_color="#FFFFFF", corner_radius=8)
        self.entry_hora.pack(fill="x")

        ctk.CTkLabel(card, text="OBSERVACIONES", **lbl_kw).pack(anchor="w", padx=22, pady=(12, 3))
        self.entry_obs = ctk.CTkEntry(card, placeholder_text="Opcional", **ent_kw)
        self.entry_obs.pack(padx=22)

        ctk.CTkButton(card, text="GUARDAR RESERVA", command=self.guardar,
            fg_color="#A3F843", hover_color="#91E03A", text_color="#000000",
            font=("Arial", 13, "bold"), corner_radius=10, width=408, height=42
        ).pack(padx=22, pady=(18, 22))

    def guardar(self):
        cliente = self.entry_cliente.get().strip()
        seleccion = self.combo_cancha.get()
        fecha = self.date_entry.get_date().isoformat()
        hora = self.entry_hora.get().strip()
        obs = self.entry_obs.get().strip()

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

        cancha_id = next((r[0] for r in self.canchas if f"{r[1]} ({r[2]})" == seleccion), None)
        if cancha_id is None:
            messagebox.showerror("Error", "No se pudo identificar la cancha seleccionada.")
            return
        if hay_superposicion(cancha_id, fecha, hora):
            messagebox.showerror("Error", "Esa cancha ya está ocupada en ese horario (bloqueo de 1 hora).")
            return

        reserva_id = insertar_reserva(cliente, cancha_id, fecha, hora, obs)
        messagebox.showinfo("Reserva guardada", f"Reserva #{reserva_id} registrada correctamente.")
        self.destroy()
