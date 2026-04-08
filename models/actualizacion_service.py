# models/actualizacion_service.py
APP_VERSION = "1.3.11"


def verificar_actualizacion():
    """
    Retorna (hay_update: bool, version_nueva: str, url: str) consultando Supabase.
    Si falla la conexión, retorna (False, "", "").
    """
    try:
        from db.database import SessionLocal
        from models.configuracion import Configuracion

        with SessionLocal() as session:
            def _get(clave):
                row = session.get(Configuracion, clave)
                return row.valor if row else ""

            latest  = _get("latest_version")
            url     = _get("download_url")

        if latest and _version_mayor(latest, APP_VERSION):
            return True, latest, url
        return False, "", ""
    except Exception:
        return False, "", ""


def _version_mayor(a: str, b: str) -> bool:
    """Retorna True si la versión a es mayor que b (compara semver)."""
    try:
        return tuple(int(x) for x in a.split(".")) > tuple(int(x) for x in b.split("."))
    except Exception:
        return False
