# Bloc de Notas - Gestión de Atención al Cliente

Aplicación de escritorio (Tkinter) para gestionar atención al cliente y registrar TNPS.

## Requisitos

- Python 3.10 o superior
- Sistema operativo: Windows

## Instalación

1. Crear y activar un entorno virtual (recomendado):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Instalar dependencias:

```powershell
pip install -r requirements.txt
```

## Ejecución

```powershell
python main.py
```

## Base de Datos

La aplicación usa **SQLite** (incluido con Python). La base de datos `atencion_clientes.db` se crea automáticamente al ejecutar la app.

## Estructura del Proyecto

```
bloc_de_notas/
├── main.py              # Punto de entrada
├── requirements.txt     # Dependencias
├── README.md            # Documentación
├── data/                # Base de datos SQLite
│   └── atencion_clientes.db
└── src/
    ├── __init__.py
    ├── models/          # Capa de datos
    │   ├── __init__.py
    │   ├── database.py  # Funciones SQLite
    │   └── templates.py # Plantillas de texto
    ├── views/           # Capa de presentación
    │   ├── __init__.py
    │   ├── main_window.py  # Ventana principal
    │   └── modals.py    # Ventanas modales
    └── utils/           # Utilidades
        ├── __init__.py
        └── helpers.py   # Funciones auxiliares
```

## Funcionalidades

- Registro de clientes y motivos de llamada
- Gestión de casos: Retención, Cuestionamiento, Atención Técnica
- Cálculo y seguimiento de TNPS
- Temporizador de llamadas
- Gestión de credenciales (VPN/SIAC)
- Temas claro/oscuro