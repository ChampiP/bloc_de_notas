## bloc_de_notas — Requisitos y ejecución

Descripción

Aplicación de escritorio (Tkinter) para gestionar atención al cliente y registrar TNPS.

Requisitos

- Python 3.10 o superior (probado con 3.11)
- MySQL Server (local o accesible por red)
- Paquetes Python:
  - pymysql
  - plyer

Entorno recomendado (PowerShell)

1) Crear y activar un entorno virtual (opcional pero recomendado)

```powershell
python -m venv .venv
# Activar el entorno virtual en PowerShell
.\.venv\Scripts\Activate.ps1
```

2) Instalar dependencias

```powershell
pip install --upgrade pip
pip install pymysql plyer
```

Base de datos (MySQL)

- Crear la base de datos y las tablas ejecutando el script SQL principal:

  - Abre tu cliente MySQL (MySQL Shell, Workbench o desde terminal) y ejecuta `create_db.sql`.

  - Si necesitas poblar tablas adicionales o crear motivos, ejecuta `create_motivos_tables.sql`.

- (Opcional) Si la tabla requiere la columna `notas`, ejecutar `add_notas_column.sql`.

Nota: los scripts están en la raíz del proyecto: `create_db.sql`, `create_motivos_tables.sql`, `add_notas_column.sql`.

Ejecución de la aplicación

Con el entorno virtual activado, ejecuta:

```powershell
python main.py
```

O, si prefieres usar la ruta absoluta al intérprete de la venv:

```powershell
C:\ruta\a\tu\proyecto\.venv\Scripts\python.exe main.py
```

Indicador de estado de la base de datos

- La interfaz mostrará en la esquina superior derecha un indicador: "DB: OK" (verde) o "DB: Offline" (rojo).
- Si la DB no está accesible la UI seguirá funcionando localmente, pero las operaciones de guardado fallarán.

Consejos y resolución de problemas

- Asegúrate de que MySQL esté en ejecución antes de abrir la app (por ejemplo, inicia XAMPP o el servicio MySQL).
- Si recibes errores de conexión, revisa `db.py` y la configuración de conexión (host, usuario, contraseña, puerto).
- Para comprobar disponibilidad de MySQL desde PowerShell:

```powershell
# intenta conectar con mysql.exe (si está en PATH)
mysql -u tu_usuario -p -h 127.0.0.1 -P 3306
```

- Si usas Windows y el comando `mysql` no existe, abre MySQL Workbench o añade el binario de MySQL al PATH.

Sugerencias de desarrollo (próximos pasos)

- Implementar una cola offline para almacenar inserciones localmente y reintentar cuando la DB vuelva a estar disponible.
- Añadir tests unitarios y logging a archivo para diagnosticar errores en producción.
- Completar los modales de Retención y Cuestionamiento con flujos de negocio y validaciones.

Archivos clave en el proyecto

- `main.py` — punto de entrada de la aplicación.
- `db.py` — funciones de acceso a la base de datos.
- `ui.py` / `modales.py` / `templates.py` — componentes de la interfaz.
- Scripts SQL: `create_db.sql`, `create_motivos_tables.sql`, `add_notas_column.sql`, `create_motivos_tables.sql`, `clear_db.sql`, `setup_db.sql`.

Contacto y notas finales

Mantén este archivo actualizado con cualquier dependencia nueva. Si quieres, puedo:

- añadir un `requirements.txt` generado (`pip freeze > requirements.txt`),
- crear un pequeño script `run.ps1` que active el venv y ejecute `main.py`,
- o añadir instrucciones para un Dockerfile si prefieres contenerizar la app.

---
Pequeña verificación: la sección de ejecución y la ruta al intérprete están orientadas a Windows/PowerShell. Ajusta la ruta absoluta del venv según tu proyecto.
