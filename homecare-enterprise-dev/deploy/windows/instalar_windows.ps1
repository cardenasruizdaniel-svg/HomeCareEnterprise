# =========================================================
# HomeCare Enterprise - Instalador para Windows / Windows Server
# =========================================================
#
# Que hace este script (en orden):
#   1. Verifica que se este ejecutando como Administrador.
#   2. Verifica si Python 3.11+ esta instalado; si no, lo
#      descarga (instalador oficial de python.org) y lo
#      instala en silencio.
#   3. Copia el programa a la carpeta de instalacion
#      (por defecto: C:\HomeCareEnterprise).
#   4. Crea un entorno virtual y instala las dependencias
#      de requirements.txt dentro de el.
#   5. Crea el archivo .env a partir de .env.example si no
#      existe todavia.
#   6. Registra el programa como una tarea programada de
#      Windows que se ejecuta cada vez que el usuario que
#      instala inicia sesion en Windows.
#   7. Abre el puerto en el Firewall de Windows.
#   8. Inicia el programa inmediatamente y verifica que
#      responda antes de terminar.
#
# Uso:
#   Clic derecho sobre Instalar_Windows.bat -> "Ejecutar como
#   administrador" (el .bat solo llama a este script con los
#   permisos correctos).
#
# =========================================================

param(
    [string]$CarpetaInstalacion = "C:\HomeCareEnterprise",
    [int]$Puerto = 8000
)

$ErrorActionPreference = "Stop"

function Escribir-Titulo($texto) {
    Write-Host ""
    Write-Host "==========================================================" -ForegroundColor Cyan
    Write-Host " $texto" -ForegroundColor Cyan
    Write-Host "==========================================================" -ForegroundColor Cyan
}

function Escribir-Ok($texto)   { Write-Host "  [OK] $texto" -ForegroundColor Green }
function Escribir-Info($texto) { Write-Host "  [ .. ] $texto" -ForegroundColor Yellow }
function Escribir-Error($texto){ Write-Host "  [ERROR] $texto" -ForegroundColor Red }

# ---------------------------------------------------------
# 1. VERIFICAR PERMISOS DE ADMINISTRADOR
# ---------------------------------------------------------

Escribir-Titulo "HomeCare Enterprise - Instalador para Windows"

$esAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $esAdmin) {
    Escribir-Error "Este instalador debe ejecutarse como Administrador."
    Escribir-Error "Cierre esta ventana y use 'Instalar_Windows.bat' con clic derecho -> Ejecutar como administrador."
    Read-Host "Presione ENTER para salir"
    exit 1
}

Escribir-Ok "Ejecutando con permisos de Administrador."

# ---------------------------------------------------------
# 2. VERIFICAR / INSTALAR PYTHON
# ---------------------------------------------------------

Escribir-Titulo "Verificando Python"

# HomeCare Enterprise necesita una version de Python en el
# rango 3.11-3.12: son las que tienen "ruedas" (wheels)
# precompiladas para TODAS sus dependencias en Windows. Las
# versiones mas nuevas (3.13, 3.14...) pueden no tener aun
# rueda precompilada para librerias como pydantic-core, lo
# que obliga a compilarlas desde cero y falla si no hay
# Visual Studio Build Tools instalado. Por eso este
# instalador NUNCA usa el "python" que ya este en el PATH
# del sistema: instala y usa su propia copia de Python 3.12,
# sin tocar ni reemplazar ninguna otra version que ya tenga
# el equipo (conviven sin problema).

$VERSION_OBJETIVO = "3.12"
$rutaPython312 = $null

function Buscar-Python312 {
    # 1) Preguntarle al selector oficial "py" si ya existe 3.12
    try {
        $resultado = & py -3.12 -c "import sys; print(sys.executable)" 2>&1
        if ($LASTEXITCODE -eq 0 -and (Test-Path $resultado)) {
            return $resultado.Trim()
        }
    } catch {}

    # 2) Buscar en la ruta de instalacion estandar
    $candidatos = @(
        "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe",
        "C:\Python312\python.exe"
    )
    foreach ($c in $candidatos) {
        if (Test-Path $c) { return $c }
    }

    return $null
}

$rutaPython312 = Buscar-Python312

if ($rutaPython312) {
    Escribir-Ok "Python 3.12 ya disponible en: $rutaPython312"
} else {
    Escribir-Info "Python $VERSION_OBJETIVO no encontrado. Descargando instalador oficial de python.org..."
    Escribir-Info "(Si el equipo ya tiene otra version de Python instalada, no se toca ni se reemplaza: quedan las dos.)"

    $urlPython = "https://www.python.org/ftp/python/3.12.7/python-3.12.7-amd64.exe"
    $instaladorPython = "$env:TEMP\python312-instalador.exe"

    Invoke-WebRequest -Uri $urlPython -OutFile $instaladorPython -UseBasicParsing

    Escribir-Info "Instalando Python 3.12 en silencio (esto puede tardar unos minutos)..."

    # PrependPath=0 a proposito: no queremos que compita con
    # la version que ya tenga el sistema por defecto. Se
    # usara siempre por ruta completa o via el selector "py".
    Start-Process -FilePath $instaladorPython -ArgumentList "/quiet InstallAllUsers=1 PrependPath=0 Include_launcher=1 Include_test=0" -Wait

    Remove-Item $instaladorPython -Force

    $rutaPython312 = Buscar-Python312

    if ($null -eq $rutaPython312) {
        Escribir-Error "No se pudo verificar la instalacion de Python 3.12. Reinicie el equipo y vuelva a ejecutar este instalador."
        Read-Host "Presione ENTER para salir"
        exit 1
    }

    Escribir-Ok "Python 3.12 instalado en: $rutaPython312"
}

# ---------------------------------------------------------
# 3. COPIAR EL PROGRAMA A LA CARPETA DE INSTALACION
# ---------------------------------------------------------

Escribir-Titulo "Copiando archivos del programa"

$carpetaOrigen = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)   # deploy/windows -> deploy -> raiz del proyecto

if (-not (Test-Path $CarpetaInstalacion)) {
    New-Item -ItemType Directory -Path $CarpetaInstalacion | Out-Null
}

Escribir-Info "Copiando de '$carpetaOrigen' a '$CarpetaInstalacion' ..."

robocopy $carpetaOrigen $CarpetaInstalacion /E /XD ".git" "__pycache__" "venv" "exports" /XF "*.pyc" "database.db" | Out-Null

Escribir-Ok "Archivos copiados."

# ---------------------------------------------------------
# 4. ENTORNO VIRTUAL + DEPENDENCIAS
# ---------------------------------------------------------

Escribir-Titulo "Instalando dependencias de Python"

Set-Location $CarpetaInstalacion

if (Test-Path "$CarpetaInstalacion\venv") {
    $versionVenvActual = & "$CarpetaInstalacion\venv\Scripts\python.exe" --version 2>&1

    if ($versionVenvActual -notmatch "Python 3\.12") {
        Escribir-Info "El entorno virtual existente usa una version distinta ($versionVenvActual). Se recreara con Python 3.12..."
        Remove-Item -Path "$CarpetaInstalacion\venv" -Recurse -Force
    }
}

if (-not (Test-Path "$CarpetaInstalacion\venv")) {
    Escribir-Info "Creando entorno virtual con Python 3.12..."
    & $rutaPython312 -m venv venv
}

$pipExe = "$CarpetaInstalacion\venv\Scripts\pip.exe"
$pythonExe = "$CarpetaInstalacion\venv\Scripts\python.exe"

Escribir-Info "Actualizando pip..."
& $pythonExe -m pip install --upgrade pip --quiet

Escribir-Info "Instalando dependencias (requirements.txt)..."
& $pipExe install -r requirements.txt --quiet

if ($LASTEXITCODE -ne 0) {
    Escribir-Error "Fallo la instalacion de dependencias. Revise el mensaje de error de arriba."
    Escribir-Error "Si el error menciona 'Building wheel' o 'link.exe not found', avise para revisarlo -- no reinicie el instalador todavia."
    Read-Host "Presione ENTER para salir"
    exit 1
}

Escribir-Ok "Dependencias instaladas."

# ---------------------------------------------------------
# 5. ARCHIVO .env
# ---------------------------------------------------------

Escribir-Titulo "Configuracion (.env)"

if (-not (Test-Path "$CarpetaInstalacion\.env")) {
    Copy-Item "$CarpetaInstalacion\.env.example" "$CarpetaInstalacion\.env"
    Escribir-Ok "Se creo el archivo .env a partir de .env.example."
    Escribir-Info "IMPORTANTE: edite $CarpetaInstalacion\.env para configurar correo, WhatsApp, RIPS, etc."
} else {
    Escribir-Ok "Ya existia un archivo .env; no se modifico."
}

# ---------------------------------------------------------
# 6. TAREA PROGRAMADA (equivalente a servicio de Windows)
# ---------------------------------------------------------

Escribir-Titulo "Configurando inicio automatico"

# Limpieza de intentos anteriores: Tarea Programada y
# lanzador VBS de versiones previas de este instalador (el
# VBS se abandona porque algunos antivirus, incluido Windows
# Defender, bloquean en silencio la ejecucion de archivos
# .vbs por ser un vector comun de virus).
if (Get-ScheduledTask -TaskName "HomeCareEnterprise" -ErrorAction SilentlyContinue) {
    Stop-ScheduledTask -TaskName "HomeCareEnterprise" -ErrorAction SilentlyContinue
    Unregister-ScheduledTask -TaskName "HomeCareEnterprise" -Confirm:$false
    Escribir-Info "Se elimino una Tarea Programada de un intento de instalacion anterior."
}

$carpetaInicio = [Environment]::GetFolderPath("Startup")
$lanzadorVbsAntiguo = Join-Path $carpetaInicio "HomeCareEnterprise.vbs"
if (Test-Path $lanzadorVbsAntiguo) {
    Remove-Item -Path $lanzadorVbsAntiguo -Force -ErrorAction SilentlyContinue
    Escribir-Info "Se elimino el lanzador .vbs de un intento anterior (bloqueado por el antivirus)."
}

# Se usa un acceso directo (.lnk) normal en la carpeta de
# Inicio del usuario -- exactamente el mismo mecanismo que
# usan OneDrive, Spotify, etc. para abrir solos al iniciar
# sesion. Apunta a un archivo .bat (no .ps1): algunos equipos
# tienen restringida la ejecucion de scripts de PowerShell
# (por politica de Windows, antivirus, o configuracion del
# fabricante) incluso con -ExecutionPolicy Bypass, mientras
# que los archivos .bat no tienen ese tipo de restriccion.

$scriptArranque = "$CarpetaInstalacion\deploy\windows\arrancar_servidor.bat"
$rutaAccesoDirecto = Join-Path $carpetaInicio "HomeCareEnterprise.lnk"

$argumentosBat = "`"$CarpetaInstalacion`" $Puerto"

$wshShell = New-Object -ComObject WScript.Shell
$accesoDirecto = $wshShell.CreateShortcut($rutaAccesoDirecto)
$accesoDirecto.TargetPath = $scriptArranque
$accesoDirecto.Arguments = $argumentosBat
$accesoDirecto.WorkingDirectory = $CarpetaInstalacion
$accesoDirecto.WindowStyle = 1   # 1 = ventana normal (visible). Se evita "minimizada"
                                  # por la misma razon que se evita "oculta": en algunos
                                  # equipos Windows/el antivirus bloquean en silencio los
                                  # procesos que no arrancan con ventana visible normal.
$accesoDirecto.Description = "HomeCare Enterprise - inicio automatico"
$accesoDirecto.Save()

Escribir-Ok "Acceso directo de inicio automatico creado en: $rutaAccesoDirecto"
Escribir-Info "(Se ejecutara solo, en una ventana visible, cada vez que $env:USERNAME inicie sesion en Windows. Puede minimizarla a mano, pero no cerrarla.)"

# ---------------------------------------------------------
# 7. FIREWALL
# ---------------------------------------------------------

Escribir-Titulo "Configurando Firewall de Windows"

$reglaExistente = Get-NetFirewallRule -DisplayName "HomeCare Enterprise" -ErrorAction SilentlyContinue

if (-not $reglaExistente) {
    New-NetFirewallRule -DisplayName "HomeCare Enterprise" -Direction Inbound -Protocol TCP -LocalPort $Puerto -Action Allow | Out-Null
    Escribir-Ok "Regla de Firewall creada para el puerto $Puerto."
} else {
    Escribir-Ok "La regla de Firewall ya existia."
}

# ---------------------------------------------------------
# 8. INICIAR AHORA Y VERIFICAR
# ---------------------------------------------------------

Escribir-Titulo "Iniciando HomeCare Enterprise"

# IMPORTANTE: se usa una ventana NORMAL (visible), no oculta.
# Se detecto que Windows/el antivirus bloquean en silencio los
# procesos que se intentan lanzar con -WindowStyle Hidden,
# aunque el mismo proceso funcione perfecto con la ventana
# visible. El usuario puede minimizar esa ventana despues, pero
# no debe cerrarla.
Start-Process -FilePath $scriptArranque -ArgumentList $argumentosBat -WindowStyle Normal

Escribir-Info "Esperando que el servidor responda (puede tardar un par de minutos la primera vez, mientras crea la base de datos)..."

$listo = $false
for ($i = 0; $i -lt 60; $i++) {
    Start-Sleep -Seconds 2
    try {
        $respuesta = Invoke-WebRequest -Uri "http://localhost:$Puerto/health" -UseBasicParsing -TimeoutSec 3
        if ($respuesta.StatusCode -eq 200) {
            $listo = $true
            break
        }
    } catch {
        # todavia no responde, seguir esperando
    }
}

if ($listo) {
    Escribir-Ok "El servidor esta corriendo correctamente."
} else {
    Escribir-Error "El servidor no respondio a tiempo. Revise el log en: $CarpetaInstalacion\logs\servidor.log"
}

# ---------------------------------------------------------
# RESUMEN FINAL
# ---------------------------------------------------------

$ipLocal = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.InterfaceAlias -notmatch "Loopback" } | Select-Object -First 1).IPAddress

Escribir-Titulo "Instalacion completada"

Write-Host ""
Write-Host "  Carpeta de instalacion : $CarpetaInstalacion"
Write-Host "  Acceso desde este equipo:  http://localhost:$Puerto"
if ($ipLocal) {
Write-Host "  Acceso desde la red:       http://$($ipLocal):$Puerto"
}
Write-Host "  Usuario inicial:           admin"
Write-Host "  Contraseña inicial:        admin123  (cambiela de inmediato)"
Write-Host "  Configuracion (.env):      $CarpetaInstalacion\.env"
Write-Host "  Registro (logs):           $CarpetaInstalacion\logs\servidor.log"
Write-Host ""
Write-Host "  El programa se iniciara automaticamente cada vez que $env:USERNAME inicie sesion en este equipo."
Write-Host ""

Read-Host "Presione ENTER para cerrar"
