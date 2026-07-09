@echo off
REM =========================================================
REM HomeCare Enterprise - Instalador (Windows)
REM Doble clic en este archivo para instalar el programa.
REM Pedira permisos de Administrador automaticamente.
REM =========================================================

:: Verificar si ya se esta ejecutando como Administrador
net session >nul 2>&1
if %errorLevel% == 0 (
    goto :ejecutar
) else (
    echo Solicitando permisos de Administrador...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

:ejecutar
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "deploy\windows\instalar_windows.ps1"
pause
