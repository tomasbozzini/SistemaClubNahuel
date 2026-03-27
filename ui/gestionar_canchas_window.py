# ui/gestionar_canchas_window.py
import customtkinter as ctk
from ui.ventana_mixin import VentanaMixin
from tkinter import ttk, messagebox
from auth.session import SessionManager
from models.canchas_service import listar_canchas, insertar_cancha, eliminar_cancha, existe_cancha

_COLOR_TIPO = {"pádel": "#00C4FF", "padel": "#00C4FF",
               "fútbol": "#A3F843", "futbol": "#A3F843",
               "tenis": "#FF8C42"}


class GestionarCanchasWindow(VentanaMixin, ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.withdraw()

        if not SessionManager.esta_logueado():
            self.after(0, self.destroy)
            return

        self.title("Gestionar Canchas")
        width, height = 680, 580
        self.geometry(f"{width}x{height}")
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (width  // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")
        self.transient(parent)
        self.resizable(False, False)
        self.configure(fg_color="#0D0D0D")

        # Barra de acento orange (color de "canchas")
        ctk.CTkFrame(self, height=4, fg_color="#FF8C42", corner_radius=0).pack(fill="x")

        # Header
        hdr = ctk.CTkFrame(self, fg_color="#111111", corner_radius=0)
        hdr.pack(fill="x")
        ctk.CTkLabel(hdr, text="GESTIONAR CANCHAS",
            font=("Arial Black", 20, "bold"), text_color="#FFFFFF").pack(
            anchor="w", padx=28, pady=(16, 2))
        ctk.CTkLabel(hdr, text="Agregá o eliminá canchas del club",
            font=("Arial", 11), text_color="#FF8C42").pack(anchor="w", padx=28, pady=(0, 14))

        ctk.CTkFrame(self, height=1, fg_color="#1C1C1C", corner_radius=0).pack(fill="x")

        # ── Formulario ───────────────────────────────────────────────────────
        form_card = ctk.CTkFrame(self, fg_color="#141414", corner_radius=0)
        form_card.pack(fill="x")

        fila = ctk.CTkFrame(form_card, fg_color="transparent")
        fila.pack(padx=24, pady=18, fill="x")

        lbl_kw = {"font": ("Arial", 10, "bold"), "text_color": "#555555", "anchor": "w"}

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
            width=150, fg_color="#1A1A1A", border_color="#252525", border_width=1,
            text_color="#FFFFFF", button_color="#252525", button_hover_color="#FF8C42",
            dropdown_fg_color="#1A1A1A", dropdown_text_color="#FFFFFF",
            corner_radius=10, height=40)
        self.combo_tipo.set("Pádel")
        self.combo_tipo.pack(fill="x")

        ctk.CTkButton(fila, text="+ AGREGAR", command=self.agregar_cancha,
            fg_color="#FF8C42", hover_color="#FFA066", text_color="#0D0D0D",
            font=("Arial Black", 12, "bold"), corner_radius=10, width=110, height=40
        ).pack(side="left", anchor="s")

        ctk.CTkFrame(self, height=1, fg_color="#1C1C1C", corner_radius=0).pack(fill="x")

        # ── Lista ────────────────────────────────────────────────────────────
        list_card = ctk.CTkFrame(self, fg_color="#0F0F0F", corner_radius=0)
        list_card.pack(fill="both", expand=True)

        ctk.CTkLabel(list_card, text="CANCHAS REGISTRADAS",
            font=("Arial", 10, "bold"), text_color="#333333").pack(
            anchor="w", padx=24, pady=(14, 6))

        self._aplicar_estilo_tree()

        tree_frame = ctk.CTkFrame(list_card, fg_color="transparent")
        tree_frame.pack(fill="both", expand=True, padx=14)

        cols = ("ID", "Nombre", "Tipo")
        self.tree = ttk.Treeview(tree_frame, columns=cols, show="headings",
            style="Club.Treeview", height=8)
        widths = {"ID": 55, "Nombre": 310, "Tipo": 210}
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=widths.get(c, 120), anchor="center")

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview,
            style="Club.Vertical.TScrollbar")
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Tags por tipo
        self.tree.tag_configure("padel",  foreground="#00C4FF")
        self.tree.tag_configure("futbol", foreground="#A3F843")
        self.tree.tag_configure("tenis",  foreground="#FF8C42")

        # Botón eliminar
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

    def cargar_canchas(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for fila in listar_canchas():
            tipo_raw = fila[2].lower().replace("á", "a").replace("ú", "u")
            tag = tipo_raw if tipo_raw in ("padel", "futbol", "tenis") else ""
            self.tree.insert("", "end", values=fila[:3], tags=(tag,))

    def agregar_cancha(self):
        nombre = self.entry_nombre.get().strip()
        tipo   = self.combo_tipo.get().strip()
        if not nombre or not tipo:
            messagebox.showwarning("Error", "Completá todos los campos.")
            return
        if existe_cancha(nombre):
            messagebox.showerror("Error", "Ya existe una cancha con ese nombre.")
            return
        insertar_cancha(nombre, tipo)
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
            self.cargar_canchas()
