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
