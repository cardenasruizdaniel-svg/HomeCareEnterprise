@echo off
REM =========================================================
REM HomeCare Enterprise - Crea el acceso directo del escritorio
REM Doble clic en este archivo UNA SOLA VEZ para que aparezca
REM el ícono de HomeCare Enterprise en tu escritorio.
REM =========================================================

set "CARPETA=%~dp0"
set "CARPETA=%CARPETA:~0,-1%"

powershell -NoProfile -ExecutionPolicy Bypass -File "%CARPETA%\deploy\windows\crear_acceso_directo.ps1" -CarpetaInstalacion "%CARPETA%"

pause
