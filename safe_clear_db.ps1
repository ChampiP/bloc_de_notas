<#
safe_clear_db.ps1

Script seguro para vaciar la BD `atencion_clientes` siguiendo `clear_db.sql`.
- Realiza backups de las tablas `clientes` y `tnps` (usa `mysqldump` si está en PATH).
- Pide confirmación explícita antes de ejecutar el borrado.
- Ejecuta `clear_db.sql` usando el cliente `mysql` (se solicitará contraseña interactiva con -p).

Uso (PowerShell):
  .\safe_clear_db.ps1

Requisitos:
- Tener `mysqldump` y `mysql` en PATH (opcional: si no están, el script pedirá confirmación y puede continuar sin backups).
- El script no guarda la contraseña en texto plano; la CLI pedirá la contraseña cuando corresponda.
#>

param(
    [string]$Host = "localhost",
    [int]$Port = 3306,
    [string]$User = "root",
    [string]$Database = "atencion_clientes",
    [string]$ClearScript = "clear_db.sql",
    [string]$BackupDir = ".\backups"
)

function Write-Info($msg){ Write-Host "[INFO] $msg" -ForegroundColor Cyan }
function Write-Warn($msg){ Write-Host "[WARN] $msg" -ForegroundColor Yellow }
function Write-Err($msg){ Write-Host "[ERROR] $msg" -ForegroundColor Red }

# Crear carpeta de backups
if (-not (Test-Path $BackupDir)) { New-Item -ItemType Directory -Path $BackupDir | Out-Null }

$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$clientesDump = Join-Path $BackupDir "clientes-$timestamp.sql"
$tnpsDump = Join-Path $BackupDir "tnps-$timestamp.sql"

Write-Info "Host: $Host  DB: $Database"

# Detectar mysqldump
$mysqldump = Get-Command mysqldump -ErrorAction SilentlyContinue
$mysql = Get-Command mysql -ErrorAction SilentlyContinue

if ($mysqldump) {
    Write-Info "mysqldump detectado en: $($mysqldump.Path)"
    Write-Info "Se realizará dump de tablas 'clientes' y 'tnps' en: $BackupDir"
    try {
        Write-Info "Ejecutando mysqldump para 'clientes'..."
        & mysqldump -h $Host -P $Port -u $User -p $Database clientes 2>$null | Out-File -FilePath $clientesDump -Encoding ascii
        Write-Info "Guardado: $clientesDump"
    } catch {
        Write-Warn "Fallo al hacer dump de 'clientes': $_"
    }
    try {
        Write-Info "Ejecutando mysqldump para 'tnps'..."
        & mysqldump -h $Host -P $Port -u $User -p $Database tnps 2>$null | Out-File -FilePath $tnpsDump -Encoding ascii
        Write-Info "Guardado: $tnpsDump"
    } catch {
        Write-Warn "Fallo al hacer dump de 'tnps': $_"
    }
} else {
    Write-Warn "mysqldump no encontrado en PATH. No se harán backups automáticos con mysqldump."
    Write-Info "Si quieres backup automático, instala el cliente MySQL y asegúrate que 'mysqldump' esté en PATH."
}

# Mostrar archivos de backup (si existen)
if (Test-Path $clientesDump) { Write-Info "Backup clientes: $clientesDump" }
if (Test-Path $tnpsDump) { Write-Info "Backup tnps: $tnpsDump" }

# Comprobar existencia del script de borrado
if (-not (Test-Path $ClearScript)) {
    Write-Err "El archivo $ClearScript no existe en el directorio actual. Cancelo operación."
    exit 2
}

Write-Warn "Este script borrará TODOS los datos de las tablas 'clientes' y 'tnps' en la base de datos '$Database'."
$confirm = Read-Host "Escribe 'YES' (en mayúsculas) para continuar"
if ($confirm -ne 'YES') {
    Write-Info "Operación cancelada por el usuario. Ningún cambio realizado."
    exit 0
}

# Ejecutar clear_db.sql usando el cliente mysql (redirige entrada usando cmd /c para asegurar redirección)
if ($mysql) {
    try {
        Write-Info "Ejecutando $ClearScript en la base de datos $Database..."
        $cmd = "mysql -h $Host -P $Port -u $User -p $Database < \"$ClearScript\""
        # Ejecutar en cmd para que la redirección funcione correctamente
        cmd.exe /c $cmd
        if ($LASTEXITCODE -eq 0) {
            Write-Info "Clear script ejecutado correctamente."
        } else {
            Write-Err "El comando mysql devolvió código $LASTEXITCODE. Revisa la salida para detalles."
        }
    } catch {
        Write-Err "Error al ejecutar clear script: $_"
    }
} else {
    Write-Warn "Cliente 'mysql' no encontrado en PATH. No puedo ejecutar $ClearScript automáticamente."
    Write-Info "Puedes ejecutar manualmente: mysql -h $Host -P $Port -u $User -p $Database < $ClearScript"
}

Write-Info "Operación finalizada. Revisa los archivos de backup en: $BackupDir (si se crearon)."
