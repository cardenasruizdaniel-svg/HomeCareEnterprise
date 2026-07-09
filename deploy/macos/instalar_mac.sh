#!/bin/bash
# =========================================================
# HomeCare Enterprise - Instalador para macOS
# =========================================================
#
# Que hace este script (en orden):
#   1. Verifica que se ejecute con sudo (permisos de admin).
#   2. Instala Homebrew si no existe (gestor de paquetes
#      estandar de macOS).
#   3. Instala Python 3.11+ via Homebrew si hace falta.
#   4. Copia el programa a /usr/local/homecare-enterprise.
#   5. Crea un entorno virtual e instala las dependencias.
#   6. Crea el archivo .env a partir de .env.example.
#   7. Registra un LaunchDaemon para que el programa arranque
#      solo con el equipo, sin necesidad de iniciar sesion
#      (equivalente a un servicio de Windows).
#   8. Inicia el programa inmediatamente y verifica que
#      responda.
#
# Uso:
#   Doble clic en Instalar_macOS.command
#   (o desde Terminal: sudo bash deploy/macos/instalar_mac.sh)
#
# =========================================================

set -e

CARPETA_INSTALACION="/usr/local/homecare-enterprise"
PUERTO=8000
NOMBRE_DAEMON="com.homecare.enterprise"
ARCHIVO_PLIST="/Library/LaunchDaemons/${NOMBRE_DAEMON}.plist"

titulo() {
  echo ""
  echo "=========================================================="
  echo " $1"
  echo "=========================================================="
}

ok()    { echo "  [OK] $1"; }
info()  { echo "  [..] $1"; }
error() { echo "  [ERROR] $1"; }

# ---------------------------------------------------------
# 1. VERIFICAR PERMISOS
# ---------------------------------------------------------

titulo "HomeCare Enterprise - Instalador para macOS"

if [ "$EUID" -ne 0 ]; then
  error "Este instalador necesita permisos de administrador."
  error "Ejecute: sudo bash \"$0\""
  exit 1
fi

ok "Ejecutando con permisos de administrador."

# Usuario real que invoco sudo (para instalar Homebrew, que no
# debe correr como root)
USUARIO_REAL="${SUDO_USER:-$(whoami)}"

# ---------------------------------------------------------
# 2. HOMEBREW
# ---------------------------------------------------------

titulo "Verificando Homebrew"

RUTA_BREW=""
if command -v brew >/dev/null 2>&1; then
  RUTA_BREW="$(command -v brew)"
elif [ -x "/opt/homebrew/bin/brew" ]; then
  RUTA_BREW="/opt/homebrew/bin/brew"
elif [ -x "/usr/local/bin/brew" ]; then
  RUTA_BREW="/usr/local/bin/brew"
fi

if [ -z "$RUTA_BREW" ]; then
  info "Homebrew no encontrado. Instalando (esto puede tardar varios minutos)..."
  sudo -u "$USUARIO_REAL" /bin/bash -c \
    "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

  if [ -x "/opt/homebrew/bin/brew" ]; then
    RUTA_BREW="/opt/homebrew/bin/brew"
  else
    RUTA_BREW="/usr/local/bin/brew"
  fi
fi

ok "Homebrew disponible en: $RUTA_BREW"

# ---------------------------------------------------------
# 3. PYTHON
# ---------------------------------------------------------

titulo "Verificando Python"

if ! command -v python3 >/dev/null 2>&1 || \
   [ "$(python3 -c 'import sys; print(1 if sys.version_info >= (3,11) else 0)')" != "1" ]; then
  info "Instalando Python 3.12 via Homebrew..."
  sudo -u "$USUARIO_REAL" "$RUTA_BREW" install python@3.12
fi

PYTHON_BIN="$(command -v python3)"
ok "Python disponible: $($PYTHON_BIN --version)"

# ---------------------------------------------------------
# 4. COPIAR EL PROGRAMA
# ---------------------------------------------------------

titulo "Copiando archivos del programa"

CARPETA_ORIGEN="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

mkdir -p "$CARPETA_INSTALACION"

info "Copiando de '$CARPETA_ORIGEN' a '$CARPETA_INSTALACION' ..."

rsync -a --exclude ".git" --exclude "__pycache__" --exclude "venv" --exclude "exports" --exclude "database.db" \
  "$CARPETA_ORIGEN"/ "$CARPETA_INSTALACION"/

ok "Archivos copiados."

# ---------------------------------------------------------
# 5. ENTORNO VIRTUAL + DEPENDENCIAS
# ---------------------------------------------------------

titulo "Instalando dependencias de Python"

cd "$CARPETA_INSTALACION"

if [ ! -d "venv" ]; then
  info "Creando entorno virtual..."
  "$PYTHON_BIN" -m venv venv
fi

info "Actualizando pip..."
./venv/bin/python -m pip install --upgrade pip --quiet

info "Instalando dependencias (requirements.txt)..."
./venv/bin/pip install -r requirements.txt --quiet

ok "Dependencias instaladas."

# ---------------------------------------------------------
# 6. ARCHIVO .env
# ---------------------------------------------------------

titulo "Configuracion (.env)"

if [ ! -f "$CARPETA_INSTALACION/.env" ]; then
  cp "$CARPETA_INSTALACION/.env.example" "$CARPETA_INSTALACION/.env"
  ok "Se creo el archivo .env a partir de .env.example."
  info "IMPORTANTE: edite $CARPETA_INSTALACION/.env para configurar correo, WhatsApp, RIPS, etc."
else
  ok "Ya existia un archivo .env; no se modifico."
fi

# Dar permisos al usuario real sobre la carpeta instalada
chown -R "$USUARIO_REAL" "$CARPETA_INSTALACION"

# ---------------------------------------------------------
# 7. LAUNCHDAEMON (inicio automatico, equivalente a servicio)
# ---------------------------------------------------------

titulo "Configurando inicio automatico"

mkdir -p "$CARPETA_INSTALACION/logs"

cat > "$ARCHIVO_PLIST" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>${NOMBRE_DAEMON}</string>

    <key>ProgramArguments</key>
    <array>
        <string>${CARPETA_INSTALACION}/venv/bin/python</string>
        <string>-m</string>
        <string>uvicorn</string>
        <string>main:app</string>
        <string>--host</string>
        <string>0.0.0.0</string>
        <string>--port</string>
        <string>${PUERTO}</string>
    </array>

    <key>WorkingDirectory</key>
    <string>${CARPETA_INSTALACION}</string>

    <key>RunAtLoad</key>
    <true/>

    <key>KeepAlive</key>
    <true/>

    <key>StandardOutPath</key>
    <string>${CARPETA_INSTALACION}/logs/servidor.log</string>

    <key>StandardErrorPath</key>
    <string>${CARPETA_INSTALACION}/logs/servidor.log</string>
</dict>
</plist>
PLIST

chown root:wheel "$ARCHIVO_PLIST"
chmod 644 "$ARCHIVO_PLIST"

# Si ya existia cargado, descargarlo primero
launchctl unload "$ARCHIVO_PLIST" 2>/dev/null || true

launchctl load "$ARCHIVO_PLIST"

ok "LaunchDaemon '${NOMBRE_DAEMON}' creado (se inicia automaticamente con el equipo)."

# ---------------------------------------------------------
# 8. VERIFICAR QUE RESPONDA
# ---------------------------------------------------------

titulo "Iniciando HomeCare Enterprise"

info "Esperando que el servidor responda..."

LISTO=0
for i in $(seq 1 20); do
  sleep 2
  if curl -sf "http://localhost:${PUERTO}/health" >/dev/null 2>&1; then
    LISTO=1
    break
  fi
done

if [ "$LISTO" = "1" ]; then
  ok "El servidor esta corriendo correctamente."
else
  error "El servidor no respondio a tiempo. Revise el log en: $CARPETA_INSTALACION/logs/servidor.log"
fi

# ---------------------------------------------------------
# RESUMEN FINAL
# ---------------------------------------------------------

IP_LOCAL="$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null || echo "")"

titulo "Instalacion completada"

echo ""
echo "  Carpeta de instalacion : $CARPETA_INSTALACION"
echo "  Acceso desde este equipo:  http://localhost:${PUERTO}"
if [ -n "$IP_LOCAL" ]; then
echo "  Acceso desde la red:       http://${IP_LOCAL}:${PUERTO}"
fi
echo "  Usuario inicial:           admin"
echo "  Contraseña inicial:        admin123  (cambiela de inmediato)"
echo "  Configuracion (.env):      $CARPETA_INSTALACION/.env"
echo "  Registro (logs):           $CARPETA_INSTALACION/logs/servidor.log"
echo ""
echo "  El programa se iniciara automaticamente cada vez que encienda este equipo."
echo ""
echo "  Nota sobre el Firewall de macOS: si tiene activado el Firewall de la"
echo "  aplicacion (Preferencias del Sistema > Red > Firewall) y quiere acceder"
echo "  desde otros equipos de la red, autorice conexiones entrantes para Python"
echo "  cuando el sistema lo solicite, o agregue una excepcion manual."
echo ""

read -p "Presione ENTER para cerrar..."
