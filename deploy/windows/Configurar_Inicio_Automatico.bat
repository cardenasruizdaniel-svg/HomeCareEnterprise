@echo off
REM =========================================================
REM HomeCare Enterprise - Configurar inicio automatico
REM (correr UNA sola vez, con doble clic)
REM =========================================================
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "configurar_inicio_automatico.ps1"
