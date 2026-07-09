# =========================================================
# HomeCare Enterprise - Desinstalador para Windows
# =========================================================

param(
    [string]$CarpetaInstalacion = "C:\HomeCareEnterprise",
    [switch]$BorrarDatos
)

$esAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $esAdmin) {
    Write-Host "Este script debe ejecutarse como Administrador." -ForegroundColor Red
    Read-Host "Presione ENTER para salir"
    exit 1
}

Write-Host "Quitando el acceso directo de inicio automatico..." -ForegroundColor Yellow

$carpetaInicio = [Environment]::GetFolderPath("Startup")

foreach ($nombre in @("HomeCareEnterprise.lnk", "HomeCareEnterprise.vbs")) {
    $ruta = Join-Path $carpetaInicio $nombre
    if (Test-Path $ruta) {
        Remove-Item -Path $ruta -Force -ErrorAction SilentlyContinue
    }
}

# Compatibilidad con instalaciones anteriores que usaban Tarea Programada
if (Get-ScheduledTask -TaskName "HomeCareEnterprise" -ErrorAction SilentlyContinue) {
    Stop-ScheduledTask -TaskName "HomeCareEnterprise" -ErrorAction SilentlyContinue
    Unregister-ScheduledTask -TaskName "HomeCareEnterprise" -Confirm:$false
}

Write-Host "Deteniendo el proceso del servidor (si esta corriendo)..." -ForegroundColor Yellow

Get-Process python -ErrorAction SilentlyContinue | Where-Object {
    $_.Path -like "$CarpetaInstalacion*"
} | Stop-Process -Force -ErrorAction SilentlyContinue

Write-Host "Eliminando la regla de Firewall..." -ForegroundColor Yellow

Remove-NetFirewallRule -DisplayName "HomeCare Enterprise" -ErrorAction SilentlyContinue

if ($BorrarDatos) {
    Write-Host "Eliminando la carpeta de instalacion COMPLETA (incluye la base de datos)..." -ForegroundColor Red
    Remove-Item -Path $CarpetaInstalacion -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "Listo. El programa y todos sus datos fueron eliminados." -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "El programa fue desinstalado (ya no arranca con Windows)." -ForegroundColor Green
    Write-Host "La carpeta '$CarpetaInstalacion' NO se elimino, para conservar la base de datos y los archivos."
    Write-Host "Si quiere borrar TODO (incluida la base de datos), vuelva a ejecutar este script con -BorrarDatos"
}

Read-Host "Presione ENTER para cerrar"
