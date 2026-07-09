# =========================================================
# HomeCare Enterprise - Crea el acceso directo del escritorio
# =========================================================

param(
    [string]$CarpetaInstalacion
)

$escritorio = [Environment]::GetFolderPath('Desktop')
$shell = New-Object -ComObject WScript.Shell
$directo = $shell.CreateShortcut("$escritorio\HomeCare Enterprise.lnk")
$directo.TargetPath = "$CarpetaInstalacion\Abrir_HomeCareEnterprise.bat"
$directo.WorkingDirectory = $CarpetaInstalacion
$directo.IconLocation = "$CarpetaInstalacion\deploy\windows\homecare_icono.ico"
$directo.Description = "Abrir HomeCare Enterprise"
$directo.Save()

Write-Host ""
Write-Host "Listo. Ya deberia aparecer el icono 'HomeCare Enterprise' en tu escritorio." -ForegroundColor Green
