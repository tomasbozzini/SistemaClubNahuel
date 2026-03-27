# ui/ventana_mixin.py
# Mixin reutilizable para CTkToplevel — asegura que la ventana aparezca al frente.


class VentanaMixin:
    def _mostrar_ventana(self):
        self.deiconify()
        self.lift()
        self.focus_force()
        self.attributes("-topmost", True)
        self.after(100, lambda: self.attributes("-topmost", False))
