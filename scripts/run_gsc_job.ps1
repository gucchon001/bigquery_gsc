param(
    [ValidateSet('development','production')]
    [string]$Environment = 'development'
)

$ErrorActionPreference = 'Stop'

# Repo root = this file's parent directory's parent
$repoRoot = Resolve-Path (Join-Path $PSScriptRoot '..')
Set-Location $repoRoot

# Logs
if (-not (Test-Path -LiteralPath 'logs')) { New-Item -ItemType Directory -Path 'logs' | Out-Null }
$ts = (Get-Date).ToString('yyyyMMdd_HHmmss')
$logPath = Join-Path 'logs' ("scheduled_${ts}.log")

# Env vars
$env:PYTHONPATH = (Join-Path $repoRoot 'src')
# 任意: 実行環境を渡したい場合に使用（EnvironmentUtils側で読む変数名に合わせて調整）
$env:APP_ENV = $Environment

# Python path
$pythonExe = Join-Path $repoRoot 'venv/Scripts/python.exe'
if (-not (Test-Path -LiteralPath $pythonExe)) {
    Write-Error "Python venv not found: $pythonExe"
}

# Run
Write-Output "[INFO] Starting GSC job ($Environment) at $(Get-Date -Format o)" | Tee-Object -FilePath $logPath -Append | Out-Null
& $pythonExe (Join-Path $repoRoot 'src/main.py') 2>&1 | Tee-Object -FilePath $logPath -Append
$exitCode = $LASTEXITCODE
Write-Output "[INFO] Finished with code $exitCode at $(Get-Date -Format o)" | Tee-Object -FilePath $logPath -Append | Out-Null
exit $exitCode


