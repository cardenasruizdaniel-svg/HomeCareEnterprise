@echo off
REM =========================================================
REM HomeCare Enterprise - Arranque del servidor (Windows)
REM Version en .bat: evita cualquier restriccion de politica
REM de ejecucion de scripts de PowerShell que pueda tener el
REM equipo (algunos antivirus o configuraciones de fabricante
REM bloquean los .ps1 incluso con -ExecutionPolicy Bypass).
REM Este archivo lo usa el acceso directo de inicio
REM automatico. No debe ejecutarse manualmente salvo pruebas.
REM =========================================================

setlocal enabledelayedexpansion

REM Fuerza a Python a usar UTF-8 siempre, incluso cuando su
REM salida se redirige a un archivo (como aqui abajo). Sin
REM esto, Windows usa una codificacion antigua (cp1252) para
REM la salida redirigida, que no entiende tildes ni simbolos
REM especiales, y el programa se cae en silencio al imprimir
REM cualquiera de ellos.
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"

REM Parametros: %1 = carpeta de instalacion, %2 = puerto
set "CARPETA=%~1"
set "PUERTO=%~2"

if "%CARPETA%"=="" set "CARPETA=C:\HomeCareEnterprise"
if "%PUERTO%"=="" set "PUERTO=8000"

REM Archivo de ultimo recurso: se escribe SIEMPRE, antes que
REM cualquier otra cosa.
echo [%date% %time%] Script .bat de arranque ejecutado. Usuario: %USERNAME%. Carpeta: %CARPETA%. Puerto: %PUERTO% >> "%CARPETA%\ULTIMO_INTENTO_ARRANQUE.txt"

if not exist "%CARPETA%\logs" mkdir "%CARPETA%\logs"

set "LOG=%CARPETA%\logs\servidor.log"
set "PYTHON_EXE=%CARPETA%\venv\Scripts\python.exe"

if not exist "%PYTHON_EXE%" (
    echo [%date% %time%] ERROR: no se encontro Python en %PYTHON_EXE% >> "%CARPETA%\logs\error_arranque.log"
    exit /b 1
)

cd /d "%CARPETA%"

:bucle
echo [%date% %time%] Iniciando HomeCare Enterprise en el puerto %PUERTO%... >> "%LOG%"

"%PYTHON_EXE%" -u -m uvicorn main:app --host 0.0.0.0 --port %PUERTO% --workers 1 >> "%LOG%" 2>&1

echo [%date% %time%] El servidor se detuvo. Reintentando en 10 segundos... >> "%LOG%"

timeout /t 10 /nobreak >nul

goto bucle
