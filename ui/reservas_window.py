# ui/reservas_window.py
import customtkinter as ctk
from ui.ventana_mixin import VentanaMixin, centrar_ventana
from tkcalendar import DateEntry
from tkinter import messagebox
from datetime import datetime, date as date_type
from auth.session import SessionManager
from utils.validaciones import validar_horario, sanitizar_texto
from models.canchas_service import listar_canchas_con_precio
from models.reservas_service import insertar_reserva, insertar_reservas_recurrentes, verificar_slot, listar_slots_disponibles


_DURACION_LABEL = {"padel": "1 h 30 min", "futbol": "1 hora", "tenis": "1 hora"}
_COLOR_TIPO     = {"padel": "#00C4FF", "futbol": "#A3F843", "tenis": "#FF8C42"}


class _AutocompletePopup(ctk.CTkToplevel):
    """Dropdown de autocompletado posicionado bajo el entry de cliente."""

    def __init__(self, parent, entry, items, on_select):
        super().__init__(parent)
        self.overrideredirect(True)
        self.configure(fg_color="#1A1A1A")

        x = entry.winfo_rootx()
        y = entry.winfo_rooty() + entry.winfo_height() + 2
        w = entry.winfo_width()
        item_h = 36
        h = min(len(items) * item_h, 180)
        self.geometry(f"{w}x{h}+{x}+{y}")
        self.lift()
        self.attributes("-topmost", True)

        for cid, nombre, tel, email in items:
            row = ctk.CTkFrame(self, fg_color="#1A1A1A", height=item_h, corner_radius=0)
            row.pack(fill="x")
            row.pack_propagate(False)
            ctk.CTkLabel(row, text=nombre,
                font=("Arial", 11), text_color="#FFFFFF", anchor="w").pack(
                side="left", padx=(12, 4))
            if tel:
                ctk.CTkLabel(row, text=tel,
                    font=("Arial", 9), text_color="#555555", anchor="w").pack(side="left")

            def _sel(n=nombre, t=tel):
                on_select(n, t)
                if self.winfo_exists():
                    self.destroy()

            row.bind("<Enter>", lambda e, r=row: r.configure(fg_color="#252525"))
            row.bind("<Leave>", lambda e, r=row: r.configure(fg_color="#1A1A1A"))

            # Bind recursivo: CTkLabel tiene widgets internos anidados;
            # hay que llegar al tkinter.Label real para capturar el click.
            def _bind_recursive(widget, callback):
                widget.bind("<Button-1>", lambda e: callback())
                for child in widget.winfo_children():
                    _bind_recursive(child, callback)

            self.after(1, lambda r=row, s=_sel: _bind_recursive(r, s))


class ReservasWindow(VentanaMixin, ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.withdraw()

        if not SessionManager.esta_logueado():
            self.after(0, self.destroy)
            return

        self.title("Nueva Reserva")
        self.update_idletasks()
        centrar_ventana(self, 520, 780)
        self.resizable(False, False)
        self.transient(parent)
        self.configure(fg_color="#0D0D0D")

        self._autocomplete_popup = None
        self._debounce_id = None

        # Barra de acento
        ctk.CTkFrame(self, height=4, fg_color="#A3F843", corner_radius=0).pack(fill="x")

        # Header
        hdr = ctk.CTkFrame(self, fg_color="#111111", corner_radius=0)
        hdr.pack(fill="x")
        ctk.CTkLabel(hdr, text="NUEVA RESERVA",
            font=("Arial Black", 20, "bold"), text_color="#FFFFFF").pack(
            anchor="w", padx=28, pady=(16, 2))
        ctk.CTkLabel(hdr, text="Completá los datos del turno",
            font=("Arial", 11), text_color="#A3F843").pack(anchor="w", padx=28, pady=(0, 14))

        ctk.CTkFrame(self, height=1, fg_color="#1C1C1C", corner_radius=0).pack(fill="x")

        # Card formulario
        card = ctk.CTkFrame(self, fg_color="#141414", corner_radius=0)
        card.pack(padx=0, pady=0, fill="both", expand=True)

        lbl_kw = {"font": ("Arial", 10, "bold"), "text_color": "#555555", "anchor": "w"}
        ent_kw = {"width": 432, "fg_color": "#1A1A1A", "border_color": "#252525",
                  "border_width": 1, "text_color": "#FFFFFF", "corner_radius": 10, "height": 40}

        # Cliente (con autocompletado)
        ctk.CTkLabel(card, text="CLIENTE", **lbl_kw).pack(anchor="w", padx=28, pady=(22, 4))
        self.entry_cliente = ctk.CTkEntry(card, placeholder_text="Nombre del cliente", **ent_kw)
        self.entry_cliente.pack(padx=28)
        self.entry_cliente.bind("<KeyRelease>", self._on_cliente_key)
        self.entry_cliente.bind("<FocusOut>", lambda e: self.after(150, self._cerrar_autocomplete))

        # Celular
        ctk.CTkLabel(card, text="CELULAR", **lbl_kw).pack(anchor="w", padx=28, pady=(14, 4))
        self.entry_celular = ctk.CTkEntry(card, placeholder_text="Ej: 11-1234-5678", **ent_kw)
        self.entry_celular.pack(padx=28)

        # Cancha
        ctk.CTkLabel(card, text="CANCHA", **lbl_kw).pack(anchor="w", padx=28, pady=(16, 4))
        self.canchas = []

        self.combo_cancha = ctk.CTkComboBox(card, values=["Cargando..."], width=432, height=40,
            fg_color="#1A1A1A", border_color="#252525", border_width=1,
            text_color="#FFFFFF", button_color="#252525", button_hover_color="#A3F843",
            dropdown_fg_color="#1A1A1A", dropdown_text_color="#FFFFFF", corner_radius=10,
            command=self._actualizar_hint)
        self.combo_cancha.set("Cargando...")
        self.combo_cancha.pack(padx=28)
        self._cargar_canchas_async()

        # Hint de duración/precio
        self.lbl_hint = ctk.CTkLabel(card, text="",
            font=("Arial", 10, "bold"), text_color="#444444", anchor="w")
        self.lbl_hint.pack(anchor="w", padx=28, pady=(4, 0))
        self._actualizar_hint()

        # Fila fecha / hora
        fila = ctk.CTkFrame(card, fg_color="transparent")
        fila.pack(padx=28, fill="x", pady=(14, 0))

        col_fecha = ctk.CTkFrame(fila, fg_color="transparent")
        col_fecha.pack(side="left", expand=True, fill="x", padx=(0, 14))
        ctk.CTkLabel(col_fecha, text="FECHA", **lbl_kw).pack(anchor="w", pady=(0, 4))
        self.date_entry = DateEntry(col_fecha, date_pattern="yyyy-mm-dd",
            background="#1A1A1A", foreground="white", borderwidth=0,
            headersbackground="#0D0D0D", headersforeground="#A3F843",
            selectbackground="#A3F843", selectforeground="black",
            normalbackground="#1A1A1A", normalforeground="white",
            weekendbackground="#1A1A1A", weekendforeground="#A3F843",
            font=("Arial", 11))
        self.date_entry.pack(anchor="w", ipady=6)
        self.date_entry.bind("<<DateEntrySelected>>", lambda e: self._cargar_slots_async())

        col_hora = ctk.CTkFrame(fila, fg_color="transparent")
        col_hora.pack(side="left", expand=True, fill="x")
        ctk.CTkLabel(col_hora, text="HORARIO DISPONIBLE", **lbl_kw).pack(anchor="w", pady=(0, 4))
        self.combo_hora = ctk.CTkComboBox(col_hora,
            values=["— elegí cancha y fecha —"],
            height=40, fg_color="#1A1A1A", border_color="#252525", border_width=1,
            text_color="#FFFFFF", button_color="#252525", button_hover_color="#A3F843",
            dropdown_fg_color="#1A1A1A", dropdown_text_color="#FFFFFF",
            corner_radius=10, state="readonly")
        self.combo_hora.set("— elegí cancha y fecha —")
        self.combo_hora.pack(fill="x")

        # Observaciones
        ctk.CTkLabel(card, text="OBSERVACIONES", **lbl_kw).pack(anchor="w", padx=28, pady=(16, 4))
        self.entry_obs = ctk.CTkEntry(card, placeholder_text="Opcional", **ent_kw)
        self.entry_obs.pack(padx=28)

        # Estado de pago
        ctk.CTkLabel(card, text="ESTADO DE PAGO", **lbl_kw).pack(anchor="w", padx=28, pady=(14, 4))
        self._pago_seg = ctk.CTkSegmentedButton(
            card,
            values=["Pendiente", "Seña", "Pagado"],
            width=432, height=36,
            fg_color="#1A1A1A",
            selected_color="#A3F843",
            selected_hover_color="#C5FF6B",
            unselected_color="#1A1A1A",
            unselected_hover_color="#252525",
            text_color="#FFFFFF",
            font=("Arial", 11, "bold"),
            corner_radius=10,
        )
        self._pago_seg.set("Pendiente")
        self._pago_seg.pack(padx=28)

        # ── Recurrencia ───────────────────────────────────────────────────────
        ctk.CTkFrame(card, height=1, fg_color="#1C1C1C", corner_radius=0).pack(
            fill="x", padx=0, pady=(18, 0))

        rec_row = ctk.CTkFrame(card, fg_color="transparent")
        rec_row.pack(padx=28, pady=(12, 0), fill="x")

        self.var_recurrente = ctk.BooleanVar(value=False)
        self.chk_recurrente = ctk.CTkCheckBox(rec_row,
            text="Repetir semanalmente",
            variable=self.var_recurrente,
            command=self._toggle_recurrencia,
            fg_color="#A3F843", hover_color="#C5FF6B",
            checkmark_color="#0D0D0D",
            text_color="#888888", font=("Arial", 11))
        self.chk_recurrente.pack(side="left")

        self._hasta_frame = ctk.CTkFrame(rec_row, fg_color="transparent")
        self._hasta_frame.pack(side="left", padx=(20, 0))
        ctk.CTkLabel(self._hasta_frame, text="HASTA:",
            font=("Arial", 10, "bold"), text_color="#555555").pack(side="left", padx=(0, 8))
        self.date_hasta = DateEntry(self._hasta_frame, date_pattern="yyyy-mm-dd",
            background="#1A1A1A", foreground="white", borderwidth=0,
            headersbackground="#0D0D0D", headersforeground="#A3F843",
            selectbackground="#A3F843", selectforeground="black",
            normalbackground="#1A1A1A", normalforeground="white",
            weekendbackground="#1A1A1A", weekendforeground="#A3F843",
            font=("Arial", 11), state="disabled")
        self.date_hasta.pack(side="left", ipady=5)
        self._hasta_frame.pack_forget()

        # Botón guardar
        ctk.CTkFrame(card, height=1, fg_color="#1C1C1C", corner_radius=0).pack(
            fill="x", pady=(16, 0))
        self.btn_guardar = ctk.CTkButton(card, text="GUARDAR RESERVA  →", command=self.guardar,
            fg_color="#A3F843", hover_color="#C5FF6B", text_color="#0D0D0D",
            font=("Arial Black", 13, "bold"), corner_radius=0, width=520, height=46
        )
        self.btn_guardar.pack(fill="x")

        self.after(150, self._mostrar_ventana)

    # ── Carga de canchas ──────────────────────────────────────────────────────

    def _cargar_canchas_async(self):
        import threading
        def _worker():
            try:
                canchas = listar_canchas_con_precio()
                self.after(0, lambda: self._poblar_combo_canchas(canchas))
            except Exception:
                self.after(0, lambda: self.combo_cancha.configure(values=["Error al cargar"]))
        threading.Thread(target=_worker, daemon=True).start()

    def _poblar_combo_canchas(self, canchas):
        if not self.winfo_exists():
            return
        self.canchas = canchas
        opciones = [f"{r[1]} ({r[2]})" for r in canchas]
        self.combo_cancha.configure(values=opciones if opciones else ["Sin canchas"])
        if opciones:
            self.combo_cancha.set(opciones[0])
        self._actualizar_hint()

    # ── Autocompletado ────────────────────────────────────────────────────────

    def _on_cliente_key(self, event):
        if event.keysym in ("Up", "Down", "Return", "Escape", "Tab"):
            return
        self._cerrar_autocomplete()
        # Debounce: esperar 300 ms sin teclas antes de consultar
        if self._debounce_id:
            self.after_cancel(self._debounce_id)
        self._debounce_id = self.after(300, self._buscar_autocomplete)

    def _buscar_autocomplete(self):
        import threading
        self._debounce_id = None
        texto = self.entry_cliente.get().strip()
        if len(texto) < 2:
            return
        def _worker():
            try:
                from models.clientes_service import buscar_clientes
                items = buscar_clientes(texto)
                self.after(0, lambda: self._mostrar_autocomplete(items))
            except Exception:
                pass
        threading.Thread(target=_worker, daemon=True).start()

    def _mostrar_autocomplete(self, items):
        if not self.winfo_exists():
            return
        if items:
            self._autocomplete_popup = _AutocompletePopup(
                self, self.entry_cliente, items, self._seleccionar_cliente
            )

    def _cerrar_autocomplete(self):
        if self._autocomplete_popup:
            try:
                if self._autocomplete_popup.winfo_exists():
                    self._autocomplete_popup.destroy()
            except Exception:
                pass
            self._autocomplete_popup = None

    def _seleccionar_cliente(self, nombre, telefono):
        self.entry_cliente.delete(0, "end")
        self.entry_cliente.insert(0, nombre)
        if telefono:
            self.entry_celular.delete(0, "end")
            self.entry_celular.insert(0, telefono)

    # ── Recurrencia ───────────────────────────────────────────────────────────

    def _toggle_recurrencia(self):
        if self.var_recurrente.get():
            self._hasta_frame.pack(side="left", padx=(20, 0))
            self.date_hasta.configure(state="normal")
        else:
            self._hasta_frame.pack_forget()
            self.date_hasta.configure(state="disabled")

    # ── Slots disponibles ─────────────────────────────────────────────────────

    def _cargar_slots_async(self, *_):
        """Carga horarios disponibles para la cancha y fecha seleccionadas."""
        import threading
        if not hasattr(self, "combo_hora") or not self.winfo_exists():
            return
        seleccion = self.combo_hora.get()  # evitar recarga si está cargando
        # Obtener cancha_id
        combo_val = self.combo_cancha.get()
        cancha_id = next((r[0] for r in self.canchas if f"{r[1]} ({r[2]})" == combo_val), None)
        if not cancha_id:
            return
        try:
            fecha = self.date_entry.get_date().isoformat()
        except Exception:
            return

        self.combo_hora.configure(values=["Cargando..."], state="disabled")
        self.combo_hora.set("Cargando...")

        def _worker():
            try:
                slots = listar_slots_disponibles(cancha_id, fecha)
                self.after(0, lambda: self._poblar_slots(slots))
            except Exception:
                self.after(0, lambda: self._poblar_slots([]))

        threading.Thread(target=_worker, daemon=True).start()

    def _poblar_slots(self, slots):
        if not self.winfo_exists():
            return
        if slots:
            self.combo_hora.configure(values=slots, state="readonly")
            self.combo_hora.set(slots[0])
        else:
            self.combo_hora.configure(values=["Sin horarios disponibles"], state="readonly")
            self.combo_hora.set("Sin horarios disponibles")

    # ── Hint cancha ───────────────────────────────────────────────────────────

    def _actualizar_hint(self, *_):
        seleccion = self.combo_cancha.get()
        cancha = next((r for r in self.canchas if f"{r[1]} ({r[2]})" == seleccion), None)
        if not cancha:
            self.lbl_hint.configure(text="")
            return
        tipo     = cancha[2].lower().replace("á", "a").replace("ú", "u")
        duracion = _DURACION_LABEL.get(tipo, "1 hora")
        color    = _COLOR_TIPO.get(tipo, "#666666")
        precio   = cancha[3]
        if precio:
            precio_str = f"${precio:,.0f}".replace(",", ".")
            texto = f"Duración:  {duracion}   ·   Precio:  {precio_str}"
        else:
            texto = f"Duración:  {duracion}   ·   Precio:  sin definir"
        self.lbl_hint.configure(text=texto, text_color=color)
        # Recargar slots al cambiar la cancha
        self._cargar_slots_async()

    # ── Guardar ───────────────────────────────────────────────────────────────

    def guardar(self):
        import threading
        self._cerrar_autocomplete()

        cliente   = sanitizar_texto(self.entry_cliente.get(), max_largo=100)
        celular   = sanitizar_texto(self.entry_celular.get(), max_largo=30)
        seleccion = self.combo_cancha.get()
        fecha     = self.date_entry.get_date().isoformat()
        hora      = self.combo_hora.get().strip()
        obs       = sanitizar_texto(self.entry_obs.get(), max_largo=300)
        pago_map  = {"Pendiente": "pendiente", "Seña": "seña", "Pagado": "pagado"}
        estado_pago = pago_map.get(self._pago_seg.get(), "pendiente")

        if not cliente:
            messagebox.showerror("Error", "Ingresá el nombre del cliente.")
            return
        if not celular:
            messagebox.showerror("Error", "Ingresá el número de celular.")
            return
        if not seleccion:
            messagebox.showerror("Error", "Seleccioná una cancha.")
            return
        if not hora or not validar_horario(hora):
            messagebox.showerror("Error",
                "Seleccioná un horario disponible de la lista.")
            return

        try:
            reserva_dt = datetime.strptime(f"{fecha} {hora}", "%Y-%m-%d %H:%M")
        except ValueError:
            messagebox.showerror("Error", "Fecha u hora inválida.")
            return
        if reserva_dt <= datetime.now():
            messagebox.showerror("Horario inválido",
                "No se puede reservar en una fecha y hora pasada.")
            return

        cancha_id = next((r[0] for r in self.canchas if f"{r[1]} ({r[2]})" == seleccion), None)
        if cancha_id is None:
            messagebox.showerror("Error", "No se pudo identificar la cancha seleccionada.")
            return

        es_recurrente = self.var_recurrente.get()
        fecha_hasta = None
        if es_recurrente:
            fecha_hasta = self.date_hasta.get_date().isoformat()
            if fecha_hasta <= fecha:
                messagebox.showerror("Error",
                    "La fecha 'hasta' debe ser posterior a la fecha de inicio.")
                return

        # Deshabilitar botón mientras procesa
        self.btn_guardar.configure(state="disabled", text="Guardando...")
        self.configure(cursor="watch")

        def _worker():
            try:
                if es_recurrente:
                    exitosas, conflictos, fechas_conf = insertar_reservas_recurrentes(
                        cliente, cancha_id, fecha, hora, obs, celular, fecha_hasta, estado_pago
                    )
                    self.after(0, lambda: self._on_guardado_recurrente(exitosas, conflictos, fechas_conf))
                else:
                    error = verificar_slot(cancha_id, fecha, hora)
                    if error:
                        self.after(0, lambda: self._on_slot_error(error))
                        return
                    rid = insertar_reserva(cliente, cancha_id, fecha, hora, obs, celular, estado_pago)
                    self.after(0, lambda: self._on_guardado_ok(rid))
            except Exception as e:
                self.after(0, lambda: self._on_guardar_error(str(e)))

        threading.Thread(target=_worker, daemon=True).start()

    def _on_guardar_error(self, msg):
        if not self.winfo_exists():
            return
        self.configure(cursor="")
        self.btn_guardar.configure(state="normal", text="GUARDAR RESERVA  →")
        messagebox.showerror("Error", msg)

    def _on_slot_error(self, error):
        if not self.winfo_exists():
            return
        self.configure(cursor="")
        self.btn_guardar.configure(state="normal", text="GUARDAR RESERVA  →")
        messagebox.showerror("Sin disponibilidad", error)

    def _on_guardado_ok(self, reserva_id):
        if not self.winfo_exists():
            return
        self.configure(cursor="")
        messagebox.showinfo("Reserva guardada",
            f"Reserva #{reserva_id} registrada correctamente.")
        self.event_generate("<<ReservaGuardada>>", when="tail")
        self.destroy()

    def _on_guardado_recurrente(self, exitosas, conflictos, fechas_conf):
        if not self.winfo_exists():
            return
        self.configure(cursor="")
        if exitosas == 0:
            self.btn_guardar.configure(state="normal", text="GUARDAR RESERVA  →")
            messagebox.showerror("Sin disponibilidad",
                "No se pudo crear ninguna reserva.\n"
                "Todas las fechas tienen conflictos o la cancha está bloqueada.")
            return
        msg = f"Se crearon {exitosas} reserva(s) semanales."
        if conflictos:
            omitidas = "\n".join(fechas_conf[:5])
            if len(fechas_conf) > 5:
                omitidas += f"\n... y {len(fechas_conf)-5} más"
            msg += f"\n\n{conflictos} fecha(s) omitida(s) por conflicto:\n{omitidas}"
        messagebox.showinfo("Reservas creadas", msg)
        self.event_generate("<<ReservaGuardada>>", when="tail")
        self.destroy()
