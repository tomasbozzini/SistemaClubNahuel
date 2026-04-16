# ui/calendario_reservas_window.py
import customtkinter as ctk
from ui.ventana_mixin import VentanaMixin, centrar_ventana
from tkcalendar import Calendar
from datetime import datetime
from auth.session import SessionManager
from models.reservas_service import listar_reservas_por_fecha

_COLOR_TIPO = {"pádel": "#00C4FF", "padel": "#00C4FF",
               "fútbol": "#7C5CFF", "futbol": "#7C5CFF",
               "tenis": "#FF8C42"}


class CalendarioWindow(VentanaMixin, ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.withdraw()

        if not SessionManager.esta_logueado():
            self.after(0, self.destroy)
            return

        self.title("Calendario de Reservas")
        self.update_idletasks()
        centrar_ventana(self, 880, 540)
        self.resizable(False, False)
        self.transient(parent)
        self.configure(fg_color="#0D0D0D")

        # Barra de acento purple (color de "calendario")
        ctk.CTkFrame(self, height=4, fg_color="#9D6EFF", corner_radius=0).pack(fill="x")

        # Header
        hdr = ctk.CTkFrame(self, fg_color="#111111", corner_radius=0)
        hdr.pack(fill="x")
        ctk.CTkLabel(hdr, text="CALENDARIO DE RESERVAS",
            font=("Arial Black", 20, "bold"), text_color="#FFFFFF").pack(
            anchor="w", padx=28, pady=(16, 2))
        ctk.CTkLabel(hdr, text="Seleccioná un día para ver los turnos",
            font=("Arial", 11), text_color="#9D6EFF").pack(anchor="w", padx=28, pady=(0, 14))

        ctk.CTkFrame(self, height=1, fg_color="#1C1C1C", corner_radius=0).pack(fill="x")

        # Body
        body = ctk.CTkFrame(self, fg_color="#0D0D0D")
        body.pack(padx=0, pady=0, fill="both", expand=True)

        # ── Panel izquierdo — calendario ─────────────────────────────────────
        left = ctk.CTkFrame(body, fg_color="#111111", corner_radius=0, width=295)
        left.pack(side="left", fill="y")
        left.pack_propagate(False)

        ctk.CTkFrame(left, height=1, fg_color="#1C1C1C", corner_radius=0).pack(fill="x")

        cal_wrap = ctk.CTkFrame(left, fg_color="transparent")
        cal_wrap.pack(pady=(16, 0), padx=12)

        self.calendar = Calendar(cal_wrap, selectmode="day", date_pattern="yyyy-mm-dd",
            background="#111111", foreground="white", borderwidth=0,
            headersbackground="#0D0D0D", headersforeground="#9D6EFF",
            selectbackground="#9D6EFF", selectforeground="white",
            normalbackground="#111111", normalforeground="#BBBBBB",
            weekendbackground="#111111", weekendforeground="#9D6EFF",
            othermonthbackground="#0D0D0D", othermonthforeground="#333333",
            font=("Arial", 11), showweeknumbers=False)
        self.calendar.pack()

        ctk.CTkFrame(left, height=1, fg_color="#1C1C1C", corner_radius=0).pack(
            fill="x", pady=(14, 0))

        self.orden_por_deporte = False
        self.btn_ordenar = ctk.CTkButton(left, text="Ordenar por deporte",
            command=self.toggle_orden,
            fg_color="transparent", hover_color="#161616",
            text_color="#9D6EFF", border_color="#1E1428", border_width=1,
            corner_radius=0, height=36, font=("Arial", 11))
        self.btn_ordenar.pack(fill="x")

        ctk.CTkFrame(left, height=1, fg_color="#1C1C1C", corner_radius=0).pack(fill="x")

        btn_wrap = ctk.CTkFrame(left, fg_color="transparent")
        btn_wrap.pack(fill="x", padx=14, pady=(16, 0))
        ctk.CTkButton(btn_wrap, text="✦  NUEVA RESERVA",
            command=self._abrir_reserva,
            fg_color="#7C5CFF", hover_color="#9D84FF",
            text_color="#FFFFFF", font=("Arial Black", 11, "bold"),
            corner_radius=10, height=38).pack(fill="x")

        # Separador vertical
        ctk.CTkFrame(body, width=1, fg_color="#1C1C1C", corner_radius=0).pack(side="left", fill="y")

        # ── Panel derecho — reservas del día ─────────────────────────────────
        right = ctk.CTkFrame(body, fg_color="#0D0D0D", corner_radius=0)
        right.pack(side="left", fill="both", expand=True)

        # Cabecera del panel derecho
        right_hdr = ctk.CTkFrame(right, fg_color="#111111", corner_radius=0)
        right_hdr.pack(fill="x")
        self.lbl_fecha_sel = ctk.CTkLabel(right_hdr, text="",
            font=("Arial Black", 14), text_color="#9D6EFF")
        self.lbl_fecha_sel.pack(anchor="w", padx=20, pady=(12, 4))
        self.lbl_n_reservas = ctk.CTkLabel(right_hdr, text="",
            font=("Arial", 11), text_color="#333333")
        self.lbl_n_reservas.pack(anchor="w", padx=20, pady=(0, 10))
        ctk.CTkFrame(right_hdr, height=1, fg_color="#1C1C1C", corner_radius=0).pack(fill="x")

        # Scrollable frame de tarjetas
        self.scroll_frame = ctk.CTkScrollableFrame(right,
            fg_color="#0D0D0D", corner_radius=0,
            scrollbar_button_color="#1C1C1C",
            scrollbar_button_hover_color="#2A2A2A")
        self.scroll_frame.pack(fill="both", expand=True, padx=0, pady=0)

        self.calendar.bind("<<CalendarSelected>>", lambda e: self.mostrar_reservas())
        self.mostrar_reservas()
        self.after(150, self._mostrar_ventana)

    def _abrir_reserva(self):
        from ui.reservas_window import ReservasWindow
        win = ReservasWindow(self.master)
        win.lift()
        win.focus_force()

    def toggle_orden(self):
        self.orden_por_deporte = not self.orden_por_deporte
        self.btn_ordenar.configure(
            text="Ordenar por hora" if self.orden_por_deporte else "Ordenar por deporte"
        )
        self.mostrar_reservas()

    def mostrar_reservas(self):
        fecha = self.calendar.get_date()
        self.lbl_fecha_sel.configure(text=fecha)

        # Limpiar tarjetas anteriores
        for w in self.scroll_frame.winfo_children():
            w.destroy()

        from datetime import datetime as _dt
        fecha_date = _dt.strptime(fecha, "%Y-%m-%d").date()
        # listar_reservas_por_fecha devuelve:
        # (cancha_id, cancha_nombre, hora_ini, hora_fin, cliente, tipo)
        raw = listar_reservas_por_fecha(fecha_date)
        # Convertir al formato que espera el resto del método:
        # (id, cliente, cancha, tipo, fecha, hora, notas)
        reservas = [
            (None, r[4], r[1], r[5] if len(r) > 5 else "", fecha, r[2], "")
            for r in raw
        ]

        if self.orden_por_deporte:
            reservas.sort(key=lambda r: (r[3], _dt.strptime(r[5], "%H:%M")))
        else:
            reservas.sort(key=lambda r: _dt.strptime(r[5], "%H:%M"))

        n = len(reservas)
        self.lbl_n_reservas.configure(
            text=f"{n} turno{'s' if n != 1 else ''}" if n else "Sin reservas"
        )

        if not reservas:
            empty = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
            empty.pack(expand=True, pady=60)
            ctk.CTkLabel(empty, text="◉",
                font=("Arial", 32), text_color="#1C1C1C").pack()
            ctk.CTkLabel(empty, text="Sin reservas para este día",
                font=("Arial", 12), text_color="#2A2A2A").pack(pady=(6, 0))
            return

        ultimo_tipo = None
        for res in reservas:
            # res = (id, cliente, cancha, tipo, fecha, hora, notas)
            tipo_raw = res[3].lower().replace("á", "a").replace("ú", "u")
            color = _COLOR_TIPO.get(tipo_raw, _COLOR_TIPO.get(res[3].lower(), "#666666"))

            # Encabezado de grupo (si ordena por deporte)
            if self.orden_por_deporte and res[3] != ultimo_tipo:
                ultimo_tipo = res[3]
                sep = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
                sep.pack(fill="x", padx=16, pady=(12, 4))
                ctk.CTkLabel(sep, text=f"  {res[3].upper()}",
                    font=("Arial", 10, "bold"), text_color=color).pack(side="left")
                ctk.CTkFrame(sep, height=1, fg_color=color).pack(
                    side="left", fill="x", expand=True, padx=(8, 0), pady=6)

            # Tarjeta de reserva
            card = ctk.CTkFrame(self.scroll_frame, fg_color="#141414",
                corner_radius=4, border_width=1, border_color="#1E1E1E",
                height=30)
            card.pack(fill="x", padx=14, pady=1)
            card.pack_propagate(False)

            # Barra de acento izquierda
            ctk.CTkFrame(card, width=3, fg_color=color, corner_radius=0).pack(
                side="left", fill="y")

            # Hora
            ctk.CTkLabel(card, text=res[5],
                font=("Arial Black", 11, "bold"), text_color=color,
                width=46).pack(side="left", padx=(8, 0))

            # Separador
            ctk.CTkFrame(card, width=1, fg_color="#222222", corner_radius=0).pack(
                side="left", fill="y", pady=5)

            # Cancha + cliente
            ctk.CTkLabel(card, text=res[2],
                font=("Arial", 11, "bold"), text_color="#CCCCCC").pack(side="left", padx=(10, 0))
            ctk.CTkLabel(card, text=f"  ·  {res[1]}",
                font=("Arial", 10), text_color="#444444").pack(side="left")

            # Notas
            if res[6]:
                ctk.CTkLabel(card, text=res[6],
                    font=("Arial", 9), text_color="#2A2A2A").pack(side="right", padx=8)
