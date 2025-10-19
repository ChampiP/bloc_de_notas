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
