# Launcher для Karusel: добавляет cuDNN из venv в PATH и запускает тест
# через python из локального виртуального окружения.

param(
    [string]$VenvRoot = "",
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$PythonArgs
)

$ErrorActionPreference = "Stop"

$karuselRoot = $PSScriptRoot
$repoRoot = Split-Path $karuselRoot -Parent

if ([string]::IsNullOrWhiteSpace($VenvRoot)) {
    $VenvRoot = Join-Path $repoRoot "venv"
}

$pythonExe = Join-Path $VenvRoot "Scripts\python.exe"
$cudnnBin = Join-Path $VenvRoot "Lib\site-packages\nvidia\cudnn\bin"
$testFile = Join-Path $karuselRoot "tests\test_agents_2_3.py"

if (-not (Test-Path $pythonExe)) {
    throw "Python venv not found: $pythonExe"
}

if (-not (Test-Path $testFile)) {
    throw "Test file not found: $testFile"
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

Write-Host "Python: $pythonExe" -ForegroundColor Cyan
Write-Host "Test:   $testFile" -ForegroundColor Cyan

Push-Location $karuselRoot
try {
    & $pythonExe $testFile @PythonArgs
    exit $LASTEXITCODE
}
finally {
    Pop-Location
}
