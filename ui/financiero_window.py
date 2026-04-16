# ui/financiero_window.py
import customtkinter as ctk
from ui.ventana_mixin import VentanaMixin, centrar_ventana
from tkinter import ttk
from datetime import date
from auth.session import SessionManager
from models.reservas_service import listar_historial_financiero, totales_financieros
from models.canchas_service import listar_canchas_activas
from ui.export_service import exportar_excel_financiero, exportar_pdf_financiero

_COLOR = "#FFD700"


def _fmt_peso(valor: float) -> str:
    return f"$ {int(valor):,}".replace(",", ".")


class FinancieroWindow(VentanaMixin, ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.withdraw()

        if not SessionManager.esta_logueado():
            self.after(0, self.destroy)
            return

        from db.database import get_club_nombre
        self.title(f"Historial Financiero — {get_club_nombre()}")
        self.update_idletasks()
        centrar_ventana(self, 1100, 680)
        self.transient(parent)
        self.resizable(False, False)
        self.configure(fg_color="#0D0D0D")

        self._periodo   = "hoy"
        self._cancha_id = None
        self._lbl_totales: dict[str, ctk.CTkLabel] = {}
        self._filas_actuales: list = []

        self._build_ui()
        self.after(150, self._mostrar_ventana)

    # ── Construcción UI ───────────────────────────────────────────────────────

    def _build_ui(self):
        ctk.CTkFrame(self, height=4, fg_color=_COLOR, corner_radius=0).pack(fill="x")

        # Header
        hdr = ctk.CTkFrame(self, fg_color="#111111", corner_radius=0)
        hdr.pack(fill="x")
        ctk.CTkLabel(hdr, text="HISTORIAL FINANCIERO",
            font=("Arial Black", 20, "bold"), text_color="#FFFFFF").pack(
            anchor="w", padx=28, pady=(16, 2))
        ctk.CTkLabel(hdr, text="Registros de reservas y totales recaudados",
            font=("Arial", 11), text_color=_COLOR).pack(
            anchor="w", padx=28, pady=(0, 14))
        ctk.CTkFrame(self, height=1, fg_color="#1C1C1C", corner_radius=0).pack(fill="x")

        self._build_tarjetas_totales()
        ctk.CTkFrame(self, height=1, fg_color="#1C1C1C", corner_radius=0).pack(fill="x")

        self._build_filtros()
        ctk.CTkFrame(self, height=1, fg_color="#1C1C1C", corner_radius=0).pack(fill="x")

        self._build_tabla()
        self._aplicar_filtros()

    def _build_tarjetas_totales(self):
        wrap = ctk.CTkFrame(self, fg_color="#111111", corner_radius=0)
        wrap.pack(fill="x")
        inner = ctk.CTkFrame(wrap, fg_color="transparent")
        inner.pack(padx=24, pady=14)

        cards_def = [
            ("hoy",   "HOY",       "#FFD700"),
            ("mes",   "ESTE MES",  "#00C4FF"),
            ("anio",  "ESTE AÑO",  "#7C5CFF"),
            ("total", "TOTAL",     "#9D6EFF"),
        ]
        for key, titulo, color in cards_def:
            card = ctk.CTkFrame(inner, fg_color="#1A1A1A", corner_radius=12,
                border_width=1, border_color="#2A2A2A", width=230, height=74)
            card.pack(side="left", padx=7)
            card.pack_propagate(False)
            ctk.CTkFrame(card, height=3, fg_color=color, corner_radius=0).place(
                x=0, y=0, relwidth=1.0)
            ctk.CTkLabel(card, text=titulo,
                font=("Arial", 9, "bold"), text_color="#444444").place(x=14, y=14)
            lbl = ctk.CTkLabel(card, text=_fmt_peso(0),
                font=("Arial Black", 15, "bold"), text_color=color)
            lbl.place(x=14, y=36)
            self._lbl_totales[key] = lbl

    def _build_filtros(self):
        wrap = ctk.CTkFrame(self, fg_color="#141414", corner_radius=0)
        wrap.pack(fill="x")
        row = ctk.CTkFrame(wrap, fg_color="transparent")
        row.pack(padx=24, pady=13, fill="x")

        lbl_kw = {"font": ("Arial", 10, "bold"), "text_color": "#555555", "anchor": "w"}

        # Periodo
        col_p = ctk.CTkFrame(row, fg_color="transparent")
        col_p.pack(side="left", padx=(0, 24))
        ctk.CTkLabel(col_p, text="PERÍODO", **lbl_kw).pack(anchor="w", pady=(0, 4))
        self._btn_periodos: dict[str, ctk.CTkButton] = {}
        btn_row = ctk.CTkFrame(col_p, fg_color="transparent")
        btn_row.pack()
        for key, label in [("hoy","Hoy"), ("mes","Este mes"), ("anio","Este año"), ("todo","Todos")]:
            btn = ctk.CTkButton(
                btn_row, text=label, width=88, height=32,
                corner_radius=8, font=("Arial", 11),
                fg_color=_COLOR if key == "hoy" else "#1A1A1A",
                hover_color="#FFE55C" if key == "hoy" else "#252525",
                text_color="#0D0D0D" if key == "hoy" else "#888888",
                border_width=1,
                border_color=_COLOR if key == "hoy" else "#2A2A2A",
                command=lambda k=key: self._set_periodo(k),
            )
            btn.pack(side="left", padx=3)
            self._btn_periodos[key] = btn

        # Cancha
        col_c = ctk.CTkFrame(row, fg_color="transparent")
        col_c.pack(side="left")
        ctk.CTkLabel(col_c, text="CANCHA", **lbl_kw).pack(anchor="w", pady=(0, 4))
        canchas = listar_canchas_activas()
        self._map_canchas = {"Todas": None}
        self._map_canchas.update({f"{c[1]} ({c[2]})": c[0] for c in canchas})
        self._combo_cancha = ctk.CTkComboBox(
            col_c, values=list(self._map_canchas.keys()), width=210, height=32,
            fg_color="#1A1A1A", border_color="#2A2A2A", border_width=1,
            text_color="#FFFFFF", button_color="#2A2A2A",
            button_hover_color=_COLOR,
            dropdown_fg_color="#1A1A1A", dropdown_text_color="#FFFFFF",
            corner_radius=8, command=self._on_cancha_change,
        )
        self._combo_cancha.set("Todas")
        self._combo_cancha.pack()

        # Derecha: exportar + contador + refrescar
        side_right = ctk.CTkFrame(row, fg_color="transparent")
        side_right.pack(side="right")
        ctk.CTkButton(
            side_right, text="↺  REFRESCAR", width=130, height=32,
            fg_color="transparent", hover_color="#1A1A1A",
            text_color=_COLOR, border_color="#2A2000", border_width=1,
            corner_radius=8, font=("Arial", 11, "bold"),
            command=self._aplicar_filtros,
        ).pack(side="right", padx=(4, 0))
        ctk.CTkButton(
            side_right, text="⬇ PDF", width=80, height=32,
            fg_color="transparent", hover_color="#0A0A1A",
            text_color="#00C4FF", border_color="#0A1A2A", border_width=1,
            corner_radius=8, font=("Arial", 11, "bold"),
            command=lambda: exportar_pdf_financiero(self._filas_actuales),
        ).pack(side="right", padx=4)
        ctk.CTkButton(
            side_right, text="⬇ EXCEL", width=96, height=32,
            fg_color="transparent", hover_color="#0A1A0A",
            text_color="#7C5CFF", border_color="#2A1F55", border_width=1,
            corner_radius=8, font=("Arial", 11, "bold"),
            command=lambda: exportar_excel_financiero(self._filas_actuales),
        ).pack(side="right", padx=4)
        self._lbl_count = ctk.CTkLabel(side_right, text="",
            font=("Arial", 11), text_color="#333333")
        self._lbl_count.pack(side="right", padx=(0, 12))

    def _build_tabla(self):
        self._aplicar_estilo_tree()
        card = ctk.CTkFrame(self, fg_color="#0F0F0F", corner_radius=0)
        card.pack(fill="both", expand=True)

        # El label se reserva PRIMERO (side=bottom) para que el tree no lo tape
        self._lbl_total_tabla = ctk.CTkLabel(
            card, text="", font=("Arial Black", 12, "bold"), text_color=_COLOR)
        self._lbl_total_tabla.pack(side="bottom", anchor="e", padx=20, pady=8)

        tree_frame = ctk.CTkFrame(card, fg_color="transparent")
        tree_frame.pack(fill="both", expand=True, padx=14, pady=(14, 0))

        cols = ("ID", "Cliente", "Cancha", "Tipo", "Fecha", "Inicio", "Fin", "Duración", "Estado", "Precio")
        self.tree = ttk.Treeview(tree_frame, columns=cols, show="headings",
            style="Club.Treeview")
        widths = {
            "ID": 44, "Cliente": 158, "Cancha": 130, "Tipo": 68,
            "Fecha": 96, "Inicio": 58, "Fin": 58, "Duración": 72,
            "Estado": 96, "Precio": 112,
        }
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=widths.get(c, 80), anchor="center")

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview,
            style="Club.Vertical.TScrollbar")
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.tree.tag_configure("completada", foreground="#7C5CFF")
        self.tree.tag_configure("confirmada", foreground="#FFA040")
        self.tree.tag_configure("cancelada",  foreground="#FF5C5C")

    def _aplicar_estilo_tree(self):
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Club.Treeview",
            background="#0F0F0F", foreground="#888888",
            fieldbackground="#0F0F0F", rowheight=34, borderwidth=0,
            font=("Arial", 11))
        style.configure("Club.Treeview.Heading",
            background="#141414", foreground="#555555",
            font=("Arial", 10, "bold"), relief="flat")
        style.map("Club.Treeview",
            background=[("selected", "#1C1C1C")],
            foreground=[("selected", "#FFFFFF")])
        style.map("Club.Treeview.Heading",
            background=[("active", "#1A1A1A"), ("!active", "#141414")])
        style.configure("Club.Vertical.TScrollbar",
            background="#1C1C1C", troughcolor="#0F0F0F",
            arrowcolor="#333333", borderwidth=0)

    # ── Lógica ────────────────────────────────────────────────────────────────

    def _set_periodo(self, key: str):
        self._periodo = key
        for k, btn in self._btn_periodos.items():
            activo = k == key
            btn.configure(
                fg_color    =_COLOR if activo else "#1A1A1A",
                hover_color ="#FFE55C" if activo else "#252525",
                text_color  ="#0D0D0D" if activo else "#888888",
                border_color=_COLOR if activo else "#2A2A2A",
            )
        self._aplicar_filtros()

    def _on_cancha_change(self, valor: str):
        self._cancha_id = self._map_canchas.get(valor)
        self._aplicar_filtros()

    def _aplicar_filtros(self):
        import threading
        hoy = date.today()
        if self._periodo == "hoy":
            desde, hasta = hoy, hoy
        elif self._periodo == "mes":
            desde, hasta = hoy.replace(day=1), hoy
        elif self._periodo == "anio":
            desde, hasta = hoy.replace(month=1, day=1), hoy
        else:
            desde, hasta = None, None

        # Limpiar tabla y mostrar cursor de espera
        for item in self.tree.get_children():
            self.tree.delete(item)
        self._lbl_count.configure(text="Cargando...")
        self.configure(cursor="watch")

        periodo    = self._periodo
        cancha_id  = self._cancha_id

        def _worker():
            try:
                filas = listar_historial_financiero(
                    fecha_desde=desde,
                    fecha_hasta=hasta,
                    cancha_id=cancha_id,
                )
                datos = totales_financieros()
                self.after(0, lambda: self._poblar_resultados(filas, datos))
            except Exception as e:
                self.after(0, lambda: self._lbl_count.configure(text="Error al cargar"))
                self.after(0, lambda: self.configure(cursor=""))

        threading.Thread(target=_worker, daemon=True).start()

    def _poblar_resultados(self, filas, datos):
        if not self.winfo_exists():
            return
        self.configure(cursor="")
        self._cargar_tabla(filas)
        self._mostrar_totales(datos)

    def _cargar_tabla(self, filas: list):
        self._filas_actuales = filas
        for item in self.tree.get_children():
            self.tree.delete(item)

        total_visible = 0.0
        for f in filas:
            estado    = f[8]
            dur       = f[7]
            dur_str   = f"{dur // 60}h {dur % 60:02d}m" if dur % 60 else f"{dur // 60}h"
            precio_str = _fmt_peso(f[9]) if estado == "completada" else "—"
            tag = estado if estado in ("completada", "confirmada", "cancelada") else ""

            self.tree.insert("", "end", values=(
                f[0], f[1], f[2], f[3].capitalize(),
                f[4], f[5], f[6], dur_str,
                estado.capitalize(), precio_str,
            ), tags=(tag,))

            if estado == "completada":
                total_visible += f[9]

        n = len(filas)
        self._lbl_count.configure(text=f"{n} registro{'s' if n != 1 else ''}")
        self._lbl_total_tabla.configure(
            text=f"Total cobrado (vista actual):  {_fmt_peso(total_visible)}" if total_visible > 0 else ""
        )

    def _actualizar_totales(self):
        import threading
        def _worker():
            try:
                datos = totales_financieros()
                self.after(0, lambda: self._mostrar_totales(datos))
            except Exception:
                pass
        threading.Thread(target=_worker, daemon=True).start()

    def _mostrar_totales(self, datos):
        if not self.winfo_exists():
            return
        self._lbl_totales["hoy"].configure(text=_fmt_peso(datos["hoy"]))
        self._lbl_totales["mes"].configure(text=_fmt_peso(datos["mes"]))
        self._lbl_totales["anio"].configure(text=_fmt_peso(datos["anio"]))
        self._lbl_totales["total"].configure(text=_fmt_peso(datos["total"]))
