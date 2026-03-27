import unicodedata
from datetime import datetime


def validar_horario(hora_str: str) -> bool:
    """
    Verifica que el formato del horario sea HH:MM (24 horas).
    Retorna True si es válido, False si no lo es.
    """
    try:
        datetime.strptime(hora_str, "%H:%M")
        return True
    except ValueError:
        return False


def sanitizar_texto(texto: str, max_largo: int = 200) -> str:
    """
    Limpia texto libre ingresado por el usuario:
    - Elimina espacios extra al inicio/fin.
    - Recorta a max_largo caracteres.
    - Elimina caracteres de control (null bytes, tabs, etc.) que podrían
      causar comportamiento inesperado en la BD o en la UI.
    """
    if not texto:
        return ""
    texto = texto.strip()[:max_largo]
    return "".join(c for c in texto if unicodedata.category(c) != "Cc")
