# ui/ver_reservas_window.py
import customtkinter as ctk
from ui.ventana_mixin import VentanaMixin
import tkinter as tk
from tkinter import ttk, messagebox
from auth.session import SessionManager
from models.reservas_service import listar_reservas, eliminar_reserva

_COLOR_TIPO = {"pádel": "#00C4FF", "padel": "#00C4FF",
               "fútbol": "#A3F843", "futbol": "#A3F843",
               "tenis": "#FF8C42"}


class VerReservasWindow(VentanaMixin, ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.withdraw()

        if not SessionManager.esta_logueado():
            self.after(0, self.destroy)
            return

        self.title("Ver Reservas")
        width, height = 900, 520
        self.geometry(f"{width}x{height}")
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (width  // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")
        self.transient(parent)
        self.configure(fg_color="#0D0D0D")

        # Barra de acento cyan (color de "ver")
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

        # Leyenda de colores + botón ordenar
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

        cols = ("ID", "Cliente", "Cancha", "Tipo", "Fecha", "Hora", "Notas")
        self.tree = ttk.Treeview(tree_frame, columns=cols, show="headings",
            style="Club.Treeview")
        widths = {"ID": 42, "Cliente": 165, "Cancha": 145, "Tipo": 80,
                  "Fecha": 100, "Hora": 64, "Notas": 210}
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

        # Botón eliminar
        ctk.CTkFrame(card, height=1, fg_color="#1C1C1C", corner_radius=0).pack(
            fill="x", pady=(10, 0))
        ctk.CTkButton(card, text="ELIMINAR RESERVA SELECCIONADA",
            command=self.eliminar_reserva_seleccionada,
            fg_color="transparent", hover_color="#1A0000",
            text_color="#FF5C5C", border_color="#2A0000", border_width=1,
            corner_radius=0, height=40, font=("Arial", 11, "bold")
        ).pack(fill="x")

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
        filas = listar_reservas()
        if self._orden_deporte:
            filas = sorted(filas, key=lambda f: (f[3].lower(), f[4], f[5]))
        for f in filas:
            tipo_raw = f[3].lower().replace("á", "a").replace("ú", "u")
            tag = tipo_raw if tipo_raw in ("padel", "futbol", "tenis") else ""
            self.tree.insert("", tk.END, values=f, tags=(tag,))
        n = len(filas)
        self.lbl_count.configure(text=f"{n} turno{'s' if n != 1 else ''}")

    def eliminar_reserva_seleccionada(self):
        seleccion = self.tree.selection()
        if not seleccion:
            messagebox.showwarning("Atención", "Seleccioná una reserva para eliminar.")
            return
        reserva_id = self.tree.item(seleccion[0])["values"][0]
        if messagebox.askyesno("Confirmar", f"¿Eliminar la reserva #{reserva_id}?"):
            eliminar_reserva(reserva_id)
            self.cargar_reservas()
