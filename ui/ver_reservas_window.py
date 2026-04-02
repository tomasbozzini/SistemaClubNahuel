# ui/ver_reservas_window.py
import customtkinter as ctk
from ui.ventana_mixin import VentanaMixin, centrar_ventana
import tkinter as tk
from tkinter import ttk, messagebox
import webbrowser
import urllib.parse
from auth.session import SessionManager
from models.reservas_service import (
    listar_reservas, eliminar_reserva,
    actualizar_estado_pago, eliminar_reservas_futuras_del_grupo,
)
from ui.export_service import exportar_excel_reservas, exportar_pdf_reservas

_COLOR_TIPO  = {"pádel": "#00C4FF", "padel": "#00C4FF",
                "fútbol": "#A3F843", "futbol": "#A3F843",
                "tenis": "#FF8C42"}
_COLOR_PAGO  = {"pendiente": "#FF5C5C", "seña": "#FFD700", "pagado": "#A3F843"}
_LABEL_PAGO  = {"pendiente": "● Pendiente", "seña": "● Seña", "pagado": "● Pagado"}


class _DialogEliminarRecurrente(ctk.CTkToplevel):
    """Diálogo para elegir cómo eliminar una reserva recurrente."""

    def __init__(self, parent):
        super().__init__(parent)
        self.result = None  # "solo" | "futuras" | None
        self.title("Reserva recurrente")
        self.resizable(False, False)
        self.configure(fg_color="#0D0D0D")
        self.transient(parent)
        self.grab_set()

        w, h = 420, 210
        x = parent.winfo_rootx() + parent.winfo_width()  // 2 - w // 2
        y = parent.winfo_rooty() + parent.winfo_height() // 2 - h // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

        ctk.CTkFrame(self, height=4, fg_color="#FF5C5C", corner_radius=0).pack(fill="x")

        ctk.CTkLabel(self, text="Esta reserva es parte de una serie recurrente.",
            font=("Arial", 11), text_color="#FFFFFF", wraplength=380).pack(pady=(18, 4))
        ctk.CTkLabel(self, text="¿Qué querés eliminar?",
            font=("Arial", 10), text_color="#888888").pack(pady=(0, 14))

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack()

        ctk.CTkButton(btn_frame, text="Solo esta fecha",
            command=lambda: self._set("solo"),
            fg_color="#1A1A1A", hover_color="#252525",
            text_color="#00C4FF", border_color="#001E2A", border_width=1,
            corner_radius=8, width=150, height=36, font=("Arial", 11, "bold"),
        ).pack(side="left", padx=6)

        ctk.CTkButton(btn_frame, text="Esta y las futuras",
            command=lambda: self._set("futuras"),
            fg_color="transparent", hover_color="#1A0000",
            text_color="#FF5C5C", border_color="#2A0000", border_width=1,
            corner_radius=8, width=160, height=36, font=("Arial", 11, "bold"),
        ).pack(side="left", padx=6)

        ctk.CTkButton(self, text="Cancelar", command=self.destroy,
            fg_color="transparent", hover_color="#161616",
            text_color="#444444", corner_radius=8, width=80, height=28,
        ).pack(pady=(14, 0))

        self.wait_window()

    def _set(self, val):
        self.result = val
        self.destroy()


class VerReservasWindow(VentanaMixin, ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.withdraw()

        if not SessionManager.esta_logueado():
            self.after(0, self.destroy)
            return

        self.title("Ver Reservas")
        self.update_idletasks()
        centrar_ventana(self, 1160, 560)
        self.transient(parent)
        self.configure(fg_color="#0D0D0D")

        # Barra de acento
        ctk.CTkFrame(self, height=4, fg_color="#00C4FF", corner_radius=0).pack(fill="x")

        # Header
        hdr = ctk.CTkFrame(self, fg_color="#111111", corner_radius=0)
        hdr.pack(fill="x")
        hdr_inner = ctk.CTkFrame(hdr, fg_color="transparent")
        hdr_inner.pack(fill="x", padx=28, pady=(14, 12))

        ctk.CTkLabel(hdr_inner, text="VER RESERVAS",
            font=("Arial Black", 20, "bold"), text_color="#FFFFFF").pack(side="left")
        self.lbl_count = ctk.CTkLabel(hdr_inner, text="",
            font=("Arial", 11), text_color="#2A2A2A")
        self.lbl_count.pack(side="left", padx=(12, 0))

        right_hdr = ctk.CTkFrame(hdr_inner, fg_color="transparent")
        right_hdr.pack(side="right")

        self.btn_orden = ctk.CTkButton(right_hdr, text="Ordenar por deporte",
            command=self._toggle_orden,
            fg_color="transparent", hover_color="#1A1A2A",
            text_color="#00C4FF", border_color="#001E2A", border_width=1,
            corner_radius=8, height=28, width=160, font=("Arial", 10))
        self.btn_orden.pack(side="left", padx=(0, 16))

        leyenda = ctk.CTkFrame(right_hdr, fg_color="transparent")
        leyenda.pack(side="left")
        for label, color in [("Pádel", "#00C4FF"), ("Fútbol", "#A3F843"), ("Tenis", "#FF8C42")]:
            ctk.CTkLabel(leyenda, text="● ", font=("Arial", 10), text_color=color).pack(side="left")
            ctk.CTkLabel(leyenda, text=label + "  ", font=("Arial", 10),
                text_color="#444444").pack(side="left")

        ctk.CTkFrame(self, height=1, fg_color="#1C1C1C", corner_radius=0).pack(fill="x")

        # Tabla
        card = ctk.CTkFrame(self, fg_color="#141414", corner_radius=0)
        card.pack(padx=0, pady=0, fill="both", expand=True)

        self._aplicar_estilo_tree()

        tree_frame = ctk.CTkFrame(card, fg_color="transparent")
        tree_frame.pack(fill="both", expand=True, padx=16, pady=(16, 0))

        cols = ("ID", "Cliente", "Celular", "Cancha", "Tipo", "Fecha", "Hora", "Pago", "Notas")
        self.tree = ttk.Treeview(tree_frame, columns=cols, show="headings",
            style="Club.Treeview")
        widths = {"ID": 42, "Cliente": 148, "Celular": 112, "Cancha": 120, "Tipo": 70,
                  "Fecha": 90, "Hora": 58, "Pago": 100, "Notas": 190}
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=widths.get(c, 100), anchor="center")

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview,
            style="Club.Vertical.TScrollbar")
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Tags por tipo de cancha
        self.tree.tag_configure("padel",  foreground="#00C4FF")
        self.tree.tag_configure("futbol", foreground="#A3F843")
        self.tree.tag_configure("tenis",  foreground="#FF8C42")

        # Barra inferior de acciones
        ctk.CTkFrame(card, height=1, fg_color="#1C1C1C", corner_radius=0).pack(
            fill="x", pady=(10, 0))

        barra_top = ctk.CTkFrame(card, fg_color="transparent")
        barra_top.pack(fill="x")

        ctk.CTkButton(barra_top, text="⬇ EXCEL",
            command=self._exportar_excel,
            fg_color="transparent", hover_color="#0A1A0A",
            text_color="#A3F843", border_color="#1A2A1A", border_width=1,
            corner_radius=0, height=38, width=110, font=("Arial", 11, "bold"),
        ).pack(side="left")

        ctk.CTkButton(barra_top, text="⬇ PDF",
            command=self._exportar_pdf,
            fg_color="transparent", hover_color="#0A0A1A",
            text_color="#00C4FF", border_color="#0A1A2A", border_width=1,
            corner_radius=0, height=38, width=100, font=("Arial", 11, "bold"),
        ).pack(side="left")

        ctk.CTkButton(barra_top, text="CAMBIAR PAGO",
            command=self._cambiar_estado_pago,
            fg_color="transparent", hover_color="#1A1A00",
            text_color="#FFD700", border_color="#2A2A00", border_width=1,
            corner_radius=0, height=38, width=140, font=("Arial", 11, "bold"),
        ).pack(side="left")

        ctk.CTkButton(barra_top, text="📱 RECORDATORIO",
            command=lambda: self._whatsapp("recordatorio"),
            fg_color="transparent", hover_color="#001A00",
            text_color="#A3F843", border_color="#0A1A0A", border_width=1,
            corner_radius=0, height=38, width=160, font=("Arial", 10, "bold"),
        ).pack(side="left")

        ctk.CTkButton(barra_top, text="📱 CANCELACIÓN",
            command=lambda: self._whatsapp("cancelacion"),
            fg_color="transparent", hover_color="#1A0A00",
            text_color="#FF8C42", border_color="#2A1A00", border_width=1,
            corner_radius=0, height=38, width=150, font=("Arial", 10, "bold"),
        ).pack(side="left")

        ctk.CTkButton(barra_top, text="ELIMINAR RESERVA",
            command=self.eliminar_reserva_seleccionada,
            fg_color="transparent", hover_color="#1A0000",
            text_color="#FF5C5C", border_color="#2A0000", border_width=1,
            corner_radius=0, height=38, font=("Arial", 11, "bold"),
        ).pack(side="right", fill="x", expand=True)

        self._orden_deporte = False
        self.cargar_reservas()
        self.after(150, self._mostrar_ventana)

    def _aplicar_estilo_tree(self):
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Club.Treeview",
            background="#141414", foreground="#888888",
            fieldbackground="#141414", rowheight=34, borderwidth=0,
            font=("Arial", 11))
        style.configure("Club.Treeview.Heading",
            background="#1A1A1A", foreground="#555555",
            font=("Arial", 10, "bold"), relief="flat")
        style.map("Club.Treeview",
            background=[("selected", "#1E1E1E")],
            foreground=[("selected", "#FFFFFF")])
        style.map("Club.Treeview.Heading",
            background=[("active", "#222222"), ("!active", "#1A1A1A")])
        style.configure("Club.Vertical.TScrollbar",
            background="#1C1C1C", troughcolor="#141414",
            arrowcolor="#333333", borderwidth=0)

    def _toggle_orden(self):
        self._orden_deporte = not self._orden_deporte
        self.btn_orden.configure(
            text="Ordenar por fecha" if self._orden_deporte else "Ordenar por deporte"
        )
        self.cargar_reservas()

    def cargar_reservas(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        self._filas = listar_reservas()
        filas = self._filas
        if self._orden_deporte:
            filas = sorted(filas, key=lambda f: (f[3].lower(), f[4], f[5]))
        for f in filas:
            # f: (id[0], cliente[1], cancha[2], tipo[3], fecha[4], hora[5],
            #     notas[6], telefono[7], estado_pago[8], grupo_recurrente_id[9], total_serie[10])
            tipo_raw  = f[3].lower().replace("á", "a").replace("ú", "u")
            tag       = tipo_raw if tipo_raw in ("padel", "futbol", "tenis") else ""
            pago_text = _LABEL_PAGO.get(f[8], f[8])
            total_serie = f[10] if len(f) > 10 else 0
            if total_serie > 1:
                notas_text = f"↺ {total_serie} fechas" + (f"  |  {f[6]}" if f[6] else "")
            else:
                notas_text = f[6]
            display = (
                f[0], f[1], f[7], f[2], f[3], f[4], f[5],
                pago_text,
                notas_text,
            )
            self.tree.insert("", tk.END, values=display, tags=(tag,))
        n = len(filas)
        self.lbl_count.configure(text=f"{n} turno{'s' if n != 1 else ''}")

    def _fila_seleccionada(self):
        """Retorna la fila de datos completa del item seleccionado, o None."""
        sel = self.tree.selection()
        if not sel:
            return None
        reserva_id = int(self.tree.item(sel[0])["values"][0])
        return next((f for f in self._filas if f[0] == reserva_id), None)

    def _exportar_excel(self):
        exportar_excel_reservas(getattr(self, "_filas", []))

    def _exportar_pdf(self):
        exportar_pdf_reservas(getattr(self, "_filas", []))

    # ── Pago ─────────────────────────────────────────────────────────────────

    def _cambiar_estado_pago(self):
        fila = self._fila_seleccionada()
        if not fila:
            messagebox.showwarning("Atención", "Seleccioná una reserva.")
            return

        reserva_id    = fila[0]
        estado_actual = fila[8]

        # Diálogo simple con 3 opciones
        dlg = ctk.CTkToplevel(self)
        dlg.title("Estado de pago")
        dlg.resizable(False, False)
        dlg.configure(fg_color="#0D0D0D")
        dlg.transient(self)
        dlg.grab_set()
        w, h = 360, 220
        x = self.winfo_rootx() + self.winfo_width()  // 2 - w // 2
        y = self.winfo_rooty() + self.winfo_height() // 2 - h // 2
        dlg.geometry(f"{w}x{h}+{x}+{y}")

        ctk.CTkFrame(dlg, height=4, fg_color="#FFD700", corner_radius=0).pack(fill="x")
        ctk.CTkLabel(dlg, text="ESTADO DE PAGO",
            font=("Arial Black", 14, "bold"), text_color="#FFFFFF").pack(pady=(16, 4))
        ctk.CTkLabel(dlg, text=f"Reserva #{reserva_id} — {fila[1]}",
            font=("Arial", 10), text_color="#555555").pack(pady=(0, 14))

        btn_kw = {"corner_radius": 8, "width": 120, "height": 36,
                  "fg_color": "transparent", "border_width": 1}

        fila_btns = ctk.CTkFrame(dlg, fg_color="transparent")
        fila_btns.pack()

        for estado, color in [("pendiente", "#FF5C5C"), ("seña", "#FFD700"), ("pagado", "#A3F843")]:
            bold = "bold" if estado == estado_actual else "normal"
            ctk.CTkButton(fila_btns,
                text=estado.capitalize(),
                command=lambda e=estado, d=dlg: self._aplicar_pago(reserva_id, e, d),
                text_color=color, hover_color="#1A1A1A",
                border_color=color,
                font=("Arial", 11, bold),
                **btn_kw,
            ).pack(side="left", padx=5)

        ctk.CTkButton(dlg, text="Cancelar", command=dlg.destroy,
            fg_color="transparent", text_color="#444444",
            corner_radius=8, width=80, height=28,
        ).pack(pady=(12, 0))

    def _aplicar_pago(self, reserva_id, estado, dlg):
        actualizar_estado_pago(reserva_id, estado)
        dlg.destroy()
        self.cargar_reservas()

    # ── WhatsApp ──────────────────────────────────────────────────────────────

    def _whatsapp(self, tipo: str):
        fila = self._fila_seleccionada()
        if not fila:
            messagebox.showwarning("Atención", "Seleccioná una reserva.")
            return

        nombre  = fila[1]
        celular = fila[7]
        cancha  = fila[2]
        fecha   = fila[4]
        hora    = fila[5]

        if not celular or str(celular).strip() in ("", "-", "None"):
            messagebox.showwarning("Sin celular",
                "La reserva no tiene celular registrado.")
            return

        telefono = str(celular).replace("-", "").replace(" ", "").replace("+", "")
        if not telefono.startswith("54"):
            telefono = "549" + telefono.lstrip("0")

        if tipo == "recordatorio":
            msg = (
                f"Hola {nombre}! Te recordamos tu reserva en {cancha} "
                f"el {fecha} a las {hora} hs. ¡Te esperamos!"
            )
        else:
            msg = (
                f"Hola {nombre}, te informamos que tu reserva en {cancha} "
                f"el {fecha} a las {hora} hs fue cancelada. "
                f"Disculpá las molestias."
            )

        url = f"https://wa.me/{telefono}?text={urllib.parse.quote(msg)}"
        webbrowser.open(url)

    # ── Eliminar ──────────────────────────────────────────────────────────────

    def eliminar_reserva_seleccionada(self):
        fila = self._fila_seleccionada()
        if not fila:
            messagebox.showwarning("Atención", "Seleccioná una reserva para eliminar.")
            return

        reserva_id  = fila[0]
        grupo_id    = fila[9]
        fecha_reserva = fila[4]

        if grupo_id:
            dlg = _DialogEliminarRecurrente(self)
            if dlg.result is None:
                return
            if dlg.result == "futuras":
                if messagebox.askyesno("Confirmar",
                    f"¿Eliminar la reserva #{reserva_id} y todas las futuras de la serie?"):
                    eliminar_reservas_futuras_del_grupo(grupo_id, fecha_reserva)
                    self.cargar_reservas()
            else:
                if messagebox.askyesno("Confirmar", f"¿Eliminar solo la reserva #{reserva_id}?"):
                    eliminar_reserva(reserva_id)
                    self.cargar_reservas()
        else:
            if messagebox.askyesno("Confirmar", f"¿Eliminar la reserva #{reserva_id}?"):
                eliminar_reserva(reserva_id)
                self.cargar_reservas()
