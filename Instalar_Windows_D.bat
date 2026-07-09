@echo off
REM =========================================================
REM HomeCare Enterprise - Instalador personalizado
REM Instala en: D:\HomeCareEnterprise
REM Puerto: 8088
REM
REM IMPORTANTE: este archivo debe ejecutarse YA como
REM Administrador (clic derecho -> "Ejecutar como
REM administrador", o abrirlo desde una ventana de
REM PowerShell/CMD que ya este en modo Administrador).
REM Ya NO intenta autoelevarse solo, porque ese paso
REM automatico puede quedar bloqueado en silencio por
REM Windows/el antivirus sin mostrar ningun aviso.
REM =========================================================

REM Se usa una verificacion de PowerShell directa (la misma
REM API de .NET) en vez de "net session" o "fltmc", porque en
REM algunos equipos (por politica corporativa o el antivirus)
REM esos comandos externos quedan bloqueados incluso para un
REM Administrador real, dando un falso "no es Administrador".
powershell -NoProfile -Command "if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) { exit 1 }"
if %errorLevel% NEQ 0 (
    echo.
    echo =========================================================
    echo   Este instalador necesita permisos de Administrador.
    echo =========================================================
    echo.
    echo   Ciérrelo, y vuelva a abrirlo de una de estas dos formas:
    echo.
    echo   OPCION A: clic derecho sobre este archivo, y elija
    echo             "Ejecutar como administrador".
    echo.
    echo   OPCION B: abra PowerShell como Administrador
    echo             (clic derecho en el boton de Inicio de
    echo             Windows -^> "Terminal (Administrador)"),
    echo             y ahi escriba:
    echo.
    echo             cd D:\HomeCareEnterprise
    echo             .\Instalar_Windows_D.bat
    echo.
    pause
    exit /b
)

cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "deploy\windows\instalar_windows.ps1" -CarpetaInstalacion "D:\HomeCareEnterprise" -Puerto 8088

echo.
echo Creando el acceso directo del escritorio...
powershell -NoProfile -ExecutionPolicy Bypass -File "D:\HomeCareEnterprise\deploy\windows\crear_acceso_directo.ps1" -CarpetaInstalacion "D:\HomeCareEnterprise"

pause
