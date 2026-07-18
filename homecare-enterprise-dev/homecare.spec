# -*- mode: python ; coding: utf-8 -*-
"""
=========================================================
HomeCare Enterprise - Especificación de PyInstaller
=========================================================

Este archivo le dice a PyInstaller CÓMO empaquetar la
aplicación completa en un ejecutable de Windows.

CÓMO USARLO (en una computadora con Windows):

  1. Instale Python 3.11 o 3.12 (https://python.org) --
     al instalarlo, marque la casilla "Add Python to PATH".

  2. Abra la carpeta del proyecto en una terminal (CMD o
     PowerShell) y ejecute:

       pip install -r requirements.txt
       pip install pyinstaller

  3. Ejecute:

       pyinstaller homecare.spec

  4. Cuando termine (puede tardar varios minutos, es una
     aplicación grande por el reconocimiento facial), va a
     quedar la aplicación lista en la carpeta:

       dist\\HomeCare Enterprise\\

     Ahí mismo, "HomeCare Enterprise.exe" ya funciona --
     puede probarlo con doble clic antes de armar el
     instalador final con Inno Setup (ver instalador.iss).

Se usa modo "un solo directorio" (no "un solo archivo") a
propósito: con "un solo archivo", el programa tendría que
descomprimirse por completo cada vez que se abre (varios
cientos de MB, por las librerías de reconocimiento facial),
lo cual sería muy lento. En modo carpeta, se descomprime UNA
sola vez al instalar, y después abre rápido cada vez.
"""

import os

block_cipher = None

RAIZ_PROYECTO = os.path.abspath(".")

datos_incluidos = [
    ("templates", "templates"),
    ("static", "static"),
    ("docs", "docs"),
]

# Solo se agregan las carpetas que de verdad existan en este
# proyecto (por si alguna no aplica en su copia).
datos_incluidos = [(origen, destino) for origen, destino in datos_incluidos if os.path.isdir(origen)]

analisis = Analysis(
    ["iniciar_homecare.py"],
    pathex=[RAIZ_PROYECTO],
    binaries=[],
    datas=datos_incluidos,
    hiddenimports=[
        "uvicorn.logging",
        "uvicorn.loops",
        "uvicorn.loops.auto",
        "uvicorn.protocols",
        "uvicorn.protocols.http",
        "uvicorn.protocols.http.auto",
        "uvicorn.protocols.websockets",
        "uvicorn.protocols.websockets.auto",
        "uvicorn.lifespan",
        "uvicorn.lifespan.on",
        "passlib.handlers.bcrypt",
        "multipart",
        "email.mime.multipart",
        "email.mime.text",
        "email.mime.base",
        "cv2",
        "PIL",
        "reportlab.pdfbase._fontdata",
        "openpyxl",
        "jinja2.ext",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(analisis.pure, analisis.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    analisis.scripts,
    [],
    exclude_binaries=True,
    name="HomeCare Enterprise",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,  # deja ver una ventana con el estado del servidor -- se puede pasar a False cuando ya esté probado y estable
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon="static/img/logo_homecare.ico" if os.path.isfile("static/img/logo_homecare.ico") else None,
)

coleccion = COLLECT(
    exe,
    analisis.binaries,
    analisis.zipfiles,
    analisis.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="HomeCare Enterprise",
)
