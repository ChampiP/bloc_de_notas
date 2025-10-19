from datetime import datetime

def get_saludo_personalizado(nombre_agente="Brayan champi", nombre_cliente="Cliente"):
    hora_actual = datetime.now().time()
    if hora_actual < datetime.strptime("18:30", "%H:%M").time():
        saludo = "Buenas tardes"
    else:
        saludo = "Buenas noches"
    return f"{saludo} Le saluda {nombre_agente} de Claro. Hoy estaré a cargo de su atención. ¿Cómo le puedo ayudar? Sr {nombre_cliente}"

def evaluar_tnps(valor):
    valor = int(valor)
    if valor < 6:
        return -100
    elif valor > 7:
        return 100
    else:
        return 0


def calculate_tnps_point(value):
    """Map a single TNPS score to a percentage point according to rules:
    8-9 -> 100, 6-7 -> 50, 0-5 -> 0
    Returns integer 0/50/100.
    """
    try:
        v = int(value)
    except Exception:
        return 0
    if v >= 8:
        return 100
    if v >= 6:
        return 50
    return 0


def calculate_tnps_percentage(scores):
    """Calculate the TNPS percentage from an iterable of scores using calculate_tnps_point.
    Returns a float percentage (0-100) rounded to 2 decimals.
    """
    pts = []
    for s in scores:
        try:
            pts.append(calculate_tnps_point(s))
        except Exception:
            continue
    if not pts:
        return 0.0
    return round(sum(pts) / len(pts), 2)
