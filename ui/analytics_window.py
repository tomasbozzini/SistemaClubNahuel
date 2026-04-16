# ui/analytics_window.py
# Analítica & Reportes — exclusivo plan Enterprise.

import threading
from datetime import date, timedelta
import customtkinter as ctk
from auth.session import SessionManager
from ui.ventana_mixin import VentanaMixin, centrar_ventana

_BG     = "#0A0A0F"
_PANEL  = "#111118"
_CARD   = "#16161F"
_BORDER = "#24243A"
_VIOLET = "#7C5CFF"
_CYAN   = "#00D4FF"
_GOLD   = "#FFD700"
_RED    = "#FF5C5C"
_ORANGE = "#FF8C42"
_DIM    = "#555566"


class AnalyticsWindow(VentanaMixin, ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.withdraw()

        if not SessionManager.esta_logueado():
            self.after(0, self.destroy)
            return

        self.title("Analítica & Reportes")
        centrar_ventana(self, 980, 720)
        self.resizable(False, False)
        self.configure(fg_color=_BG)

        self._tab_actual = None
        self._tabs       = {}
        self._content    = None

        self._build_ui()
        self._seleccionar("Ocupación")
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.after(150, self._mostrar_ventana)

    # ── Layout ────────────────────────────────────────────────────────────────

    def _build_ui(self):
        ctk.CTkFrame(self, height=3, fg_color=_VIOLET, corner_radius=0).pack(fill="x")

        # Header
        hdr = ctk.CTkFrame(self, fg_color=_PANEL, corner_radius=0)
        hdr.pack(fill="x")
        inner = ctk.CTkFrame(hdr, fg_color="transparent")
        inner.pack(pady=16)
        ctk.CTkLabel(inner, text="◉", font=("Arial Black", 28), text_color=_VIOLET).pack()
        ctk.CTkLabel(inner, text="ANALÍTICA & REPORTES",
                     font=("Arial Black", 16, "bold"), text_color="#FFFFFF").pack(pady=(2, 0))
        ctk.CTkLabel(inner, text="Plan Enterprise — datos en tiempo real",
                     font=("Arial", 10), text_color=_DIM).pack()

        ctk.CTkFrame(self, height=1, fg_color="#1C1C1C", corner_radius=0).pack(fill="x")

        # Tab bar
        tab_bar = ctk.CTkFrame(self, fg_color=_PANEL, corner_radius=0)
        tab_bar.pack(fill="x")
        for nombre in ("Ocupación", "Ranking clientes", "Proyección"):
            btn = ctk.CTkButton(
                tab_bar, text=nombre,
                command=lambda n=nombre: self._seleccionar(n),
                fg_color="transparent", hover_color="#1C1C2A",
                text_color=_DIM, font=("Arial", 11),
                corner_radius=0, height=38, width=160,
                border_width=0,
            )
            btn.pack(side="left")
            self._tabs[nombre] = btn

        ctk.CTkFrame(self, height=1, fg_color="#1C1C1C", corner_radius=0).pack(fill="x")

        self._content = ctk.CTkFrame(self, fg_color=_BG, corner_radius=0)
        self._content.pack(fill="both", expand=True)

    def _seleccionar(self, nombre: str):
        if self._tab_actual:
            self._tabs[self._tab_actual].configure(
                text_color=_DIM, fg_color="transparent",
                font=("Arial", 11),
            )
        self._tab_actual = nombre
        self._tabs[nombre].configure(
            text_color=_VIOLET, fg_color="#1C1C2A",
            font=("Arial", 11, "bold"),
        )
        for w in self._content.winfo_children():
            w.destroy()
        {
            "Ocupación":        self._render_ocupacion,
            "Ranking clientes": self._render_ranking,
            "Proyección":       self._render_proyeccion,
        }[nombre]()

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _lbl_carga(self, texto="Calculando..."):
        l = ctk.CTkLabel(self._content, text=texto,
                         font=("Arial", 12), text_color=_DIM)
        l.pack(pady=40)
        return l

    def _seccion(self, titulo, subtitulo=""):
        f = ctk.CTkFrame(self._content, fg_color="transparent")
        f.pack(fill="x", padx=28, pady=(20, 6))
        ctk.CTkLabel(f, text=titulo,
                     font=("Arial Black", 17, "bold"), text_color="#FFFFFF").pack(anchor="w")
        if subtitulo:
            ctk.CTkLabel(f, text=subtitulo,
                         font=("Arial", 10), text_color=_DIM).pack(anchor="w", pady=(2, 0))
        ctk.CTkFrame(self._content, height=1, fg_color="#1C1C2A",
                     corner_radius=0).pack(fill="x", padx=28, pady=(4, 14))

    def _metric_card(self, parent, valor, label, color=_VIOLET, ancho=200):
        card = ctk.CTkFrame(parent, fg_color=_CARD, corner_radius=12,
                            border_width=1, border_color=_BORDER, width=ancho)
        card.pack(side="left", padx=6, pady=4)
        card.pack_propagate(False)
        ctk.CTkFrame(card, height=3, fg_color=color, corner_radius=0).pack(fill="x")
        ctk.CTkLabel(card, text=str(valor),
                     font=("Arial Black", 26, "bold"), text_color=color).pack(pady=(10, 0))
        ctk.CTkLabel(card, text=label,
                     font=("Arial", 10), text_color=_DIM,
                     wraplength=ancho - 16, justify="center").pack(pady=(2, 10))

    # ── TAB 1: Ocupación por cancha ───────────────────────────────────────────

    def _render_ocupacion(self):
        self._seccion("Ocupación por cancha",
                      "Porcentaje de horas reservadas vs disponibles")

        # Filtros de período
        filtros = ctk.CTkFrame(self._content, fg_color=_CARD, corner_radius=10,
                               border_width=1, border_color=_BORDER)
        filtros.pack(fill="x", padx=28, pady=(0, 14))
        fi = ctk.CTkFrame(filtros, fg_color="transparent")
        fi.pack(padx=18, pady=12)

        ctk.CTkLabel(fi, text="Período:", font=("Arial", 10, "bold"),
                     text_color=_DIM).pack(side="left", padx=(0, 8))

        periodo_var = ctk.StringVar(value="Este mes")
        for op in ("Esta semana", "Este mes", "Últimos 3 meses", "Este año"):
            ctk.CTkRadioButton(
                fi, text=op, variable=periodo_var, value=op,
                fg_color=_VIOLET, hover_color="#1C1C2A",
                text_color="#CCCCCC", font=("Arial", 10),
            ).pack(side="left", padx=8)

        self._frame_ocup = ctk.CTkFrame(self._content, fg_color="transparent")
        self._frame_ocup.pack(fill="both", expand=True, padx=28, pady=(0, 16))

        def _buscar():
            lbl = ctk.CTkLabel(self._frame_ocup, text="Calculando...",
                               font=("Arial", 12), text_color=_DIM)
            lbl.pack(pady=20)
            for w in self._frame_ocup.winfo_children():
                w.destroy()
            lbl2 = ctk.CTkLabel(self._frame_ocup, text="Calculando...",
                                font=("Arial", 12), text_color=_DIM)
            lbl2.pack(pady=20)

            desde, hasta = _periodo_a_fechas(periodo_var.get())
            threading.Thread(
                target=self._cargar_ocupacion,
                args=(desde, hasta, lbl2),
                daemon=True,
            ).start()

        ctk.CTkButton(
            fi, text="Calcular",
            command=_buscar,
            fg_color=_VIOLET, hover_color="#9D84FF",
            text_color="#FFFFFF", font=("Arial Black", 10, "bold"),
            corner_radius=8, height=32, width=100,
        ).pack(side="left", padx=(16, 0))

        _buscar()

    def _cargar_ocupacion(self, desde: date, hasta: date, placeholder):
        try:
            from sqlalchemy import text
            from db.database import engine
            club_id = SessionManager.get_club_id()

            dias = max((hasta - desde).days + 1, 1)

            with engine.connect() as conn:
                rows = conn.execute(text("""
                    SELECT c.id, c.nombre, c.tipo,
                           COALESCE(c.duracion_minutos, 60) AS duracion,
                           COUNT(r.id) AS total_reservas,
                           COALESCE(SUM(r.precio_total), 0) AS ingresos
                    FROM canchas c
                    LEFT JOIN reservas r
                        ON r.cancha_id = c.id
                        AND r.fecha BETWEEN :desde AND :hasta
                        AND r.estado = 'confirmada'
                    WHERE c.club_id = :cid
                    GROUP BY c.id, c.nombre, c.tipo, c.duracion_minutos
                    ORDER BY total_reservas DESC
                """), {"cid": club_id, "desde": desde, "hasta": hasta}).fetchall()

            # Horas disponibles: suponemos 14h/día (8:00 - 22:00)
            horas_disponibles = dias * 14
            data = []
            for r in rows:
                horas_usadas = (r.total_reservas * r.duracion) / 60
                pct = min(round(horas_usadas / horas_disponibles * 100, 1), 100)
                data.append({
                    "nombre": r.nombre,
                    "tipo":   r.tipo,
                    "reservas": int(r.total_reservas),
                    "horas":  round(horas_usadas, 1),
                    "pct":    pct,
                    "ingresos": float(r.ingresos),
                })

            self.after(0, lambda: self._render_tabla_ocupacion(data, placeholder, desde, hasta))
        except Exception as e:
            self.after(0, lambda: placeholder.configure(
                text=f"Error: {e}", text_color=_RED))

    def _render_tabla_ocupacion(self, data, placeholder, desde, hasta):
        if not self._frame_ocup.winfo_exists():
            return
        try:
            placeholder.destroy()
        except Exception:
            pass

        # Métricas resumen
        total_res  = sum(d["reservas"] for d in data)
        avg_pct    = round(sum(d["pct"] for d in data) / len(data), 1) if data else 0
        total_ing  = sum(d["ingresos"] for d in data)

        resumen = ctk.CTkFrame(self._frame_ocup, fg_color="transparent")
        resumen.pack(fill="x", pady=(0, 14))
        self._metric_card(resumen, total_res,           "Reservas en período",      _VIOLET)
        self._metric_card(resumen, f"{avg_pct}%",       "Ocupación promedio",        _CYAN)
        self._metric_card(resumen, f"${total_ing:,.0f}", "Ingresos en período",      _GOLD)
        ctk.CTkLabel(resumen,
                     text=f"Período: {desde.strftime('%d/%m/%Y')} — {hasta.strftime('%d/%m/%Y')}",
                     font=("Arial", 10), text_color=_DIM).pack(side="left", padx=16)

        # Tabla
        sf = ctk.CTkScrollableFrame(self._frame_ocup, fg_color="transparent",
                                    scrollbar_button_color="#2A2A3A")
        sf.pack(fill="both", expand=True)

        # Header
        hdr = ctk.CTkFrame(sf, fg_color="#1A1A28", corner_radius=6)
        hdr.pack(fill="x", pady=(0, 2))
        for txt, w in [("Cancha", 200), ("Tipo", 80), ("Reservas", 80),
                       ("Horas usadas", 100), ("Ocupación", 100), ("Ingresos", 100)]:
            ctk.CTkLabel(hdr, text=txt, width=w,
                         font=("Arial", 9, "bold"), text_color=_DIM,
                         anchor="w").pack(side="left", padx=(10, 4), pady=6)

        _TIPO_COLOR = {"padel": _CYAN, "futbol": _VIOLET, "tenis": _ORANGE}

        for i, d in enumerate(data):
            row = ctk.CTkFrame(sf, fg_color="#181828" if i % 2 else _CARD,
                               corner_radius=6, border_width=1, border_color=_BORDER)
            row.pack(fill="x", pady=1)

            pct_color = _GOLD if d["pct"] >= 70 else (_CYAN if d["pct"] >= 40 else _DIM)
            tipo_color = _TIPO_COLOR.get(d["tipo"], "#888888")

            vals = [
                (d["nombre"],          200, "#FFFFFF"),
                (d["tipo"].capitalize(), 80, tipo_color),
                (d["reservas"],         80, "#FFFFFF"),
                (f"{d['horas']}h",      100, "#FFFFFF"),
                (f"{d['pct']}%",        100, pct_color),
                (f"${d['ingresos']:,.0f}", 100, _GOLD),
            ]
            for txt, w, col in vals:
                ctk.CTkLabel(row, text=str(txt), width=w,
                             font=("Arial", 10), text_color=col,
                             anchor="w").pack(side="left", padx=(10, 4), pady=6)

            # Barra de ocupación visual
            bar_wrap = ctk.CTkFrame(row, fg_color="#1A1A28", corner_radius=4,
                                    width=80, height=8)
            bar_wrap.pack(side="left", padx=8)
            bar_wrap.pack_propagate(False)
            fill_w = max(int(d["pct"] / 100 * 80), 2)
            ctk.CTkFrame(bar_wrap, width=fill_w, height=8,
                         fg_color=pct_color, corner_radius=4).place(x=0, y=0)

    # ── TAB 2: Ranking de clientes ────────────────────────────────────────────

    def _render_ranking(self):
        self._seccion("Ranking de clientes",
                      "Los clientes que más reservaron, ordenados por frecuencia")

        # Filtro top N
        fi = ctk.CTkFrame(self._content, fg_color=_CARD, corner_radius=10,
                          border_width=1, border_color=_BORDER)
        fi.pack(fill="x", padx=28, pady=(0, 14))
        fila = ctk.CTkFrame(fi, fg_color="transparent")
        fila.pack(padx=18, pady=12)

        ctk.CTkLabel(fila, text="Mostrar top:", font=("Arial", 10, "bold"),
                     text_color=_DIM).pack(side="left", padx=(0, 8))
        top_var = ctk.StringVar(value="20")
        for n in ("10", "20", "50"):
            ctk.CTkRadioButton(
                fila, text=n, variable=top_var, value=n,
                fg_color=_VIOLET, hover_color="#1C1C2A",
                text_color="#CCCCCC", font=("Arial", 10),
            ).pack(side="left", padx=8)

        ctk.CTkLabel(fila, text="  Ordenar por:", font=("Arial", 10, "bold"),
                     text_color=_DIM).pack(side="left", padx=(16, 8))
        orden_var = ctk.StringVar(value="reservas")
        for txt, val in [("Reservas", "reservas"), ("Gasto total", "gasto")]:
            ctk.CTkRadioButton(
                fila, text=txt, variable=orden_var, value=val,
                fg_color=_VIOLET, hover_color="#1C1C2A",
                text_color="#CCCCCC", font=("Arial", 10),
            ).pack(side="left", padx=8)

        self._frame_rank = ctk.CTkFrame(self._content, fg_color="transparent")
        self._frame_rank.pack(fill="both", expand=True, padx=28, pady=(0, 16))

        def _buscar():
            for w in self._frame_rank.winfo_children():
                w.destroy()
            lbl = ctk.CTkLabel(self._frame_rank, text="Calculando...",
                               font=("Arial", 12), text_color=_DIM)
            lbl.pack(pady=20)
            limite = int(top_var.get())
            orden  = orden_var.get()
            threading.Thread(
                target=self._cargar_ranking,
                args=(limite, orden, lbl),
                daemon=True,
            ).start()

        ctk.CTkButton(
            fila, text="Calcular",
            command=_buscar,
            fg_color=_VIOLET, hover_color="#9D84FF",
            text_color="#FFFFFF", font=("Arial Black", 10, "bold"),
            corner_radius=8, height=32, width=100,
        ).pack(side="left", padx=(16, 0))

        _buscar()

    def _cargar_ranking(self, limite: int, orden: str, placeholder):
        try:
            from sqlalchemy import text
            from db.database import engine
            club_id = SessionManager.get_club_id()

            order_col = "total_reservas DESC" if orden == "reservas" else "total_gastado DESC"
            with engine.connect() as conn:
                rows = conn.execute(text(f"""
                    SELECT nombre_cliente,
                           telefono_cliente,
                           COUNT(*) AS total_reservas,
                           COALESCE(SUM(precio_total), 0) AS total_gastado,
                           MAX(fecha) AS ultima_visita
                    FROM reservas
                    WHERE club_id = :cid AND estado = 'confirmada'
                      AND nombre_cliente IS NOT NULL AND nombre_cliente != ''
                    GROUP BY nombre_cliente, telefono_cliente
                    ORDER BY {order_col}
                    LIMIT :lim
                """), {"cid": club_id, "lim": limite}).fetchall()

            data = [dict(r._mapping) for r in rows]
            self.after(0, lambda: self._render_tabla_ranking(data, placeholder))
        except Exception as e:
            self.after(0, lambda: placeholder.configure(
                text=f"Error: {e}", text_color=_RED))

    def _render_tabla_ranking(self, data, placeholder):
        if not self._frame_rank.winfo_exists():
            return
        try:
            placeholder.destroy()
        except Exception:
            pass

        # Métricas
        total_clientes = len(data)
        total_res      = sum(d["total_reservas"] for d in data)
        total_gasto    = sum(float(d["total_gastado"]) for d in data)

        resumen = ctk.CTkFrame(self._frame_rank, fg_color="transparent")
        resumen.pack(fill="x", pady=(0, 14))
        self._metric_card(resumen, total_clientes,         "Clientes únicos",      _VIOLET)
        self._metric_card(resumen, total_res,              "Reservas totales",     _CYAN)
        self._metric_card(resumen, f"${total_gasto:,.0f}", "Gasto total",          _GOLD)

        sf = ctk.CTkScrollableFrame(self._frame_rank, fg_color="transparent",
                                    scrollbar_button_color="#2A2A3A")
        sf.pack(fill="both", expand=True)

        hdr = ctk.CTkFrame(sf, fg_color="#1A1A28", corner_radius=6)
        hdr.pack(fill="x", pady=(0, 2))
        for txt, w in [("#", 30), ("Cliente", 220), ("Teléfono", 120),
                       ("Reservas", 80), ("Gasto total", 110), ("Última visita", 110)]:
            ctk.CTkLabel(hdr, text=txt, width=w,
                         font=("Arial", 9, "bold"), text_color=_DIM,
                         anchor="w").pack(side="left", padx=(10, 4), pady=6)

        medallas = {0: "🥇", 1: "🥈", 2: "🥉"}
        for i, d in enumerate(data):
            row = ctk.CTkFrame(sf, fg_color="#181828" if i % 2 else _CARD,
                               corner_radius=6, border_width=1, border_color=_BORDER)
            row.pack(fill="x", pady=1)

            pos_txt  = medallas.get(i, str(i + 1))
            nombre_c = _GOLD if i == 0 else (_DIM if i >= 10 else "#FFFFFF")
            ultima   = str(d["ultima_visita"])[:10] if d["ultima_visita"] else "-"

            vals = [
                (pos_txt,                    30,  _GOLD if i < 3 else _DIM),
                (d["nombre_cliente"][:26],   220, nombre_c),
                (d["telefono_cliente"] or "-", 120, _DIM),
                (int(d["total_reservas"]),   80,  _CYAN),
                (f"${float(d['total_gastado']):,.0f}", 110, _GOLD),
                (ultima,                     110, _DIM),
            ]
            for txt, w, col in vals:
                ctk.CTkLabel(row, text=str(txt), width=w,
                             font=("Arial", 10), text_color=col,
                             anchor="w").pack(side="left", padx=(10, 4), pady=6)

    # ── TAB 3: Proyección de ingresos ─────────────────────────────────────────

    def _render_proyeccion(self):
        self._seccion("Proyección de ingresos",
                      "Estimación mensual basada en el ritmo actual de reservas")

        lbl = self._lbl_carga()
        threading.Thread(target=self._cargar_proyeccion, args=(lbl,), daemon=True).start()

    def _cargar_proyeccion(self, placeholder):
        try:
            from sqlalchemy import text
            from db.database import engine
            club_id = SessionManager.get_club_id()
            hoy     = date.today()

            with engine.connect() as conn:
                # Ingresos de los últimos 30, 60, 90 días
                def _ingresos_periodo(dias):
                    desde = hoy - timedelta(days=dias)
                    return float(conn.execute(text("""
                        SELECT COALESCE(SUM(precio_total), 0)
                        FROM reservas
                        WHERE club_id = :cid AND estado = 'confirmada'
                          AND fecha BETWEEN :desde AND :hasta
                    """), {"cid": club_id, "desde": desde, "hasta": hoy}).scalar() or 0)

                ing_30  = _ingresos_periodo(30)
                ing_60  = _ingresos_periodo(60)
                ing_90  = _ingresos_periodo(90)

                # Ingreso este mes (real)
                primer_dia_mes = hoy.replace(day=1)
                ing_mes_actual = float(conn.execute(text("""
                    SELECT COALESCE(SUM(precio_total), 0)
                    FROM reservas
                    WHERE club_id = :cid AND estado = 'confirmada'
                      AND fecha BETWEEN :desde AND :hasta
                """), {"cid": club_id, "desde": primer_dia_mes, "hasta": hoy}).scalar() or 0)

                # Reservas futuras confirmadas (este mes)
                ing_futuro = float(conn.execute(text("""
                    SELECT COALESCE(SUM(precio_total), 0)
                    FROM reservas
                    WHERE club_id = :cid AND estado = 'confirmada'
                      AND fecha > :hoy
                      AND EXTRACT(MONTH FROM fecha) = EXTRACT(MONTH FROM CURRENT_DATE)
                      AND EXTRACT(YEAR  FROM fecha) = EXTRACT(YEAR  FROM CURRENT_DATE)
                """), {"cid": club_id, "hoy": hoy}).scalar() or 0)

                # Por cancha
                por_cancha = conn.execute(text("""
                    SELECT c.nombre, c.tipo,
                           COALESCE(SUM(r.precio_total), 0) AS ing_30
                    FROM canchas c
                    LEFT JOIN reservas r
                        ON r.cancha_id = c.id
                        AND r.estado = 'confirmada'
                        AND r.fecha BETWEEN :desde AND :hoy
                    WHERE c.club_id = :cid
                    GROUP BY c.id, c.nombre, c.tipo
                    ORDER BY ing_30 DESC
                """), {"cid": club_id, "desde": hoy - timedelta(days=30),
                       "hoy": hoy}).fetchall()

            data = {
                "ing_30":  ing_30,
                "ing_60":  ing_60,
                "ing_90":  ing_90,
                "ing_mes": ing_mes_actual,
                "ing_fut": ing_futuro,
                "proy_mes": ing_mes_actual + ing_futuro,
                # Proyección anual: promedio mensual (90d / 3) * 12
                "proy_anual": (ing_90 / 3) * 12,
                "por_cancha": [dict(r._mapping) for r in por_cancha],
                "hoy": hoy,
            }
            self.after(0, lambda: self._render_datos_proyeccion(data, placeholder))
        except Exception as e:
            self.after(0, lambda: placeholder.configure(
                text=f"Error: {e}", text_color=_RED))

    def _render_datos_proyeccion(self, d: dict, placeholder):
        if not self._content.winfo_exists():
            return
        try:
            placeholder.destroy()
        except Exception:
            pass

        # Todo dentro de un scrollable para que nada quede cortado
        sf = ctk.CTkScrollableFrame(self._content, fg_color="transparent",
                                    scrollbar_button_color="#2A2A3A")
        sf.pack(fill="both", expand=True, padx=0, pady=0)

        # Métricas principales
        row1 = ctk.CTkFrame(sf, fg_color="transparent")
        row1.pack(fill="x", padx=28, pady=(4, 8))
        self._metric_card(row1, f"${d['ing_30']:,.0f}",   "Ingresos últimos 30 días",  _VIOLET, 200)
        self._metric_card(row1, f"${d['ing_mes']:,.0f}",  "Real este mes (hasta hoy)", _CYAN,   200)
        self._metric_card(row1, f"${d['ing_fut']:,.0f}",  "Reservas futuras este mes", _GOLD,   200)
        self._metric_card(row1, f"${d['proy_mes']:,.0f}", "Proyección mes completo",   _ORANGE, 200)

        # Proyección anual
        proy_card = ctk.CTkFrame(sf, fg_color=_CARD, corner_radius=12,
                                 border_width=1, border_color=_BORDER)
        proy_card.pack(fill="x", padx=28, pady=(0, 16))
        ctk.CTkFrame(proy_card, height=3, fg_color=_GOLD, corner_radius=0).pack(fill="x")
        inner = ctk.CTkFrame(proy_card, fg_color="transparent")
        inner.pack(padx=24, pady=14, fill="x")
        ctk.CTkLabel(inner, text="Proyección anual (basada en últimos 90 días)",
                     font=("Arial Black", 13, "bold"), text_color="#FFFFFF").pack(anchor="w")
        ctk.CTkLabel(inner, text=f"${d['proy_anual']:,.0f}",
                     font=("Arial Black", 32, "bold"), text_color=_GOLD).pack(anchor="w", pady=(4, 0))
        prom_men = d["ing_90"] / 3
        ctk.CTkLabel(inner,
                     text=f"Promedio mensual: ${prom_men:,.0f}  ·  "
                          f"Datos al {d['hoy'].strftime('%d/%m/%Y')}",
                     font=("Arial", 10), text_color=_DIM).pack(anchor="w")

        # Tabla por cancha
        ctk.CTkLabel(sf, text="Ingresos por cancha (últimos 30 días)",
                     font=("Arial Black", 13, "bold"),
                     text_color="#FFFFFF").pack(anchor="w", padx=28, pady=(0, 8))

        tabla = ctk.CTkFrame(sf, fg_color="transparent")
        tabla.pack(fill="x", padx=28, pady=(0, 16))

        hdr = ctk.CTkFrame(tabla, fg_color="#1A1A28", corner_radius=6)
        hdr.pack(fill="x", pady=(0, 2))
        for txt, w in [("Cancha", 260), ("Tipo", 100), ("Ingresos 30d", 140), ("% del total", 160)]:
            ctk.CTkLabel(hdr, text=txt, width=w,
                         font=("Arial", 9, "bold"), text_color=_DIM,
                         anchor="w").pack(side="left", padx=(10, 4), pady=6)

        total_30 = sum(float(r["ing_30"]) for r in d["por_cancha"]) or 1
        _TIPO_COLOR = {"padel": _CYAN, "futbol": _VIOLET, "tenis": _ORANGE}

        for i, r in enumerate(d["por_cancha"]):
            fila = ctk.CTkFrame(tabla, fg_color="#181828" if i % 2 else _CARD,
                                corner_radius=6, border_width=1, border_color=_BORDER)
            fila.pack(fill="x", pady=1)
            ing       = float(r["ing_30"])
            pct       = ing / total_30 * 100
            tipo_color = _TIPO_COLOR.get(r["tipo"], "#888888")

            for txt, w, col in [
                (r["nombre"],             260, "#FFFFFF"),
                (r["tipo"].capitalize(),  100, tipo_color),
                (f"${ing:,.0f}",          140, _GOLD),
            ]:
                ctk.CTkLabel(fila, text=str(txt), width=w,
                             font=("Arial", 10), text_color=col,
                             anchor="w").pack(side="left", padx=(10, 4), pady=6)

            # Barra proporcional + porcentaje
            bar_container = ctk.CTkFrame(fila, fg_color="transparent")
            bar_container.pack(side="left", padx=8)
            bar_wrap = ctk.CTkFrame(bar_container, fg_color="#1A1A28", corner_radius=4,
                                    width=100, height=8)
            bar_wrap.pack(side="left")
            bar_wrap.pack_propagate(False)
            bar_fill = max(int(pct / 100 * 100), 2) if ing > 0 else 0
            if bar_fill:
                ctk.CTkFrame(bar_wrap, width=bar_fill, height=8,
                             fg_color=_GOLD, corner_radius=4).place(x=0, y=0)
            ctk.CTkLabel(bar_container, text=f"{pct:.1f}%",
                         font=("Arial", 9), text_color=_DIM).pack(side="left", padx=(6, 0))


# ── Helper ────────────────────────────────────────────────────────────────────

def _periodo_a_fechas(periodo: str) -> tuple[date, date]:
    hoy = date.today()
    if periodo == "Esta semana":
        desde = hoy - timedelta(days=hoy.weekday())
    elif periodo == "Este mes":
        desde = hoy.replace(day=1)
    elif periodo == "Últimos 3 meses":
        desde = hoy - timedelta(days=90)
    else:  # Este año
        desde = hoy.replace(month=1, day=1)
    return desde, hoy
