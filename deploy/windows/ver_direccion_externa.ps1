# =========================================================
# HomeCare Enterprise - Ver la direccion externa actual
#
# Como la direccion (https://...) cambia cada vez que se abre
# el tunel (con el plan gratis de ngrok), este script la
# consulta directamente al panel local de ngrok y la muestra
# clara -- sin tener que andar buscando en ninguna ventana de
# PowerShell.
#
# Solo funciona si el tunel ya esta activo (con
# "0_Activar_Todo.bat" o "2_Abrir_Acceso_Externo.bat").
# =========================================================

Write-Host ""
Write-Host "==========================================================="
Write-Host "  HomeCare Enterprise - Direccion externa actual"
Write-Host "==========================================================="
Write-Host ""

try {
    $respuesta = Invoke-RestMethod -Uri "http://127.0.0.1:4040/api/tunnels" -TimeoutSec 3
    $tunel = $respuesta.tunnels | Where-Object { $_.proto -eq "https" } | Select-Object -First 1

    if ($tunel) {
        $url = $tunel.public_url

        Write-Host "  Direccion para entrar desde afuera:" -ForegroundColor Cyan
        Write-Host "  $url" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "  App movil:  $url/app" -ForegroundColor Yellow
        Write-Host ""

        Set-Clipboard -Value $url
        Write-Host "  (Ya se copio al portapapeles -- puede pegarla directo con Ctrl+V)" -ForegroundColor Gray

        Start-Process $url
    } else {
        Write-Host "  El tunel esta activo pero no se encontro una direccion https." -ForegroundColor Red
    }
} catch {
    Write-Host "  No se encontro el tunel activo en este momento." -ForegroundColor Red
    Write-Host "  Verifique que este corriendo (con 0_Activar_Todo.bat), y que hayan" -ForegroundColor Gray
    Write-Host "  pasado unos segundos desde que arranco." -ForegroundColor Gray
}

Write-Host ""
Read-Host "Presione Enter para cerrar"
