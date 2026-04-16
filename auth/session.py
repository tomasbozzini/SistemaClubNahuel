# auth/session.py


class SessionManager:
    """
    Guarda el usuario logueado en memoria durante la ejecución de la app.
    Las credenciales nunca se escriben a disco.
    """
    _usuario    = None
    _club_plan  = None   # cache para get_plan()

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
        cls._usuario   = None
        cls._club_plan = None

    @classmethod
    def es_superadmin(cls) -> bool:
        return cls._usuario is not None and cls._usuario.rol == "superadmin"

    @classmethod
    def es_supervisor(cls) -> bool:
        return cls._usuario is not None and cls._usuario.rol == "supervisor"

    @classmethod
    def es_admin(cls) -> bool:
        return cls._usuario is not None and cls._usuario.rol == "admin"

    @classmethod
    def get_plan(cls) -> str:
        """
        Retorna el plan del club actual ('basic', 'pro', 'enterprise').
        Usa cache para evitar consultas repetidas. Superadmin → 'enterprise'.
        """
        if cls._usuario is None:
            return "basic"
        if cls._usuario.rol == "superadmin":
            return "enterprise"
        if cls._club_plan is not None:
            return cls._club_plan
        club_id = getattr(cls._usuario, "club_id", None)
        if club_id:
            try:
                from sqlalchemy import text
                from db.database import engine
                with engine.connect() as conn:
                    plan = conn.execute(
                        text("SELECT plan FROM clubs WHERE id = :id"), {"id": club_id}
                    ).scalar()
                cls._club_plan = plan or "basic"
            except Exception:
                cls._club_plan = "basic"
        else:
            cls._club_plan = "basic"
        return cls._club_plan

    @classmethod
    def get_club_id(cls) -> int | None:
        """
        Retorna el club_id del usuario logueado.
        - superadmin → None (acceso a todos los clubes, sin filtro)
        - admin / supervisor → club_id del usuario
        - sin sesión → club_id del config.ini como fallback
        """
        if cls._usuario is None:
            return _club_id_desde_config()
        if cls._usuario.rol == "superadmin":
            return None
        return getattr(cls._usuario, "club_id", None)


def _club_id_desde_config() -> int:
    """Lee club_id del config.ini ya parseado por db/database.py."""
    from db.database import get_club_id_config
    return get_club_id_config()
