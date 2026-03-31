# ui/gestionar_canchas_window.py
import customtkinter as ctk
from ui.ventana_mixin import VentanaMixin
from tkinter import ttk, messagebox
from auth.session import SessionManager
from models.canchas_service import (
    listar_canchas_con_precio, insertar_cancha, eliminar_cancha,
    existe_cancha, actualizar_duracion_cancha,
)
from utils.validaciones import sanitizar_texto

_TIPOS_VALIDOS = {"Fútbol", "Pádel", "Tenis"}
_DURACION_DEFAULT = {"Fútbol": 60, "Pádel": 90, "Tenis": 60}
_DURACIONES = ["30", "45", "60", "75", "90", "120"]


class GestionarCanchasWindow(VentanaMixin, ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.withdraw()

        if not SessionManager.esta_logueado():
            self.after(0, self.destroy)
            return

        self.title("Gestionar Canchas")
        width, height = 740, 640
        self.geometry(f"{width}x{height}")
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (width  // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")
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
        ctk.CTkLabel(hdr, text="Agregá, eliminá o modificá la duración de las canchas",
            font=("Arial", 11), text_color="#FF8C42").pack(anchor="w", padx=28, pady=(0, 14))

        ctk.CTkFrame(self, height=1, fg_color="#1C1C1C", corner_radius=0).pack(fill="x")

        # ── Formulario agregar ────────────────────────────────────────────────
        form_card = ctk.CTkFrame(self, fg_color="#141414", corner_radius=0)
        form_card.pack(fill="x")

        fila = ctk.CTkFrame(form_card, fg_color="transparent")
        fila.pack(padx=24, pady=18, fill="x")

        lbl_kw = {"font": ("Arial", 10, "bold"), "text_color": "#555555", "anchor": "w"}
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
        self.combo_dur = ctk.CTkComboBox(col_dur, values=_DURACIONES,
            width=120, **combo_kw)
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

        # ── Lista ─────────────────────────────────────────────────────────────
        list_card = ctk.CTkFrame(self, fg_color="#0F0F0F", corner_radius=0)
        list_card.pack(fill="both", expand=True)

        ctk.CTkLabel(list_card, text="CANCHAS REGISTRADAS",
            font=("Arial", 10, "bold"), text_color="#333333").pack(
            anchor="w", padx=24, pady=(14, 6))

        self._aplicar_estilo_tree()

        tree_frame = ctk.CTkFrame(list_card, fg_color="transparent")
        tree_frame.pack(fill="both", expand=True, padx=14)

        cols = ("ID", "Nombre", "Tipo", "Duración (min)")
        self.tree = ttk.Treeview(tree_frame, columns=cols, show="headings",
            style="Club.Treeview", height=7)
        widths = {"ID": 50, "Nombre": 260, "Tipo": 160, "Duración (min)": 120}
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=widths.get(c, 100), anchor="center")

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview,
            style="Club.Vertical.TScrollbar")
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.tree.tag_configure("padel",  foreground="#00C4FF")
        self.tree.tag_configure("futbol", foreground="#A3F843")
        self.tree.tag_configure("tenis",  foreground="#FF8C42")

        self.tree.bind("<<TreeviewSelect>>", self._on_seleccion)

        ctk.CTkFrame(list_card, height=1, fg_color="#1C1C1C", corner_radius=0).pack(
            fill="x", pady=(10, 0))
        ctk.CTkButton(list_card, text="ELIMINAR CANCHA SELECCIONADA",
            command=self.eliminar_cancha,
            fg_color="transparent", hover_color="#1A0000",
            text_color="#FF5C5C", border_color="#2A0000", border_width=1,
            corner_radius=0, height=38, font=("Arial", 11, "bold")
        ).pack(fill="x")

        self.cargar_canchas()
        self.after(150, self._mostrar_ventana)

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

    def _on_tipo_change(self, valor: str):
        default = _DURACION_DEFAULT.get(valor, 60)
        self.combo_dur.set(str(default))

    def _on_seleccion(self, _event):
        sel = self.tree.selection()
        if not sel:
            self._cancha_sel_id = None
            self._lbl_sel.configure(text="Seleccioná una cancha de la lista para editar su duración",
                text_color="#333333")
            self._btn_actualizar.configure(state="disabled")
            return
        v = self.tree.item(sel[0], "values")
        self._cancha_sel_id = int(v[0])
        nombre   = v[1]
        duracion = v[3]
        self._lbl_sel.configure(text=f"Cancha seleccionada:  {nombre}", text_color="#FFFFFF")
        self._combo_dur_edit.set(str(duracion))
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
        messagebox.showinfo("Listo", f"Duración actualizada a {dur} minutos.\nLas nuevas reservas usarán esta duración.")

    def cargar_canchas(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for fila in listar_canchas_con_precio():
            # fila = (id, nombre, tipo, precio, duracion_minutos)
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
