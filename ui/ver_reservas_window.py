# ui/ver_reservas_window.py
import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox
from auth.session import SessionManager
from models.reservas_service import listar_reservas, eliminar_reserva


class VerReservasWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.withdraw()

        if not SessionManager.esta_logueado():
            self.after(0, self.destroy)
            return

        self.title("Ver Reservas")
        width, height = 880, 530
        self.geometry(f"{width}x{height}")
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (width  // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")
        self.transient(parent)
        self.configure(fg_color="#121212")

        ctk.CTkFrame(self, height=4, fg_color="#A3F843", corner_radius=0).pack(fill="x")

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=32, pady=(18, 0))
        ctk.CTkLabel(header, text="VER RESERVAS",
            font=("Arial Black", 20, "bold"), text_color="#FFFFFF").pack(side="left")
        self.lbl_count = ctk.CTkLabel(header, text="",
            font=("Arial", 12), text_color="#555555")
        self.lbl_count.pack(side="left", padx=(12, 0))

        ctk.CTkFrame(self, height=1, fg_color="#2A2A2A", corner_radius=0).pack(
            fill="x", padx=32, pady=(12, 0))

        card = ctk.CTkFrame(self, fg_color="#1A1A1A", corner_radius=14)
        card.pack(padx=32, pady=14, fill="both", expand=True)

        self._aplicar_estilo_tree()

        tree_frame = ctk.CTkFrame(card, fg_color="transparent")
        tree_frame.pack(fill="both", expand=True, padx=14, pady=(14, 8))

        cols = ("ID", "Cliente", "Cancha", "Tipo", "Fecha", "Hora", "Notas")
        self.tree = ttk.Treeview(tree_frame, columns=cols, show="headings", style="Club.Treeview")
        widths = {"ID": 45, "Cliente": 160, "Cancha": 140, "Tipo": 85,
                  "Fecha": 100, "Hora": 65, "Notas": 190}
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=widths.get(c, 100), anchor="center")

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview,
            style="Club.Vertical.TScrollbar")
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        ctk.CTkButton(card, text="ELIMINAR RESERVA SELECCIONADA",
            command=self.eliminar_reserva_seleccionada,
            fg_color="transparent", hover_color="#1E1E1E",
            text_color="#FF5C5C", border_color="#FF5C5C", border_width=2,
            corner_radius=8, height=38, font=("Arial", 12, "bold")
        ).pack(pady=(0, 14))

        self.cargar_reservas()
        self.deiconify()

    def _aplicar_estilo_tree(self):
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Club.Treeview",
            background="#1A1A1A", foreground="#CCCCCC",
            fieldbackground="#1A1A1A", rowheight=32, borderwidth=0,
            font=("Arial", 11))
        style.configure("Club.Treeview.Heading",
            background="#212121", foreground="#A3F843",
            font=("Arial", 11, "bold"), relief="flat")
        style.map("Club.Treeview",
            background=[("selected", "#2C2C2C")],
            foreground=[("selected", "#A3F843")])
        style.map("Club.Treeview.Heading",
            background=[("active", "#2A2A2A"), ("!active", "#212121")])
        style.configure("Club.Vertical.TScrollbar",
            background="#2A2A2A", troughcolor="#1A1A1A",
            arrowcolor="#666666", borderwidth=0)

    def cargar_reservas(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        filas = listar_reservas()
        for f in filas:
            self.tree.insert("", tk.END, values=f)
        n = len(filas)
        self.lbl_count.configure(text=f"({n} turno{'s' if n != 1 else ''})")

    def eliminar_reserva_seleccionada(self):
        seleccion = self.tree.selection()
        if not seleccion:
            messagebox.showwarning("Atención", "Seleccioná una reserva para eliminar.")
            return
        reserva_id = self.tree.item(seleccion[0])["values"][0]
        if messagebox.askyesno("Confirmar", f"¿Eliminar la reserva #{reserva_id}?"):
            eliminar_reserva(reserva_id)
            self.cargar_reservas()
