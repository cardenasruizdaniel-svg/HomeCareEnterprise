@echo off
REM =========================================================
REM HomeCare Enterprise - Reiniciar base de datos en blanco
REM Doble clic para dejar el sistema sin pacientes ni datos de
REM prueba, CONSERVANDO el usuario administrador.
REM Se guarda una copia de seguridad automatica antes de borrar.
REM =========================================================

set "CARPETA=%~dp0"
set "CARPETA=%CARPETA:~0,-1%"

echo.
echo =========================================================
echo   HomeCare Enterprise - Reiniciar base de datos en blanco
echo =========================================================
echo.
echo   ADVERTENCIA: esto va a borrar TODOS los pacientes,
echo   profesionales, visitas e historias clinicas actuales.
echo   El usuario administrador SI se conserva.
echo   Se guarda una copia de seguridad automatica antes.
echo.
echo   IMPORTANTE: cierre el programa (que no este corriendo)
echo   antes de continuar, o esta operacion puede fallar.
echo.
set /p CONFIRMAR="Escriba SI (en mayusculas) para continuar, o cierre esta ventana para cancelar: "

if not "%CONFIRMAR%"=="SI" (
    echo Operacion cancelada.
    pause
    exit /b
)

cd /d "%CARPETA%"
"%CARPETA%\venv\Scripts\python.exe" reiniciar_base_datos.py

echo.
pause
