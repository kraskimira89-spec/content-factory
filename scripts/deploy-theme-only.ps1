# Только деплой темы на VPS (без коммита и пуша).
# Для использования в Планировщике заданий или вручную.
#
# Запуск:
#   powershell -ExecutionPolicy Bypass -File "D:\content-factory\scripts\deploy-theme-only.ps1"

$ErrorActionPreference = "Stop"
$factoryRoot = "D:\content-factory"

Write-Host "=== Деплой темы на VPS (mode: theme) ===" -ForegroundColor Cyan
Push-Location $factoryRoot
try {
    python scripts/deploy_to_vps.py --mode theme
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Деплой завершился с ошибкой." -ForegroundColor Red
        exit 1
    }
    Write-Host "Готово: тема обновлена на VPS." -ForegroundColor Green
} finally {
    Pop-Location
}
