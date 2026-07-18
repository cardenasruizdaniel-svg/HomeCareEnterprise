#!/bin/bash
# =========================================================
# HomeCare Enterprise - Instalador (macOS)
# Doble clic en este archivo para instalar el programa.
# Pedira su contraseña de administrador.
# =========================================================

cd "$(dirname "${BASH_SOURCE[0]}")"

echo "Este instalador necesita permisos de administrador."
echo "Se le pedira su contraseña de Mac a continuación."
echo ""

sudo bash "deploy/macos/instalar_mac.sh"
