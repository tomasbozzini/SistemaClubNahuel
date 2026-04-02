# ui/gestionar_canchas_window.py
import customtkinter as ctk
from ui.ventana_mixin import VentanaMixin, centrar_ventana
from tkcalendar import DateEntry
from tkinter import ttk, messagebox
from auth.session import SessionManager
from models.canchas_service import (
    listar_canchas_con_precio, insertar_cancha, eliminar_cancha,
    existe_cancha, actualizar_duracion_cancha,
)
from models.bloqueos_service import (
    listar_bloqueos_futuros, insertar_bloqueo, eliminar_bloqueo,
    reservas_afectadas_por_bloqueo,
)
from utils.validaciones import sanitizar_texto

_TIPOS_VALIDOS   = {"Fútbol", "Pádel", "Tenis"}
_DURACION_DEFAULT = {"Fútbol": 60, "Pádel": 90, "Tenis": 60}
_DURACIONES       = ["30", "45", "60", "75", "90", "120"]


class GestionarCanchasWindow(VentanaMixin, ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.withdraw()

        if not SessionManager.esta_logueado():
            self.after(0, self.destroy)
            return

        self.title("Gestionar Canchas")
        self.update_idletasks()
        centrar_ventana(self, 780, 860)
        self.transient(parent)
        self.resizable(False, False)
        self.configure(fg_color="#0D0D0D")

        self._cancha_sel_id = None

        ctk.CTkFrame(self, height=4, fg_color="#FF8C42", corner_radius=0).pack(fill="x")

        hdr = ctk.CTkFrame(self, fg_color="#111111", corner_radius=0)
        hdr.pack(fill="x")
        ctk.CTkLabel(hdr, text="GESTIONAR CANCHAS",
            font=("Arial Black", 20, "bold"), text_color="#FFFFFF").pack(
            anchor="w", padx=28, pady=(16, 2))
        ctk.CTkLabel(hdr, text="Agregá, eliminá o modificá las canchas y sus bloqueos",
            font=("Arial", 11), text_color="#FF8C42").pack(anchor="w", padx=28, pady=(0, 14))

        ctk.CTkFrame(self, height=1, fg_color="#1C1C1C", corner_radius=0).pack(fill="x")

        # ── Formulario agregar ────────────────────────────────────────────────
        form_card = ctk.CTkFrame(self, fg_color="#141414", corner_radius=0)
        form_card.pack(fill="x")

        fila = ctk.CTkFrame(form_card, fg_color="transparent")
        fila.pack(padx=24, pady=16, fill="x")

        lbl_kw   = {"font": ("Arial", 10, "bold"), "text_color": "#555555", "anchor": "w"}
        combo_kw = dict(fg_color="#1A1A1A", border_color="#252525", border_width=1,
            text_color="#FFFFFF", button_color="#252525", button_hover_color="#FF8C42",
            dropdown_fg_color="#1A1A1A", dropdown_text_color="#FFFFFF",
            corner_radius=10, height=40)

        col_nombre = ctk.CTkFrame(fila, fg_color="transparent")
        col_nombre.pack(side="left", expand=True, fill="x", padx=(0, 10))
        ctk.CTkLabel(col_nombre, text="NOMBRE", **lbl_kw).pack(anchor="w", pady=(0, 4))
        self.entry_nombre = ctk.CTkEntry(col_nombre, placeholder_text="Ej: Pádel 3",
            fg_color="#1A1A1A", border_color="#252525", border_width=1,
            text_color="#FFFFFF", corner_radius=10, height=40)
        self.entry_nombre.pack(fill="x")

        col_tipo = ctk.CTkFrame(fila, fg_color="transparent")
        col_tipo.pack(side="left", expand=False, fill="x", padx=(0, 10))
        ctk.CTkLabel(col_tipo, text="TIPO", **lbl_kw).pack(anchor="w", pady=(0, 4))
        self.combo_tipo = ctk.CTkComboBox(col_tipo, values=["Fútbol", "Pádel", "Tenis"],
            width=140, command=self._on_tipo_change, **combo_kw)
        self.combo_tipo.set("Pádel")
        self.combo_tipo.pack(fill="x")

        col_dur = ctk.CTkFrame(fila, fg_color="transparent")
        col_dur.pack(side="left", expand=False, fill="x", padx=(0, 10))
        ctk.CTkLabel(col_dur, text="DURACIÓN (min)", **lbl_kw).pack(anchor="w", pady=(0, 4))
        self.combo_dur = ctk.CTkComboBox(col_dur, values=_DURACIONES, width=120, **combo_kw)
        self.combo_dur.set("90")
        self.combo_dur.pack(fill="x")

        ctk.CTkButton(fila, text="+ AGREGAR", command=self.agregar_cancha,
            fg_color="#FF8C42", hover_color="#FFA066", text_color="#0D0D0D",
            font=("Arial Black", 12, "bold"), corner_radius=10, width=110, height=40
        ).pack(side="left", anchor="s")

        ctk.CTkFrame(self, height=1, fg_color="#1C1C1C", corner_radius=0).pack(fill="x")

        # ── Editar duración de cancha seleccionada ────────────────────────────
        self._edit_card = ctk.CTkFrame(self, fg_color="#111111", corner_radius=0)
        self._edit_card.pack(fill="x")

        edit_row = ctk.CTkFrame(self._edit_card, fg_color="transparent")
        edit_row.pack(padx=24, pady=12, fill="x")

        self._lbl_sel = ctk.CTkLabel(edit_row,
            text="Seleccioná una cancha de la lista para editar su duración",
            font=("Arial", 10), text_color="#333333", anchor="w")
        self._lbl_sel.pack(side="left", expand=True, fill="x")

        self._combo_dur_edit = ctk.CTkComboBox(edit_row, values=_DURACIONES,
            width=120, **combo_kw)
        self._combo_dur_edit.pack(side="left", padx=(10, 8))
        self._combo_dur_edit.set("60")

        self._btn_actualizar = ctk.CTkButton(edit_row, text="ACTUALIZAR DURACIÓN",
            command=self._actualizar_duracion,
            fg_color="transparent", hover_color="#1A1A00",
            text_color="#FFD700", border_color="#2A2A00", border_width=1,
            corner_radius=10, width=180, height=36,
            font=("Arial", 11, "bold"),
            state="disabled",
        )
        self._btn_actualizar.pack(side="left")

        ctk.CTkFrame(self, height=1, fg_color="#1C1C1C", corner_radius=0).pack(fill="x")

        # ── Lista de canchas ──────────────────────────────────────────────────
        list_card = ctk.CTkFrame(self, fg_color="#0F0F0F", corner_radius=0)
        list_card.pack(fill="x")

        ctk.CTkLabel(list_card, text="CANCHAS REGISTRADAS",
            font=("Arial", 10, "bold"), text_color="#333333").pack(
            anchor="w", padx=24, pady=(12, 6))

        self._aplicar_estilo_tree()

        tree_frame = ctk.CTkFrame(list_card, fg_color="transparent")
        tree_frame.pack(fill="x", padx=14)

        cols = ("ID", "Nombre", "Tipo", "Duración (min)")
        self.tree = ttk.Treeview(tree_frame, columns=cols, show="headings",
            style="Club.Treeview", height=5)
        widths = {"ID": 50, "Nombre": 300, "Tipo": 160, "Duración (min)": 120}
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=widths.get(c, 100), anchor="center")

        scrollbar_c = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview,
            style="Club.Vertical.TScrollbar")
        self.tree.configure(yscrollcommand=scrollbar_c.set)
        self.tree.pack(side="left", fill="x", expand=True)
        scrollbar_c.pack(side="right", fill="y")

        self.tree.tag_configure("padel",  foreground="#00C4FF")
        self.tree.tag_configure("futbol", foreground="#A3F843")
        self.tree.tag_configure("tenis",  foreground="#FF8C42")
        self.tree.bind("<<TreeviewSelect>>", self._on_seleccion)

        ctk.CTkFrame(list_card, height=1, fg_color="#1C1C1C", corner_radius=0).pack(
            fill="x", pady=(8, 0))
        ctk.CTkButton(list_card, text="ELIMINAR CANCHA SELECCIONADA",
            command=self.eliminar_cancha,
            fg_color="transparent", hover_color="#1A0000",
            text_color="#FF5C5C", border_color="#2A0000", border_width=1,
            corner_radius=0, height=36, font=("Arial", 11, "bold")
        ).pack(fill="x")

        ctk.CTkFrame(self, height=1, fg_color="#1C1C1C", corner_radius=0).pack(fill="x")

        # ── Sección Bloqueos ──────────────────────────────────────────────────
        bloqueo_hdr = ctk.CTkFrame(self, fg_color="#111111", corner_radius=0)
        bloqueo_hdr.pack(fill="x")
        ctk.CTkLabel(bloqueo_hdr, text="BLOQUEOS POR MANTENIMIENTO",
            font=("Arial", 11, "bold"), text_color="#FF5C5C").pack(
            anchor="w", padx=24, pady=(10, 10))

        bloqueo_form = ctk.CTkFrame(self, fg_color="#141414", corner_radius=0)
        bloqueo_form.pack(fill="x")

        bfila = ctk.CTkFrame(bloqueo_form, fg_color="transparent")
        bfila.pack(padx=24, pady=14, fill="x")

        # Selector de cancha para bloqueo
        col_bcancha = ctk.CTkFrame(bfila, fg_color="transparent")
        col_bcancha.pack(side="left", expand=True, fill="x", padx=(0, 10))
        ctk.CTkLabel(col_bcancha, text="CANCHA", **lbl_kw).pack(anchor="w", pady=(0, 4))
        self._canchas_cache = []
        self.combo_bloqueo_cancha = ctk.CTkComboBox(col_bcancha, values=[""],
            **{**combo_kw, "width": 200})
        self.combo_bloqueo_cancha.pack(fill="x")

        date_kw = dict(
            background="#1A1A1A", foreground="white", borderwidth=0,
            headersbackground="#0D0D0D", headersforeground="#FF5C5C",
            selectbackground="#FF5C5C", selectforeground="black",
            normalbackground="#1A1A1A", normalforeground="white",
            weekendbackground="#1A1A1A", weekendforeground="#FF5C5C",
            font=("Arial", 10),
        )

        col_bdesde = ctk.CTkFrame(bfila, fg_color="transparent")
        col_bdesde.pack(side="left", expand=False, fill="x", padx=(0, 10))
        ctk.CTkLabel(col_bdesde, text="DESDE", **lbl_kw).pack(anchor="w", pady=(0, 4))
        self.date_bloqueo_desde = DateEntry(col_bdesde, date_pattern="yyyy-mm-dd",
            width=11, **date_kw)
        self.date_bloqueo_desde.pack(anchor="w", ipady=5)

        col_bhasta = ctk.CTkFrame(bfila, fg_color="transparent")
        col_bhasta.pack(side="left", expand=False, fill="x", padx=(0, 10))
        ctk.CTkLabel(col_bhasta, text="HASTA", **lbl_kw).pack(anchor="w", pady=(0, 4))
        self.date_bloqueo_hasta = DateEntry(col_bhasta, date_pattern="yyyy-mm-dd",
            width=11, **date_kw)
        self.date_bloqueo_hasta.pack(anchor="w", ipady=5)

        col_bmotivo = ctk.CTkFrame(bfila, fg_color="transparent")
        col_bmotivo.pack(side="left", expand=True, fill="x", padx=(0, 10))
        ctk.CTkLabel(col_bmotivo, text="MOTIVO", **lbl_kw).pack(anchor="w", pady=(0, 4))
        self.entry_motivo = ctk.CTkEntry(col_bmotivo, placeholder_text="Ej: Pintura",
            fg_color="#1A1A1A", border_color="#252525", border_width=1,
            text_color="#FFFFFF", corner_radius=10, height=38)
        self.entry_motivo.pack(fill="x")

        ctk.CTkButton(bfila, text="BLOQUEAR", command=self._agregar_bloqueo,
            fg_color="#FF5C5C", hover_color="#FF7A7A", text_color="#0D0D0D",
            font=("Arial Black", 11, "bold"), corner_radius=10, width=100, height=38,
        ).pack(side="left", anchor="s")

        ctk.CTkFrame(self, height=1, fg_color="#1C1C1C", corner_radius=0).pack(fill="x")

        # Lista de bloqueos
        blist_card = ctk.CTkFrame(self, fg_color="#0F0F0F", corner_radius=0)
        blist_card.pack(fill="both", expand=True)

        ctk.CTkLabel(blist_card, text="BLOQUEOS ACTIVOS Y FUTUROS",
            font=("Arial", 10, "bold"), text_color="#333333").pack(
            anchor="w", padx=24, pady=(12, 6))

        btree_frame = ctk.CTkFrame(blist_card, fg_color="transparent")
        btree_frame.pack(fill="both", expand=True, padx=14)

        bcols = ("ID", "Cancha", "Desde", "Hasta", "Motivo")
        self.btree = ttk.Treeview(btree_frame, columns=bcols, show="headings",
            style="Club.Treeview", height=4)
        bwidths = {"ID": 50, "Cancha": 230, "Desde": 110, "Hasta": 110, "Motivo": 240}
        for c in bcols:
            self.btree.heading(c, text=c)
            self.btree.column(c, width=bwidths.get(c, 100), anchor="center")

        scrollbar_b = ttk.Scrollbar(btree_frame, orient="vertical", command=self.btree.yview,
            style="Club.Vertical.TScrollbar")
        self.btree.configure(yscrollcommand=scrollbar_b.set)
        self.btree.pack(side="left", fill="both", expand=True)
        scrollbar_b.pack(side="right", fill="y")

        ctk.CTkFrame(blist_card, height=1, fg_color="#1C1C1C", corner_radius=0).pack(
            fill="x", pady=(8, 0))
        ctk.CTkButton(blist_card, text="QUITAR BLOQUEO SELECCIONADO",
            command=self._quitar_bloqueo,
            fg_color="transparent", hover_color="#1A0000",
            text_color="#FF5C5C", border_color="#2A0000", border_width=1,
            corner_radius=0, height=36, font=("Arial", 11, "bold"),
        ).pack(fill="x")

        self.cargar_canchas()
        self._cargar_bloqueos()
        self.after(150, self._mostrar_ventana)

    # ── Estilos ───────────────────────────────────────────────────────────────

    def _aplicar_estilo_tree(self):
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Club.Treeview",
            background="#0F0F0F", foreground="#888888",
            fieldbackground="#0F0F0F", rowheight=32, borderwidth=0,
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

    # ── Canchas ───────────────────────────────────────────────────────────────

    def _on_tipo_change(self, valor: str):
        self.combo_dur.set(str(_DURACION_DEFAULT.get(valor, 60)))

    def _on_seleccion(self, _event):
        sel = self.tree.selection()
        if not sel:
            self._cancha_sel_id = None
            self._lbl_sel.configure(
                text="Seleccioná una cancha de la lista para editar su duración",
                text_color="#333333")
            self._btn_actualizar.configure(state="disabled")
            return
        v = self.tree.item(sel[0], "values")
        self._cancha_sel_id = int(v[0])
        self._lbl_sel.configure(text=f"Cancha seleccionada:  {v[1]}", text_color="#FFFFFF")
        self._combo_dur_edit.set(str(v[3]))
        self._btn_actualizar.configure(state="normal")

    def _actualizar_duracion(self):
        if not self._cancha_sel_id:
            return
        try:
            dur = int(self._combo_dur_edit.get())
        except ValueError:
            messagebox.showwarning("Error", "Duración inválida.")
            return
        actualizar_duracion_cancha(self._cancha_sel_id, dur)
        self.cargar_canchas()
        messagebox.showinfo("Listo",
            f"Duración actualizada a {dur} minutos.\nLas nuevas reservas usarán esta duración.")

    def cargar_canchas(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        self._canchas_cache = listar_canchas_con_precio()
        opciones = [f"{r[1]} ({r[2]})" for r in self._canchas_cache]
        self.combo_bloqueo_cancha.configure(values=opciones if opciones else [""])
        if opciones:
            self.combo_bloqueo_cancha.set(opciones[0])

        for fila in self._canchas_cache:
            cid, nombre, tipo, _, duracion = fila
            tipo_raw = tipo.lower().replace("á", "a").replace("ú", "u")
            tag = tipo_raw if tipo_raw in ("padel", "futbol", "tenis") else ""
            self.tree.insert("", "end", values=(cid, nombre, tipo.capitalize(), duracion), tags=(tag,))

    def agregar_cancha(self):
        nombre = sanitizar_texto(self.entry_nombre.get(), max_largo=100)
        tipo   = self.combo_tipo.get().strip()
        try:
            duracion = int(self.combo_dur.get())
        except ValueError:
            messagebox.showwarning("Error", "Duración inválida.")
            return
        if not nombre or not tipo:
            messagebox.showwarning("Error", "Completá todos los campos.")
            return
        if tipo not in _TIPOS_VALIDOS:
            messagebox.showwarning("Error", "Tipo de cancha inválido.")
            return
        if existe_cancha(nombre):
            messagebox.showerror("Error", "Ya existe una cancha con ese nombre.")
            return
        insertar_cancha(nombre, tipo, duracion)
        self.entry_nombre.delete(0, "end")
        self.cargar_canchas()

    def eliminar_cancha(self):
        seleccion = self.tree.selection()
        if not seleccion:
            messagebox.showwarning("Atención", "Seleccioná una cancha para eliminar.")
            return
        cancha    = self.tree.item(seleccion[0], "values")
        cancha_id, nombre = cancha[0], cancha[1]
        if messagebox.askyesno("Confirmar", f"¿Eliminar la cancha '{nombre}'?"):
            eliminar_cancha(cancha_id)
            self._cancha_sel_id = None
            self._btn_actualizar.configure(state="disabled")
            self._lbl_sel.configure(
                text="Seleccioná una cancha de la lista para editar su duración",
                text_color="#333333")
            self.cargar_canchas()
            self._cargar_bloqueos()

    # ── Bloqueos ──────────────────────────────────────────────────────────────

    def _agregar_bloqueo(self):
        sel_cancha = self.combo_bloqueo_cancha.get()
        if not sel_cancha or sel_cancha == "":
            messagebox.showwarning("Error", "Seleccioná una cancha para bloquear.")
            return

        cancha_id = next(
            (r[0] for r in self._canchas_cache if f"{r[1]} ({r[2]})" == sel_cancha),
            None
        )
        if cancha_id is None:
            messagebox.showwarning("Error", "No se pudo identificar la cancha.")
            return

        fecha_desde = self.date_bloqueo_desde.get_date().isoformat()
        fecha_hasta = self.date_bloqueo_hasta.get_date().isoformat()
        motivo      = sanitizar_texto(self.entry_motivo.get(), max_largo=200)

        if fecha_hasta < fecha_desde:
            messagebox.showerror("Error",
                "La fecha 'hasta' debe ser igual o posterior a 'desde'.")
            return

        # Verificar reservas afectadas
        afectadas = reservas_afectadas_por_bloqueo(cancha_id, fecha_desde, fecha_hasta)
        if afectadas:
            detalle = "\n".join(
                f"  · {str(r.fecha)}  {str(r.hora_inicio)[:5]}  —  {r.nombre_cliente}"
                for r in afectadas[:8]
            )
            if len(afectadas) > 8:
                detalle += f"\n  ... y {len(afectadas)-8} más"
            ok = messagebox.askyesno(
                "Reservas afectadas",
                f"Este bloqueo afecta {len(afectadas)} reserva(s) existente(s):\n\n"
                f"{detalle}\n\n"
                "Estas reservas NO se eliminan automáticamente.\n"
                "¿Continuar con el bloqueo de todas formas?"
            )
            if not ok:
                return

        insertar_bloqueo(cancha_id, fecha_desde, fecha_hasta, motivo)
        self.entry_motivo.delete(0, "end")
        self._cargar_bloqueos()
        messagebox.showinfo("Bloqueo registrado",
            f"Cancha bloqueada del {fecha_desde} al {fecha_hasta}.")

    def _cargar_bloqueos(self):
        for item in self.btree.get_children():
            self.btree.delete(item)
        for fila in listar_bloqueos_futuros():
            # (id, cancha_nombre, cancha_id, fecha_desde, fecha_hasta, motivo)
            self.btree.insert("", "end",
                values=(fila[0], fila[1], fila[3], fila[4], fila[5]))

    def _quitar_bloqueo(self):
        sel = self.btree.selection()
        if not sel:
            messagebox.showwarning("Atención", "Seleccioná un bloqueo para quitar.")
            return
        v = self.btree.item(sel[0], "values")
        bloqueo_id, cancha_nombre = int(v[0]), v[1]
        if messagebox.askyesno("Confirmar",
            f"¿Quitar el bloqueo de '{cancha_nombre}' ({v[2]} → {v[3]})?"):
            eliminar_bloqueo(bloqueo_id)
            self._cargar_bloqueos()
