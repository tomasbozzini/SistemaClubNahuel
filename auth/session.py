# auth/session.py


class SessionManager:
    """
    Guarda el usuario logueado en memoria durante la ejecución de la app.
    Las credenciales nunca se escriben a disco.
    """
    _usuario = None

    @classmethod
    def iniciar_sesion(cls, usuario):
        cls._usuario = usuario

    @classmethod
    def get_usuario_actual(cls):
        return cls._usuario

    @classmethod
    def esta_logueado(cls) -> bool:
        return cls._usuario is not None

    @classmethod
    def cerrar_sesion(cls):
        cls._usuario = None

    @classmethod
    def es_admin(cls) -> bool:
        return cls._usuario is not None and cls._usuario.rol == "admin"
