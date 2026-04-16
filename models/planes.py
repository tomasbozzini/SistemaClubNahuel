# models/planes.py
# Definición de planes y sus límites/funciones

PLANES = {
    "basic": {
        "nombre": "Basic",
        "precio_implementacion": 800,
        "precio_mensual": 40,
        "max_canchas": 3,
        "max_usuarios": 2,
        "funciones": {
            "reservas":             True,
            "calendario":           True,
            "disponibilidad":       True,
            "clientes":             True,
            "exportar_excel":       False,
            "exportar_pdf":         False,
            "historial_financiero": False,
            "whatsapp":             False,
            "reservas_recurrentes": False,
            "analitica":            False,
        },
    },
    "pro": {
        "nombre": "Pro",
        "precio_implementacion": 1200,
        "precio_mensual": 60,
        "max_canchas": 8,
        "max_usuarios": 5,
        "funciones": {
            "reservas":             True,
            "calendario":           True,
            "disponibilidad":       True,
            "clientes":             True,
            "exportar_excel":       True,
            "exportar_pdf":         True,
            "historial_financiero": True,
            "whatsapp":             True,
            "reservas_recurrentes": True,
            "analitica":            False,
        },
    },
    "enterprise": {
        "nombre": "Enterprise",
        "precio_implementacion": 1800,
        "precio_mensual": 90,
        "max_canchas": None,
        "max_usuarios": None,
        "funciones": {
            "reservas":             True,
            "calendario":           True,
            "disponibilidad":       True,
            "clientes":             True,
            "exportar_excel":       True,
            "exportar_pdf":         True,
            "historial_financiero": True,
            "whatsapp":             True,
            "reservas_recurrentes": True,
            "analitica":            True,
        },
    },
}


def tiene_funcion(plan: str, funcion: str) -> bool:
    """Retorna True si el plan incluye la función dada."""
    return PLANES.get(plan, {}).get("funciones", {}).get(funcion, False)


def get_limite_canchas(plan: str):
    """Retorna el límite de canchas del plan (None = ilimitado)."""
    return PLANES.get(plan, {}).get("max_canchas", 0)


def get_limite_usuarios(plan: str):
    """Retorna el límite de usuarios del plan (None = ilimitado)."""
    return PLANES.get(plan, {}).get("max_usuarios", 0)


def get_precio_implementacion(plan: str) -> int:
    return PLANES.get(plan, {}).get("precio_implementacion", 0)


def get_precio_mensual(plan: str) -> int:
    return PLANES.get(plan, {}).get("precio_mensual", 0)
