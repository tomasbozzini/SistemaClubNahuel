# ui/disponibilidad_window.py
"""
Vista de disponibilidad en tiempo real.
Muestra una grilla con las canchas como columnas y los horarios como filas.
"""
import customtkinter as ctk
from ui.ventana_mixin import VentanaMixin
import tkinter as tk
from tkcalendar import DateEntry
from datetime import date, datetime, time, timedelta
from auth.session import SessionManager
from models.canchas_service import listar_canchas_activas
from models.reservas_service import listar_reservas_por_fecha

_COLOR = "#00D68F"
_SLOT_MINUTES = 30
_HORA_INICIO  = 8
_HORA_FIN     = 22

# Colores de celdas
_BG_LIBRE     = "#0F1F0F"
_FG_LIBRE     = "#00D68F"
_BG_OCUPADO   = "#1A0A0A"
_FG_OCUPADO   = "#FF5C5C"
_BG_PASADO    = "#0D0D0D"
_FG_PASADO    = "#2A2A2A"
_BG_HEADER    = "#111111"
_FG_HEADER    = "#555555"


def _slots() -> list[str]:
    result = []
    h, m = _HORA_INICIO, 0
    while h < _HORA_FIN or (h == _HORA_FIN and m == 0):
        result.append(f"{h:02d}:{m:02d}")
        m += _SLOT_MINUTES
        if m >= 60:
            m -= 60
            h += 1
    return result


def _slot_time(slot: str) -> time:
    h, m = map(int, slot.split(":"))
    return time(h, m)


def _slot_end_time(slot: str) -> time:
    dt = datetime.combine(date.today(), _slot_time(slot)) + timedelta(minutes=_SLOT_MINUTES)
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

        self._build_ui()
        self.after(150, self._mostrar_ventana)

    # ── Construcción UI ───────────────────────────────────────────────────────

    def _build_ui(self):
        ctk.CTkFrame(self, height=4, fg_color=_COLOR, corner_radius=0).pack(fill="x")

        # Header
        hdr = ctk.CTkFrame(self, fg_color="#111111", corner_radius=0)
        hdr.pack(fill="x")
        hdr_inner = ctk.CTkFrame(hdr, fg_color="transparent")
        hdr_inner.pack(fill="x", padx=28, pady=(14, 12))

        ctk.CTkLabel(hdr_inner, text="DISPONIBILIDAD EN TIEMPO REAL",
            font=("Arial Black", 20, "bold"), text_color="#FFFFFF").pack(side="left")

        # Leyenda
        leyenda = ctk.CTkFrame(hdr_inner, fg_color="transparent")
        leyenda.pack(side="right", padx=(0, 8))
        for txt, col in [("● Libre", _FG_LIBRE), ("● Ocupado", _FG_OCUPADO), ("● Pasado", _FG_PASADO)]:
            ctk.CTkLabel(leyenda, text=txt, font=("Arial", 10, "bold"),
                text_color=col).pack(side="left", padx=8)

        ctk.CTkFrame(self, height=1, fg_color="#1C1C1C", corner_radius=0).pack(fill="x")

        # Barra de filtros
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

        ctk.CTkFrame(self, height=1, fg_color="#1C1C1C", corner_radius=0).pack(fill="x")

        # Canvas + scrollbars para la grilla
        wrap = ctk.CTkFrame(self, fg_color="#0D0D0D", corner_radius=0)
        wrap.pack(fill="both", expand=True)

        self._canvas = tk.Canvas(wrap, bg="#0D0D0D", highlightthickness=0)
        vsb = tk.Scrollbar(wrap, orient="vertical",   command=self._canvas.yview)
        hsb = tk.Scrollbar(wrap, orient="horizontal", command=self._canvas.xview)
        self._canvas.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        vsb.pack(side="right",  fill="y")
        hsb.pack(side="bottom", fill="x")
        self._canvas.pack(side="left", fill="both", expand=True)

        self._grid_frame = tk.Frame(self._canvas, bg="#0D0D0D")
        self._canvas_window = self._canvas.create_window(
            (0, 0), window=self._grid_frame, anchor="nw"
        )
        self._grid_frame.bind(
            "<Configure>",
            lambda e: self._canvas.configure(scrollregion=self._canvas.bbox("all"))
        )
        self._canvas.bind("<Configure>", self._on_canvas_resize)

        # Scroll con rueda del mouse
        self._canvas.bind_all("<MouseWheel>",
            lambda e: self._canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))

        self._refrescar()
        self._iniciar_auto_refresh()

    def _on_canvas_resize(self, event):
        self._canvas.itemconfig(self._canvas_window, width=event.width)

    # ── Lógica ────────────────────────────────────────────────────────────────

    def _refrescar(self):
        fecha_str = self._date_entry.get()
        try:
            fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date()
        except ValueError:
            fecha = date.today()
        self._build_grid(fecha)
        self._lbl_update.configure(
            text=f"Última actualización: {datetime.now().strftime('%H:%M:%S')}"
        )

    def _build_grid(self, fecha_date: date):
        for w in self._grid_frame.winfo_children():
            w.destroy()

        canchas  = listar_canchas_activas()   # [(id, nombre, tipo), ...]
        reservas = listar_reservas_por_fecha(fecha_date)
        # reservas: [(cancha_id, cancha_nombre, hora_inicio, hora_fin, nombre_cliente), ...]

        # Mapa de ocupación: {(cancha_id, slot) -> nombre_cliente}
        ocupacion: dict[tuple, str] = {}
        all_slots = _slots()
        for cid, cname, hora_ini, hora_fin, cliente in reservas:
            for slot in all_slots:
                s_start = _slot_time(slot)
                s_end   = _slot_end_time(slot)
                try:
                    r_start = _slot_time(hora_ini)
                    r_end   = _slot_time(hora_fin)
                except ValueError:
                    continue
                if r_start < s_end and r_end > s_start:
                    ocupacion[(cid, slot)] = cliente

        ahora    = datetime.now().time()
        es_hoy   = (fecha_date == date.today())

        # Dimensiones de celdas
        time_w  = 64
        cell_w  = max(110, (1000 - time_w - 20) // max(len(canchas), 1))
        cell_h  = 30
        pad_x   = 1
        pad_y   = 1

        lbl_kw = {"font": ("Arial", 9, "bold"), "anchor": "center",
                  "relief": "flat", "bd": 0}

        # ── Fila de encabezado de canchas ──
        tk.Label(self._grid_frame, text="Hora", bg=_BG_HEADER, fg=_FG_HEADER,
                 width=7, height=2, **lbl_kw).grid(
            row=0, column=0, padx=pad_x, pady=pad_y, sticky="nsew")

        for col, (cid, cname, ctype) in enumerate(canchas, 1):
            tipo_norm = ctype.lower().replace("á", "a").replace("ú", "u")
            tipo_color = {"padel": "#00C4FF", "futbol": "#A3F843", "tenis": "#FF8C42"}.get(tipo_norm, "#666666")
            lbl = tk.Label(self._grid_frame,
                text=f"{cname}\n{ctype.capitalize()}",
                bg=_BG_HEADER, fg=tipo_color,
                width=cell_w // 7, height=2, **lbl_kw)
            lbl.grid(row=0, column=col, padx=pad_x, pady=pad_y, sticky="nsew")
            self._grid_frame.columnconfigure(col, minsize=cell_w)

        self._grid_frame.columnconfigure(0, minsize=time_w)

        # ── Filas de horarios ──
        for row, slot in enumerate(all_slots, 1):
            slot_end = _slot_end_time(slot)
            is_past  = es_hoy and slot_end <= ahora

            # Resaltar slot actual
            slot_start = _slot_time(slot)
            is_now = es_hoy and slot_start <= ahora < slot_end

            time_bg = "#1A1A1A" if is_now else ("#0D0D0D" if is_past else "#111111")
            time_fg = _COLOR if is_now else (_FG_PASADO if is_past else "#666666")

            tk.Label(self._grid_frame, text=slot,
                bg=time_bg, fg=time_fg,
                width=7, height=2, **lbl_kw).grid(
                row=row, column=0, padx=pad_x, pady=pad_y, sticky="nsew")

            for col, (cid, cname, ctype) in enumerate(canchas, 1):
                key = (cid, slot)
                if is_past:
                    bg, fg, txt = _BG_PASADO, _FG_PASADO, "—"
                elif key in ocupacion:
                    cliente = ocupacion[key]
                    # Truncar nombre si es muy largo
                    txt = cliente[:14] + "…" if len(cliente) > 14 else cliente
                    bg, fg = _BG_OCUPADO, _FG_OCUPADO
                else:
                    bg, fg, txt = _BG_LIBRE, _FG_LIBRE, "LIBRE"

                tk.Label(self._grid_frame, text=txt,
                    bg=bg, fg=fg,
                    width=cell_w // 7, height=2, **lbl_kw).grid(
                    row=row, column=col, padx=pad_x, pady=pad_y, sticky="nsew")

        self._canvas.update_idletasks()
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))

    def _iniciar_auto_refresh(self):
        """Refresca la grilla automáticamente cada 60 segundos."""
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
        super().destroy()
