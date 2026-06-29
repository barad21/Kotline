$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

& "$Root\scripts\build_windows.ps1"

$Iscc = Get-Command iscc -ErrorAction SilentlyContinue
if (-not $Iscc) {
    $DefaultIscc = "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe"
    if (Test-Path $DefaultIscc) {
        $Iscc = Get-Command $DefaultIscc
    }
}
if (-not $Iscc) {
    throw "Inno Setup not found. Install from https://jrsoftware.org/isinfo.php or add iscc to PATH."
}

& $Iscc.Source "$Root\packaging\windows\Kotline.iss"

Write-Host "Installer complete:"
Write-Host "  $Root\dist\installer\Kotline-Setup-0.1.0.exe"
