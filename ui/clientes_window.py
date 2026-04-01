# ui/clientes_window.py
import customtkinter as ctk
from ui.ventana_mixin import VentanaMixin
import tkinter as tk
from tkinter import ttk, messagebox
from auth.session import SessionManager
from models.clientes_service import (
    listar_clientes, insertar_cliente, actualizar_cliente, eliminar_cliente,
)
from utils.validaciones import sanitizar_texto


class ClientesWindow(VentanaMixin, ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.withdraw()

        if not SessionManager.esta_logueado():
            self.after(0, self.destroy)
            return

        self.title("Gestionar Clientes")
        width, height = 720, 580
        self.geometry(f"{width}x{height}")
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")
        self.transient(parent)
        self.resizable(False, False)
        self.configure(fg_color="#0D0D0D")

        self._cliente_sel_id = None

        ctk.CTkFrame(self, height=4, fg_color="#9D6EFF", corner_radius=0).pack(fill="x")

        hdr = ctk.CTkFrame(self, fg_color="#111111", corner_radius=0)
        hdr.pack(fill="x")
        ctk.CTkLabel(hdr, text="GESTIONAR CLIENTES",
            font=("Arial Black", 20, "bold"), text_color="#FFFFFF").pack(
            anchor="w", padx=28, pady=(16, 2))
        ctk.CTkLabel(hdr, text="Registrá clientes para autocompletar reservas",
            font=("Arial", 11), text_color="#9D6EFF").pack(anchor="w", padx=28, pady=(0, 14))

        ctk.CTkFrame(self, height=1, fg_color="#1C1C1C", corner_radius=0).pack(fill="x")

        # ── Formulario ────────────────────────────────────────────────────────
        form_card = ctk.CTkFrame(self, fg_color="#141414", corner_radius=0)
        form_card.pack(fill="x")

        fila = ctk.CTkFrame(form_card, fg_color="transparent")
        fila.pack(padx=24, pady=16, fill="x")

        lbl_kw = {"font": ("Arial", 10, "bold"), "text_color": "#555555", "anchor": "w"}
        ent_kw = dict(fg_color="#1A1A1A", border_color="#252525", border_width=1,
                      text_color="#FFFFFF", corner_radius=10, height=38)

        col_nombre = ctk.CTkFrame(fila, fg_color="transparent")
        col_nombre.pack(side="left", expand=True, fill="x", padx=(0, 10))
        ctk.CTkLabel(col_nombre, text="NOMBRE", **lbl_kw).pack(anchor="w", pady=(0, 4))
        self.entry_nombre = ctk.CTkEntry(col_nombre, placeholder_text="Nombre completo", **ent_kw)
        self.entry_nombre.pack(fill="x")

        col_tel = ctk.CTkFrame(fila, fg_color="transparent")
        col_tel.pack(side="left", expand=False, fill="x", padx=(0, 10))
        ctk.CTkLabel(col_tel, text="CELULAR", **lbl_kw).pack(anchor="w", pady=(0, 4))
        self.entry_tel = ctk.CTkEntry(col_tel, placeholder_text="Ej: 11-1234-5678",
            width=160, **ent_kw)
        self.entry_tel.pack(fill="x")

        col_email = ctk.CTkFrame(fila, fg_color="transparent")
        col_email.pack(side="left", expand=False, fill="x", padx=(0, 10))
        ctk.CTkLabel(col_email, text="EMAIL (opcional)", **lbl_kw).pack(anchor="w", pady=(0, 4))
        self.entry_email = ctk.CTkEntry(col_email, placeholder_text="email@ejemplo.com",
            width=180, **ent_kw)
        self.entry_email.pack(fill="x")

        self._btn_guardar = ctk.CTkButton(fila, text="+ GUARDAR", command=self._guardar,
            fg_color="#9D6EFF", hover_color="#B98FFF", text_color="#0D0D0D",
            font=("Arial Black", 11, "bold"), corner_radius=10, width=100, height=38)
        self._btn_guardar.pack(side="left", anchor="s")

        ctk.CTkFrame(self, height=1, fg_color="#1C1C1C", corner_radius=0).pack(fill="x")

        # ── Fila editar seleccionado ──────────────────────────────────────────
        self._edit_card = ctk.CTkFrame(self, fg_color="#111111", corner_radius=0)
        self._edit_card.pack(fill="x")

        edit_row = ctk.CTkFrame(self._edit_card, fg_color="transparent")
        edit_row.pack(padx=24, pady=10, fill="x")

        self._lbl_sel = ctk.CTkLabel(edit_row,
            text="Seleccioná un cliente de la lista para editar",
            font=("Arial", 10), text_color="#333333", anchor="w")
        self._lbl_sel.pack(side="left", expand=True, fill="x")

        self._btn_editar = ctk.CTkButton(edit_row, text="GUARDAR CAMBIOS",
            command=self._editar,
            fg_color="transparent", hover_color="#1A001A",
            text_color="#9D6EFF", border_color="#2A002A", border_width=1,
            corner_radius=10, width=160, height=34, font=("Arial", 11, "bold"),
            state="disabled")
        self._btn_editar.pack(side="left", padx=(10, 0))

        ctk.CTkFrame(self, height=1, fg_color="#1C1C1C", corner_radius=0).pack(fill="x")

        # ── Lista ─────────────────────────────────────────────────────────────
        list_card = ctk.CTkFrame(self, fg_color="#0F0F0F", corner_radius=0)
        list_card.pack(fill="both", expand=True)

        ctk.CTkLabel(list_card, text="CLIENTES REGISTRADOS",
            font=("Arial", 10, "bold"), text_color="#333333").pack(
            anchor="w", padx=24, pady=(14, 6))

        self._aplicar_estilo_tree()
        tree_frame = ctk.CTkFrame(list_card, fg_color="transparent")
        tree_frame.pack(fill="both", expand=True, padx=14)

        cols = ("ID", "Nombre", "Celular", "Email")
        self.tree = ttk.Treeview(tree_frame, columns=cols, show="headings",
            style="Club.Treeview", height=10)
        widths = {"ID": 50, "Nombre": 260, "Celular": 150, "Email": 210}
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=widths.get(c, 100), anchor="center")

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview,
            style="Club.Vertical.TScrollbar")
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.tree.bind("<<TreeviewSelect>>", self._on_seleccion)

        ctk.CTkFrame(list_card, height=1, fg_color="#1C1C1C", corner_radius=0).pack(
            fill="x", pady=(10, 0))
        ctk.CTkButton(list_card, text="ELIMINAR CLIENTE SELECCIONADO",
            command=self._eliminar,
            fg_color="transparent", hover_color="#1A0000",
            text_color="#FF5C5C", border_color="#2A0000", border_width=1,
            corner_radius=0, height=38, font=("Arial", 11, "bold")
        ).pack(fill="x")

        self._cargar()
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
        style.configure("Club.Vertical.TScrollbar",
            background="#1C1C1C", troughcolor="#0F0F0F",
            arrowcolor="#333333", borderwidth=0)

    def _cargar(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for fila in listar_clientes():
            self.tree.insert("", "end", values=fila)

    def _on_seleccion(self, _event):
        sel = self.tree.selection()
        if not sel:
            self._cliente_sel_id = None
            self._lbl_sel.configure(text="Seleccioná un cliente de la lista para editar",
                text_color="#333333")
            self._btn_editar.configure(state="disabled")
            return
        v = self.tree.item(sel[0], "values")
        self._cliente_sel_id = int(v[0])
        self._lbl_sel.configure(text=f"Editando:  {v[1]}", text_color="#FFFFFF")
        self._btn_editar.configure(state="normal")
        # Poner datos en el form
        self.entry_nombre.delete(0, "end")
        self.entry_nombre.insert(0, v[1])
        self.entry_tel.delete(0, "end")
        self.entry_tel.insert(0, v[2])
        self.entry_email.delete(0, "end")
        self.entry_email.insert(0, v[3])

    def _guardar(self):
        nombre = sanitizar_texto(self.entry_nombre.get(), max_largo=100)
        tel    = sanitizar_texto(self.entry_tel.get(), max_largo=30)
        email  = sanitizar_texto(self.entry_email.get(), max_largo=150)
        if not nombre:
            messagebox.showwarning("Error", "El nombre es obligatorio.")
            return
        insertar_cliente(nombre, tel, email)
        self._limpiar_form()
        self._cargar()

    def _editar(self):
        if not self._cliente_sel_id:
            return
        nombre = sanitizar_texto(self.entry_nombre.get(), max_largo=100)
        tel    = sanitizar_texto(self.entry_tel.get(), max_largo=30)
        email  = sanitizar_texto(self.entry_email.get(), max_largo=150)
        if not nombre:
            messagebox.showwarning("Error", "El nombre es obligatorio.")
            return
        actualizar_cliente(self._cliente_sel_id, nombre, tel, email)
        self._limpiar_form()
        self._cargar()

    def _eliminar(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Atención", "Seleccioná un cliente para eliminar.")
            return
        v = self.tree.item(sel[0], "values")
        if messagebox.askyesno("Confirmar", f"¿Eliminar al cliente '{v[1]}'?"):
            eliminar_cliente(int(v[0]))
            self._cliente_sel_id = None
            self._limpiar_form()
            self._cargar()

    def _limpiar_form(self):
        for entry in (self.entry_nombre, self.entry_tel, self.entry_email):
            entry.delete(0, "end")
        self._cliente_sel_id = None
        self._lbl_sel.configure(text="Seleccioná un cliente de la lista para editar",
            text_color="#333333")
        self._btn_editar.configure(state="disabled")
