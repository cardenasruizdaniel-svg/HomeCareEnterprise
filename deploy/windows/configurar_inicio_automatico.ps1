# =========================================================
# HomeCare Enterprise - Configurar inicio automatico
# (Programa local + Acceso externo por tunel)
#
# Se ejecuta UNA sola vez. Despues de correrlo:
#   - Cada vez que se prenda este computador y alguien inicie
#     sesion en Windows, el programa Y el tunel de acceso
#     externo arrancan solos -- sin abrir PowerShell a mano.
#   - Quedan dos iconos en el Escritorio para el uso diario:
#       "HomeCare - Iniciar Todo"      (por si hace falta
#        reiniciarlo sin cerrar sesion de Windows)
#       "HomeCare - Ver Direccion Externa" (para copiar la
#        direccion https:// actual, sin buscarla en ninguna
#        ventana)
#
# Requisito: haber configurado ngrok una sola vez de antemano
# (ver el Manual de Instalacion Local y Acceso Externo).
# =========================================================

function Escribir-Titulo($texto) {
    Write-Host ""
    Write-Host "==========================================================" -ForegroundColor Cyan
    Write-Host " $texto" -ForegroundColor Cyan
    Write-Host "==========================================================" -ForegroundColor Cyan
}
function Escribir-Ok($texto)   { Write-Host "  [OK] $texto" -ForegroundColor Green }
function Escribir-Info($texto) { Write-Host "  [ .. ] $texto" -ForegroundColor Yellow }

Escribir-Titulo "HomeCare Enterprise - Configurar inicio automatico"

$CarpetaDeploy = $PSScriptRoot
$IconoPersonalizado = Join-Path $CarpetaDeploy "homecare_icono.ico"

$wshShell = New-Object -ComObject WScript.Shell

# ---------------------------------------------------------
# 1. ACCESO DIRECTO EN LA CARPETA DE INICIO DE WINDOWS
#    (arranca solo, cada vez que se inicia sesion)
# ---------------------------------------------------------

Escribir-Titulo "Configurando el arranque automatico"

$carpetaInicio = [Environment]::GetFolderPath("Startup")
$rutaAccesoInicio = Join-Path $carpetaInicio "HomeCare Enterprise (automatico).lnk"

$accesoInicio = $wshShell.CreateShortcut($rutaAccesoInicio)
$accesoInicio.TargetPath = Join-Path $CarpetaDeploy "0_Activar_Todo.bat"
$accesoInicio.WorkingDirectory = $CarpetaDeploy
$accesoInicio.WindowStyle = 7   # 7 = minimizada -- arranca sola sin taparle la pantalla
                                 # a la persona apenas prende el computador, pero sigue
                                 # siendo una ventana real y visible en la barra de tareas
                                 # (no oculta del todo, para no verse sospechosa ante un
                                 # antivirus).
if (Test-Path $IconoPersonalizado) { $accesoInicio.IconLocation = $IconoPersonalizado }
$accesoInicio.Description = "HomeCare Enterprise - arranca el programa y el acceso externo solos"
$accesoInicio.Save()

Escribir-Ok "Se creo el arranque automatico en: $rutaAccesoInicio"
Escribir-Info "(Correra minimizada cada vez que se inicie sesion en este usuario de Windows.)"

# ---------------------------------------------------------
# 2. ACCESOS DIRECTOS EN EL ESCRITORIO (uso manual del dia a dia)
# ---------------------------------------------------------

Escribir-Titulo "Creando accesos directos en el Escritorio"

$Escritorio = [Environment]::GetFolderPath("Desktop")

$accesoIniciar = $wshShell.CreateShortcut((Join-Path $Escritorio "HomeCare - Iniciar Todo.lnk"))
$accesoIniciar.TargetPath = Join-Path $CarpetaDeploy "0_Activar_Todo.bat"
$accesoIniciar.WorkingDirectory = $CarpetaDeploy
if (Test-Path $IconoPersonalizado) { $accesoIniciar.IconLocation = $IconoPersonalizado }
$accesoIniciar.Description = "Arranca el programa HomeCare y el acceso externo"
$accesoIniciar.Save()
Escribir-Ok "Acceso directo: HomeCare - Iniciar Todo"

$accesoDireccion = $wshShell.CreateShortcut((Join-Path $Escritorio "HomeCare - Ver Direccion Externa.lnk"))
$accesoDireccion.TargetPath = Join-Path $CarpetaDeploy "3_Ver_Direccion_Externa.bat"
$accesoDireccion.WorkingDirectory = $CarpetaDeploy
if (Test-Path $IconoPersonalizado) { $accesoDireccion.IconLocation = $IconoPersonalizado }
$accesoDireccion.Description = "Muestra y copia la direccion https:// actual para entrar desde afuera"
$accesoDireccion.Save()
Escribir-Ok "Acceso directo: HomeCare - Ver Direccion Externa"

# ---------------------------------------------------------
# 3. ARRANCAR AHORA MISMO (para no tener que reiniciar el
#    computador y probar de inmediato)
# ---------------------------------------------------------

Escribir-Titulo "Listo"
Write-Host ""
Write-Host "  A partir de ahora, el programa y el acceso externo van a" -ForegroundColor White
Write-Host "  arrancar solos cada vez que se prenda este computador." -ForegroundColor White
Write-Host ""
Write-Host "  Para arrancarlos ya mismo (sin reiniciar el computador)," -ForegroundColor White
Write-Host "  use el nuevo icono del Escritorio: 'HomeCare - Iniciar Todo'." -ForegroundColor White
Write-Host ""

Read-Host "Presione Enter para cerrar"
