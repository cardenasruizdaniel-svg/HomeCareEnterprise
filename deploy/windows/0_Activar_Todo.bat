@echo off
REM =========================================================
REM HomeCare Enterprise - Activar TODO con un clic
REM (Programa local + Acceso externo por tunel)
REM
REM Este es el archivo que se usa en el dia a dia: un solo
REM doble clic abre DOS ventanas -- una con el programa
REM corriendo, y otra con el tunel de acceso externo ya
REM activo -- sin tener que escribir ningun comando.
REM
REM Requisito: haber configurado ngrok una sola vez de
REM antemano (ver el manual). Si no esta instalado/configurado,
REM la ventana del tunel se lo va a avisar con instrucciones.
REM =========================================================

cd /d "%~dp0"

echo.
echo ===========================================================
echo   HomeCare Enterprise - Activando el programa completo
echo ===========================================================
echo.
echo   Se van a abrir DOS ventanas nuevas:
echo     1. El programa (no la cierre mientras lo este usando)
echo     2. El acceso externo (revise ahi la direccion https)
echo.
echo   Esta ventana se puede cerrar despues de unos segundos.
echo ===========================================================
echo.

start "HomeCare - Programa" cmd /k "1_Iniciar_Programa_Local.bat"

echo [ .. ] Esperando a que el programa termine de arrancar...
timeout /t 12 /nobreak >nul

start "HomeCare - Acceso Externo" cmd /k "2_Abrir_Acceso_Externo.bat"

echo.
echo [OK] Listo. Revise la ventana "HomeCare - Acceso Externo"
echo      para ver la direccion publica de esta sesion.
echo.
timeout /t 5
