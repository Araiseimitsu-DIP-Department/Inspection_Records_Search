# onefile exe ビルド — 実処理は scripts/pyinstaller_build.py（日本語パス・PS 文字コード差の回避）

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

$Py = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $Py)) {
    Write-Error ".venv not found. Create venv and pip install -r requirements.txt first."
}

& $Py (Join-Path $Root "scripts\pyinstaller_build.py")
