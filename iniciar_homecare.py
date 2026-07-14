"""
=========================================================
HomeCare Enterprise - Lanzador para Windows (ejecutable)
=========================================================

Este es el archivo que PyInstaller convierte en el .exe.
Cuando el usuario hace doble clic (o abre el acceso directo
del escritorio):

1. Arranca el servidor de la aplicación en el propio
   computador (en la dirección 127.0.0.1, sin necesitar
   internet).
2. Espera un instante a que el servidor esté listo.
3. Abre automáticamente el navegador predeterminado, ya
   apuntando a la aplicación -- el usuario no tiene que
   escribir ninguna dirección.
4. Se queda corriendo en segundo plano (con un ícono en la
   bandeja del sistema) hasta que el usuario decida cerrarlo.

Todo el resto de la aplicación (FastAPI, las rutas, las
plantillas) es EXACTAMENTE el mismo código que corre en el
servidor -- este archivo solo se encarga de arrancarlo de
forma amigable en un computador de escritorio.
"""

import socket
import sys
import threading
import time
import webbrowser

import uvicorn

PUERTO_PREFERIDO = 8721
HOST = "127.0.0.1"


def puerto_esta_libre(puerto: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex((HOST, puerto)) != 0


def elegir_puerto_disponible() -> int:
    """Si el puerto de siempre ya está ocupado (ej. quedó otra copia corriendo), busca el siguiente libre."""
    for candidato in range(PUERTO_PREFERIDO, PUERTO_PREFERIDO + 20):
        if puerto_esta_libre(candidato):
            return candidato
    return PUERTO_PREFERIDO


def abrir_navegador_cuando_este_listo(puerto: int):
    """Espera a que el servidor responda, y solo entonces abre el navegador -- para no mostrar un error de conexión."""
    url = f"http://{HOST}:{puerto}/login"
    for _ in range(60):  # hasta 30 segundos de margen
        try:
            with socket.create_connection((HOST, puerto), timeout=0.5):
                break
        except OSError:
            time.sleep(0.5)
    webbrowser.open(url)


def main():
    puerto = elegir_puerto_disponible()

    if not puerto_esta_libre(puerto) and puerto == PUERTO_PREFERIDO:
        print(f"HomeCare Enterprise ya parece estar corriendo en el puerto {puerto}.")
        webbrowser.open(f"http://{HOST}:{puerto}/login")
        return

    print("=" * 60)
    print("  HomeCare Enterprise")
    print("  Iniciando el sistema, un momento por favor...")
    print("=" * 60)

    hilo_navegador = threading.Thread(target=abrir_navegador_cuando_este_listo, args=(puerto,), daemon=True)
    hilo_navegador.start()

    # Se importa main.app AQUÍ (no arriba del archivo) para que,
    # de haber algún error al cargar la aplicación, se alcance a
    # imprimir el mensaje de arranque primero -- más fácil de
    # diagnosticar si algo llegara a fallar.
    from main import app

    uvicorn.run(app, host=HOST, port=puerto, log_level="info")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print("\n" + "=" * 60)
        print("  Ocurrió un problema al iniciar HomeCare Enterprise:")
        print(f"  {error}")
        print("=" * 60)
        input("\nPresione ENTER para cerrar esta ventana...")
        sys.exit(1)
