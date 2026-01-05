$ErrorActionPreference = 'Stop'

# Set UTF-8 encoding for output
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
chcp 65001 | Out-Null

# Virtual environment path
$VenvPath = Join-Path "." "venv"
$PythonExe = Join-Path $VenvPath "Scripts/python.exe"

# Script path
$ScriptPath = Join-Path "." "src/main.py"

try {
    if (-not (Test-Path -LiteralPath $PythonExe)) {
        Write-Host "[ERROR] Virtual environment not found: $VenvPath" -ForegroundColor Red
        exit 1
    }

    if (-not (Test-Path -LiteralPath $ScriptPath)) {
        Write-Host "[ERROR] Script not found: $ScriptPath" -ForegroundColor Red
        exit 1
    }

    Write-Host "[INFO] Running script: $ScriptPath"
    $env:PYTHONIOENCODING = "utf-8"
    & $PythonExe -X utf8 $ScriptPath
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] Script execution failed." -ForegroundColor Red
        exit $LASTEXITCODE
    }

    Write-Host "[INFO] Execution completed."
}
catch {
    Write-Host "[ERROR] Unexpected error: $_" -ForegroundColor Red
    exit 1
}