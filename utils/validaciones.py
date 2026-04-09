import re
import unicodedata
from datetime import datetime


def validar_horario(hora_str) -> bool:
    """
    Verifica que el formato del horario sea HH:MM (24 horas).
    Retorna True si es válido, False si no lo es o si el valor es None.
    """
    if not hora_str or not isinstance(hora_str, str):
        return False
    try:
        datetime.strptime(hora_str.strip(), "%H:%M")
        return True
    except ValueError:
        return False


def validar_email(email: str) -> bool:
    """Valida que el email tenga formato básico usuario@dominio.ext y longitud <= 150."""
    if not email or len(email) > 150:
        return False
    return bool(re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', email))


def sanitizar_texto(texto: str, max_largo: int = 200) -> str:
    """
    Limpia texto libre ingresado por el usuario:
    - Elimina espacios extra al inicio/fin y colapsa espacios internos múltiples.
    - Recorta a max_largo caracteres.
    - Elimina caracteres de control (null bytes, tabs, etc.) que podrían
      causar comportamiento inesperado en la BD o en la UI.
    """
    if not texto:
        return ""
    texto = "".join(c for c in texto if unicodedata.category(c) != "Cc")
    texto = " ".join(texto.split())  # colapsa espacios internos múltiples
    return texto[:max_largo]
