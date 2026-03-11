# Запуск установки git-hook деплоя в репозитории темы (seo_entuziastov75).
# Можно вызывать из content-factory — скрипт сам перейдёт в репо темы.
#
# Запуск:
#   powershell -ExecutionPolicy Bypass -File "D:\content-factory\scripts\install-deploy-hook-in-vps.ps1"

$ErrorActionPreference = "Stop"
$factoryRoot = "D:\content-factory"
$vpsPath = "C:\Users\user\Documents\seo_entuziastov75"
if (-not (Test-Path $vpsPath)) { $vpsPath = "D:\entuziastov75-vps" }

$hookScript = Join-Path $vpsPath "scripts\install-deploy-hook.ps1"
if (-not (Test-Path $hookScript)) {
    Write-Host "Theme repo script not found: $hookScript" -ForegroundColor Red
    exit 1
}

Push-Location $vpsPath
try {
    & (Join-Path $vpsPath "scripts\install-deploy-hook.ps1")
} finally {
    Pop-Location
}
