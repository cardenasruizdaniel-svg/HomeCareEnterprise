@echo off
REM =========================================================
REM HomeCare Enterprise - Abrir el programa
REM
REM El servidor normalmente ya arranca solo cada vez que
REM inicia sesion en Windows (quedo configurado por el
REM instalador). Pero por si acaso no esta corriendo (por
REM ejemplo, si se cerro la ventana del servidor sin cerrar
REM sesion), este icono tambien es capaz de arrancarlo el
REM mismo, con una ventana visible (nunca oculta/minimizada,
REM porque eso queda bloqueado en algunos equipos).
REM =========================================================

set "CARPETA=%~dp0"
set "CARPETA=%CARPETA:~0,-1%"
set "PUERTO=8088"
set "URL=http://localhost:%PUERTO%/login"

netstat -an | findstr ":%PUERTO% " | findstr "LISTENING" >nul 2>&1
if %errorlevel% == 0 (
    start "" "%URL%"
    exit /b
)

echo El servidor no esta corriendo todavia. Arrancandolo ahora...
start "HomeCare Enterprise - Servidor" "%CARPETA%\deploy\windows\arrancar_servidor.bat" "%CARPETA%" %PUERTO%

set "INTENTOS=0"
:esperar
timeout /t 2 /nobreak >nul
set /a INTENTOS+=1
netstat -an | findstr ":%PUERTO% " | findstr "LISTENING" >nul 2>&1
if %errorlevel% == 0 goto :listo
if %INTENTOS% GEQ 45 goto :agotado
goto :esperar

:listo
start "" "%URL%"
exit /b

:agotado
echo.
echo El servidor esta tardando mas de lo normal en iniciar.
echo Revise si se abrio una ventana nueva llamada "HomeCare Enterprise - Servidor"
echo y que no muestre ningun error ahi.
echo.
pause
exit /b
