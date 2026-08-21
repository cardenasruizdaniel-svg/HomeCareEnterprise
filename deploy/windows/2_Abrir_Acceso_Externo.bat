@echo off
REM =========================================================
REM HomeCare Enterprise - Abrir acceso externo (tunel ngrok)
REM
REM Para usarlo: primero debe estar corriendo el programa
REM (con "1_Iniciar_Programa_Local.bat"), y DESPUES de eso,
REM doble clic sobre este archivo -- abre una direccion
REM publica (https://...) para entrar al programa desde
REM fuera de esta red (otro celular, otra oficina, etc.).
REM
REM Requiere tener ngrok instalado (Microsoft Store, o desde
REM ngrok.com/download) y su clave (authtoken) ya configurada
REM una sola vez -- ver el manual para los detalles.
REM =========================================================

set "PUERTO=8000"

echo.
echo ===========================================================
echo   HomeCare Enterprise - Acceso externo
echo ===========================================================
echo.

where ngrok >nul 2>nul
if errorlevel 1 (
    echo [ERROR] No se encontro ngrok instalado en este equipo.
    echo.
    echo         Instalelo de una de estas dos formas:
    echo           1^) Desde la Microsoft Store, buscando "ngrok"
    echo           2^) Descargandolo de https://ngrok.com/download
    echo.
    echo         Vea el manual de "Instalacion Local y Acceso
    echo         Externo" para los pasos completos.
    echo.
    pause
    exit /b 1
)

echo [ .. ] Verifique que la ventana del programa ^(paso 1^) ya
echo        este corriendo y muestre "Sistema listo" antes de
echo        continuar.
echo.
echo [ .. ] Abriendo el tunel hacia el puerto %PUERTO%...
echo.
echo ===========================================================
echo   Cuando aparezca la linea "Forwarding", esa direccion
echo   https://....ngrok-free.dev (o .app) es la que se usa
echo   para entrar desde fuera de esta red.
echo.
echo   Con el plan gratis, esa direccion CAMBIA cada vez que
echo   se abre este archivo -- revisela cada vez.
echo.
echo   NO CIERRE ESTA VENTANA mientras necesite el acceso
echo   externo activo.
echo ===========================================================
echo.

ngrok http %PUERTO%

echo.
echo El tunel se cerro. La direccion externa ya no funciona.
pause
