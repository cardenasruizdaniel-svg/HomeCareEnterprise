# =========================================================
# HomeCare Enterprise - Arranque del servidor (Windows)
# Este script lo ejecuta la Tarea Programada al iniciar
# Windows. No debe ejecutarse manualmente salvo para pruebas.
# =========================================================

param(
    [string]$CarpetaInstalacion = "C:\HomeCareEnterprise",
    [int]$Puerto = 8000
)

# Fuerza a Python a usar UTF-8 siempre (ver arrancar_servidor.bat
# para el detalle de por que esto es necesario en Windows).
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"

# Archivo de ultimo recurso: se escribe SIEMPRE, antes que
# cualquier otra cosa, directamente en la carpeta de
# instalacion (que ya sabemos que existe). Si el script
# fallara incluso antes de poder crear la carpeta de logs,
# aqui debe quedar constancia igual.
$archivoUltimoRecurso = Join-Path $CarpetaInstalacion "ULTIMO_INTENTO_ARRANQUE.txt"

try {
    "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] Script de arranque ejecutado. Usuario: $env:USERNAME. Carpeta: $CarpetaInstalacion. Puerto: $Puerto" | `
        Out-File -FilePath $archivoUltimoRecurso -Append -Encoding utf8
} catch {
    # Si ni siquiera esto se puede escribir, no hay nada mas
    # que hacer desde aqui.
}

# Carpeta de logs FUERA del bloque try, para poder escribir
# ahi el error incluso si algo mas abajo falla.
$carpetaLogs = Join-Path $CarpetaInstalacion "logs"

try {
    if (-not (Test-Path $carpetaLogs)) {
        New-Item -ItemType Directory -Path $carpetaLogs -Force | Out-Null
    }
} catch {
    # Si ni siquiera se puede crear la carpeta de logs, no hay
    # donde escribir el error; se sale en silencio (no hay
    # forma de reportarlo de otra manera desde una Tarea
    # Programada sin ventana).
    exit 1
}

$archivoLog = Join-Path $carpetaLogs "servidor.log"
$archivoErrorArranque = Join-Path $carpetaLogs "error_arranque.log"

function Registrar($mensaje) {
    "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] $mensaje" | Out-File -FilePath $archivoLog -Append -Encoding utf8
}

try {

    Registrar "===== Arranque del script iniciado ====="
    Registrar "Carpeta de instalacion: $CarpetaInstalacion"
    Registrar "Puerto: $Puerto"
    Registrar "Ejecutando como usuario: $env:USERNAME (perfil: $env:USERPROFILE)"

    if (-not (Test-Path $CarpetaInstalacion)) {
        throw "La carpeta de instalacion '$CarpetaInstalacion' no existe o no es accesible para esta cuenta."
    }

    Set-Location $CarpetaInstalacion

    $pythonExe = Join-Path $CarpetaInstalacion "venv\Scripts\python.exe"

    if (-not (Test-Path $pythonExe)) {
        throw "No se encontro Python del entorno virtual en '$pythonExe'. Vuelva a ejecutar el instalador."
    }

    Registrar "Python encontrado en: $pythonExe"

    # -----------------------------------------------
    # Bucle de reintento: si el proceso se cae, se
    # reinicia solo (ademas del reintento que ya provee
    # la propia Tarea Programada de Windows).
    # -----------------------------------------------

    while ($true) {

        Registrar "Iniciando HomeCare Enterprise en el puerto $Puerto..."

        & $pythonExe -u -m uvicorn main:app --host 0.0.0.0 --port $Puerto --workers 1 *>> $archivoLog

        Registrar "El servidor se detuvo (codigo de salida: $LASTEXITCODE). Reintentando en 10 segundos..."

        Start-Sleep -Seconds 10
    }

} catch {

    $mensajeError = $_.Exception.Message

    # Se escribe en DOS archivos: el log normal (por si se
    # pudo crear) y un archivo dedicado solo a errores de
    # arranque, para que sea facil de encontrar.

    "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] ERROR FATAL AL ARRANCAR: $mensajeError" | `
        Out-File -FilePath $archivoErrorArranque -Append -Encoding utf8

    try {
        Registrar "ERROR FATAL AL ARRANCAR: $mensajeError"
    } catch {}

    exit 1
}
