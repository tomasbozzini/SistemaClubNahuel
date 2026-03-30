# ui/gestion_usuarios_window.py
import customtkinter as ctk
from ui.ventana_mixin import VentanaMixin
from tkinter import ttk, messagebox
from auth.session import SessionManager
from models.usuarios_service import listar_admins, crear_admin, actualizar_admin, eliminar_admin, restablecer_password
from utils.validaciones import sanitizar_texto, validar_email

_COLOR = "#9D6EFF"   # violeta — color gestión de usuarios


class GestionUsuariosWindow(VentanaMixin, ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.withdraw()

        usuario = SessionManager.get_usuario_actual()
        if not usuario or usuario.rol != "supervisor":
            self.after(0, self.destroy)
            return

        self.title("Gestión de Usuarios — Club Nahuel")
        width, height = 760, 600
        self.geometry(f"{width}x{height}")
        self.update_idletasks()
        x = (self.winfo_screenwidth()  // 2) - (width  // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")
        self.transient(parent)
        self.resizable(False, False)
        self.configure(fg_color="#0D0D0D")

        self._usuario_sel_id = None
        self._modo = "nuevo"   # nuevo | editar
        self._build_ui()
        self.after(150, self._mostrar_ventana)

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        ctk.CTkFrame(self, height=4, fg_color=_COLOR, corner_radius=0).pack(fill="x")

        # Header
        hdr = ctk.CTkFrame(self, fg_color="#111111", corner_radius=0)
        hdr.pack(fill="x")
        ctk.CTkLabel(hdr, text="GESTIÓN DE USUARIOS",
            font=("Arial Black", 20, "bold"), text_color="#FFFFFF").pack(
            anchor="w", padx=28, pady=(16, 2))
        ctk.CTkLabel(hdr, text="Administrá los usuarios con rol ADMIN",
            font=("Arial", 11), text_color=_COLOR).pack(
            anchor="w", padx=28, pady=(0, 14))
        ctk.CTkFrame(self, height=1, fg_color="#1C1C1C", corner_radius=0).pack(fill="x")

        # Formulario
        self._build_form()
        ctk.CTkFrame(self, height=1, fg_color="#1C1C1C", corner_radius=0).pack(fill="x")

        # Lista
        self._build_lista()

    def _build_form(self):
        form = ctk.CTkFrame(self, fg_color="#141414", corner_radius=0)
        form.pack(fill="x")

        inner = ctk.CTkFrame(form, fg_color="transparent")
        inner.pack(padx=24, pady=16, fill="x")

        lbl_kw = {"font": ("Arial", 10, "bold"), "text_color": "#555555", "anchor": "w"}
        ent_kw = {
            "fg_color": "#1A1A1A", "border_color": "#252525", "border_width": 1,
            "text_color": "#FFFFFF", "corner_radius": 10, "height": 40,
        }

        # Fila 1: nombre + email
        row1 = ctk.CTkFrame(inner, fg_color="transparent")
        row1.pack(fill="x", pady=(0, 10))

        col_nombre = ctk.CTkFrame(row1, fg_color="transparent")
        col_nombre.pack(side="left", expand=True, fill="x", padx=(0, 10))
        ctk.CTkLabel(col_nombre, text="NOMBRE DE USUARIO", **lbl_kw).pack(anchor="w", pady=(0, 4))
        self._entry_nombre = ctk.CTkEntry(col_nombre, placeholder_text="Ej: Juan Pérez", **ent_kw)
        self._entry_nombre.pack(fill="x")

        col_email = ctk.CTkFrame(row1, fg_color="transparent")
        col_email.pack(side="left", expand=True, fill="x")
        ctk.CTkLabel(col_email, text="EMAIL", **lbl_kw).pack(anchor="w", pady=(0, 4))
        self._entry_email = ctk.CTkEntry(col_email, placeholder_text="Ej: juan@club.com", **ent_kw)
        self._entry_email.pack(fill="x")

        # Fila 2: contraseña + botones
        row2 = ctk.CTkFrame(inner, fg_color="transparent")
        row2.pack(fill="x")

        col_pass = ctk.CTkFrame(row2, fg_color="transparent")
        col_pass.pack(side="left", expand=True, fill="x", padx=(0, 10))
        self._lbl_pass = ctk.CTkLabel(col_pass, text="CONTRASEÑA", **lbl_kw)
        self._lbl_pass.pack(anchor="w", pady=(0, 4))
        self._entry_pass = ctk.CTkEntry(col_pass, placeholder_text="••••••••",
            show="•", **ent_kw)
        self._entry_pass.pack(fill="x")

        btns = ctk.CTkFrame(row2, fg_color="transparent")
        btns.pack(side="left", anchor="s")

        self._btn_guardar = ctk.CTkButton(
            btns, text="+ CREAR ADMIN", command=self._guardar,
            fg_color=_COLOR, hover_color="#B899FF",
            text_color="#FFFFFF", font=("Arial Black", 12, "bold"),
            corner_radius=10, width=130, height=40,
        )
        self._btn_guardar.pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            btns, text="LIMPIAR", command=self._limpiar_form,
            fg_color="transparent", hover_color="#1A1A1A",
            text_color="#555555", border_color="#2A2A2A", border_width=1,
            corner_radius=10, width=90, height=40,
        ).pack(side="left")

    def _build_lista(self):
        list_card = ctk.CTkFrame(self, fg_color="#0F0F0F", corner_radius=0)
        list_card.pack(fill="both", expand=True)

        ctk.CTkLabel(list_card, text="USUARIOS ADMIN REGISTRADOS",
            font=("Arial", 10, "bold"), text_color="#333333").pack(
            anchor="w", padx=24, pady=(14, 6))

        self._aplicar_estilo_tree()

        tree_frame = ctk.CTkFrame(list_card, fg_color="transparent")
        tree_frame.pack(fill="both", expand=True, padx=14)

        cols = ("ID", "Nombre", "Email", "Estado")
        self.tree = ttk.Treeview(tree_frame, columns=cols, show="headings",
            style="Club.Treeview", height=7)
        widths = {"ID": 50, "Nombre": 220, "Email": 280, "Estado": 100}
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=widths.get(c, 100), anchor="center")

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview,
            style="Club.Vertical.TScrollbar")
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.tree.tag_configure("activo",   foreground="#A3F843")
        self.tree.tag_configure("inactivo", foreground="#FF5C5C")

        self.tree.bind("<<TreeviewSelect>>", self._on_seleccion)

        # Botones de acción
        ctk.CTkFrame(list_card, height=1, fg_color="#1C1C1C", corner_radius=0).pack(
            fill="x", pady=(10, 0))
        ctk.CTkButton(list_card, text="RESTABLECER CONTRASEÑA",
            command=self._restablecer_password,
            fg_color="transparent", hover_color="#1A1A00",
            text_color="#FFD700", border_color="#2A2A00", border_width=1,
            corner_radius=0, height=38, font=("Arial", 11, "bold"),
        ).pack(fill="x")
        ctk.CTkFrame(list_card, height=1, fg_color="#1C1C1C", corner_radius=0).pack(fill="x")
        ctk.CTkButton(list_card, text="ELIMINAR USUARIO SELECCIONADO",
            command=self._eliminar,
            fg_color="transparent", hover_color="#1A0000",
            text_color="#FF5C5C", border_color="#2A0000", border_width=1,
            corner_radius=0, height=38, font=("Arial", 11, "bold"),
        ).pack(fill="x")

        self._cargar_usuarios()

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

    def _cargar_usuarios(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for u in listar_admins():
            # u = (id, nombre, email, activo)
            tag = "activo" if u[3] else "inactivo"
            estado = "Activo" if u[3] else "Inactivo"
            self.tree.insert("", "end", values=(u[0], u[1], u[2], estado), tags=(tag,))

    # ── Eventos ───────────────────────────────────────────────────────────────

    def _on_seleccion(self, event):
        sel = self.tree.selection()
        if not sel:
            return
        v = self.tree.item(sel[0], "values")
        self._usuario_sel_id = int(v[0])
        self._modo = "editar"
        self._entry_nombre.delete(0, "end")
        self._entry_nombre.insert(0, v[1])
        self._entry_email.delete(0, "end")
        self._entry_email.insert(0, v[2])
        self._entry_pass.delete(0, "end")
        self._lbl_pass.configure(text="NUEVA CONTRASEÑA (dejar vacío para no cambiar)")
        self._btn_guardar.configure(text="GUARDAR CAMBIOS")

    def _limpiar_form(self):
        self._usuario_sel_id = None
        self._modo = "nuevo"
        self._entry_nombre.delete(0, "end")
        self._entry_email.delete(0, "end")
        self._entry_pass.delete(0, "end")
        self._lbl_pass.configure(text="CONTRASEÑA")
        self._btn_guardar.configure(text="+ CREAR ADMIN")
        if self.tree.selection():
            self.tree.selection_remove(self.tree.selection())

    def _guardar(self):
        nombre = sanitizar_texto(self._entry_nombre.get(), max_largo=100)
        email  = sanitizar_texto(self._entry_email.get(), max_largo=100).lower()
        passwd = self._entry_pass.get().strip()

        if not nombre or not email:
            messagebox.showwarning("Atención", "Nombre y email son obligatorios.")
            return
        if not validar_email(email):
            messagebox.showwarning("Atención", "El email no tiene un formato válido.")
            return

        try:
            if self._modo == "nuevo":
                if not passwd:
                    messagebox.showwarning("Atención", "La contraseña es obligatoria para nuevos usuarios.")
                    return
                crear_admin(nombre, email, passwd)
                messagebox.showinfo("Listo", f"Usuario '{nombre}' creado con rol ADMIN.")
            else:
                actualizar_admin(self._usuario_sel_id, nombre, email, passwd)
                messagebox.showinfo("Listo", f"Usuario '{nombre}' actualizado.")
        except ValueError as e:
            messagebox.showerror("Error", str(e))
            return

        self._limpiar_form()
        self._cargar_usuarios()

    def _restablecer_password(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Atención", "Seleccioná un usuario para restablecer la contraseña.")
            return
        v = self.tree.item(sel[0], "values")
        usuario_id, nombre = int(v[0]), v[1]
        if not messagebox.askyesno("Confirmar",
                f"¿Restablecer la contraseña de '{nombre}'?\n\nSe generará una contraseña temporal."):
            return
        try:
            nueva = restablecer_password(usuario_id)
        except ValueError as e:
            messagebox.showerror("Error", str(e))
            return
        messagebox.showinfo(
            "Contraseña restablecida",
            f"Nueva contraseña temporal para '{nombre}':\n\n"
            f"  {nueva}\n\n"
            "Comunicásela al usuario y pedile que la cambie al ingresar."
        )

    def _eliminar(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Atención", "Seleccioná un usuario para eliminar.")
            return
        v = self.tree.item(sel[0], "values")
        usuario_id, nombre = int(v[0]), v[1]
        if messagebox.askyesno("Confirmar", f"¿Eliminar al usuario '{nombre}'?\nEsta acción no se puede deshacer."):
            eliminar_admin(usuario_id)
            self._limpiar_form()
            self._cargar_usuarios()
