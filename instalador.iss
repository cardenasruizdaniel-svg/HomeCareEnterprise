; =========================================================
; HomeCare Enterprise - Instalador de Windows
; =========================================================
;
; Este archivo lo usa Inno Setup (gratuito) para armar el
; instalador final -- el .exe que la gente va a abrir con
; doble clic, con el asistente tipo "Siguiente, Siguiente,
; Instalar", igual que instalar Office.
;
; CÓMO USARLO (en una computadora con Windows):
;
;   1. Instale Inno Setup (gratis): https://jrsoftware.org/isdl.php
;
;   2. Antes de este paso, ya debe haber corrido:
;        pyinstaller homecare.spec
;      así que exista la carpeta:
;        dist\HomeCare Enterprise\
;
;   3. Abra este archivo (instalador.iss) con Inno Setup,
;      y presione "Compilar" (o Ctrl+F9).
;
;   4. El instalador final queda en la carpeta "Salida\",
;      con un nombre como:
;        HomeCare_Enterprise_Instalador.exe
;
;      Ese es el archivo que se comparte e instala en
;      cualquier computador con Windows -- no necesita tener
;      Python instalado, todo ya viene incluido.
; =========================================================

#define NombreApp "HomeCare Enterprise"
#define VersionApp "1.0.0"
#define Publicador "HomeCare del Quind\u00edo I.P.S."
#define CarpetaDist "dist\HomeCare Enterprise"

[Setup]
AppId={{8B6F2E1A-4C3D-4A9B-9E7F-1D2C3B4A5E6F}}
AppName={#NombreApp}
AppVersion={#VersionApp}
AppPublisher={#Publicador}
DefaultDirName={autopf}\{#NombreApp}
DefaultGroupName={#NombreApp}
DisableProgramGroupPage=yes
OutputDir=Salida
OutputBaseFilename=HomeCare_Enterprise_Instalador
Compression=lzma2
SolidCompression=yes
SetupIconFile=static\img\logo_homecare.ico
WizardStyle=modern
PrivilegesRequired=admin
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\{#NombreApp}.exe

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "iconoescritorio"; Description: "Crear un ícono en el Escritorio"; GroupDescription: "Accesos directos:"
Name: "iniciarautomatico"; Description: "Abrir HomeCare Enterprise cada vez que se encienda el computador"; GroupDescription: "Inicio automático:"; Flags: unchecked

[Files]
; Copia TODA la carpeta que generó PyInstaller (el programa completo, con Python y sus librerías ya incluidos)
Source: "{#CarpetaDist}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#NombreApp}"; Filename: "{app}\{#NombreApp}.exe"; IconFilename: "{app}\{#NombreApp}.exe"
Name: "{group}\Desinstalar {#NombreApp}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#NombreApp}"; Filename: "{app}\{#NombreApp}.exe"; IconFilename: "{app}\{#NombreApp}.exe"; Tasks: iconoescritorio
Name: "{userstartup}\{#NombreApp}"; Filename: "{app}\{#NombreApp}.exe"; Tasks: iniciarautomatico

[Run]
Filename: "{app}\{#NombreApp}.exe"; Description: "Abrir {#NombreApp} ahora"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Al desinstalar, se pregunta -- pero por defecto NO se borran los datos (base de datos, documentos subidos),
; para que si alguien reinstala una versión nueva no pierda su información. Esos datos quedan en:
;   %LOCALAPPDATA%\HomeCareEnterprise\
; y hay que borrarlos a mano si de verdad se quiere empezar de cero.

[Messages]
spanish.WelcomeLabel2=Este asistente va a instalar [name/ver] en este computador.%n%nSe recomienda cerrar las dem\u00e1s aplicaciones antes de continuar.
