$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

if (-not (Test-Path .venv\Scripts\Activate.ps1)) {
    python -m venv .venv
}
. .venv\Scripts\Activate.ps1

pip install -e ".[desktop,build]" -q
python scripts/generate_icons.py
pyinstaller packaging\kesit.spec --noconfirm

Write-Host "Build complete:"
Write-Host "  Binary: $Root\dist\Kotline\Kotline.exe"
Write-Host "  Folder: $Root\dist\Kotline\"
