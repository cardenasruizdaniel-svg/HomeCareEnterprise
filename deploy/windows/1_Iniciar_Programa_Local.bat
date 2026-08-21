@echo off
REM =========================================================
REM HomeCare Enterprise - Iniciar el programa en este equipo
REM
REM Para usarlo: doble clic sobre este archivo. Deja la
REM ventana abierta -- ahi se ve el programa funcionando, y
REM cerrarla apaga el programa.
REM
REM Detecta solo si el programa esta instalado con el
REM instalador completo (con su propio Python en la carpeta
REM "venv") o si se esta corriendo directo desde una copia de
REM la carpeta del proyecto -- y usa el que corresponda, sin
REM que la persona tenga que saber la diferencia.
REM =========================================================

setlocal enabledelayedexpansion
REM deploy/windows/ esta DOS niveles abajo de la raiz del
REM proyecto (donde vive main.py) -- hay que subir dos veces,
REM no una sola.
cd /d "%~dp0..\.."

set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"
set "PUERTO=8000"

echo.
echo ===========================================================
echo   HomeCare Enterprise - Iniciando el programa localmente
echo ===========================================================
echo.

if exist "venv\Scripts\python.exe" (
    echo [OK] Usando el Python del instalador ^(venv^)...
    set "PYTHON_EXE=venv\Scripts\python.exe"
) else (
    echo [ .. ] No se encontro una instalacion completa ^(venv^) en esta carpeta.
    echo [ .. ] Se va a usar el Python del sistema en su lugar.
    where python >nul 2>nul
    if errorlevel 1 (
        echo.
        echo [ERROR] No se encontro Python instalado en este equipo.
        echo         Instale Python 3.11 o superior desde https://python.org
        echo         y vuelva a intentarlo.
        echo.
        pause
        exit /b 1
    )
    set "PYTHON_EXE=python"
)

echo [ .. ] Verificando que las dependencias esten instaladas...
%PYTHON_EXE% -m pip install -r requirements.txt --quiet --disable-pip-version-check >nul 2>nul

echo.
echo ===========================================================
echo   El programa va a quedar disponible en:
echo   http://localhost:%PUERTO%
echo.
echo   NO CIERRE ESTA VENTANA mientras este usando el programa.
echo   Para apagarlo, simplemente cierre esta ventana.
echo ===========================================================
echo.

%PYTHON_EXE% -m uvicorn main:app --host 0.0.0.0 --port %PUERTO%

echo.
echo El programa se detuvo.
pause
