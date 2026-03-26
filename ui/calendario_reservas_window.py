# ui/calendario_reservas_window.py
import customtkinter as ctk
from tkcalendar import Calendar
from tkinter import END
from models.models import listar_reservas
from datetime import datetime


class CalendarioWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Calendario de Reservas")
        width, height = 860, 530
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
        ctk.CTkLabel(self, text="CALENDARIO DE RESERVAS",
            font=("Arial Black", 20, "bold"), text_color="#FFFFFF").pack(pady=(18, 0))
        ctk.CTkLabel(self, text="Seleccioná un día para ver los turnos",
            font=("Arial", 11), text_color="#A3F843").pack(pady=(2, 0))
        ctk.CTkFrame(self, height=1, fg_color="#2A2A2A", corner_radius=0).pack(fill="x", padx=32, pady=(12, 0))

        # Body: columna izquierda (calendario) + columna derecha (lista)
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(padx=32, pady=14, fill="both", expand=True)

        # --- Izquierda: calendario + botón ordenar ---
        left = ctk.CTkFrame(body, fg_color="#1A1A1A", corner_radius=14)
        left.pack(side="left", fill="y", padx=(0, 12))

        self.calendar = Calendar(left, selectmode="day", date_pattern="yyyy-mm-dd",
            background="#1A1A1A", foreground="white", borderwidth=0,
            headersbackground="#121212", headersforeground="#A3F843",
            selectbackground="#A3F843", selectforeground="black",
            normalbackground="#1A1A1A", normalforeground="white",
            weekendbackground="#1A1A1A", weekendforeground="#A3F843",
            othermonthbackground="#121212", othermonthforeground="#444444",
            font=("Arial", 11), showweeknumbers=False)
        self.calendar.pack(padx=14, pady=(14, 10))

        self.orden_por_deporte = False
        self.btn_ordenar = ctk.CTkButton(left, text="Ordenar por deporte",
            command=self.toggle_orden,
            fg_color="#212121", hover_color="#2A2A2A",
            text_color="#A3F843", border_color="#333333", border_width=1,
            corner_radius=8, height=34, font=("Arial", 11))
        self.btn_ordenar.pack(padx=14, pady=(0, 14), fill="x")

        # --- Derecha: fecha seleccionada + lista de reservas ---
        right = ctk.CTkFrame(body, fg_color="#1A1A1A", corner_radius=14)
        right.pack(side="left", fill="both", expand=True)

        self.lbl_fecha_sel = ctk.CTkLabel(right, text="",
            font=("Arial Black", 13), text_color="#FFFFFF")
        self.lbl_fecha_sel.pack(anchor="w", padx=18, pady=(16, 4))

        self.textbox = ctk.CTkTextbox(right,
            fg_color="#121212", text_color="#CCCCCC",
            font=("Courier New", 12), corner_radius=8,
            scrollbar_button_color="#2A2A2A",
            scrollbar_button_hover_color="#3A3A3A",
            border_width=0)
        self.textbox.pack(padx=12, pady=(0, 12), fill="both", expand=True)
        self.textbox.configure(state="disabled")

        self.calendar.bind("<<CalendarSelected>>", lambda e: self.mostrar_reservas())
        self.mostrar_reservas()

    def toggle_orden(self):
        self.orden_por_deporte = not self.orden_por_deporte
        self.btn_ordenar.configure(
            text="Ordenar por hora" if self.orden_por_deporte else "Ordenar por deporte"
        )
        self.mostrar_reservas()

    def mostrar_reservas(self):
        fecha = self.calendar.get_date()
        self.lbl_fecha_sel.configure(text=fecha)

        reservas = [r for r in listar_reservas() if r[4] == fecha]

        if self.orden_por_deporte:
            reservas.sort(key=lambda r: (r[3], datetime.strptime(r[5], "%H:%M")))
        else:
            reservas.sort(key=lambda r: datetime.strptime(r[5], "%H:%M"))

        self.textbox.configure(state="normal")
        self.textbox.delete("1.0", END)

        if not reservas:
            self.textbox.insert(END, "\n  Sin reservas para este día.")
        else:
            current_tipo = None
            for res in reservas:
                if self.orden_por_deporte and res[3] != current_tipo:
                    current_tipo = res[3]
                    self.textbox.insert(END, f"\n  ── {current_tipo} ──\n")
                self.textbox.insert(END, f"  {res[5]}   {res[2]:<20}  {res[1]}\n")

        self.textbox.configure(state="disabled")
