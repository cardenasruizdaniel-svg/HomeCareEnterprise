#!/bin/bash
# =========================================================
# HomeCare Enterprise - Desinstalador para macOS
# Uso: sudo bash desinstalar_mac.sh [--borrar-datos]
# =========================================================

set -e

CARPETA_INSTALACION="/usr/local/homecare-enterprise"
NOMBRE_DAEMON="com.homecare.enterprise"
ARCHIVO_PLIST="/Library/LaunchDaemons/${NOMBRE_DAEMON}.plist"

if [ "$EUID" -ne 0 ]; then
  echo "Este script debe ejecutarse con sudo."
  exit 1
fi

echo "Deteniendo el servicio..."
launchctl unload "$ARCHIVO_PLIST" 2>/dev/null || true
rm -f "$ARCHIVO_PLIST"

if [ "$1" = "--borrar-datos" ]; then
  echo "Eliminando la carpeta de instalacion COMPLETA (incluye la base de datos)..."
  rm -rf "$CARPETA_INSTALACION"
  echo "Listo. El programa y todos sus datos fueron eliminados."
else
  echo ""
  echo "El programa fue desinstalado (ya no arranca con el equipo)."
  echo "La carpeta '$CARPETA_INSTALACION' NO se elimino, para conservar la base de datos."
  echo "Si quiere borrar TODO, ejecute: sudo bash $0 --borrar-datos"
fi
