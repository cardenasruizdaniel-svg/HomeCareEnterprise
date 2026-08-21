@echo off
REM Ver la direccion externa actual del tunel -- doble clic y listo.
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "ver_direccion_externa.ps1"
