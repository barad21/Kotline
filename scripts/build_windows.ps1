$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root
if (Test-Path .venv\Scripts\Activate.ps1) { . .venv\Scripts\Activate.ps1 }
pip install -e ".[desktop,build]" -q
pyinstaller packaging\kesit.spec --noconfirm
Write-Host "Build complete: $Root\dist\Kesit\"
