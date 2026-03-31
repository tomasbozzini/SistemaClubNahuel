# ui/disponibilidad_window.py
"""
Vista de disponibilidad en tiempo real.
Grilla: canchas como columnas (encabezado fijo) y horarios como filas (scroll vertical).
"""
import customtkinter as ctk
from ui.ventana_mixin import VentanaMixin
import tkinter as tk
from tkcalendar import DateEntry
from datetime import date, datetime, time, timedelta
from auth.session import SessionManager
from models.canchas_service import listar_canchas_con_precio
from models.reservas_service import listar_reservas_por_fecha

_COLOR       = "#00D68F"
_SLOT_MINUTES = 30
_HORA_INICIO  = 8
_HORA_FIN     = 24

_BG_LIBRE    = "#0F1F0F"
_FG_LIBRE    = "#00D68F"
_BG_OCUPADO  = "#1A0A0A"
_FG_OCUPADO  = "#FF5C5C"
_BG_PASADO   = "#0D0D0D"
_FG_PASADO   = "#2A2A2A"
_BG_HEADER   = "#111111"
_FG_HEADER   = "#555555"
_TIME_W      = 64   # ancho de la columna de hora
_CELL_H      = 34   # alto de cada celda


def _slots() -> list[str]:
    result, h, m = [], _HORA_INICIO, 0
    while h < _HORA_FIN:
        result.append(f"{h:02d}:{m:02d}")
        m += _SLOT_MINUTES
        if m >= 60:
            m -= 60
            h += 1
    result.append("00:00")
    return result


def _t(slot: str) -> time:
    h, m = map(int, slot.split(":"))
    return time(h, m)


def _t_end(slot: str) -> time:
    dt = datetime.combine(date.today(), _t(slot)) + timedelta(minutes=_SLOT_MINUTES)
    return dt.time()


class DisponibilidadWindow(VentanaMixin, ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.withdraw()

        if not SessionManager.esta_logueado():
            self.after(0, self.destroy)
            return

        self.title("Disponibilidad en Tiempo Real — Club Nahuel")
        width, height = 1000, 680
        self.geometry(f"{width}x{height}")
        self.update_idletasks()
        x = (self.winfo_screenwidth()  // 2) - (width  // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")
        self.transient(parent)
        self.resizable(True, True)
        self.configure(fg_color="#0D0D0D")

        self._auto_refresh_id = None
        self._cell_w = 130   # ancho por columna de cancha (se recalcula)

        self._build_ui()
        self.after(150, self._mostrar_ventana)

    # ── Construcción UI ───────────────────────────────────────────────────────

    def _build_ui(self):
        ctk.CTkFrame(self, height=4, fg_color=_COLOR, corner_radius=0).pack(fill="x")

        # Título
        hdr = ctk.CTkFrame(self, fg_color="#111111", corner_radius=0)
        hdr.pack(fill="x")
        hdr_inner = ctk.CTkFrame(hdr, fg_color="transparent")
        hdr_inner.pack(fill="x", padx=28, pady=(14, 12))
        ctk.CTkLabel(hdr_inner, text="DISPONIBILIDAD EN TIEMPO REAL",
            font=("Arial Black", 20, "bold"), text_color="#FFFFFF").pack(side="left")
        leyenda = ctk.CTkFrame(hdr_inner, fg_color="transparent")
        leyenda.pack(side="right", padx=(0, 8))
        for txt, col in [("● Libre", _FG_LIBRE), ("● Ocupado", _FG_OCUPADO), ("● Pasado", _FG_PASADO)]:
            ctk.CTkLabel(leyenda, text=txt, font=("Arial", 10, "bold"),
                text_color=col).pack(side="left", padx=8)

        ctk.CTkFrame(self, height=1, fg_color="#1C1C1C", corner_radius=0).pack(fill="x")

        # Filtros
        filtros = ctk.CTkFrame(self, fg_color="#141414", corner_radius=0)
        filtros.pack(fill="x")
        frow = ctk.CTkFrame(filtros, fg_color="transparent")
        frow.pack(padx=24, pady=12, fill="x")
        ctk.CTkLabel(frow, text="FECHA", font=("Arial", 10, "bold"),
            text_color="#555555").pack(side="left", padx=(0, 8))
        self._date_entry = DateEntry(frow, date_pattern="yyyy-mm-dd",
            background="#1A1A1A", foreground="white", borderwidth=0,
            headersbackground="#0D0D0D", headersforeground=_COLOR,
            selectbackground=_COLOR, selectforeground="black",
            normalbackground="#1A1A1A", normalforeground="white",
            weekendbackground="#1A1A1A", weekendforeground=_COLOR,
            font=("Arial", 11))
        self._date_entry.pack(side="left", ipady=5)
        self._date_entry.bind("<<DateEntrySelected>>", lambda _: self._refrescar())
        ctk.CTkButton(frow, text="↺  ACTUALIZAR", width=140, height=32,
            fg_color="transparent", hover_color="#1A1A1A",
            text_color=_COLOR, border_color="#003A22", border_width=1,
            corner_radius=8, font=("Arial", 11, "bold"),
            command=self._refrescar,
        ).pack(side="left", padx=16)
        self._lbl_update = ctk.CTkLabel(frow, text="",
            font=("Arial", 10), text_color="#333333")
        self._lbl_update.pack(side="left")

        ctk.CTkButton(frow, text="＋  NUEVA RESERVA", width=160, height=32,
            fg_color="transparent", hover_color="#1A1A1A",
            text_color="#CCCCCC", border_color="#333333", border_width=1,
            corner_radius=8, font=("Arial", 11, "bold"),
            command=self._abrir_nueva_reserva,
        ).pack(side="right")

        ctk.CTkFrame(self, height=1, fg_color="#1C1C1C", corner_radius=0).pack(fill="x")

        # ── Área de grilla ────────────────────────────────────────────────────
        wrap = tk.Frame(self, bg="#0D0D0D")
        wrap.pack(fill="both", expand=True)

        # Scrollbars
        vsb = tk.Scrollbar(wrap, orient="vertical",   bg="#1C1C1C", troughcolor="#0D0D0D")
        hsb = tk.Scrollbar(wrap, orient="horizontal", bg="#1C1C1C", troughcolor="#0D0D0D")

        # Fila superior: esquina fija + encabezados de canchas
        top_row = tk.Frame(wrap, bg=_BG_HEADER)
        self._corner = tk.Frame(top_row, bg=_BG_HEADER, width=_TIME_W, height=_CELL_H + 2)
        self._corner.pack_propagate(False)
        self._corner.pack(side="left")
        self._hdr_canvas = tk.Canvas(top_row, bg=_BG_HEADER, highlightthickness=0,
                                     height=_CELL_H + 2)
        self._hdr_canvas.pack(side="left", fill="x", expand=True)

        # Fila inferior: horarios fijos + celdas de canchas
        bot_row = tk.Frame(wrap, bg="#0D0D0D")
        self._time_canvas = tk.Canvas(bot_row, bg="#0D0D0D", highlightthickness=0,
                                      width=_TIME_W)
        self._time_canvas.pack(side="left", fill="y")
        self._body_canvas = tk.Canvas(bot_row, bg="#0D0D0D", highlightthickness=0)
        self._body_canvas.pack(side="left", fill="both", expand=True)

        # Sincronización de scroll
        self._syncing_y = False

        def _xscroll(*args):
            self._hdr_canvas.xview(*args)
            self._body_canvas.xview(*args)

        def _body_xview_changed(*args):
            hsb.set(*args)
            self._hdr_canvas.xview_moveto(args[0])

        def _body_yview_changed(*args):
            vsb.set(*args)
            if not self._syncing_y:
                self._syncing_y = True
                self._time_canvas.yview_moveto(args[0])
                self._syncing_y = False

        def _time_yview_changed(*args):
            if not self._syncing_y:
                self._syncing_y = True
                self._body_canvas.yview_moveto(args[0])
                self._syncing_y = False

        def _yscroll(*args):
            self._body_canvas.yview(*args)
            self._time_canvas.yview(*args)

        hsb.configure(command=_xscroll)
        vsb.configure(command=_yscroll)
        self._body_canvas.configure(
            xscrollcommand=_body_xview_changed,
            yscrollcommand=_body_yview_changed,
        )
        self._time_canvas.configure(yscrollcommand=_time_yview_changed)

        # Pack: vsb y hsb primero para que ocupen los bordes correctamente
        vsb.pack(side="right",  fill="y")
        hsb.pack(side="bottom", fill="x")
        top_row.pack(side="top", fill="x")
        bot_row.pack(side="top", fill="both", expand=True)

        # Frames dentro de los canvases
        self._hdr_frame  = tk.Frame(self._hdr_canvas,  bg=_BG_HEADER)
        self._time_frame = tk.Frame(self._time_canvas, bg="#0D0D0D")
        self._body_frame = tk.Frame(self._body_canvas, bg="#0D0D0D")

        self._hdr_canvas.create_window( (0, 0), window=self._hdr_frame,  anchor="nw")
        self._time_canvas.create_window((0, 0), window=self._time_frame, anchor="nw")
        self._body_canvas.create_window((0, 0), window=self._body_frame, anchor="nw")

        self._hdr_frame.bind("<Configure>",
            lambda e: self._hdr_canvas.configure(scrollregion=self._hdr_canvas.bbox("all")))
        self._time_frame.bind("<Configure>",
            lambda e: self._time_canvas.configure(scrollregion=self._time_canvas.bbox("all")))
        self._body_frame.bind("<Configure>",
            lambda e: self._body_canvas.configure(scrollregion=self._body_canvas.bbox("all")))

        def _on_mousewheel(e):
            units = int(-1 * (e.delta / 120))
            self._body_canvas.yview_scroll(units, "units")
            self._time_canvas.yview_scroll(units, "units")

        self._mw_binding = self.bind_all("<MouseWheel>", _on_mousewheel, add="+")

        self._refrescar()
        self._iniciar_auto_refresh()

    # ── Lógica ────────────────────────────────────────────────────────────────

    def _refrescar(self):
        fecha_str = self._date_entry.get()
        try:
            fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date()
        except ValueError:
            fecha = date.today()
        self._build_grid(fecha)
        self._lbl_update.configure(
            text=f"Actualizado: {datetime.now().strftime('%H:%M:%S')}"
        )

    def _build_grid(self, fecha_date: date):
        for w in self._hdr_frame.winfo_children():
            w.destroy()
        for w in self._time_frame.winfo_children():
            w.destroy()
        for w in self._body_frame.winfo_children():
            w.destroy()

        canchas  = listar_canchas_con_precio()  # (id, nombre, tipo, precio, duracion_minutos)
        reservas = listar_reservas_por_fecha(fecha_date)

        # Duración por cancha (en minutos)
        dur_map = {c[0]: (c[4] or 60) for c in canchas}

        # Dos mapas:
        #   ocupacion_activa:   slot cubierto por la reserva → muestra nombre del cliente
        #   ocupacion_bloqueada: slot previo que generaría conflicto → rojo sin nombre
        ocupacion_activa:    dict[tuple, str] = {}
        ocupacion_bloqueada: set[tuple]       = set()
        all_slots = _slots()

        def _to_min(hora_str: str) -> int:
            h, m = map(int, hora_str.split(":"))
            v = h * 60 + m
            return 1440 if v == 0 else v  # 00:00 = fin de día

        for cid, _, hora_ini, hora_fin, cliente in reservas:
            dur     = dur_map.get(cid, 60)
            ini_min = _to_min(hora_ini)
            fin_min = _to_min(hora_fin)
            for slot in all_slots:
                try:
                    slot_min      = _to_min(slot)
                    slot_end_30   = slot_min + _SLOT_MINUTES   # fin del bloque de 30 min
                    slot_end_dur  = slot_min + dur              # fin si reservara acá
                    # ¿El slot está dentro de la reserva existente?
                    cubierto      = ini_min < slot_end_30 and fin_min > slot_min
                    # ¿Reservar acá generaría conflicto?
                    conflicto     = slot_min < fin_min and slot_end_dur > ini_min
                    if cubierto:
                        ocupacion_activa[(cid, slot)] = cliente
                    elif conflicto:
                        ocupacion_bloqueada.add((cid, slot))
                except ValueError:
                    continue

        ahora  = datetime.now().time()
        es_hoy = (fecha_date == date.today())

        # Ancho de celda: distribuir espacio disponible
        n_canchas   = max(len(canchas), 1)
        self._cell_w = max(110, (980 - _TIME_W) // n_canchas)
        cw = self._cell_w

        lbl_kw = {"font": ("Arial", 9, "bold"), "anchor": "center", "relief": "flat", "bd": 0}

        # ── Encabezado de canchas (en hdr_frame) ──────────────────────────────
        for col, (cid, cname, ctype, _p, _d) in enumerate(canchas):
            tipo_norm = ctype.lower().replace("á", "a").replace("ú", "u")
            tipo_color = {"padel": "#00C4FF", "futbol": "#A3F843", "tenis": "#FF8C42"}.get(tipo_norm, "#888888")
            tk.Label(self._hdr_frame,
                text=f"{cname}\n{ctype.capitalize()}",
                bg=_BG_HEADER, fg=tipo_color,
                width=cw // 7, height=2, **lbl_kw).grid(
                row=0, column=col, padx=1, pady=1, sticky="nsew")
            self._hdr_frame.columnconfigure(col, minsize=cw)

        # ── Filas de horarios (en body_frame) ─────────────────────────────────
        for col in range(len(canchas)):
            self._body_frame.columnconfigure(col, minsize=cw)

        for row, slot in enumerate(all_slots):
            s_end   = _t_end(slot)
            s_start = _t(slot)
            # Si s_end < s_start el slot cruza medianoche; usar fin-de-día para comparar
            s_end_cmp = s_end if s_end > s_start else time(23, 59, 59)
            is_past = es_hoy and s_end_cmp <= ahora
            is_now  = es_hoy and s_start <= ahora < s_end

            time_bg = "#1C1C1C" if is_now else ("#0D0D0D" if is_past else "#111111")
            time_fg = _COLOR    if is_now else (_FG_PASADO if is_past else "#555555")

            # Horario en el canvas fijo de tiempo
            tk.Label(self._time_frame, text=slot,
                bg=time_bg, fg=time_fg,
                width=_TIME_W // 7, height=2, **lbl_kw).grid(
                row=row, column=0, padx=1, pady=1, sticky="nsew")

            for col, (cid, cname, ctype, _p, _d) in enumerate(canchas):
                key = (cid, slot)
                if is_past:
                    bg, fg, txt = _BG_PASADO, _FG_PASADO, "—"
                elif key in ocupacion_activa:
                    cliente = ocupacion_activa[key]
                    txt = cliente[:15] + "…" if len(cliente) > 15 else cliente
                    bg, fg = _BG_OCUPADO, _FG_OCUPADO
                elif key in ocupacion_bloqueada:
                    bg, fg, txt = _BG_OCUPADO, "#3A1A1A", "—"
                else:
                    bg, fg, txt = _BG_LIBRE, _FG_LIBRE, "LIBRE"

                tk.Label(self._body_frame, text=txt,
                    bg=bg, fg=fg,
                    width=cw // 7, height=2, **lbl_kw).grid(
                    row=row, column=col, padx=1, pady=1, sticky="nsew")

        # Actualizar scroll regions
        self._hdr_frame.update_idletasks()
        self._time_frame.update_idletasks()
        self._body_frame.update_idletasks()
        self._hdr_canvas.configure(scrollregion=self._hdr_canvas.bbox("all"))
        self._time_canvas.configure(scrollregion=self._time_canvas.bbox("all"))
        self._body_canvas.configure(scrollregion=self._body_canvas.bbox("all"))

    def _abrir_nueva_reserva(self):
        from ui.reservas_window import ReservasWindow
        win = ReservasWindow(self)
        win.bind("<<ReservaGuardada>>", lambda e: self._refrescar())

    def _iniciar_auto_refresh(self):
        self._refrescar()
        try:
            self._auto_refresh_id = self.after(60_000, self._iniciar_auto_refresh)
        except Exception:
            pass

    def destroy(self):
        if self._auto_refresh_id:
            try:
                self.after_cancel(self._auto_refresh_id)
            except Exception:
                pass
        try:
            self.unbind_all("<MouseWheel>")
        except Exception:
            pass
        super().destroy()
