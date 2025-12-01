"""
Funciones utilitarias para la aplicación.
"""
from datetime import datetime


def get_saludo_dinamico(nombre_cliente="Cliente"):
    """Genera un saludo corto según la hora del día para mostrar en la UI."""
    hora_actual = datetime.now().time()
    if hora_actual < datetime.strptime("12:00", "%H:%M").time():
        saludo = "Buenos días"
    elif hora_actual < datetime.strptime("18:30", "%H:%M").time():
        saludo = "Buenas tardes"
    else:
        saludo = "Buenas noches"
    return f"{saludo}, Sr. {nombre_cliente}"


def get_saludo_personalizado(nombre_agente="Brayan Champi", nombre_cliente="Cliente"):
    """Genera un saludo personalizado según la hora del día."""
    hora_actual = datetime.now().time()
    if hora_actual < datetime.strptime("12:00", "%H:%M").time():
        saludo = "Buenos días"
    elif hora_actual < datetime.strptime("18:30", "%H:%M").time():
        saludo = "Buenas tardes"
    else:
        saludo = "Buenas noches"
    return f"{saludo}, le saluda {nombre_agente} de Claro. ¿Cómo puedo ayudarle, Sr. {nombre_cliente}?"


def calculate_tnps_point(value):
    """
    Convierte un puntaje TNPS a un valor porcentual.
    8-9 -> 100 (Promotor)
    6-7 -> 50 (Neutro)
    0-5 -> 0 (Detractor)
    """
    try:
        v = int(value)
    except (ValueError, TypeError):
        return 0
    if v >= 8:
        return 100
    if v >= 6:
        return 50
    return 0


def calculate_tnps_percentage(scores):
    """
    Calcula el porcentaje TNPS a partir de una lista de puntajes.
    Devuelve un float (0-100) redondeado a 2 decimales.
    """
    if not scores:
        return 0.0
    
    pts = [calculate_tnps_point(s) for s in scores]
    return round(sum(pts) / len(pts), 2)
