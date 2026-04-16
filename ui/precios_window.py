# ui/precios_window.py
import customtkinter as ctk
from ui.ventana_mixin import VentanaMixin, centrar_ventana
from tkinter import ttk, messagebox
from auth.session import SessionManager
from models.canchas_service import listar_canchas_con_precio, actualizar_precio_cancha

_COLOR = "#00D4FF"   # verde esmeralda — color precios


def _fmt_peso(valor: float) -> str:
    return f"$ {int(valor):,}".replace(",", ".")


class PreciosWindow(VentanaMixin, ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.withdraw()

        usuario = SessionManager.get_usuario_actual()
        if not usuario or usuario.rol not in ("supervisor", "admin"):
            self.after(0, self.destroy)
            return

        from db.database import get_club_nombre
        self.title(f"Gestión de Precios — {get_club_nombre()}")
        self.update_idletasks()
        centrar_ventana(self, 700, 560)
        self.transient(parent)
        self.resizable(False, False)
        self.configure(fg_color="#0D0D0D")

        self._cancha_seleccionada_id = None
        self._build_ui()
        self.after(150, self._mostrar_ventana)

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        ctk.CTkFrame(self, height=4, fg_color=_COLOR, corner_radius=0).pack(fill="x")

        # Header
        hdr = ctk.CTkFrame(self, fg_color="#111111", corner_radius=0)
        hdr.pack(fill="x")
        ctk.CTkLabel(hdr, text="GESTIÓN DE PRECIOS",
            font=("Arial Black", 20, "bold"), text_color="#FFFFFF").pack(
            anchor="w", padx=28, pady=(16, 2))
        ctk.CTkLabel(hdr, text="Configurá el precio de cada cancha",
            font=("Arial", 11), text_color=_COLOR).pack(
            anchor="w", padx=28, pady=(0, 14))
        ctk.CTkFrame(self, height=1, fg_color="#1C1C1C", corner_radius=0).pack(fill="x")

        # Panel de edición
        form = ctk.CTkFrame(self, fg_color="#141414", corner_radius=0)
        form.pack(fill="x")

        form_inner = ctk.CTkFrame(form, fg_color="transparent")
        form_inner.pack(padx=24, pady=16, fill="x")

        lbl_kw = {"font": ("Arial", 10, "bold"), "text_color": "#555555", "anchor": "w"}
        ent_kw = {
            "fg_color": "#1A1A1A", "border_color": "#252525", "border_width": 1,
            "text_color": "#FFFFFF", "corner_radius": 10, "height": 40,
        }

        # Cancha seleccionada (readonly)
        col_nombre = ctk.CTkFrame(form_inner, fg_color="transparent")
        col_nombre.pack(side="left", expand=True, fill="x", padx=(0, 12))
        ctk.CTkLabel(col_nombre, text="CANCHA SELECCIONADA", **lbl_kw).pack(anchor="w", pady=(0, 4))
        self._lbl_cancha_sel = ctk.CTkLabel(
            col_nombre, text="— Seleccioná una cancha de la lista —",
            font=("Arial", 12), text_color="#444444",
            fg_color="#1A1A1A", corner_radius=10, height=40, width=300,
        )
        self._lbl_cancha_sel.pack(fill="x")

        # Nuevo precio
        col_precio = ctk.CTkFrame(form_inner, fg_color="transparent")
        col_precio.pack(side="left", padx=(0, 12))
        ctk.CTkLabel(col_precio, text="NUEVO PRECIO ($)", **lbl_kw).pack(anchor="w", pady=(0, 4))
        self._entry_precio = ctk.CTkEntry(col_precio, placeholder_text="Ej: 72000",
            width=140, **ent_kw)
        self._entry_precio.pack()

        # Botón guardar
        ctk.CTkButton(
            form_inner, text="GUARDAR", command=self._guardar_precio,
            fg_color=_COLOR, hover_color="#00FFB2",
            text_color="#0D0D0D", font=("Arial Black", 12, "bold"),
            corner_radius=10, width=110, height=40,
        ).pack(side="left", anchor="s")

        ctk.CTkFrame(self, height=1, fg_color="#1C1C1C", corner_radius=0).pack(fill="x")

        # Tabla de canchas
        list_card = ctk.CTkFrame(self, fg_color="#0F0F0F", corner_radius=0)
        list_card.pack(fill="both", expand=True)

        ctk.CTkLabel(list_card, text="CANCHAS ACTIVAS",
            font=("Arial", 10, "bold"), text_color="#333333").pack(
            anchor="w", padx=24, pady=(14, 6))

        self._aplicar_estilo_tree()

        tree_frame = ctk.CTkFrame(list_card, fg_color="transparent")
        tree_frame.pack(fill="both", expand=True, padx=14)

        cols = ("ID", "Nombre", "Tipo", "Duración", "Precio actual")
        self.tree = ttk.Treeview(tree_frame, columns=cols, show="headings",
            style="Club.Treeview", height=9)
        widths = {"ID": 50, "Nombre": 220, "Tipo": 100, "Duración": 100, "Precio actual": 180}
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=widths.get(c, 100), anchor="center")

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview,
            style="Club.Vertical.TScrollbar")
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.tree.tag_configure("padel",  foreground="#00C4FF")
        self.tree.tag_configure("futbol", foreground="#7C5CFF")
        self.tree.tag_configure("tenis",  foreground="#FF8C42")

        self.tree.bind("<<TreeviewSelect>>", self._on_seleccion)

        self._cargar_canchas()

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

    def _cargar_canchas(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for c in listar_canchas_con_precio():
            # c = (id, nombre, tipo, precio, duracion_minutos)
            tipo_raw = c[2].lower().replace("á", "a").replace("ú", "u")
            dur      = c[4]
            dur_str  = f"{dur // 60}h {dur % 60:02d}m" if dur % 60 else f"{dur // 60}h"
            tag = tipo_raw if tipo_raw in ("padel", "futbol", "tenis") else ""
            precio_str = _fmt_peso(c[3]) if c[3] > 0 else "Sin precio"
            self.tree.insert("", "end",
                values=(c[0], c[1], c[2].capitalize(), dur_str, precio_str),
                tags=(tag,))

    def _on_seleccion(self, event):
        sel = self.tree.selection()
        if not sel:
            return
        valores = self.tree.item(sel[0], "values")
        self._cancha_seleccionada_id = int(valores[0])
        self._lbl_cancha_sel.configure(
            text=f"  {valores[1]}  —  {valores[2]}",
            text_color="#FFFFFF",
        )
        self._entry_precio.delete(0, "end")

    def _guardar_precio(self):
        if not self._cancha_seleccionada_id:
            messagebox.showwarning("Atención", "Seleccioná una cancha primero.")
            return
        texto = self._entry_precio.get().strip().replace(".", "").replace(",", "")
        if not texto.isdigit():
            messagebox.showerror("Error", "Ingresá un precio válido (solo números).")
            return
        precio = float(texto)
        actualizar_precio_cancha(self._cancha_seleccionada_id, precio)
        self._entry_precio.delete(0, "end")
        self._cargar_canchas()
        messagebox.showinfo("Listo", f"Precio actualizado a {_fmt_peso(precio)}")
