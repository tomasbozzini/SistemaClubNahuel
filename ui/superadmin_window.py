# ui/superadmin_window.py
# Panel completo del superadmin con sidebar + 6 secciones.

import threading
import tkinter as tk
import customtkinter as ctk
from auth.session import SessionManager
from ui.ventana_mixin import VentanaMixin, _get_work_area

# ── Paleta ────────────────────────────────────────────────────────────────────
_BG      = "#0D0D0D"
_PANEL   = "#111111"
_CARD    = "#141414"
_BORDER  = "#222222"
_ACCENT  = "#7C5CFF"   # violeta eléctrico principal
_ACCENT2 = "#00D4FF"   # cian eléctrico secundario
_RED     = "#FF5C5C"
_GOLD    = "#FFD700"
_TEAL    = "#2DD4BF"
_ORANGE  = "#FF8C42"

_NAV_ITEMS = [
    ("◉", "Dashboard"),
    ("◈", "Clubes"),
    ("◎", "Resumen"),
    ("✦", "Supervisores"),
    ("$", "Finanzas"),
    ("≡", "Logs"),
    ("⚙", "Operaciones"),
]


class SuperAdminWindow(VentanaMixin, ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.withdraw()

        if not SessionManager.esta_logueado() or not SessionManager.es_superadmin():
            self.after(0, self._volver_login)
            return

        self.title("SuperAdmin — Sistema Club")
        self.update_idletasks()
        work_w, work_h = _get_work_area(self)
        width  = min(1100, work_w - 20)
        height = min(780,  work_h - 20)
        x = (work_w - width)  // 2
        y = (work_h - height) // 2
        self.geometry(f"{width}x{height}+{x}+{y}")
        self.resizable(False, False)
        self.configure(fg_color=_BG)

        self._seccion_actual = None
        self._nav_btns       = {}
        self._content_frame  = None

        self._build_layout()
        self._seleccionar("Dashboard")

        self.protocol("WM_DELETE_WINDOW", self._cerrar)
        self.after(150, self._mostrar_ventana)

    # ── Layout principal ──────────────────────────────────────────────────────

    def _build_layout(self):
        usuario = SessionManager.get_usuario_actual()

        # Franja superior de color
        ctk.CTkFrame(self, height=3, fg_color=_ACCENT, corner_radius=0).pack(fill="x")

        body = ctk.CTkFrame(self, fg_color=_BG, corner_radius=0)
        body.pack(fill="both", expand=True)

        # ── Sidebar ───────────────────────────────────────────────────────────
        sidebar = ctk.CTkFrame(body, width=210, fg_color=_PANEL, corner_radius=0)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        # Logo / título
        brand = ctk.CTkFrame(sidebar, fg_color="transparent")
        brand.pack(pady=(24, 8), padx=16, fill="x")
        ctk.CTkLabel(brand, text="◈", font=("Arial Black", 28),
                     text_color=_ACCENT).pack()
        ctk.CTkLabel(brand, text="SUPER ADMIN",
                     font=("Arial Black", 13, "bold"),
                     text_color="#FFFFFF").pack(pady=(2, 0))
        ctk.CTkLabel(brand, text="Panel de Control",
                     font=("Arial", 9), text_color="#444444").pack()

        ctk.CTkFrame(sidebar, height=1, fg_color="#1C1C1C",
                     corner_radius=0).pack(fill="x", pady=12)

        # Chips del usuario
        chip = ctk.CTkFrame(sidebar, fg_color="#1A1A1A", corner_radius=20,
                            border_width=1, border_color="#2A2A2A")
        chip.pack(padx=14, pady=(0, 16), fill="x")
        ctk.CTkLabel(chip, text=f"  {usuario.nombre}",
                     font=("Arial", 11, "bold"), text_color=_ACCENT,
                     anchor="w").pack(padx=8, pady=(5, 0), fill="x")
        ctk.CTkLabel(chip, text="  superadmin",
                     font=("Arial", 9), text_color="#444444",
                     anchor="w").pack(padx=8, pady=(0, 5), fill="x")

        # Botones de nav
        nav_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        nav_frame.pack(fill="x", padx=8)
        for icono, nombre in _NAV_ITEMS:
            btn = self._crear_nav_btn(nav_frame, icono, nombre)
            self._nav_btns[nombre] = btn

        # Botones inferiores
        ctk.CTkFrame(sidebar, height=1, fg_color="#1C1C1C",
                     corner_radius=0).pack(fill="x", pady=12, side="bottom")
        bottom = ctk.CTkFrame(sidebar, fg_color="transparent")
        bottom.pack(side="bottom", padx=10, pady=(0, 14), fill="x")
        ctk.CTkButton(
            bottom, text="Cerrar sesión",
            command=self._cerrar_sesion,
            fg_color="transparent", hover_color="#1A0000",
            text_color="#FFA500", border_color="#2A2000", border_width=1,
            corner_radius=8, height=34, font=("Arial", 10, "bold"),
        ).pack(fill="x", pady=(0, 6))
        ctk.CTkButton(
            bottom, text="Salir",
            command=self._cerrar,
            fg_color="transparent", hover_color="#1A0000",
            text_color=_RED, border_color="#2A0000", border_width=1,
            corner_radius=8, height=34, font=("Arial", 10, "bold"),
        ).pack(fill="x")

        # ── Área de contenido ─────────────────────────────────────────────────
        ctk.CTkFrame(body, width=1, fg_color="#1C1C1C",
                     corner_radius=0).pack(side="left", fill="y")
        self._content_frame = ctk.CTkFrame(body, fg_color=_BG, corner_radius=0)
        self._content_frame.pack(side="left", fill="both", expand=True)

    def _crear_nav_btn(self, parent, icono, nombre):
        frame = ctk.CTkFrame(parent, fg_color="transparent", corner_radius=8)
        frame.pack(fill="x", pady=2)

        lbl_icon  = ctk.CTkLabel(frame, text=icono,
                                 font=("Arial Black", 14), text_color="#444444", width=28)
        lbl_icon.pack(side="left", padx=(10, 6), pady=8)
        lbl_text  = ctk.CTkLabel(frame, text=nombre,
                                 font=("Arial", 11), text_color="#888888", anchor="w")
        lbl_text.pack(side="left", fill="x", expand=True)

        def on_click():
            self._seleccionar(nombre)

        def on_enter(_e):
            if self._seccion_actual != nombre:
                frame.configure(fg_color="#1A1A1A")

        def on_leave(_e):
            if self._seccion_actual != nombre:
                frame.configure(fg_color="transparent")

        for w in (frame, lbl_icon, lbl_text):
            w.bind("<Button-1>", lambda _e: on_click())
            w.bind("<Enter>",   on_enter)
            w.bind("<Leave>",   on_leave)

        frame._lbl_icon = lbl_icon
        frame._lbl_text = lbl_text
        return frame

    def _seleccionar(self, nombre: str):
        # Deactivate old
        if self._seccion_actual and self._seccion_actual in self._nav_btns:
            old = self._nav_btns[self._seccion_actual]
            old.configure(fg_color="transparent")
            old._lbl_icon.configure(text_color="#444444")
            old._lbl_text.configure(text_color="#888888",
                                    font=("Arial", 11))

        self._seccion_actual = nombre
        btn = self._nav_btns[nombre]
        btn.configure(fg_color="#1C1C1C")
        btn._lbl_icon.configure(text_color=_ACCENT)
        btn._lbl_text.configure(text_color="#FFFFFF",
                                font=("Arial", 11, "bold"))

        # Limpiar contenido
        for w in self._content_frame.winfo_children():
            w.destroy()

        render = {
            "Dashboard":    self._render_dashboard,
            "Clubes":       self._render_clubes,
            "Resumen":      self._render_resumen,
            "Supervisores": self._render_supervisores,
            "Finanzas":     self._render_finanzas,
            "Logs":         self._render_logs,
            "Operaciones":  self._render_operaciones,
        }.get(nombre)
        if render:
            render()

    # ── Helper widgets ────────────────────────────────────────────────────────

    def _seccion_header(self, titulo: str, subtitulo: str = ""):
        hdr = ctk.CTkFrame(self._content_frame, fg_color="transparent")
        hdr.pack(fill="x", padx=28, pady=(22, 6))
        ctk.CTkLabel(hdr, text=titulo,
                     font=("Arial Black", 20, "bold"),
                     text_color="#FFFFFF").pack(anchor="w")
        if subtitulo:
            ctk.CTkLabel(hdr, text=subtitulo,
                         font=("Arial", 11), text_color="#444444").pack(anchor="w", pady=(2, 0))
        ctk.CTkFrame(self._content_frame, height=1, fg_color="#1C1C1C",
                     corner_radius=0).pack(fill="x", padx=28, pady=(6, 16))

    def _metric_card(self, parent, valor, label, color=_ACCENT):
        card = ctk.CTkFrame(parent, fg_color=_CARD, corner_radius=12,
                            border_width=1, border_color=_BORDER)
        card.pack(side="left", padx=6, pady=4, fill="x", expand=True)
        accent = ctk.CTkFrame(card, height=3, fg_color=color, corner_radius=0)
        accent.pack(fill="x")
        ctk.CTkLabel(card, text=str(valor),
                     font=("Arial Black", 26, "bold"),
                     text_color=color).pack(pady=(10, 0))
        ctk.CTkLabel(card, text=label,
                     font=("Arial", 10), text_color="#555555").pack(pady=(2, 10))
        return card

    def _table_header(self, parent, cols: list[tuple[str, int]]):
        """cols = [(label, width), ...]"""
        row = ctk.CTkFrame(parent, fg_color="#1A1A1A", corner_radius=6)
        row.pack(fill="x", padx=0, pady=(0, 2))
        for label, w in cols:
            ctk.CTkLabel(row, text=label, width=w,
                         font=("Arial", 9, "bold"), text_color="#555555",
                         anchor="w").pack(side="left", padx=(10, 4), pady=6)

    def _table_row(self, parent, valores: list[tuple[str, int]], color="#FFFFFF",
                   alt=False, command=None):
        bg = "#181818" if alt else _CARD
        row = ctk.CTkFrame(parent, fg_color=bg, corner_radius=6,
                           border_width=1, border_color=_BORDER)
        row.pack(fill="x", padx=0, pady=1)
        for texto, w in valores:
            ctk.CTkLabel(row, text=str(texto), width=w,
                         font=("Arial", 10), text_color=color,
                         anchor="w").pack(side="left", padx=(10, 4), pady=6)
        if command:
            row.bind("<Button-1>", lambda _e: command())
        return row

    def _scrollable(self, height=None):
        """Retorna un CTkScrollableFrame dentro de content_frame."""
        sf = ctk.CTkScrollableFrame(
            self._content_frame,
            fg_color="transparent",
            scrollbar_button_color="#2A2A2A",
            scrollbar_button_hover_color="#3A3A3A",
        )
        if height:
            sf.configure(height=height)
        sf.pack(fill="both", expand=True, padx=28, pady=(0, 16))
        return sf

    def _mostrar_toast(self, msg: str, color=_ACCENT):
        toast = ctk.CTkLabel(
            self._content_frame, text=f"  {msg}  ",
            font=("Arial", 11, "bold"), text_color=color,
            fg_color="#1C1C1C", corner_radius=8,
        )
        toast.place(relx=0.5, rely=0.96, anchor="s")
        self.after(2800, lambda: toast.destroy() if toast.winfo_exists() else None)

    # ── SECCIÓN 1 — DASHBOARD ─────────────────────────────────────────────────

    def _render_dashboard(self):
        self._seccion_header("Dashboard", "Métricas globales del sistema")

        lbl_carga = ctk.CTkLabel(self._content_frame, text="Cargando métricas...",
                                 font=("Arial", 12), text_color="#444444")
        lbl_carga.pack(pady=40)

        def _cargar():
            try:
                from models.clubs_service import get_metricas_dashboard
                m = get_metricas_dashboard()
                self.after(0, lambda: self._render_dashboard_datos(m, lbl_carga))
            except Exception as e:
                self.after(0, lambda: lbl_carga.configure(
                    text=f"Error cargando métricas: {e}", text_color=_RED))

        threading.Thread(target=_cargar, daemon=True).start()

    def _render_dashboard_datos(self, m: dict, placeholder):
        if not self._content_frame.winfo_exists():
            return
        try:
            placeholder.destroy()
        except Exception:
            pass

        # Fila 1 — clubes y pagos
        row1 = ctk.CTkFrame(self._content_frame, fg_color="transparent")
        row1.pack(fill="x", padx=28, pady=(0, 8))
        self._metric_card(row1, m["clubes_activos"],   "Clubes activos",   _ACCENT)
        self._metric_card(row1, m["clubes_inactivos"], "Clubes inactivos", "#555555")
        self._metric_card(row1, m["pagos_vencidos"],   "Pagos vencidos",   _RED)
        self._metric_card(row1, m["vencen_pronto"],    "Vencen en 7 días", _GOLD)

        # Fila 2 — financiero y actividad
        row2 = ctk.CTkFrame(self._content_frame, fg_color="transparent")
        row2.pack(fill="x", padx=28, pady=(0, 20))
        self._metric_card(row2, f"${m['ingreso_proyectado']:,.0f}", "Ingreso mensual proyectado", _TEAL)
        self._metric_card(row2, f"${m['pagado_mes']:,.0f}",         "Cobrado este mes",           _ACCENT2)
        self._metric_card(row2, m["total_usuarios"],                "Usuarios activos",           _ORANGE)
        self._metric_card(row2, m["reservas_hoy"],                  "Reservas hoy",               _ACCENT)

        # Acceso rápido
        ctk.CTkLabel(self._content_frame, text="Acceso rápido",
                     font=("Arial Black", 13, "bold"),
                     text_color="#FFFFFF").pack(anchor="w", padx=28, pady=(0, 8))
        quick = ctk.CTkFrame(self._content_frame, fg_color="transparent")
        quick.pack(fill="x", padx=28)

        accesos = [
            ("Gestionar clubes",      "Clubes",      _ACCENT),
            ("Registrar pago",        "Finanzas",    _TEAL),
            ("Crear supervisor",      "Supervisores", _ACCENT2),
            ("Ver logs",              "Logs",        _GOLD),
        ]
        for texto, seccion, color in accesos:
            ctk.CTkButton(
                quick, text=texto,
                command=lambda s=seccion: self._seleccionar(s),
                fg_color=_CARD, hover_color="#1C1C1C",
                text_color=color, border_color=color, border_width=1,
                corner_radius=8, height=36, font=("Arial", 11, "bold"),
            ).pack(side="left", padx=(0, 8))

    # ── SECCIÓN 2 — CLUBES ────────────────────────────────────────────────────

    def _render_clubes(self):
        self._seccion_header("Gestión de Clubes", "Alta, edición y control de estado")

        btn_row = ctk.CTkFrame(self._content_frame, fg_color="transparent")
        btn_row.pack(fill="x", padx=28, pady=(0, 12))
        ctk.CTkButton(
            btn_row, text="+ Nuevo club",
            command=self._dialog_nuevo_club,
            fg_color=_ACCENT, hover_color="#9D84FF",
            text_color="#FFFFFF", font=("Arial Black", 11, "bold"),
            corner_radius=8, height=36, width=140,
        ).pack(side="left")
        ctk.CTkButton(
            btn_row, text="↺ Actualizar",
            command=self._render_clubes,
            fg_color=_CARD, hover_color="#1C1C1C",
            text_color="#888888", border_color=_BORDER, border_width=1,
            corner_radius=8, height=36, width=120,
        ).pack(side="left", padx=(8, 0))

        lbl_carga = ctk.CTkLabel(self._content_frame, text="Cargando clubes...",
                                 font=("Arial", 12), text_color="#444444")
        lbl_carga.pack(pady=20)

        def _cargar():
            try:
                from models.clubs_service import listar_todos_los_clubs
                clubs = listar_todos_los_clubs()
                self.after(0, lambda: self._render_tabla_clubes(clubs, lbl_carga))
            except Exception as e:
                self.after(0, lambda: lbl_carga.configure(
                    text=f"Error: {e}", text_color=_RED))

        threading.Thread(target=_cargar, daemon=True).start()

    def _render_tabla_clubes(self, clubs, placeholder):
        if not self._content_frame.winfo_exists():
            return
        try:
            placeholder.destroy()
        except Exception:
            pass

        sf = self._scrollable()
        cols = [("ID", 30), ("Nombre", 150), ("Ciudad", 85), ("Plan", 65),
                ("Estado", 65), ("Pago", 65), ("Mensual", 65), ("Acciones", 170)]
        self._table_header(sf, cols)

        _ESTADO_COLOR = {"al_dia": _TEAL, "vencido": _RED, "proximo": _GOLD}
        _PLAN_COLOR   = {"basic": "#888888", "pro": _ACCENT2, "enterprise": _GOLD}

        for i, c in enumerate(clubs):
            row = ctk.CTkFrame(sf, fg_color="#181818" if i % 2 else _CARD,
                               corner_radius=6, border_width=1, border_color=_BORDER)
            row.pack(fill="x", pady=1)

            estado_color = "#888888" if not c["activo"] else _TEAL
            pago_color   = _ESTADO_COLOR.get(c.get("estado_pago", ""), "#888888")
            plan_color   = _PLAN_COLOR.get(c.get("plan", ""), "#888888")

            vals = [
                (c["id"],    30),
                (c["nombre"][:18], 150),
                (c.get("ciudad", "-") or "-", 85),
                (c.get("plan", "-"),  65),
                ("Activo" if c["activo"] else "Inactivo", 65),
                (c.get("estado_pago", "-") or "-", 65),
                (f"${c.get('precio_mensual') or 0:.0f}", 65),
            ]
            for texto, w in vals:
                col_text = "#FFFFFF"
                if texto in ("Activo", "Inactivo"):
                    col_text = estado_color
                elif texto == c.get("estado_pago", ""):
                    col_text = pago_color
                elif texto == c.get("plan", ""):
                    col_text = plan_color
                ctk.CTkLabel(row, text=str(texto), width=w,
                             font=("Arial", 10), text_color=col_text,
                             anchor="w").pack(side="left", padx=(10, 4), pady=6)

            # Acciones
            acc = ctk.CTkFrame(row, fg_color="transparent")
            acc.pack(side="left", padx=4)
            club_id = c["id"]
            ctk.CTkButton(
                acc, text="Editar", width=62, height=26,
                fg_color=_CARD, hover_color="#252525",
                text_color=_ACCENT, border_color=_ACCENT, border_width=1,
                corner_radius=6, font=("Arial", 9, "bold"),
                command=lambda cid=club_id: self._dialog_editar_club(cid),
            ).pack(side="left", padx=2)
            estado_txt = "Desact." if c["activo"] else "Activar"
            ctk.CTkButton(
                acc, text=estado_txt, width=62, height=26,
                fg_color=_CARD, hover_color="#252525",
                text_color=_ORANGE, border_color=_ORANGE, border_width=1,
                corner_radius=6, font=("Arial", 9, "bold"),
                command=lambda cid=club_id: self._toggle_club_activo(cid),
            ).pack(side="left", padx=2)

    def _dialog_nuevo_club(self):
        self._dialog_club_form(None)

    def _dialog_editar_club(self, club_id: int):
        def _cargar():
            from models.clubs_service import get_club
            club = get_club(club_id)
            self.after(0, lambda: self._dialog_club_form(club))
        threading.Thread(target=_cargar, daemon=True).start()

    def _dialog_club_form(self, club: dict | None):
        es_edicion = club is not None
        dlg = ctk.CTkToplevel(self)
        dlg.title("Editar club" if es_edicion else "Nuevo club")
        dlg.configure(fg_color=_BG)
        dlg.resizable(False, False)
        dlg.grab_set()
        dlg.update_idletasks()
        w, h = 480, 560
        x = self.winfo_rootx() + (self.winfo_width()  - w) // 2
        y = self.winfo_rooty() + (self.winfo_height() - h) // 2
        dlg.geometry(f"{w}x{h}+{x}+{y}")

        ctk.CTkFrame(dlg, height=3, fg_color=_ACCENT, corner_radius=0).pack(fill="x")
        ctk.CTkLabel(dlg, text="Editar club" if es_edicion else "Nuevo club",
                     font=("Arial Black", 16, "bold"),
                     text_color="#FFFFFF").pack(pady=(18, 4))
        ctk.CTkFrame(dlg, height=1, fg_color="#1C1C1C",
                     corner_radius=0).pack(fill="x", padx=24, pady=(8, 16))

        sf = ctk.CTkScrollableFrame(dlg, fg_color="transparent")
        sf.pack(fill="both", expand=True, padx=24, pady=(0, 8))

        ent_kw = {
            "fg_color": "#141414", "border_color": "#252525", "border_width": 1,
            "text_color": "#FFFFFF", "corner_radius": 8, "height": 40,
        }
        lbl_kw = {"font": ("Arial", 10, "bold"), "text_color": "#555555", "anchor": "w"}

        def campo(label, default=""):
            ctk.CTkLabel(sf, text=label, **lbl_kw).pack(anchor="w", pady=(8, 2))
            e = ctk.CTkEntry(sf, **ent_kw)
            e.pack(fill="x")
            if default:
                e.insert(0, str(default))
            return e

        e_nombre  = campo("Nombre", club["nombre"] if club else "")
        e_ciudad  = campo("Ciudad", club.get("ciudad", "") if club else "")
        e_monto   = campo("Monto implementación", club.get("monto_implementacion", "") if club else "")
        e_mensual = campo("Precio mensual", club.get("precio_mensual", "") if club else "")
        e_dia     = campo("Día vencimiento (1-28)", club.get("dia_vencimiento", "5") if club else "5")
        e_notas   = campo("Notas", club.get("notas", "") if club else "")

        # Plan selector
        ctk.CTkLabel(sf, text="Plan", **lbl_kw).pack(anchor="w", pady=(8, 2))
        plan_var = ctk.StringVar(value=club.get("plan", "basic") if club else "basic")
        plan_frame = ctk.CTkFrame(sf, fg_color="transparent")
        plan_frame.pack(fill="x")
        for p in ("basic", "pro", "enterprise"):
            ctk.CTkRadioButton(
                plan_frame, text=p.capitalize(), variable=plan_var, value=p,
                fg_color=_ACCENT, hover_color="#1C1C1C",
                text_color="#CCCCCC", font=("Arial", 11),
            ).pack(side="left", padx=(0, 16), pady=4)

        # estado_pago (solo edición)
        estado_var = ctk.StringVar(value=club.get("estado_pago", "al_dia") if club else "al_dia")
        if es_edicion:
            ctk.CTkLabel(sf, text="Estado de pago", **lbl_kw).pack(anchor="w", pady=(8, 2))
            ep_frame = ctk.CTkFrame(sf, fg_color="transparent")
            ep_frame.pack(fill="x")
            for ep in ("al_dia", "vencido", "proximo"):
                ctk.CTkRadioButton(
                    ep_frame, text=ep, variable=estado_var, value=ep,
                    fg_color=_ACCENT, hover_color="#1C1C1C",
                    text_color="#CCCCCC", font=("Arial", 11),
                ).pack(side="left", padx=(0, 16), pady=4)

        lbl_err = ctk.CTkLabel(sf, text="", font=("Arial", 10),
                               text_color=_RED, wraplength=400)
        lbl_err.pack(pady=(8, 0))

        def _guardar():
            nombre = e_nombre.get().strip()
            ciudad = e_ciudad.get().strip()
            try:
                monto   = float(e_monto.get().replace(",", ".") or 0)
                mensual = float(e_mensual.get().replace(",", ".") or 0)
                dia     = int(e_dia.get() or 5)
            except ValueError:
                lbl_err.configure(text="Monto, precio y día deben ser números.")
                return
            if not nombre:
                lbl_err.configure(text="El nombre es obligatorio.")
                return
            if not (1 <= dia <= 28):
                lbl_err.configure(text="Día de vencimiento debe estar entre 1 y 28.")
                return

            btn_ok.configure(state="disabled", text="Guardando...")

            def _worker():
                try:
                    if es_edicion:
                        from models.clubs_service import actualizar_club
                        actualizar_club(
                            club["id"], nombre, ciudad, plan_var.get(),
                            monto, mensual, dia, estado_var.get(),
                            e_notas.get().strip(),
                        )
                    else:
                        from models.clubs_service import crear_club
                        crear_club(nombre, ciudad, plan_var.get(),
                                   monto, mensual, dia, e_notas.get().strip())
                    self.after(0, lambda: (dlg.destroy(), self._render_clubes(),
                                          self._mostrar_toast("Club guardado correctamente.")))
                except Exception as ex:
                    self.after(0, lambda: (lbl_err.configure(text=str(ex)),
                                           btn_ok.configure(state="normal", text="Guardar")))

            threading.Thread(target=_worker, daemon=True).start()

        btn_row = ctk.CTkFrame(dlg, fg_color="transparent")
        btn_row.pack(padx=24, pady=12, fill="x")
        ctk.CTkButton(
            btn_row, text="Cancelar", command=dlg.destroy,
            fg_color=_CARD, hover_color="#1C1C1C",
            text_color="#888888", border_color=_BORDER, border_width=1,
            corner_radius=8, height=40,
        ).pack(side="left", expand=True, fill="x", padx=(0, 6))
        btn_ok = ctk.CTkButton(
            btn_row, text="Guardar", command=_guardar,
            fg_color=_ACCENT, hover_color="#9D84FF",
            text_color="#FFFFFF", font=("Arial Black", 11, "bold"),
            corner_radius=8, height=40,
        )
        btn_ok.pack(side="left", expand=True, fill="x")

    def _toggle_club_activo(self, club_id: int):
        def _worker():
            try:
                from models.clubs_service import toggle_activo
                nuevo = toggle_activo(club_id)
                txt = "Activo" if nuevo else "Inactivo"
                self.after(0, lambda: (self._render_clubes(),
                                       self._mostrar_toast(f"Club → {txt}")))
            except Exception as e:
                self.after(0, lambda: self._mostrar_toast(str(e), _RED))
        threading.Thread(target=_worker, daemon=True).start()

    # ── SECCIÓN 3 — SUPERVISORES ──────────────────────────────────────────────

    def _render_supervisores(self):
        self._seccion_header("Crear Supervisor", "Asigná un supervisor a un club")

        wrap = ctk.CTkFrame(self._content_frame, fg_color=_CARD, corner_radius=12,
                            border_width=1, border_color=_BORDER)
        wrap.pack(padx=28, pady=(0, 16), fill="x")
        ctk.CTkFrame(wrap, height=3, fg_color=_ACCENT2, corner_radius=0).pack(fill="x")

        form = ctk.CTkFrame(wrap, fg_color="transparent")
        form.pack(padx=24, pady=18, fill="x")

        ent_kw = {
            "fg_color": "#0D0D0D", "border_color": "#252525", "border_width": 1,
            "text_color": "#FFFFFF", "corner_radius": 8, "height": 40,
        }
        lbl_kw = {"font": ("Arial", 10, "bold"), "text_color": "#555555", "anchor": "w"}

        def campo(label, placeholder="", ancho=None):
            ctk.CTkLabel(form, text=label, **lbl_kw).grid(
                sticky="w", pady=(10, 2))
            kw = dict(ent_kw, placeholder_text=placeholder,
                      placeholder_text_color="#333333")
            if ancho:
                kw["width"] = ancho
            e = ctk.CTkEntry(form, **kw)
            e.grid(sticky="ew", ipady=0)
            return e

        form.columnconfigure(0, weight=1)
        e_nombre = campo("Nombre completo", "Ej: María García")
        e_email  = campo("Email / Usuario",  "ej: maria@club.com")
        e_pass   = ctk.CTkEntry(form, placeholder_text="Contraseña",
                                placeholder_text_color="#333333",
                                show="•", **ent_kw)
        ctk.CTkLabel(form, text="Contraseña", **lbl_kw).grid(sticky="w", pady=(10, 2))
        e_pass.grid(sticky="ew")

        # Selector de club
        ctk.CTkLabel(form, text="Club", **lbl_kw).grid(sticky="w", pady=(10, 2))

        clubs_var    = ctk.StringVar(value="Cargando...")
        clubs_map    = {}   # nombre → id
        club_menu    = ctk.CTkOptionMenu(
            form, variable=clubs_var,
            fg_color="#0D0D0D", button_color="#1C1C1C",
            button_hover_color="#2A2A2A", text_color="#FFFFFF",
            dropdown_fg_color="#111111", dropdown_hover_color="#1C1C1C",
        )
        club_menu.grid(sticky="ew", pady=(0, 4))

        def _cargar_clubs():
            try:
                from models.clubs_service import listar_todos_los_clubs
                cs = [c for c in listar_todos_los_clubs() if c["activo"]]
                for c in cs:
                    clubs_map[c["nombre"]] = c["id"]
                opciones = [c["nombre"] for c in cs] or ["(sin clubes)"]
                self.after(0, lambda: (club_menu.configure(values=opciones),
                                       clubs_var.set(opciones[0])))
            except Exception:
                self.after(0, lambda: clubs_var.set("Error"))

        threading.Thread(target=_cargar_clubs, daemon=True).start()

        lbl_err = ctk.CTkLabel(form, text="", font=("Arial", 10),
                               text_color=_RED, wraplength=400)
        lbl_err.grid(sticky="w", pady=(8, 0))

        lbl_ok = ctk.CTkLabel(form, text="", font=("Arial", 10),
                              text_color=_TEAL, wraplength=400)
        lbl_ok.grid(sticky="w")

        def _crear():
            nombre = e_nombre.get().strip()
            email  = e_email.get().strip()
            pwd    = e_pass.get()
            club_n = clubs_var.get()
            club_id = clubs_map.get(club_n)

            lbl_err.configure(text="")
            lbl_ok.configure(text="")

            if not all([nombre, email, pwd, club_id]):
                lbl_err.configure(text="Completá todos los campos.")
                return

            btn_crear.configure(state="disabled", text="Creando...")

            def _worker():
                try:
                    from models.usuarios_service import crear_usuario
                    crear_usuario(nombre=nombre, email=email, password=pwd,
                                  rol="supervisor", club_id=club_id)
                    self.after(0, lambda: (
                        lbl_ok.configure(text=f"Supervisor '{nombre}' creado."),
                        btn_crear.configure(state="normal", text="Crear supervisor"),
                        e_nombre.delete(0, "end"),
                        e_email.delete(0, "end"),
                        e_pass.delete(0, "end"),
                    ))
                except Exception as ex:
                    self.after(0, lambda: (
                        lbl_err.configure(text=str(ex)),
                        btn_crear.configure(state="normal", text="Crear supervisor"),
                    ))

            threading.Thread(target=_worker, daemon=True).start()

        btn_crear = ctk.CTkButton(
            wrap, text="Crear supervisor",
            command=_crear,
            fg_color=_ACCENT2, hover_color="#B08AFF",
            text_color="#FFFFFF", font=("Arial Black", 12, "bold"),
            corner_radius=8, height=44,
        )
        btn_crear.pack(padx=24, pady=(0, 20), fill="x")

        # Lista de supervisores existentes
        self._seccion_header("Supervisores existentes")
        lbl_carga = ctk.CTkLabel(self._content_frame, text="Cargando...",
                                 font=("Arial", 11), text_color="#444444")
        lbl_carga.pack()

        def _cargar_sup():
            try:
                from sqlalchemy import text
                from db.database import engine
                with engine.connect() as conn:
                    rows = conn.execute(text("""
                        SELECT u.id, u.nombre, u.email, u.activo, c.nombre AS club_nombre
                        FROM usuarios u
                        LEFT JOIN clubs c ON u.club_id = c.id
                        WHERE u.rol = 'supervisor'
                        ORDER BY c.nombre, u.nombre
                    """)).fetchall()
                data = [dict(r._mapping) for r in rows]
                self.after(0, lambda: self._render_tabla_supervisores(data, lbl_carga))
            except Exception as e:
                self.after(0, lambda: lbl_carga.configure(
                    text=f"Error: {e}", text_color=_RED))

        threading.Thread(target=_cargar_sup, daemon=True).start()

    def _render_tabla_supervisores(self, rows, placeholder):
        if not self._content_frame.winfo_exists():
            return
        try:
            placeholder.destroy()
        except Exception:
            pass

        sf = self._scrollable(height=260)
        cols = [("ID", 35), ("Nombre", 155), ("Email", 170),
                ("Club", 135), ("Activo", 50), ("Acciones", 145)]
        self._table_header(sf, cols)

        for i, r in enumerate(rows):
            bg  = "#181818" if i % 2 else _CARD
            row = ctk.CTkFrame(sf, fg_color=bg, corner_radius=6,
                               border_width=1, border_color=_BORDER)
            row.pack(fill="x", pady=1)

            color = _TEAL if r["activo"] else "#555555"
            for texto, w in [
                (r["id"],                        35),
                (r["nombre"],                    155),
                (r["email"],                     170),
                (r["club_nombre"] or "-",        135),
                ("Sí" if r["activo"] else "No",  50),
            ]:
                ctk.CTkLabel(row, text=str(texto), width=w,
                             font=("Arial", 10), text_color=color,
                             anchor="w").pack(side="left", padx=(10, 4), pady=6)

            acc = ctk.CTkFrame(row, fg_color="transparent")
            acc.pack(side="left", padx=4)
            uid = r["id"]
            ctk.CTkButton(
                acc, text="Editar", width=58, height=26,
                fg_color=_CARD, hover_color="#252525",
                text_color=_ACCENT, border_color=_ACCENT, border_width=1,
                corner_radius=6, font=("Arial", 9, "bold"),
                command=lambda uid=uid, rd=dict(r): self._dialog_editar_supervisor(uid, rd),
            ).pack(side="left", padx=2)
            ctk.CTkButton(
                acc, text="Eliminar", width=68, height=26,
                fg_color=_CARD, hover_color="#1A0000",
                text_color=_RED, border_color=_RED, border_width=1,
                corner_radius=6, font=("Arial", 9, "bold"),
                command=lambda uid=uid, n=r["nombre"]: self._confirmar_eliminar_supervisor(uid, n),
            ).pack(side="left", padx=2)

    def _dialog_editar_supervisor(self, usuario_id: int, datos: dict):
        dlg = ctk.CTkToplevel(self)
        dlg.title("Editar supervisor")
        dlg.configure(fg_color=_BG)
        dlg.resizable(False, False)
        dlg.grab_set()
        dlg.update_idletasks()
        w, h = 440, 460
        x = self.winfo_rootx() + (self.winfo_width()  - w) // 2
        y = self.winfo_rooty() + (self.winfo_height() - h) // 2
        dlg.geometry(f"{w}x{h}+{x}+{y}")

        ctk.CTkFrame(dlg, height=3, fg_color=_ACCENT2, corner_radius=0).pack(fill="x")
        ctk.CTkLabel(dlg, text="Editar Supervisor",
                     font=("Arial Black", 16, "bold"),
                     text_color="#FFFFFF").pack(pady=(18, 4))
        ctk.CTkFrame(dlg, height=1, fg_color="#1C1C1C",
                     corner_radius=0).pack(fill="x", padx=24, pady=(8, 16))

        sf = ctk.CTkScrollableFrame(dlg, fg_color="transparent")
        sf.pack(fill="both", expand=True, padx=24, pady=(0, 8))

        ent_kw = {
            "fg_color": "#141414", "border_color": "#252525", "border_width": 1,
            "text_color": "#FFFFFF", "corner_radius": 8, "height": 40,
        }
        lbl_kw = {"font": ("Arial", 10, "bold"), "text_color": "#555555", "anchor": "w"}

        def campo(label, default="", show=""):
            ctk.CTkLabel(sf, text=label, **lbl_kw).pack(anchor="w", pady=(8, 2))
            kw = dict(ent_kw)
            if show:
                kw["show"] = show
            e = ctk.CTkEntry(sf, **kw)
            e.pack(fill="x")
            if default:
                e.insert(0, str(default))
            return e

        e_nombre = campo("Nombre completo", datos.get("nombre", ""))
        e_email  = campo("Email / Usuario",  datos.get("email", ""))
        e_pass   = campo("Nueva contraseña (dejar vacío para no cambiar)", show="•")

        ctk.CTkLabel(sf, text="Club", **lbl_kw).pack(anchor="w", pady=(8, 2))
        clubs_var = ctk.StringVar(value=datos.get("club_nombre") or "Cargando...")
        clubs_map = {}
        club_menu = ctk.CTkOptionMenu(
            sf, variable=clubs_var,
            fg_color="#141414", button_color="#1C1C1C",
            button_hover_color="#2A2A2A", text_color="#FFFFFF",
            dropdown_fg_color="#111111", dropdown_hover_color="#1C1C1C",
        )
        club_menu.pack(fill="x", pady=(0, 4))

        def _cargar_clubs():
            try:
                from models.clubs_service import listar_todos_los_clubs
                cs = [c for c in listar_todos_los_clubs() if c["activo"]]
                for c in cs:
                    clubs_map[c["nombre"]] = c["id"]
                opciones = [c["nombre"] for c in cs] or ["(sin clubes)"]
                current  = datos.get("club_nombre") or opciones[0]
                self.after(0, lambda: (
                    club_menu.configure(values=opciones),
                    clubs_var.set(current if current in opciones else opciones[0]),
                ))
            except Exception:
                self.after(0, lambda: clubs_var.set("Error"))

        threading.Thread(target=_cargar_clubs, daemon=True).start()

        lbl_err = ctk.CTkLabel(sf, text="", font=("Arial", 10),
                               text_color=_RED, wraplength=380)
        lbl_err.pack(pady=(8, 0))

        def _guardar():
            nombre  = e_nombre.get().strip()
            email   = e_email.get().strip()
            pwd     = e_pass.get()
            club_n  = clubs_var.get()
            club_id = clubs_map.get(club_n)

            if not nombre or not email:
                lbl_err.configure(text="Nombre y email son obligatorios.")
                return

            btn_ok.configure(state="disabled", text="Guardando...")

            def _worker():
                try:
                    from models.usuarios_service import actualizar_supervisor
                    actualizar_supervisor(usuario_id, nombre, email, pwd, club_id)
                    self.after(0, lambda: (
                        dlg.destroy(),
                        self._render_supervisores(),
                        self._mostrar_toast(f"Supervisor '{nombre}' actualizado."),
                    ))
                except Exception as ex:
                    self.after(0, lambda: (
                        lbl_err.configure(text=str(ex)),
                        btn_ok.configure(state="normal", text="Guardar"),
                    ))

            threading.Thread(target=_worker, daemon=True).start()

        btn_row = ctk.CTkFrame(dlg, fg_color="transparent")
        btn_row.pack(padx=24, pady=12, fill="x")
        ctk.CTkButton(
            btn_row, text="Cancelar", command=dlg.destroy,
            fg_color=_CARD, hover_color="#1C1C1C",
            text_color="#888888", border_color=_BORDER, border_width=1,
            corner_radius=8, height=40,
        ).pack(side="left", expand=True, fill="x", padx=(0, 6))
        btn_ok = ctk.CTkButton(
            btn_row, text="Guardar", command=_guardar,
            fg_color=_ACCENT2, hover_color="#00F0FF",
            text_color="#0D0D0D", font=("Arial Black", 11, "bold"),
            corner_radius=8, height=40,
        )
        btn_ok.pack(side="left", expand=True, fill="x")

    def _confirmar_eliminar_supervisor(self, usuario_id: int, nombre: str):
        from tkinter import messagebox
        ok = messagebox.askyesno(
            "Confirmar eliminación",
            f"¿Eliminar al supervisor '{nombre}'?\nEsta acción no se puede deshacer.",
            parent=self,
        )
        if not ok:
            return

        def _worker():
            try:
                from models.usuarios_service import eliminar_supervisor
                eliminar_supervisor(usuario_id)
                self.after(0, lambda: (
                    self._render_supervisores(),
                    self._mostrar_toast(f"Supervisor '{nombre}' eliminado.", _RED),
                ))
            except Exception as e:
                self.after(0, lambda: self._mostrar_toast(str(e), _RED))

        threading.Thread(target=_worker, daemon=True).start()

    # ── SECCIÓN 3b — RESUMEN CLUBES ──────────────────────────────────────────

    def _render_resumen(self):
        self._seccion_header("Resumen por Club",
                             "Cantidad de supervisores y admins asignados a cada club")

        btn_row = ctk.CTkFrame(self._content_frame, fg_color="transparent")
        btn_row.pack(fill="x", padx=28, pady=(0, 12))
        ctk.CTkButton(
            btn_row, text="↺ Actualizar",
            command=self._render_resumen,
            fg_color=_CARD, hover_color="#1C1C1C",
            text_color="#888888", border_color=_BORDER, border_width=1,
            corner_radius=8, height=36, width=120,
        ).pack(side="left")

        lbl_carga = ctk.CTkLabel(self._content_frame, text="Cargando...",
                                 font=("Arial", 12), text_color="#444444")
        lbl_carga.pack(pady=20)

        def _cargar():
            try:
                from collections import defaultdict
                from sqlalchemy import text as sa_text
                from db.database import engine
                with engine.connect() as conn:
                    clubs_rows = conn.execute(sa_text("""
                        SELECT c.id, c.nombre, c.activo,
                               COUNT(DISTINCT CASE WHEN u.rol='supervisor' THEN u.id END) AS n_supervisores,
                               COUNT(DISTINCT CASE WHEN u.rol='admin' THEN u.id END) AS n_admins
                        FROM clubs c
                        LEFT JOIN usuarios u ON u.club_id = c.id
                        GROUP BY c.id, c.nombre, c.activo
                        ORDER BY c.nombre
                    """)).fetchall()
                    clubs_data = [dict(r._mapping) for r in clubs_rows]

                    admins_rows = conn.execute(sa_text("""
                        SELECT u.club_id, u.nombre, u.email, u.activo
                        FROM usuarios u
                        WHERE u.rol = 'admin'
                        ORDER BY u.nombre
                    """)).fetchall()
                    admins_data = [dict(r._mapping) for r in admins_rows]

                admins_by_club = defaultdict(list)
                for a in admins_data:
                    admins_by_club[a["club_id"]].append(a)

                self.after(0, lambda: self._render_resumen_datos(
                    clubs_data, admins_by_club, lbl_carga))
            except Exception as e:
                self.after(0, lambda: lbl_carga.configure(
                    text=f"Error: {e}", text_color=_RED))

        threading.Thread(target=_cargar, daemon=True).start()

    def _render_resumen_datos(self, clubs, admins_by_club, placeholder):
        if not self._content_frame.winfo_exists():
            return
        try:
            placeholder.destroy()
        except Exception:
            pass

        sf = self._scrollable()

        for club in clubs:
            club_id = club["id"]
            activo  = club["activo"]
            n_sup   = club["n_supervisores"]
            n_adm   = club["n_admins"]
            admins  = admins_by_club.get(club_id, [])

            card = ctk.CTkFrame(sf, fg_color=_CARD, corner_radius=12,
                                border_width=1, border_color=_BORDER)
            card.pack(fill="x", pady=5)

            # Cabecera
            hdr = ctk.CTkFrame(card, fg_color="transparent")
            hdr.pack(fill="x", padx=18, pady=(12, 8))

            left = ctk.CTkFrame(hdr, fg_color="transparent")
            left.pack(side="left", fill="x", expand=True)
            estado_color = _TEAL if activo else "#555555"
            ctk.CTkLabel(left, text=club["nombre"],
                         font=("Arial Black", 13, "bold"),
                         text_color="#FFFFFF").pack(anchor="w")
            ctk.CTkLabel(left, text="Activo" if activo else "Inactivo",
                         font=("Arial", 9), text_color=estado_color).pack(anchor="w")

            # Contadores
            right = ctk.CTkFrame(hdr, fg_color="transparent")
            right.pack(side="right")
            for val, lbl_txt, color in [
                (n_sup, "supervisores", _ACCENT2),
                (n_adm, "admins",       _ACCENT),
            ]:
                chip = ctk.CTkFrame(right, fg_color="#1A1A1A", corner_radius=8,
                                    border_width=1, border_color="#2A2A2A")
                chip.pack(side="left", padx=4)
                ctk.CTkLabel(chip, text=str(val),
                             font=("Arial Black", 20, "bold"),
                             text_color=color).pack(padx=18, pady=(6, 0))
                ctk.CTkLabel(chip, text=lbl_txt,
                             font=("Arial", 9), text_color="#444444").pack(padx=18, pady=(0, 6))

            # Lista de admins
            ctk.CTkFrame(card, height=1, fg_color="#1C1C1C",
                         corner_radius=0).pack(fill="x", padx=18, pady=(0, 6))
            adm_frame = ctk.CTkFrame(card, fg_color="transparent")
            adm_frame.pack(fill="x", padx=18, pady=(0, 12))

            if admins:
                ctk.CTkLabel(adm_frame, text="Admins:",
                             font=("Arial", 9, "bold"),
                             text_color="#555555").pack(anchor="w", pady=(0, 2))
                for a in admins:
                    color_a = "#CCCCCC" if a["activo"] else "#444444"
                    ctk.CTkLabel(adm_frame,
                                 text=f"  • {a['nombre']}  ({a['email']})",
                                 font=("Arial", 10), text_color=color_a,
                                 anchor="w").pack(anchor="w")
            else:
                ctk.CTkLabel(adm_frame, text="Sin admins asignados",
                             font=("Arial", 9), text_color="#333333").pack(anchor="w")

    # ── SECCIÓN 4 — FINANZAS ──────────────────────────────────────────────────

    def _render_finanzas(self):
        self._seccion_header("Finanzas del Negocio", "Pagos de mantenimiento por club")

        # Formulario registro de pago
        wrap = ctk.CTkFrame(self._content_frame, fg_color=_CARD, corner_radius=12,
                            border_width=1, border_color=_BORDER)
        wrap.pack(padx=28, pady=(0, 16), fill="x")
        ctk.CTkFrame(wrap, height=3, fg_color=_TEAL, corner_radius=0).pack(fill="x")

        form = ctk.CTkFrame(wrap, fg_color="transparent")
        form.pack(padx=24, pady=14, fill="x")
        form.columnconfigure((0, 1, 2, 3, 4), weight=1)

        ent_kw = {
            "fg_color": "#0D0D0D", "border_color": "#252525", "border_width": 1,
            "text_color": "#FFFFFF", "corner_radius": 8, "height": 38,
            "placeholder_text_color": "#333333",
        }
        lbl_kw = {"font": ("Arial", 9, "bold"), "text_color": "#555555"}

        clubs_var = ctk.StringVar(value="Cargando...")
        clubs_map = {}
        club_menu = ctk.CTkOptionMenu(
            form, variable=clubs_var,
            fg_color="#0D0D0D", button_color="#1C1C1C",
            button_hover_color="#2A2A2A", text_color="#FFFFFF",
            dropdown_fg_color="#111111",
        )
        ctk.CTkLabel(form, text="Club", **lbl_kw).grid(row=0, column=0, sticky="w", pady=(0, 4))
        club_menu.grid(row=1, column=0, sticky="ew", padx=(0, 8))

        e_monto = ctk.CTkEntry(form, placeholder_text="Monto $", **ent_kw)
        ctk.CTkLabel(form, text="Monto", **lbl_kw).grid(row=0, column=1, sticky="w", pady=(0, 4))
        e_monto.grid(row=1, column=1, sticky="ew", padx=(0, 8))

        e_periodo = ctk.CTkEntry(form, placeholder_text="Ej: Abril 2025", **ent_kw)
        ctk.CTkLabel(form, text="Período", **lbl_kw).grid(row=0, column=2, sticky="w", pady=(0, 4))
        e_periodo.grid(row=1, column=2, sticky="ew", padx=(0, 8))

        e_notas = ctk.CTkEntry(form, placeholder_text="Notas opcionales", **ent_kw)
        ctk.CTkLabel(form, text="Notas", **lbl_kw).grid(row=0, column=3, sticky="w", pady=(0, 4))
        e_notas.grid(row=1, column=3, sticky="ew", padx=(0, 8))

        def _cargar_clubs():
            try:
                from models.clubs_service import listar_todos_los_clubs
                cs = [c for c in listar_todos_los_clubs() if c["activo"]]
                for c in cs:
                    clubs_map[c["nombre"]] = c["id"]
                opciones = [c["nombre"] for c in cs] or ["(sin clubes)"]
                self.after(0, lambda: (club_menu.configure(values=opciones),
                                       clubs_var.set(opciones[0])))
            except Exception:
                pass

        threading.Thread(target=_cargar_clubs, daemon=True).start()

        lbl_pago_err = ctk.CTkLabel(wrap, text="", font=("Arial", 10), text_color=_RED)
        lbl_pago_err.pack(padx=24, pady=(0, 4))

        def _registrar():
            club_n  = clubs_var.get()
            club_id = clubs_map.get(club_n)
            try:
                monto = float(e_monto.get().replace(",", ".") or 0)
            except ValueError:
                lbl_pago_err.configure(text="Monto inválido.")
                return
            if not club_id or monto <= 0:
                lbl_pago_err.configure(text="Seleccioná un club y un monto válido.")
                return
            btn_reg.configure(state="disabled", text="Registrando...")

            def _worker():
                try:
                    from models.clubs_service import registrar_pago
                    registrar_pago(club_id, monto,
                                   e_periodo.get().strip(),
                                   e_notas.get().strip())
                    self.after(0, lambda: (
                        lbl_pago_err.configure(text=""),
                        e_monto.delete(0, "end"),
                        e_periodo.delete(0, "end"),
                        e_notas.delete(0, "end"),
                        btn_reg.configure(state="normal", text="Registrar pago"),
                        self._mostrar_toast(f"Pago registrado para {club_n}."),
                        self._refrescar_historial_pagos(),
                    ))
                except Exception as ex:
                    self.after(0, lambda: (
                        lbl_pago_err.configure(text=str(ex)),
                        btn_reg.configure(state="normal", text="Registrar pago"),
                    ))

            threading.Thread(target=_worker, daemon=True).start()

        btn_reg = ctk.CTkButton(
            wrap, text="Registrar pago",
            command=_registrar,
            fg_color=_TEAL, hover_color="#00F0A8",
            text_color="#0D0D0D", font=("Arial Black", 11, "bold"),
            corner_radius=8, height=40,
        )
        btn_reg.pack(padx=24, pady=(0, 16), fill="x")

        # Historial
        ctk.CTkLabel(self._content_frame, text="Historial de pagos",
                     font=("Arial Black", 13, "bold"),
                     text_color="#FFFFFF").pack(anchor="w", padx=28, pady=(0, 8))

        self._frame_historial_pagos = ctk.CTkFrame(
            self._content_frame, fg_color="transparent")
        self._frame_historial_pagos.pack(fill="both", expand=True, padx=28, pady=(0, 16))
        self._refrescar_historial_pagos()

    def _refrescar_historial_pagos(self):
        if not hasattr(self, "_frame_historial_pagos"):
            return

        def _cargar():
            try:
                from models.clubs_service import listar_pagos
                pagos = listar_pagos(limite=80)
                self.after(0, lambda: self._render_tabla_pagos(pagos))
            except Exception:
                pass

        threading.Thread(target=_cargar, daemon=True).start()

    def _render_tabla_pagos(self, pagos):
        if not hasattr(self, "_frame_historial_pagos") or \
                not self._frame_historial_pagos.winfo_exists():
            return
        for w in self._frame_historial_pagos.winfo_children():
            w.destroy()

        sf = ctk.CTkScrollableFrame(
            self._frame_historial_pagos, fg_color="transparent",
            scrollbar_button_color="#2A2A2A", height=250,
        )
        sf.pack(fill="both", expand=True)
        cols = [("ID", 40), ("Club", 160), ("Fecha", 90),
                ("Monto", 80), ("Período", 100), ("Notas", 200)]
        self._table_header(sf, cols)
        for i, p in enumerate(pagos):
            vals = [
                (p["id"],                  40),
                (p["club_nombre"],         160),
                (str(p["fecha_pago"])[:10], 90),
                (f"${p['monto']:,.0f}",    80),
                (p["periodo"] or "-",      100),
                (p["notas"] or "-",        200),
            ]
            self._table_row(sf, vals, color=_TEAL, alt=i % 2 == 1)

    # ── SECCIÓN 5 — LOGS ──────────────────────────────────────────────────────

    def _render_logs(self):
        self._seccion_header("Logs y Auditoría", "Historial de accesos de todos los clubes")

        # Filtros
        filtros_frame = ctk.CTkFrame(self._content_frame, fg_color=_CARD,
                                     corner_radius=10, border_width=1,
                                     border_color=_BORDER)
        filtros_frame.pack(fill="x", padx=28, pady=(0, 14))
        fi = ctk.CTkFrame(filtros_frame, fg_color="transparent")
        fi.pack(padx=18, pady=12, fill="x")
        fi.columnconfigure((0, 1, 2, 3), weight=1)

        ent_kw = {
            "fg_color": "#0D0D0D", "border_color": "#252525", "border_width": 1,
            "text_color": "#FFFFFF", "corner_radius": 8, "height": 36,
            "placeholder_text_color": "#333333",
        }

        e_accion = ctk.CTkEntry(fi, placeholder_text="Acción (login/logout...)", **ent_kw)
        ctk.CTkLabel(fi, text="Filtrar por acción",
                     font=("Arial", 9, "bold"), text_color="#555555").grid(
            row=0, column=0, sticky="w", pady=(0, 4))
        e_accion.grid(row=1, column=0, sticky="ew", padx=(0, 8))

        clubs_var_log = ctk.StringVar(value="Todos los clubes")
        clubs_map_log = {"Todos los clubes": None}
        club_menu_log = ctk.CTkOptionMenu(
            fi, variable=clubs_var_log,
            fg_color="#0D0D0D", button_color="#1C1C1C",
            button_hover_color="#2A2A2A", text_color="#FFFFFF",
            dropdown_fg_color="#111111",
        )
        ctk.CTkLabel(fi, text="Club",
                     font=("Arial", 9, "bold"), text_color="#555555").grid(
            row=0, column=1, sticky="w", pady=(0, 4))
        club_menu_log.grid(row=1, column=1, sticky="ew", padx=(0, 8))

        limite_var = ctk.StringVar(value="100")
        limite_menu = ctk.CTkOptionMenu(
            fi, variable=limite_var, values=["50", "100", "200", "500"],
            fg_color="#0D0D0D", button_color="#1C1C1C",
            button_hover_color="#2A2A2A", text_color="#FFFFFF",
            dropdown_fg_color="#111111",
        )
        ctk.CTkLabel(fi, text="Límite",
                     font=("Arial", 9, "bold"), text_color="#555555").grid(
            row=0, column=2, sticky="w", pady=(0, 4))
        limite_menu.grid(row=1, column=2, sticky="ew", padx=(0, 8))

        def _cargar_clubs_log():
            try:
                from models.clubs_service import listar_todos_los_clubs
                cs = listar_todos_los_clubs()
                for c in cs:
                    clubs_map_log[c["nombre"]] = c["id"]
                opciones = ["Todos los clubes"] + [c["nombre"] for c in cs]
                self.after(0, lambda: club_menu_log.configure(values=opciones))
            except Exception:
                pass

        threading.Thread(target=_cargar_clubs_log, daemon=True).start()

        self._frame_logs = ctk.CTkFrame(self._content_frame, fg_color="transparent")
        self._frame_logs.pack(fill="both", expand=True, padx=28, pady=(0, 16))

        def _buscar():
            accion  = e_accion.get().strip() or None
            club_id = clubs_map_log.get(clubs_var_log.get())
            limite  = int(limite_var.get())

            for w in self._frame_logs.winfo_children():
                w.destroy()
            lbl = ctk.CTkLabel(self._frame_logs, text="Buscando...",
                               font=("Arial", 11), text_color="#444444")
            lbl.pack(pady=20)

            def _worker():
                try:
                    from models.clubs_service import listar_logs_todos
                    logs = listar_logs_todos(club_id=club_id, accion=accion, limite=limite)
                    self.after(0, lambda: self._render_tabla_logs(logs, lbl))
                except Exception as e:
                    self.after(0, lambda: lbl.configure(
                        text=f"Error: {e}", text_color=_RED))

            threading.Thread(target=_worker, daemon=True).start()

        ctk.CTkButton(
            fi, text="Buscar",
            command=_buscar,
            fg_color=_ACCENT, hover_color="#9D84FF",
            text_color="#FFFFFF", font=("Arial Black", 10, "bold"),
            corner_radius=8, height=36,
        ).grid(row=1, column=3, sticky="ew")

        _buscar()

    def _render_tabla_logs(self, logs, placeholder):
        if not hasattr(self, "_frame_logs") or not self._frame_logs.winfo_exists():
            return
        try:
            placeholder.destroy()
        except Exception:
            pass

        sf = ctk.CTkScrollableFrame(
            self._frame_logs, fg_color="transparent",
            scrollbar_button_color="#2A2A2A",
        )
        sf.pack(fill="both", expand=True)
        cols = [("Timestamp", 140), ("Usuario", 120), ("Acción", 100),
                ("Club", 120), ("Detalle", 200), ("Host", 120)]
        self._table_header(sf, cols)

        _ACCION_COLOR = {
            "login":  _TEAL,
            "logout": _GOLD,
            "error":  _RED,
        }
        for i, l in enumerate(logs):
            accion  = str(l.get("accion", ""))
            color   = _ACCION_COLOR.get(accion, "#888888")
            ts      = str(l.get("timestamp", ""))[:16]
            vals = [
                (ts,                          140),
                (l.get("username", "-"),      120),
                (accion,                      100),
                (l.get("club_nombre") or "-", 120),
                (str(l.get("detalle") or "-")[:40], 200),
                (str(l.get("hostname") or "-")[:20], 120),
            ]
            self._table_row(sf, vals, color=color, alt=i % 2 == 1)

    # ── SECCIÓN 6 — OPERACIONES ───────────────────────────────────────────────

    def _render_operaciones(self):
        self._seccion_header("Operaciones", "Control avanzado por club")

        lbl_carga = ctk.CTkLabel(self._content_frame, text="Cargando clubes...",
                                 font=("Arial", 12), text_color="#444444")
        lbl_carga.pack(pady=20)

        def _cargar():
            try:
                from models.clubs_service import listar_todos_los_clubs
                clubs = listar_todos_los_clubs()
                self.after(0, lambda: self._render_ops_clubs(clubs, lbl_carga))
            except Exception as e:
                self.after(0, lambda: lbl_carga.configure(
                    text=f"Error: {e}", text_color=_RED))

        threading.Thread(target=_cargar, daemon=True).start()

    def _render_ops_clubs(self, clubs, placeholder):
        if not self._content_frame.winfo_exists():
            return
        try:
            placeholder.destroy()
        except Exception:
            pass

        sf = self._scrollable()
        for c in clubs:
            club_id   = c["id"]
            club_n    = c["nombre"]
            mant_on   = bool(c.get("modo_mantenimiento"))

            card = ctk.CTkFrame(sf, fg_color=_CARD, corner_radius=12,
                                border_width=1, border_color=_BORDER)
            card.pack(fill="x", pady=5)
            top = ctk.CTkFrame(card, fg_color="transparent")
            top.pack(fill="x", padx=18, pady=(14, 6))

            # Info
            info = ctk.CTkFrame(top, fg_color="transparent")
            info.pack(side="left", fill="x", expand=True)
            ctk.CTkLabel(info, text=f"{club_n}",
                         font=("Arial Black", 14, "bold"),
                         text_color="#FFFFFF").pack(anchor="w")
            plan_txt = c.get("plan", "-")
            ciudad   = c.get("ciudad", "-") or "-"
            activo   = "Activo" if c["activo"] else "Inactivo"
            estado_c = _TEAL if c["activo"] else _RED
            ctk.CTkLabel(info,
                         text=f"Plan {plan_txt}  ·  {ciudad}  ·  ",
                         font=("Arial", 10), text_color="#555555").pack(anchor="w")
            row_est = ctk.CTkFrame(info, fg_color="transparent")
            row_est.pack(anchor="w")
            ctk.CTkLabel(row_est, text=activo,
                         font=("Arial", 10, "bold"),
                         text_color=estado_c).pack(side="left")

            # Botones de acción
            btns = ctk.CTkFrame(top, fg_color="transparent")
            btns.pack(side="right")

            # Mantenimiento
            mant_color = _ORANGE if mant_on else "#555555"
            mant_txt   = "⚠ Desactivar mantenimiento" if mant_on else "⚠ Modo mantenimiento"
            btn_mant = ctk.CTkButton(
                btns, text=mant_txt, width=200, height=32,
                fg_color=_CARD, hover_color="#252525",
                text_color=mant_color, border_color=mant_color, border_width=1,
                corner_radius=8, font=("Arial", 9, "bold"),
                command=lambda cid=club_id: self._toggle_mantenimiento(cid),
            )
            btn_mant.pack(side="left", padx=(0, 6))

            # Exportar
            ctk.CTkButton(
                btns, text="↓ Exportar Excel", width=160, height=32,
                fg_color=_CARD, hover_color="#252525",
                text_color=_TEAL, border_color=_TEAL, border_width=1,
                corner_radius=8, font=("Arial", 9, "bold"),
                command=lambda cid=club_id, n=club_n: self._exportar_excel(cid, n),
            ).pack(side="left", padx=(0, 6))

            # Editar
            ctk.CTkButton(
                btns, text="Editar", width=80, height=32,
                fg_color=_CARD, hover_color="#252525",
                text_color=_ACCENT, border_color=_ACCENT, border_width=1,
                corner_radius=8, font=("Arial", 9, "bold"),
                command=lambda cid=club_id: self._dialog_editar_club(cid),
            ).pack(side="left")

            # Badge mantenimiento visible
            if mant_on:
                ctk.CTkLabel(card,
                             text="  MODO MANTENIMIENTO ACTIVO  ",
                             font=("Arial", 9, "bold"),
                             text_color=_ORANGE,
                             fg_color="#1A0E00",
                             corner_radius=4).pack(anchor="w", padx=18, pady=(0, 10))

    def _toggle_mantenimiento(self, club_id: int):
        def _worker():
            try:
                from models.clubs_service import toggle_mantenimiento
                nuevo = toggle_mantenimiento(club_id)
                txt = "Mantenimiento ACTIVADO" if nuevo else "Mantenimiento DESACTIVADO"
                self.after(0, lambda: (self._render_operaciones(),
                                       self._mostrar_toast(txt, _ORANGE if nuevo else _TEAL)))
            except Exception as e:
                self.after(0, lambda: self._mostrar_toast(str(e), _RED))
        threading.Thread(target=_worker, daemon=True).start()

    def _exportar_excel(self, club_id: int, club_nombre: str):
        from tkinter import filedialog
        ruta = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel", "*.xlsx")],
            initialfile=f"{club_nombre.replace(' ', '_')}_datos.xlsx",
            title="Guardar exportación",
        )
        if not ruta:
            return

        def _worker():
            from models.clubs_service import exportar_datos_club
            ok, msg = exportar_datos_club(club_id, ruta)
            if ok:
                self.after(0, lambda: self._mostrar_toast(f"Exportado: {msg}"))
            else:
                self.after(0, lambda: self._mostrar_toast(f"Error: {msg}", _RED))

        threading.Thread(target=_worker, daemon=True).start()

    # ── Cierre ────────────────────────────────────────────────────────────────

    def _cerrar_sesion(self):
        from models.logs_service import registrar_log
        usuario = SessionManager.get_usuario_actual()
        if usuario:
            registrar_log("logout", username=usuario.nombre, usuario_id=usuario.id)
        SessionManager.cerrar_sesion()
        self._volver_login()

    def _volver_login(self):
        try:
            self.master.deiconify()
        except Exception:
            pass
        self.destroy()

    def _cerrar(self):
        SessionManager.cerrar_sesion()
        self.master.quit()
