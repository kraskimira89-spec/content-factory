# Универсальный launcher для Karusel: добавляет cuDNN из venv в PATH
# и запускает указанный Python-скрипт через локальное виртуальное окружение.

param(
    [string]$ScriptPath,
    [string]$VenvRoot = "",
    [string]$WorkingDirectory = "",
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$ScriptArgs
)

$ErrorActionPreference = "Stop"

$karuselRoot = $PSScriptRoot
$repoRoot = Split-Path $karuselRoot -Parent

if ([string]::IsNullOrWhiteSpace($ScriptPath)) {
    throw "Specify -ScriptPath, for example: .\run-python-gpu.ps1 -ScriptPath .\tests\test_agents_2_3.py"
}

if ([string]::IsNullOrWhiteSpace($VenvRoot)) {
    $VenvRoot = Join-Path $repoRoot "venv"
}

if ([string]::IsNullOrWhiteSpace($WorkingDirectory)) {
    $WorkingDirectory = $karuselRoot
}

$pythonExe = Join-Path $VenvRoot "Scripts\python.exe"
$cudnnBin = Join-Path $VenvRoot "Lib\site-packages\nvidia\cudnn\bin"

if (-not (Test-Path $pythonExe)) {
    throw "Python venv not found: $pythonExe"
}

$resolvedWorkingDirectory = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($WorkingDirectory)
$resolvedScriptPath = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($ScriptPath)

if (-not (Test-Path $resolvedScriptPath)) {
    throw "Script file not found: $resolvedScriptPath"
}

if (-not (Test-Path $resolvedWorkingDirectory)) {
    throw "Working directory not found: $resolvedWorkingDirectory"
}

if (Test-Path $cudnnBin) {
    $pathParts = @()
    if (-not [string]::IsNullOrWhiteSpace($env:Path)) {
        $pathParts = $env:Path.Split(";") | Where-Object { $_ -ne "" }
    }
    if ($pathParts -notcontains $cudnnBin) {
        $env:Path = $cudnnBin + ";" + $env:Path
    }
    Write-Host "cuDNN PATH added: $cudnnBin" -ForegroundColor Green
} else {
    Write-Host "cuDNN path not found: $cudnnBin" -ForegroundColor Yellow
    Write-Host "Install with: $pythonExe -m pip install nvidia-cudnn-cu12" -ForegroundColor Yellow
}

Write-Host "Python:  $pythonExe" -ForegroundColor Cyan
Write-Host "Script:  $resolvedScriptPath" -ForegroundColor Cyan
Write-Host "Workdir: $resolvedWorkingDirectory" -ForegroundColor Cyan

Push-Location $resolvedWorkingDirectory
try {
    & $pythonExe $resolvedScriptPath @ScriptArgs
    exit $LASTEXITCODE
}
finally {
    Pop-Location
}
