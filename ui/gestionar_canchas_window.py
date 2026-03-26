# ui/gestionar_canchas_window.py
import customtkinter as ctk
from tkinter import ttk, messagebox
from models.models import listar_canchas, insertar_cancha, eliminar_cancha, existe_cancha


class GestionarCanchasWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.withdraw()
        self.title("Gestionar Canchas")
        width, height = 700, 630
        self.geometry(f"{width}x{height}")
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")
        self.transient(parent)
        self.resizable(False, False)
        self.configure(fg_color="#121212")

        # Barra superior
        ctk.CTkFrame(self, height=4, fg_color="#A3F843", corner_radius=0).pack(fill="x")

        # Header
        ctk.CTkLabel(self, text="GESTIONAR CANCHAS",
            font=("Arial Black", 20, "bold"), text_color="#FFFFFF").pack(pady=(18, 0))
        ctk.CTkLabel(self, text="Agregá o eliminá canchas del club",
            font=("Arial", 11), text_color="#A3F843").pack(pady=(2, 0))
        ctk.CTkFrame(self, height=1, fg_color="#2A2A2A", corner_radius=0).pack(fill="x", padx=36, pady=(12, 0))

        # Card agregar
        card_agregar = ctk.CTkFrame(self, fg_color="#1A1A1A", corner_radius=14)
        card_agregar.pack(padx=36, pady=(16, 8), fill="x")

        lbl_kw = {"font": ("Arial", 10, "bold"), "text_color": "#777777", "anchor": "w"}

        fila = ctk.CTkFrame(card_agregar, fg_color="transparent")
        fila.pack(padx=20, pady=16, fill="x")

        col_nombre = ctk.CTkFrame(fila, fg_color="transparent")
        col_nombre.pack(side="left", expand=True, fill="x", padx=(0, 10))
        ctk.CTkLabel(col_nombre, text="NOMBRE", **lbl_kw).pack(anchor="w", pady=(0, 4))
        self.entry_nombre = ctk.CTkEntry(col_nombre, placeholder_text="Ej: Pádel 3",
            fg_color="#212121", border_color="#333333", text_color="#FFFFFF",
            corner_radius=8, height=38)
        self.entry_nombre.pack(fill="x")

        col_tipo = ctk.CTkFrame(fila, fg_color="transparent")
        col_tipo.pack(side="left", expand=True, fill="x", padx=(0, 10))
        ctk.CTkLabel(col_tipo, text="TIPO", **lbl_kw).pack(anchor="w", pady=(0, 4))
        self.combo_tipo = ctk.CTkComboBox(col_tipo, values=["Fútbol", "Pádel", "Tenis"],
            fg_color="#212121", border_color="#333333", text_color="#FFFFFF",
            button_color="#333333", button_hover_color="#A3F843",
            dropdown_fg_color="#1E1E1E", dropdown_text_color="#FFFFFF",
            corner_radius=8, height=38)
        self.combo_tipo.set("Pádel")
        self.combo_tipo.pack(fill="x")

        ctk.CTkButton(fila, text="AGREGAR", command=self.agregar_cancha,
            fg_color="#A3F843", hover_color="#91E03A", text_color="#000000",
            font=("Arial", 12, "bold"), corner_radius=8, width=110, height=38
        ).pack(side="left", anchor="s")

        # Card listado
        card_lista = ctk.CTkFrame(self, fg_color="#1A1A1A", corner_radius=14)
        card_lista.pack(padx=36, pady=(0, 20), fill="both", expand=True)

        ctk.CTkLabel(card_lista, text="CANCHAS REGISTRADAS",
            font=("Arial", 10, "bold"), text_color="#777777").pack(anchor="w", padx=20, pady=(14, 6))

        self._aplicar_estilo_tree()

        tree_frame = ctk.CTkFrame(card_lista, fg_color="transparent")
        tree_frame.pack(fill="both", expand=True, padx=12)

        # Mostramos las 4 columnas incluyendo el estado actual de la cancha
        cols = ("ID", "Nombre", "Tipo", "Estado")
        self.tree = ttk.Treeview(tree_frame, columns=cols, show="headings",
            style="Club.Treeview", height=8)
        widths = {"ID": 55, "Nombre": 220, "Tipo": 150, "Estado": 130}
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=widths.get(c, 120), anchor="center")

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview,
            style="Club.Vertical.TScrollbar")
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        ctk.CTkButton(card_lista, text="ELIMINAR CANCHA SELECCIONADA",
            command=self.eliminar_cancha,
            fg_color="transparent", hover_color="#1E1E1E",
            text_color="#FF5C5C", border_color="#FF5C5C", border_width=2,
            corner_radius=8, height=36, font=("Arial", 11, "bold")
        ).pack(pady=(8, 14))

        self.cargar_canchas()
        self.deiconify()

    def _aplicar_estilo_tree(self):
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Club.Treeview",
            background="#1A1A1A", foreground="#CCCCCC",
            fieldbackground="#1A1A1A", rowheight=32, borderwidth=0,
            font=("Arial", 11)
        )
        style.configure("Club.Treeview.Heading",
            background="#212121", foreground="#A3F843",
            font=("Arial", 11, "bold"), relief="flat"
        )
        style.map("Club.Treeview",
            background=[("selected", "#2C2C2C")],
            foreground=[("selected", "#A3F843")]
        )
        style.map("Club.Treeview.Heading",
            background=[("active", "#2A2A2A"), ("!active", "#212121")]
        )
        style.configure("Club.Vertical.TScrollbar",
            background="#2A2A2A", troughcolor="#1A1A1A",
            arrowcolor="#666666", borderwidth=0
        )

    def cargar_canchas(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for fila in listar_canchas():
            self.tree.insert("", "end", values=fila)

    def agregar_cancha(self):
        nombre = self.entry_nombre.get().strip()
        tipo = self.combo_tipo.get().strip()
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
        cancha = self.tree.item(seleccion[0], "values")
        cancha_id, nombre = cancha[0], cancha[1]
        if messagebox.askyesno("Confirmar", f"¿Eliminar la cancha '{nombre}'?"):
            eliminar_cancha(cancha_id)
            self.cargar_canchas()
