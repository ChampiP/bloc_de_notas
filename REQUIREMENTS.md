# bloc_de_notas — Requisitos y ejecución

Resumen

Una aplicación de escritorio (Tkinter) para gestionar atención al cliente y registrar TNPS.

Requisitos

- Python 3.10+ (probado con 3.11)
- MySQL Server (local o accesible por red)
- Paquetes Python:
  - pymysql
  - plyer

Instalación rápida

1. Crear y activar un entorno virtual (opcional pero recomendado):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Instalar dependencias:

```powershell
pip install pymysql plyer
```

3. Crear la base de datos y tablas (usar MySQL):

```sql
-- ejecutar create_db.sql
```

4. (Opcional) Agregar columna notas si no existe:

```sql
-- ejecutar add_notas_column.sql
```

Ejecución

```powershell
C:/Users/MDY/Desktop/bloc_de_notas/.venv/Scripts/python.exe main.py
```

Notas

- La app mostrará un indicador de estado de la base de datos en la esquina superior derecha: "DB: OK" (verde) o "DB: Offline" (rojo). Si la DB no está accesible, la UI seguirá funcionando pero los guardados fallarán.
- Para desarrollo, inicia MySQL (o XAMPP) antes de abrir la app para tener integración completa.

Siguientes pasos recomendados

- Implementar una cola offline para insertar cuando la DB vuelva a estar disponible.
- Añadir tests unitarios y logging a archivo.
- Completar los modales de Retención y Cuestionamiento con flujos reales de negocio.
